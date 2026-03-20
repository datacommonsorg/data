# Copyright 2026 Google LLC
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
"""Unit tests for schema_reconciler.py."""

import sys
import os
import unittest
from unittest import mock

# Add the directory containing schema_reconciler.py to sys.path
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.join(
    _SCRIPT_DIR,
    '../../util'))  # For dc_api_wrapper if needed by schema_reconciler

# Mock dc_api_wrapper before importing schema_reconciler to avoid dependency issues
sys.modules['dc_api_wrapper'] = mock.Mock()

import schema_reconciler


class SchemaReconcilerTest(unittest.TestCase):

    def setUp(self):
        self.schema_nodes = {
            'dcid:OldVal': {
                'Node': 'dcid:OldVal',
                'typeOf': 'dcs:Class',
                'supercededBy': 'dcid:NewVal'
            },
            'dcid:oldProp': {
                'Node': 'dcid:oldProp',
                'typeOf': 'dcs:Property',
                'supercededBy': 'dcid:newProp'
            },
            'dcid:NewVal': {
                'Node': 'dcid:NewVal',
                'typeOf': 'dcs:Class'
            },
            'dcid:newProp': {
                'Node': 'dcid:newProp',
                'typeOf': 'dcs:Property'
            },
            'prop1': {
                'Node': 'prop1'
            },
            'value1': {
                'Node': 'value1'
            },
            'typeOf': {
                'Node': 'typeOf'
            },
            'dcs:StatVarObservation': {
                'Node': 'dcs:StatVarObservation'
            },
        }
        self.reconciler = schema_reconciler.SchemaReconciler(
            config={'recon_lookup_api': False})
        self.reconciler.add_schema_nodes(self.schema_nodes)

        # Configure mock to return empty dict if called
        schema_reconciler.dc_api.dc_api_get_node_property.return_value = {}

    def test_reconcile_simple(self):
        # Test value reconciliation
        nodes = {'node1': {'prop1': 'dcid:OldVal'}}
        num_remapped = self.reconciler.reconcile_nodes(nodes,
                                                       keep_legacy_obs=False)
        self.assertEqual(num_remapped, 1)
        self.assertEqual(nodes['node1']['prop1'], 'dcid:NewVal')

    def test_reconcile_property(self):
        # Test property reconciliation
        nodes = {'node1': {'oldProp': 'value1'}}
        num_remapped = self.reconciler.reconcile_nodes(nodes,
                                                       keep_legacy_obs=False)
        self.assertEqual(num_remapped, 1)
        self.assertIn('newProp', nodes['node1'])
        self.assertEqual(nodes['node1']['newProp'], 'value1')
        self.assertNotIn('oldProp', nodes['node1'])

    def test_keep_legacy_svobs(self):
        nodes = {
            'obs1': {
                'typeOf': 'StatVarObservation',
                'prop1': 'dcid:OldVal'
            }
        }
        num_remapped = self.reconciler.reconcile_nodes(nodes,
                                                       keep_legacy_obs=True)

        # Should have 2 nodes now: original and new
        self.assertEqual(len(nodes), 2)
        self.assertEqual(num_remapped, 1)

        # Original should be unchanged
        self.assertEqual(nodes['obs1']['prop1'], 'dcid:OldVal')

        # New node should have new value
        self.assertIn('obs1-1', nodes)
        self.assertEqual(nodes['obs1-1']['prop1'], 'dcid:NewVal')

    def test_no_change(self):
        nodes = {'node1': {'prop1': 'dcid:NewVal'}}
        num_remapped = self.reconciler.reconcile_nodes(nodes)
        self.assertEqual(num_remapped, 0)
        self.assertEqual(nodes['node1']['prop1'], 'dcid:NewVal')

    def test_list_values(self):
        nodes = {'node1': {'prop1': 'dcid:OldVal, dcid:NewVal'}}
        num_remapped = self.reconciler.reconcile_nodes(nodes,
                                                       keep_legacy_obs=False)
        self.assertEqual(num_remapped, 1)
        # Should be "dcid:NewVal, dcid:NewVal" -> duplicate values might be kept or joined
        # Code: ",".join(remapped_values)
        self.assertEqual(nodes['node1']['prop1'], 'dcid:NewVal,dcid:NewVal')


if __name__ == '__main__':
    unittest.main()
