# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for process.py of the CDC Natality import automation."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import pandas as pd

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))


class ProcessPipelineTest(unittest.TestCase):

    def test_end_to_end_pipeline_with_preprocessed_data(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_dir = os.path.join(tmp_dir, 'input_files')
            output_dir = os.path.join(tmp_dir, 'output')
            os.makedirs(input_dir, exist_ok=True)

            sample_country_csv = os.path.join(input_dir, 'country_cleaned_16-20.csv')
            sample_state_csv = os.path.join(input_dir, 'state_cleaned_16-20.csv')
            sample_county_csv = os.path.join(input_dir, 'county_cleaned_16-20.csv')

            country_df = pd.DataFrame([{
                'Year': '2020',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '3613647'
            }, {
                'Year': '2019',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '3747540'
            }])
            country_df.to_csv(sample_country_csv, index=False)

            state_df = pd.DataFrame([{
                'Year': '2020',
                'Geo': 'geoId/01',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '57647',
                'Unit': ''
            }, {
                'Year': '2020',
                'Geo': 'geoId/02',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '9469',
                'Unit': ''
            }])
            state_df.to_csv(sample_state_csv, index=False)

            county_df = pd.DataFrame([{
                'Year': '2020',
                'Geo': 'geoId/01003',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '2245',
                'Unit': ''
            }])
            county_df.to_csv(sample_county_csv, index=False)

            process_py = os.path.join(_SCRIPT_PATH, 'process.py')
            cmd = [
                sys.executable, process_py, f'--input_path={input_dir}',
                f'--output_path={output_dir}'
            ]
            subprocess.check_call(cmd)

            expected_files = [
                'country.csv', 'state.csv', 'county.csv', 'country.tmcf',
                'state.tmcf', 'county.tmcf'
            ]
            for filename in expected_files:
                out_path = os.path.join(output_dir, filename)
                self.assertTrue(os.path.exists(out_path),
                                f'Missing expected file: {filename}')
                self.assertGreater(os.path.getsize(out_path), 0,
                                   f'Output file is empty: {filename}')

            result_country = pd.read_csv(os.path.join(output_dir, 'country.csv'))
            self.assertEqual(len(result_country), 2)
            self.assertIn('StatVar', result_country.columns)

            result_state = pd.read_csv(os.path.join(output_dir, 'state.csv'))
            self.assertEqual(len(result_state), 2)
            self.assertIn('Geo', result_state.columns)

            result_county = pd.read_csv(os.path.join(output_dir, 'county.csv'))
            self.assertEqual(len(result_county), 1)

    def test_pipeline_with_testdata_fallback(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_dir = os.path.join(tmp_dir, 'empty_inputs')
            output_dir = os.path.join(tmp_dir, 'output')
            os.makedirs(input_dir, exist_ok=True)

            process_py = os.path.join(_SCRIPT_PATH, 'process.py')
            cmd = [
                sys.executable, process_py, f'--input_path={input_dir}',
                f'--output_path={output_dir}', '--use_test_data'
            ]
            subprocess.check_call(cmd)

            for filename in ['country.csv', 'state.csv', 'county.csv']:
                out_path = os.path.join(output_dir, filename)
                self.assertTrue(os.path.exists(out_path),
                                f'Missing expected file: {filename}')
                self.assertGreater(os.path.getsize(out_path), 0)

            # Assert that county Geo values are valid 5-digit DCIDs and not 2-digit state DCIDs
            county_df = pd.read_csv(os.path.join(output_dir, 'county.csv'), dtype=str)
            self.assertTrue(all(county_df['Geo'].str.match(r'^geoId/\d{5}$')),
                            f"Invalid county Geo DCIDs found: {county_df['Geo'].unique()}")

            # Assert that country Count_* observations are clean integers without .0 decimals
            country_df = pd.read_csv(os.path.join(output_dir, 'country.csv'), dtype=str)
            count_rows = country_df[country_df['StatVar'].str.startswith('Count')]
            self.assertFalse(count_rows.empty)
            for val in count_rows['Quantity']:
                self.assertFalse('.' in str(val), f"Float notation found in count Quantity: {val}")

    def test_multi_bracket_sorting_and_deduplication(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_dir = os.path.join(tmp_dir, 'input_files')
            output_dir = os.path.join(tmp_dir, 'output')
            os.makedirs(input_dir, exist_ok=True)

            # Stage multi-bracket state files with overlapping year 2016
            state_95_02 = pd.DataFrame([{
                'Year': '2002',
                'Geo': 'geoId/01',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '50000',
                'Unit': ''
            }])
            state_95_02.to_csv(os.path.join(input_dir, 'state_cleaned_95-02.csv'), index=False)

            state_03_06 = pd.DataFrame([{
                'Year': '2006',
                'Geo': 'geoId/01',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '55000',
                'Unit': ''
            }])
            state_03_06.to_csv(os.path.join(input_dir, 'state_cleaned_03-06.csv'), index=False)

            # Older bracket for 2016: Quantity = 57000
            state_07_20 = pd.DataFrame([{
                'Year': '2016',
                'Geo': 'geoId/01',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '57000',
                'Unit': ''
            }])
            state_07_20.to_csv(os.path.join(input_dir, 'state_cleaned_07-20.csv'), index=False)

            # Newer expanded bracket for 2016: Quantity = 59000 (should win with keep='last')
            state_16_20 = pd.DataFrame([{
                'Year': '2016',
                'Geo': 'geoId/01',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '59000',
                'Unit': ''
            }])
            state_16_20.to_csv(os.path.join(input_dir, 'state_cleaned_16-20.csv'), index=False)

            # Stage single county file
            county_df = pd.DataFrame([{
                'Year': '2016',
                'Geo': 'geoId/01001',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '1200',
                'Unit': ''
            }])
            county_df.to_csv(os.path.join(input_dir, 'county_cleaned_16-20.csv'), index=False)

            # Note: We intentionally do NOT stage country CSVs to test state-to-country aggregation fallback
            process_py = os.path.join(_SCRIPT_PATH, 'process.py')
            cmd = [
                sys.executable, process_py, f'--input_path={input_dir}',
                f'--output_path={output_dir}'
            ]
            subprocess.check_call(cmd)

            result_state = pd.read_csv(os.path.join(output_dir, 'state.csv'), dtype=str)
            row_2016 = result_state[(result_state['Year'] == '2016') &
                                    (result_state['Geo'] == 'geoId/01') &
                                    (result_state['StatVar'] == 'Count_BirthEvent_LiveBirth')]
            self.assertEqual(len(row_2016), 1)
            # Verify keep='last' selected the newer bracket (59000, not 57000)
            self.assertEqual(row_2016.iloc[0]['Quantity'], '59000')

            # Verify country fallback was generated and contains integer format
            result_country = pd.read_csv(os.path.join(output_dir, 'country.csv'), dtype=str)
            self.assertTrue(len(result_country) >= 3)
            for val in result_country['Quantity']:
                self.assertFalse('.' in str(val), f"Float notation found in aggregated Quantity: {val}")


if __name__ == '__main__':
    unittest.main()

