# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for property_value_mapper.py."""

import unittest

import os
import sys

from absl import app
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

from property_value_mapper import PropertyValueMapper


class PropertyValueMapperTest(unittest.TestCase):

    def test_load_pvmap(self):
        pv_mapper = PropertyValueMapper(pv_map_files=[
            os.path.join(_SCRIPT_DIR, 'test_data/sample_pv_map.py')
        ])

        # Verify PVmap has key 'GLOBAL'
        pv_map = pv_mapper.get_pv_map()
        self.assertTrue('GLOBAL' in pv_map)
        self.assertTrue(len(pv_map['GLOBAL']) > 0)

        # Lookup PV Map for known key
        pvs = pv_mapper.get_pvs_for_key('Males')
        self.assertEqual(pvs, {'gender': 'dcs:Male'})

        # Lookup PV Map for case mismatched key fails
        pvs = pv_mapper.get_pvs_for_key('males')
        self.assertEqual(pvs, None)

        # Load PVMap for a different namespace: Variable
        pv_mapper.load_pvs_from_file(
            os.path.join(_SCRIPT_DIR, 'test_data/sample_pv_map.csv'),
            'Variable')
        self.assertTrue('Variable' in pv_mapper.get_pv_map())

        # Lookup PVMap for 'Variable' column
        pvs = pv_mapper.get_pvs_for_key('total', 'Variable')
        self.assertEqual(pvs, {'populationType': 'dcs:Person'})
        # Verify keys from Variable are not retruned for GLOBAL
        pvs = pv_mapper.get_pvs_for_key('total')
        self.assertEqual(pvs, None)

    def test_pvmap_get_all_pvs(self):
        pv_mapper = PropertyValueMapper(pv_map_files=[
            os.path.join(_SCRIPT_DIR, 'test_data/sample_pv_map.py'),
            os.path.join(_SCRIPT_DIR, 'test_data/sample_pv_map.csv'),
        ])
        self.assertEqual(len(pv_mapper.get_pv_map()), 1)

        # Verify matches for words in long key not in pv_map
        pvs = pv_mapper.get_all_pvs_for_value('Total Males')
        expected_pvs = [
            # PVs for 'total'
            {
                'populationType': 'dcs:Person'
            },
            {
                'Key': 'Total'
            },
            # PVs for Male
            {
                'gender': 'dcs:Male'
            },
            {
                'Key': 'Males'
            }
        ]
        self.assertEqual(pvs, expected_pvs)

    def test_process_pvs(self):
        pv_mapper = PropertyValueMapper(pv_map_files=[
            os.path.join(_SCRIPT_DIR, 'test_data/sample_pv_map.py'),
            os.path.join(_SCRIPT_DIR, 'test_data/sample_pv_map.csv'),
        ])

        pvs = pv_mapper.get_pvs_for_key('Person Age')
        self.assertEqual(
            pvs, {
                '#Regex': '(?P<StartAge>[0-9]+)-(?P<EndAge>[0-9]+)',
                'age': 'dcid:{@StartAge}To{@EndAge}Years'
            })
        # Verify processing of regex for range
        self.assertTrue(pv_mapper.process_pvs_for_data('10-20', pvs))
        self.assertEqual(
            pvs, {
                'EndAge': '20',
                'StartAge': '10',
                'age': 'dcid:{@StartAge}To{@EndAge}Years'
            })
