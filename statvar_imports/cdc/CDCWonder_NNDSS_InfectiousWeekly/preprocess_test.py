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
import sys
import tempfile
import unittest

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preprocess  # noqa: E402


class PreprocessTest(unittest.TestCase):

    def test_get_mmwr_week_start_date(self):
        self.assertEqual(preprocess.get_mmwr_week_start_date(2022, 1),
                         "2022-01-02")
        self.assertEqual(preprocess.get_mmwr_week_start_date(2022, 10),
                         "2022-03-06")
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
        self.assertEqual(records.get(("NEW YORK CITY", "Campylobacteriosis")),
                         "30")
        self.assertEqual(records.get(("NEW YORK", "Campylobacteriosis")), "50")
        self.assertEqual(len(records), 3)

    def test_preprocess_csv_header_only_missing_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            in_csv = os.path.join(tmpdir, "rows.csv")
            out_csv = os.path.join(tmpdir, "NNDSS_Weekly_Data.csv")
            with open(in_csv, "w", encoding="utf-8") as f:
                f.write("Reporting Area,Current MMWR Year\n")
            with self.assertRaises(KeyError):
                preprocess.preprocess_csv(in_csv, out_csv)

    def test_normalize_output_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "nndss_weekly_output.csv")
            tmcf_path = os.path.join(tmpdir, "nndss_weekly_output.tmcf")
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write("observationDate,observationAbout,value,variableMeasured\n"
                        "2024-03-03,country/USA,3,StatVar1\n")
            with open(tmcf_path, "w", encoding="utf-8") as f:
                f.write("Node: E:nndss_weekly_output->E0\n"
                        "observationPeriod: P1W\n"
                        "typeOf: dcs:StatVarObservation\n")
            preprocess.normalize_output_files(output_dir=tmpdir)
            with open(csv_path, "r", encoding="utf-8") as f:
                csv_text = f.read()
            with open(tmcf_path, "r", encoding="utf-8") as f:
                tmcf_text = f.read()
            self.assertIn("observationPeriod", csv_text.splitlines()[0])
            self.assertIn("2024-03-03,country/USA,3,StatVar1,P1W", csv_text)
            self.assertIn(
                "observationPeriod: C:nndss_weekly_output->observationPeriod",
                tmcf_text,
            )


if __name__ == "__main__":
    unittest.main()
