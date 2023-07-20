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
'''Tests for util.py.

Usage: python3 -m unittest discover -v -s ../ -p "process_test.py"
'''
import os
import pandas as pd
import sys
import tempfile
import unittest

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from un.sdg import process

module_dir_ = os.path.dirname(__file__)


def assert_equal_dir(self, result_dir, expected_dir):
    for root, _, files in os.walk(result_dir):
        for file in sorted(files):
            with open(os.path.join(root, file)) as result:
                with open(os.path.join(expected_dir, file)) as expected:
                    self.assertEqual(result.read(), expected.read())


class ProcessTest(unittest.TestCase):

    def test_get_geography(self):
        self.assertEqual(process.get_geography(840, 'Country'),
                         'dcs:country/USA')
        self.assertEqual(process.get_geography('AF_MAZAR_E_SHARIF', 'City'),
                         'dcs:wikidataId/Q130469')
        self.assertEqual(process.get_geography(1, 'Region'), 'dcs:Earth')

    def test_get_unit(self):
        self.assertEqual(process.get_unit('CON_USD', 2021), '[CON_USD 2021]')
        self.assertEqual(process.get_unit('CON_USD', float('nan')),
                         'dcs:SDG_CON_USD')

    def test_get_measurement_method(self):
        d = {'NATURE': ['E'], 'OBS_STATUS': ['A'], 'REPORTING_TYPE': ['G']}
        df = pd.DataFrame.from_dict(d)
        for _, row in df.iterrows():
            self.assertEqual(process.get_measurement_method(row), 'SDG_E_A_G')

    def test_process(self):
        with tempfile.TemporaryDirectory() as tmp_schema:
            with tempfile.TemporaryDirectory() as tmp_csv:
                process.process(
                    os.path.join(module_dir_, 'testdata/test_input'),
                    tmp_schema, tmp_csv)
                assert_equal_dir(
                    self, tmp_schema,
                    os.path.join(module_dir_, 'testdata/test_schema'))
                assert_equal_dir(self, tmp_csv,
                                 os.path.join(module_dir_, 'testdata/test_csv'))


if __name__ == '__main__':
    unittest.main()
