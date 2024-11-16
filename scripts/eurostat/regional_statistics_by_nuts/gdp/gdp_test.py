import unittest
import os
from import_data import *
import pandas as pd
import tempfile
import sys

MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(0, MODULE_DIR)

TEST_DATASET_DIR = os.path.join(MODULE_DIR, "test_data", "sample_input")

EXPECTED_FILES_DIR = os.path.join(MODULE_DIR, "test_data", "sample_output")


class TestProcess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing.
    The test will be conducted for EuroStat BMI Sample Datasets,
    It will be generating CSV, MCF and TMCF files based on the sample input.
    Comparing the data with the expected files.
    """

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)
        input_path = os.path.join(TEST_DATASET_DIR, 'sample_data.tsv')
        input_df = pd.read_csv(input_path, sep='\s*\t\s*', engine='python')
        input_df = input_df.rename(
            columns={'freq,unit,geo\TIME_PERIOD': 'unit,geo\\time'})
        input_df['unit,geo\\time'] = input_df['unit,geo\\time'].str.slice(2)
        self.CLEANED_CSV_FILE_PATH = os.path.join(EXPECTED_FILES_DIR,
                                                  "test_output.csv")
        preprocess(
            translate_wide_to_long('',
                                   is_download_required=False,
                                   df_input=input_df),
            self.CLEANED_CSV_FILE_PATH)

        with open(self.CLEANED_CSV_FILE_PATH, encoding="utf-8-sig") as csv_file:
            self.actual_csv_data = csv_file.read()

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(EXPECTED_FILES_DIR,
                                              "eurostat_gdp.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        self.assertEqual(expected_csv_data.strip(),
                         self.actual_csv_data.strip())


if __name__ == "__main__":
    unittest.main()
