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
        self.input_csv = os.path.join(self.testdata_dir, "Poverty_original_test_fixture.csv")
        self.expected_csv = os.path.join(self.testdata_dir, "Poverty_cleaned_expected.csv")
        self.actual_csv = os.path.join(self.testdata_dir, "Poverty_cleaned_actual.csv")

        if os.path.exists(self.actual_csv):
            os.remove(self.actual_csv)

    def tearDown(self):
        if os.path.exists(self.actual_csv):
            os.remove(self.actual_csv)

    def test_preprocess_poverty(self):
        preprocess_poverty(src_path=self.input_csv, dst_path=self.actual_csv)

        self.assertTrue(os.path.exists(self.actual_csv))

        # Compare outputs
        df_actual = pd.read_csv(self.actual_csv)
        df_expected = pd.read_csv(self.expected_csv)

        pd.testing.assert_frame_equal(df_actual, df_expected)

if __name__ == "__main__":
    unittest.main()
