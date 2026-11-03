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
"""Unit tests for Brazil Census population by age and sex download module."""

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
    "brazil_population_by_age_and_sex_download",
    os.path.join(SCRIPT_DIR, "download.py"),
)
download_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["brazil_population_by_age_and_sex_download"] = download_mod
_SPEC.loader.exec_module(download_mod)

FLAGS = download_mod.FLAGS
download_all_years = download_mod.download_all_years
compute_broad_age_aggregations = download_mod.compute_broad_age_aggregations
fetch_sidra_data = download_mod.fetch_sidra_data
get_robust_session = download_mod.get_robust_session


class DownloadTest(unittest.TestCase):
    """Unit test suite for Brazil population by age and sex downloader."""

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
        self.assertIn(503, adapter.max_retries.status_forcelist)

    def test_compute_broad_age_aggregations(self):
        """Tests calculation of 0To14, 15To59, and 60OrMore broad cohorts."""
        test_rows = [
            {"Ano": "2022", "Localidade": "Brazil", "Idade": "0 a 4 anos", "Sexo": "Total", "Populacao": "100"},
            {"Ano": "2022", "Localidade": "Brazil", "Idade": "5 a 9 anos", "Sexo": "Total", "Populacao": "150"},
            {"Ano": "2022", "Localidade": "Brazil", "Idade": "10 a 14 anos", "Sexo": "Total", "Populacao": "200"},
            {"Ano": "2022", "Localidade": "Brazil", "Idade": "15 a 19 anos", "Sexo": "Total", "Populacao": "300"},
            {"Ano": "2022", "Localidade": "Brazil", "Idade": "60 a 64 anos", "Sexo": "Total", "Populacao": "50"},
            {"Ano": "2022", "Localidade": "Brazil", "Idade": "65 a 69 anos", "Sexo": "Total", "Populacao": "40"},
        ]
        aggs = compute_broad_age_aggregations(test_rows, "2022")
        self.assertTrue(len(aggs) >= 3)
        agg_map = {(r["Idade"], r["Sexo"]): int(r["Populacao"]) for r in aggs}
        self.assertEqual(agg_map.get(("De 0 a 14 anos", "Total")), 450)
        self.assertEqual(agg_map.get(("De 15 a 59 anos", "Total")), 300)
        self.assertEqual(agg_map.get(("De 60 anos ou mais", "Total")), 90)

    def test_fetch_sidra_data_success(self):
        """Tests successful SIDRA fetch returning parsed JSON rows."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"NC": "Nível"},
            {"NC": "1", "D1N": "Brasil", "D3N": "2022", "D4N": "Total", "D5N": "Total", "V": "203080756"},
        ]
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response

        data = fetch_sidra_data(session, "https://fake.url")
        self.assertEqual(len(data), 2)
        self.assertEqual(data[1]["D1N"], "Brasil")

    def test_fetch_sidra_data_empty_raises(self):
        """Tests that empty response raises RuntimeError."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response

        with self.assertRaises(RuntimeError) as ctx:
            fetch_sidra_data(session, "https://fake.url")
        self.assertIn("Invalid or empty response", str(ctx.exception))

    @patch.object(download_mod, "fetch_raw_historical_files")
    def test_download_all_years_success(self, mock_hist):
        """Tests download_all_years combining historical workbooks and live SIDRA data."""
        mock_hist.return_value = [
            {"Ano": "1940", "Localidade": "Brazil", "Idade": "Total", "Sexo": "Total", "Populacao": "41236315"}
        ]
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"NC": "Header"},
            {"NC": "1", "D1N": "Brasil", "D3N": "2022", "D4N": "Total", "D5N": "Total", "V": "203080756"},
            {"NC": "1", "D1N": "Brasil", "D3N": "2022", "D4N": "Total", "D5N": "0 a 4 anos", "V": "1000"},
            {"NC": "1", "D1N": "Brasil", "D3N": "2022", "D4N": "Total", "D5N": "5 a 9 anos", "V": "2000"},
            {"NC": "1", "D1N": "Brasil", "D3N": "2022", "D4N": "Total", "D5N": "10 a 14 anos", "V": "3000"},
        ]
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response

        out_csv = os.path.join(self.test_dir, "output.csv")
        saved_file = download_all_years(session=session, output_file=out_csv, fallback_to_cached=False)
        self.assertTrue(os.path.isfile(saved_file))

        df = pd.read_csv(saved_file)
        self.assertIn("1940", df["Ano"].astype(str).values)
        self.assertIn("2022", df["Ano"].astype(str).values)
        self.assertIn("De 0 a 14 anos", df["Idade"].values)

    @patch.object(download_mod, "fetch_raw_historical_files")
    def test_download_all_years_fallback_to_cached(self, mock_hist):
        """Tests that fallback to existing CSV succeeds when fallback is enabled."""
        mock_hist.return_value = []
        session = MagicMock()
        session.get.side_effect = requests.HTTPError("503 Service Unavailable")

        cached_csv = os.path.join(self.test_dir, "cached.csv")
        with open(cached_csv, "w", encoding="utf-8") as f:
            f.write("Ano,Localidade,Idade,Sexo,Populacao\n2022,Brazil,Total,Total,100\n")

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
