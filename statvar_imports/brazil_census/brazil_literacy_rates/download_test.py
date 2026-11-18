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
"""Unit tests for Brazil Census Literacy & Illiteracy Rates download module."""

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
    "brazil_literacy_rates_download",
    os.path.join(SCRIPT_DIR, "download.py"),
)
download_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["brazil_literacy_rates_download"] = download_mod
_SPEC.loader.exec_module(download_mod)

FLAGS = download_mod.FLAGS
download_all_years = download_mod.download_all_years
get_robust_session = download_mod.get_robust_session


def _mock_sidra_get(unknown_place: bool = False):
    """Returns a mock session.get side_effect for Tables 9543 and 9542."""

    def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        if "9543" in url:
            if unknown_place:
                resp.json.return_value = [
                    {
                        "NC": "Nível Territorial"
                    },
                    {
                        "NC": "6",
                        "D1C": "9999999",
                        "D1N": "Unknown - XX",
                        "D3N": "2022",
                        "D6C": "100362",
                        "V": "80.0",
                    },
                ]
            else:
                resp.json.return_value = [
                    {
                        "NC": "Nível Territorial"
                    },
                    {
                        "NC": "6",
                        "D1C": "5101837",
                        "D1N": "Boa Esperança do Norte - MT",
                        "D3N": "2022",
                        "D6C": "100362",
                        "V": "91.5",
                    },
                    {
                        "NC": "1",
                        "D1N": "Brasil",
                        "D3N": "2022",
                        "D6C": "100362",
                        "V": "93.0",
                    },
                    {
                        "NC": "1",
                        "D1N": "Brasil",
                        "D3N": "2010",
                        "D6C": "100362",
                        "V": "90.0",
                    },
                ]
        else:
            if unknown_place:
                resp.json.return_value = [
                    {
                        "NC": "Nível Territorial"
                    },
                    {
                        "NC": "1",
                        "D1N": "Brasil",
                        "D3N": "2022",
                        "D6C": "93024",
                        "D7C": "100362",
                        "V": "1000",
                    },
                ]
            else:
                table_9542_rows = [
                    {
                        "NC": "Nível Territorial"
                    },
                    {
                        "NC": "6",
                        "D1C": "5101837",
                        "D1N": "Boa Esperança do Norte - MT",
                        "D3N": "2022",
                        "D6C": "1023",
                        "D7C": "100362",
                        "V": "900",
                    },
                ]
                bra_counts = {
                    ("93024", "100362"): "1000",
                    ("93024", "93086"): "100",
                    ("93024", "93087"): "100",
                    ("93024", "2999"): "200",
                    ("93024", "9482"): "200",
                    ("93024", "9483"): "200",
                    ("93024", "9484"): "200",
                    ("93024", "6613"): "20",
                    ("93024", "6614"): "20",
                    ("93024", "6615"): "20",
                    ("93024", "6616"): "20",
                    ("93024", "6617"): "20",
                    ("93024", "3000"): "100",
                    ("1023", "100362"): "900",
                    ("1023", "93086"): "98",
                    ("1024", "93086"): "2",
                    ("1024", "93087"): "3",
                    ("1024", "2999"): "10",
                    ("1024", "9482"): "10",
                    ("1024", "9483"): "10",
                    ("1024", "9484"): "10",
                    ("1024", "6613"): "2",
                    ("1024", "6614"): "2",
                    ("1024", "6615"): "2",
                    ("1024", "6616"): "2",
                    ("1024", "6617"): "2",
                    ("1024", "3000"): "20",
                }
                for (c59, c287), val in bra_counts.items():
                    table_9542_rows.append({
                        "NC": "1",
                        "D1N": "Brasil",
                        "D3N": "2022",
                        "D6C": c59,
                        "D7C": c287,
                        "V": val,
                    })
                resp.json.return_value = table_9542_rows
        return resp

    return mock_get


class DownloadTest(unittest.TestCase):
    """Unit test suite for Literacy Rates downloader."""

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
        session.get.side_effect = _mock_sidra_get()

        out_csv = os.path.join(self.test_dir, "brazil_literacy_rates.csv")
        saved_file = download_all_years(session=session,
                                        output_file=out_csv,
                                        fallback_to_cached=False)
        self.assertEqual(saved_file, out_csv)
        self.assertTrue(os.path.isfile(saved_file))
        mock_sync.assert_called_once()
        self.assertEqual(
            mock_sync.call_args.args[1],
            os.path.join(self.test_dir, "history",
                         "brazil_literacy_rates_historical.csv"),
        )

        df = pd.read_csv(saved_file)
        self.assertEqual(
            list(df.columns),
            [
                "observationAbout",
                "observationDate",
                "variableMeasured",
                "value",
                "unit",
                "scalingFactor",
            ],
        )
        self.assertEqual(set(df["observationDate"].values), {2022})
        self.assertEqual(set(df["observationAbout"].values),
                         {"dcid:country/BRA"})
        self.assertEqual(len(df), 5)

    def test_fetch_2022_literacy_rates_skips_5101837_and_raises_unknown(self):
        """Tests that unindexed 5101837 is skipped while other unmapped places raise ValueError."""
        session = MagicMock()
        session.get.side_effect = _mock_sidra_get(unknown_place=False)

        rows = download_mod._fetch_2022_literacy_rates_rows(session=session)
        abouts = {r["observationAbout"] for r in rows}
        self.assertEqual(abouts, {"dcid:country/BRA"})
        measured = {r["variableMeasured"] for r in rows}
        for expected_sv in (
                "dcid:Count_Person_20OrMoreYears_Literate_AsAFractionOf_Count_Person_20OrMoreYears",
                "dcid:Count_Person_15To24Years_Illiterate_AsAFractionOf_Count_Person_15To24Years",
                "dcid:Count_Person_25To59Years_Illiterate_AsAFractionOf_Count_Person_25To59Years",
                "dcid:Count_Person_60OrMoreYears_Illiterate_AsAFractionOf_Count_Person_60OrMoreYears",
        ):
            self.assertIn(expected_sv, measured)

        session.get.side_effect = _mock_sidra_get(unknown_place=True)
        with self.assertRaises(ValueError):
            download_mod._fetch_2022_literacy_rates_rows(session=session)

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

    def test_download_fallback_to_cached_preserves_target(self):
        """Tests that network/sync failure preserves existing cached CSV when fallback is enabled."""
        session = MagicMock()
        session.get.side_effect = requests.HTTPError("503 Service Unavailable")

        cached_rates = os.path.join(self.test_dir, "rates.csv")
        with open(cached_rates, "w", encoding="utf-8") as f:
            f.write(
                "observationAbout,observationDate,variableMeasured,value,unit,scalingFactor\n"
                "dcid:country/BRA,2022,dcid:Dummy,0.9,dcs:Percent,100\n")
        rates_hist = os.path.join(self.test_dir, "history",
                                  "brazil_literacy_rates_historical.csv")
        os.makedirs(os.path.dirname(rates_hist), exist_ok=True)
        with open(rates_hist, "w", encoding="utf-8") as f:
            f.write("h\n1\n")

        saved = download_all_years(session=session,
                                   output_file=cached_rates,
                                   fallback_to_cached=True)
        self.assertEqual(saved, cached_rates)
        with open(cached_rates, "r", encoding="utf-8") as f:
            self.assertIn("dcid:Dummy,0.9", f.read())


if __name__ == "__main__":
    unittest.main()
