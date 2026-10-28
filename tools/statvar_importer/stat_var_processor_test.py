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
from stat_var_processor import StatVarDataProcessor, StatVarsMap, process


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
            df_expected = df_expected.sort_values(
                by=df_expected.columns.to_list(), ignore_index=True)
            df_actual = df_actual.sort_values(by=df_expected.columns.to_list(),
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

    def test_setup_config_mapped_columns_int(self):
        """Tests integer mapped_columns expands to 1..N."""
        processor = StatVarDataProcessor()
        processor.setup_config({'mapped_columns': 4})
        self.assertEqual(processor._config.get('mapped_columns'), [1, 2, 3, 4])

    def test_setup_config_mapped_columns_multi_int_list(self):
        """Tests multi-element integer list preserves specific indices."""
        processor = StatVarDataProcessor()
        processor.setup_config({'mapped_columns': [1, 3, 5]})
        self.assertEqual(processor._config.get('mapped_columns'), [1, 3, 5])

    def test_setup_config_mapped_columns_single_letter(self):
        """Tests single uppercase column letter expands to 1..N."""
        processor = StatVarDataProcessor()
        processor.setup_config({'mapped_columns': 'C'})
        self.assertEqual(processor._config.get('mapped_columns'), [1, 2, 3])

    def test_setup_config_mapped_columns_multi_letters(self):
        """Tests comma-separated column letters convert to 1-based indices."""
        processor = StatVarDataProcessor()
        processor.setup_config({'mapped_columns': 'A,C,AA'})
        self.assertEqual(processor._config.get('mapped_columns'), [1, 3, 27])

    def test_setup_config_mapped_columns_multi_letters_whitespace_mixed_case(
            self):
        """Tests whitespace-padded mixed-case column letters parse cleanly."""
        processor = StatVarDataProcessor()
        processor.setup_config({'mapped_columns': ' A , c , aa '})
        self.assertEqual(processor._config.get('mapped_columns'), [1, 3, 27])

    def test_setup_config_mapped_columns_zero_str(self):
        """Tests string zero does not produce column index 0."""
        processor = StatVarDataProcessor()
        processor.setup_config({'mapped_columns': '0'})
        self.assertEqual(processor._config.get('mapped_columns'), [])

    def test_setup_config_mapped_columns_non_ascii_letter(self):
        """Tests non-ASCII column letter is not parsed as a column index."""
        processor = StatVarDataProcessor()
        processor.setup_config({'mapped_columns': 'é'})
        self.assertEqual(processor._config.get('mapped_columns'), [])


class TestStatVarsMap(unittest.TestCase):
    """Unit tests for StatVarsMap."""

    def test_set_statvar_dup_svobs_missing_key_prefixed_variable(self):
        """Tests missing svobs_key with prefixed variableMeasured."""
        statvars_map = StatVarsMap(config_dict={'debug': True})
        statvars_map.set_statvar_dup_svobs('missing_key_1', {
            'variableMeasured': 'dcid:Count_Person',
            'value': 10,
        })
        self.assertEqual(
            statvars_map._counters.get_counter(
                'error-statvar-obs-missing-for-dup-svobs'), 1)
        self.assertEqual(
            statvars_map._counters.get_counter(
                'error-statvar-obs-missing-for-dup-svobs_Count_Person'), 1)

    def test_set_statvar_dup_svobs_missing_key_missing_variable(self):
        """Tests missing svobs_key when variableMeasured is absent."""
        statvars_map = StatVarsMap(config_dict={'debug': True})
        statvars_map.set_statvar_dup_svobs('missing_key_2', {'value': 20})
        self.assertEqual(
            statvars_map._counters.get_counter(
                'error-statvar-obs-missing-for-dup-svobs'), 1)


if __name__ == '__main__':
    app.run()
    unittest.main()
