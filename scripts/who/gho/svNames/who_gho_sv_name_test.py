# Copyright 2022 Google LLC
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
from who_gho_sv_name import generate_mcf_with_processed_names

MODULE_DIR = os.path.dirname(__file__)
TEST_DATA_DIR = os.path.join(MODULE_DIR, "test_data")


class TestGenerateSvNames(unittest.TestCase):

    def test_generate_mcf_with_processed_names(self):
        sv_file = os.path.join(TEST_DATA_DIR, "who_gho_stat_vars.mcf")
        properties_file = os.path.join(TEST_DATA_DIR, "who_properties.mcf")
        name_replacements_file = os.path.join(MODULE_DIR,
                                              "name_replacements.json")
        expected_sv_mcf = os.path.join(TEST_DATA_DIR, "expected_who_sv.mcf")

        generate_mcf_with_processed_names(properties_file, sv_file,
                                          name_replacements_file, TEST_DATA_DIR)

        # check csv.
        with open(os.path.join(TEST_DATA_DIR, "updated_who_gho_stat_vars.mcf"),
                  'r+') as actual_f:
            actual: str = actual_f.read()
        with open(expected_sv_mcf, 'r+') as expected_f:
            expected: str = expected_f.read()
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
