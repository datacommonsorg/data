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
"""Unit tests for CDCWonder_NNDSS_InfectiousWeekly preprocess.py."""

import os
import tempfile
import unittest

import pandas as pd
import preprocess


class PreprocessTest(unittest.TestCase):

    def test_get_mmwr_week_start_date(self):
        self.assertEqual(preprocess.get_mmwr_week_start_date(2022, 1), "2022-01-02")
        self.assertEqual(preprocess.get_mmwr_week_start_date(2022, 10), "2022-03-06")
        self.assertIsNone(preprocess.get_mmwr_week_start_date(2022, 0))
        self.assertIsNone(preprocess.get_mmwr_week_start_date(2022, 54))
        self.assertIsNone(preprocess.get_mmwr_week_start_date("bad", 1))

    def test_preprocess_csv_filters_and_ny_sum(self):
        rows = [
            {
                "Reporting Area": "US RESIDENTS",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Chlamydia trachomatis infection",
                "Current week": "500.0",
                "Current week, flag": "-",
            },
            {
                "Reporting Area": "NEW YORK",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Campylobacteriosis",
                "Current week": "20.0",
                "Current week, flag": "-",
            },
            {
                "Reporting Area": "NEW YORK CITY",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Campylobacteriosis",
                "Current week": "30.0",
                "Current week, flag": "-",
            },
            {
                "Reporting Area": "ALABAMA",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Campylobacteriosis",
                "Current week": "5.0",
                "Current week, flag": "N",
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            in_csv = os.path.join(tmpdir, "rows.csv")
            out_csv = os.path.join(tmpdir, "NNDSS_Weekly_Data.csv")
            pd.DataFrame(rows).to_csv(in_csv, index=False)
            out_df = preprocess.preprocess_csv(in_csv, out_csv)

        records = {
            (r["Reporting Area"], r["Label"]): r["Current week"]
            for _, r in out_df.iterrows()
        }
        self.assertEqual(
            records.get(("US RESIDENTS", "Chlamydia trachomatis infection")),
            "500",
        )
        self.assertEqual(records.get(("NEW YORK CITY", "Campylobacteriosis")), "30")
        self.assertEqual(records.get(("NEW YORK", "Campylobacteriosis")), "50")
        self.assertEqual(len(records), 3)


if __name__ == "__main__":
    unittest.main()
