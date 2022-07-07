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
Script to automate the testing for USA Population by Race preprocess script.
"""

import os
import unittest
import shutil
from os import path
from preprocess import CensusUSAPopulationByRace
# module_dir is the path to where this test is running from.
module_dir = os.path.dirname(__file__)
TEST_DATA_FOLDER = os.path.join(module_dir, "test_data")
OP_DATA_FOLDER = os.path.join(module_dir, "test_output_data")


class TestPreprocess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing
    """

    cleaned_csv_file_path = OP_DATA_FOLDER
    mcf_file_path = OP_DATA_FOLDER
    tmcf_file_path = OP_DATA_FOLDER

    ip_files = os.listdir(os.path.join(TEST_DATA_FOLDER, "test_files"))
    ip_data_path = [
        os.path.join(os.path.join(TEST_DATA_FOLDER, "test_files"), file_name)
        for file_name in ip_files
    ]

    base = CensusUSAPopulationByRace(ip_data_path, cleaned_csv_file_path,
                                     mcf_file_path, tmcf_file_path)
    base.process()

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF File
        """
        files = [
            "USA_Population_Count_by_Race_before_2000",
            "USA_Population_Count_by_Race_county_after_2000",
            "USA_Population_Count_by_Race_National_state_2000"
        ]
        for file in files:
            temp_mcf_file = file + ".mcf"
            expected_mcf_file_path = os.path.join(TEST_DATA_FOLDER,
                                                  "expected_files",
                                                  temp_mcf_file)

            with open(expected_mcf_file_path,
                      encoding="UTF-8") as expected_mcf_file:
                expected_mcf_data = expected_mcf_file.read()

            temp_tmcf_file = file + ".tmcf"
            expected_tmcf_file_path = os.path.join(TEST_DATA_FOLDER,
                                                   "expected_files",
                                                   temp_tmcf_file)
            with open(expected_tmcf_file_path,
                      encoding="UTF-8") as expected_tmcf_file:
                expected_tmcf_data = expected_tmcf_file.read()

            with open(os.path.join(self.mcf_file_path, temp_mcf_file),
                      encoding="UTF-8") as mcf_file:
                mcf_data = mcf_file.read()

            with open(os.path.join(self.tmcf_file_path, temp_tmcf_file),
                      encoding="UTF-8") as tmcf_file:
                tmcf_data = tmcf_file.read()

            self.assertEqual(expected_mcf_data.strip(), mcf_data.strip())
            self.assertEqual(expected_tmcf_data.strip(), tmcf_data.strip())
        shutil.rmtree(self.cleaned_csv_file_path, ignore_errors=True)

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(
            TEST_DATA_FOLDER, "expected_USA_Population_Count_by_Race.csv")

        expected_csv_data = ""
        files = [
            "USA_Population_Count_by_Race_before_2000",
            "USA_Population_Count_by_Race_county_after_2000",
            "USA_Population_Count_by_Race_National_state_2000"
        ]
        for file in files:
            temp_csv_file = file + ".csv"
            expected_csv_file_path = os.path.join(TEST_DATA_FOLDER,
                                                  "expected_files",
                                                  temp_csv_file)
            with open(expected_csv_file_path,
                      encoding="utf-8-sig") as expected_csv_file:
                expected_csv_data = expected_csv_file.read()
            with open(os.path.join(self.cleaned_csv_file_path, temp_csv_file),
                      encoding="UTF-8") as csv_file:
                csv_data = csv_file.read()

            self.assertEqual(expected_csv_data.strip(), csv_data.strip())
