# Copyright 2021 Google LLC
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
Unit tests for criteria_gases.py

Usage: python3 criteria_gases_test.py
'''
import unittest, csv, os, tempfile
from criteria_gases import join, write_csv, write_tmcf

module_dir_ = os.path.dirname(__file__)

class TestCriteriaGasesTest(unittest.TestCase):

    def test_write_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir: 
            pollutant = '44201'  # Ozone
            camel_case = {
                '': '',
                ' - ': '',
            }
            d = {}
            with open(os.path.join(module_dir_, 'test_data/test_import_data.csv'), 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    join(d, row, camel_case)

                test_csv = os.path.join(tmp_dir, 'test_csv.csv')
                write_csv(test_csv, d, pollutant)         
                
                expected_csv = os.path.join(module_dir_, 'test_data/test_import.csv')
                with open(test_csv, 'r') as test: 
                    test_str: str = test.read()
                    with open(expected_csv, 'r') as expected:
                        expected_str: str = expected.read()
                        self.assertEqual(test_str, expected_str)
                os.remove(test_csv)


    def test_write_tmcf(self):
        with tempfile.TemporaryDirectory() as tmp_dir: 
            pollutant = '44201'  # Ozone
            test_tmcf = os.path.join(tmp_dir, 'test_tmcf.tmcf')
            write_tmcf(test_tmcf, pollutant)
            
            expected_tmcf = os.path.join(module_dir_, 'EPA_CriteriaGases_44201.tmcf')
            with open(test_tmcf, 'r') as test: 
                    test_str: str = test.read()
                    with open(expected_tmcf, 'r') as expected:
                        expected_str: str = expected.read()
                        self.assertEqual(test_str, expected_str)
            os.remove(test_tmcf)


if __name__ == '__main__':
    unittest.main()