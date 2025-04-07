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
This module provides generic class for testing processed csv, mcf and tmcf files
"""

import os
import unittest
import tempfile


class CommonTestClass:
    """
    """
    _df = None

    class CommonTestCases(unittest.TestCase):
        """
        Provides generic implementation for testing csv, mcf and tmcf files.

        Limitation: Expected files directory should consist of single *.csv,
        *.mcf and *.tmcf file.
        """
        _import_class = None
        _import_name = None
        _test_module_directory = ""

        # pylint: disable=too-many-locals
        def __init__(self, methodName: str = ...) -> None:
            super().__init__(methodName)

            test_input_files_directory = os.path.join(
                self._test_module_directory, "test_files", "input_files")
            ip_test_files = os.listdir(test_input_files_directory)
            ip_test_files = [
                test_input_files_directory + os.sep + file
                for file in ip_test_files
            ]
            self._expected_files_directory = os.path.join(
                self._test_module_directory, "test_files", "expected_files")

            for file_name in os.listdir(self._expected_files_directory):
                if file_name.endswith(".csv"):
                    self._expected_csv_file = file_name
                elif file_name.endswith(".mcf"):
                    self._expected_mcf_file = file_name
                elif file_name.endswith(".tmcf"):
                    self._expected_tmcf_file = file_name

            self._ob = self._import_class(ip_test_files)

        def test_csv(self):
            expected_csv_file_path = os.path.join(
                self._expected_files_directory, self._expected_csv_file)

            with open(expected_csv_file_path, encoding="UTF-8") as expected_csv:
                expected_csv_data = expected_csv.read()

            with tempfile.TemporaryDirectory() as tmp_dir:
                csv_file_path = os.path.join(tmp_dir, "test_census.csv")
                self._ob.set_cleansed_csv_file_path(csv_file_path)
                CommonTestClass._df = self._ob.generate_csv(self._import_name)
                with open(csv_file_path, encoding="UTF-8") as csv_file:
                    actual_csv_data = csv_file.read()

                self.assertEquals(expected_csv_data, actual_csv_data)

        def test_mcf(self):
            expected_mcf_file_path = os.path.join(
                self._expected_files_directory, self._expected_mcf_file)

            with open(expected_mcf_file_path, encoding="UTF-8") as expected_mcf:
                expected_mcf_data = expected_mcf.read()

            with tempfile.TemporaryDirectory() as tmp_dir:
                mcf_file_path = os.path.join(tmp_dir, "test_census.mcf")
                self._ob.set_mcf_file_path(mcf_file_path)
                self._ob.generate_mcf(CommonTestClass._df)
                with open(mcf_file_path, encoding="UTF-8") as mcf_file:
                    actual_mcf_data = mcf_file.read()

                self.assertEquals(expected_mcf_data, actual_mcf_data)

        def test_tmcf(self):
            expected_tmcf_file_path = os.path.join(
                self._expected_files_directory, self._expected_tmcf_file)

            with open(expected_tmcf_file_path,
                      encoding="UTF-8") as expected_tmcf:
                expected_tmcf_data = expected_tmcf.read()

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmcf_file_path = os.path.join(tmp_dir, "test_census.tmcf")
                self._ob.set_tmcf_file_path(tmcf_file_path)
                self._ob.generate_tmcf(self._import_name)
                with open(tmcf_file_path, encoding="UTF-8") as tmcf_file:
                    actual_tmcf_data = tmcf_file.read()

                self.assertEquals(expected_tmcf_data, actual_tmcf_data)
