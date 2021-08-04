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
Description: This script contains unit tests for the parse_air_quality.py script.
@input_file   filepath to the original csv that needs to be cleaned
@output_file  filepath to the csv to which the cleaned data is written
python3 parse_air_quality_test.py input_file output_file
'''

import unittest
import os
import sys
from parse_air_quality import clean_air_quality_data

module_dir_ = os.path.dirname(__file__)


class TestParseAirQuality(unittest.TestCase):
    """
    Tests the functions in parse_air_quality.py.
    """

    def test_clean_air_quality_data(self, test_csv, expected_csv):
        """
        Tests the clean_air_quality_data function.
        """
        print(module_dir_)
        output_csv = test_csv[:-4] + '_output.csv'
        clean_air_quality_data(test_csv, output_csv)
        with open(output_csv, 'r') as test:
            test_str: str = test.read()
            with open(expected_csv, 'r') as expected:
                expected_str: str = expected.read()
                self.assertEqual(test_str, expected_str)
        os.remove(output_csv)

def main():
    """Main function to generate the cleaned csv file."""
    input_file = sys.argv[1]
    expected_output_file = sys.argv[2]
    test = TestParseAirQuality()
    TestParseAirQuality.test_clean_air_quality_data(test, input_file, expected_output_file)

if __name__ == '__main__':
    main()
