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
import sys
import tempfile
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

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
        """Verifies session retry configuration includes 429, 5xx, and 52x codes."""
        session = get_robust_session()
        self.assertIsInstance(session, requests.Session)
        adapter = session.adapters.get("https://")
        self.assertIsNotNone(adapter)
        self.assertEqual(adapter.max_retries.total, 10)
        self.assertIn(429, adapter.max_retries.status_forcelist)
        self.assertIn(500, adapter.max_retries.status_forcelist)
        self.assertIn(503, adapter.max_retries.status_forcelist)
        self.assertIn(520, adapter.max_retries.status_forcelist)

    def test_compute_broad_age_aggregations(self):
        """Tests calculation of 0To14, 15To59, and 60OrMore broad cohorts when all sub-cohorts exist."""
        test_rows = [
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "0 a 4 anos",
                "Sexo": "Total",
                "Populacao": "100",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "5 a 9 anos",
                "Sexo": "Total",
                "Populacao": "150",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "10 a 14 anos",
                "Sexo": "Total",
                "Populacao": "200",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "15 a 19 anos",
                "Sexo": "Total",
                "Populacao": "300",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "20 a 24 anos",
                "Sexo": "Total",
                "Populacao": "100",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "25 a 29 anos",
                "Sexo": "Total",
                "Populacao": "100",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "30 a 34 anos",
                "Sexo": "Total",
                "Populacao": "100",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "35 a 39 anos",
                "Sexo": "Total",
                "Populacao": "100",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "40 a 44 anos",
                "Sexo": "Total",
                "Populacao": "100",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "45 a 49 anos",
                "Sexo": "Total",
                "Populacao": "100",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "50 a 54 anos",
                "Sexo": "Total",
                "Populacao": "100",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "55 a 59 anos",
                "Sexo": "Total",
                "Populacao": "100",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "60 a 64 anos",
                "Sexo": "Total",
                "Populacao": "50",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "65 a 69 anos",
                "Sexo": "Total",
                "Populacao": "40",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "70 a 74 anos",
                "Sexo": "Total",
                "Populacao": "30",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "75 a 79 anos",
                "Sexo": "Total",
                "Populacao": "20",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "80 a 84 anos",
                "Sexo": "Total",
                "Populacao": "15",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "85 a 89 anos",
                "Sexo": "Total",
                "Populacao": "10",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "90 a 94 anos",
                "Sexo": "Total",
                "Populacao": "5",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "95 a 99 anos",
                "Sexo": "Total",
                "Populacao": "3",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "100 anos ou mais",
                "Sexo": "Total",
                "Populacao": "2",
            },
        ]
        aggs = compute_broad_age_aggregations(test_rows, "2022")
        self.assertEqual(len(aggs), 3)
        agg_map = {(r["Idade"], r["Sexo"]): int(r["Populacao"]) for r in aggs}
        self.assertEqual(agg_map.get(("De 0 a 14 anos", "Total")), 450)
        self.assertEqual(agg_map.get(("De 15 a 59 anos", "Total")), 1100)
        self.assertEqual(agg_map.get(("De 60 anos ou mais", "Total")), 175)

    def test_compute_broad_age_aggregations_skips_partial_cohorts(self):
        """Tests that partial sub-cohorts do not emit undercounted broad aggregates."""
        partial_rows = [
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "0 a 4 anos",
                "Sexo": "Total",
                "Populacao": "100",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "60 a 64 anos",
                "Sexo": "Total",
                "Populacao": "50",
            },
            {
                "Ano": "2022",
                "Localidade": "Brazil",
                "Idade": "65 a 69 anos",
                "Sexo": "Total",
                "Populacao": "40",
            },
        ]
        aggs = compute_broad_age_aggregations(partial_rows, "2022")
        self.assertEqual(aggs, [])

    def test_fetch_sidra_data_success(self):
        """Tests successful SIDRA fetch returning parsed JSON rows."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "NC": "Nível"
            },
            {
                "NC": "1",
                "D1N": "Brasil",
                "D3N": "2022",
                "D4N": "Total",
                "D5N": "Total",
                "V": "203080756",
            },
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

    def test_age_code_coverage(self):
        """Verifies TABLE_9514_AGE_CODES covers all required live age cohorts."""
        self.assertIn("93086", download_mod.TABLE_9514_AGE_CODES)
        self.assertEqual(len(download_mod.COHORTS_0_14), 3)
        self.assertEqual(len(download_mod.COHORTS_15_59), 9)
        self.assertTrue(
            set(download_mod.COHORTS_0_14).isdisjoint(
                set(download_mod.COHORTS_15_59)))
        for code in ("93070", "93084", "93085", "93087", "93088", "93089",
                     "93090", "93091", "93092", "93093", "93094"):
            self.assertIn(code, download_mod.TABLE_9514_AGE_CODES)

    @patch.object(download_mod, "sync_historical_csv")
    def test_download_all_years_success(self, mock_sync):
        """Tests download_all_years fetches live 2022+ SIDRA data and syncs history."""
        session = MagicMock()

        def get_mock_response(url, **kwargs):
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            cohorts = [
                ("Total", "200000"),
                ("0 a 4 anos", "1000"),
                ("5 a 9 anos", "2000"),
                ("10 a 14 anos", "3000"),
                ("15 a 19 anos", "4000"),
                ("20 a 24 anos", "5000"),
                ("25 a 29 anos", "5000"),
                ("30 a 34 anos", "5000"),
                ("35 a 39 anos", "5000"),
                ("40 a 44 anos", "5000"),
                ("45 a 49 anos", "5000"),
                ("50 a 54 anos", "5000"),
                ("55 a 59 anos", "5000"),
                ("60 a 64 anos", "4000"),
                ("65 a 69 anos", "3500"),
                ("70 a 74 anos", "3000"),
                ("75 a 79 anos", "2500"),
                ("80 a 84 anos", "1500"),
                ("85 a 89 anos", "1000"),
                ("90 a 94 anos", "500"),
                ("95 a 99 anos", "250"),
                ("100 anos ou mais", "100"),
            ]
            rows = [{"NC": "Header"}]
            for idade, val in cohorts:
                rows.append({
                    "NC": "1",
                    "D1N": "Brasil",
                    "D3N": "2022",
                    "D4N": "Total",
                    "D5N": idade,
                    "V": val,
                })
            rows.append({
                "NC": "6",
                "D1C": "3550308",
                "D1N": "São Paulo - SP",
                "D3N": "2022",
                "D4N": "Total",
                "D5N": "15 a 19 anos",
                "V": "900000",
            })
            resp.json.return_value = rows
            return resp

        session.get.side_effect = get_mock_response

        out_csv = os.path.join(self.test_dir, "output.csv")
        saved_file = download_all_years(session=session,
                                        output_file=out_csv,
                                        fallback_to_cached=False)
        self.assertTrue(os.path.isfile(saved_file))
        mock_sync.assert_called_once()

        df = pd.read_csv(saved_file)
        self.assertEqual(set(df["Ano"].astype(str).values), {"2022"})
        self.assertIn("De 0 a 14 anos", df["Idade"].values)
        self.assertIn("De 60 anos ou mais", df["Idade"].values)
        self.assertIn("3550308", df["Localidade"].astype(str).values)

    def test_download_all_years_fallback_to_cached(self):
        """Tests that fallback succeeds when both cached CSV and history exist."""
        session = MagicMock()
        session.get.side_effect = requests.HTTPError("503 Service Unavailable")

        cached_csv = os.path.join(self.test_dir, "cached.csv")
        with open(cached_csv, "w", encoding="utf-8") as f:
            f.write(
                "Ano,Localidade,Idade,Sexo,Populacao\n2022,Brazil,Total,Total,100\n"
            )
        hist_dir = os.path.join(self.test_dir, "history")
        os.makedirs(hist_dir, exist_ok=True)
        with open(os.path.join(
                hist_dir, "brazil_population_by_age_and_sex_historical.csv"),
                  "w",
                  encoding="utf-8") as f:
            f.write("h\n1\n")

        saved = download_all_years(session=session,
                                   output_file=cached_csv,
                                   fallback_to_cached=True)
        self.assertEqual(saved, cached_csv)
        self.assertTrue(os.path.isfile(saved))


if __name__ == "__main__":
    unittest.main()
