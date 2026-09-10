"""Unit tests for process_poverty.py."""

import os
import sys
import tempfile
import unittest
import pandas as pd

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from statvar_imports.commerce_eda_poverty.process_poverty import clean_geoid, preprocess_poverty


class TestProcessPoverty(unittest.TestCase):

    def test_clean_geoid(self):
        # Valid 5-digit GEOIDs
        self.assertEqual(clean_geoid("01001"), "01001")
        self.assertEqual(clean_geoid("72143"), "72143")
        self.assertEqual(clean_geoid("78010"), "78010")

        # 4-digit GEOID with stripped leading zero from Excel (Alaska 02090)
        self.assertEqual(clean_geoid("2090"), "02090")

        # Invalid GEOID with non-existent state code (00100)
        self.assertIsNone(clean_geoid("0100"))
        self.assertIsNone(clean_geoid("00100"))

        # Invalid non-numeric or malformed
        self.assertIsNone(clean_geoid("abc"))
        self.assertIsNone(clean_geoid(""))
        self.assertIsNone(clean_geoid(None))
        self.assertIsNone(clean_geoid("123456"))

    def test_preprocess_poverty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_csv = os.path.join(tmpdir, "input.csv")
            actual_csv = os.path.join(tmpdir, "actual.csv")

            input_data = (
                "PERSISTENT POVERTY COUNTIES\n"
                "Source: U.S. Treasury CDFI Fund\n"
                "Name,GEOID,\"1990 Decennial Census, % in Poverty\",\"2000 Decennial Census, % in Poverty\",\"Most Recent Estimate, % in Poverty* \",Extra\n"
                "County A,01001,15.2,12.1,10.5,foo\n"
                "County B,01003,11.5,9.8,8.2,bar\n"
                "County C,abc,10.0,10.0,10.0,baz\n"
                "County D,2090,7.6,7.8,9.6,qux\n"
                "County E,0100,5.0,4.2,3.1,quux\n"
                "County F,01005,150.0,20.0,25.0,corge\n"
                "County G,01007,-5.0,18.0,14.0,grault\n"
                "County H,01009,,,,garply\n"
                "County I,01011,-10.0,120.0,NA,waldo\n"
            )
            with open(input_csv, "w") as f:
                f.write(input_data)

            preprocess_poverty(src_path=input_csv, dst_path=actual_csv, min_county_count=1)

            self.assertTrue(os.path.exists(actual_csv))
            df_actual = pd.read_csv(actual_csv, dtype={"GEOID": str})

            # Expected records:
            # 01001 (County A): 15.2, 12.1, 10.5
            # 01003 (County B): 11.5, 9.8, 8.2
            # 02090 (County D): 7.6, 7.8, 9.6
            # 01005 (County F): NaN (out-of-bounds 150.0 masked), 20.0, 25.0
            # 01007 (County G): NaN (negative -5.0 masked), 18.0, 14.0
            # County C (abc) and County E (0100 -> 00100): dropped due to invalid GEOID
            # County H (all blank) and County I (all out-of-bounds/NA): dropped due to all-NaN poverty rates
            expected_data = {
                "GEOID": ["01001", "01003", "02090", "01005", "01007"],
                "poverty_rate_1990": [15.2, 11.5, 7.6, None, None],
                "poverty_rate_2000": [12.1, 9.8, 7.8, 20.0, 18.0],
                "poverty_rate_recent": [10.5, 8.2, 9.6, 25.0, 14.0],
            }
            df_expected = pd.DataFrame(expected_data)

            pd.testing.assert_frame_equal(df_actual, df_expected, check_dtype=False)


if __name__ == "__main__":
    unittest.main()
