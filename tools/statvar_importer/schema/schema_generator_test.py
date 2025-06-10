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
"""Unit tests for schema_generator.py."""

import unittest

from absl import app
from absl import logging
import schema_generator


class SchemaGeneratorTest(unittest.TestCase):
    new_nodes = {
        'dcid:NewStatVar1': {
            'Node': 'dcid:NewStatVar1',
            'typeOf': 'dcs:StatisticalVariable',
            'populationType': 'dcs:NewPopulation1',
            'measuredProperty': 'dcs:count',
            'statType': 'dcs:measuredvalue',
            'name': '"New StatVar Node 1"',
            'existingProperty': 'dcid:NewValue1',
            'newProperty1': 'dcid:NewPropValue1',
        },
    }

    schema_nodes = {
        'dcid:existingProperty': {
            'Node': 'dcis:existingProperty',
            'typeOf': 'dcs:Property',
            'domainIncludes': 'dcs:Person',
            'rangeIncludes': 'dcs:ExistingEnum',
        },
        'dcid:ExistingEnum': {
            'Node': 'dcid:ExistingEnum',
            'typeOf': 'dcs:Class',
            'subClassOf': 'dcs:Enumeration',
        },
    }

    def setUp(self):
        # logging.set_verbosity(2)
        self.maxDiff = None

    def test_generate_schema(self):
        new_schema = {}
        new_schema = schema_generator.generate_schema_nodes(
            self.new_nodes, self.schema_nodes, '', new_schema)
        logging.info(f'Generated schema: {new_schema}')
        expected_schema = {
            'dcid:NewPopulation1': {
                'Node': 'dcid:NewPopulation1',
                'typeOf': 'dcid:Thing',
                'name': '"New Population 1"',
                'isProvisional': 'dcs:True',
            },
            'dcid:NewProperty1Enum': {
                'Node': 'dcid:NewProperty1Enum',
                'isProvisional': 'dcs:True',
                'name': '"NewProperty1Enum"',
                'subClassOf': 'dcs:Enumeration',
                'typeOf': 'schema:Class',
            },
            'dcid:existingProperty': {
                # Add new domain for existing property
                'domainIncludes': 'dcid:NewPopulation1',
                'Node': 'dcid:existingProperty',
                'typeOf': 'dcs:Property',
                'name': '"existingProperty"',
            },
            'dcid:NewValue1': {
                'Node': 'dcid:NewValue1',
                'typeOf': 'dcid:ExistingEnum',
                'name': '"New Value 1"',
                'isProvisional': 'dcs:True',
            },
            'dcid:newProperty1': {
                'domainIncludes': 'dcid:NewPopulation1',
                'rangeIncludes': 'dcid:NewProperty1Enum',
                'Node': 'dcid:newProperty1',
                'typeOf': 'dcs:Property',
                'name': '"newProperty1"',
                'isProvisional': 'dcs:True',
            },
            'dcid:NewPropValue1': {
                'Node': 'dcid:NewPropValue1',
                'typeOf': 'dcid:NewProperty1Enum',
                'name': '"New Prop Value 1"',
                'isProvisional': 'dcs:True',
            },
        }
        self.assertEqual(expected_schema, new_schema)

    def test_generate_statvar_name(self):
        self.assertEqual(
            "Count Person: Age Years 10 Onwards",
            schema_generator.generate_statvar_name({
                'typeOf': 'StatisticalVariable',
                'populationType': 'dcid:Person',
                'measuredProperty': 'dcid:count',
                'age': '[10 - Years]',
            }))
        self.assertEqual(
            "Mean Annual Generation Electricity: Energy Source Bagasse, Energy Source Type Renewable",
            schema_generator.generate_statvar_name({
                'Node': 'dcid:Annual_Generation_Electricity_Bagasse_Renewable',
                'typeOf': 'dcid:StatisticalVariable',
                'populationType': 'dcid:Electricity',
                'measuredProperty': 'dcid:generation',
                'measurementQualifier': 'dcid:Annual',
                'statType': 'dcid:meanValue',
                'energySource': 'dcid:Bagasse',
                'energySourceType': 'dcid:Renewable',
            }))
