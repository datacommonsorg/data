import os
import pandas as pd
import sys
import tempfile
import unittest

from absl import app
from absl import logging

from mcf_diff import diff_mcf_files

# Allows the following module imports to work when running as a script
# relative to data/scripts/
#sys.path.append(
#    os.path.sep.join([
#        '..' for x in filter(lambda x: x == os.path.sep,
#                             os.path.abspath(__file__).split('data/')[1])
#    ]))

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)

from stat_var_processor import process

class TestStatVarProcessor(unittest.TestCase):

    def compare_mcf_files(self, file_pairs: dict):
        '''Compare files with MCF nodes allowing reordering of nodes and properties.'''
        for actual_file, expected_file in file_pairs.items():
            counters = {}
            diff = diff_mcf_files(actual_file, expected_file,
                                  {'show_diff_nodes_only': True}, counters)
            self.assertEqual(
                diff, '', f'Found diffs in MCF nodes:' +
                f'"{actual_file}" vs "{expected_file}":' +
                f'{diff}\nCounters: {counters}')

    def compare_csv_files(self, file_pairs: dict):
        '''Compare CSV files with statvar obsevration data.'''
        for actual_file, expected_file in file_pairs.items():
            # Sort files by columns.
            df_expected = pd.read_csv(expected_file)
            df_actual = pd.read_csv(actual_file)
            self.assertEqual(
                df_expected.columns.to_list(),
                df_actual.columns.to_list(),
                f'Found different columns in CSV files:' +
                f'expected:{expected_file}:{df_expected.columns.to_list()}, ' +
                f'actual:{actual_file}:{df_actual.columns.to_list()}, ')
            df_expected.sort_values(by=df_expected.columns.to_list(), inplace=True)
            df_actual.sort_values(by=df_expected.columns.to_list(), inplace=True)
            self.assertTrue(
                df_expected.equals(df_actual), f'Found diffs in CSV rows:' +
                f'"{actual_file}" vs "{expected_file}":')

    def compare_files(self, file_pairs: dict):
        '''Raise a test failure if actual and expected files differ.'''
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
                    actual_str, expected_str,
                    f'Mismatched actual:{actual_file} expected:{expected_file}')

    def process_file(self, file_prefix: str):
        test_name = os.path.basename(file_prefix)
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_output = os.path.join(tmp_dir, f'{test_name}_output')
            test_config = os.path.join(module_dir_, f'{file_prefix}_config.py')
            test_column_map = os.path.join(module_dir_,
                                           f'{file_prefix}_pv_map.py')
            test_input = os.path.join(module_dir_, f'{file_prefix}_input.csv')

            self.assertTrue(
                process(input_data=[test_input],
                        output_path=test_output,
                        config_file=test_config,
                        pv_map_files=[test_column_map]),
                f'Errors in processing {test_input}')
            expected_test_output = os.path.join(module_dir_,
                                                f'{file_prefix}_output')
            output_files = {}
            for output_file in ['.csv', '.tmcf', '.mcf']:
                output_files[test_output +
                             output_file] = expected_test_output + output_file
            self.compare_files(output_files)
            for file in output_files.keys():
                os.remove(file)

    # Test processing of sample files.
    def test_process(self):
        test_files = [
            'test_data/sample',
            'test_data/sample_schemaless',
            'test_data/india_census_sample',
            'test_data/us_census_EC1200A1-2022-09-15',
            'test_data/us_census_B01001',
            'test_data/us_flood_fima',
        ]
        for test_file in test_files:
            logging.info(f'Testing file {test_file}...')
            self.process_file(test_file)


if __name__ == '__main__':
    app.run()
    unittest.main()
