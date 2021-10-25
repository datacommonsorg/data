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

import filecmp
import os
import json
import tempfile
import unittest
from os import path
from india_udise.udise_schools.preprocess import UDISESchools
from india_udise.udise_schools.preprocess import ATTRIBUTE_MAPPING
# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestPreprocess(unittest.TestCase):

    def test_create_csv(self):
        years = ["2019-20"]
        api_report_code = "1003"
        api_map_id = "81"

        data_folder = os.path.join(module_dir_, "test_data")

        expected_csv_file_path = os.path.join(
            data_folder, "expected_UDISEIndia_Schools.csv")
        expected_mcf_file_path = os.path.join(
            data_folder, "expected_UDISEIndia_Schools.mcf")

        csv_file_path = os.path.join(data_folder, "UDISEIndia_Schools.csv")
        mcf_file_path = os.path.join(data_folder, "UDISEIndia_Schools.mcf")

        base = UDISESchools(api_report_code,
                            api_map_id,
                            data_folder,
                            csv_file_path,
                            mcf_file_path,
                            years,
                            attribute_mapping=ATTRIBUTE_MAPPING)
        base.process()

        expected_csv_file = open(expected_csv_file_path)
        expected_csv_data = expected_csv_file.read()
        expected_csv_file.close()

        expected_mcf_file = open(expected_mcf_file_path)
        expected_mcf_data = expected_mcf_file.read()
        expected_mcf_file.close()

        csv_file = open(csv_file_path)
        csv_data = csv_file.read()
        csv_file.close()

        mcf_file = open(mcf_file_path)
        mcf_data = mcf_file.read()
        mcf_file.close()

        if path.exists(csv_file_path):
            os.remove(csv_file_path)
        if path.exists(mcf_file_path):
            os.remove(mcf_file_path)
        self.maxDiff = None
        self.assertEqual(expected_mcf_data, mcf_data)
        self.assertEqual(expected_csv_data, csv_data)
