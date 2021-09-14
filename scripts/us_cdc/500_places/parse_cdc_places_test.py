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
Author: Padma Gundapaneni @padma-g
Date: 8/30/2021
Description: This script contains unit tests for the parse_cdc_places.py script.
@input_file   filepath to the original csv that needs to be cleaned
@output_file  filepath to the csv to which the cleaned data is written
python3 parse_cdc_places_test.py input_file output_file
'''

import unittest
import os
from .parse_cdc_places import clean_cdc_places_data

TEST_CASE_FILES = [
    # Pairs of input CSV and expected CSV files.
    ('sample_county.csv', 'sample_county_expected.csv', ','),
    ('sample_city.csv', 'sample_city_expected.csv', ','),
    ('sample_census_tract.csv', 'sample_census_tract_expected.csv', ','),
    ('sample_zip_code.csv', 'sample_zip_code_expected.csv', ','),
]


class TestParseCDCPlaces(unittest.TestCase):
    """
    Tests the functions in parse_cdc_places.py.
    """

    def test_clean_cdc_places_data(self):
        """
        Tests the clean_cdc_places_data function.
        """
        test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        for input_file, expected_output, sep in TEST_CASE_FILES:
            print('\n')
            print('Input File: ' + input_file)
            test_csv = os.path.join(test_dir, input_file)
            output_csv = os.path.join(test_dir,
                                      (input_file[:-4] + '_output.csv'))
            clean_cdc_places_data(test_csv, output_csv, sep=sep)
            expected_csv = os.path.join(test_dir, expected_output)
        with open(output_csv, 'r') as test:
            test_str: str = test.read()
            with open(expected_csv, 'r') as expected:
                expected_str: str = expected.read()
                self.assertEqual(test_str, expected_str)
        os.remove(output_csv)
        print('Passed test!')


if __name__ == '__main__':
    unittest.main()
