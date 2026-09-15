"""Unit tests for process_poverty.py."""

import os
import sys
import tempfile
import unittest
from unittest import mock
import pandas as pd

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from statvar_imports.commerce_eda_poverty.process_poverty import (
    GCS_SOURCE_URI,
    clean_geoid,
    download_from_gcs,
    preprocess_poverty,
)


class TestProcessPoverty(unittest.TestCase):

    def test_clean_geoid(self):
        # 5-digit strings
        self.assertEqual(clean_geoid("01001"), "01001")
        self.assertEqual(clean_geoid("72143"), "72143")
        self.assertEqual(clean_geoid("78010"), "78010")

        # 4-digit zero-padding (e.g. Alaska 02090)
        self.assertEqual(clean_geoid("2090"), "02090")

        # Float strings
        self.assertEqual(clean_geoid("1001.0"), "01001")
        self.assertEqual(clean_geoid("01001.0"), "01001")
        self.assertEqual(clean_geoid("1001.00"), "01001")

        # Numeric floats and ints
        self.assertEqual(clean_geoid(1001.0), "01001")
        self.assertEqual(clean_geoid(2090), "02090")

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

    @mock.patch("util.file_util.file_copy")
    def test_download_from_gcs_success(self, mock_file_copy):
        with tempfile.TemporaryDirectory() as tmpdir:
            dst = os.path.join(tmpdir, "output.csv")

            def fake_copy(src, dst_path):
                with open(dst_path, "w") as f:
                    f.write("content\n")

            mock_file_copy.side_effect = fake_copy
            download_from_gcs(dst_path=dst)
            mock_file_copy.assert_called_once_with(GCS_SOURCE_URI, dst)
            self.assertTrue(os.path.exists(dst))
            self.assertGreater(os.path.getsize(dst), 0)

    @mock.patch("util.file_util.file_copy")
    def test_download_from_gcs_failure(self, mock_file_copy):
        with tempfile.TemporaryDirectory() as tmpdir:
            dst = os.path.join(tmpdir, "output.csv")

            # Failure case 1: file_copy raises exception
            mock_file_copy.side_effect = IOError("Download failed")
            with self.assertRaises(RuntimeError):
                download_from_gcs(dst_path=dst)

            # Failure case 2: file_copy succeeds but destination file not created
            mock_file_copy.side_effect = None
            with self.assertRaises(RuntimeError):
                download_from_gcs(dst_path=dst)

            # Failure case 3: destination file is empty (0 bytes)
            def fake_empty_copy(src, dst_path):
                with open(dst_path, "w") as f:
                    pass

            mock_file_copy.side_effect = fake_empty_copy
            with self.assertRaises(RuntimeError):
                download_from_gcs(dst_path=dst)

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

    def test_preprocess_poverty_missing_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_csv = os.path.join(tmpdir, "bad.csv")
            with open(bad_csv, "w") as f:
                f.write("Line 1\nLine 2\nGEOID,OtherCol\n01001,10.0\n")
            dst_path = os.path.join(tmpdir, "output.csv")
            with self.assertRaises(ValueError):
                preprocess_poverty(src_path=bad_csv, dst_path=dst_path)

    def test_preprocess_poverty_min_county_count_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = os.path.join(MODULE_DIR, "test_data", "Poverty_input.csv")
            dst_path = os.path.join(tmpdir, "output.csv")
            with self.assertRaises(ValueError):
                preprocess_poverty(src_path=fixture_path, dst_path=dst_path, min_county_count=3000)

    def test_preprocess_poverty_with_test_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = os.path.join(MODULE_DIR, "test_data", "Poverty_input.csv")
            actual_csv = os.path.join(tmpdir, "Poverty_cleaned.csv")

            preprocess_poverty(src_path=fixture_path, dst_path=actual_csv, min_county_count=100)

            self.assertTrue(os.path.exists(actual_csv))
            df_actual = pd.read_csv(actual_csv, dtype={"GEOID": str})

            # 200 lines total: 3 header lines + 191 county/territory rows + 6 footnote lines = 191 cleaned rows
            self.assertEqual(len(df_actual), 191)
            self.assertEqual(
                list(df_actual.columns),
                ["GEOID", "poverty_rate_1990", "poverty_rate_2000", "poverty_rate_2020", "poverty_rate_2021"],
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
                'Name,GEOID,"1990 Decennial Census, % in Poverty","2000 Decennial Census, % in Poverty","Most Recent Estimate, % in Poverty* "\n'
                '"Autauga County, AL",01001,15.7,10.9,13.3\n'
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


if __name__ == "__main__":
    unittest.main()
