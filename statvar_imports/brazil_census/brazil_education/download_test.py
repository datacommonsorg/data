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
from unittest.mock import MagicMock
from unittest.mock import patch

import pandas as pd
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SPEC = importlib.util.spec_from_file_location(
    "brazil_education_download", os.path.join(SCRIPT_DIR, "download.py"))
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
        """Verifies session retry configuration includes 429, 5xx, and 52x codes."""
        session = get_robust_session()
        self.assertIsInstance(session, requests.Session)
        adapter = session.adapters.get("https://")
        self.assertIsNotNone(adapter)
        self.assertEqual(adapter.max_retries.total, 10)
        self.assertIn(429, adapter.max_retries.status_forcelist)
        self.assertIn(500, adapter.max_retries.status_forcelist)
        self.assertIn(520, adapter.max_retries.status_forcelist)

    @patch.object(download_mod, "sync_historical_csv")
    def test_download_mocked_success(self, mock_sync_history):
        """Tests successful live 2022+ download and historical sync call."""
        session = MagicMock()

        def get_mock_response(url, **kwargs):
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            resp.json.return_value = [
                {
                    "NC": "Nível Territorial"
                },
                {
                    "NC": "1",
                    "D1N": "Brasil",
                    "D3N": "2022",
                    "D4C": "95300",
                    "D4N": "Total",
                    "V": "10000000",
                },
                {
                    "NC": "1",
                    "D1N": "Brasil",
                    "D3N": "2022",
                    "D4C": "95301",
                    "D4N": "Creche",
                    "V": "2000000",
                },
                {
                    "NC": "1",
                    "D1N": "Brasil",
                    "D3N": "2010",
                    "D4C": "95300",
                    "D4N": "Total",
                    "V": "999",
                },
            ]
            return resp

        session.get.side_effect = get_mock_response

        out_csv = os.path.join(self.test_dir, "output.csv")
        saved_file = download_all_years(session=session,
                                        output_file=out_csv,
                                        fallback_to_cached=False)
        self.assertTrue(os.path.isfile(saved_file))
        mock_sync_history.assert_called_once()

        df = pd.read_csv(saved_file)
        self.assertEqual(len(df), 2)
        self.assertEqual(
            list(df.columns),
            ["Ano", "Localidade", "RedeEnsino", "NivelEnsino", "Estudantes"],
        )
        self.assertEqual(set(df["Ano"].values), {2022})
        creche_2022 = df[df["NivelEnsino"] == "Creche"].iloc[0]
        self.assertEqual(creche_2022["Localidade"], "Brazil")
        self.assertEqual(
            creche_2022["Estudantes"],
            2000000 * len(download_mod.TABLE_2022_EDUCATION_SPECS),
        )

    @patch.object(download_mod, "sync_historical_csv")
    def test_download_empty_response_raises(self, _mock_sync):
        """Tests that an empty response payload raises RuntimeError."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response

        out_csv = os.path.join(self.test_dir, "output.csv")
        with self.assertRaises(RuntimeError):
            download_all_years(session=session,
                               output_file=out_csv,
                               fallback_to_cached=False)

    @patch.object(download_mod, "sync_historical_csv")
    def test_download_network_failure_raises(self, _mock_sync):
        """Tests that network error raises RuntimeError when fallback is disabled."""
        session = MagicMock()
        session.get.side_effect = requests.ConnectionError(
            "Connection timed out")

        out_csv = os.path.join(self.test_dir, "output.csv")
        with self.assertRaises(RuntimeError):
            download_all_years(session=session,
                               output_file=out_csv,
                               fallback_to_cached=False)

    def test_download_fallback_to_cached(self):
        """Tests that fallback succeeds only when both cached CSV and history exist."""
        session = MagicMock()
        session.get.side_effect = requests.HTTPError("503 Service Unavailable")

        cached_csv = os.path.join(self.test_dir, "cached.csv")
        with open(cached_csv, "w", encoding="utf-8") as f:
            f.write("Ano,Localidade,RedeEnsino,NivelEnsino,Estudantes\n"
                    "2022,Brazil,Total,Total,100\n")
        hist_dir = os.path.join(self.test_dir, "history")
        os.makedirs(hist_dir, exist_ok=True)
        with open(os.path.join(hist_dir, "brazil_education_historical.csv"),
                  "w",
                  encoding="utf-8") as f:
            f.write(
                "observationAbout,observationDate,observationPeriod,value,variableMeasured\n"
                "dcid:country/BRA,2010,P1Y,100,dcid:Count_Student\n")

        saved = download_all_years(session=session,
                                   output_file=cached_csv,
                                   fallback_to_cached=True)
        self.assertEqual(saved, cached_csv)
        self.assertTrue(os.path.isfile(saved))


if __name__ == "__main__":
    unittest.main()
