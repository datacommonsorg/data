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
from statvar_dcid_gen import camel_to_snake
from statvar_dcid_gen import generate_dcid_for_statvar
from statvar_dcid_gen import get_dcid_name
from statvar_dcid_gen import get_dcid_token


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
            dcid3, 'test/ADULT_PERSON.GENDER--MALE__PLACE--URBAN')



if __name__ == '__main__':
    unittest.main()
