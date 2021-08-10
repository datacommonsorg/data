# Copyright 2021 Google LLC
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

import unittest
import json
import os
from generate_csv_and_sv import generate_csv_and_sv


class TestGenerateCsvAndSv(unittest.TestCase):

    def test_generate_csv_and_sv(self):
        data_files = [
            "./test_data/EMFLIMITELECTRIC.json", "./test_data/WSH_8.json", "./test_data/Adult_curr_cig_smoking.json"
        ]
        with open("./test_data/schema_mapping.json", "r+") as schema_mapping:
            schema_mapping = json.load(schema_mapping)
        output_dir = "./test_data"
        expected_csv = "./test_data/expected.csv"
        expected_mcf = "./test_data/expected.mcf"

        generate_csv_and_sv(data_files, schema_mapping, output_dir)

        # check csv.
        with open(os.path.join(output_dir, "who.csv"), 'r+') as actual_f:
            actual: str = actual_f.read()
        with open(expected_csv, 'r+') as expected_f:
            expected: str = expected_f.read()
        self.assertEqual(actual, expected)

        # check mcf.
        with open(os.path.join(output_dir, "who_sv.mcf"), 'r+') as actual_f:
            actual: str = actual_f.read()
        with open(expected_mcf, 'r+') as expected_f:
            expected: str = expected_f.read()
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
