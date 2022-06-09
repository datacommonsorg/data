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
from os import path
import unittest
from process import EuroStatAlcoholConsumption
# module_dir_ is the path to where this test is running from.
MODULE_DIR_ = os.path.dirname(__file__)
TEST_DATA_FOLDER = os.path.join(MODULE_DIR_, "test_data")
OP_DATA_FOLDER = os.path.join(MODULE_DIR_, "test_output_data")
INPUT_PATH = os.path.dirname(os.path.abspath(__file__)) + os.sep + "input_data"


class TestPreprocess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing.
    The test will be conducted for EuroStat Physical Activity
    It will be generating CSV, MCF and TMCF files based on the sample input.
    Comparing the data with the expected files.
    """
    CLEANED_CSV_FILE_PATH = os.path.join(OP_DATA_FOLDER, "data.csv")
    MCF_FILE_PATH = os.path.join(OP_DATA_FOLDER, "test_census.mcf")
    TMCF_FILE_PATH = os.path.join(OP_DATA_FOLDER, "test_census.tmcf")
    test_input_path = (os.path.dirname(os.path.abspath(__file__)) + os.sep
        + 'test_data/test_input_files')
    ip_data = os.listdir(test_input_path)
    ip_data = [os.path.dirname(os.path.abspath(__file__)) + os.sep
        + 'test_data/test_input_files' + os.sep + file for file in ip_data]
        
    base = EuroStatAlcoholConsumption(ip_data, CLEANED_CSV_FILE_PATH,
                                    MCF_FILE_PATH, TMCF_FILE_PATH)
    base.process()

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF File
        """
        expected_MCF_FILE_PATH = os.path.join(
            TEST_DATA_FOLDER,
            "expected_eurostat_population_alcoholconsumption.mcf")

        expected_TMCF_FILE_PATH = os.path.join(
            TEST_DATA_FOLDER,
            "expected_eurostat_population_alcoholconsumption.tmcf")

        with open(expected_MCF_FILE_PATH,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_TMCF_FILE_PATH,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        with open(self.MCF_FILE_PATH, encoding="UTF-8") as mcf_file:
            actual_mcf_data = mcf_file.read()

        with open(self.TMCF_FILE_PATH, encoding="UTF-8") as tmcf_file:
            actual_tmcf_data = tmcf_file.read()
        if path.exists(self.MCF_FILE_PATH):
            os.remove(self.MCF_FILE_PATH)
        if path.exists(self.TMCF_FILE_PATH):
            os.remove(self.TMCF_FILE_PATH)

        self.assertEqual(expected_mcf_data.strip(), actual_mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(), actual_tmcf_data.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(
            TEST_DATA_FOLDER,
            "expected_eurostat_population_alcoholconsumption.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8-sig") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        with open(self.CLEANED_CSV_FILE_PATH, encoding="utf-8-sig") as csv_file:
            actual_csv_data = csv_file.read()
        if path.exists(self.CLEANED_CSV_FILE_PATH):
            os.remove(self.CLEANED_CSV_FILE_PATH)

        self.assertEqual(expected_csv_data.strip(), actual_csv_data.strip())
