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
'''Tests for process.py.

Usage: python3 -m unittest discover -v -s ../ -p "process_test.py"
'''
import os
import pandas as pd
import sys
import unittest
from unittest.mock import patch

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from us_hud.income import process

module_dir_ = os.path.dirname(__file__)

TEST_DIR = os.path.join(module_dir_, 'testdata')


class ProcessTest(unittest.TestCase):

    def test_get_url(self):
        self.assertEqual(
            process.get_url(2022),
            'https://www.huduser.gov/portal/datasets/il/il22/Section8-FY22.xlsx'
        )
        self.assertEqual(process.get_url(1997), '')

    def test_compute_150(self):
        pass

    @patch('pandas.read_excel')
    def test_process(self, mock_df):
        mock_df.return_value = pd.DataFrame(
            pd.read_csv(os.path.join(TEST_DIR, 'test_input_2006.csv')))
        matches = {'dcs:geoId/02110': 'dcs:geoId/0236400'}
        process.process(2006, matches, TEST_DIR)
        with open(os.path.join(TEST_DIR, 'output_2006.csv')) as result:
            with open(os.path.join(TEST_DIR,
                                   'expected_output_2006.csv')) as expected:
                self.assertEqual(result.read(), expected.read())
