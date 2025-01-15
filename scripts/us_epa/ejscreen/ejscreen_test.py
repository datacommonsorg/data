'''
Unit tests for ejscreen.py
Usage: python3 -m unittest discover -v -s ../ -p "ejscreen_test.py"
'''
import unittest
import os
import tempfile
import pandas as pd
from ejscreen import write_csv

module_dir_ = os.path.dirname(__file__)


class TestEjscreen(unittest.TestCase):

    def test_write_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Ensure test data file exists in the expected directory
            test_data_file = os.path.join(module_dir_,
                                          'test_data/test_data.csv')
            expected_data_file = os.path.join(
                module_dir_, 'test_data/test_data_expected.csv')

            if not os.path.exists(test_data_file) or not os.path.exists(
                    expected_data_file):
                raise FileNotFoundError(
                    f"Test data files are missing: {test_data_file}, {expected_data_file}"
                )

            dfs = {}
            dfs['2020'] = pd.read_csv(test_data_file, float_precision='high')
            test_csv = os.path.join(tmp_dir, 'test_csv.csv')
            write_csv(dfs, test_csv)

            with open(test_csv, 'r') as test:
                test_str = test.read()
                with open(expected_data_file, 'r') as expected:
                    expected_str = expected.read()
                    self.assertEqual(test_str, expected_str)

            # Remove temporary test file after assertion
            os.remove(test_csv)


if __name__ == '__main__':
    unittest.main()
