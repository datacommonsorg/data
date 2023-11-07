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

PLACE_MAPPINGS = {
    '1': 'Earth',
    '2': 'africa',
    '4': 'country/AFG',
    '5': 'southamerica',
    '8': 'country/ALB',
    '9': 'oceania',
    '11': 'WesternAfrica',
    '12': 'country/DZA',
    '13': 'CentralAmerica',
    '14': 'EasternAfrica',
    '840': 'country/USA',
    'AF_MAZAR_E_SHARIF': 'wikidataId/Q130469'
}


def assert_equal_dir(self, result_dir, expected_dir):
    for root, _, files in os.walk(result_dir):
        for file in sorted(files):
            with open(os.path.join(root, file)) as result:
                with open(os.path.join(expected_dir, file)) as expected:
                    self.assertEqual(result.read(), expected.read())


class ProcessTest(unittest.TestCase):

    def test_get_geography(self):
        self.assertEqual(process.get_geography(840, PLACE_MAPPINGS),
                         'dcid:country/USA')
        self.assertEqual(
            process.get_geography('AF_MAZAR_E_SHARIF', PLACE_MAPPINGS),
            'dcid:wikidataId/Q130469')
        self.assertEqual(process.get_geography(1, PLACE_MAPPINGS), 'dcid:Earth')

    def test_get_measurement_method(self):
        d = {'NATURE': ['E'], 'OBS_STATUS': ['A'], 'REPORTING_TYPE': ['G']}
        df = pd.DataFrame.from_dict(d)
        for _, row in df.iterrows():
            self.assertEqual(process.get_measurement_method(row), 'SDG_E_A_G')

    def test_drop_null(self):
        self.assertEqual(
            process.drop_null(
                0, 'SE_ACS_CMPTR',
                'This data point is NIL for the submitting nation.'), '')
        self.assertEqual(process.drop_null(1, 'SE_ACS_CMPTR', ''), 1)

    def test_drop_special(self):
        self.assertEqual(process.drop_special(0, 'SH_SAN_SAFE@URBANISATION--R'),
                         '')
        self.assertEqual(
            process.drop_special(0, 'AG_FOOD_WST@FOOD_WASTE_SECTOR--FWS_OOHC'),
            0)

    def test_fix_encoding(self):
        source = 'Instituto Nacional das Comunicaçőes de Moçambique'
        self.assertEqual(process.fix_encoding(source), source)

    def test_process(self):
        with tempfile.TemporaryDirectory() as tmp_schema:
            with tempfile.TemporaryDirectory() as tmp_csv:
                process.process(
                    os.path.join(module_dir_, 'testdata/test_input'),
                    tmp_schema, tmp_csv, PLACE_MAPPINGS)
                assert_equal_dir(
                    self, tmp_schema,
                    os.path.join(module_dir_, 'testdata/test_schema'))
                assert_equal_dir(self, tmp_csv,
                                 os.path.join(module_dir_, 'testdata/test_csv'))


if __name__ == '__main__':
    unittest.main()
