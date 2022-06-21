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
Script to automate the testing for EuroStat BMI process script.
"""

import os
import unittest
import sys
import tempfile
# module_dir is the path to where this test is running from.
_MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(0, _MODULE_DIR)
# pylint: disable=wrong-import-position
from process import process
# pylint: enable=wrong-import-position

_TEST_DATASET_DIR = os.path.join(_MODULE_DIR, "test_data", "datasets")
_EXPECTED_FILES_DIR = os.path.join(_MODULE_DIR, "test_data", "expected_files")


class TestProcess(unittest.TestCase):
    """
    This module is used to test EuroStat BMI data processing.
    It will generate and test CSV, MCF and TMCF files for given test input files
    and comapre it with expected results.
    """
    test_data_files = os.listdir(_TEST_DATASET_DIR)
    ip_data = [
        os.path.join(_TEST_DATASET_DIR, file_name)
        for file_name in test_data_files
    ]

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

        with tempfile.TemporaryDirectory() as tmp_dir:
            _CLEANED_CSV_FILE_PATH = os.path.join(tmp_dir, "data.csv")
            _MCF_FILE_PATH = os.path.join(tmp_dir, "test_census.mcf")
            _TMCF_FILE_PATH = os.path.join(tmp_dir, "test_census.tmcf")

            process(self.ip_data, _CLEANED_CSV_FILE_PATH, _MCF_FILE_PATH,
                    _TMCF_FILE_PATH)

            with open(_MCF_FILE_PATH, encoding="UTF-8") as mcf_file:
                self._actual_mcf_data = mcf_file.read()

            with open(_TMCF_FILE_PATH, encoding="UTF-8") as tmcf_file:
                self._actual_tmcf_data = tmcf_file.read()

            with open(_CLEANED_CSV_FILE_PATH, encoding="UTF-8") as csv_file:
                self._actual_csv_data = csv_file.read()

    def test_mcf_tmcf_files(self):
        """
        This method tests MCF, tMCF files generated using process module against
        expected results.
        """
        expected_mcf_file_path = os.path.join(_EXPECTED_FILES_DIR,
                                              "eurostat_population_bmi.mcf")

        expected_tmcf_file_path = os.path.join(_EXPECTED_FILES_DIR,
                                               "eurostat_population_bmi.tmcf")

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
        expected_csv_file_path = os.path.join(_EXPECTED_FILES_DIR,
                                              "eurostat_population_bmi.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="UTF-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        self.assertEqual(expected_csv_data.strip(),
                         self._actual_csv_data.strip())
