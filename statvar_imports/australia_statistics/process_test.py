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
from unittest import mock

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


class _FakeXlrdSheet:
    """Minimal in-memory xlrd Sheet double for unit testing .xls parsers."""

    def __init__(self, grid: list[list[object]]):
        self._grid = grid
        self.nrows = len(grid)
        self.ncols = max((len(r) for r in grid), default=0)

    def cell_value(self, rowx: int, colx: int) -> object:
        if rowx < len(self._grid) and colx < len(self._grid[rowx]):
            return self._grid[rowx][colx]
        return ''


class _FakeXlrdBook:
    """Minimal in-memory xlrd Book double for unit testing .xls parsers."""

    def __init__(self, sheets: dict[str, list[list[object]]]):
        self._sheets = {k: _FakeXlrdSheet(v) for k, v in sheets.items()}

    def sheet_names(self) -> list[str]:
        return list(self._sheets.keys())

    def sheet_by_name(self, name: str) -> _FakeXlrdSheet:
        return self._sheets[name]


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

    def test_parse_census_2021_population_xlsx(self):
        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = 'Table 1'
        ws1.cell(1, 1, 'New South Wales')
        ws1.cell(1, 2, 3984166)
        ws1.cell(1, 3, 4087992)
        ws1.cell(1, 4, 8072163)

        ws3 = wb.create_sheet('Table 3')
        ws3.cell(1, 1, '0-4 years')
        ws3.cell(1, 2, 743898)
        ws3.cell(1, 3, 702777)
        ws3.cell(1, 4, 1446675)

        buf = io.BytesIO()
        wb.save(buf)
        gender_rows, agegrp_rows = process.parse_census_2021_population_xlsx(
            buf.getvalue())
        self.assertEqual(len(gender_rows), 3)
        self.assertEqual(
            gender_rows[0],
            {
                'observationDate': '2021',
                'indicatorCd': 'POP_Males_Total',
                'regionCd': 'New South Wales',
                'value': '3984166',
            },
        )
        self.assertEqual(len(agegrp_rows), 3)
        self.assertEqual(
            agegrp_rows[2],
            {
                'observationDate': '2021',
                'indicatorCd': 'POP_Persons_0-4 years',
                'regionCd': 'AUS',
                'value': '1446675',
            },
        )

    def test_parse_historical_population_xls(self):
        sheet_grid = [
            [],
            [],
            [],
            [],
            ['Age group', 1901, 2016],
            ['Males', '', ''],
            ['5-9', 230000, 780000],
            ['Total', 1977928, 11950000],
        ]
        sheets = {
            'Table 2.1': sheet_grid,
            'Table 2.4': sheet_grid,
            'Table 2.6': sheet_grid,
            'Table 2.8': sheet_grid,
            'Table 2.10': sheet_grid,
            'Table 2.12': sheet_grid,
            'Table 2.15': sheet_grid,
            'Table 2.16': sheet_grid,
            'Table 2.17': sheet_grid,
        }
        with mock.patch.object(
                process.xlrd,
                'open_workbook',
                return_value=_FakeXlrdBook(sheets),
        ):
            aus_1901_1985, aus_1986_2016, states_rows = (
                process.parse_historical_population_xls(b'fake_xls'))

        self.assertEqual(len(aus_1901_1985), 2)
        self.assertEqual(
            aus_1901_1985[0],
            {
                'observationDate': '1901',
                'indicatorCd': 'POP_Males_5-9',
                'regionCd': 'AUS',
                'value': '230000',
            },
        )
        self.assertEqual(len(aus_1986_2016), 2)
        self.assertEqual(
            aus_1986_2016[0]['observationDate'],
            '2016',
        )
        # 8 states (including NT in Table 2.16 and ACT in Table 2.17) * 4 values = 32
        self.assertEqual(len(states_rows), 32)
        regions = {r['regionCd'] for r in states_rows}
        self.assertIn('NT', regions)
        self.assertIn('ACT', regions)

    def test_parse_health_2021_xlsx(self):
        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = 'Table 1'
        ws1.cell(11, 2, '0-4')
        ws1.cell(12, 2, 'years')
        ws1.cell(11, 3, 'Total')
        ws1.cell(12, 3, '')
        ws1.cell(13, 2, 'MALES')
        ws1.cell(14, 1, 'Asthma')
        ws1.cell(14, 2, 41200)
        ws1.cell(14, 3, 950000)
        ws1.cell(15, 2, 'PERSONS')
        ws1.cell(16, 1, 'Asthma')
        ws1.cell(16, 2, 75000)
        ws1.cell(16, 3, 2068000)  # Skipped in Table 1 since Table 3 has Total

        ws3 = wb.create_sheet('Table 3')
        ws3.cell(13, 1, 'Asthma')
        for col_idx in range(2, 11):
            ws3.cell(13, col_idx, 100000 * col_idx)

        buf = io.BytesIO()
        wb.save(buf)
        national_rows, state_rows = process.parse_health_2021_xlsx(
            buf.getvalue())
        self.assertEqual(len(national_rows), 3)
        self.assertEqual(
            national_rows[0],
            {
                'observationDate': '2021',
                'indicatorCd': 'HEALTH_MALES_0-4 years_Asthma',
                'regionCd': 'AUS',
                'value': '41200',
            },
        )
        self.assertEqual(len(state_rows), 9)
        self.assertEqual(
            state_rows[0],
            {
                'observationDate': '2021',
                'indicatorCd': 'HEALTH_Total_Asthma',
                'regionCd': 'NSW',
                'value': '200000',
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

    def test_parse_historical_life_expectancy_xls(self):
        table_6_1 = [
            [],
            [],
            [],
            [],
            [''] * 10 + ['1993-1995', '2015-2017'],
            ['Males'] + [''] * 11,
            ['NSW'] + [''] * 9 + [75.0, 80.5],
        ]
        table_6_2 = [
            [],
            [],
            [],
            [],
            ['Age', '1881-1890', '2015-2017'],
            [],
            [1, 50.12, 79.85],
        ]
        table_6_6 = [
            [],
            [],
            [],
            [],
            ['Age', '1881-1890', '2015-2017'],
            [],
            [1, 53.45, 84.1],
        ]
        sheets = {
            'Table 6.1': table_6_1,
            'Table 6.2': table_6_2,
            'Table 6.6': table_6_6,
        }
        with mock.patch.object(
                process.xlrd,
                'open_workbook',
                return_value=_FakeXlrdBook(sheets),
        ):
            age_rows, state_rows = process.parse_historical_life_expectancy_xls(
                b'fake_xls')

        self.assertEqual(len(state_rows), 1)
        self.assertEqual(
            state_rows[0],
            {
                'observationDate': '2017',
                'indicatorCd': 'LE_Males_0',
                'regionCd': 'NSW',
                'value': '80.5',
            },
        )
        self.assertEqual(len(age_rows), 4)
        self.assertEqual(
            age_rows[0],
            {
                'observationDate': '1890',
                'indicatorCd': 'LE_Males_1',
                'regionCd': 'AUS',
                'value': '50.12',
            },
        )

    def test_parse_recent_life_expectancy_workbook_xlsx_and_xls(self):
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        for idx in range(1, 10):
            ws = wb.create_sheet(f'Table_1.{idx}')
            ws.cell(6, 1, 0)
            ws.cell(6, 5, 81.2)
            ws.cell(6, 9, 85.3)
            ws.cell(7, 1, 1)
            ws.cell(7, 5, 80.4)
            ws.cell(7, 9, 84.5)
        buf = io.BytesIO()
        wb.save(buf)

        age_rows, state_rows = process.parse_recent_life_expectancy_workbook(
            buf.getvalue(), 'xlsx', '2024')
        self.assertEqual(len(state_rows), 18)
        self.assertEqual(len(age_rows), 2)
        self.assertEqual(
            age_rows[0],
            {
                'observationDate': '2024',
                'indicatorCd': 'LE_Males_1',
                'regionCd': 'AUS',
                'value': '80.4',
            },
        )

        xls_grid = [
            [],
            [],
            [],
            [],
            [],
            [],
            [0, '', '', '', 81.2, '', '', '', 85.3],
            [1, '', '', '', 80.4, '', '', '', 84.5],
        ]
        xls_sheets = {f'Table_1.{idx}': xls_grid for idx in range(1, 10)}
        with mock.patch.object(
                process.xlrd,
                'open_workbook',
                return_value=_FakeXlrdBook(xls_sheets),
        ):
            age_xls, state_xls = process.parse_recent_life_expectancy_workbook(
                b'fake_xls', 'xls', '2018')
        self.assertEqual(len(state_xls), 18)
        self.assertEqual(len(age_xls), 2)

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
