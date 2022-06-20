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
import unittest
import tempfile
# pylint: disable=import-error
from preprocess import process
# pylint: enable=import-error
# _MODULE_DIR is the path to where this test is running from.
_MODULE_DIR = os.path.dirname(__file__)
_TEST_DATA_FOLDER = os.path.join(_MODULE_DIR, "test_data")


class TestPreprocess(unittest.TestCase):
    """
    This module is used to test EuroStat BMI data processing.
    It will generate and test CSV, MCF and TMCF files for given test input files
    and comapre it with expected results.
    """

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

        ip_data_path = [os.path.join(_TEST_DATA_FOLDER, "test_input_data.csv")]

        with tempfile.TemporaryDirectory() as tmp_dir:
            cleaned_csv_file_path = os.path.join(tmp_dir,
                                                 "test_output_data.csv")
            mcf_file_path = os.path.join(tmp_dir, "test_census.mcf")
            tmcf_file_path = os.path.join(tmp_dir, "test_census.tmcf")

            process(ip_data_path, cleaned_csv_file_path, mcf_file_path,
                    tmcf_file_path)

            with open(mcf_file_path, encoding="UTF-8") as mcf_file:
                self._actual_mcf_data = mcf_file.read()

            with open(tmcf_file_path, encoding="UTF-8") as tmcf_file:
                self._actual_tmcf_data = tmcf_file.read()

            with open(cleaned_csv_file_path, encoding="utf-8") as csv_file:
                self._actual_csv_data = csv_file.read()

    def test_mcf_tmcf_files(self):
        """
        This method tests MCF, tMCF files generated using process module against
        expected results.
        """
        expected_mcf_file_path = os.path.join(
            _TEST_DATA_FOLDER, "excepted_usa_annual_population.mcf")

        expected_tmcf_file_path = os.path.join(
            _TEST_DATA_FOLDER, "excepted_usa_annual_population.tmcf")

        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        self.assertEqual(expected_mcf_data.strip(),
                         self._actual_mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(),
                         self._actual_tmcf_data.strip())

    def test_create_csv(self):
        """
        This method tests CSV file generated using process module against
        expected CSV result.
        """
        expected_csv_file_path = os.path.join(
            _TEST_DATA_FOLDER, "expected_usa_population_count.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        self.assertEqual(expected_csv_data.strip(),
                         self._actual_csv_data.strip())
