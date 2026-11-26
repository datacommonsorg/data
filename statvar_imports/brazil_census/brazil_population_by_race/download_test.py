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
"""Unit tests for Brazil Census Race download module."""

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
    "brazil_population_by_race_download",
    os.path.join(SCRIPT_DIR, "download.py"),
)
download_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["brazil_population_by_race_download"] = download_mod
_SPEC.loader.exec_module(download_mod)

FLAGS = download_mod.FLAGS
download_all_years = download_mod.download_all_years
get_robust_session = download_mod.get_robust_session


class DownloadTest(unittest.TestCase):
    """Unit test suite for Race downloader."""

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
    def test_download_mocked_success(self, mock_sync):
        """Tests successful live 2022+ download and historical sync."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "NC": "Nível Territorial"
            },
            {
                "NC": "1",
                "D1N": "Brasil",
                "D3N": "2022",
                "D4N": "Total",
                "V": "203080756",
            },
            {
                "NC": "1",
                "D1N": "Brasil",
                "D3N": "2022",
                "D4N": "Branca",
                "V": "88258544",
            },
            {
                "NC": "1",
                "D1N": "Brasil",
                "D3N": "2010",
                "D4N": "Branca",
                "V": "91051646",
            },
        ]
        mock_response.raise_for_status.return_value = None
        session.get.return_value = mock_response

        out_csv = os.path.join(self.test_dir, "output.csv")
        saved_file = download_all_years(session=session,
                                        output_file=out_csv,
                                        fallback_to_cached=False)
        self.assertTrue(os.path.isfile(saved_file))
        mock_sync.assert_called_once()

        df = pd.read_csv(saved_file)
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns),
                         ["Ano", "Localidade", "Cor", "Populacao"])
        self.assertEqual(set(df["Ano"].values), {2022})

    @patch.object(download_mod, "sync_historical_csv")
    def test_download_empty_response_raises(self, _mock_sync):
        """Tests that empty data raises RuntimeError when fallback is disabled."""
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
        """Tests that fallback succeeds when both cached CSV and history exist."""
        session = MagicMock()
        session.get.side_effect = requests.HTTPError("503 Service Unavailable")

        cached_csv = os.path.join(self.test_dir, "cached.csv")
        with open(cached_csv, "w", encoding="utf-8") as f:
            f.write("Ano,Localidade,Cor,Populacao\n2022,Brazil,Total,100\n")
        hist_dir = os.path.join(self.test_dir, "history")
        os.makedirs(hist_dir, exist_ok=True)
        with open(os.path.join(hist_dir,
                               "brazil_population_by_race_historical.csv"),
                  "w",
                  encoding="utf-8") as f:
            f.write("h\n1\n")

        saved = download_all_years(session=session,
                                   output_file=cached_csv,
                                   fallback_to_cached=True)
        self.assertEqual(saved, cached_csv)
        self.assertTrue(os.path.isfile(saved))

    @patch.object(download_mod, "sync_historical_csv")
    def test_table_9605_discovers_multiple_periods_and_skips_5101837(
            self, _mock_sync):
        """Tests Table 9605 discovers >=2022 periods dynamically and skips 5101837 by default."""
        session = MagicMock()
        seen_urls = []

        def get_mock_response(url, **kwargs):
            seen_urls.append(url)
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            if "/n1/1/" in url:
                resp.json.return_value = [
                    {
                        "NC": "Header"
                    },
                    {
                        "NC": "1",
                        "D1N": "Brasil",
                        "D3C": "2010",
                        "D3N": "2010",
                        "V": "190755799",
                    },
                    {
                        "NC": "1",
                        "D1N": "Brasil",
                        "D3C": "2022",
                        "D3N": "2022",
                        "V": "203080756",
                    },
                    {
                        "NC": "1",
                        "D1N": "Brasil",
                        "D3C": "2032",
                        "D3N": "2032",
                        "V": "215000000",
                    },
                ]
            elif "/p/2032/" in url:
                resp.json.return_value = [
                    {
                        "NC": "Header"
                    },
                    {
                        "NC": "1",
                        "D1N": "Brasil",
                        "D3N": "2032",
                        "D4N": "Total",
                        "V": "215000000",
                    },
                    {
                        "NC": "6",
                        "D1C": "5101837",
                        "D3N": "2032",
                        "D4N": "Total",
                        "V": "999",
                    },
                ]
            else:
                resp.json.return_value = [
                    {
                        "NC": "Header"
                    },
                    {
                        "NC": "1",
                        "D1N": "Brasil",
                        "D3N": "2022",
                        "D4N": "Total",
                        "V": "203080756",
                    },
                ]
            return resp

        session.get.side_effect = get_mock_response
        out_csv = os.path.join(self.test_dir, "race_multi.csv")
        download_all_years(session=session,
                           output_file=out_csv,
                           fallback_to_cached=False)

        self.assertTrue(
            any("t/9605/n6/all/v/93/p/2022/" in u for u in seen_urls))
        self.assertTrue(
            any("t/9605/n6/all/v/93/p/2032/" in u for u in seen_urls))
        self.assertFalse(
            any("/n1/all/n2/all/n3/all/n6/all/" in u for u in seen_urls))
        df = pd.read_csv(out_csv)
        self.assertEqual(set(df["Ano"].values), {2022, 2032})
        self.assertNotIn("5101837", set(df["Localidade"].astype(str).values))

    @patch.object(download_mod, "sync_historical_csv")
    def test_table_9605_empty_period_batches_raises(self, _mock_sync):
        """Tests Table 9605 raises RuntimeError if probe returns only <2022 periods."""
        session = MagicMock()
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = [
            {
                "NC": "Header"
            },
            {
                "NC": "1",
                "D1N": "Brasil",
                "D3C": "2010",
                "D3N": "2010",
                "V": "190755799",
            },
        ]
        session.get.return_value = resp

        out_csv = os.path.join(self.test_dir, "race_empty_periods.csv")
        with self.assertRaises(RuntimeError):
            download_all_years(session=session,
                               output_file=out_csv,
                               fallback_to_cached=False)


if __name__ == "__main__":
    unittest.main()
