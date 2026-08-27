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
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import requests

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from statvar_imports.commerce_eda_usaspending.process import process_data, fetch_usaspending_data

class TestProcessUSASpending(unittest.TestCase):
    def setUp(self):
        self.testdata_dir = os.path.join(MODULE_DIR, "testdata")
        self.actual_csv = os.path.join(self.testdata_dir, "Investment_cleaned_actual.csv")
        self.golden_csv = os.path.join(self.testdata_dir, "Investment_cleaned_golden.csv")

        if os.path.exists(self.actual_csv):
            os.remove(self.actual_csv)

    def tearDown(self):
        if os.path.exists(self.actual_csv):
            os.remove(self.actual_csv)

    @patch("requests.Session.post")
    def test_fetch_usaspending_data_success(self, mock_post):
        # Mock a paginated API response (2 pages)
        mock_resp1 = MagicMock()
        mock_resp1.status_code = 200
        mock_resp1.json.return_value = {
            "results": [
                {
                    "Award ID": "123",
                    "Start Date": "2012-10-15",
                    "Award Amount": 100000.0,
                    "Place of Performance State Code": "AL",
                    "CFDA Number": "11.300"
                }
            ],
            "page_metadata": {"hasNext": True}
        }
        
        mock_resp2 = MagicMock()
        mock_resp2.status_code = 200
        mock_resp2.json.return_value = {
            "results": [
                {
                    "Award ID": "456",
                    "Start Date": "2013-05-10",
                    "Award Amount": 50000.0,
                    "Place of Performance State Code": "AL",
                    "CFDA Number": "11.300"
                }
            ],
            "page_metadata": {"hasNext": False}
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
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("Internal Server Error")
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
                "Award Amount": 100000.0
            },
            # Alabama Public Works FY 2013 (start date 2013-05-10 -> FY 2013) - should be aggregated
            {
                "Place of Performance State Code": "AL",
                "CFDA Number": "11.300",
                "Start Date": "2013-05-10",
                "Award Amount": 50000.0
            },
            # Alaska Planning FY 2014
            {
                "Place of Performance State Code": "AK",
                "CFDA Number": "11.302",
                "Start Date": "2014-04-20",
                "Award Amount": 25000.0
            },
            # Invalid state (ignored)
            {
                "Place of Performance State Code": "XX",
                "CFDA Number": "11.300",
                "Start Date": "2013-05-10",
                "Award Amount": 10000.0
            },
            # Invalid CFDA (ignored)
            {
                "Place of Performance State Code": "AL",
                "CFDA Number": "99.999",
                "Start Date": "2013-05-10",
                "Award Amount": 10000.0
            },
            # Out of year range (FY 2011)
            {
                "Place of Performance State Code": "AL",
                "CFDA Number": "11.300",
                "Start Date": "2011-05-10",
                "Award Amount": 10000.0
            }
        ]

        # Run process
        process_data(mock_awards, start_year=2012, end_year=2015, output_path=self.actual_csv)

        self.assertTrue(os.path.exists(self.actual_csv))

        # Compare DataFrames
        df_actual = pd.read_csv(self.actual_csv)
        df_golden = pd.read_csv(self.golden_csv)

        pd.testing.assert_frame_equal(df_actual, df_golden)

if __name__ == "__main__":
    unittest.main()
