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
"""Tests for generateColMap."""

import csv
import json
import os
import sys
import unittest

# Allows the following module imports to work when running as a script
# relative to data/scripts/
sys.path.append('/'.join([
    '..' for x in filter(lambda x: x == '/',
                         os.path.abspath(__file__).split('data/scripts/')[1])
]))

from generate_col_map import generate_stat_var_map, process_zip_file


# TODO: use a smaller spec which exercises all functions in the module
# TODO: Add smaller unittests for each class / function in the module
# TODO: Update tests to use smaller input / expected files for end-to-end test.
class GenerateColMapTest(unittest.TestCase):
    """ Test Cases for checking the generation of column map from JSON Spec"""

    def test_generating_column_map_from_csv(self):
        header_row = 1
        base_path = os.path.dirname(__file__)
        spec_path = os.path.join(base_path, "./testdata/spec_s2702.json")
        input_csv_path = os.path.join(base_path,
                                      "./testdata/ACSST5Y2013_S2702.csv")
        expected_map_path = os.path.join(
            base_path, "./testdata/column_map_from_csv_expected.json")

        f = open(spec_path, 'r')
        spec_dict = json.load(f)
        f.close()
        column_list = None
        with open(input_csv_path, 'r') as f:
            csv_reader = csv.reader(f)
            for index, line in enumerate(csv_reader):
                if index == header_row:
                    column_list = line
                    break
                continue

        generated_col_map = generate_stat_var_map(spec_dict, column_list)

        f = open(expected_map_path, 'r')
        expected_map = json.load(f)
        f.close()

        self.assertEqual(expected_map, generated_col_map)

    def test_generating_column_map_from_zip(self):
        base_path = os.path.dirname(__file__)
        spec_path = os.path.join(base_path, "./testdata/spec_s2702.json")
        input_zip_path = os.path.join(base_path, "./testdata/s2702_alabama.zip")
        expected_map_path = os.path.join(
            base_path, "./testdata/column_map_from_zip_expected.json")

        generated_col_map = process_zip_file(input_zip_path,
                                             spec_path,
                                             write_output=False)

        f = open(expected_map_path, 'r')
        expected_map = json.load(f)
        f.close()

        self.assertEqual(expected_map, generated_col_map)


if __name__ == '__main__':
    unittest.main()
