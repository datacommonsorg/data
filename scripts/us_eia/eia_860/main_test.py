# Copyright 2021 Google LLC
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
"""Test for process_*.py"""

import os
import tempfile
import unittest

import utility
import power_plant

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)

_TEST_CASES = [
    # processor, input-excel, expected-csv
    (utility.process, '1___Utility.xlsx', '1_utility.csv'),
    (power_plant.process, '2___Plant.xlsx', '2_plant.csv'),
]


class TestProcess(unittest.TestCase):

    def test_process(self):
        for (processor, in_file, out_csv) in _TEST_CASES:
            with tempfile.TemporaryDirectory() as tmp_dir:
                in_file = os.path.join(module_dir_, 'test_data', in_file)
                test_csv = os.path.join(tmp_dir, out_csv)

                processor(in_file, test_csv)

                with open(os.path.join(module_dir_, 'test_data', out_csv)) as f:
                    exp_csv_data = f.read()
                with open(test_csv) as f:
                    test_csv_data = f.read()

                os.remove(test_csv)

            self.maxDiff = None
            self.assertEqual(exp_csv_data, test_csv_data)


if __name__ == '__main__':
    unittest.main()