'''
Unit tests for ejscreen.py
Usage: python3 ejscreen_test.py
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
            dfs = {}
            dfs['2020'] = pd.read_csv(os.path.join(module_dir_,
                                                   'test_data/test_data.csv'),
                                      float_precision='high')
            test_csv = os.path.join(tmp_dir, 'test_csv.csv')
            write_csv(dfs, test_csv)
            expected_csv = os.path.join(module_dir_,
                                        'test_data/test_data_expected.csv')
            with open(test_csv, 'r') as test:
                test_str: str = test.read()
                with open(expected_csv, 'r') as expected:
                    expected_str: str = expected.read()
                    self.assertEqual(test_str, expected_str)
            os.remove(test_csv)


if __name__ == '__main__':
    unittest.main()
