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
"""Unit tests for preprocess.py."""

import csv
import filecmp
import json
import os
import sys
import tempfile
import unittest

import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.israel_census import preprocess  # pylint: disable=g-import-not-at-top


class PreprocessTest(unittest.TestCase):

    def test_build_population_vital_and_cause_of_death_rows(self):
        pop_rows = preprocess.build_population_religion_rows([
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '10065.5'
            },
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '7212.9'
            },
            {
                'series_id': '3703',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '7693.3'
            },
            {
                'series_id': '3704',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '2111.8'
            },
        ])
        self.assertEqual(len(pop_rows), 1)
        self.assertEqual(pop_rows[0]['Region'], 'ISR')
        self.assertEqual(pop_rows[0]['Year'], '2024')
        self.assertEqual(pop_rows[0]['total'], '10065.5')
        self.assertEqual(pop_rows[0]['jews'], '7212.9')
        self.assertEqual(pop_rows[0]['Others'], '480.4')
        self.assertEqual(pop_rows[0]['arab'], '2111.8')

        vital_rows = preprocess.build_vital_statistics_rows([
            {
                'series_id': '3755',
                'time_unit': '',
                'time_period': '2009-01',
                'value': '2514'
            },
        ])
        yr_map = {r['Year']: r for r in vital_rows}
        self.assertEqual(yr_map['2009']['Arab Christians - Live-Births'],
                         '2514')
        self.assertEqual(yr_map['1996']['Arab Christians - Live-Births'],
                         '2279')

        cod_rows = preprocess.build_cause_of_death_rows([
            {
                'time_unit': 'Year',
                'level4': 'Ischaemic Heart Diseases',
                'name_id': 'Jewish and Others, Males',
                'time_period': '2018-01',
                'value': '26.1',
            },
            {
                'time_unit': 'Year',
                'level4': 'Ischaemic Heart Diseases',
                'name_id': 'Jewish and Others, Males',
                'time_period': '2020-01',
                'value': '24.8',
            },
        ])
        cod_by_yr = {r['Year']: r for r in cod_rows}
        self.assertEqual(cod_by_yr['2019']['isc_jew_male'], '25.2')

    def test_convert_dem1_2_and_dem1_14_binary_excel_to_unscaled_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_dir = os.path.join(tmp_dir, 'input_files')
            out_dir = os.path.join(tmp_dir, 'staged_inputs')
            os.makedirs(raw_dir, exist_ok=True)
            os.makedirs(out_dir, exist_ok=True)

            dem1_2_df = pd.DataFrame([[
                '',
                '74121.8',
                '36638.9',
                '37482.9',
                '68232.0',
                '33630.3',
                '34601.8',
                '5889.8',
                '3008.7',
                '2881.1',
                'TOTAL',
            ]])
            dem1_2_path = os.path.join(raw_dir, 'dem1_2.xls')
            dem1_2_df.to_excel(dem1_2_path,
                               index=False,
                               header=False,
                               engine='openpyxl')
            urb_out = os.path.join(out_dir,
                                   'isr_urban_rural_gender_aa1_2008.csv')
            preprocess._convert_dem1_2_xls_to_csv(dem1_2_path, urb_out)

            dem1_14_df = pd.DataFrame([[
                '0-14',
                '20906',
                '20906',
                '-',
                '-',
                '-',
                '-',
                '14-0',
            ]])
            dem1_14_path = os.path.join(raw_dir, 'dem1_14.xls')
            dem1_14_df.to_excel(dem1_14_path,
                                index=False,
                                header=False,
                                engine='openpyxl')
            age_out = os.path.join(out_dir, 'isr_age_maritalstatus_2008.csv')
            preprocess._convert_dem1_14_xls_to_csv(dem1_14_path, age_out)

            with open(urb_out, 'r', encoding='utf-8') as fp:
                urb_rows = list(csv.DictReader(fp))
            self.assertEqual(len(urb_rows), 1)
            self.assertEqual(urb_rows[0]['Region'], 'ISR')
            self.assertEqual(urb_rows[0]['Year'], '2008')
            self.assertEqual(urb_rows[0]['Grand totalTotal'], '')
            self.assertEqual(urb_rows[0]['Grand totalMales'], '36638.9')
            self.assertEqual(urb_rows[0]['Urban localitiesTotal'], '68232')

            with open(age_out, 'r', encoding='utf-8') as fp:
                age_rows = list(csv.DictReader(fp))
            self.assertEqual(len(age_rows), 1)
            self.assertEqual(age_rows[0]['Region'], 'ISR')
            self.assertEqual(age_rows[0]['Year'], '2008')
            self.assertEqual(age_rows[0]['Age group'], '0-14')
            self.assertEqual(age_rows[0]['Total'], '20906')
            self.assertEqual(age_rows[0]['Never married'], '20906')

    def test_convert_emp_xls_to_csv_for_all_three_employment_tables(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_dir = os.path.join(tmp_dir, 'input_files')
            out_dir = os.path.join(tmp_dir, 'staged_inputs')
            os.makedirs(raw_dir, exist_ok=True)
            os.makedirs(out_dir, exist_ok=True)

            emp_rows = [
                [
                    'סך הכל',
                    '14987.5',
                    '1419.2',
                    '1883',
                    '2218.7',
                    '1997.6',
                    '1672',
                    '1565.9',
                    '1408.5',
                    '1343',
                    '884.5',
                    '595.1',
                    'TOTAL',
                ],
                [
                    'אלמן',
                    '90.3',
                    '-',
                    '-',
                    '-',
                    '2.1',
                    '3.3',
                    '6.6',
                    '10.4',
                    '17.5',
                    '20.1',
                    '30.4',
                    'Widowed',
                ],
            ]
            emp_tables = (
                ('lab4_14.xls', 'isr_menemployed_age_martialstatus_2008.csv',
                 '_Male', False),
                ('lab4_14_1.xls',
                 'isr_totalemployed_age_martialstatus_2008.csv', '', False),
                ('lab4_14_2.xls',
                 'isr_womenemployed_age_martialstatus_2008.csv', '_Female',
                 True),
            )
            for xls_name, csv_name, gender_suf, is_female in emp_tables:
                xls_path = os.path.join(raw_dir, xls_name)
                pd.DataFrame(emp_rows).to_excel(
                    xls_path,
                    index=False,
                    header=False,
                    engine='openpyxl',
                )
                preprocess._convert_emp_xls_to_csv(
                    xls_path,
                    os.path.join(out_dir, csv_name),
                    gender_suf=gender_suf,
                    is_female=is_female,
                )

            with open(
                    os.path.join(out_dir,
                                 'isr_menemployed_age_martialstatus_2008.csv'),
                    'r',
                    encoding='utf-8',
            ) as fp:
                men_rows = list(csv.DictReader(fp))
            self.assertEqual(men_rows[0]['code'], 'מועסקים')
            self.assertEqual(men_rows[0]['סך הכל'], '14987.5')

            with open(
                    os.path.join(
                        out_dir,
                        'isr_totalemployed_age_martialstatus_2008.csv'),
                    'r',
                    encoding='utf-8',
            ) as fp:
                tot_rows = list(csv.DictReader(fp))
            widowed_15_39_row = next(
                r for r in tot_rows if r['code'] == 'אלמן_15_39')
            self.assertEqual(widowed_15_39_row['סך הכל'], '2.1')

            with open(
                    os.path.join(
                        out_dir,
                        'isr_womenemployed_age_martialstatus_2008.csv'),
                    'r',
                    encoding='utf-8',
            ) as fp:
                women_rows = list(csv.DictReader(fp))
            self.assertTrue(any(r['code'] == 'אלמנה' for r in women_rows))

    def test_read_mifkad_table_rows_raises_when_missing(self):
        with self.assertRaises(FileNotFoundError):
            preprocess._read_mifkad_table_rows('/nonexistent/dem1_2.xls')

    def test_build_input_tables_requires_all_expected_inputs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_dir = os.path.join(tmp_dir, 'input_files')
            out_dir = os.path.join(tmp_dir, 'staged_inputs')
            os.makedirs(raw_dir, exist_ok=True)
            with self.assertRaises(FileNotFoundError):
                preprocess.build_input_tables(raw_dir, out_dir)

            with open(os.path.join(raw_dir, 'cbs_series_2_1_1_1.csv'),
                      'w',
                      encoding='utf-8') as fp:
                fp.write(
                    'id,time_name,obs_time_period,obs_value\n3700,Year,2024-01,10065.5\n'
                )
            with open(os.path.join(raw_dir, 'cbs_series_2_3_1.csv'),
                      'w',
                      encoding='utf-8') as fp:
                fp.write(
                    'id,time_name,obs_time_period,obs_value\n3751,Year,2023-01,131143\n'
                )
            with open(os.path.join(raw_dir, 'cbs_series_4_2_1.csv'),
                      'w',
                      encoding='utf-8') as fp:
                fp.write(
                    'id,time_name,path_level4_name,path_name_id_name,obs_time_period,obs_value\n'
                    '1,Year,Ischaemic Heart Diseases,"Jewish and Others, Males",2022-01,25.2\n'
                )
            yishuv_records = [{
                'region_code': '999',
                'data_mode': 'Machoz',
                'payload': {
                    'Groups': [{
                        'Id':
                            3,
                        'Name':
                            'Total',
                        'Subjects': [{
                            'Id': 218,
                            'Name': 'Those aged 15 and over – total',
                            'Value': '5227.3',
                        }],
                    }],
                },
            }, {
                'region_code': '21',
                'data_mode': 'Nafa',
                'payload': {
                    'Groups': [{
                        'Id':
                            2,
                        'Name':
                            'Demography',
                        'Subjects': [
                            {
                                'Id': 18,
                                'Name': 'Population – total',
                                'Value': '104.5',
                            },
                            {
                                'Id': 218,
                                'Name': 'Those aged 15 and over – total',
                                'Value': '73.5',
                            },
                        ],
                    }],
                },
            }]
            with open(os.path.join(raw_dir, 'cbs_yishuv_census_2008.json'),
                      'w',
                      encoding='utf-8') as fp:
                json.dump(yishuv_records, fp)

            pd.DataFrame([[
                '', '74121.8', '36638.9', '37482.9', '68232.0', '33630.3',
                '34601.8', '5889.8', '3008.7', '2881.1', 'TOTAL'
            ]]).to_excel(os.path.join(raw_dir, 'dem1_2.xls'),
                         index=False,
                         header=False,
                         engine='openpyxl')
            pd.DataFrame([[
                '0-14', '20906', '20906', '-', '-', '-', '-', '14-0'
            ]]).to_excel(os.path.join(raw_dir, 'dem1_14.xls'),
                         index=False,
                         header=False,
                         engine='openpyxl')
            emp_rows = [[
                'סך הכל', '14987.5', '1419.2', '1883', '2218.7', '1997.6',
                '1672', '1565.9', '1408.5', '1343', '884.5', '595.1', 'TOTAL'
            ]]
            for xls_name in ('lab4_14.xls', 'lab4_14_1.xls', 'lab4_14_2.xls'):
                pd.DataFrame(emp_rows).to_excel(os.path.join(raw_dir, xls_name),
                                                index=False,
                                                header=False,
                                                engine='openpyxl')

            staged_paths = preprocess.build_input_tables(raw_dir, out_dir)
            self.assertEqual(len(staged_paths), 11)

    def test_sample_raw_input_matches_sample_input(self):
        raw_fixture = os.path.join(_SCRIPT_DIR, 'test_data',
                                   'sample_raw_input.csv')
        staged_fixture = os.path.join(_SCRIPT_DIR, 'test_data',
                                      'sample_input.csv')
        rows = preprocess.build_population_religion_rows(
            preprocess.read_raw_cbs_series_csv(raw_fixture))
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_csv = os.path.join(tmp_dir, 'staged.csv')
            preprocess._write_rows_atomically(
                out_csv,
                ('Region', 'Year', 'total', 'jews', 'nonjews', 'Others',
                 'arab'),
                rows,
            )
            self.assertTrue(
                filecmp.cmp(out_csv, staged_fixture, shallow=False),
                'Preprocessed sample_raw_input.csv does not match sample_input.csv',
            )


if __name__ == '__main__':
    unittest.main()
