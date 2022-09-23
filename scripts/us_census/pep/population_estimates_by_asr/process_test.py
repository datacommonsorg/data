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
import sys
import unittest
import shutil

from national_2020_2021 import national2020
from national_2010_2019 import national2010
from national_2000_2010 import national2000
from state_1990_2000 import state1990
from state_2010_2020 import state2010
from county_1970_1979 import county1970
from county_1980_1989 import county1980
from process import USCensusPEPByASR
# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)
test_data_folder = os.path.join(module_dir_, "test_data")
op_data_folder = os.path.join(module_dir_, "test_output_data")
input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "test_temp_files")


class TestPreprocess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing
    """
    cleaned_csv_file_path = os.path.join(op_data_folder, "data.csv")
    mcf_file_path = os.path.join(op_data_folder, "test_census.mcf")
    tmcf_file_path = os.path.join(op_data_folder, "test_census.tmcf")
    if not os.path.exists(input_path):
        os.mkdir(input_path)
    national_url_file = "test_data/test_input_data/national_test.json"
    state_url_file = "test_data/test_input_data/state_test.json"
    county_url_file = "test_data/test_input_data/county_test.json"
    output_folder = "test_temp_files"
    national2020(national_url_file, output_folder)
    national2010(national_url_file, output_folder)
    national2000(national_url_file, output_folder)
    state2010(state_url_file, output_folder)
    state1990(state_url_file, output_folder)
    county1980(county_url_file, output_folder)
    county1970(county_url_file, output_folder)

    ip_data = [
        os.path.join(input_path, 'county_1970_1979.csv'),
        os.path.join(input_path, 'county_1980_1989.csv'),
        os.path.join(input_path, 'state_1980_1989.csv'),
        os.path.join(input_path, 'state_1990_2000.csv'),
        os.path.join(input_path, 'state_2010_2020.csv'),
        os.path.join(input_path, 'national_1990_2000.csv'),
        os.path.join(input_path, 'national_2000_2010.csv'),
        os.path.join(input_path, 'national_2010_2019.csv'),
        os.path.join(input_path, 'national_2020_2021.csv')
    ]

    base = USCensusPEPByASR(ip_data, cleaned_csv_file_path, mcf_file_path,
                            tmcf_file_path)
    base.process()
    shutil.rmtree(input_path, ignore_errors=True)

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF File
        """
        expected_mcf_file_path = os.path.join(
            test_data_folder, "Expected_Population_Estimates_By_ASR.mcf")

        expected_tmcf_file_path = os.path.join(
            test_data_folder, "Expected_Population_Estimates_By_ASR.tmcf")

        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        with open(self.mcf_file_path, encoding="UTF-8") as mcf_file:
            mcf_data = mcf_file.read()

        with open(self.tmcf_file_path, encoding="UTF-8") as tmcf_file:
            tmcf_data = tmcf_file.read()
        if path.exists(self.mcf_file_path):
            os.remove(self.mcf_file_path)
        if path.exists(self.tmcf_file_path):
            os.remove(self.tmcf_file_path)

        self.assertEqual(expected_mcf_data.strip(), mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(), tmcf_data.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(
            test_data_folder, "Expected_Population_Estimates_By_ASR.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8-sig") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        with open(self.cleaned_csv_file_path, encoding="utf-8-sig") as csv_file:
            csv_data = csv_file.read()
        if path.exists(self.cleaned_csv_file_path):
            os.remove(self.cleaned_csv_file_path)

        self.assertEqual(expected_csv_data.strip(), csv_data.strip())
