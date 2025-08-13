# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''
Unit tests for ejscreen.py
Usage: python3 -m unittest discover -v -s ../ -p "ejscreen_test.py"
'''
import unittest
import os
import tempfile
import pandas as pd
from .ejscreen import write_csv

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



if __name__ == '__main__':
    unittest.main()
