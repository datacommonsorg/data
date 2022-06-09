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
Script to automate the testing for EuroStat Physical Activity process script.
"""

import os
from os import path
import unittest
from process import EuroStatPhysicalActivity
# module_dir is the path to where this test is running from.
module_dir = os.path.dirname(__file__)
test_data_folder = os.path.join(module_dir, "test_files")
op_data_folder = os.path.join(module_dir, "test_output_data")
input_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + "input_data"


class TestPreprocess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing.
    The test will be conducted for EuroStat Physical Activity
    It will be generating CSV, MCF and TMCF files based on the sample input.
    Comparing the data with the expected files.
    """
    cleaned_csv_file_path = os.path.join(op_data_folder, "data.csv")
    mcf_file_path = os.path.join(op_data_folder, "test_census.mcf")
    tmcf_file_path = os.path.join(op_data_folder, "test_census.tmcf")
    test_input_path = (os.path.dirname(os.path.abspath(__file__)) + os.sep +
                       'test_files/test_input_files')
    ip_data = os.listdir(test_input_path)
    ip_data = [
        os.path.dirname(os.path.abspath(__file__)) + os.sep +
        'test_files/test_input_files' + os.sep + file for file in ip_data
    ]

    base = EuroStatPhysicalActivity(ip_data, cleaned_csv_file_path,
                                    mcf_file_path, tmcf_file_path)
    base.process()

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF File
        """
        expected_mcf_file_path = os.path.join(
            test_data_folder,
            "expected_eurostat_population_physicalactivity.mcf")

        expected_tmcf_file_path = os.path.join(
            test_data_folder,
            "expected_eurostat_population_physicalactivity.tmcf")

        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        with open(self.mcf_file_path, encoding="UTF-8") as mcf_file:
            actual_mcf_data = mcf_file.read()

        with open(self.tmcf_file_path, encoding="UTF-8") as tmcf_file:
            actual_tmcf_data = tmcf_file.read()
        if path.exists(self.mcf_file_path):
            os.remove(self.mcf_file_path)
        if path.exists(self.tmcf_file_path):
            os.remove(self.tmcf_file_path)

        self.assertEqual(expected_mcf_data.strip(), actual_mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(), actual_tmcf_data.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(
            test_data_folder,
            "expected_eurostat_population_physicalactivity.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8-sig") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        with open(self.cleaned_csv_file_path, encoding="utf-8-sig") as csv_file:
            actual_csv_data = csv_file.read()
        if path.exists(self.cleaned_csv_file_path):
            os.remove(self.cleaned_csv_file_path)

        self.assertEqual(expected_csv_data.strip(), actual_csv_data.strip())
