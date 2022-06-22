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
MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(0, MODULE_DIR)
# pylint: disable=wrong-import-position
from process import EuroStatAlcoholConsumption
# pylint: enable=wrong-import-position

TEST_DATASET_DIR = os.path.join(MODULE_DIR, "test_data", "datasets")
EXPECTED_FILES_DIR = os.path.join(MODULE_DIR, "test_data", "expected_files")
OUTPUT_DATA_DIR = os.path.join(MODULE_DIR, "test_output_data")


class TestProcess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing.
    The test will be conducted for EuroStat BMI Sample Datasets,
    It will be generating CSV, MCF and TMCF files based on the sample input.
    Comparing the data with the expected files.
    """
    ip_data = os.listdir(TEST_DATASET_DIR)
    ip_data = [TEST_DATASET_DIR + os.sep + file for file in ip_data]

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

        with tempfile.TemporaryDirectory() as tmp_dir:
            # pylint: disable=invalid-name
            _CLEANED_CSV_FILE_PATH = os.path.join(tmp_dir, "data.csv")
            _MCF_FILE_PATH = os.path.join(tmp_dir, "test_census.mcf")
            _TMCF_FILE_PATH = os.path.join(tmp_dir, "test_census.tmcf")

            base = EuroStatAlcoholConsumption(self.ip_data,
                                              _CLEANED_CSV_FILE_PATH,
                                              _MCF_FILE_PATH, _TMCF_FILE_PATH)
            base.process()

            with open(_MCF_FILE_PATH, encoding="UTF-8") as mcf_file:
                self.actual_mcf_data = mcf_file.read()

            with open(_TMCF_FILE_PATH, encoding="UTF-8") as tmcf_file:
                self.actual_tmcf_data = tmcf_file.read()

            with open(_CLEANED_CSV_FILE_PATH, encoding="UTF-8") as csv_file:
                self.actual_csv_data = csv_file.read()
            # pylint: enable=invalid-name

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF File
        """
        expected_mcf_file_path = os.path.join(
            EXPECTED_FILES_DIR,
            "expected_eurostat_population_alcoholconsumption.mcf")

        expected_tmcf_file_path = os.path.join(
            EXPECTED_FILES_DIR,
            "expected_eurostat_population_alcoholconsumption.tmcf")

        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        self.assertEqual(expected_mcf_data.strip(),
                         self.actual_mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(),
                         self.actual_tmcf_data.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(
            EXPECTED_FILES_DIR,
            "expected_eurostat_population_alcoholconsumption.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="UTF-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        self.assertEqual(expected_csv_data.strip(),
                         self.actual_csv_data.strip())
