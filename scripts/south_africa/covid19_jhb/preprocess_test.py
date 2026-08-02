"""Test script for preprocess.py"""

import os
import tempfile
import unittest
import pandas as pd
from preprocess import process_csv

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestPreprocessCSV(unittest.TestCase):
    """Test the preprocess_csv function from preprocess.py."""

    def setUp(self):
        # Set up a temporary directory for test files
        self.tmp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        # Clean up the temporary directory after each test
        self.tmp_dir.cleanup()

    def test_preprocess_csv(self):
        # Define paths to input and expected output CSV files
        input_csv_path = os.path.join(module_dir_, "test_data/test_data.csv")
        expected_output_path = os.path.join(module_dir_,
                                            "test_data/test_expected_data.csv")

        # Preprocess the test data
        output_csv_path = os.path.join(self.tmp_dir.name, "test_output.csv")
        process_csv(input_csv_path, output_csv_path)

        # Read the processed data from the output CSV file
        df_processed = pd.read_csv(output_csv_path)

        # Read the expected output from the CSV file
        expected_output = pd.read_csv(expected_output_path)

        # Check if the processed data matches the expected output
        pd.testing.assert_frame_equal(df_processed, expected_output)


if __name__ == "__main__":
    unittest.main()
