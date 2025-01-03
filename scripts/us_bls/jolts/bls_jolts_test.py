# Copyright 2022 Google LLC
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
Script to automate the testing for USA Population preprocess script.
"""

import os
import sys
import unittest
import tempfile
# _MODULE_DIR is the path to where this test is running from.
_MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(1, _MODULE_DIR)
# pylint: disable=wrong-import-position
# pylint: disable=import-error
from bls_jolts import generate_cleaned_dataframe, process
# pylint: enable=import-error
# pylint: enable=wrong-import-position
INPUT_DIR = 'input_files'
OUTPUT_DIR = 'actual_output_files'
OUTPUT_FILES = 'expected_output_files'
TEST_DATA_DIR = 'test_data'

if not os.path.exists("./test_data/actual_output_files/"):
    os.makedirs("./test_data/actual_output_files/")


class TestPreprocess(unittest.TestCase):
    """
    This module is used to test USCensus PEP_Annual_Population data processing.
    It will generate and test CSV, MCF and TMCF files for given test input files
    and compare it with expected results.
    """

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

        files_dir = os.path.join(_MODULE_DIR, TEST_DATA_DIR, INPUT_DIR)

        data_file_path = os.path.join(_MODULE_DIR, TEST_DATA_DIR, OUTPUT_DIR)

        cleaned_csv_path = os.path.join(data_file_path,
                                        "BLSJolts_StatisticalVariables.csv")
        mcf_path = os.path.join(data_file_path,
                                "BLSJolts_StatisticalVariables.mcf")

        jolts_df, schema_mapping = generate_cleaned_dataframe(files_dir)
        final_columns = ['Date', 'StatisticalVariable', 'Value']
        # output_csv_path = os.path.join(OUTPUT_FILES, "BLSJolts_StatisticalVariables.csv")
        jolts_df.loc[:, final_columns].to_csv(cleaned_csv_path)

        # Call the process function to write statistical variables to MCF
        process(jolts_df, schema_mapping, data_file_path)

        with open(mcf_path, encoding="UTF-8") as mcf_file:
            self._actual_mcf_data = mcf_file.read()

        with open(cleaned_csv_path, encoding="utf-8") as csv_file:
            self._actual_csv_data = csv_file.read()

    def test_mcf_files(self):
        """
        This method tests MCF files generated using process module against
        expected results.
        """
        expected_mcf_file_path = os.path.join(
            _MODULE_DIR, TEST_DATA_DIR, OUTPUT_FILES,
            "BLSJolts_StatisticalVariables.mcf")

        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        self.assertEqual(expected_mcf_data.strip(),
                         self._actual_mcf_data.strip())

    def test_create_csv(self):
        """
        This method tests CSV file generated using process module against
        expected CSV result.
        """
        expected_csv_file_path = os.path.join(
            _MODULE_DIR, TEST_DATA_DIR, OUTPUT_FILES,
            "BLSJolts_StatisticalVariables.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        self.assertEqual(expected_csv_data.strip(),
                         self._actual_csv_data.strip())


if __name__ == '__main__':
    unittest.main()
