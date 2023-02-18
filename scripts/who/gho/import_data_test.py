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
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from import_data import import_data

MODULE_DIR = os.path.dirname(__file__)
TEST_DATA_DIR = os.path.join(MODULE_DIR, "test_data")


class TestImportData(unittest.TestCase):

    def test_import_data(self):
        # data files are from downloading the data for 3 of the indicators using
        # the WHO API: https://ghoapi.azureedge.net/api/<INDICATOR CODE>
        data_files = [
            os.path.join(TEST_DATA_DIR, "EMFLIMITELECTRIC.json"),
            os.path.join(TEST_DATA_DIR, "WSH_8.json"),
            os.path.join(TEST_DATA_DIR, "Adult_curr_cig_smoking.json")
        ]
        curated_dim_map = os.path.join(MODULE_DIR, "curated_dim_map.json")
        curated_sv_map = os.path.join(TEST_DATA_DIR,
                                      "test_curated_sv_dcid_map.json")
        expected_csv = os.path.join(TEST_DATA_DIR, "expected_csv.csv")
        expected_sv_mcf = os.path.join(TEST_DATA_DIR, "expected_sv.mcf")
        expected_generated_schema_mcf = os.path.join(
            TEST_DATA_DIR, "expected_generated_schema.mcf")
        expected_skipped_mcf_sv = os.path.join(TEST_DATA_DIR,
                                               "expected_skipped_mcf_sv.json")

        import_data(data_files, curated_dim_map, curated_sv_map, TEST_DATA_DIR,
                    "")

        # check csv.
        with open(os.path.join(TEST_DATA_DIR, "who.csv"), 'r+') as actual_f:
            actual: str = actual_f.read()
        with open(expected_csv, 'r+') as expected_f:
            expected: str = expected_f.read()
        self.assertEqual(actual, expected)

        # check sv mcf.
        with open(os.path.join(TEST_DATA_DIR, "who_sv.mcf"), 'r+') as actual_f:
            actual: str = actual_f.read()
        with open(expected_sv_mcf, 'r+') as expected_f:
            expected: str = expected_f.read()
        self.assertEqual(actual, expected)

        # check generated schema mcf.
        with open(os.path.join(TEST_DATA_DIR, "who_generated_schema.mcf"),
                  'r+') as actual_f:
            actual: str = actual_f.read()
        with open(expected_generated_schema_mcf, 'r+') as expected_f:
            expected: str = expected_f.read()
        self.assertEqual(actual, expected)

        # check skipped dcids.
        with open(os.path.join(TEST_DATA_DIR, "skipped_mcf_sv.json"),
                  'r+') as actual_f:
            actual: str = actual_f.read()
        with open(expected_skipped_mcf_sv, 'r+') as expected_f:
            expected: str = expected_f.read()
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
