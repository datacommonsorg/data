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
            fixture_path = os.path.join(MODULE_DIR, "test_data", "Poverty_original_fixture.csv")
            dst_path = os.path.join(tmpdir, "output.csv")
            with self.assertRaises(ValueError):
                preprocess_poverty(src_path=fixture_path, dst_path=dst_path, min_county_count=100)

    def test_preprocess_poverty_with_static_fixtures(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = os.path.join(MODULE_DIR, "test_data", "Poverty_original_fixture.csv")
            actual_csv = os.path.join(tmpdir, "Poverty_cleaned.csv")
            expected_csv = os.path.join(MODULE_DIR, "test_data", "Poverty_cleaned_expected.csv")

            preprocess_poverty(src_path=fixture_path, dst_path=actual_csv, min_county_count=1)

            self.assertTrue(os.path.exists(actual_csv))
            df_actual = pd.read_csv(actual_csv, dtype={"GEOID": str})
            df_expected = pd.read_csv(expected_csv, dtype={"GEOID": str})
            pd.testing.assert_frame_equal(df_actual, df_expected)


if __name__ == "__main__":
    unittest.main()
