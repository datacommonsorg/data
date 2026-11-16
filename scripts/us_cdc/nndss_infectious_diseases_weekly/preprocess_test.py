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

    def test_apply_resident_suffix(self):
        self.assertEqual(
            preprocess.apply_resident_suffix(
                "Count_MedicalConditionIncident_ConditionChlamydia",
                "USResident",
            ),
            "Count_MedicalConditionIncident_ConditionChlamydia_USResident",
        )
        self.assertEqual(
            preprocess.apply_resident_suffix(
                "Count_MedicalConditionIncident_5_LessYears_ConditionHaemophilusInfluenzae_InvasiveDisease_NonSerotypeB",
                "USResident",
            ),
            "Count_MedicalConditionIncident_5_LessYears_ConditionHaemophilusInfluenzae_InvasiveDisease_USResident_NonSerotypeB",
        )
        self.assertEqual(
            preprocess.apply_resident_suffix(
                "Count_MedicalConditionIncident_ConditionMeningococcalMeningitis_SerogroupB",
                "NonUSResident",
            ),
            "Count_MedicalConditionIncident_ConditionMeningococcalMeningitis_NonUSResident_SerogroupB",
        )

    def test_process_x9gk_csv_filters_and_ny_sum(self):
        rows = [
            # Valid Current week row for US RESIDENTS
            {
                "Reporting Area": "US RESIDENTS",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Chlamydia trachomatis infection",
                "Current week": "500.0",
                "Current week, flag": "-",
            },
            # NY (ex-NYC) + NYC should emit geoId/3651000=30 and geoId/36=50
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
            # Suppressed flag N should be skipped
            {
                "Reporting Area": "ALABAMA",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Campylobacteriosis",
                "Current week": "5.0",
                "Current week, flag": "N",
            },
            # Rabies, Animal and non-HPS Hantavirus must be ignored
            {
                "Reporting Area": "ALABAMA",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Rabies, Animal",
                "Current week": "4.0",
                "Current week, flag": "-",
            },
            {
                "Reporting Area": "ALABAMA",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Hantavirus infection, non-hantavirus pulmonary syndrome",
                "Current week": "1.0",
                "Current week, flag": "-",
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "input.csv")
            pd.DataFrame(rows).to_csv(csv_path, index=False)
            out_df = preprocess.process_x9gk_csv(csv_path)

        records = {
            (r["observationAbout"], r["variableMeasured"]): r["value"]
            for _, r in out_df.iterrows()
        }
        self.assertEqual(
            records.get(
                (
                    "country/USA",
                    "Count_MedicalConditionIncident_ConditionChlamydia_USResident",
                )
            ),
            "500",
        )
        self.assertEqual(
            records.get(
                ("geoId/3651000", "Count_MedicalConditionIncident_ConditionCampylobacteriosis")
            ),
            "30",
        )
        self.assertEqual(
            records.get(
                ("geoId/36", "Count_MedicalConditionIncident_ConditionCampylobacteriosis")
            ),
            "50",
        )
        self.assertEqual(len(records), 3)


if __name__ == "__main__":
    unittest.main()
