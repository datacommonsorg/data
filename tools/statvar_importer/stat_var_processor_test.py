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

import os
import sys
import tempfile
import unittest

from absl import app
from absl import logging
import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

from counters import Counters
from mcf_diff import diff_mcf_files
from stat_var_processor import StatVarDataProcessor, process, StatVarsMap
from collections import OrderedDict


class TestStatVarProcessor(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.data_processor_class = StatVarDataProcessor
        self.test_files = [
            os.path.join(_SCRIPT_DIR, 'test_data', 'sample'),
            os.path.join(_SCRIPT_DIR, 'test_data', 'sample_schemaless'),
            os.path.join(_SCRIPT_DIR, 'test_data', 'india_census_sample'),
            os.path.join(_SCRIPT_DIR, 'test_data',
                         'us_census_EC1200A1-2022-09-15'),
            os.path.join(_SCRIPT_DIR, 'test_data', 'us_census_B01001'),
        ]
        self.pv_maps = []
        logging.info(
            f'Setting test files: {self.test_files}, pv_maps: {self.pv_maps}')

    def compare_mcf_files(self, file_pairs: dict):
        """Compare files with MCF nodes allowing reordering of nodes and properties."""
        for actual_file, expected_file in file_pairs.items():
            counters = Counters()
            diff = diff_mcf_files(actual_file, expected_file,
                                  {'show_diff_nodes_only': True}, counters)
            self.assertEqual(
                diff,
                '',
                f'Found diffs in MCF nodes:' +
                f'"{actual_file}" vs "{expected_file}":' +
                f'{diff}\nCounters: {counters.get_counters_string()}',
            )

    def compare_csv_files(self, file_pairs: dict):
        """Compare CSV files with statvar obsevration data."""
        for actual_file, expected_file in file_pairs.items():
            # Sort files by columns.
            df_expected = pd.read_csv(expected_file)
            df_actual = pd.read_csv(actual_file)
            self.assertEqual(
                df_expected.columns.to_list(),
                df_actual.columns.to_list(),
                f'Found different columns in CSV files:' +
                f'expected:{expected_file}:{df_expected.columns.to_list()}, ' +
                f'actual:{actual_file}:{df_actual.columns.to_list()}, ',
            )
            df_expected.sort_values(by=df_expected.columns.to_list(),
                                    inplace=True,
                                    ignore_index=True)
            df_actual.sort_values(by=df_expected.columns.to_list(),
                                  inplace=True,
                                  ignore_index=True)
            self.assertTrue(
                df_expected.equals(df_actual),
                f'Found diffs in CSV rows:' +
                f'"{actual_file}" vs "{expected_file}":',
            )

    def compare_files(self, file_pairs: dict):
        """Raise a test failure if actual and expected files differ."""
        for actual_file, expected_file in file_pairs.items():
            logging.debug(f'Comparing files: {actual_file}, {expected_file}...')
            if actual_file.endswith('mcf'):
                self.compare_mcf_files({actual_file: expected_file})
            elif actual_file.endswith('csv'):
                self.compare_csv_files({actual_file: expected_file})
            else:
                with open(actual_file, 'r') as actual_f:
                    actual_str = actual_f.read()
                with open(expected_file, 'r') as expected_f:
                    expected_str = expected_f.read()
                self.assertEqual(
                    actual_str,
                    expected_str,
                    f'Mismatched actual:{actual_file} expected:{expected_file}',
                )

    def process_file(self, file_prefix: str):
        test_name = os.path.basename(file_prefix)
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = '/tmp/unittest'
            test_output = os.path.join(tmp_dir, f'{test_name}_output')
            test_config = os.path.join(_SCRIPT_DIR, f'{file_prefix}_config.py')
            test_pv_maps = [
                os.path.join(_SCRIPT_DIR, f'{file_prefix}_pv_map.py')
            ]
            test_pv_maps.extend(self.pv_maps)
            test_input = os.path.join(_SCRIPT_DIR, f'{file_prefix}_input.csv')

            self.assertTrue(
                process(
                    data_processor_class=self.data_processor_class,
                    input_data=[test_input],
                    output_path=test_output,
                    config=test_config,
                    pv_map_files=test_pv_maps,
                ),
                f'Errors in processing {test_input}',
            )
            expected_test_output = os.path.join(_SCRIPT_DIR,
                                                f'{file_prefix}_output')
            output_files = {}
            for output_file in ['.csv', '.tmcf', '_stat_vars.mcf']:
                output_files[test_output +
                             output_file] = (expected_test_output + output_file)
            self.compare_files(output_files)
            # for file in output_files.keys():
            #    os.remove(file)

    # Test processing of sample files.
    def test_process(self):
        logging.info(f'Testing inputs: {self.test_files}')
        for test_file in self.test_files:
            logging.info(f'Testing file {test_file}...')
            self.process_file(test_file)


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
    app.run()
    unittest.main()
