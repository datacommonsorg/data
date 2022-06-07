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

    cleaned_csv_file_path = os.path.join(OP_DATA_FOLDER, "data.csv")
    mcf_file_path = os.path.join(OP_DATA_FOLDER, "test_census")
    tmcf_file_path = os.path.join(OP_DATA_FOLDER, "test_census")
    mcf_file_path1 = os.path.join(OP_DATA_FOLDER, "test_census_State1980")
    tmcf_file_path1 = os.path.join(OP_DATA_FOLDER, "test_census_State1980")


    ip_data_path = [os.path.join(TEST_DATA_FOLDER, \
        "test_census_data_USCountyak90.txt")]

    base = CensusUSAPopulationByRace(ip_data_path, cleaned_csv_file_path,
                                     mcf_file_path, tmcf_file_path)
    base.process()

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF File
        """
        expected_mcf_file_path = os.path.join(
            TEST_DATA_FOLDER, "expected_USA_Population_Count_by_Race.mcf")
        expected_mcf_file_path1 = os.path.join(
            TEST_DATA_FOLDER,
            "expected_USA_Population_Count_by_Race_State1980.mcf")

        expected_tmcf_file_path = os.path.join(
            TEST_DATA_FOLDER, "expected_USA_Population_Count_by_Race.tmcf")
        expected_tmcf_file_path1 = os.path.join(
            TEST_DATA_FOLDER,
            "expected_USA_Population_Count_by_Race_State1980.tmcf")

        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()
        with open(expected_mcf_file_path1,
                  encoding="UTF-8") as expected_mcf_file1:
            expected_mcf_data1 = expected_mcf_file1.read()

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()
        with open(expected_tmcf_file_path1,
                  encoding="UTF-8") as expected_tmcf_file1:
            expected_tmcf_data1 = expected_tmcf_file1.read()

        with open(self.mcf_file_path + ".mcf", encoding="UTF-8") as mcf_file:
            mcf_data = mcf_file.read()
        with open(self.mcf_file_path1 + ".mcf", encoding="UTF-8") as mcf_file1:
            mcf_data1 = mcf_file1.read()

        with open(self.tmcf_file_path + ".tmcf", encoding="UTF-8") as tmcf_file:
            tmcf_data = tmcf_file.read()
        with open(self.tmcf_file_path1 + ".tmcf",
                  encoding="UTF-8") as tmcf_file1:
            tmcf_data1 = tmcf_file1.read()

        if path.exists(self.mcf_file_path):
            os.remove(self.mcf_file_path)
        if path.exists(self.tmcf_file_path):
            os.remove(self.tmcf_file_path)

        self.assertEqual(expected_mcf_data.strip(), mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(), tmcf_data.strip())
        self.assertEqual(expected_mcf_data1.strip(), mcf_data1.strip())
        self.assertEqual(expected_tmcf_data1.strip(), tmcf_data1.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(
            TEST_DATA_FOLDER, "expected_USA_Population_Count_by_Race.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8-sig") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        with open(self.cleaned_csv_file_path, encoding="utf-8-sig") as csv_file:
            csv_data = csv_file.read()

        if path.exists(self.cleaned_csv_file_path):
            os.remove(self.cleaned_csv_file_path)

        self.assertEqual(expected_csv_data.strip(), csv_data.strip())
