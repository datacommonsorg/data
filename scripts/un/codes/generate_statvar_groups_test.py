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
"""Unit tests for generate_statvar_groups.py."""

import os
import shutil
import sys
import tempfile
import unittest

from absl import flags
import generate_statvar_groups
from generate_statvar_groups import UNStatVarGroupGenerator

flags.FLAGS(['generate_statvar_groups_test.py'])


class GenerateStatvarGroupsTest(unittest.TestCase):
    """Test suite verifying UN StatVar group generation functions and class."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_default_statvar_group_config(self):
        cfg = generate_statvar_groups.get_default_statvar_group_config()
        self.assertIn('svg_root', cfg)
        self.assertIn('svg_prefix', cfg)
        self.assertIn('svg_properties', cfg)

    def test_to_snake_case(self):
        self.assertEqual(
            generate_statvar_groups.to_snake_case('camelCaseText'),
            'CAMEL_CASE_TEXT',
        )
        self.assertEqual(
            generate_statvar_groups.to_snake_case('camelCaseText', upper=False),
            'camel_Case_Text',
        )
        self.assertEqual(
            generate_statvar_groups.to_snake_case('Multiple   Spaces Here'),
            'MULTIPLE_SPACES_HERE',
        )
        self.assertEqual(generate_statvar_groups.to_snake_case(None), '')

    def test_to_quoted(self):
        self.assertEqual(
            generate_statvar_groups.to_quoted('Hello "World"'),
            '"Hello \'World\'"',
        )
        self.assertEqual(
            generate_statvar_groups.to_quoted('  "Already Quoted"  '),
            '"Already Quoted"',
        )
        self.assertEqual(generate_statvar_groups.to_quoted(''), '')
        self.assertEqual(generate_statvar_groups.to_quoted(None), '')

    def test_strip_prefix_safe(self):
        self.assertEqual(
            generate_statvar_groups.strip_prefix_safe(
                'TEST_Population', 'TEST_'
            ),
            'Population',
        )
        # Invalid regex pattern recovery check
        self.assertEqual(
            generate_statvar_groups.strip_prefix_safe('[prefix]Value', '['),
            'prefix]Value',
        )
        self.assertEqual(
            generate_statvar_groups.strip_prefix_safe('Value', None), 'Value'
        )

    def test_generator_schema_lookup(self):
        gen = UNStatVarGroupGenerator({'statvar_dcid_remove_prefix': 'TEST_'})
        schema_mcf = os.path.join(self.test_dir, 'schema.mcf')
        with open(schema_mcf, 'w') as f:
            f.write(
                'Node: dcid:Person\n'
                'typeOf: dcid:Class\n'
                'name: "Person Node"\n'
                'alternateName: "Alt Person"\n'
            )
        gen.load_schema_mcf(schema_mcf)
        self.assertIsNotNone(gen.get_schema_node('Person'))
        self.assertEqual(gen.get_schema_name('dcid:Person'), 'Alt Person')

        # Fallback when node not in schema
        self.assertEqual(
            gen.get_schema_name('dcid:TEST_CountPerson'), 'Count person'
        )

    def test_get_statvar_group_node_and_add(self):
        gen = UNStatVarGroupGenerator()
        node = gen.get_statvar_group_node('svg_1', 'Group One', 'dc/g/Root')
        self.assertEqual(node['Node'], 'dcid:svg_1')
        self.assertEqual(node['typeOf'], 'dcid:StatVarGroup')
        self.assertEqual(node['name'], '"Group One"')
        self.assertEqual(node['specializationOf'], 'dcid:dc/g/Root')

        gen.add_statvar_group(node)
        grps = gen.get_statvar_groups()
        self.assertIn('dcid:svg_1', grps)

    def test_generate_prop_value_svg(self):
        gen = UNStatVarGroupGenerator({'svg_dcid_remove_prefix': 'UN_'})
        pvs = {'gender': 'dcid:UN_Female', 'age': 'dcid:Age_0_To_18'}
        grps = gen.generate_prop_value_svg(
            pvs, ['gender', 'age'], 'dc/g/Root', 'custom/g/'
        )
        self.assertEqual(len(grps), 2)
        # Verify both property groups and value groups were added
        all_grps = gen.get_statvar_groups()
        self.assertIn('dcid:custom/g/GENDER', all_grps)
        self.assertIn('dcid:custom/g/GENDER--FEMALE', all_grps)
        self.assertIn('dcid:custom/g/GENDER--FEMALE__AGE', all_grps)
        self.assertIn('dcid:custom/g/GENDER--FEMALE__AGE--AGE_0_TO_18',
                      all_grps)

    def test_generate_groups_for_statvar(self):
        gen = UNStatVarGroupGenerator(
            {
                'svg_properties': ['populationType'],
                'statvar_group_permutations': False,
                'statvar_add_linked_member_of': True,
            }
        )
        pvs = {
            'Node': 'dcid:Count_Person_Female',
            'typeOf': 'dcid:StatisticalVariable',
            'populationType': 'dcid:Person',
            'gender': 'dcid:Female',
            'statType': 'dcid:measuredValue',  # Ignored default
        }
        gen.generate_groups_for_statvar(pvs, 'dc/g/Root', 'custom/g/')
        all_grps = gen.get_statvar_groups()
        self.assertIn('dcid:custom/g/PERSON', all_grps)
        self.assertIn('dcid:Count_Person_Female', all_grps)
        sv_node = all_grps['dcid:Count_Person_Female']
        self.assertIn('memberOf', sv_node)
        self.assertIn('linkedMemberOf', sv_node)
        self.assertIn('dcid:custom/g/PERSON__GENDER--FEMALE',
                      sv_node['memberOf'])

    def test_generate_statvar_groups_and_wrapper(self):
        gen = UNStatVarGroupGenerator()
        sv_nodes = {
            'Count_Person': {
                'Node': 'dcid:Count_Person',
                'typeOf': 'dcid:StatisticalVariable',
                'populationType': 'Person',
            },
            'NotASv': {
                'Node': 'dcid:NotASv',
                'typeOf': 'dcid:Class',
            },
        }
        gen.generate_statvar_groups(sv_nodes)
        all_grps = gen.get_statvar_groups()
        # Verify only StatisticalVariable was processed
        self.assertIn('dcid:Count_Person', all_grps)
        self.assertNotIn('dcid:NotASv', all_grps)
        # Verify custom root SVG node is generated when not containing 'Root'
        gen_custom = UNStatVarGroupGenerator({'svg_root': 'dc/g/UNData'})
        gen_custom.generate_statvar_groups(sv_nodes)
        self.assertIn('dcid:dc/g/UNData', gen_custom.get_statvar_groups())

        # Test high-level wrapper reading and writing MCF
        in_mcf = os.path.join(self.test_dir, 'input.mcf')
        out_mcf = os.path.join(self.test_dir, 'out_dir', 'groups.mcf')
        with open(in_mcf, 'w') as f:
            f.write(
                'Node: dcid:Test_SV\n'
                'typeOf: dcid:StatisticalVariable\n'
                'populationType: dcid:Person\n'
            )
        generate_statvar_groups.generate_statvar_groups(
            in_mcf, '', out_mcf, config={}
        )
        self.assertTrue(os.path.exists(out_mcf))


if __name__ == '__main__':
    unittest.main()
