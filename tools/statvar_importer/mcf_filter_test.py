# Copyright 2022 Google LLC
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
"""Tests for mcf_filter.py"""

import os
import shutil
import sys
import tempfile
import unittest

from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

_TEST_DIR = os.path.join(_SCRIPT_DIR, 'test_data')

import mcf_filter

from mcf_file_util import load_mcf_nodes

from counters import Counters
from mcf_file_util import load_mcf_nodes, write_mcf_nodes


class TestMCFFilter(unittest.TestCase):

    def setUp(self):
        # Create a temp directory
        self._tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the temp directory
        shutil.rmtree(self._tmp_dir)

    def test_filter_mcf_file(self):
        # Test filtering nodes from MCF files.
        source_mcf = os.path.join(_TEST_DIR,
                                  'india_census_sample_output_stat_vars.mcf')
        exclude_mcf = os.path.join(_TEST_DIR,
                                   'us_census_B01001_output_stat_vars.mcf')
        source_nodes = load_mcf_nodes(source_mcf)
        exclude_nodes = load_mcf_nodes(exclude_mcf)
        filtered_mcf = os.path.join(self._tmp_dir, 'sample_filtered.mcf')
        filtered_nodes = mcf_filter.filter_mcf_file(source_mcf, exclude_mcf, {},
                                                    filtered_mcf)
        self.assertTrue(len(filtered_nodes) > 0)
        self.assertTrue(len(source_nodes) > len(filtered_nodes))

        # Verify all nodes in exclude mcf are removed from source
        for dcid, pvs in source_nodes.items():
            if dcid:
                if dcid in exclude_nodes:
                    self.assertFalse(dcid in filtered_nodes)
                else:
                    self.assertEqual(pvs, filtered_nodes[dcid])

    def test_drop_existing_mcf_nodes(self):
        mcf_nodes = {
            # Existing statvar
            'Count_Person': {
                'typeOf': 'StatisticalVariable',
                'populationType': 'Person',
                'measuredProperty': 'count',
                'statType': 'measuredValue',
            },
            # Statvar with namespace
            'dcid:Count_Person_Male': {
                'typeOf': 'dcs:StatisticalVariable',
                'populationType': 'dcs:Person',
                'measuredProperty': 'dcs:count',
                'gender': 'dcid:Male',
                'statType': 'dcs:measuredValue',
            },
            # New non existant statvar
            'dcid:Count_Person_Test': {
                'typeOf': 'dcs:StatisticalVariable',
                'populationType': 'dcs:Person',
                'measuredProperty': 'dcs:count',
                'testType': 'dcid:Test',
                'statType': 'dcs:measuredValue',
            },
        }
        filtered_nodes = mcf_filter.drop_existing_mcf_nodes(mcf_nodes)
        self.assertTrue(len(filtered_nodes) > 0)
        self.assertTrue(len(filtered_nodes) < len(mcf_nodes))
        self.assertFalse('Count_Person' in filtered_nodes)
        self.assertFalse('dcid:Count_Person_Male' in filtered_nodes)
        self.assertEqual(
            filtered_nodes['dcid:Count_Person_Test'],
            mcf_nodes['dcid:Count_Person_Test'],
        )
