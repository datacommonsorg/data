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
from preprocess import create_formatted_csv_file

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestPreprocessCSVTest(unittest.TestCase):
    def test_create_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_file = os.path.join(module_dir_,
                                     'test_data/testcase1_data.json')
            expected_file = os.path.join(
                module_dir_, 'test_data/testcase1_expected_data.csv')
            with open(json_file, "r") as f:
                data = json.loads(f.read())
                result_file = os.path.join(
                    tmp_dir, 'testcase1_COVID19_cases_indian_states.csv')
                create_formatted_csv_file(result_file, data)
                same = filecmp.cmp(result_file, expected_file)
                self.assertTrue(same)

    def test_create_csv_skip_unassigned(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_file = os.path.join(module_dir_,
                                     'test_data/testcase2_data.json')
            expected_file = os.path.join(
                module_dir_, 'test_data/testcase2_expected_data.csv')
            with open(json_file, "r") as f:
                data = json.loads(f.read())
                result_file = os.path.join(
                    tmp_dir, 'testcase2_COVID19_cases_indian_states.csv')
                create_formatted_csv_file(result_file, data)
                same = filecmp.cmp(result_file, expected_file)
                os.remove(result_file)

        self.assertTrue(same)


if __name__ == '__main__':
    unittest.main()
