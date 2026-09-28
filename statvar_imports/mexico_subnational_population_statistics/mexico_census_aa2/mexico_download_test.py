# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import unittest
import pandas as pd

# Ensure directory is on sys.path so config and mexico_download are resolved
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

import mexico_download


class MexicoDownloadNormalizeTest(unittest.TestCase):
    """Unit tests for normalize_dataframe in mexico_download."""

    def test_normalize_adm0_standard(self):
        """Test ADM0 normalization: drops ISO3, renames headers, orders columns."""
        input_data = {
            "ISO3": ["MEX"],
            "ADM0_ES": ["Mexico"],
            "ADM0_PCODE": ["MX"],
            "T_TL": [128972439],
            "Year": [2021],
            "M_TL": [63139259],
        }
        df = pd.DataFrame(input_data)
        normalized_df = mexico_download.normalize_dataframe(
            df, "mex_admpop_adm0_2021")

        expected_columns = ["ADM0_EN", "ADM0_PCODE", "Year", "T_TL", "M_TL"]
        self.assertEqual(list(normalized_df.columns), expected_columns)
        self.assertEqual(normalized_df["ADM0_EN"].iloc[0], "Mexico")
        self.assertEqual(normalized_df["T_TL"].iloc[0], 128972439)

    def test_normalize_adm0_with_subnational_columns_and_digit_header(self):
        """Test ADM0 normalization: renames '0' -> ADM0_EN and drops subnational cols."""
        input_data = {
            "0": ["Mexico"],
            "ADM0_PCODE": ["MX"],
            "ADM1_EN": ["Aguascalientes"],
            "ADM1_PCODE": ["MX01"],
            "ADM2_EN": ["Aguascalientes"],
            "ADM2_PCODE": ["MX01001"],
            "Year": [2024],
            "T_TL": [132274416],
        }
        df = pd.DataFrame(input_data)
        normalized_df = mexico_download.normalize_dataframe(df, "adm0_sheet")

        expected_columns = ["ADM0_EN", "ADM0_PCODE", "Year", "T_TL"]
        self.assertEqual(list(normalized_df.columns), expected_columns)
        self.assertNotIn("ADM1_EN", normalized_df.columns)
        self.assertNotIn("ADM1_PCODE", normalized_df.columns)
        self.assertNotIn("ADM2_EN", normalized_df.columns)
        self.assertNotIn("ADM2_PCODE", normalized_df.columns)
        self.assertEqual(normalized_df["ADM0_EN"].iloc[0], "Mexico")

    def test_normalize_adm1(self):
        """Test ADM1 normalization: renames ADM1_ES -> ADM1_EN and orders leading columns."""
        input_data = {
            "ISO3": ["MEX"],
            "ADM1_ES": ["Aguascalientes"],
            "ADM0_ES": ["Mexico"],
            "Year": [2021],
            "ADM0_PCODE": ["MX"],
            "ADM1_PCODE": ["MX01"],
            "F_00_04": [24253],
        }
        df = pd.DataFrame(input_data)
        normalized_df = mexico_download.normalize_dataframe(
            df, "mex_admpop_adm1_2021")

        expected_columns = [
            "ADM0_EN", "ADM0_PCODE", "ADM1_EN", "ADM1_PCODE", "Year", "F_00_04"
        ]
        self.assertEqual(list(normalized_df.columns), expected_columns)
        self.assertNotIn("ISO3", normalized_df.columns)
        self.assertEqual(normalized_df["ADM1_EN"].iloc[0], "Aguascalientes")

    def test_normalize_adm2(self):
        """Test ADM2 normalization: renames ADM2_ES -> ADM2_EN and orders leading columns."""
        input_data = {
            "ISO3": ["MEX"],
            "ADM2_ES": ["Calvillo"],
            "ADM1_ES": ["Aguascalientes"],
            "ADM0_ES": ["Mexico"],
            "Year": [2024],
            "ADM0_PCODE": ["MX"],
            "ADM1_PCODE": ["MX01"],
            "ADM2_PCODE": ["MX01003"],
            "T_TL": [58250],
        }
        df = pd.DataFrame(input_data)
        normalized_df = mexico_download.normalize_dataframe(
            df, "mex_admpop_adm2_2024")

        expected_columns = [
            "ADM0_EN", "ADM0_PCODE", "ADM1_EN", "ADM1_PCODE", "ADM2_EN",
            "ADM2_PCODE", "Year", "T_TL"
        ]
        self.assertEqual(list(normalized_df.columns), expected_columns)
        self.assertEqual(normalized_df["ADM2_EN"].iloc[0], "Calvillo")

    def test_normalize_unrecognized_sheet(self):
        """Test sheet name without adm keyword leaves columns un-reordered."""
        input_data = {
            "ISO3": ["MEX"],
            "ADM0_ES": ["Mexico"],
            "Extra": [123],
        }
        df = pd.DataFrame(input_data)
        normalized_df = mexico_download.normalize_dataframe(df, "Readme_Info")

        expected_columns = ["ADM0_EN", "Extra"]
        self.assertEqual(list(normalized_df.columns), expected_columns)

    def test_normalize_partial_leading_columns(self):
        """Test normalization when some leading columns are missing from the input."""
        input_data = {
            "ADM0_EN": ["Mexico"],
            "T_TL": [100],
        }
        df = pd.DataFrame(input_data)
        normalized_df = mexico_download.normalize_dataframe(
            df, "mex_admpop_adm0")

        expected_columns = ["ADM0_EN", "T_TL"]
        self.assertEqual(list(normalized_df.columns), expected_columns)


if __name__ == "__main__":
    unittest.main()
