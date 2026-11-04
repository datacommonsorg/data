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
"""Unit tests for download.py."""

import os
import sys
import tempfile
import unittest

import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import download


class DownloadTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.orig_cwd = os.getcwd()
        self.temp_dir = tempfile.TemporaryDirectory()
        os.chdir(self.temp_dir.name)
        os.makedirs("input", exist_ok=True)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        self.temp_dir.cleanup()
        super().tearDown()

    def _build_monthly_prices_sheet(self):
        rows = [
            [None, None, None],
            [None, None, None],
            [None, None, None],
            [None, None, None],
            [None, "Crude oil, average", "Coal, Australian"],
            [None, "($/bbl)", "($/mt)"],
            ["1960M01", 1.63, "..."],
            ["1960M02", 1.63, 12.5],
        ]
        return pd.DataFrame(rows)

    def _build_monthly_indices_sheet(self):
        rows = [
            [None, None, None],
            [None, None, None],
            [None, None, None],
            [None, None, None],
            [None, None, None],
            [None, "Energy", None],
            [None, "Index", "Non-Energy"],
            [None, "(2010=100)", "Index"],
            [None, None, "(2010=100)"],
            ["1960M01", 2.05, ".."],
            ["1960M02", 2.10, 15.3],
        ]
        return pd.DataFrame(rows)

    def _build_annual_indices_sheet(self):
        rows = [
            [None, None, None],
            [None, None, None],
            [None, None, None],
            [None, None, None],
            [None, None, None],
            [None, "Energy", None],
            [None, "Index", "Agriculture"],
            [None, "(2010=100)", "Index"],
            [None, None, "(2010=100)"],
            [1960, 2.05, "…"],
            [1961, 2.10, 18.4],
        ]
        return pd.DataFrame(rows)

    def _build_annual_prices_sheet(self):
        # Column 0 contains only floats/NaNs so pandas infers float64 dtype,
        # verifying that process_xlsx casts to object before assigning "Year".
        rows = [
            [float("nan"), None, None],
            [float("nan"), None, None],
            [float("nan"), None, None],
            [float("nan"), None, None],
            [float("nan"), "Nominal US Dollars", None],
            [float("nan"), "($/bbl)", "($/mt)"],
            [float("nan"), "Crude oil, average", "Coal, Australian"],
            [1960.0, 1.63, "..."],
            [1961.0, 1.57, 14.2],
        ]
        return pd.DataFrame(rows)

    def test_process_xlsx_all_six_sheets(self):
        xlsx_path = os.path.join(self.temp_dir.name, "test_commodity.xlsx")
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            self._build_monthly_prices_sheet().to_excel(
                writer, sheet_name="Monthly Prices", index=False, header=False)
            self._build_monthly_indices_sheet().to_excel(
                writer, sheet_name="Monthly Indices", index=False, header=False)
            self._build_annual_indices_sheet().to_excel(
                writer,
                sheet_name="Annual Indices (Nominal)",
                index=False,
                header=False)
            self._build_annual_indices_sheet().to_excel(
                writer,
                sheet_name="Annual Indices (Real)",
                index=False,
                header=False)
            self._build_annual_prices_sheet().to_excel(
                writer,
                sheet_name="Annual Prices (Nominal)",
                index=False,
                header=False)
            self._build_annual_prices_sheet().to_excel(
                writer,
                sheet_name="Annual Prices (Real)",
                index=False,
                header=False)

        download.process_xlsx(xlsx_path)

        # 1. Monthly Prices
        mp_df = pd.read_csv(os.path.join("input", "monthly_prices_data.csv"))
        self.assertEqual(
            list(mp_df.columns),
            ["Year", "Month", "Crude oil, average", "Coal, Australian"])
        self.assertEqual(mp_df.iloc[0]["Crude oil, average"], "($/bbl)")
        self.assertEqual(
            str(mp_df.iloc[1]["Year"]),
            "1960.0" if "." in str(mp_df.iloc[1]["Year"]) else "1960")
        self.assertEqual(mp_df.iloc[1]["Month"], "M01")
        self.assertTrue(pd.isna(mp_df.iloc[1]["Coal, Australian"]))

        # 2. Monthly Indices
        mi_df = pd.read_csv(os.path.join("input", "monthly_indices_data.csv"))
        self.assertEqual(list(mi_df.columns), [
            "Year", "Month", "Energy Index (2010=100)",
            "Non-Energy Index (2010=100)"
        ])
        self.assertEqual(int(mi_df.iloc[0]["Year"]), 1960)
        self.assertEqual(mi_df.iloc[0]["Month"], "M01")
        self.assertTrue(pd.isna(mi_df.iloc[0]["Non-Energy Index (2010=100)"]))
        self.assertAlmostEqual(
            float(mi_df.iloc[1]["Non-Energy Index (2010=100)"]), 15.3)

        # 3 & 4. Annual Indices (Nominal & Real)
        for csv_name in [
                "annual_indices_nominal_data.csv",
                "annual_indices_real_data.csv"
        ]:
            ai_df = pd.read_csv(os.path.join("input", csv_name))
            self.assertEqual(list(ai_df.columns), [
                "Year", "Energy Index (2010=100)",
                "Agriculture Index (2010=100)"
            ])
            self.assertEqual(int(ai_df.iloc[0]["Year"]), 1960)
            self.assertTrue(
                pd.isna(ai_df.iloc[0]["Agriculture Index (2010=100)"]))
            self.assertAlmostEqual(
                float(ai_df.iloc[1]["Agriculture Index (2010=100)"]), 18.4)

        # 5 & 6. Annual Prices (Nominal & Real)
        for csv_name in [
                "annual_prices_nominal_data.csv", "annual_prices_real_data.csv"
        ]:
            ap_df = pd.read_csv(os.path.join("input", csv_name), header=None)
            self.assertEqual(ap_df.iloc[6, 0], "Year")
            self.assertEqual(ap_df.iloc[6, 1], "Crude oil, average")
            self.assertTrue(pd.isna(ap_df.iloc[7, 2]))
            self.assertAlmostEqual(float(ap_df.iloc[8, 2]), 14.2)


if __name__ == "__main__":
    unittest.main()
