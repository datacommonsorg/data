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
'''Tests for config.py'''

import os
import sys
import tempfile
import shutil
import unittest

from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

_TEST_DIR = os.path.join(_SCRIPT_DIR, 'test_data')

import mcf_diff

from counters import Counters
from mcf_file_util import load_mcf_nodes, write_mcf_nodes

_SAMPLE_MCF_NODES = '''
# Sample nodes
Node: SampleNode1
dcid: "SampleNode1"
typeOf: schema:Class
description: "Sample node"
myProp: dcs:Value
multiValueProp: dcs:Value1, schame:Value2
strProp: "String value for a property"

Node: dcid:Node2
name: "Sample node"
propInt: 123
propRange: [10 20 Years]
'''

_node1 = {
    'Node': 'dcid:Node1',
    'typeOf': 'dcs:Class',
    'prop1': 'dcs:Value',
    'prop2': 'dcs:DeletedProp',
    'propList': 'dcs:Value3,dcs:Value2',
    'strProp': '"Quoted String"',
    'propRange': '[10 20 Years]',
}

_node2 = {
    'Node': 'dcid:Node1',
    'propList': 'dcid:Value2,dcid:Value3,dcid:Value1',
    'prop1': 'dcid:Value',
    'propRange': '[Years 10 20]',
    'strProp': '"Some quoted string"',
    'newProp2': 'schema:NewValue',
    'typeOf': 'dcid:Class',
}


class TestMCFDiff(unittest.TestCase):

    def setUp(self):
        # Create a temp directory
        self._tmp_dir = tempfile.mkdtemp()
        self._sample_mcf_file = os.path.join(self._tmp_dir, 'sample.mcf')
        with open(self._sample_mcf_file, 'w') as file:
            file.write(_SAMPLE_MCF_NODES)

    def tearDown(self):
        # Remove the temp directory
        shutil.rmtree(self._tmp_dir)

    def test_diff_mcf_node_pvs(self):
        '''Test diff on MCF node dictionary.'''
        has_diff, diff_str = mcf_diff.diff_mcf_node_pvs(_node1, _node2)
        self.assertTrue(has_diff)
        expected_diff_str = '''  Node: dcid:Node1
  typeOf: dcid:Class
+ newProp2: dcid:NewValue
  prop1: dcid:Value
- prop2: dcid:DeletedProp
- propList: dcid:Value2,dcid:Value3
+ propList: dcid:Value1,dcid:Value2,dcid:Value3
?           ++++++++++++

  propRange: [10 20 Years]
- strProp: "Quoted String"
?           ^      ^

+ strProp: "Some quoted string"
?           ^^^^^^      ^
'''
        self.assertEqual(diff_str, expected_diff_str)

        # Diff with properies ignored.
        has_diff, diff_str = mcf_diff.diff_mcf_node_pvs(_node1, _node2, {
            'ignore_property': ['newProp2', 'prop2', 'propList', 'strProp'],
        })
        self.assertFalse(has_diff)
        expected_str = '''  Node: dcid:Node1
  typeOf: dcid:Class
  prop1: dcid:Value
  propRange: [10 20 Years]'''
        self.assertEqual(diff_str, expected_str)

    def test_diff_mcf_files(self):
        nodes1 = load_mcf_nodes(self._sample_mcf_file)
        nodes2 = dict(nodes1)

        # change the name for Node1
        # Name is ignored.
        nodes2['dcid:SampleNode1']['name'] = 'sample node one'
        nodes2['dcid:NewNode'] = _node2
        mcf_file2 = os.path.join(self._tmp_dir, 'sample_nodes2.mcf')
        write_mcf_nodes(nodes2, mcf_file2)

        counters = Counters()
        diff_str = mcf_diff.diff_mcf_files(self._sample_mcf_file, mcf_file2,
                                           mcf_diff.get_diff_config(), counters)
        expected_diff_str = '''- 
+ Node: dcid:Node1
+ typeOf: dcid:Class
+ newProp2: dcid:NewValue
+ prop1: dcid:Value
+ propList: dcid:Value1,dcid:Value2,dcid:Value3
+ propRange: [10 20 Years]
+ strProp: "Some quoted string"

'''
        self.assertEqual(diff_str, expected_diff_str)
        self.assertEqual(counters.get_counter('nodes matched'), 2)
        self.assertEqual(counters.get_counter('PVs matched'), 8)
        self.assertEqual(counters.get_counter('dcid missing in nodes1'), 1)
