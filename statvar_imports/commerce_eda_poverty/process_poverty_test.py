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

"""Unit tests for process_poverty.py."""

import io
import os
import sys
import tempfile
import unittest
import pandas as pd

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from statvar_imports.commerce_eda_poverty.process_poverty import (
    clean_geoid,
    preprocess_poverty,
    resolve_source_file_path,
)


def _create_mock_excel_file(filepath, rows, description_row=True):
    """Creates a .xlsx workbook mimicking the CDFI PPC Excel file."""
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        data = []
        if description_row:
            data.append(["Persistent Poverty Counties (PPCs) description header", "", "", "", ""])
        data.append(["County FIPS", "County, State", "1990 Poverty %", "2000 Poverty %", "2016-2020 Poverty %"])
        data.extend(rows)
        pd.DataFrame(data).to_excel(writer, sheet_name="Sheet1", index=False, header=False)


class TestProcessPoverty(unittest.TestCase):

    def test_clean_geoid(self):
        # 5-digit strings
        self.assertEqual(clean_geoid("01001"), "01001")
        self.assertEqual(clean_geoid("72143"), "72143")
        self.assertEqual(clean_geoid("78010"), "78010")

        # 4-digit zero-padding (e.g. Alabama 01005, Alaska 02090)
        self.assertEqual(clean_geoid("1005"), "01005")
        self.assertEqual(clean_geoid("2090"), "02090")

        # 2-digit Island Territories
        self.assertEqual(clean_geoid("60"), "60")
        self.assertEqual(clean_geoid("66"), "66")
        self.assertEqual(clean_geoid("69"), "69")
        self.assertEqual(clean_geoid("78"), "78")
        self.assertEqual(clean_geoid(60), "60")

        # Float strings
        self.assertEqual(clean_geoid("1001.0"), "01001")
        self.assertEqual(clean_geoid("01001.0"), "01001")
        self.assertEqual(clean_geoid("1001.00"), "01001")

        # Numeric floats and ints
        self.assertEqual(clean_geoid(1001.0), "01001")
        self.assertEqual(clean_geoid(2090), "02090")

        # State summary FIPS ending in 000 must return None
        self.assertIsNone(clean_geoid("01000"))
        self.assertIsNone(clean_geoid("1000"))
        self.assertIsNone(clean_geoid("72000"))
        self.assertIsNone(clean_geoid("01"))

        # Invalid cases returning None
        self.assertIsNone(clean_geoid("1001.5"))
        self.assertIsNone(clean_geoid("-1001.0"))
        self.assertIsNone(clean_geoid(-1001.0))
        self.assertIsNone(clean_geoid("abc"))
        self.assertIsNone(clean_geoid(""))
        self.assertIsNone(clean_geoid(None))
        self.assertIsNone(clean_geoid("00100"))
        self.assertIsNone(clean_geoid("0100"))
        self.assertIsNone(clean_geoid("99001"))
        self.assertIsNone(clean_geoid("123456"))

    def test_resolve_source_file_path_specified(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = os.path.join(tmpdir, "custom.csv")
            with open(sample_file, "w") as f:
                f.write("a,b\n1,2\n")
            self.assertEqual(resolve_source_file_path(sample_file), sample_file)

    def test_resolve_source_file_path_missing_raises(self):
        with self.assertRaises(FileNotFoundError):
            resolve_source_file_path("/non/existent/path/poverty.xlsx")

    def test_preprocess_poverty_from_excel(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            xlsx_path = os.path.join(tmpdir, "source.xlsx")
            cleaned_path = os.path.join(tmpdir, "cleaned.csv")

            sample_rows = [
                ["01005", "Barbour County, Alabama", "25.2", "26.8", "28.6"],
                ["01011", "Bullock County, Alabama", "36.5", "33.5", "29.5"],
                ["60", "American Samoa", "57.8", "61.0", "54.6"],
                ["99999", "Invalid County", "10.0", "10.0", "10.0"],  # Invalid GEOID -> dropped
                ["01000", "Alabama State", "15.0", "15.0", "15.0"],   # State summary XX000 -> dropped
            ]
            _create_mock_excel_file(xlsx_path, sample_rows, description_row=True)

            preprocess_poverty(src_path=xlsx_path, dst_path=cleaned_path, min_county_count=3)
            self.assertTrue(os.path.exists(cleaned_path))

            df = pd.read_csv(cleaned_path, dtype={"GEOID": str})
            self.assertEqual(len(df), 3)
            self.assertListEqual(
                list(df.columns),
                ["GEOID", "poverty_rate_1990", "poverty_rate_2000", "poverty_rate_2020"],
            )
            self.assertIn("60", df["GEOID"].values)
            self.assertIn("01005", df["GEOID"].values)
            self.assertNotIn("99999", df["GEOID"].values)
            self.assertNotIn("01000", df["GEOID"].values)

    def test_preprocess_poverty_from_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "source.csv")
            cleaned_path = os.path.join(tmpdir, "cleaned.csv")

            csv_content = (
                "County FIPS,County, State,1990 Poverty %,2000 Poverty %,2016-2020 Poverty %\n"
                "01005,Barbour County, Alabama,25.2,26.8,28.6\n"
                "01011,Bullock County, Alabama,36.5,33.5,29.5\n"
                "60,American Samoa,57.8,61.0,54.6\n"
            )
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write(csv_content)

            preprocess_poverty(src_path=csv_path, dst_path=cleaned_path, min_county_count=3)
            self.assertTrue(os.path.exists(cleaned_path))

            df = pd.read_csv(cleaned_path, dtype={"GEOID": str})
            self.assertEqual(len(df), 3)
            self.assertListEqual(
                list(df.columns),
                ["GEOID", "poverty_rate_1990", "poverty_rate_2000", "poverty_rate_2020"],
            )

    def test_preprocess_poverty_with_test_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = os.path.join(MODULE_DIR, "test_data", "Poverty_input.csv")
            expected_path = os.path.join(MODULE_DIR, "test_data", "Poverty_expected_output.csv")
            actual_csv = os.path.join(tmpdir, "Poverty_cleaned.csv")

            preprocess_poverty(src_path=fixture_path, dst_path=actual_csv, min_county_count=10)

            self.assertTrue(os.path.exists(actual_csv))
            df_actual = pd.read_csv(actual_csv, dtype={"GEOID": str})
            df_expected = pd.read_csv(expected_path, dtype={"GEOID": str})
            pd.testing.assert_frame_equal(df_actual, df_expected)

    def test_preprocess_poverty_out_of_bounds_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "out_of_bounds.csv")
            cleaned_path = os.path.join(tmpdir, "cleaned.csv")

            csv_content = (
                "County FIPS,County, State,1990 Poverty %,2000 Poverty %,2016-2020 Poverty %\n"
                "01005,Barbour County, Alabama,-5.0,26.8,150.0\n"
                "01011,Bullock County, Alabama,36.5,33.5,29.5\n"
            )
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write(csv_content)

            preprocess_poverty(src_path=csv_path, dst_path=cleaned_path, min_county_count=2)
            df = pd.read_csv(cleaned_path, dtype={"GEOID": str})

            # Row 0 (01005): -5.0 -> NaN, 150.0 -> NaN, 26.8 -> retained
            row_01005 = df[df["GEOID"] == "01005"].iloc[0]
            self.assertTrue(pd.isna(row_01005["poverty_rate_1990"]))
            self.assertEqual(row_01005["poverty_rate_2000"], 26.8)
            self.assertTrue(pd.isna(row_01005["poverty_rate_2020"]))

    def test_preprocess_poverty_empty_or_missing_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_csv = os.path.join(tmpdir, "missing.csv")
            dst_csv = os.path.join(tmpdir, "out.csv")

            with self.assertRaises(ValueError):
                preprocess_poverty(src_path=missing_csv, dst_path=dst_csv)

            empty_csv = os.path.join(tmpdir, "empty.csv")
            with open(empty_csv, "w", encoding="utf-8") as f:
                f.write("")

            with self.assertRaises(ValueError):
                preprocess_poverty(src_path=empty_csv, dst_path=dst_csv)

    def test_preprocess_poverty_sanity_threshold_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "few_rows.csv")
            dst_csv = os.path.join(tmpdir, "out.csv")

            csv_content = (
                "County FIPS,County, State,1990 Poverty %,2000 Poverty %,2016-2020 Poverty %\n"
                "01005,Barbour County, Alabama,25.2,26.8,28.6\n"
            )
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write(csv_content)

            with self.assertRaises(ValueError):
                preprocess_poverty(src_path=csv_path, dst_path=dst_csv, min_county_count=10)


if __name__ == "__main__":
    unittest.main()
