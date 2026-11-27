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
from unittest import mock

import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.israel_census import preprocess  # pylint: disable=wrong-import-position


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
            # Anomalous 2025-01 rows (both low Total and corrupted Jews=2149.5 vs Jews and Others=7730.0)
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '2025-01',
                'value': '7766.7'
            },
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '2025-01',
                'value': '2149.5'
            },
            {
                'series_id': '3703',
                'time_unit': 'Year',
                'time_period': '2025-01',
                'value': '7730.0'
            },
            {
                'series_id': '3704',
                'time_unit': 'Year',
                'time_period': '2025-01',
                'value': '2130.6'
            },
            # Anomalous 2026-01 rows where Total is valid (9860.6) but Jews (2149.5) is corrupted vs Jews and Others (7730.0)
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '2026-01',
                'value': '9860.6'
            },
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '2026-01',
                'value': '2149.5'
            },
            {
                'series_id': '3703',
                'time_unit': 'Year',
                'time_period': '2026-01',
                'value': '7730.0'
            },
            {
                'series_id': '3704',
                'time_unit': 'Year',
                'time_period': '2026-01',
                'value': '2130.6'
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
        self.assertEqual(yr_map['2009']['live_births_arab_christian'], '2514')
        self.assertEqual(yr_map['1996']['live_births_arab_christian'], '2279')

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

            total_emp_rows = [
                [
                    'סך הכל',
                    '28048',
                    '2900',
                    '3696',
                    '4081.9',
                    '3686',
                    '3077.7',
                    '2973.8',
                    '2720',
                    '2500',
                    '1600',
                    '812.6',
                    'TOTAL',
                ],
                [
                    'אלמן',
                    '180',
                    '-',
                    '1.5',
                    '6.2',
                    '11',
                    '15',
                    '20',
                    '25',
                    '30',
                    '35',
                    '36.3',
                    'Widowed',
                ],
            ]
            men_emp_rows = [
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
            women_emp_rows = [
                [
                    'סך הכל',
                    '13060.5',
                    '1480.8',
                    '1813',
                    '1863.2',
                    '1688.4',
                    '1405.7',
                    '1407.9',
                    '1311.5',
                    '1157',
                    '715.5',
                    '217.5',
                    'TOTAL',
                ],
                [
                    'אלמנה',
                    '89.7',
                    '-',
                    '1.3',
                    '5.2',
                    '10.1',
                    '11.7',
                    '13.4',
                    '14.6',
                    '12.5',
                    '14.9',
                    '6',
                    'Widowed',
                ],
            ]
            emp_tables = (
                ('lab4_14.xls', 'isr_totalemployed_age_maritalstatus_2008.csv',
                 '', False, total_emp_rows),
                ('lab4_14_1.xls', 'isr_menemployed_age_maritalstatus_2008.csv',
                 '_Male', False, men_emp_rows),
                ('lab4_14_2.xls',
                 'isr_womenemployed_age_maritalstatus_2008.csv', '_Female',
                 True, women_emp_rows),
            )
            for xls_name, csv_name, gender_suf, is_female, rows in emp_tables:
                xls_path = os.path.join(raw_dir, xls_name)
                pd.DataFrame(rows).to_excel(
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
                    os.path.join(
                        out_dir,
                        'isr_totalemployed_age_maritalstatus_2008.csv'),
                    'r',
                    encoding='utf-8',
            ) as fp:
                tot_rows = list(csv.DictReader(fp))
            self.assertEqual(tot_rows[0]['code'], 'סך הכל')
            self.assertEqual(tot_rows[0]['סך הכל'], '28048')
            self.assertFalse(any(r['code'] == 'אלמן_15_39' for r in tot_rows))
            tot_widowed = next(r for r in tot_rows if r['code'] == 'אלמן')
            self.assertEqual(tot_widowed['39-35'], '11')

            with open(
                    os.path.join(out_dir,
                                 'isr_menemployed_age_maritalstatus_2008.csv'),
                    'r',
                    encoding='utf-8',
            ) as fp:
                men_rows = list(csv.DictReader(fp))
            self.assertEqual(men_rows[0]['code'], 'מועסקים')
            self.assertEqual(men_rows[0]['סך הכל'], '14987.5')
            widowed_15_39_row = next(
                r for r in men_rows if r['code'] == 'אלמן_15_39')
            self.assertEqual(widowed_15_39_row['סך הכל'], '2.1')
            men_widowed = next(r for r in men_rows if r['code'] == 'אלמן')
            self.assertEqual(men_widowed['39-35'], '')

            with open(
                    os.path.join(
                        out_dir,
                        'isr_womenemployed_age_maritalstatus_2008.csv'),
                    'r',
                    encoding='utf-8',
            ) as fp:
                women_rows = list(csv.DictReader(fp))
            self.assertTrue(any(r['code'] == 'אלמנה' for r in women_rows))
            self.assertFalse(any(r['code'] == 'אלמן_15_39' for r in women_rows))

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
                fp.write('id,time_name,obs_time_period,obs_value\n'
                         '3700,Year,2024-01,10065.5\n'
                         '3701,Year,2024-01,7212.9\n'
                         '3703,Year,2024-01,7693.3\n'
                         '3704,Year,2024-01,2111.8\n')
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
            pd.DataFrame(
                [['0-14', '20906', '20906', '-', '-', '-', '-',
                  '14-0']]).to_excel(os.path.join(raw_dir, 'dem1_14.xls'),
                                     index=False,
                                     header=False,
                                     engine='openpyxl')
            emp_by_file = {
                'lab4_14.xls': '28048',
                'lab4_14_1.xls': '14987.5',
                'lab4_14_2.xls': '13060.5',
            }
            for xls_name, total_val in emp_by_file.items():
                emp_rows = [[
                    'סך הכל', total_val, '1419.2', '1883', '2218.7', '1997.6',
                    '1672', '1565.9', '1408.5', '1343', '884.5', '595.1',
                    'TOTAL'
                ]]
                pd.DataFrame(emp_rows).to_excel(os.path.join(raw_dir, xls_name),
                                                index=False,
                                                header=False,
                                                engine='openpyxl')

            # Default strict_completeness=True rejects partial 1-region regional tables.
            with self.assertRaisesRegex(RuntimeError, 'too few data rows'):
                preprocess.build_input_tables(raw_dir, out_dir)

            # Seed one stale managed file and one unrelated file in out_dir.
            stale_csv = os.path.join(out_dir, 'isr_obsolete_table.csv')
            keep_txt = os.path.join(out_dir, 'notes.txt')
            with open(stale_csv, 'w', encoding='utf-8') as fp:
                fp.write('stale\n')
            with open(keep_txt, 'w', encoding='utf-8') as fp:
                fp.write('keep\n')

            staged_paths = preprocess.build_input_tables(
                raw_dir, out_dir, strict_completeness=False)
            self.assertEqual(len(staged_paths), 11)
            self.assertFalse(os.path.exists(stale_csv))
            self.assertTrue(os.path.exists(keep_txt))
            with open(
                    os.path.join(
                        out_dir,
                        'isr_totalemployed_age_maritalstatus_2008.csv'),
                    'r',
                    encoding='utf-8',
            ) as fp:
                self.assertEqual(list(csv.DictReader(fp))[0]['סך הכל'], '28048')
            with open(
                    os.path.join(out_dir,
                                 'isr_menemployed_age_maritalstatus_2008.csv'),
                    'r',
                    encoding='utf-8',
            ) as fp:
                self.assertEqual(
                    list(csv.DictReader(fp))[0]['סך הכל'], '14987.5')
            with open(
                    os.path.join(
                        out_dir,
                        'isr_womenemployed_age_maritalstatus_2008.csv'),
                    'r',
                    encoding='utf-8',
            ) as fp:
                self.assertEqual(
                    list(csv.DictReader(fp))[0]['סך הכל'], '13060.5')

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

    def test_parse_cbs_boardsgenerator_census_payload_preserves_numeric_zero(
            self):
        payload = {
            'Groups': [{
                'Id':
                    0,
                'Name':
                    'Zero Group',
                'Subjects': [
                    {
                        'Id': 18,
                        'Name': 'Zero int',
                        'Value': 0,
                    },
                    {
                        'Id': 19,
                        'Name': 'Zero float',
                        'Value': 0.0,
                    },
                    {
                        'Id': 20,
                        'Name': 'Missing value',
                        'Value': None,
                    },
                ],
            }]
        }
        rows = preprocess.parse_cbs_boardsgenerator_census_payload(
            payload, '999', 'Machoz')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['group_id'], '0')
        self.assertEqual(rows[0]['subject_id'], '18')
        self.assertEqual(rows[0]['value'], '0')
        self.assertEqual(rows[1]['subject_id'], '19')
        self.assertEqual(rows[1]['value'], '0.0')

    def test_read_mifkad_table_rows_uses_calamine_for_ole2_xls(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            xls_path = os.path.join(tmp_dir, 'mock_ole2.xls')
            with open(xls_path, 'wb') as fp:
                fp.write(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1mock_ole2_body')
            fake_df = pd.DataFrame([['row1_c1', 'row1_c2']])
            with mock.patch.object(pd, 'read_excel',
                                   return_value=fake_df) as mock_read:
                rows = preprocess._read_mifkad_table_rows(xls_path)
            mock_read.assert_called_once_with(
                xls_path,
                header=None,
                dtype=str,
                engine='calamine',
            )
            self.assertEqual(rows, [['row1_c1', 'row1_c2']])

    def test_build_population_religion_rows_guards_pre_1995_and_missing_arab(
            self):
        rows = preprocess.build_population_religion_rows([
            # Valid pre-1995 row (Total >= Jews + Non-Jews - 1.0)
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '1990-01',
                'value': '4821.7',
            },
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '1990-01',
                'value': '3946.7',
            },
            {
                'series_id': '3702',
                'time_unit': 'Year',
                'time_period': '1990-01',
                'value': '875.0',
            },
            # Anomalous pre-1995 row (Total < Jews + Non-Jews)
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '1991-01',
                'value': '500.0',
            },
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '1991-01',
                'value': '1203.0',
            },
            {
                'series_id': '3702',
                'time_unit': 'Year',
                'time_period': '1991-01',
                'value': '167.1',
            },
            # Valid transition year (1994, no Non-Jews and no Jews-and-Others)
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '1994-01',
                'value': '5471.5',
            },
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '1994-01',
                'value': '4441.1',
            },
            # Anomalous transition row (Jews > Total)
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '1993-01',
                'value': '100.0',
            },
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '1993-01',
                'value': '200.0',
            },
            # Anomalous post-1994 row missing Arab (3704)
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '9000.0',
            },
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '7000.0',
            },
            {
                'series_id': '3703',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '7500.0',
            },
        ])
        self.assertEqual([r['Year'] for r in rows], ['1990', '1994'])

    def test_convert_dem1_14_subtracts_0_to_14_from_never_married_15_plus(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            dem1_14_path = os.path.join(tmp_dir, 'dem1_14.xls')
            out_csv = os.path.join(tmp_dir, 'isr_age_maritalstatus_2008.csv')
            df = pd.DataFrame([
                [
                    'סך הכל',
                    '74042.5',
                    '36684.4',
                    '31301.2',
                    '2996',
                    '2793.7',
                    '267.3',
                    'TOTAL',
                ],
                ['14-0', '20524.6', '20524.6', '', '', '', '', '0-14'],
            ])
            df.to_excel(dem1_14_path,
                        index=False,
                        header=False,
                        engine='openpyxl')
            preprocess._convert_dem1_14_xls_to_csv(dem1_14_path, out_csv)
            with open(out_csv, 'r', encoding='utf-8') as fp:
                rows = list(csv.DictReader(fp))
            self.assertEqual([r['Age group'] for r in rows], ['15+', '0-14'])
            row_15p = rows[0]
            self.assertEqual(row_15p['Total'], '')
            self.assertEqual(row_15p['Never married'], '16159.8')
            self.assertEqual(row_15p['Married'], '31301.2')
            self.assertEqual(row_15p['Divorced'], '2996')
            self.assertEqual(row_15p['Widowed'], '2793.7')
            self.assertEqual(row_15p['Married but separated'], '267.3')
            self.assertEqual(rows[1]['Never married'], '20524.6')

            # Missing 0-14 row must omit Never married on 15+ instead of emitting all-ages total.
            dem_no_child = os.path.join(tmp_dir, 'dem_no_child.xls')
            out_no_child = os.path.join(tmp_dir, 'out_no_child.csv')
            pd.DataFrame([[
                'TOTAL', '74042.5', '36684.4', '31301.2', '2996', '2793.7',
                '267.3', 'TOTAL'
            ]]).to_excel(dem_no_child,
                         index=False,
                         header=False,
                         engine='openpyxl')
            preprocess._convert_dem1_14_xls_to_csv(dem_no_child, out_no_child)
            with open(out_no_child, 'r', encoding='utf-8') as fp:
                rows_nc = list(csv.DictReader(fp))
            self.assertEqual(rows_nc[0]['Age group'], '15+')
            self.assertEqual(rows_nc[0]['Never married'], '')
            self.assertEqual(rows_nc[0]['Married'], '31301.2')

            # Negative difference (all_ages < 0-14) must warn and drop Never married.
            dem_bad = os.path.join(tmp_dir, 'dem_bad.xls')
            out_bad = os.path.join(tmp_dir, 'out_bad.csv')
            pd.DataFrame([
                ['TOTAL', '500', '100', '300', '', '', '', 'TOTAL'],
                ['0-14', '200', '200', '', '', '', '', '0-14'],
            ]).to_excel(dem_bad, index=False, header=False, engine='openpyxl')
            preprocess._convert_dem1_14_xls_to_csv(dem_bad, out_bad)
            with open(out_bad, 'r', encoding='utf-8') as fp:
                rows_bad = list(csv.DictReader(fp))
            self.assertEqual(rows_bad[0]['Age group'], '15+')
            self.assertEqual(rows_bad[0]['Never married'], '')
            self.assertEqual(rows_bad[0]['Married'], '300')

    def test_parse_number_rejects_non_finite_floats(self):
        for token in ('nan', 'NaN', 'inf', '-inf', 'Infinity', '1e500'):
            self.assertIsNone(preprocess._parse_number(token))

        # Non-finite values must not crash build_population_religion_rows.
        rows = preprocess.build_population_religion_rows([
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': 'nan',
            },
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': 'inf',
            },
            {
                'series_id': '3703',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '-inf',
            },
        ])
        self.assertEqual(rows, [])

    def test_population_vital_and_cod_reject_negative_partial_and_unicode_years(
            self):
        pop_rows = preprocess.build_population_religion_rows([
            # Negative value (arab=-500) must be skipped.
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '2020-01',
                'value': '10000',
            },
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '2020-01',
                'value': '7212.9',
            },
            {
                'series_id': '3703',
                'time_unit': 'Year',
                'time_period': '2020-01',
                'value': '7693.3',
            },
            {
                'series_id': '3704',
                'time_unit': 'Year',
                'time_period': '2020-01',
                'value': '-500',
            },
            # Missing 3703 with 3704 (arab > total) must be skipped.
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '2021-01',
                'value': '1000',
            },
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '2021-01',
                'value': '900',
            },
            {
                'series_id': '3704',
                'time_unit': 'Year',
                'time_period': '2021-01',
                'value': '2130.6',
            },
            # Partial row missing Total (3700) must be skipped.
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '2022-01',
                'value': '7200',
            },
            # Non-ASCII Unicode digits ('٢٠٢٤-01') must be skipped.
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '٢٠٢٤-01',
                'value': '10065.5',
            },
        ])
        self.assertEqual(pop_rows, [])

        self.assertEqual(
            preprocess.build_vital_statistics_rows([{
                'series_id': '3751',
                'time_unit': 'Year',
                'time_period': '٢٠٢٤-01',
                'value': '130000',
            }]),
            [],
        )
        self.assertEqual(
            preprocess.build_cause_of_death_rows([{
                'series_id': '70001',
                'time_unit': 'Year',
                'time_period': '٢٠٢٤-01',
                'value': '25.2',
            }]),
            [],
        )

    def test_parse_and_convert_yishuv_json_guards_malformed_and_unknown_mode(
            self):
        # Non-dict Groups and Subjects entries are skipped without AttributeError.
        payload = {
            'Groups': [
                'bad_group',
                {
                    'Id':
                        2,
                    'Name':
                        'Demography',
                    'Subjects': [
                        'bad_subject',
                        {
                            'Id': 18,
                            'Name': 'Population – total',
                            'Value': '104.5',
                        },
                    ],
                },
            ]
        }
        rows = preprocess.parse_cbs_boardsgenerator_census_payload(
            payload, '21', 'Nafa')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['value'], '104.5')

        # Unknown data_mode must not silently fall through into nafa_age.
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = os.path.join(tmp_dir, 'cbs_yishuv_census_2008.json')
            records = [
                'bad_record',
                {
                    'region_code': '21',
                    'data_mode': 'Yishuv',
                    'payload': {
                        'Groups': [{
                            'Id':
                                3,
                            'Name':
                                'Total',
                            'Subjects': [{
                                'Id': 218,
                                'Name': 'Those aged 15 and over – total',
                                'Value': '999.9',
                            }],
                        }]
                    },
                },
            ]
            with open(json_path, 'w', encoding='utf-8') as fp:
                json.dump(records, fp)
            preprocess._convert_yishuv_json_to_csvs(json_path, tmp_dir)
            with open(os.path.join(tmp_dir,
                                   'isr_subdistrict_age_gender_2008.csv'),
                      'r',
                      encoding='utf-8') as fp:
                self.assertEqual(list(csv.DictReader(fp)), [])

    def test_build_cause_of_death_rows_uses_series_id_and_normalized_labels(
            self):
        rows = preprocess.build_cause_of_death_rows([
            # Exact CBS series_id resolves even when labels are perturbed.
            {
                'series_id': '70013',
                'time_unit': 'Year',
                'level4': 'Renamed Cause Label',
                'name_id': 'Renamed Group Label',
                'time_period': '2022-01',
                'value': '12.3',
            },
            # Unused "All Causes" series_id is always ignored.
            {
                'series_id': '70007',
                'time_unit': 'Year',
                'level4': 'Ischaemic Heart Diseases',
                'name_id': 'Jewish and Others, Males',
                'time_period': '2022-01',
                'value': '999.9',
            },
            # Unknown synthetic series_id falls back to normalized label matching.
            {
                'series_id': '1',
                'time_unit': 'Year',
                'level4': '  ISCHAEMIC   Heart Diseases ',
                'name_id': 'Jewish   and Others |  Males ',
                'time_period': '2022-01',
                'value': '25.2',
            },
        ])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['Year'], '2022')
        self.assertEqual(rows[0]['infd_jew_female'], '12.3')
        self.assertEqual(rows[0]['isc_jew_male'], '25.2')

    def test_cause_of_death_fallback_never_overwrites_canonical_series_id(self):
        # Canonical 70001 followed by unknown 99999 with identical labels.
        rows_after = preprocess.build_cause_of_death_rows([
            {
                'series_id': '70001',
                'time_unit': 'Year',
                'level4': 'Ischaemic Heart Diseases',
                'name_id': 'Jewish  and Others| Males',
                'time_period': '2022-01',
                'value': '25.2',
            },
            {
                'series_id': '99999',
                'time_unit': 'Year',
                'level4': 'Ischaemic Heart Diseases',
                'name_id': 'Jewish  and Others| Males',
                'time_period': '2022-01',
                'value': '999.9',
            },
        ])
        self.assertEqual(rows_after[0]['isc_jew_male'], '25.2')

        # Unknown 99999 before canonical 70001: canonical still wins.
        rows_before = preprocess.build_cause_of_death_rows([
            {
                'series_id': '99999',
                'time_unit': 'Year',
                'level4': 'Ischaemic Heart Diseases',
                'name_id': 'Jewish  and Others| Males',
                'time_period': '2022-01',
                'value': '999.9',
            },
            {
                'series_id': '70001',
                'time_unit': 'Year',
                'level4': 'Ischaemic Heart Diseases',
                'name_id': 'Jewish  and Others| Males',
                'time_period': '2022-01',
                'value': '25.2',
            },
        ])
        self.assertEqual(rows_before[0]['isc_jew_male'], '25.2')

    def test_series_builders_reject_malformed_periods_and_prefer_year_rows(
            self):
        # Malformed periods ('2024-Q2', '2024xyz', '2024-02') are rejected.
        self.assertEqual(
            preprocess.build_population_religion_rows([
                {
                    'series_id': '3700',
                    'time_unit': 'Year',
                    'time_period': '2024-Q2',
                    'value': '10000',
                },
                {
                    'series_id': '3701',
                    'time_unit': 'Year',
                    'time_period': '2024-Q2',
                    'value': '7000',
                },
                {
                    'series_id': '3700',
                    'time_unit': 'Year',
                    'time_period': '2023xyz',
                    'value': '10000',
                },
                {
                    'series_id': '3701',
                    'time_unit': 'Year',
                    'time_period': '2023xyz',
                    'value': '7000',
                },
            ]),
            [],
        )
        # Explicit time_unit='Year' takes precedence over blank time_unit.
        pop_rows = preprocess.build_population_religion_rows([
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '1994-01',
                'value': '5471.5',
            },
            {
                'series_id': '3700',
                'time_unit': '',
                'time_period': '1994-01',
                'value': '9999.0',
            },
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '1994-01',
                'value': '4441.1',
            },
        ])
        self.assertEqual(len(pop_rows), 1)
        self.assertEqual(pop_rows[0]['total'], '5471.5')

    def test_population_independent_nonjews_and_total_only_rejection(self):
        # Both 3703 and anomalous 3702 (nonjews=999999) must be skipped.
        rows = preprocess.build_population_religion_rows([
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '10000',
            },
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '7000',
            },
            {
                'series_id': '3702',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '999999',
            },
            {
                'series_id': '3703',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '7500',
            },
            {
                'series_id': '3704',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '2000',
            },
            # Total-only row (3700 without any religion breakdown) must be skipped.
            {
                'series_id': '3700',
                'time_unit': 'Year',
                'time_period': '2025-01',
                'value': '10200',
            },
        ])
        self.assertEqual(rows, [])

    def test_negative_values_rejected_across_all_converters_and_r26_guard(self):
        # Vital statistics negative rejected.
        self.assertEqual(
            preprocess.build_vital_statistics_rows([{
                'series_id': '3751',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '-500',
            }]),
            [],
        )
        # Cause of death negative rejected.
        self.assertEqual(
            preprocess.build_cause_of_death_rows([{
                'series_id': '70001',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '-12.5',
            }]),
            [],
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            # dem1_14 negative 0-14 must NOT inflate 15+ Never married.
            dem_path = os.path.join(tmp_dir, 'dem1_14_neg.xls')
            dem_out = os.path.join(tmp_dir, 'dem1_14_out.csv')
            pd.DataFrame([
                ['TOTAL', '1000', '500', '400', '', '', '', 'TOTAL'],
                ['0-14', '200', '-100', '', '', '', '', '0-14'],
            ]).to_excel(dem_path, index=False, header=False, engine='openpyxl')
            preprocess._convert_dem1_14_xls_to_csv(dem_path, dem_out)
            with open(dem_out, 'r', encoding='utf-8') as fp:
                rows = list(csv.DictReader(fp))
            self.assertEqual(rows[0]['Age group'], '15+')
            self.assertEqual(rows[0]['Never married'], '')
            self.assertEqual(rows[0]['Married'], '400')
            self.assertEqual(rows[1]['Age group'], '0-14')
            self.assertEqual(rows[1]['Never married'], '')

            # yishuv JSON negative value rejected & integer 0 region_code preserved.
            json_path = os.path.join(tmp_dir, 'yishuv_neg.json')
            with open(json_path, 'w', encoding='utf-8') as fp:
                json.dump(
                    [
                        {
                            'region_code': 0,
                            'data_mode': 'Machoz',
                            'payload': {
                                'Groups': [{
                                    'Id': 1,
                                    'Subjects': [{
                                        'Id': 218,
                                        'Value': '10'
                                    }]
                                }]
                            },
                        },
                        {
                            'region_code': '999',
                            'data_mode': 'Machoz',
                            'payload': {
                                'Groups': [{
                                    'Id': 3,
                                    'Subjects': [{
                                        'Id': 218,
                                        'Value': '-10.5'
                                    }]
                                }]
                            },
                        },
                    ],
                    fp,
                )
            preprocess._convert_yishuv_json_to_csvs(json_path, tmp_dir)
            with open(os.path.join(tmp_dir,
                                   'isr_agebracket_gender_aa1_2008.csv'),
                      'r',
                      encoding='utf-8') as fp:
                self.assertEqual(list(csv.DictReader(fp)), [])

            # lab4_14_1.xls raises RuntimeError if 15-34 widowed male cells are
            # populated alongside CBS footnote R26 35-39 merged cell.
            emp_path = os.path.join(tmp_dir, 'lab4_14_1_overlap.xls')
            pd.DataFrame([
                [
                    'אלמן', '90.4', '0.5', '-', '-', '2.1', '3.3', '6.6',
                    '10.4', '17.5', '20', '30.5', 'Widowed'
                ],
            ]).to_excel(emp_path, index=False, header=False, engine='openpyxl')
            with self.assertRaisesRegex(RuntimeError, 'double-count'):
                preprocess._convert_emp_xls_to_csv(
                    emp_path,
                    os.path.join(tmp_dir, 'out_emp.csv'),
                    gender_suf='_Male',
                    is_female=False,
                )

    def test_read_raw_cbs_series_csv_strips_whitespace_headers(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = os.path.join(tmp_dir, 'spaced.csv')
            with open(csv_path, 'w', encoding='utf-8') as fp:
                fp.write(' id , time_name , obs_time_period , obs_value \n'
                         '3700,Year,2024-01,10065.5\n')
            rows = preprocess.read_raw_cbs_series_csv(csv_path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['series_id'], '3700')
            self.assertEqual(rows[0]['time_unit'], 'Year')
            self.assertEqual(rows[0]['time_period'], '2024-01')
            self.assertEqual(rows[0]['value'], '10065.5')

    def test_mifkad_converters_tolerate_trailing_empty_cols_and_unknown_hebrew(
            self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # dem1_2 with extra trailing empty columns after index 10.
            dem1_2_p = os.path.join(tmp_dir, 'dem1_2_wide.xls')
            dem1_2_out = os.path.join(tmp_dir, 'dem1_2.csv')
            pd.DataFrame([
                [
                    'מחוז המרכז',
                    '17704.2',
                    '8757.9',
                    '8946.3',
                    '16258.3',
                    '8015.2',
                    '8243.1',
                    '1446',
                    '742.8',
                    '703.2',
                    'Central District',
                    '',
                    '',
                ],
            ]).to_excel(dem1_2_p, index=False, header=False, engine='openpyxl')
            preprocess._convert_dem1_2_xls_to_csv(dem1_2_p, dem1_2_out)
            with open(dem1_2_out, 'r', encoding='utf-8') as fp:
                rows_12 = list(csv.DictReader(fp))
            self.assertEqual(len(rows_12), 1)
            self.assertEqual(rows_12[0]['Region'], 'DIST_4')

            # dem1_14 with altered Hebrew in row[0] and 'TOTAL' at row[7].
            dem1_14_p = os.path.join(tmp_dir, 'dem1_14_wide.xls')
            dem1_14_out = os.path.join(tmp_dir, 'dem1_14.csv')
            pd.DataFrame([
                [
                    'תווית שונה',
                    '74042.5',
                    '36684.4',
                    '31301.2',
                    '2996',
                    '2793.7',
                    '267.3',
                    'TOTAL',
                    '',
                ],
                ['14-0', '20524.6', '20524.6', '', '', '', '', '0-14', ''],
            ]).to_excel(dem1_14_p, index=False, header=False, engine='openpyxl')
            preprocess._convert_dem1_14_xls_to_csv(dem1_14_p, dem1_14_out)
            with open(dem1_14_out, 'r', encoding='utf-8') as fp:
                rows_114 = list(csv.DictReader(fp))
            self.assertEqual([r['Age group'] for r in rows_114],
                             ['15+', '0-14'])
            self.assertEqual(rows_114[0]['Never married'], '16159.8')

            # lab4_14 with extra trailing empty columns after index 12.
            emp_p = os.path.join(tmp_dir, 'lab4_14_wide.xls')
            emp_out = os.path.join(tmp_dir, 'emp.csv')
            pd.DataFrame([
                [
                    'סך הכל',
                    '28048',
                    '3004.3',
                    '3696',
                    '4081.9',
                    '3686',
                    '3077.7',
                    '2973.8',
                    '2720',
                    '2448.1',
                    '1498.6',
                    '861.7',
                    'TOTAL',
                    '',
                ],
            ]).to_excel(emp_p, index=False, header=False, engine='openpyxl')
            preprocess._convert_emp_xls_to_csv(emp_p,
                                               emp_out,
                                               gender_suf='',
                                               is_female=False)
            with open(emp_out, 'r', encoding='utf-8') as fp:
                rows_emp = list(csv.DictReader(fp))
            self.assertEqual(rows_emp[0]['סך הכל'], '28048')

    def test_negative_duplicates_order_independent_and_fallback_not_masking_negative(
            self):
        base_2024 = [
            {
                'series_id': '3701',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '7212.9',
            },
            {
                'series_id': '3703',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '7693.3',
            },
            {
                'series_id': '3704',
                'time_unit': 'Year',
                'time_period': '2024-01',
                'value': '2111.8',
            },
        ]
        pos_row = {
            'series_id': '3700',
            'time_unit': 'Year',
            'time_period': '2024-01',
            'value': '10065.5',
        }
        neg_row = {
            'series_id': '3700',
            'time_unit': 'Year',
            'time_period': '2024-01',
            'value': '-5',
        }
        self.assertEqual(
            preprocess.build_population_religion_rows([pos_row, neg_row] +
                                                      base_2024), [])
        self.assertEqual(
            preprocess.build_population_religion_rows([neg_row, pos_row] +
                                                      base_2024), [])

        # Negative 2019 cause-of-death value must NOT be silently replaced by
        # _CBS_2019_CAUSE_OF_DEATH_FALLBACK.
        cod_rows = preprocess.build_cause_of_death_rows([
            {
                'series_id': '70001',
                'time_unit': 'Year',
                'time_period': '2018-01',
                'value': '26.0',
            },
            {
                'series_id': '70001',
                'time_unit': 'Year',
                'time_period': '2019-01',
                'value': '-99.0',
            },
            {
                'series_id': '70001',
                'time_unit': 'Year',
                'time_period': '2020-01',
                'value': '24.0',
            },
        ])
        self.assertEqual([r['Year'] for r in cod_rows], ['2018', '2020'])

        # Blank-time_unit monthly series ('2024-01' + '2024-02') is skipped.
        self.assertEqual(
            preprocess.build_vital_statistics_rows([
                {
                    'series_id': '3751',
                    'time_unit': '',
                    'time_period': '2024-01',
                    'value': '100',
                },
                {
                    'series_id': '3751',
                    'time_unit': '',
                    'time_period': '2024-02',
                    'value': '105',
                },
            ]),
            [],
        )

        # Completeness floor covers all 11 staged CSV filenames.
        self.assertEqual(
            set(preprocess.EXPECTED_MIN_DATA_ROWS_BY_TABLE),
            set(preprocess.EXPECTED_INPUT_TABLE_FILENAMES),
        )


if __name__ == '__main__':
    unittest.main()
