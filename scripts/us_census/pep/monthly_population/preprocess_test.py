# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import unittest
from os import path
from preprocess import CensusUSACountryPopulation
# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestPreprocess(unittest.TestCase):

    def test_create_csv(self):

        data_folder = os.path.join(module_dir_, "test_data")

        expected_csv_file_path = os.path.join(
            data_folder, "expected_USA_Population_Count.csv")
        expected_mcf_file_path = os.path.join(
            data_folder, "expected_USA_Population_Count.mcf")
        expected_tmcf_file_path = os.path.join(
            data_folder, "expected_USA_Population_Count.tmcf")

        ip_data_path = [os.path.join(data_folder, "test_census_data.xlsx")]

        op_data_folder = os.path.join(module_dir_, "test_output_data")
        cleaned_csv_file_path = os.path.join(op_data_folder, "data.csv")
        mcf_file_path = os.path.join(op_data_folder, "test_census.mcf")
        tmcf_file_path = os.path.join(op_data_folder, "test_census.tmcf")

        base = CensusUSACountryPopulation(ip_data_path, cleaned_csv_file_path,
                                          mcf_file_path, tmcf_file_path)
        base.process()

        expected_csv_file = open(expected_csv_file_path, encoding="UTF-8-sig")
        expected_csv_data = expected_csv_file.read()
        expected_csv_file.close()

        expected_mcf_file = open(expected_mcf_file_path)
        expected_mcf_data = expected_mcf_file.read()
        expected_mcf_file.close()

        expected_tmcf_file = open(expected_tmcf_file_path)
        expected_tmcf_data = expected_tmcf_file.read()
        expected_tmcf_file.close()

        csv_file = open(cleaned_csv_file_path)
        csv_data = csv_file.read()
        csv_file.close()

        mcf_file = open(mcf_file_path)
        mcf_data = mcf_file.read()
        mcf_file.close()

        tmcf_file = open(tmcf_file_path)
        tmcf_data = tmcf_file.read()
        tmcf_file.close()
        if path.exists(cleaned_csv_file_path):
            os.remove(cleaned_csv_file_path)
        if path.exists(mcf_file_path):
            os.remove(mcf_file_path)
        if path.exists(tmcf_file_path):
            os.remove(tmcf_file_path)

        self.maxDiff = None

        self.assertEqual(expected_csv_data.strip(), csv_data.strip())
        self.assertEqual(expected_mcf_data.strip(), mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(), tmcf_data.strip())
