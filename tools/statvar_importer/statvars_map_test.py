# Copyright 2022 Google LLC
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
"""Unit tests for statvars_map.py."""

import unittest
from collections import OrderedDict

from statvars_map import StatVarsMap


class TestStatVarsMapDcidGeneration(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        # Minimal config for StatVarsMap, can be expanded if tests need more.
        self.config = {
            'statvar_dcid_ignore_values': [
                'measuredValue', 'StatisticalVariable'
            ],
            'default_statvar_pvs':
                OrderedDict([
                    ('typeOf', 'dcs:StatisticalVariable'),
                    ('statType', 'dcs:measuredValue'),
                    ('measuredProperty', 'dcs:count'),
                    ('populationType', ''),
                ]),
            'schemaless':
                False,  # Test schemaless explicitly if needed by _get_dcid_term_for_pv path
        }
        self.stat_vars_map = StatVarsMap(config_dict=self.config)

    def test_construct_new_dcid_simple(self):
        pvs = {
            'typeOf': 'dcs:StatisticalVariable',
            'populationType': 'dcs:Person',
            'measuredProperty': 'dcs:count',
            'statType': 'dcs:measuredValue',
            'location': 'dcid:country/USA'
        }
        # dcid_ignore_props is usually prepared by the caller (generate_statvar_dcid)
        # For direct testing of _construct_new_statvar_dcid, we simulate it being empty or pre-filtered
        dcid_ignore_props = []
        dcid = self.stat_vars_map._construct_new_statvar_dcid(
            pvs, dcid_ignore_props)
        self.assertEqual(dcid, 'Count_Person_Country/USA')

    def test_construct_new_dcid_with_measurement_denominator(self):
        pvs = {
            'typeOf': 'dcs:StatisticalVariable',
            'populationType': 'dcs:Person',
            'measuredProperty': 'dcs:count',
            'statType': 'dcs:measuredValue',
            'measurementDenominator': 'dcid:Count_Person_Overall'
        }
        dcid_ignore_props = []
        dcid = self.stat_vars_map._construct_new_statvar_dcid(
            pvs, dcid_ignore_props)
        self.assertEqual(dcid,
                         'Count_Person_AsAFractionOf_Count_Person_Overall')

    def test_construct_new_dcid_with_ignored_values(self):
        pvs = {
            'typeOf': 'dcs:StatisticalVariable',
            'populationType': 'dcs:Person',
            'measuredProperty': 'dcs:count',
            'statType':
                'dcs:measuredValue',  # This value is in statvar_dcid_ignore_values
            'someOtherProp': 'measuredValue'  # This value is also ignored
        }
        dcid_ignore_props = []
        # statType's value 'dcs:measuredValue' (becomes 'measuredValue' after stripping namespace) is ignored
        # due to 'statvar_dcid_ignore_values' as it's a value of a default property.
        # 'someOtherProp':'measuredValue' results in 'MeasuredValue' term because 'measuredValue' as a value
        # for a non-default property is not in 'statvar_dcid_ignore_values'.
        dcid = self.stat_vars_map._construct_new_statvar_dcid(
            pvs, dcid_ignore_props)
        self.assertEqual(dcid, 'Count_Person_MeasuredValue')

    def test_construct_new_dcid_with_custom_order_and_ignored_props(self):
        # dcid_ignore_props is handled by the caller, so we test the helper with props already filtered.
        # Here, we simulate that 'name' and 'description' were ignored by the caller.
        pvs = {
            'typeOf': 'dcs:StatisticalVariable',
            'populationType': 'dcs:Worker',
            'measuredProperty': 'dcs:count',
            'statType': 'dcs:medianValue',  # Not ignored value
            'employmentStatus': 'dcs:Unemployed',
        }
        dcid_ignore_props = [
        ]  # Simulating these are already filtered out by caller
        dcid = self.stat_vars_map._construct_new_statvar_dcid(
            pvs, dcid_ignore_props)
        # Order: typeOf, statType, measuredProperty, populationType (from default_statvar_pvs), then sorted others
        self.assertEqual(dcid, 'MedianValue_Count_Worker_Unemployed')

    def test_construct_new_dcid_character_sanitization(self):
        pvs = {
            'populationType': 'dcs:Person',
            'property With Spaces': 'Value With Spaces'
        }
        dcid_ignore_props = []
        # Enable schemaless to test _get_dcid_term_for_pv's prop_value path for custom props
        self.stat_vars_map._config.set_config('schemaless', True)
        dcid = self.stat_vars_map._construct_new_statvar_dcid(
            pvs, dcid_ignore_props)
        self.stat_vars_map._config.set_config('schemaless', False)  # Reset
        self.assertEqual(dcid, 'Person_Value_With_Spaces')

    def test_construct_new_dcid_schemaless_style_prop_name(self):
        # Tests that properties starting with '#' (like '# CustomProp') are not included in DCID generation by _construct_new_statvar_dcid,
        # as pv_utils.is_valid_property likely excludes them for DCID term purposes, even if schemaless is True.
        pvs = {
            'populationType': 'dcs:TestPopulation',
            '# CustomProp':
                'CustomValue'  # Property starts with #, schemaless=true needed for _get_dcid_term_for_pv
        }
        dcid_ignore_props = []
        self.stat_vars_map._config.set_config('schemaless', True)
        dcid = self.stat_vars_map._construct_new_statvar_dcid(
            pvs, dcid_ignore_props)
        self.stat_vars_map._config.set_config('schemaless', False)  # Reset
        self.assertEqual(dcid, 'TestPopulation')

    def test_construct_new_dcid_numeric_value_in_prop(self):
        pvs = {'populationType': 'dcs:Sample', 'age': 25}
        dcid_ignore_props = []
        dcid = self.stat_vars_map._construct_new_statvar_dcid(
            pvs, dcid_ignore_props)
        self.assertEqual(dcid, 'Sample_Age_25')

    def test_construct_new_dcid_quantity_range(self):
        pvs = {'populationType': 'dcs:Adult', 'ageRange': '[25 65 Years]'}
        dcid_ignore_props = []
        dcid = self.stat_vars_map._construct_new_statvar_dcid(
            pvs, dcid_ignore_props)
        self.assertEqual(dcid, 'Adult_25To65Years')

    def test_construct_new_dcid_quantity_range_open_ended_min(self):
        pvs = {'populationType': 'dcs:Senior', 'ageRange': '[65 - Years]'}
        dcid_ignore_props = []
        dcid = self.stat_vars_map._construct_new_statvar_dcid(
            pvs, dcid_ignore_props)
        self.assertEqual(dcid, 'Senior_65OrMoreYears')

    def test_construct_new_dcid_quantity_range_open_ended_max(self):
        pvs = {'populationType': 'dcs:Child', 'ageRange': '[- 10 Years]'}
        dcid_ignore_props = []
        dcid = self.stat_vars_map._construct_new_statvar_dcid(
            pvs, dcid_ignore_props)
        self.assertEqual(dcid, 'Child_10OrLessYears')


if __name__ == '__main__':
    unittest.main()
