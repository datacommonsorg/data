# Copyright 2025 Google LLC
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
"""
Description: This script contains unit tests for the parse_precipitation_index.py script.
"""

import unittest
import os
from parse_precipitation_index import clean_precipitation_data

module_dir_ = os.path.dirname(__file__)


class TestParsePrecipitationData(unittest.TestCase):
    """
    Tests the functions in parse_precipitation_index.py.
    """

    def _test_data_cleaning(self, input_path, expected_path):
        """
        Helper function to test data cleaning for a given input and expected output.
        """
        # Using a temporary file in the same directory as the test script for simplicity
        output_csv_path = os.path.join(module_dir_, 'test_output.csv')

        clean_precipitation_data(input_path, output_csv_path)

        with open(output_csv_path, 'r') as test_file:
            test_lines = [line.strip() for line in test_file.readlines()]
        with open(expected_path, 'r') as expected_file:
            expected_lines = [
                line.strip() for line in expected_file.readlines()
            ]

        self.assertEqual(test_lines, expected_lines)

        os.remove(output_csv_path)

    def test_clean_precipitation_data_index(self):
        """
        Tests the clean_precipitation_data function for StandardizedPrecipitationIndex.
        """
        input_csv = os.path.join(
            module_dir_,
            'index/test_data/CDC_StandardizedPrecipitationIndex_input.csv')
        expected_csv = os.path.join(
            module_dir_,
            'index/test_data/CDC_StandardizedPrecipitationIndex_output.csv')
        self._test_data_cleaning(input_csv, expected_csv)

    def test_clean_precipitation_data_evapotranspiration(self):
        """
        Tests the clean_precipitation_data function for StandardizedPrecipitationEvapotranspirationIndex.
        """
        input_csv = os.path.join(
            module_dir_,
            'evapotranspiration_index/test_data/CDC_StandardizedPrecipitationEvapotranspirationIndex_input.csv'
        )
        expected_csv = os.path.join(
            module_dir_,
            'evapotranspiration_index/test_data/CDC_StandardizedPrecipitationEvapotranspirationIndex_output.csv'
        )
        self._test_data_cleaning(input_csv, expected_csv)


if __name__ == '__main__':
    unittest.main()
