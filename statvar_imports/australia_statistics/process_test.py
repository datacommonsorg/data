#!/usr/bin/env python3
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
"""Unit tests for Australia Statistics process.py."""

import io
import os
import sys
import tempfile
import unittest

import openpyxl

# Ensure repository root is in sys.path for both local and root-level test runs
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '../..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.australia_statistics import process

for _flag_name in ('input_data', 'output_csv'):
    if _flag_name in process._FLAGS:
        delattr(process._FLAGS, _flag_name)


class ProcessTest(unittest.TestCase):

    def test_parse_sdmx_labour_force_csv_preserves_raw_unscaled_counts(self):
        sample_csv = (
            'DATAFLOW,MEASURE,SEX,AGE,TSEST,REGION,FREQ,TIME_PERIOD,OBS_VALUE\n'
            'ABS:LF(1.0.0),M3,3,1599,10,AUS,M,2026-09,14925.782419\n'
            'ABS:LF(1.0.0),M6,1,1599,10,1,M,2026-09,105.5\n'
            'ABS:LF(1.0.0),M13,2,1599,10,2,M,2026-09,4.249\n')
        rows = process.parse_sdmx_labour_force_csv(sample_csv)
        self.assertEqual(len(rows), 3)
        self.assertEqual(
            rows[0],
            {
                'observationDate': '2026-09',
                'indicatorCd': 'LF_M3_3',
                'regionCd': 'AUS',
                'value': '14925.782419',
            },
        )
        self.assertEqual(
            rows[1],
            {
                'observationDate': '2026-09',
                'indicatorCd': 'LF_M6_1',
                'regionCd': '1',
                'value': '105.5',
            },
        )
        self.assertEqual(
            rows[2],
            {
                'observationDate': '2026-09',
                'indicatorCd': 'LF_M13_2',
                'regionCd': '2',
                'value': '4.2',
            },
        )

    def test_parse_sdmx_erp_q_csv_filters_q2_and_retains_2021_state_age_sex(
            self):
        sample_csv = (
            'DATAFLOW,MEASURE,SEX,AGE,REGION,FREQ,TIME_PERIOD,OBS_VALUE\n'
            'ABS:ERP_Q(1.0.0),1,3,TOT,AUS,Q,2021-Q2,25685412\n'
            'ABS:ERP_Q(1.0.0),1,3,TOT,1,Q,2021-Q2,8095000\n'
            'ABS:ERP_Q(1.0.0),1,1,A04,1,Q,2021-Q2,240000\n'
            'ABS:ERP_Q(1.0.0),1,3,TOT,AUS,Q,2025-Q1,27500000\n'
            'ABS:ERP_Q(1.0.0),1,3,TOT,AUS,Q,2025-Q2,27614411\n'
            'ABS:ERP_Q(1.0.0),1,1,A04,1,Q,2025-Q2,248100\n')
        rows = process.parse_sdmx_erp_q_csv(sample_csv)
        self.assertEqual(len(rows), 3)
        self.assertEqual(
            rows[0],
            {
                'observationDate': '2021',
                'indicatorCd': 'ERP_1_A04',
                'regionCd': '1',
                'value': '240000',
            },
        )
        self.assertEqual(
            rows[1],
            {
                'observationDate': '2025',
                'indicatorCd': 'ERP_3_TOT',
                'regionCd': 'AUS',
                'value': '27614411',
            },
        )
        self.assertEqual(
            rows[2],
            {
                'observationDate': '2025',
                'indicatorCd': 'ERP_1_A04',
                'regionCd': '1',
                'value': '248100',
            },
        )

    def test_parse_household_income_xlsx(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Table 1.1'
        ws.cell(5, 3, '2017–18')
        ws.cell(5, 4, '2019–20')
        ws.cell(8, 1, 'Lowest quintile')
        ws.cell(8, 2, '$')
        ws.cell(8, 3, 411)
        ws.cell(8, 4, 415)
        ws.cell(21, 1, '50th (P50)')
        ws.cell(21, 2, '$')
        ws.cell(21, 3, 926)
        ws.cell(21, 4, 959)
        ws.cell(27, 1, 'Income share')
        ws.cell(28, 1, 'Lowest quintile')
        ws.cell(28, 3, 7.5)

        buf = io.BytesIO()
        wb.save(buf)
        rows = process.parse_household_income_xlsx(buf.getvalue())
        self.assertEqual(len(rows), 4)
        self.assertEqual(
            rows[0],
            {
                'observationDate': '2018',
                'indicatorCd': 'INC_Lowest quintile',
                'regionCd': 'AUS',
                'value': '411',
            },
        )
        self.assertEqual(
            rows[3],
            {
                'observationDate': '2020',
                'indicatorCd': 'INC_50th (P50)',
                'regionCd': 'AUS',
                'value': '959',
            },
        )

    def test_expand_input_files_sorts_largest_first_and_skips_empty(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            empty_file = os.path.join(tmp_dir, '0_empty.csv')
            small_file = os.path.join(tmp_dir, 'a_small.csv')
            large_file = os.path.join(tmp_dir, 'b_large.csv')
            with open(empty_file, 'w', encoding='utf-8') as f:
                f.write('')
            with open(small_file, 'w', encoding='utf-8') as f:
                f.write('a,b\n1,2\n')
            with open(large_file, 'w', encoding='utf-8') as f:
                f.write('a,b\n' + '1,2\n' * 50)

            pattern = os.path.join(tmp_dir, '*.csv')
            expanded = process._expand_input_files(pattern)
            self.assertEqual(expanded, [large_file, small_file])

    def test_collect_staged_rows_and_write_staged_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            lf_path = os.path.join(tmp_dir, 'abs_lf_sdmx.csv')
            with open(lf_path, 'w', encoding='utf-8') as f:
                f.write(
                    'DATAFLOW,MEASURE,SEX,AGE,TSEST,REGION,FREQ,TIME_PERIOD,OBS_VALUE\n'
                    'ABS:LF(1.0.0),M3,3,1599,10,AUS,M,2026-09,14925.782419\n')

            rows = process._collect_staged_rows([lf_path])
            self.assertEqual(len(rows), 1)

            staged_csv = os.path.join(tmp_dir, 'staged.csv')
            process._write_staged_csv(staged_csv, rows)
            with open(staged_csv, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            self.assertEqual(
                lines,
                [
                    'observationDate,indicatorCd,regionCd,value',
                    '2026-09,LF_M3_3,AUS,14925.782419',
                ],
            )

    def test_write_staged_csv_raises_on_empty_rows(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            staged_csv = os.path.join(tmp_dir, 'empty.csv')
            with self.assertRaises(RuntimeError):
                process._write_staged_csv(staged_csv, [])


if __name__ == '__main__':
    unittest.main()
