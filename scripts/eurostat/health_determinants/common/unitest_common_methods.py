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

    class CommonTestCases(unittest.TestCase):
        """
        Provides generic implementation for testing csv, mcf and tmcf files.
        
        klass variable is initialized with test input files directory,
        expected files directory and class of data import

        Limitation: Expected files directory should consist of single *.csv, 
        *.mcf and *.tmcf file.
        """
        klass = None

        def __init__(self, methodName: str = ...) -> None:
            super().__init__(methodName)

            obj = self.klass()

            for file_name in os.listdir(obj.expected_files_directory):
                if file_name.endswith(".csv"):
                    expected_csv_file = file_name
                elif file_name.endswith(".mcf"):
                    expected_mcf_file = file_name
                elif file_name.endswith(".tmcf"):
                    expected_tmcf_file = file_name

            expected_csv_file_path = os.path.join(obj.expected_files_directory,
                                                  expected_csv_file)
            with open(expected_csv_file_path, encoding="UTF-8") as expected_csv:
                self.expected_csv_data = expected_csv.read()

            expected_mcf_file_path = os.path.join(obj.expected_files_directory,
                                                  expected_mcf_file)
            with open(expected_mcf_file_path, encoding="UTF-8") as expected_mcf:
                self.expected_mcf_data = expected_mcf.read()

            expected_tmcf_file_path = os.path.join(obj.expected_files_directory,
                                                   expected_tmcf_file)
            with open(expected_tmcf_file_path,
                      encoding="UTF-8") as expected_tmcf:
                self.expected_tmcf_data = expected_tmcf.read()

            with tempfile.TemporaryDirectory() as tmp_dir:
                cleaned_csv_file_path = os.path.join(tmp_dir, "data.csv")
                mcf_file_path = os.path.join(tmp_dir, "test_census.mcf")
                tmcf_file_path = os.path.join(tmp_dir, "test_census.tmcf")

                ob = obj.import_class(obj.ip_test_files, cleaned_csv_file_path,
                                      mcf_file_path, tmcf_file_path)
                ob.generate_csv()
                ob.generate_mcf()
                ob.generate_tmcf()

                with open(cleaned_csv_file_path, encoding="UTF-8") as csv_file:
                    self.actual_csv_data = csv_file.read()

                with open(mcf_file_path, encoding="UTF-8") as mcf_file:
                    self.actual_mcf_data = mcf_file.read()

                with open(tmcf_file_path, encoding="UTF-8") as tmcf_file:
                    self.actual_tmcf_data = tmcf_file.read()

        def test_csv(self):
            self.assertEquals(self.expected_csv_data, self.actual_csv_data)

        def test_mcf(self):
            self.assertEquals(self.expected_mcf_data, self.actual_mcf_data)

        def test_tmcf(self):
            self.assertEquals(self.expected_tmcf_data, self.actual_tmcf_data)
