# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Script to automate the testing for FAO_Currency_statvar import.
"""

import os
import unittest
from absl import app, logging

from preprocess import melt_year_and_flag_columns

input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testdata/")

class TestPreprocess(unittest.TestCase):
    """
    This module is used to test FAO_Currency_Statvar data processing.
    It will generate and test input CSV file for given test input file
    and compare it with expected results.
    """

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

    
        input_file = os.path.join(input_dir, 'Exchange_rate_E_All_Data.csv')
        self.actual_output_file = os.path.join(input_dir, 'final_input_data.csv')
        self.expected_output_file = os.path.join(input_dir, 'final_input_data_expected.csv')

        melt_year_and_flag_columns(input_file, self.actual_output_file)

    def test_input_csv_files(self):
        """
        This method tests input csv files generated using preprocess module against
        expected results.
        """
        with open(self.actual_output_file, encoding="UTF-8") as act_input_file:
            self.actual_input_data = act_input_file.read()

        with open(self.expected_output_file, encoding="utf-8") as exp_input_file:
            self.expected_input_data = exp_input_file.read()

        self.assertEqual(self.actual_input_data.strip(),
                         self.expected_input_data.strip())
        
        logging.info("Testing completed for preprocessed input file!")

def main(argv):
    unittest.main()

if __name__ == '__main__':
    app.run(main)
    
