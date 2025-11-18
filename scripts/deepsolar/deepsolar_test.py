'''
Unit tests for deepsolar.py
Usage: python3 deepsolar_test.py
'''

import unittest
import os
import tempfile
import pandas as pd
from pandas.testing import assert_frame_equal
from .deepsolar import write_csv

module_dir_ = os.path.dirname(__file__)


class TestDeepSolar(unittest.TestCase):

    def test_write_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_input = os.path.join(module_dir_, 'test_data/test_data.csv')
            test_csv_path = os.path.join(tmp_dir, 'test_csv.csv')
            write_csv(test_input, test_csv_path)

            expected_csv_path = os.path.join(
                module_dir_, 'test_data/test_data_expected.csv')

            # Read CSVs into pandas DataFrames
            test_df = pd.read_csv(test_csv_path)
            expected_df = pd.read_csv(expected_csv_path)

            # Compare DataFrames with tolerance for floating point differences
            assert_frame_equal(test_df, expected_df, rtol=1e-5)

            os.remove(test_csv_path)


if __name__ == '__main__':
    unittest.main()
