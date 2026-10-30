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
"""Unit tests for Brazil Census Education download module."""

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SPEC = importlib.util.spec_from_file_location(
    "brazil_education_download", os.path.join(SCRIPT_DIR, "download.py")
)
download_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["brazil_education_download"] = download_mod
_SPEC.loader.exec_module(download_mod)

FLAGS = download_mod.FLAGS
download_all_years = download_mod.download_all_years
get_robust_session = download_mod.get_robust_session


class DownloadTest(unittest.TestCase):
    """Unit test suite for Education downloader."""

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

    @patch.object(download_mod, "fetch_2010_education_files", return_value=[])
    @patch.object(
        download_mod, "fetch_from_ibge_ftp_or_input_files", return_value=[]
    )
    def test_download_mocked_success(self, _mock_ftp, _mock_2010):
        """Tests successful download and CSV emission with exact D5C category mapping."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_payload = [
            {"NC": "Nível Territorial"},
            {
                "NC": "1",
                "D1N": "Brasil",
                "D3N": "2010",
                "D4N": "Total",
                "D5C": "0",
                "D5N": "Total",
                "V": "59565188",
            },
            {
                "NC": "1",
                "D1N": "Brasil",
                "D3N": "2010",
                "D4N": "Pública",
                "D5C": "95304",
                "D5N": "Regular do ensino fundamental",
                "V": "27500000",
            },
            {
                "NC": "1",
                "D1N": "Brasil",
                "D3N": "2010",
                "D4N": "Total",
                "D5C": "7910",
                "D5N": "Especialização de nível superior",
                "V": "666613",
            },
        ]
        mock_response.json.return_value = mock_payload
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response

        out_csv = os.path.join(self.test_dir, "output.csv")
        saved_file = download_all_years(
            session=session, output_file=out_csv, fallback_to_cached=False
        )
        self.assertTrue(os.path.isfile(saved_file))

        df = pd.read_csv(saved_file)
        self.assertEqual(len(df), 2)
        self.assertEqual(
            list(df.columns),
            ["Ano", "Localidade", "RedeEnsino", "NivelEnsino", "Estudantes"],
        )
        total_row = df[df["NivelEnsino"] == "Total"].iloc[0]
        self.assertEqual(total_row["Localidade"], "Brazil")
        self.assertEqual(total_row["Estudantes"], 59565188)

    @patch.object(download_mod, "fetch_2010_education_files", return_value=[])
    @patch.object(
        download_mod, "fetch_from_ibge_ftp_or_input_files", return_value=[]
    )
    def test_download_empty_response_raises(self, _mock_ftp, _mock_2010):
        """Tests that an empty response payload raises RuntimeError."""
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

    @patch.object(download_mod, "fetch_2010_education_files", return_value=[])
    @patch.object(
        download_mod, "fetch_from_ibge_ftp_or_input_files", return_value=[]
    )
    def test_download_network_failure_raises(self, _mock_ftp, _mock_2010):
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

    @patch.object(download_mod, "fetch_2010_education_files", return_value=[])
    @patch.object(
        download_mod, "fetch_from_ibge_ftp_or_input_files", return_value=[]
    )
    def test_download_fallback_to_cached(self, _mock_ftp, _mock_2010):
        """Tests that fallback to existing CSV succeeds when fallback is enabled."""
        session = MagicMock()
        session.get.side_effect = requests.HTTPError("503 Service Unavailable")

        cached_csv = os.path.join(self.test_dir, "cached.csv")
        with open(cached_csv, "w", encoding="utf-8") as f:
            f.write(
                "Ano,Localidade,RedeEnsino,NivelEnsino,Populacao\n"
                "2010,Brazil,Total,Total,100\n"
            )

        saved = download_all_years(
            session=session, output_file=cached_csv, fallback_to_cached=True
        )
        self.assertEqual(saved, cached_csv)
        self.assertTrue(os.path.isfile(saved))


if __name__ == "__main__":
    unittest.main()
