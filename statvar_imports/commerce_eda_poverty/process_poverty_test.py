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
sys.path.insert(0, os.path.join(PROJECT_ROOT, "util"))

from statvar_imports.commerce_eda_poverty.process_poverty import (
    clean_geoid,
    download_from_gcs,
    preprocess_poverty,
)


class TestProcessPoverty(unittest.TestCase):

    def test_clean_geoid(self):
        # Valid 5-digit GEOIDs
        self.assertEqual(clean_geoid("01001"), "01001")
        self.assertEqual(clean_geoid("72143"), "72143")
        self.assertEqual(clean_geoid("78010"), "78010")

        # 4-digit GEOID with stripped leading zero from Excel (Alaska 02090)
        self.assertEqual(clean_geoid("2090"), "02090")

        # Invalid GEOID with non-existent state code (0100 -> 00100)
        self.assertIsNone(clean_geoid("0100"))
        self.assertIsNone(clean_geoid("00100"))

        # Invalid non-numeric or malformed
        self.assertIsNone(clean_geoid("abc"))
        self.assertIsNone(clean_geoid(""))
        self.assertIsNone(clean_geoid(None))
        self.assertIsNone(clean_geoid("123456"))

    def test_preprocess_poverty_wide_format_and_no_truncation(self):
        """Verifies that dataset maintains wide format and does NOT truncate rows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_csv = os.path.join(tmpdir, "input.csv")
            actual_csv = os.path.join(tmpdir, "actual.csv")

            # Generate >100 counties to assert that the 100-row truncation bug does not recur
            rows = [
                "PERSISTENT POVERTY COUNTIES",
                "Source: U.S. Treasury CDFI Fund",
                "Name,GEOID,\"1990 Decennial Census, % in Poverty\","
                "\"2000 Decennial Census, % in Poverty\","
                "\"Most Recent Estimate, % in Poverty* \",Extra",
            ]

            # 105 valid counties (Alabama FIPS 01001 through 01209, odd numbers)
            expected_geoids = []
            for i in range(1, 211, 2):
                geoid = f"01{i:03d}"
                expected_geoids.append(geoid)
                rows.append(f"County {geoid},{geoid},15.0,12.0,10.0,extra")

            # Add invalid rows that should be filtered
            rows.append("Invalid County,abc,10.0,10.0,10.0,extra")
            rows.append("Invalid FIPS,0100,10.0,10.0,10.0,extra")
            rows.append("Empty Rates,01211,,,,extra")
            rows.append("Out of Bounds,01213,-5.0,120.0,150.0,extra")

            with open(input_csv, "w", encoding="utf-8") as f:
                f.write("\n".join(rows) + "\n")

            preprocess_poverty(src_path=input_csv, dst_path=actual_csv, min_county_count=100)

            self.assertTrue(os.path.exists(actual_csv))
            df_actual = pd.read_csv(actual_csv, dtype={"GEOID": str})

            # Assert target wide format columns
            expected_cols = [
                "GEOID",
                "poverty_rate_1990",
                "poverty_rate_2000",
                "poverty_rate_recent",
            ]
            self.assertEqual(list(df_actual.columns), expected_cols)

            # Assert zero row truncation (> 100 counties retained: 105 counties)
            self.assertEqual(len(df_actual), 105)
            self.assertEqual(df_actual["GEOID"].nunique(), 105)

    def test_preprocess_poverty_empty_or_missing_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_csv = os.path.join(tmpdir, "missing.csv")
            dst_csv = os.path.join(tmpdir, "out.csv")

            with self.assertRaises(SystemExit):
                preprocess_poverty(src_path=missing_csv, dst_path=dst_csv)

            empty_csv = os.path.join(tmpdir, "empty.csv")
            with open(empty_csv, "w", encoding="utf-8") as f:
                f.write("")

            with self.assertRaises(SystemExit):
                preprocess_poverty(src_path=empty_csv, dst_path=dst_csv)

    @mock.patch("statvar_imports.commerce_eda_poverty.process_poverty.file_util.file_copy")
    def test_download_from_gcs_retry(self, mock_file_copy):
        with tempfile.TemporaryDirectory() as tmpdir:
            dst_path = os.path.join(tmpdir, "downloaded.csv")

            # Simulate first attempt failing and second succeeding
            def side_effect(src, dst):
                if mock_file_copy.call_count == 1:
                    raise IOError("Transient network error")
                with open(dst, "w", encoding="utf-8") as f:
                    f.write("content")

            mock_file_copy.side_effect = side_effect

            download_from_gcs(dst_path=dst_path, max_retries=3, backoff_factor=0.01)
            self.assertTrue(os.path.exists(dst_path))
            self.assertEqual(mock_file_copy.call_count, 2)


if __name__ == "__main__":
    unittest.main()
