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
from preprocess import process

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)
test_data_folder = os.path.join(module_dir_, "test_data")
op_data_folder = os.path.join(module_dir_, "test_output_data")


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
    process(config_files,[["county_result_2010_2020.csv",
        "state_result_2000_2010.csv"],
    ["county_result_1970_1979.csv","state_result_1990_2000.csv"],
    ["nationals_result_1980_1990.csv","nationals_result_1990_2000.csv"]])

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF and TMCF File
        """
        exp_files_mcf = ["expected_sex_race_aggregate_state_2010_2020.mcf"]
        exp_files_tmcf = ["expected_sex_race_aggregate_state_2010_2020.tmcf"]
        oup_files_mcf = ["sex_race_aggregate_state_2010_2020.mcf"]
        oup_files_tmcf = ["sex_race_aggregate_state_2010_2020.tmcf"]
        for exp_file_mcf, oup_file_mcf in zip(exp_files_mcf,oup_files_mcf):
            expected_mcf_file_path = os.path.join(
                test_data_folder, exp_file_mcf)
            with open(expected_mcf_file_path,
                    encoding="UTF-8") as expected_mcf_file:
                expected_mcf_data = expected_mcf_file.read()
            with open(oup_file_mcf, encoding="UTF-8") as mcf_file:
                mcf_data = mcf_file.read()
            self.assertEqual(expected_mcf_data.strip(), mcf_data.strip())

        for exp_file_tmcf, oup_file_tmcf in zip(exp_files_tmcf,oup_files_tmcf):
            expected_tmcf_file_path = os.path.join(
                test_data_folder, exp_file_tmcf)
            with open(expected_tmcf_file_path,
                    encoding="UTF-8") as expected_tmcf_file:
                expected_tmcf_data = expected_tmcf_file.read()
            with open(oup_file_tmcf, encoding="UTF-8") as tmcf_file:
                tmcf_data = tmcf_file.read()
            self.assertEqual(expected_tmcf_data.strip(), tmcf_data.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        self.maxDiff = None
        exp_files = ["expected_postprocess_aggregate_state_2010_2020.csv"]
        oup_files = ["postprocess_aggregate_state_2010_2020.csv"]
        for exp_file, oup_file in zip(exp_files,oup_files):

            expected_csv_file_path = os.path.join(
                test_data_folder, exp_file)

            expected_csv_data = ""
            with open(expected_csv_file_path,
                    encoding="utf-8-sig") as expected_csv_file:
                expected_csv_data = expected_csv_file.read()

            with open(oup_file, encoding="utf-8-sig") as csv_file:
                csv_data = csv_file.read()

            self.assertEqual(expected_csv_data.strip(), csv_data.strip())
