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
from process import USPrams
# pylint: enable=wrong-import-position

TEST_DATASET_DIR = os.path.join(MODULE_DIR, "test_data", "datasets")

EXPECTED_FILES_DIR = os.path.join(MODULE_DIR, "test_data", "expected_files")


class TestProcess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing.
    The test will be conducted for EuroStat BMI Sample Datasets,
    It will be generating CSV, MCF and TMCF files based on the sample input.
    Comparing the data with the expected files.
    """
    test_data_files = [
        'Alabama-PRAMS-MCH-Indicators-508.pdf',
        'Connecticut-PRAMS-MCH-Indicators-508.pdf',
        'Hawaii-PRAMS-MCH-Indicators-508.pdf'
        'Maine-PRAMS-MCH-Indicators-508.pdf',
        'Massachusetts-PRAMS-MCH-Indicators-508.pdf',
        'Montana-PRAMS-MCH-Indicators-508.pdf',
        'Rhode-Island-PRAMS-MCH-Indicators-508.pdf',
        'West-Virginia-PRAMS-MCH-Indicators-508.pdf',
        'Wyoming-PRAMS-MCH-Indicators-508.pdf'
    ]
    ip_data = [
        os.path.join(TEST_DATASET_DIR, file_name)
        for file_name in test_data_files
    ]
    ip_data = os.listdir(TEST_DATASET_DIR)
    ip_data = [os.path.join(TEST_DATASET_DIR, file) for file in ip_data]

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

        with tempfile.TemporaryDirectory() as tmp_dir:
            CLEANED_CSV_FILE_PATH = os.path.join(tmp_dir, "data.csv")
            MCF_FILE_PATH = os.path.join(tmp_dir, "test_census.mcf")
            TMCF_FILE_PATH = os.path.join(tmp_dir, "test_census.tmcf")

            base = USPrams(self.ip_data, CLEANED_CSV_FILE_PATH, MCF_FILE_PATH,
                           TMCF_FILE_PATH)
            base.process()

            with open(MCF_FILE_PATH, encoding="UTF-8") as mcf_file:
                self.actual_mcf_data = mcf_file.read()

            with open(TMCF_FILE_PATH, encoding="UTF-8") as tmcf_file:
                self.actual_tmcf_data = tmcf_file.read()

            with open(CLEANED_CSV_FILE_PATH, encoding="utf-8-sig") as csv_file:
                self.actual_csv_data = csv_file.read()

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF File
        """
        expected_mcf_file_path = os.path.join(EXPECTED_FILES_DIR, "PRAMS.mcf")

        expected_tmcf_file_path = os.path.join(EXPECTED_FILES_DIR, "PRAMS.tmcf")

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
        expected_csv_file_path = os.path.join(EXPECTED_FILES_DIR, "PRAMS.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        self.assertEqual(expected_csv_data.strip(),
                         self.actual_csv_data.strip())
