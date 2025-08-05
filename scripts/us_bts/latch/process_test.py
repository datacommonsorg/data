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
Script to automate the testing for US Tract process script.
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
    This module is used to test US Tract data processing.
    It will generate and test CSV, MCF and TMCF files for given test input files
    and comapre it with expected results.
    """
    TEST_DATA_FILES = os.listdir(_TEST_DATASET_DIR)
    IP_DATA = [
        os.path.join(_TEST_DATASET_DIR, file_name)
        for file_name in TEST_DATA_FILES
    ]

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

        with tempfile.TemporaryDirectory() as tmp_dir:

            self.cleaned_csv_file_path = os.path.join(tmp_dir, "data.csv")
            self.mcf_file_path = os.path.join(tmp_dir, "test_census.mcf")
            self.tmcf_file_path = os.path.join(tmp_dir, "test_census.tmcf")

            process(self.IP_DATA, self.cleaned_csv_file_path,
                    self.mcf_file_path, self.tmcf_file_path)

            with open(self.mcf_file_path, encoding="UTF-8") as mcf_file:
                self._actual_mcf_data = mcf_file.read()

            with open(self.tmcf_file_path, encoding="UTF-8") as tmcf_file:
                self._actual_tmcf_data = tmcf_file.read()

            with open(self.cleaned_csv_file_path, encoding="UTF-8") as csv_file:
                self._actual_csv_data = csv_file.read()

    def test_csv_mcf_tmcf_files(self):
        """
        This method tests CSV, MCF, tMCF files generated using process module
        against expected results.
        """
        expected_csv_file_path = os.path.join(
            _EXPECTED_FILES_DIR, "us_transportation_household.csv")

        expected_mcf_file_path = os.path.join(
            _EXPECTED_FILES_DIR, "us_transportation_household.mcf")

        expected_tmcf_file_path = os.path.join(
            _EXPECTED_FILES_DIR, "us_transportation_household.tmcf")

        with open(expected_csv_file_path,
                  encoding="UTF-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        self.assertEqual(expected_csv_data.strip(),
                         self._actual_csv_data.strip())
        self.assertEqual(expected_mcf_data.strip(),
                         self._actual_mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(),
                         self._actual_tmcf_data.strip())


if __name__ == '__main__':
    unittest.main()
