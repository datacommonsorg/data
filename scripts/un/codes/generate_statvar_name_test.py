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
"""Unit tests for generate_statvar_name.py."""

import os
import shutil
import sys
import tempfile
import unittest

from absl import flags
import generate_statvar_name
from generate_statvar_name import UNStatVarNameGenerator

flags.FLAGS(['generate_statvar_name_test.py'])


class GenerateStatvarNameTest(unittest.TestCase):
    """Test suite verifying UN StatVar name generation functions and class."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_to_quoted(self):
        self.assertEqual(
            generate_statvar_name.to_quoted('Hello "World"'),
            '"Hello \'World\'"',
        )
        self.assertEqual(
            generate_statvar_name.to_quoted('  "Already Quoted"  '),
            '"Already Quoted"',
        )
        self.assertEqual(generate_statvar_name.to_quoted(''), '')
        self.assertEqual(generate_statvar_name.to_quoted(None), '')

    def test_to_sentence_case(self):
        self.assertEqual(
            generate_statvar_name.to_sentence_case('measuredProperty_gender'),
            'Measured property gender',
        )
        self.assertEqual(
            generate_statvar_name.to_sentence_case('camelCaseText'),
            'Camel case text',
        )
        self.assertEqual(generate_statvar_name.to_sentence_case(None), '')

    def test_generator_schema_lookup(self):
        gen = UNStatVarNameGenerator()
        schema_mcf = os.path.join(self.test_dir, 'schema.mcf')
        with open(schema_mcf, 'w') as f:
            f.write(
                'Node: dcid:Person\n'
                'typeOf: dcid:Class\n'
                'name: "Person Node"\n'
                'alternateName: "Alt Person"\n\n'
                'Node: dcid:Count_Person\n'
                'typeOf: dcid:StatisticalVariable\n'
                'name: "Exact Count Person"\n'
            )
        gen.load_schema_mcf(schema_mcf)
        self.assertIsNotNone(gen.get_schema_node('Person'))
        self.assertEqual(gen.get_schema_name('dcid:Person'), 'Alt Person')
        self.assertEqual(
            gen.get_schema_name('dcid:Count_Person'), 'Exact Count Person'
        )
        self.assertEqual(gen.get_schema_name('dcid:NonExistentNode'), '')

    def test_generate_statvar_name_existing_and_schema(self):
        gen = UNStatVarNameGenerator()
        schema_mcf = os.path.join(self.test_dir, 'schema.mcf')
        with open(schema_mcf, 'w') as f:
            f.write(
                'Node: dcid:Schema_SV\n'
                'typeOf: dcid:StatisticalVariable\n'
                'name: "Schema Name"\n'
            )
        gen.load_schema_mcf(schema_mcf)

        # 1. Existing name retained and quoted
        pvs_existing = {'Node': 'dcid:Existing_SV', 'name': 'Existing Name'}
        res = gen.generate_statvar_name(pvs_existing)
        self.assertEqual(res['name'], '"Existing Name"')

        # 2. Schema name resolved when node has no name property
        pvs_schema = {'Node': 'dcid:Schema_SV'}
        res_schema = gen.generate_statvar_name(pvs_schema)
        self.assertEqual(res_schema['name'], '"Schema Name"')

    def test_generate_statvar_name_composite(self):
        gen = UNStatVarNameGenerator()
        schema_mcf = os.path.join(self.test_dir, 'schema.mcf')
        with open(schema_mcf, 'w') as f:
            f.write(
                'Node: dcid:Person\n'
                'typeOf: dcid:Class\n'
                'alternateName: "Person"\n\n'
                'Node: dcid:gender\n'
                'typeOf: dcid:Property\n'
                'alternateName: "Gender"\n'
            )
        gen.load_schema_mcf(schema_mcf)

        pvs = {
            'Node': 'dcid:Composite_SV',
            'typeOf': 'dcid:StatisticalVariable',
            'populationType': 'dcid:Person',
            'gender': 'dcid:Female',  # Not in schema -> fallback sentence case
            'statType': 'dcid:measuredValue',  # Ignored default property
        }
        res = gen.generate_statvar_name(pvs)
        self.assertEqual(res['name'], '"Person [Gender=Female]"')

    def test_generate_statvar_name_no_pop_type(self):
        gen = UNStatVarNameGenerator()
        pvs = {
            'Node': 'dcid:NoPop_SV',
            'typeOf': 'dcid:StatisticalVariable',
            'gender': 'dcid:Female',
        }
        res = gen.generate_statvar_name(pvs)
        self.assertEqual(res['name'], '"[Gender=Female]"')

    def test_missing_schema_names_sentence_case(self):
        # When properties, values, and populationType are NOT in schema,
        # generate_statvar_name uses the DCID itself converted from camelCase
        # to sentence case.
        gen = UNStatVarNameGenerator()
        pvs = {
            'Node': 'dcid:Test_SV',
            'typeOf': 'dcid:StatisticalVariable',
            'populationType': 'dcid:PersonOrHousehold',
            'measurementQualifier': 'dcid:AnnualAverage',
            'housingTenure': 'dcid:OwnerOccupied',
        }
        res = gen.generate_statvar_name(pvs)
        self.assertEqual(
            res['name'],
            '"Person or household [Measurement qualifier=Annual average, '
            'Housing tenure=Owner occupied]"',
        )

    def test_generate_statvar_names_wrapper(self):
        in_mcf = os.path.join(self.test_dir, 'input.mcf')
        out_mcf = os.path.join(self.test_dir, 'out_dir', 'named.mcf')
        with open(in_mcf, 'w') as f:
            f.write(
                'Node: dcid:Wrapper_SV\n'
                'typeOf: dcid:StatisticalVariable\n'
                'populationType: dcid:Person\n'
            )
        generate_statvar_name.generate_statvar_names(in_mcf, '', out_mcf)
        self.assertTrue(os.path.exists(out_mcf))
        with open(out_mcf, 'r') as f:
            content = f.read()
        self.assertIn('name: "Person"', content)


if __name__ == '__main__':
    unittest.main()
