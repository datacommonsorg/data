'''
Unit tests for deepsolar.py
Usage: python3 deepsolar_test.py
'''

import unittest
import os
import tempfile
from deepsolar import write_csv

module_dir_ = os.path.dirname(__file__)


class TestDeepSolar(unittest.TestCase):

    def test_write_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_input = os.path.join(module_dir_, 'test_data/test_data.csv')
            test_csv = os.path.join(tmp_dir, 'test_csv.csv')
            write_csv(test_input, test_csv)
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
