"""This script has the tests for preproccess_data.py.

It imports two test datasets and checks if the processed output matches the
expected output.
"""
import unittest

import pandas as pd
from preprocess_data import MergeAndProcessData


class PreprocessDataTest(unittest.TestCase):
    """This class has the method required to test preprocess_data script."""

    def test_MergeAndProcessData(self):
        expected_df = pd.read_csv("test_data/expected_output.csv")
        forest_df = pd.read_csv("test_data/forest.csv")
        df = pd.read_csv("test_data/other_sectors.csv")
        processed = MergeAndProcessData(forest_df, df)
        sort_column_list = ["country", "year", "statvar"]
        self.assertTrue(
            processed.sort_values(
                by=sort_column_list, ignore_index=True).equals(
                    expected_df.sort_values(by=sort_column_list,
                                            ignore_index=True)))


if __name__ == "__main__":
    unittest.main()
