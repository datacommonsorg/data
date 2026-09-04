import os
import sys
import unittest
import pandas as pd

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from statvar_imports.commerce_eda_poverty.process_poverty import preprocess_poverty

class TestProcessPoverty(unittest.TestCase):
    def setUp(self):
        self.testdata_dir = os.path.join(MODULE_DIR, "testdata")
        os.makedirs(self.testdata_dir, exist_ok=True)
        self.input_csv = os.path.join(self.testdata_dir, "Poverty_original_test_fixture.csv")
        self.expected_csv = os.path.join(self.testdata_dir, "Poverty_cleaned_expected.csv")
        self.actual_csv = os.path.join(self.testdata_dir, "Poverty_cleaned_actual.csv")

        # Create temporary input file
        input_data = (
            "PERSISTENT POVERTY COUNTIES\n"
            "Source: U.S. Treasury CDFI Fund\n"
            "GEOID,\"1990 Decennial Census, % in Poverty\",\"2000 Decennial Census, % in Poverty\",\"Most Recent Estimate, % in Poverty* \"\n"
            "01001,15.2,12.1,10.5\n"
            "01003,11.5,9.8,8.2\n"
            "abc,10.0,10.0,10.0\n"
            "2090,7.6,7.8,9.6\n"
            "0100,5.0,4.2,3.1\n"
        )
        with open(self.input_csv, "w") as f:
            f.write(input_data)

        # Create temporary expected file
        expected_data = (
            "GEOID,\"1990 Decennial Census, % in Poverty\",\"2000 Decennial Census, % in Poverty\",\"Most Recent Estimate, % in Poverty*\"\n"
            "01001,15.2,12.1,10.5\n"
            "01003,11.5,9.8,8.2\n"
            "02090,7.6,7.8,9.6\n"
            "00100,5.0,4.2,3.1\n"
        )
        with open(self.expected_csv, "w") as f:
            f.write(expected_data)

        if os.path.exists(self.actual_csv):
            os.remove(self.actual_csv)

    def tearDown(self):
        if os.path.exists(self.actual_csv):
            os.remove(self.actual_csv)
        if os.path.exists(self.input_csv):
            os.remove(self.input_csv)
        if os.path.exists(self.expected_csv):
            os.remove(self.expected_csv)
        try:
            os.rmdir(self.testdata_dir)
        except OSError:
            pass

    def test_preprocess_poverty(self):
        preprocess_poverty(src_path=self.input_csv, dst_path=self.actual_csv)

        self.assertTrue(os.path.exists(self.actual_csv))

        # Compare outputs
        df_actual = pd.read_csv(self.actual_csv)
        df_expected = pd.read_csv(self.expected_csv)

        pd.testing.assert_frame_equal(df_actual, df_expected)

if __name__ == "__main__":
    unittest.main()
