# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for process.py of the CDC Natality import automation."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
import duckdb
import pandas as pd

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_PATH not in sys.path:
    sys.path.append(_SCRIPT_PATH)

import process


class ProcessPipelineTest(unittest.TestCase):

    def test_end_to_end_pipeline_with_raw_tsvs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_dir = os.path.join(tmp_dir, 'input_files')
            output_dir = os.path.join(tmp_dir, 'output')
            os.makedirs(input_dir, exist_ok=True)

            sample_state_tsv = os.path.join(input_dir, 'state_raw.tsv')
            sample_county_tsv = os.path.join(input_dir, 'county_raw.tsv')

            with open(sample_state_tsv, 'w', encoding='utf-8') as f:
                f.write(
                    '"Notes"\t"State of Residence"\t"State of Residence Code"\t"Year"\t"Year Code"\tBirths\tAverage Birth Weight (grams)\n'
                )
                f.write('\t"Alabama"\t"01"\t"2020"\t"2020"\t57647\t3179.09\n')
                f.write('\t"Alaska"\t"02"\t"2020"\t"2020"\t9469\t3378.93\n')
                f.write('"Total"\t\t\t\t\t67116\t\n')
                f.write('"---"\n')

            with open(sample_county_tsv, 'w', encoding='utf-8') as f:
                f.write(
                    '"Notes"\t"County of Residence"\t"County of Residence Code"\t"Year"\t"Year Code"\tBirths\tAverage Birth Weight (grams)\n'
                )
                f.write(
                    '\t"Baldwin County, AL"\t"01003"\t"2020"\t"2020"\t2245\t3250.50\n'
                )
                f.write('"Total"\t\t\t\t\t2245\t\n')
                f.write('"---"\n')

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

            result_state = pd.read_csv(os.path.join(output_dir, 'state.csv'))
            self.assertEqual(
                len(result_state[result_state['StatVar'] ==
                                 'Count_BirthEvent_LiveBirth']), 2)
            self.assertIn('geoId/01', result_state['Geo'].values)

            result_county = pd.read_csv(os.path.join(output_dir, 'county.csv'))
            self.assertEqual(
                len(result_county[result_county['StatVar'] ==
                                  'Count_BirthEvent_LiveBirth']), 1)
            self.assertIn('geoId/01003', result_county['Geo'].values)

            result_country = pd.read_csv(os.path.join(output_dir,
                                                      'country.csv'))
            self.assertEqual(len(result_country), 1)
            # Sum of 57647 + 9469 = 67116
            self.assertEqual(result_country.iloc[0]['Quantity'], 67116)

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

            for filename in [
                    'country.csv', 'state.csv', 'county.csv', 'country.tmcf',
                    'state.tmcf', 'county.tmcf'
            ]:
                out_path = os.path.join(output_dir, filename)
                self.assertTrue(os.path.exists(out_path),
                                f'Missing expected file: {filename}')
                self.assertGreater(os.path.getsize(out_path), 0)

            # Assert that county Geo values are valid 5-digit DCIDs
            county_df = pd.read_csv(os.path.join(output_dir, 'county.csv'),
                                    dtype=str)
            self.assertTrue(
                all(county_df['Geo'].str.match(r'^geoId/\d{5}$')),
                f"Invalid county Geo DCIDs found: {county_df['Geo'].unique()}")

    def test_aggregate_all_nan_excluded(self):
        # StatVar with valid numbers should aggregate, but StatVar with all NaN/unreliable should be excluded
        test_df = pd.DataFrame([
            {
                'Year': '2020',
                'Geo': 'geoId/01',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '100'
            },
            {
                'Year': '2020',
                'Geo': 'geoId/02',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '200'
            },
            {
                'Year': '2020',
                'Geo': 'geoId/01',
                'StatVar': 'Count_BirthEvent_UnreliableData',
                'Quantity': 'Unreliable'
            },
            {
                'Year': '2020',
                'Geo': 'geoId/02',
                'StatVar': 'Count_BirthEvent_UnreliableData',
                'Quantity': ''
            },
        ])
        agg_df = process.aggregate_state_to_country(test_df)
        stat_vars = agg_df['StatVar'].tolist()
        self.assertIn('Count_BirthEvent_LiveBirth', stat_vars)
        self.assertNotIn('Count_BirthEvent_UnreliableData', stat_vars)
        valid_row = agg_df[agg_df['StatVar'] == 'Count_BirthEvent_LiveBirth']
        self.assertEqual(str(valid_row.iloc[0]['Quantity']), '300')

    def test_validation_config_sql_validator(self):
        config_path = os.path.join(_SCRIPT_PATH, 'validation_config.json')
        with open(config_path) as f:
            cfg = json.load(f)
        rule = cfg['rules'][0]
        query = rule['params']['query']
        cond = rule['params']['condition']

        con = duckdb.connect()
        # Mock passing stats (MaxDate 2024)
        valid_stats = pd.DataFrame([{
            'StatVar': 'Count_BirthEvent_LiveBirth',
            'MaxDate': '2024'
        }])
        con.register('stats', valid_stats)
        failing_df = con.execute(
            f'WITH data_to_validate AS ({query}) SELECT * FROM data_to_validate WHERE NOT ({cond})'
        ).fetchdf()
        self.assertTrue(failing_df.empty,
                        f'Expected valid stats to pass: {failing_df}')

        # Mock failing stats (MaxDate too old, e.g. 2018)
        invalid_stats = pd.DataFrame([{
            'StatVar': 'Count_BirthEvent_LiveBirth',
            'MaxDate': '2018'
        }])
        con.register('stats', invalid_stats)
        failing_df = con.execute(
            f'WITH data_to_validate AS ({query}) SELECT * FROM data_to_validate WHERE NOT ({cond})'
        ).fetchdf()
        self.assertFalse(failing_df.empty,
                         'Expected stale stats to fail validation')

    def test_pipeline_merges_historical_and_live_data(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_dir = os.path.join(tmp_dir, 'input_files')
            output_dir = os.path.join(tmp_dir, 'output')
            os.makedirs(input_dir, exist_ok=True)

            # Historical state file with a 2010 demographic breakdown and non-normalized unit
            hist_state_file = os.path.join(input_dir, 'state_cleaned_07-20.csv')
            with open(hist_state_file, 'w', encoding='utf-8') as f:
                f.write('Year,Geo,StatVar,Quantity,Unit\n')
                f.write(
                    '2010,geoId/01,Count_BirthEvent_LiveBirth_MotherWhiteAlone,40000,\n'
                )
                f.write('2010,geoId/01,Count_BirthEvent_LiveBirth,60000,\n')
                f.write(
                    '2016,geoId/01,Mean_OeGestationalAge_BirthEvent_LiveBirth,38.5,Weeks\n'
                )

            # Live 2024 raw TSV
            sample_state_tsv = os.path.join(input_dir, 'state_raw.tsv')
            with open(sample_state_tsv, 'w', encoding='utf-8') as f:
                f.write(
                    '"Notes"\t"State of Residence"\t"State of Residence Code"\t"Year"\t"Year Code"\tBirths\tAverage OE Gestational Age (weeks)\n'
                )
                f.write('\t"Alabama"\t"01"\t"2024"\t"2024"\t55000\t38.7\n')
                f.write('"Total"\t\t\t\t\t55000\t\n')
                f.write('"---"\n')

            sample_county_tsv = os.path.join(input_dir, 'county_raw.tsv')
            with open(sample_county_tsv, 'w', encoding='utf-8') as f:
                f.write(
                    '"Notes"\t"County of Residence"\t"County of Residence Code"\t"Year"\t"Year Code"\tBirths\tAverage OE Gestational Age (weeks)\n'
                )
                f.write(
                    '\t"Baldwin County, AL"\t"01003"\t"2024"\t"2024"\t2300\t38.7\n'
                )
                f.write('"Total"\t\t\t\t\t2300\t\n')
                f.write('"---"\n')

            process_py = os.path.join(_SCRIPT_PATH, 'process.py')
            cmd = [
                sys.executable, process_py, f'--input_path={input_dir}',
                f'--output_path={output_dir}'
            ]
            subprocess.check_call(cmd)

            state_df = pd.read_csv(os.path.join(output_dir, 'state.csv'),
                                   dtype=str)
            # 1. Historical 2010 demographic slice is preserved
            self.assertIn('Count_BirthEvent_LiveBirth_MotherWhiteAlone',
                          state_df['StatVar'].values)
            # 2. Live 2024 data is included
            self.assertTrue(
                any((state_df['Year'] == '2024') &
                    (state_df['Quantity'] == '55000')))
            # 3. Unit 'Weeks' was normalized to 'Week'
            units = state_df['Unit'].dropna().unique()
            self.assertNotIn('Weeks', units)
            self.assertIn('Week', units)


if __name__ == '__main__':
    unittest.main()
