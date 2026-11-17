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
"""Unit tests for merge_historical.py."""

import os
import tempfile
import unittest

import merge_historical
import pandas as pd


class MergeHistoricalTest(unittest.TestCase):

    def test_load_historical_filters_and_reindexes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hist_csv = os.path.join(tmpdir, "hist.csv")
            # Intentionally shuffled column order + 2022 row that should be filtered out
            df = pd.DataFrame(
                [
                    {
                        "value": "5",
                        "variableMeasured": "Count_MedicalConditionIncident_ConditionAnthrax",
                        "observationAbout": "geoId/01",
                        "observationDate": "2021-12-26",
                        "observationPeriod": "P1W",
                        "measurementMethod": "dcs:CDC_NNDSS_Diseases_WeeklyTables",
                    },
                    {
                        "value": "9",
                        "variableMeasured": "Count_MedicalConditionIncident_ConditionAnthrax",
                        "observationAbout": "geoId/01",
                        "observationDate": "2022-01-02",
                        "observationPeriod": "P1W",
                        "measurementMethod": "dcs:CDC_NNDSS_Diseases_WeeklyTables",
                    },
                ]
            )
            df.to_csv(hist_csv, index=False)

            loaded = merge_historical.load_historical(hist_csv, "", "")
            self.assertEqual(list(loaded.columns), merge_historical.OUTPUT_COLUMNS)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded.iloc[0]["observationDate"], "2021-12-26")

    def test_merge_outputs_strips_prefixes_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            proc_csv = os.path.join(tmpdir, "proc.csv")
            out_dir = os.path.join(tmpdir, "out")

            hist_df = pd.DataFrame(
                [
                    {
                        "observationDate": "2021-12-26",
                        "observationAbout": "geoId/01",
                        "observationPeriod": "P1W",
                        "variableMeasured": "Count_MedicalConditionIncident_ConditionAnthrax",
                        "value": "5",
                        "measurementMethod": "dcs:CDC_NNDSS_Diseases_WeeklyTables",
                    },
                    {
                        "observationDate": "2022-01-02",
                        "observationAbout": "geoId/01",
                        "observationPeriod": "P1W",
                        "variableMeasured": "Count_MedicalConditionIncident_ConditionAnthrax",
                        "value": "1",
                        "measurementMethod": "dcs:CDC_NNDSS_Diseases_WeeklyTables",
                    },
                ]
            )
            pd.DataFrame(
                [
                    {
                        "observationDate": "2022-01-02",
                        "observationAbout": "dcid:geoId/01",
                        "variableMeasured": "dcs:Count_MedicalConditionIncident_ConditionAnthrax",
                        "value": "2",
                    }
                ]
            ).to_csv(proc_csv, index=False)

            combined = merge_historical.merge_outputs(hist_df, proc_csv, out_dir)
            self.assertEqual(len(combined), 2)
            row_2022 = combined[combined["observationDate"] == "2022-01-02"].iloc[0]
            self.assertEqual(row_2022["observationAbout"], "geoId/01")
            self.assertEqual(
                row_2022["variableMeasured"],
                "Count_MedicalConditionIncident_ConditionAnthrax",
            )
            self.assertEqual(row_2022["observationPeriod"], "P1W")
            self.assertEqual(
                row_2022["measurementMethod"],
                "dcs:CDC_NNDSS_Diseases_WeeklyTables",
            )
            self.assertEqual(row_2022["value"], "2")
            self.assertTrue(
                os.path.exists(os.path.join(out_dir, "cdc_nndss_weekly_tables.tmcf"))
            )


if __name__ == "__main__":
    unittest.main()
