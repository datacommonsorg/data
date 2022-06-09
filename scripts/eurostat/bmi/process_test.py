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
from os import path
import unittest
import sys

module_dir = os.path.dirname(__file__)

sys.path.insert(0, module_dir)

from process import EuroStatBMI
# module_dir is the path to where this test is running from.

test_dataset_folder = os.path.join(module_dir, "test_data", "datasets")
expected_output_folder = os.path.join(module_dir, "test_data", "expected_files")
op_data_folder = os.path.join(module_dir, "test_output_data")
input_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + "input_data"


class TestPreprocess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing.
    The test will be conducted for EuroStat BMI
    It will be generating CSV, MCF and TMCF files based on the sample input.
    Comparing the data with the expected files.
    """
    cleaned_csv_file_path = os.path.join(op_data_folder, "data.csv")
    mcf_file_path = os.path.join(op_data_folder, "test_census.mcf")
    tmcf_file_path = os.path.join(op_data_folder, "test_census.tmcf")

    test_data_files = [
        'hlth_ehis_bm1c.tsv', 'hlth_ehis_de2.tsv', 'hlth_ehis_bm1d.tsv',
        'hlth_ehis_bm1u.tsv', 'hlth_ehis_bm1b.tsv', 'hlth_ehis_de1.tsv',
        'hlth_ehis_bm1e.tsv', 'hlth_ehis_bm1i.tsv'
    ]

    ip_data = [
        os.path.join(test_dataset_folder, file_name)
        for file_name in test_data_files
    ]
    base = EuroStatBMI(ip_data, cleaned_csv_file_path, mcf_file_path,
                       tmcf_file_path)
    base.process()

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF File
        """
        expected_mcf_file_path = os.path.join(
            expected_output_folder, "Expected_EuroStat_Population_BMI.mcf")

        expected_tmcf_file_path = os.path.join(
            expected_output_folder, "Expected_EuroStat_Population_BMI.tmcf")

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
            expected_output_folder, "Expected_EuroStat_Population_BMI.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8-sig") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        with open(self.cleaned_csv_file_path, encoding="utf-8-sig") as csv_file:
            actual_csv_data = csv_file.read()
        if path.exists(self.cleaned_csv_file_path):
            os.remove(self.cleaned_csv_file_path)

        self.assertEqual(expected_csv_data.strip(), actual_csv_data.strip())
