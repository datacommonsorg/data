# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for validator_goldens.py"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Set up paths as in validator_goldens.py
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_SCRIPT_DIR.split('/data/')[0], 'data')
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(_DATA_DIR)
sys.path.append(os.path.join(_DATA_DIR, 'util'))
sys.path.append(os.path.join(_DATA_DIR, 'tools', 'statvar_importer'))

import validator_goldens
from counters import Counters


class TestValidatorGoldens(unittest.TestCase):

    def test_get_validator_goldens_config(self):
        with patch('validator_goldens._FLAGS') as mock_flags:
            mock_flags.goldens_ignore_property = ['p1']
            mock_flags.goldens_key_property = ['p2']
            config = validator_goldens.get_validator_goldens_config()
            self.assertEqual(config['goldens_ignore_property'], ['p1'])
            self.assertEqual(config['goldens_key_property'], ['p2'])

    @patch('validator_goldens.mcf_file_util')
    def test_normalize_value(self, mock_mcf):
        # Test string with quotes
        self.assertEqual(validator_goldens.normalize_value(' "val" '), 'val')
        # Test float normalization
        self.assertEqual(validator_goldens.normalize_value(1.20), '1.2')
        # Test namespace stripping
        mock_mcf.strip_namespace.return_value = 'val'
        self.assertEqual(
            validator_goldens.normalize_value('dcid:val',
                                              strip_namespaces=True), 'val')
        mock_mcf.strip_namespace.assert_called_with('dcid:val')
        # Test list normalization
        mock_mcf.normalize_list.return_value = 'v1,v2'
        self.assertEqual(validator_goldens.normalize_value('v1,v2'), 'v1,v2')
        mock_mcf.normalize_list.assert_called_with('v1,v2')
        # Test alphanumeric string
        self.assertEqual(validator_goldens.normalize_value('simple'), 'simple')

    def test_get_node_fingerprint(self):
        node = {'p1': 'v1', 'p2': 'v2', 'p3': 'v3'}
        # All properties (default)
        self.assertEqual(validator_goldens.get_node_fingerprint(node),
                         'p1=v1;p2=v2;p3=v3')
        # Specific key properties
        self.assertEqual(
            validator_goldens.get_node_fingerprint(node,
                                                   key_property={'p1', 'p3'}),
            'p1=v1;p3=v3')
        # Ignore properties
        self.assertEqual(
            validator_goldens.get_node_fingerprint(node,
                                                   ignore_property={'p2'}),
            'p1=v1;p3=v3')
        # Combined key and ignore
        self.assertEqual(
            validator_goldens.get_node_fingerprint(node,
                                                   key_property={'p1', 'p2'},
                                                   ignore_property={'p2'}),
            'p1=v1')

    def test_validator_compare_nodes(self):
        input_nodes = {
            'n1': {
                'p1': 'v1',
                'p2': 'v2'
            },
            'n2': {
                'p1': 'v3',
                'p2': 'v4'
            }
        }
        golden_nodes = {'g1': {'p1': 'v1'}, 'g2': {'p1': 'v5'}}
        config = {'goldens_key_property': ['p1']}
        counters = Counters()
        missing = validator_goldens.validator_compare_nodes(
            input_nodes, golden_nodes, config, counters)
        # Expected fingerprint for g2 is p1=v5, which is not in input_nodes
        self.assertEqual(missing, ['p1=v5'])
        self.assertEqual(counters.get_counter('validate-goldens-missing'), 1)
        self.assertEqual(counters.get_counter('validate-goldens-matched'), 1)

    def test_validator_compare_nodes_multiple_sets(self):
        input_nodes = {
            'n1': {
                'p1': 'v1',
                'p2': 'v2'
            },
            'n2': {
                'p1': 'v1',
                'p3': 'v3'
            }
        }
        golden_nodes = {
            'g1': {
                'p1': 'v1',
                'p2': 'v2'
            },
            'g2': {
                'p1': 'v1',
                'p3': 'v3'
            }
        }
        # config empty, so it will group by all props in each golden node
        counters = Counters()
        missing = validator_goldens.validator_compare_nodes(
            input_nodes, golden_nodes, {}, counters)
        self.assertEqual(missing, [])
        self.assertEqual(counters.get_counter('validate-goldens-matched'), 2)

    @patch('validator_goldens.file_util')
    @patch('validator_goldens.mcf_file_util')
    def test_load_nodes_from_file(self, mock_mcf, mock_file):
        mock_file.file_get_matching.return_value = ['f1.csv', 'f2.mcf']
        mock_file.file_is_csv.side_effect = lambda x: x.endswith('.csv')
        mock_file.file_load_csv_dict.return_value = {0: {'p1': 'v1'}}
        mock_mcf.load_file_nodes.return_value = {'dcid:n1': {'p1': 'v2'}}
        mock_mcf.strip_namespace.return_value = 'n1'

        def side_effect_add(pvs, nodes, **kwargs):
            nodes[pvs['dcid']] = pvs
            return True

        mock_mcf.add_mcf_node.side_effect = side_effect_add

        nodes = validator_goldens.load_nodes_from_file('dummy')

        self.assertEqual(len(nodes), 2)
        self.assertIn(0, nodes)
        self.assertEqual(nodes[0]['p1'], 'v1')
        self.assertIn('n1', nodes)
        self.assertEqual(nodes['n1']['p1'], 'v2')

    @patch('validator_goldens.load_nodes_from_file')
    @patch('validator_goldens.mcf_file_util')
    def test_generate_goldens(self, mock_mcf, mock_load):
        mock_load.return_value = {
            0: {
                'variableMeasured': 'sv1',
                'observationAbout': 'geo1',
                'value': 10
            },
            1: {
                'variableMeasured': 'sv2',
                'observationAbout': 'geo1',
                'value': 20
            },
        }
        property_sets = [{'variableMeasured'},
                         {'variableMeasured', 'observationAbout'}]

        goldens = validator_goldens.generate_goldens('dummy', property_sets)

        # Unique goldens expected:
        # 1. variableMeasured=sv1
        # 2. variableMeasured=sv2
        # 3. observationAbout=geo1;variableMeasured=sv1
        # 4. observationAbout=geo1;variableMeasured=sv2
        self.assertEqual(len(goldens), 4)
        self.assertIn('variableMeasured=sv1', goldens)
        self.assertIn('variableMeasured=sv2', goldens)
        self.assertIn('observationAbout=geo1;variableMeasured=sv1', goldens)
        self.assertIn('observationAbout=geo1;variableMeasured=sv2', goldens)

    @patch('validator_goldens.load_nodes_from_file')
    @patch('validator_goldens.mcf_file_util')
    @patch('validator_goldens.data_sampler')
    def test_generate_goldens_with_sampling(self, mock_sampler, mock_mcf,
                                            mock_load):
        mock_sampler.sample_csv_file.return_value = 'tmp-sample.csv'
        mock_load.return_value = {0: {'p1': 'v1'}}

        property_sets = [{'p1'}]
        config = {'sampler_output_rows': 10}

        with patch('os.path.exists',
                   return_value=True), patch('os.remove') as mock_remove:
            goldens = validator_goldens.generate_goldens('input.csv',
                                                         property_sets,
                                                         config=config)

            self.assertEqual(len(goldens), 1)
            mock_sampler.sample_csv_file.assert_called_once()
            mock_load.assert_called_with('tmp-sample.csv')
            mock_remove.assert_called_with('tmp-sample.csv')

    @patch('validator_goldens.load_nodes_from_file')
    @patch('validator_goldens.mcf_file_util')
    def test_generate_goldens_all_props(self, mock_mcf, mock_load):
        mock_load.return_value = {0: {'p1': 'v1', 'p2': 'v2', 'ignore_me': 'x'}}
        # property_sets is empty, should use all props except ignore_me
        property_sets = []
        config = {'goldens_ignore_property': ['ignore_me']}

        goldens = validator_goldens.generate_goldens('dummy',
                                                     property_sets,
                                                     config=config)

        self.assertEqual(len(goldens), 1)
        key = list(goldens.keys())[0]
        # p1=v1;p2=v2 (alphabetical)
        self.assertEqual(key, 'p1=v1;p2=v2')
        self.assertIn('p1', goldens[key])
        self.assertIn('p2', goldens[key])
        self.assertNotIn('ignore_me', goldens[key])

    @patch('validator_goldens.load_nodes_from_file')
    @patch('validator_goldens.mcf_file_util')
    def test_generate_goldens_with_must_include_values(self, mock_mcf,
                                                       mock_load):
        # Input has two nodes, but only one matches the prominent DCID filter.
        mock_load.return_value = {
            0: {
                'p1': 'v1',
                'p2': 'other'
            },
            1: {
                'p1': 'v2',
                'p2': 'other'
            }
        }
        # Filter for p1=v1
        must_include_values = {'p1': {'v1'}}
        property_sets = [{'p1'}]

        goldens = validator_goldens.generate_goldens(
            'dummy', property_sets, must_include_values=must_include_values)

        # Only v1 should be included because of the filter (non-sampled mode).
        self.assertEqual(len(goldens), 1)
        self.assertIn('p1=v1', goldens)
        self.assertNotIn('p1=v2', goldens)

    @patch('validator_goldens.load_nodes_from_file')
    @patch('validator_goldens.mcf_file_util')
    def test_generate_goldens_all_props_mixed_schema(self, mock_mcf, mock_load):
        # input nodes have different columns
        mock_load.return_value = {0: {'p1': 'v1'}, 1: {'p2': 'v2'}}
        # property_sets is empty, should use each node's own props
        property_sets = []

        goldens = validator_goldens.generate_goldens('dummy', property_sets)

        self.assertEqual(len(goldens), 2)
        self.assertIn('p1=v1', goldens)
        self.assertIn('p2=v2', goldens)

    @patch('validator_goldens.load_nodes_from_file')
    @patch('validator_goldens.validator_compare_nodes')
    @patch('validator_goldens.file_util')
    def test_validate_goldens(self, mock_file, mock_compare, mock_load):
        mock_load.side_effect = [
            {
                'n1': {
                    'p1': 'v1'
                }
            },  # input
            {
                'g1': {
                    'p1': 'v1'
                }
            }  # golden
        ]
        mock_compare.return_value = []

        missing = validator_goldens.validate_goldens('in', 'gold', 'out')

        self.assertEqual(missing, [])
        mock_compare.assert_called_once()


if __name__ == '__main__':
    unittest.main()
