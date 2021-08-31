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
Author: Samantha Piekos @spiekos and Padma Gundapaneni @padma-g
Date: 8/3/21
Description: This script contains unit tests for the parse_precipitation_index.py script.
@input_file             filepath to the original csv that needs to be cleaned
@Expected_output_file   filepath to the csv to which the expected cleaned data is written
python3 parse_precipitation_index_test.py input_file expected_output_file
'''

import unittest
import os
from parse_precipitation_index import clean_precipitation_data

TEST_CASE_FILES = [
# Pairs of input CSV and expected CSV files.
('Palmer_Drought_Severity_Index_test_file.csv', 
    'Palmer_Drought_Severity_Index_test_file_expected_output.csv'),
('Standardized_Precipitation_Evapotranspiration_Index_test_file.csv', 
    'Standardized_Precipitation_Evapotranspiration_Index_test_file_expected_output.csv'),
('Standardized_Precipitation_Index_test_file.csv', 
    'Standardized_Precipitation_Index_test_file_expected_output.csv')
]

class TestParsePrecipitationData(unittest.TestCase):
    """
    Tests the functions in parse_precipitation_index.py.
    """
    def test_clean_precipitation_data(self):
        """
        Tests the clean_precipitation_data function.
        """
        module_dir_ = os.path.dirname(__file__)
        print('Directory: ' + module_dir_)
        for input_file, expected_output_file in TEST_CASE_FILES:
            print('\n')
            print('Input File: ' + input_file)
            test_csv = os.path.join(module_dir_, input_file)
            output_csv = os.path.join(module_dir_,
                (input_file[:-4] + '_output.csv'))
            clean_precipitation_data(test_csv, output_csv)

            expected_csv = os.path.join(module_dir_, expected_output_file)
            with open(output_csv, 'r') as test:
                test_str: str = test.read()
                with open(expected_csv, 'r') as expected:
                    expected_str: str = expected.read()
                    self.assertEqual(test_str, expected_str)
            os.remove(output_csv)
            print('Passed test!')

if __name__ == '__main__':
    unittest.main()
