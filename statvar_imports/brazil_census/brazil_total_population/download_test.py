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
"""Unit tests for Brazil Census Total Population download module."""

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
    "brazil_total_population_download", os.path.join(SCRIPT_DIR, "download.py"))
download_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["brazil_total_population_download"] = download_mod
_SPEC.loader.exec_module(download_mod)

FLAGS = download_mod.FLAGS
download_all_years = download_mod.download_all_years
get_robust_session = download_mod.get_robust_session
sync_historical_csv = download_mod.sync_historical_csv


class DownloadTest(unittest.TestCase):
    """Unit test suite for Total Population downloader."""

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
        """Tests successful live 2022+ Census & EstimaPop download + historical sync."""
        session = MagicMock()

        def get_mock_response(url, **kwargs):
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            if "6579" in url:
                resp.json.return_value = [
                    {
                        "NC": "Header"
                    },
                    {
                        "NC": "1",
                        "D1N": "Brasil",
                        "D3N": "2024",
                        "V": "212583750",
                    },
                    {
                        "NC": "6",
                        "D1C": "5101837",
                        "D3N": "2024",
                        "V": "1234",
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
                    {
                        "NC": "1",
                        "D1N": "Brasil",
                        "D3N": "2022",
                        "D4N": "Homens",
                        "V": "98532431",
                    },
                    {
                        "NC": "6",
                        "D1C": "3139904",
                        "D3N": "2022",
                        "D4N": "Total",
                        "V": "13629",
                    },
                ]
            return resp

        session.get.side_effect = get_mock_response

        out_csv = os.path.join(self.test_dir, "output.csv")
        saved_file = download_all_years(session=session,
                                        output_file=out_csv,
                                        fallback_to_cached=False)
        self.assertTrue(os.path.isfile(saved_file))
        mock_sync.assert_called_once()

        df = pd.read_csv(saved_file)
        self.assertEqual(len(df), 4)
        self.assertEqual(list(df.columns),
                         ["Ano", "Localidade", "Sexo", "Populacao"])
        self.assertEqual(set(df["Ano"].values), {2022, 2024})

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
            f.write("Ano,Localidade,Sexo,Populacao\n2022,Brazil,Total,100\n")
        hist_dir = os.path.join(self.test_dir, "history")
        os.makedirs(hist_dir, exist_ok=True)
        with open(os.path.join(hist_dir,
                               "brazil_total_population_historical.csv"),
                  "w",
                  encoding="utf-8") as f:
            f.write("h\n1\n")

        saved = download_all_years(session=session,
                                   output_file=cached_csv,
                                   fallback_to_cached=True)
        self.assertEqual(saved, cached_csv)
        self.assertTrue(os.path.isfile(saved))

    def test_sync_historical_csv_atomic_and_fallback(self):
        """Tests sync_historical_csv atomic download and fallback behavior."""
        dest = os.path.join(self.test_dir, "history", "hist.csv")

        def fake_download(filename):
            with open(filename, "w", encoding="utf-8") as f:
                f.write("col\nval\n")

        mock_blob = MagicMock()
        mock_blob.download_to_filename.side_effect = fake_download
        mock_client = MagicMock()
        mock_client.bucket.return_value.blob.return_value = mock_blob

        with patch("google.cloud.storage.Client", return_value=mock_client):
            result = sync_historical_csv("country/brazil/history/hist.csv",
                                         dest)
        self.assertEqual(result, dest)
        self.assertTrue(os.path.isfile(dest))
        with open(dest, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "col\nval\n")

        with patch("google.cloud.storage.Client",
                   side_effect=RuntimeError("GCS offline")):
            self.assertEqual(
                sync_historical_csv(
                    "country/brazil/history/hist.csv",
                    dest,
                    fallback_to_cached=True,
                ),
                dest,
            )
            with self.assertRaises(RuntimeError):
                sync_historical_csv(
                    "country/brazil/history/hist.csv",
                    dest,
                    fallback_to_cached=False,
                )

    @patch.object(download_mod, "sync_historical_csv")
    def test_table_6579_discovers_all_post_2022_periods_in_batches(
            self, _mock_sync):
        """Tests Table 6579 discovers >5 periods >2022 and fetches in 5-year batches."""
        session = MagicMock()
        seen_urls = []

        def get_mock_response(url, **kwargs):
            seen_urls.append(url)
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            if "6579/n1/1/" in url:
                resp.json.return_value = [
                    {
                        "NC": "Header"
                    },
                    *[{
                        "NC": "1",
                        "D1N": "Brasil",
                        "D3C": str(y),
                        "D3N": str(y),
                        "V": "200000000",
                    } for y in range(2020, 2031) if y not in (2022, 2023)],
                ]
            elif "6579/" in url:
                periods = url.split("/p/")[1].split("?")[0].split(",")
                resp.json.return_value = [
                    {
                        "NC": "Header"
                    },
                    *[{
                        "NC": "1",
                        "D1N": "Brasil",
                        "D3N": p,
                        "V": str(210000000 + int(p)),
                    } for p in periods],
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
        out_csv = os.path.join(self.test_dir, "output_batches.csv")
        download_all_years(session=session,
                           output_file=out_csv,
                           fallback_to_cached=False)

        self.assertTrue(
            any("/p/2024,2025,2026,2027,2028?" in u for u in seen_urls))
        self.assertTrue(any("/p/2029,2030?" in u for u in seen_urls))
        df = pd.read_csv(out_csv)
        self.assertEqual(set(df["Ano"].values),
                         {2022, 2024, 2025, 2026, 2027, 2028, 2029, 2030})


if __name__ == "__main__":
    unittest.main()
