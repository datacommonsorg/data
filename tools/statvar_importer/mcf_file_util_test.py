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
"""Unit tests for stat_var_processor.py."""

from collections import OrderedDict
import os
import sys
import tempfile
import unittest

from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))

import mcf_file_util

from mcf_diff import diff_mcf_files, diff_mcf_nodes

# module_dir_ is the path to where this test is running from.
_module_dir_ = os.path.dirname(__file__)


class TestMCFFileUtil(unittest.TestCase):

    def setUp(self):
        # logging.set_verbosity(2)
        self.maxDiff = None

    def test_strip_namespace(self):
        self.assertEqual(mcf_file_util.strip_namespace('Count_Person'),
                         'Count_Person')
        self.assertEqual(mcf_file_util.strip_namespace('dcs:Count_Person'),
                         'Count_Person')
        self.assertEqual(mcf_file_util.strip_namespace('dcid:Count_Person'),
                         'Count_Person')
        self.assertEqual(mcf_file_util.strip_namespace('"abc:123"'),
                         '"abc:123"')
        self.assertEqual(mcf_file_util.strip_namespace(10), 10)

    def test_add_namespace(self):
        self.assertEqual(mcf_file_util.add_namespace('Count_Person'),
                         'dcid:Count_Person')
        self.assertEqual(mcf_file_util.add_namespace('dcs:Count_Person'),
                         'dcs:Count_Person')
        self.assertEqual(mcf_file_util.add_namespace('"abc 123"'), '"abc 123"')
        self.assertEqual(mcf_file_util.add_namespace(10), 10)

    def test_normalize_mcf_node(self):
        mcf_dict = {
            '#': 'Comment',
            'Node': 'dcid:Count_Person_10Years',
            'typeOf': 'dcs:StatisticalVariable',
            'populationType': 'schema:Person',
            'measuredProperty': 'count',
            'age': '[10 Years]',
            # List of values are sorted
            'name': ['"Count of children"', '"Child Population"'],
            # String value with , is not sorted.
            'description': '"people of 10 years,number of children"',
        }
        normalized_node = mcf_file_util.normalize_mcf_node(mcf_dict)
        # Properties are ordered aphabetically.
        expected_node = OrderedDict([
            ('Node', 'dcid:Count_Person_10Years'),
            ('age', '[10 Years]'),
            ('description', '"people of 10 years,number of children"'),
            ('measuredProperty', 'dcid:count'),
            ('name', '"Child Population","Count of children"'),
            ('populationType', 'dcid:Person'),
            ('typeOf', 'dcid:StatisticalVariable'),
        ])
        self.assertEqual(expected_node, normalized_node)
        # Normalize quantity range to dcid
        normalized_node = mcf_file_util.normalize_mcf_node(
            mcf_dict, quantity_range_to_dcid=True)
        expected_node['age'] = 'dcid:Years10'
        self.assertEqual(expected_node, normalized_node)

    def test_normalize_range(self):
        self.assertEqual('[10 20 Years]',
                         mcf_file_util.normalize_value('[ 10 20 Years ]'))
        self.assertEqual(
            'dcid:Years10To20',
            mcf_file_util.normalize_value('[ 10 20 Years ]', True),
        )
        self.assertEqual('[- 20 Years]',
                         mcf_file_util.normalize_value('[ - 20 Years ]'))
        self.assertEqual(
            'dcid:YearsUpto20',
            mcf_file_util.normalize_value('[ - 20 Years ]', True),
        )
        self.assertEqual('dcid:Years20',
                         mcf_file_util.normalize_value('[ 20  Years ]', True))
        self.assertEqual(
            'dcid:Years20Onwards',
            mcf_file_util.normalize_value('[ 20 - Years ]', True),
        )
        self.assertEqual('dcid:Upto20',
                         mcf_file_util.normalize_value('[ - 20 ]', True))

    def test_load_mcf_file(self):
        mcf_nodes = mcf_file_util.load_mcf_nodes(
            os.path.join(_module_dir_, 'test_data',
                         'sample_output_stat_vars.mcf'))
        self.assertTrue(len(mcf_nodes) > 1)

        # Verify all nodes are keyed by dcid and have expected properties.
        for dcid, node in mcf_nodes.items():
            for expected_prop in ['Node', 'typeOf']:
                self.assertTrue(expected_prop in node)
            self.assertEqual(mcf_file_util.strip_namespace(dcid), node['Node'])

        # Verify loading node with additional property added to existing node.
        dcid = list(mcf_nodes.keys())[0]
        old_node = mcf_nodes[dcid]
        # Change node type to non-StatVar to allow addition of property
        old_node['typeOf'] = 'dcid:TestNode'
        new_node = {'Node': old_node['Node']}
        # Copy some properties
        for prop in list(old_node.keys())[len(old_node) - 2:]:
            new_node[prop] = old_node[prop]
        # Add a new property
        new_node['newProperty'] = 'dcid:NewValue'
        new_node['typeOf'] = 'dcid:TestNode'
        expected_node = dict(old_node)
        expected_node.update(new_node)
        with tempfile.TemporaryDirectory() as tmp_dir:
            new_node_file = os.path.join(tmp_dir, 'new_node.mcf')
            mcf_file_util.write_mcf_nodes(
                node_dicts=[{
                    dcid: new_node
                }],
                filename=new_node_file,
                default_pvs={},
                header='# Node with new property',
            )

            # Load the new node into the dict with old nodes.
            mcf_file_util.load_mcf_nodes(new_node_file, mcf_nodes)

            # Verify the updated node is a union of all PVs.
            self.assertTrue(old_node != new_node)
            self.assertTrue(expected_node != old_node)
            self.assertTrue(expected_node != new_node)
            diff_str = diff_mcf_nodes({dcid: expected_node},
                                      {dcid: mcf_nodes[dcid]})
            self.assertEqual(diff_str, '')

    def test_get_numeric_value(self):
        self.assertEqual(2010, mcf_file_util.get_numeric_value('2010'))
        self.assertEqual(2020, mcf_file_util.get_numeric_value('2020.0'))
        self.assertEqual(5.6, mcf_file_util.get_numeric_value('05.6%'))
        self.assertEqual(123456, mcf_file_util.get_numeric_value('1,23,456.0'))
        self.assertEqual(10.123, mcf_file_util.get_numeric_value('10.123'))
        self.assertEqual(-1.23, mcf_file_util.get_numeric_value('-1.23'))
        self.assertEqual(
            1234567.8,
            mcf_file_util.get_numeric_value(
                '1 234 567,8',
                decimal_char=',',
                separator_chars=' ',
            ))
        self.assertEqual(None, mcf_file_util.get_numeric_value('not number'))
        self.assertEqual(None, mcf_file_util.get_numeric_value('10e5'))

    def test_check_nodes_can_merge(self):
        node1 = {
            'Node': 'dcs:TestNode1',
            'typeOf': 'dcs:TestNode',
            'prop1': 'dcs:Value1',
            'prop2': 'dcid:Value2',
        }
        node2 = {
            'Node': 'dcs:TestNode1',
            'typeOf': 'dcs:TestNode',
            'prop1': 'dcs:Value1',
            'prop3': 'dcid:Value3',
        }

        nodes = {}
        mcf_file_util.add_mcf_node(node1, nodes)
        # Nodes with additional property can be merged.
        self.assertTrue(mcf_file_util.check_nodes_can_merge(node1, node2))
        self.assertTrue(mcf_file_util.add_mcf_node(node2, nodes))
        self.assertEqual(
            nodes['dcid:TestNode1'], {
                'Node': 'dcs:TestNode1',
                'prop1': 'dcs:Value1',
                'prop2': 'dcid:Value2',
                'prop3': 'dcid:Value3',
                'typeOf': 'dcs:TestNode'
            })

        # Statvar nodes with new properties cannot be merged.
        node1['typeOf'] = 'dcs:StatisticalVariable'
        node2['typeOf'] = 'dcid:StatisticalVariable'
        self.assertFalse(mcf_file_util.check_nodes_can_merge(node1, node2))

        # Statvar nodes with new values for existing properties cannot be merged.
        node1['typeOf'] = 'StatisticalVariable'
        node3 = dict(node1)
        node3['prop1'] = 'dcid:NewValue'
        self.assertFalse(mcf_file_util.check_nodes_can_merge(node1, node2))

        # Statvar nodes can't be merged with non-Statvar node
        node1['typeOf'] = 'StatisticalVariable'
        node3 = dict(node1)
        node3['typeOf'] = 'dcid:TestNode'
        self.assertFalse(mcf_file_util.check_nodes_can_merge(node1, node2))

        # Statvar nodes with names can be merged
        node3 = {
            'Node': 'dcid:TestNode1',
            'typeOf': 'dcid:StatisticalVariable',
            'prop1': 'dcs:Value1',
            'prop2': 'dcid:Value2',
            'name': 'test node with name',
            'description': 'TestNode with addiotnal name can be merged.'
        }
        self.assertTrue(mcf_file_util.check_nodes_can_merge(node1, node3))


class TestAddPVToNode(unittest.TestCase):

    def test_add_pv_to_node_new_property(self):
        node = {}
        mcf_file_util.add_pv_to_node("prop1", "value1", node, normalize=False)
        self.assertEqual(node, {"prop1": "value1"})

    def test_add_pv_to_node_existing_property_append(self):
        node = {"prop1": "value1"}
        mcf_file_util.add_pv_to_node("prop1", "value2", node, normalize=False)
        self.assertEqual(node, {"prop1": "value1,value2"})

    def test_add_pv_to_node_existing_property_replace(self):
        node = {"prop1": "value1"}
        mcf_file_util.add_pv_to_node("prop1",
                                     "value2",
                                     node,
                                     append_value=False,
                                     normalize=False)
        self.assertEqual(node, {"prop1": "value2"})

    def test_add_pv_to_node_strip_namespaces(self):
        node = {}
        mcf_file_util.add_pv_to_node("prop1",
                                     "dcid:value1",
                                     node,
                                     strip_namespaces=True,
                                     normalize=False)
        self.assertEqual(node, {"prop1": "value1"})

    def test_add_pv_to_node_normalize_strip_namespaces(self):
        node = {}
        mcf_file_util.add_pv_to_node("prop1",
                                     "dcid:value1",
                                     node,
                                     strip_namespaces=True,
                                     normalize=True)
        self.assertEqual(node, {"prop1": "value1"})

    def test_add_pv_to_node_spaces_not_stripped(self):
        node = {}
        mcf_file_util.add_pv_to_node("prop1",
                                     "  value1  ",
                                     node,
                                     normalize=False)
        self.assertEqual(node, {"prop1": "  value1  "})

    def test_add_pv_to_node_normalize_strip_spaces(self):
        node = {}
        mcf_file_util.add_pv_to_node("prop1",
                                     "  value1  ",
                                     node,
                                     normalize=True)
        self.assertEqual(node, {"prop1": "value1"})

    def test_add_pv_to_node_comma_separated_values(self):
        node = {}
        mcf_file_util.add_pv_to_node("prop1",
                                     "value1, value2,value3",
                                     node,
                                     normalize=False)
        self.assertEqual(node, {"prop1": "value1, value2,value3"})

    def test_add_pv_to_node_normalized_comma_separated_values(self):
        node = {}
        mcf_file_util.add_pv_to_node("prop1",
                                     "value1, value2,value3",
                                     node,
                                     normalize=True)
        self.assertEqual(node, {"prop1": "dcid:value1,dcid:value2,dcid:value3"})

    def test_add_pv_to_node_normalize_list_values(self):
        node = {}
        mcf_file_util.add_pv_to_node("prop1", ["value1", "value2"],
                                     node,
                                     normalize=False)
        self.assertEqual(node, {"prop1": "value1,value2"})

    def test_add_pv_to_node_normalize_list_values(self):
        node = {}
        mcf_file_util.add_pv_to_node("prop1", ["value1", "value2"],
                                     node,
                                     normalize=True)
        self.assertEqual(node, {"prop1": "dcid:value1,dcid:value2"})

    def test_add_pv_to_node_existing_list_values(self):
        node = {"prop1": "value1,value2"}
        mcf_file_util.add_pv_to_node("prop1", "value3", node, normalize=False)
        self.assertEqual(node, {"prop1": "value1,value2,value3"})

    def test_add_pv_to_node_existing_list_values_with_duplicates(self):
        node = {"prop1": "value1,value2"}
        mcf_file_util.add_pv_to_node("prop1",
                                     "value2,value3",
                                     node,
                                     normalize=False)
        self.assertEqual(node, {"prop1": "value1,value2,value3"})

    def test_add_pv_to_node_existing_list_values_with_duplicates_and_quotes(
            self):
        node = {"prop1": '"value1",value2'}
        mcf_file_util.add_pv_to_node("prop1",
                                     '"value2",value3',
                                     node,
                                     normalize=False)
        self.assertEqual(node, {"prop1": '"value1","value2","value3"'})

    def test_add_pv_to_node_existing_list_values_with_quotes_and_spaces_and_duplicates(
            self):
        node = {"prop1": '"value , 1",value2'}
        mcf_file_util.add_pv_to_node("prop1",
                                     '"value , 1",value3',
                                     node,
                                     normalize=False)
        self.assertEqual(node, {"prop1": '"value , 1","value2","value3"'})

    def test_add_pv_node_mixed_types(self):
        node = {"prop1": 'value1'}
        mcf_file_util.add_pv_to_node("prop1", 10, node, normalize=False)
        self.assertEqual(node, {"prop1": 'value1,10'})
