# Copyright 2023 Google LLC
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
"""Unit tests for schema_resolver.py."""

import os
import sys
import unittest

from absl import app
from absl import logging
import schema_resolver

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class SchemaResolverTest(unittest.TestCase):
    _schema_nodes = {
        'dcid:NewStatVar1': {
            'Node': 'dcid:NewStatVar1',
            'typeOf': 'dcs:StatisticalVariable',
            'populationType': 'dcs:Person',
            'measuredProperty': 'dcs:count',
            'statType': 'dcs:measuredvalue',
            'name': '"New StatVar Node 1"',
            'gender': 'dcid:Male',
            'age': '[10 20 Years]',
        },
        'dcid:Place1': {
            'Node': 'dcid:wikidatsId/Q1234',
            'typeOf': 'dcs:Place',
            'name': 'New Place',
            'wikidataId': 'Q1234',
            'geoId': '06543',
            'state': 'geoId/06',
        },
        'dcid:Place2': {
            'Node': 'dcid:wikidatsId/Q123',
            'typeOf': 'dcs:Place',
            'name': 'Place Two',
            'wikidataId': 'Q123',
            'state': 'geoId/06',
        },
        'dcid:Place3': {
            'Node': 'dcid:wikidatsId/Q678',
            'typeOf': 'dcs:Place',
            'name': 'Place Three',
            'wikidataId': 'Q678',
            'state': 'geoId/04',
        },
        'dcid:ComplexStatVar': {
            'Node':
                'dcid:ComplexStatVar',
            'typeOf':
                'dcid:StatisticalVariable',
            'name':
                'Statvar with quantity range and concatenated values.',
            'description':
                "Complex statvar with values concatenated with __.",
            'alternateName':
                'Age group 10 20 years with values: Value1, Value2.',
            'age':
                '[10 20 Years]',
            'myProp':
                'dcid:Value2__Value1__Value',
            'measuredProperty':
                'count',
            'populationType':
                'dcs:Person',
            'statType':
                'dcid:measuredValue',
        }
    }

    _resolver_config = {
        'resolve_props': ['dcid', 'wikidataId', 'geoId', 'state'],
    }

    def setUp(self):
        # logging.set_verbosity(2)

        # Load nodes into the resolver
        self._resolver = schema_resolver.SchemaResolver(
            os.path.join(_SCRIPT_DIR, 'test_data/sample_output.mcf'),
            self._resolver_config,
        )
        for key, node in self._schema_nodes.items():
            self._resolver.add_node(node)

    def test_resolve_statvar(self):
        lookup_node = {
            'typeOf': 'dcs:StatisticalVariable',
            'populationType': 'dcid:Person',
            'measuredProperty': 'count',
            'statType': 'schema:measuredvalue',
            'gender': 'dcid:Male',
            # Lookup with a QuantityRange dcid
            'age': 'Years10To20',
        }
        resolved_node = self._resolver.resolve_node(lookup_node)
        self.assertEqual('dcid:NewStatVar1', resolved_node.get('Node'))

        # Resolve node with extra properties should fail
        lookup_node['race'] = 'Asian'
        self.assertEqual({}, self._resolver.resolve_node(lookup_node))

        # Resolve with variation of quantity range.
        lookup_node = {
            'age': '[Years 10 20]',  # QuantityRange with unit prefix
            'myProp':
                'Value__Value2__Value1',  # Concatenated values in a different order
            'typeOf': 'StatisticalVariable',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'statType': 'measuredValue',
        }
        resolved_node = self._resolver.resolve_node(lookup_node)
        self.assertEqual('dcid:ComplexStatVar', resolved_node.get('Node'))

    def test_resolve_place(self):
        resolved_place = self._resolver.resolve_node({'wikidataId': 'Q1234'})
        self.assertEqual('dcid:wikidatsId/Q1234', resolved_place.get('Node'))
        resolved_place = self._resolver.resolve_node({'geoId': '06543'})
        self.assertEqual('dcid:wikidatsId/Q1234', resolved_place.get('Node'))

        resolved_place = self._resolver.resolve_node({'wikidataId': 'Q12'})
        self.assertEqual({}, resolved_place)
        resolved_place = self._resolver.resolve_node({'state': 'geoId/06'})
        self.assertEqual({}, resolved_place)

        resolved_place = self._resolver.resolve_node({'state': 'geoId/04'})
        self.assertEqual({}, resolved_place)
