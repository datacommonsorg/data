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

        con = duckdb.connect()

        # Rule 1: check_latest_date_freshness (lag_years <= 2)
        rule1 = cfg['rules'][0]
        q1 = rule1['params']['query']
        c1 = rule1['params']['condition']

        valid_stats = pd.DataFrame([{
            'StatVar': 'Count_BirthEvent_LiveBirth',
            'MaxDate': '2024'
        }])
        con.register('stats', valid_stats)
        failing_df = con.execute(
            f'WITH data_to_validate AS ({q1}) SELECT * FROM data_to_validate WHERE NOT ({c1})'
        ).fetchdf()
        self.assertTrue(failing_df.empty,
                        f'Expected valid stats to pass rule 1: {failing_df}')

        invalid_stats = pd.DataFrame([{
            'StatVar': 'Count_BirthEvent_LiveBirth',
            'MaxDate': '2018'
        }])
        con.register('stats', invalid_stats)
        failing_df = con.execute(
            f'WITH data_to_validate AS ({q1}) SELECT * FROM data_to_validate WHERE NOT ({c1})'
        ).fetchdf()
        self.assertFalse(failing_df.empty,
                         'Expected stale stats to fail rule 1')

        # Rule 2: check_scoped_date_consistency_active_statvars
        rule2 = cfg['rules'][1]
        q2 = rule2['params']['query']
        c2 = rule2['params']['condition']

        active_statvars = [
            'Count_BirthEvent_LiveBirth',
            'Mean_MothersAge_BirthEvent_LiveBirth',
            'Mean_OeGestationalAge_BirthEvent_LiveBirth',
            'Mean_LmpGestationalAge_BirthEvent_LiveBirth',
            'Mean_BirthWeight_BirthEvent_LiveBirth',
            'Mean_PrePregnancyBMI_BirthEvent_LiveBirth',
            'Mean_PrenatalVisitCount_BirthEvent_LiveBirth',
            'Mean_IntervalSinceLastBirth_BirthEvent_LiveBirth',
            'Mean_IntervalSinceLastPregnancyOutcomeNotLiveBirth_BirthEvent_LiveBirth',
        ]
        all_active_stats = pd.DataFrame([{
            'StatVar': sv,
            'MaxDate': '2024'
        } for sv in active_statvars])
        con.register('stats', all_active_stats)
        failing_df = con.execute(
            f'WITH data_to_validate AS ({q2}) SELECT * FROM data_to_validate WHERE NOT ({c2})'
        ).fetchdf()
        self.assertTrue(
            failing_df.empty,
            f'Expected 9 active stats to pass rule 2: {failing_df}')

        missing_active = pd.DataFrame([{
            'StatVar': sv,
            'MaxDate': '2024'
        } for sv in active_statvars[:8]])
        con.register('stats', missing_active)
        failing_df = con.execute(
            f'WITH data_to_validate AS ({q2}) SELECT * FROM data_to_validate WHERE NOT ({c2})'
        ).fetchdf()
        self.assertFalse(failing_df.empty,
                         'Expected missing statvar to fail rule 2')

        mismatch_dates = all_active_stats.copy()
        mismatch_dates.loc[0, 'MaxDate'] = '2023'
        con.register('stats', mismatch_dates)
        failing_df = con.execute(
            f'WITH data_to_validate AS ({q2}) SELECT * FROM data_to_validate WHERE NOT ({c2})'
        ).fetchdf()
        self.assertFalse(failing_df.empty,
                         'Expected date mismatch to fail rule 2')

    def test_parse_wonder_tsv_with_footnote_and_invalid_fips(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sample_tsv = os.path.join(tmp_dir, 'state_sample.tsv')
            with open(sample_tsv, 'w', encoding='utf-8') as f:
                f.write(
                    '"Notes"\t"State of Residence"\t"State of Residence Code"\t"Year"\t"Year Code"\tBirths\tAverage Age of Mother (years)\n'
                )
                f.write('\t"Alabama"\t"01"\t"2022"\t"2022"\t58000\t28.5\n')
                f.write('1\t"Alaska"\t"02"\t"2022"\t"2022"\t9500\t29.1\n')
                f.write('*\t"Arizona"\t"04"\t"2022"\t"2022"\t78000\t29.3\n')
                f.write('\t"Unidentified"\t"99"\t"2022"\t"2022"\t500\t27.0\n')
                f.write('"Total"\t\t\t\t\t146000\t\n')
                f.write('"---"\n')

            df = process.parse_wonder_tsv(sample_tsv, geo_type='state')
            geos = df['Geo'].unique().tolist()
            self.assertIn('geoId/01', geos)
            self.assertIn('geoId/02', geos)
            self.assertIn('geoId/04', geos)
            self.assertNotIn('geoId/99', geos)
            self.assertEqual(
                len(df[df['StatVar'] == 'Count_BirthEvent_LiveBirth']), 3)

            age_rows = df[df['StatVar'] ==
                          'Mean_MothersAge_BirthEvent_LiveBirth']
            self.assertEqual(len(age_rows), 3)
            self.assertTrue(all(age_rows['Unit'] == 'Year'))

    def test_chronological_bracket_deduplication(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_dir = os.path.join(tmp_dir, 'input_files')
            output_dir = os.path.join(tmp_dir, 'output')
            os.makedirs(input_dir, exist_ok=True)

            f_95_02 = os.path.join(input_dir, 'state_cleaned_95-02.csv')
            with open(f_95_02, 'w', encoding='utf-8') as f:
                f.write('Year,Geo,StatVar,Quantity,Unit\n')
                f.write('2002,geoId/01,Count_BirthEvent_LiveBirth,11111,\n')

            f_03_06 = os.path.join(input_dir, 'state_cleaned_03-06.csv')
            with open(f_03_06, 'w', encoding='utf-8') as f:
                f.write('Year,Geo,StatVar,Quantity,Unit\n')
                f.write('2002,geoId/01,Count_BirthEvent_LiveBirth,22222,\n')

            f_county = os.path.join(input_dir, 'county_cleaned_95-02.csv')
            with open(f_county, 'w', encoding='utf-8') as f:
                f.write('Year,Geo,StatVar,Quantity,Unit\n')
                f.write('2002,geoId/01003,Count_BirthEvent_LiveBirth,1234,\n')

            process_py = os.path.join(_SCRIPT_PATH, 'process.py')
            cmd = [
                sys.executable, process_py, f'--input_path={input_dir}',
                f'--output_path={output_dir}'
            ]
            subprocess.check_call(cmd)

            state_df = pd.read_csv(os.path.join(output_dir, 'state.csv'),
                                   dtype=str)
            row_2002 = state_df[(state_df['Year'] == '2002') &
                                (state_df['Geo'] == 'geoId/01')]
            self.assertEqual(len(row_2002), 1)
            self.assertEqual(row_2002.iloc[0]['Quantity'], '22222')

    def test_integer_quantity_normalization(self):
        df = pd.DataFrame([
            {
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '57647.0'
            },
            {
                'StatVar': 'Mean_BirthWeight_BirthEvent_LiveBirth',
                'Quantity': '3179.09'
            },
        ])
        norm_df = process._normalize_quantities(df)
        self.assertEqual(norm_df.iloc[0]['Quantity'], '57647')
        self.assertEqual(norm_df.iloc[1]['Quantity'], '3179.09')

    def test_pipeline_merges_historical_and_live_data(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_dir = os.path.join(tmp_dir, 'input_files')
            output_dir = os.path.join(tmp_dir, 'output')
            os.makedirs(input_dir, exist_ok=True)

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
                f.write(
                    '2016,geoId/01,Mean_MothersAge_BirthEvent_LiveBirth,28.2,Years\n'
                )

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
            self.assertIn('Count_BirthEvent_LiveBirth_MotherWhiteAlone',
                          state_df['StatVar'].values)
            self.assertTrue(
                any((state_df['Year'] == '2024') &
                    (state_df['Quantity'] == '55000')))
            units = state_df['Unit'].dropna().unique()
            self.assertNotIn('Weeks', units)
            self.assertIn('Week', units)
            self.assertNotIn('Years', units)
            self.assertIn('Year', units)


if __name__ == '__main__':
    unittest.main()
