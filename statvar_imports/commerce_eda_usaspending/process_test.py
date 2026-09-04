# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import requests

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from statvar_imports.commerce_eda_usaspending.process import fetch_usaspending_data, process_data


class TestProcessUSASpending(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_csv = os.path.join(self.temp_dir.name,
                                       "Investment_cleaned.csv")

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("requests.Session.post")
    def test_fetch_usaspending_data_success(self, mock_post):
        # Mock a paginated API response (2 pages)
        mock_resp1 = MagicMock()
        mock_resp1.status_code = 200
        mock_resp1.json.return_value = {
            "results": [{
                "Award ID": "123",
                "Start Date": "2012-10-15",
                "Award Amount": 100000.0,
                "Place of Performance State Code": "AL",
                "CFDA Number": "11.300",
            }],
            "page_metadata": {
                "hasNext": True
            },
        }

        mock_resp2 = MagicMock()
        mock_resp2.status_code = 200
        mock_resp2.json.return_value = {
            "results": [{
                "Award ID": "456",
                "Start Date": "2013-05-10",
                "Award Amount": 50000.0,
                "Place of Performance State Code": "AL",
                "CFDA Number": "11.300",
            }],
            "page_metadata": {
                "hasNext": False
            },
        }

        mock_post.side_effect = [mock_resp1, mock_resp2]

        awards = fetch_usaspending_data(start_year=2012, end_year=2014)

        self.assertEqual(len(awards), 2)
        self.assertEqual(awards[0]["Award ID"], "123")
        self.assertEqual(awards[1]["Award ID"], "456")
        self.assertEqual(mock_post.call_count, 2)

    @patch("requests.Session.post")
    def test_fetch_usaspending_data_failure(self, mock_post):
        # Mock API error (non-200)
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Internal Server Error")
        mock_post.return_value = mock_resp

        with self.assertRaises(requests.exceptions.HTTPError):
            fetch_usaspending_data(start_year=2012, end_year=2014)

    def test_process_data(self):
        # Mock API award records
        mock_awards = [
            # Alabama Public Works FY 2013 (start date 2012-10-15 -> FY 2013)
            {
                "Place of Performance State Code": "AL",
                "CFDA Number": "11.300",
                "Start Date": "2012-10-15",
                "Award Amount": 100000.0,
            },
            # Alabama Public Works FY 2013 (start date 2013-05-10 -> FY 2013) - should be aggregated
            {
                "Place of Performance State Code": "AL",
                "CFDA Number": "11.300",
                "Start Date": "2013-05-10",
                "Award Amount": 50000.0,
            },
            # Alaska Planning FY 2014
            {
                "Place of Performance State Code": "AK",
                "CFDA Number": "11.302",
                "Start Date": "2014-04-20",
                "Award Amount": 25000.0,
            },
            # Invalid state (ignored)
            {
                "Place of Performance State Code": "XX",
                "CFDA Number": "11.300",
                "Start Date": "2013-05-10",
                "Award Amount": 10000.0,
            },
            # Invalid CFDA (ignored)
            {
                "Place of Performance State Code": "AL",
                "CFDA Number": "99.999",
                "Start Date": "2013-05-10",
                "Award Amount": 10000.0,
            },
            # Out of year range (FY 2011)
            {
                "Place of Performance State Code": "AL",
                "CFDA Number": "11.300",
                "Start Date": "2011-05-10",
                "Award Amount": 10000.0,
            },
        ]

        # Run process
        process_data(
            mock_awards,
            start_year=2012,
            end_year=2015,
            output_path=self.output_csv,
        )

        self.assertTrue(os.path.exists(self.output_csv))

        # Compare DataFrames
        df_actual = pd.read_csv(self.output_csv)
        df_expected = pd.DataFrame({
            "Place": ["Alabama", "Alabama", "Alaska", "Alaska"],
            "State or Territory / EDA Program": [
                "Total",
                "Public Works",
                "Total",
                "Planning",
            ],
            "Year": [2013, 2013, 2014, 2014],
            "Value": [150000, 150000, 25000, 25000],
        })

        pd.testing.assert_frame_equal(df_actual, df_expected)

    def test_new_programs(self):
        mock_awards = [
            # CFDA 11.313 -> Trade Adjustment Assistance for Firms
            {
                "Place of Performance State Code": "CA",
                "CFDA Number": "11.313",
                "Start Date": "2020-01-15",
                "Award Amount": 10000.0,
            },
            # CFDA 11.312 -> Research and National Technical Assistance
            {
                "Place of Performance State Code": "CA",
                "CFDA Number": "11.312",
                "Start Date": "2020-02-15",
                "Award Amount": 20000.0,
            },
            # CFDA 11.300 -> Public Works
            {
                "Place of Performance State Code": "CA",
                "CFDA Number": "11.300",
                "Start Date": "2020-03-15",
                "Award Amount": 30000.0,
            },
            # CFDA 11.024 -> Regional Innovation Strategies
            {
                "Place of Performance State Code": "CA",
                "CFDA Number": "11.024",
                "Start Date": "2020-04-15",
                "Award Amount": 15000.0,
            },
        ]

        process_data(
            mock_awards,
            start_year=2019,
            end_year=2021,
            output_path=self.output_csv,
        )

        self.assertTrue(os.path.exists(self.output_csv))
        df_actual = pd.read_csv(self.output_csv)
        df_expected = pd.DataFrame({
            "Place": [
                "California", "California", "California", "California",
                "California"
            ],
            "State or Territory / EDA Program": [
                "Total",
                "Public Works",
                "Regional Innovation Strategies",
                "Research and National Technical Assistance",
                "Trade Adjustment Assistance for Firms",
            ],
            "Year": [2020, 2020, 2020, 2020, 2020],
            "Value": [75000, 30000, 15000, 20000, 10000],
        })
        pd.testing.assert_frame_equal(df_actual, df_expected)

    def test_new_territories(self):
        mock_awards = [
            # Palau (PW)
            {
                "Place of Performance State Code": "PW",
                "CFDA Number": "11.302",
                "Start Date": "2021-05-01",
                "Award Amount": 50000.0,
            },
            # Marshall Islands (MH)
            {
                "Place of Performance State Code": "MH",
                "CFDA Number": "11.307",
                "Start Date": "2021-06-01",
                "Award Amount": 75000.0,
            },
        ]

        process_data(
            mock_awards,
            start_year=2020,
            end_year=2022,
            output_path=self.output_csv,
        )

        self.assertTrue(os.path.exists(self.output_csv))
        df_actual = pd.read_csv(self.output_csv)
        df_expected = pd.DataFrame({
            "Place": [
                "Marshall Islands",
                "Marshall Islands",
                "Palau",
                "Palau",
            ],
            "State or Territory / EDA Program": [
                "Total",
                "Economic Adjustment Assistance",
                "Total",
                "Planning",
            ],
            "Year": [2021, 2021, 2021, 2021],
            "Value": [75000, 75000, 50000, 50000],
        })
        pd.testing.assert_frame_equal(df_actual, df_expected)

    def test_rounding(self):
        mock_awards = [
            # 1234.6 rounds to 1235
            {
                "Place of Performance State Code": "TX",
                "CFDA Number": "11.300",
                "Start Date": "2022-01-10",
                "Award Amount": 1234.6,
            },
            # 5678.4 rounds to 5678
            {
                "Place of Performance State Code": "TX",
                "CFDA Number": "11.302",
                "Start Date": "2022-02-10",
                "Award Amount": 5678.4,
            },
        ]

        process_data(
            mock_awards,
            start_year=2021,
            end_year=2023,
            output_path=self.output_csv,
        )

        self.assertTrue(os.path.exists(self.output_csv))
        df_actual = pd.read_csv(self.output_csv)
        # Total is 1234.6 + 5678.4 = 6913.0 -> 6913
        df_expected = pd.DataFrame({
            "Place": ["Texas", "Texas", "Texas"],
            "State or Territory / EDA Program":
            ["Total", "Planning", "Public Works"],
            "Year": [2022, 2022, 2022],
            "Value": [6913, 5678, 1235],
        })
        pd.testing.assert_frame_equal(df_actual, df_expected)

    def test_empty_awards_guard(self):
        # Empty list of awards
        process_data([],
                     start_year=2012,
                     end_year=2024,
                     output_path=self.output_csv)
        self.assertFalse(os.path.exists(self.output_csv))

        # Awards with no matching/valid records
        invalid_awards = [{
            "Place of Performance State Code": "UNKNOWN",
            "CFDA Number": "00.000",
            "Start Date": "1990-01-01",
            "Award Amount": 1000.0,
        }]
        process_data(
            invalid_awards,
            start_year=2012,
            end_year=2024,
            output_path=self.output_csv,
        )
        self.assertFalse(os.path.exists(self.output_csv))

    def test_date_parsing_and_amount_guards(self):
        mock_awards = [
            # Malformed date string (should be safely skipped)
            {
                "Place of Performance State Code": "NY",
                "CFDA Number": "11.300",
                "Start Date": "invalid-date",
                "Award Amount": 50000.0,
            },
            # Missing / None date string (should be safely skipped)
            {
                "Place of Performance State Code": "NY",
                "CFDA Number": "11.300",
                "Start Date": None,
                "Award Amount": 50000.0,
            },
            # None Award Amount (should default to 0.0 and be dropped by positive amount filter)
            {
                "Place of Performance State Code": "NY",
                "CFDA Number": "11.300",
                "Start Date": "2022-05-15",
                "Award Amount": None,
            },
            # Valid award
            {
                "Place of Performance State Code": "NY",
                "CFDA Number": "11.300",
                "Start Date": "2022-05-15",
                "Award Amount": 120000.0,
            },
        ]
        process_data(
            mock_awards,
            start_year=2021,
            end_year=2023,
            output_path=self.output_csv,
        )
        self.assertTrue(os.path.exists(self.output_csv))
        df_actual = pd.read_csv(self.output_csv)
        df_expected = pd.DataFrame({
            "Place": ["New York", "New York"],
            "State or Territory / EDA Program": ["Total", "Public Works"],
            "Year": [2022, 2022],
            "Value": [120000, 120000],
        })
        pd.testing.assert_frame_equal(df_actual, df_expected)


if __name__ == "__main__":
    unittest.main()
