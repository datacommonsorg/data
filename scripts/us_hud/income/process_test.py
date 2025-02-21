# Copyright 2023 Google LLC
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
import filecmp

script_dir = os.path.dirname(os.path.abspath(__file__))

TEST_DIR = os.path.join(script_dir, 'testdata')
OUTPUT_DIR = os.path.join(TEST_DIR, 'output')

# Ensure the module is loaded correctly
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))

from us_hud.income import process


class ProcessTest(unittest.TestCase):

    def test_get_url(self):
        """Test the get_url function and check if it returns the correct URL for the given year."""
        year = 2022
        self.assertEqual(
            process.get_url(year),
            'https://www.huduser.gov/portal/datasets/il/il22/Section8-FY22.xlsx'
        )
        year = 1997
        self.assertEqual(process.get_url(year), '')

    def test_process_with_dynamic_csv(self):
        matches = {'dcs:geoId/02110': 'dcs:geoId/0236400'}
        output_data = []
        input_folder = TEST_DIR

        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        df = process.process(2006, matches, input_folder)
        df.to_csv(os.path.join(OUTPUT_DIR, "output_test.csv"), index=False)
        same = filecmp.cmp(os.path.join(OUTPUT_DIR, "output_test.csv"),
                           os.path.join(TEST_DIR, "expected_output.csv"))
        # Assert that the files are identical
        self.assertTrue(same)


if __name__ == '__main__':
    unittest.main()