# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for Brazil Census Residence download module."""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SPEC = importlib.util.spec_from_file_location(
    "brazil_population_by_residence_download",
    os.path.join(SCRIPT_DIR, "download.py"),
)
download_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["brazil_population_by_residence_download"] = download_mod
_SPEC.loader.exec_module(download_mod)

FLAGS = download_mod.FLAGS
download_all_years = download_mod.download_all_years
get_robust_session = download_mod.get_robust_session


class DownloadTest(unittest.TestCase):
    """Unit test suite for Residence downloader."""

    def setUp(self):
        super().setUp()
        FLAGS.mark_as_parsed()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        super().tearDown()

    def test_robust_session_configuration(self):
        """Verifies session retry configuration includes 429 and 5xx error codes."""
        session = get_robust_session()
        self.assertIsInstance(session, requests.Session)
        adapter = session.adapters.get("https://")
        self.assertIsNotNone(adapter)
        self.assertEqual(adapter.max_retries.total, 10)
        self.assertIn(429, adapter.max_retries.status_forcelist)
        self.assertIn(500, adapter.max_retries.status_forcelist)

    @patch.object(download_mod, "fetch_raw_input_files")
    def test_download_mocked_success(self, mock_raw_input):
        """Tests successful download and CSV emission."""
        session = MagicMock()
        def get_mock_response(url, **kwargs):
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            if "608" in url:
                resp.json.return_value = [
                    {"NC": "Nível Territorial"},
                    {"NC": "1", "D1N": "Brasil", "D3N": "2010", "D5N": "Total", "V": "190755799"},
                    {"NC": "1", "D1N": "Brasil", "D3N": "2010", "D5N": "Urbana", "V": "160925792"},
                ]
            else:
                resp.json.return_value = [
                    {"NC": "Nível Territorial"},
                    {"NC": "1", "D1N": "Brasil", "D3N": "2022", "D4N": "Total", "V": "203080756"},
                    {"NC": "1", "D1N": "Brasil", "D3N": "2022", "D4N": "Urbana", "V": "177508417"},
                ]
            return resp
        session.get.side_effect = get_mock_response

        mock_raw_input.return_value = [
            {
                "Ano": 1940,
                "Localidade": "Brazil",
                "Situacao": "Total",
                "Sexo": "Total",
                "Populacao": 41169321,
            },
            {
                "Ano": 1940,
                "Localidade": "Brazil",
                "Situacao": "Urbana",
                "Sexo": "Total",
                "Populacao": 12877647,
            },
        ]

        out_csv = os.path.join(self.test_dir, "output.csv")
        saved_file = download_all_years(
            session=session, output_file=out_csv, fallback_to_cached=False
        )
        self.assertTrue(os.path.isfile(saved_file))

        df = pd.read_csv(saved_file)
        self.assertGreaterEqual(len(df), 4)
        self.assertEqual(
            list(df.columns),
            ["Ano", "Localidade", "Situacao", "Sexo", "Populacao"],
        )
        self.assertIn(1940, df["Ano"].values)

    @patch.object(download_mod, "fetch_raw_input_files", return_value=[])
    def test_download_empty_response_raises(self, _mock_raw_input):
        """Tests that empty data raises RuntimeError when fallback is disabled."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response

        out_csv = os.path.join(self.test_dir, "output.csv")
        with self.assertRaises(RuntimeError):
            download_all_years(
                session=session, output_file=out_csv, fallback_to_cached=False
            )

    @patch.object(download_mod, "fetch_raw_input_files", return_value=[])
    def test_download_network_failure_raises(self, _mock_raw_input):
        """Tests that network error raises RuntimeError when fallback is disabled."""
        session = MagicMock()
        session.get.side_effect = requests.ConnectionError(
            "Connection timed out"
        )

        out_csv = os.path.join(self.test_dir, "output.csv")
        with self.assertRaises(RuntimeError):
            download_all_years(
                session=session, output_file=out_csv, fallback_to_cached=False
            )

    @patch.object(download_mod, "fetch_raw_input_files", return_value=[])
    def test_download_fallback_to_cached(self, _mock_raw_input):
        """Tests that fallback to existing CSV succeeds when fallback is enabled."""
        session = MagicMock()
        session.get.side_effect = requests.HTTPError("503 Service Unavailable")

        cached_csv = os.path.join(self.test_dir, "cached.csv")
        with open(cached_csv, "w", encoding="utf-8") as f:
            f.write(
                "Ano,Localidade,Situacao,Sexo,Populacao\n"
                "1940,Brazil,Total,Total,100\n"
            )

        saved = download_all_years(
            session=session, output_file=cached_csv, fallback_to_cached=True
        )
        self.assertEqual(saved, cached_csv)
        self.assertTrue(os.path.isfile(saved))



    def test_stat_var_processor_sample_data(self):
        """Verifies stat_var_processor correctly processes test_data sample CSV."""
        repo_dir = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
        processor_script = os.path.join(repo_dir, "tools", "statvar_importer", "stat_var_processor.py")
        if not os.path.isfile(processor_script):
            self.skipTest("stat_var_processor.py not found")
        imp_name = os.path.basename(SCRIPT_DIR)
        sample_csv = os.path.join(SCRIPT_DIR, "test_data", f"sample_{imp_name}.csv")
        pv_map = os.path.join(SCRIPT_DIR, f"{imp_name}_pvmap.csv")
        metadata_csv = os.path.join(SCRIPT_DIR, f"{imp_name}_metadata.csv")
        places_csv = os.path.join(SCRIPT_DIR, "..", "brazil_places_resolved.csv")
        out_prefix = os.path.join(self.test_dir, f"{imp_name}_out")
        import csv
        import json

        # Create hermetic test config with reconcile_nodes=False to avoid external DC API calls
        meta = {"reconcile_nodes": False}
        if os.path.isfile(metadata_csv):
            with open(metadata_csv, encoding="utf-8") as f:
                for row in csv.reader(f):
                    if row and len(row) == 2 and not row[0].startswith("#"):
                        meta[row[0].strip()] = row[1].strip()
            meta["reconcile_nodes"] = False
            if "header_rows" in meta:
                meta["header_rows"] = int(meta["header_rows"])
        cfg_json = os.path.join(self.test_dir, "test_config.json")
        with open(cfg_json, "w", encoding="utf-8") as f:
            json.dump(meta, f)

        cmd = [
            sys.executable,
            processor_script,
            f"--input_data={sample_csv}",
            f"--pv_map={pv_map}",
            f"--config_file={cfg_json}",
            f"--places_resolved_csv={places_csv}",
            f"--output_path={out_prefix}",
        ]
        res = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"stat_var_processor failed: {res.stderr}")
        self.assertTrue(os.path.isfile(f"{out_prefix}.csv"))
        self.assertTrue(os.path.isfile(f"{out_prefix}.tmcf"))
        df_out = pd.read_csv(f"{out_prefix}.csv")
        self.assertGreater(len(df_out), 0)


if __name__ == "__main__":
    unittest.main()
