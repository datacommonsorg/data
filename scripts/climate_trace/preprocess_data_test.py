"""This script has the tests for preproccess_data.py.

It imports two test datasets and checks if the processed output matches the
expected output.
"""
import unittest
import os
import pandas as pd
import sys

module_dir_ = os.path.dirname(__file__)
sys.path.insert(0, module_dir_)
import preprocess_data


def _GetTestPath(relative_path):
    return os.path.join(module_dir_, relative_path)


class PreprocessDataTest(unittest.TestCase):
    """This class has the method required to test preprocess_data script."""

    def test_MergeAndProcessData(self):
        expected_df = pd.read_csv(_GetTestPath("test_data/expected_output.csv"))
        forest_df = pd.read_csv(_GetTestPath("test_data/forest.csv"))
        df = pd.read_csv(_GetTestPath("test_data/other_sectors.csv"))
        processed = preprocess_data.MergeAndProcessData(forest_df, df)
        sort_column_list = ["country", "year", "statvar", "measurement_method"]
        self.assertIsNone(
            pd.testing.assert_frame_equal(
                processed.sort_values(by=sort_column_list, ignore_index=True),
                expected_df.sort_values(by=sort_column_list,
                                        ignore_index=True)))


if __name__ == "__main__":
    unittest.main()
