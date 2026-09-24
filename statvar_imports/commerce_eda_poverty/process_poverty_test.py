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

import openpyxl
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
    """Creates a .xlsx workbook mimicking the official EDA Persistent Poverty Counties workbook."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Underlying_Data"
    if description_row:
        ws.append([
            "Table. FY2023 Persistent Poverty County Status - as of Data Year 2021",
            "", "", "", "", ""
        ])
        ws.append(["Identifing Information", "", "Census Bureau Data", "", "", ""])
    ws.append([
        "Name",
        "GEOID",
        "1990 Decennial Census, % in Poverty",
        "2000 Decennial Census, % in Poverty",
        "Most Recent Estimate, % in Poverty* ",
        "Data Source―Most Recent Estimate",
    ])
    for r in rows:
        ws.append(r)
    wb.save(filepath)


class TestProcessPoverty(unittest.TestCase):

    def test_clean_geoid(self):
        # 5-digit strings
        self.assertEqual(clean_geoid("01001"), "01001")
        self.assertEqual(clean_geoid("72143"), "72143")
        self.assertEqual(clean_geoid("78010"), "78010")

        # 4-digit zero-padding (e.g. Alabama 01005, Alaska 02090)
        self.assertEqual(clean_geoid("1005"), "01005")
        self.assertEqual(clean_geoid("2090"), "02090")

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
            resolve_source_file_path("/nonexistent/file.csv")

    def test_preprocess_poverty_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = os.path.join(tmpdir, "nonexistent.csv")
            dst_path = os.path.join(tmpdir, "output.csv")
            with self.assertRaises(ValueError):
                preprocess_poverty(src_path=missing_path, dst_path=dst_path)

    def test_preprocess_poverty_empty_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_path = os.path.join(tmpdir, "empty.csv")
            with open(empty_path, "w") as f:
                pass
            dst_path = os.path.join(tmpdir, "output.csv")
            with self.assertRaises(ValueError):
                preprocess_poverty(src_path=empty_path, dst_path=dst_path)

    def test_preprocess_poverty_header_only_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            header_only = os.path.join(tmpdir, "header_only.csv")
            with open(header_only, "w") as f:
                f.write(
                    "Header 1\nHeader 2\n"
                    "Name,GEOID,\"1990 Decennial Census, % in Poverty\","
                    "\"2000 Decennial Census, % in Poverty\","
                    "\"Most Recent Estimate, % in Poverty*\"\n"
                )
            dst_path = os.path.join(tmpdir, "output.csv")
            with self.assertRaises(ValueError):
                preprocess_poverty(src_path=header_only, dst_path=dst_path)

    def test_preprocess_poverty_missing_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_csv = os.path.join(tmpdir, "bad.csv")
            with open(bad_csv, "w") as f:
                f.write("Line 1\nLine 2\nGEOID,OtherCol\n01001,10.0\n")
            dst_path = os.path.join(tmpdir, "output.csv")
            with self.assertRaises(ValueError):
                preprocess_poverty(src_path=bad_csv, dst_path=dst_path)

    def test_preprocess_poverty_unexpected_survey_year(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            future_csv = os.path.join(tmpdir, "future.csv")
            with open(future_csv, "w") as f:
                f.write(
                    "Header 1\nHeader 2\n"
                    "Name,GEOID,\"1990 Decennial Census, % in Poverty\","
                    "\"2000 Decennial Census, % in Poverty\","
                    "\"Most Recent Estimate, % in Poverty*\","
                    "\"Data Source―Most Recent Estimate\"\n"
                    '"Autauga County, AL",01001,15.7,10.9,13.3,"SAIPE, 2025"\n'
                )
            dst_path = os.path.join(tmpdir, "output.csv")
            with self.assertRaises(ValueError):
                preprocess_poverty(src_path=future_csv, dst_path=dst_path, min_county_count=1)

    def test_preprocess_poverty_min_county_count_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = os.path.join(MODULE_DIR, "test_data", "Poverty_input.csv")
            dst_path = os.path.join(tmpdir, "output.csv")
            with self.assertRaises(ValueError):
                preprocess_poverty(src_path=fixture_path, dst_path=dst_path, min_county_count=3000)

    def test_preprocess_poverty_with_test_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = os.path.join(MODULE_DIR, "test_data", "Poverty_input.csv")
            expected_path = os.path.join(MODULE_DIR, "test_data", "Poverty_expected_output.csv")
            actual_csv = os.path.join(tmpdir, "Poverty_cleaned.csv")

            preprocess_poverty(src_path=fixture_path, dst_path=actual_csv, min_county_count=100)

            self.assertTrue(os.path.exists(actual_csv))
            df_actual = pd.read_csv(actual_csv, dtype={"GEOID": str})
            df_expected = pd.read_csv(expected_path, dtype={"GEOID": str})
            pd.testing.assert_frame_equal(df_actual, df_expected)

            # 200 lines total: 3 header lines + 191 county/territory rows
            # + 6 footnote lines = 191 cleaned rows
            self.assertEqual(len(df_actual), 191)
            self.assertEqual(
                list(df_actual.columns),
                [
                    "GEOID",
                    "poverty_rate_1990",
                    "poverty_rate_2000",
                    "poverty_rate_2020",
                    "poverty_rate_2021",
                ],
            )

            # Verify 11 island territories (AS, GU, MP, VI) map to poverty_rate_2020
            territory_rows = df_actual[df_actual["GEOID"].str[:2].isin({"60", "66", "69", "78"})]
            self.assertEqual(len(territory_rows), 11)
            self.assertTrue(territory_rows["poverty_rate_2020"].notna().all())
            self.assertTrue(territory_rows["poverty_rate_2021"].isna().all())

            # Verify states and PR (180 rows) map to poverty_rate_2021
            state_rows = df_actual[~df_actual["GEOID"].str[:2].isin({"60", "66", "69", "78"})]
            self.assertEqual(len(state_rows), 180)
            self.assertTrue(state_rows["poverty_rate_2021"].notna().all())
            self.assertTrue(state_rows["poverty_rate_2020"].isna().all())

    def test_preprocess_poverty_edge_cases(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_csv = os.path.join(tmpdir, "raw.csv")
            actual_csv = os.path.join(tmpdir, "cleaned.csv")

            raw_content = (
                "Header 1\n"
                "Header 2\n"
                "Name,GEOID,\"1990 Decennial Census, % in Poverty\","
                "\"2000 Decennial Census, % in Poverty\","
                "\"Most Recent Estimate, % in Poverty* \"\n"
                '"Autauga County, AL",01001,15.7,10.9,13.3\n'
                '"Alabama State Summary",01000,18.0,16.0,15.0\n'
                '"Yukon-Koyukuk, AK",2090,7.6,7.8,9.6\n'
                '"Eastern District, AS",60010,25.0,28.0,30.0\n'
                '"Barbour County, AL",01005.0,25.2,26.8,29.0\n'
                '"Bibb County, AL",1007.0,21.2,20.6,24.9\n'
                '"Blount County, AL",01009,-5.0,150.0,14.5\n'
                '"Bullock County, AL",01011,-10.0,120.0,999.0\n'
                '"Invalid 1",99001,15.0,15.0,15.0\n'
                '"Invalid 2",abc,10.0,10.0,10.0\n'
                '"Invalid 3",0100,5.0,4.2,3.1\n'
                '"Source footnote",,,,\n'
            )
            with open(raw_csv, "w") as f:
                f.write(raw_content)

            preprocess_poverty(src_path=raw_csv, dst_path=actual_csv, min_county_count=1)
            df_actual = pd.read_csv(actual_csv, dtype={"GEOID": str})

            expected_data = {
                "GEOID": ["01001", "02090", "60010", "01005", "01007", "01009"],
                "poverty_rate_1990": [15.7, 7.6, 25.0, 25.2, 21.2, None],
                "poverty_rate_2000": [10.9, 7.8, 28.0, 26.8, 20.6, None],
                "poverty_rate_2020": [None, None, 30.0, None, None, None],
                "poverty_rate_2021": [13.3, 9.6, None, 29.0, 24.9, 14.5],
            }
            df_expected = pd.DataFrame(expected_data)
            pd.testing.assert_frame_equal(df_actual, df_expected)

    def test_preprocess_poverty_from_excel(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            excel_path = os.path.join(tmpdir, "mock.xlsx")
            cleaned_csv = os.path.join(tmpdir, "cleaned.csv")

            mock_rows = [
                ["Autauga County, AL", "01001", 15.7, 10.9, 13.3, "SAIPE, 2021"],
                ["Eastern District, AS", "60010", 25.0, 28.0, 30.0, "Decennial Census, 2020"],
            ]
            _create_mock_excel_file(excel_path, mock_rows)

            preprocess_poverty(src_path=excel_path, dst_path=cleaned_csv, min_county_count=1)
            self.assertTrue(os.path.exists(cleaned_csv))
            df = pd.read_csv(cleaned_csv, dtype={"GEOID": str})
            self.assertEqual(len(df), 2)
            self.assertEqual(df.loc[df["GEOID"] == "01001", "poverty_rate_2021"].iloc[0], 13.3)
            self.assertEqual(df.loc[df["GEOID"] == "60010", "poverty_rate_2020"].iloc[0], 30.0)


if __name__ == "__main__":
    unittest.main()
