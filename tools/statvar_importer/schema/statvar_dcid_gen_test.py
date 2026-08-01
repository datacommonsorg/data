# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from statvar_dcid_gen import apply_cumulative_property_dropping
from statvar_dcid_gen import camel_to_snake
from statvar_dcid_gen import generate_dcid_for_statvar
from statvar_dcid_gen import get_dcid_name
from statvar_dcid_gen import get_dcid_token
from statvar_dcid_gen import order_dcid_properties
from statvar_dcid_gen import parse_fixed_properties
from statvar_dcid_gen import resolve_dcid_names
from statvar_dcid_gen import strip_overlapping_prop_prefix


class TestStatvarDcidGen(unittest.TestCase):

    def test_camel_to_snake(self):
        self.assertEqual(camel_to_snake('camelCase'), 'camel_case')
        self.assertEqual(camel_to_snake('CamelCase'), 'camel_case')
        self.assertEqual(camel_to_snake('CaseACRONYM'), 'case_acronym')
        self.assertEqual(camel_to_snake('CaseAbc123'), 'case_abc_123')
        self.assertEqual(camel_to_snake('simple'), 'simple')

    def test_get_dcid_token(self):
        self.assertEqual(get_dcid_token('Hello World!'), 'Hello_World')
        self.assertEqual(get_dcid_token('helloWorld', upper_case=True),
                         'HELLO_WORLD')
        self.assertEqual(get_dcid_token('prefixWorld', remove_prefix='prefix'),
                         'World')

    def test_get_dcid_name(self):
        schema_nodes = {
            'Person': {
                'name': '"Human"'
            },
            'dcid:Count': {
                'name': 'TotalCount'
            },
        }
        self.assertEqual(get_dcid_name('Person', schema_nodes), 'Human')
        self.assertEqual(get_dcid_name('dcid:Person', schema_nodes), 'Human')
        self.assertEqual(get_dcid_name('Count', schema_nodes), 'TotalCount')
        self.assertEqual(get_dcid_name('Unknown', schema_nodes), None)

    def test_generate_dcid(self):
        pvs = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
        }
        dcid = generate_dcid_for_statvar(pvs, {})
        self.assertEqual(dcid, 'Count_Person')

        pvs2 = {
            'statType': 'index',
            'measuredProperty': 'count',
            'populationType': 'Person',
        }
        dcid2 = generate_dcid_for_statvar(pvs2, {})
        self.assertEqual(dcid2, 'Index_Count_Person')

    def test_generate_dcid_with_property(self):
        config = {
            'statvar_dcid_fixed_properties': [
                'statType<>measuredValue', 'measuredProperty<>value',
                'populationType'
            ],
            'statvar_dcid_delimiter': '__',
            'statvar_dcid_fixed_delimiter': '.',
            'statvar_dcid_value_delimiter': '--',
            'statvar_dcid_remove_prefix': 'TEST_',
            'statvar_dcid_upper_case': True,
            'statvar_dcid_prefix': 'test/',
        }
        pvs = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
        }
        dcid = generate_dcid_for_statvar(pvs, config)
        self.assertEqual(dcid, 'test/COUNT.PERSON')

        pvs2 = {
            'statType': 'medianValue',
            'measuredProperty': 'age',
            'populationType': 'Person',
            'gender': 'Male',
            'place': 'TEST_Urban',
        }
        dcid2 = generate_dcid_for_statvar(pvs2, config)
        self.assertEqual(
            dcid2, 'test/MEDIAN_VALUE.AGE.PERSON.GENDER--MALE__PLACE--URBAN')
        pvs3 = {
            'statType': 'measuredValue',
            'measuredProperty': 'value',
            'populationType': 'AdultPerson',
            'gender': 'Male',
            'place': 'TEST_Urban',
        }
        dcid3 = generate_dcid_for_statvar(pvs3, config)
        self.assertEqual(
            dcid3, 'test/ADULT_PERSON.GENDER--MALE__PLACE--URBAN'
        )

    def test_parse_fixed_properties(self):
        props = ['statType<>measuredValue', 'populationType']
        res = parse_fixed_properties(props)
        self.assertEqual(
            res, {'statType': {'measuredValue'}, 'populationType': {''}}
        )
        default_res = parse_fixed_properties(None)
        self.assertIn('statType', default_res)

    def test_order_dcid_properties(self):
        dcid_pvs = {'statType': 'measuredValue', 'gender': 'Female'}
        fixed = {'statType': {'measuredValue'}}
        ordered = order_dcid_properties(dcid_pvs, fixed)
        self.assertEqual(ordered, ['gender'])
        self.assertNotIn('statType', dcid_pvs)

    def test_resolve_dcid_names(self):
        pvs = {'statType': 'measuredValue', 'description': 'Ignore me'}
        schema_nodes = {}
        resolved = resolve_dcid_names(pvs, schema_nodes, {'description'})
        self.assertEqual(resolved, {'statType': 'measuredValue'})

    def test_edge_cases(self):
        self.assertEqual(camel_to_snake(None), '')
        self.assertIsNone(get_dcid_name(None, {}))
        self.assertEqual(get_dcid_token(None), '')
        self.assertEqual(generate_dcid_for_statvar(None), '')

    def test_strip_overlapping_prop_prefix(self):
        self.assertEqual(
            strip_overlapping_prop_prefix(
                'MeasurementQualifier_Annual', 'measurementQualifier'
            ),
            'Annual',
        )
        self.assertEqual(
            strip_overlapping_prop_prefix(
                'UNIT_PERCENT', 'unit', upper_case=True
            ),
            'PERCENT',
        )
        self.assertEqual(
            strip_overlapping_prop_prefix('Person', 'populationType'),
            'Person',
        )

    def test_generate_dcid_with_overlapping_prefix(self):
        pvs = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'measurementQualifier': 'MeasurementQualifier_Annual',
        }
        dcid = generate_dcid_for_statvar(pvs, {})
        self.assertEqual(dcid, 'Annual_Count_Person')

    def test_dcid_max_length_fallbacks(self):
        # Test #3 fallback: use_value_names falls back to raw code when > max
        schema_nodes = {
            'Count': {
                'name': '"ExtremelyLongDescriptiveCountNameOfManyWords"'
            }
        }
        pvs = {
            'statType': 'measuredValue',
            'measuredProperty': 'Count',
            'populationType': 'Person',
        }
        config = {
            'statvar_dcid_value_name': True,
            'statvar_dcid_max_length': 30,
        }
        dcid = generate_dcid_for_statvar(pvs, config, schema_nodes)
        self.assertEqual(dcid, 'Count_Person')

        # Test #4 fallback: cumulative dropping + deterministic hash
        long_pvs = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'age': 'Age_0_To_18_Years_Old',
            'gender': 'Gender_Female_Or_Male',
            'place': 'Place_California_Or_New_York',
        }
        short_config = {'statvar_dcid_max_length': 45}
        dcid_hashed = generate_dcid_for_statvar(long_pvs, short_config)
        self.assertTrue(len(dcid_hashed) <= 45)
        self.assertTrue(dcid_hashed.startswith('Count_Person'))
        self.assertIn('_', dcid_hashed)

    def test_complex_edge_cases(self):
        # 1. camel_to_snake complex cases
        self.assertEqual(
            camel_to_snake('HTTP2ServerResponse', delim='-'),
            'http2server-response',
        )
        self.assertEqual(camel_to_snake('ALREADY_SNAKE'), 'already_snake')

        # 2. get_dcid_name complex cases
        schema_nodes = {
            'Person': {'name': ' "  Complex Person Name  " '},
            'Count': {'typeOf': 'Property'},
            'BadNode': 'NotADict',
        }
        self.assertEqual(
            get_dcid_name('un:Person', schema_nodes), 'Complex Person Name'
        )
        self.assertEqual(get_dcid_name('Count', schema_nodes), 'Count')
        self.assertIsNone(get_dcid_name('BadNode', schema_nodes))

        # 3. get_dcid_token complex cases (invalid regex warning recovery)
        self.assertEqual(
            get_dcid_token('Hello World!', remove_prefix='['), 'Hello_World'
        )
        self.assertEqual(
            get_dcid_token('TEST_prefix_value', remove_prefix='TEST_'),
            'Prefix_value',
        )
        self.assertEqual(get_dcid_token('...___...'), '')

        # 4. parse_fixed_properties complex cases
        props = ['statType<>measuredValue<>extra', '  populationType  <>  ', 12]
        parsed = parse_fixed_properties(props)
        self.assertEqual(
            parsed,
            {'statType': {'measuredValue<>extra'}, 'populationType': {''}},
        )

        # 5. apply_cumulative_property_dropping boundary cases
        small_drop = apply_cumulative_property_dropping(
            [('p1', 'VERY_LONG_CORE')],
            [('p2', 'CONSTRAINT')],
            max_len=5,
            config={'statvar_dcid_hash_length': 8},
        )
        self.assertEqual(len(small_drop), 5)


if __name__ == '__main__':
    unittest.main()
