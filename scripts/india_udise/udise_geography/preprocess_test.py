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
from india_udise.udise_geography.preprocess import UDISEGeography

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestPreprocess(unittest.TestCase):
    def test_create_csv(self):
        test_states_json_data_file_path = os.path.join(
            os.path.dirname(__file__), "test_data/test_UDISE_States.json")
        result_states_csv_file_path = os.path.join(
            os.path.dirname(__file__), "test_data/result_UDISE_States.csv")
        expected_states_csv_file_path = os.path.join(
            os.path.dirname(__file__), "test_data/expected_UDISE_States.csv")

        test_districts_json_data_file_path = os.path.join(
            os.path.dirname(__file__), "test_data/test_UDISE_Districts.json")
        result_districts_csv_data_file_path = os.path.join(
            os.path.dirname(__file__), "test_data/result_UDISE_Districts.csv")
        expected_districts_csv_data_file_path = os.path.join(
            os.path.dirname(__file__),
            "test_data/expected_UDISE_Districts.csv")

        test_blocks_json_data_file_path = os.path.join(
            os.path.dirname(__file__), "test_data/test_UDISE_Blocks.json")
        result_blocks_csv_data_file_path = os.path.join(
            os.path.dirname(__file__), "test_data/result_UDISE_Blocks.csv")
        expected_blocks_csv_data_file_path = os.path.join(
            os.path.dirname(__file__), "test_data/expected_UDISE_Blocks.csv")

        geography = UDISEGeography(
            test_states_json_data_file_path,
            result_states_csv_file_path,
            test_districts_json_data_file_path,
            result_districts_csv_data_file_path,
            test_blocks_json_data_file_path,
            result_blocks_csv_data_file_path,
        )
        geography.process()

        for test_case_files in [(result_states_csv_file_path,
                                 expected_states_csv_file_path),
                                (result_districts_csv_data_file_path,
                                 expected_districts_csv_data_file_path),
                                (result_blocks_csv_data_file_path,
                                 expected_blocks_csv_data_file_path)]:

            result_file = open(test_case_files[0])
            result_data = result_file.read()
            result_file.close()

            expected_file = open(test_case_files[1])
            expected_data = expected_file.read()
            expected_file.close()

            os.remove(test_case_files[0])
            self.assertEqual(expected_data, result_data)
