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
Script to automate the testing for USA Population by Sex Race preprocess script.
"""

import os
import unittest
import sys

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)
sys.path.insert(0, module_dir_)
from preprocess import process

expected_data_folder = os.path.join(module_dir_,
                                    "test_data/expected_output_files")
actual_data_folder = os.path.join(module_dir_, "output_files/final")
test_data_folder = os.path.join(module_dir_, "test_data")


class TestPreprocess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing
    """
    ip_config_files = test_data_folder + os.sep + "config_files"
    ip_files = os.listdir(ip_config_files)
    config_files = []
    for file in ip_files:
        config_files.append(ip_config_files + os.sep + file)

    process(config_files, test=True)

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF and TMCF File.
        """
        mcf_files = [
            "state_county_after_2000.mcf", "state_county_before_2000.mcf",
            "national_after_2000.mcf", "national_before_2000.mcf"
        ]

        for mcf_file in mcf_files:
            expected_mcf_file_path = os.path.join(expected_data_folder,
                                                  mcf_file)
            with open(expected_mcf_file_path,
                      encoding="UTF-8") as expected_mcf_file:
                expected_mcf_data = expected_mcf_file.read()

            actual_mcf_file_path = os.path.join(actual_data_folder, mcf_file)
            with open(actual_mcf_file_path,
                      encoding="UTF-8") as actual_mcf_file:
                actual_mcf_data = actual_mcf_file.read()

            self.assertEqual(expected_mcf_data.strip(), actual_mcf_data.strip())

        tmcf_files = [
            "state_county_after_2000.tmcf", "state_county_before_2000.tmcf",
            "national_after_2000.tmcf", "national_before_2000.tmcf"
        ]

        for tmcf_file in tmcf_files:
            expected_tmcf_file_path = os.path.join(expected_data_folder,
                                                   tmcf_file)
            with open(expected_tmcf_file_path,
                      encoding="UTF-8") as expected_tmcf_file:
                expected_tmcf_data = expected_tmcf_file.read()

            actual_tmcf_file_path = os.path.join(actual_data_folder, tmcf_file)
            with open(actual_tmcf_file_path,
                      encoding="UTF-8") as actual_tmcf_file:
                actual_tmcf_data = actual_tmcf_file.read()
            self.assertEqual(expected_tmcf_data.strip(),
                             actual_tmcf_data.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        # self.maxDiff = None
        output_csv_files = [
            "state_county_after_2000.csv", "state_county_before_2000.csv",
            "national_after_2000.csv", "national_before_2000.csv"
        ]

        for output_csv_file in output_csv_files:
            expected_csv_file_path = os.path.join(expected_data_folder,
                                                  output_csv_file)
            with open(expected_csv_file_path,
                      encoding="utf-8-sig") as expected_csv_file:
                expected_csv_data = expected_csv_file.read()

            actual_csv_file_path = os.path.join(actual_data_folder,
                                                output_csv_file)
            with open(actual_csv_file_path,
                      encoding="utf-8-sig") as actual_csv_file:
                actual_csv_data = actual_csv_file.read()

            self.assertEqual(expected_csv_data.strip(), actual_csv_data.strip())
