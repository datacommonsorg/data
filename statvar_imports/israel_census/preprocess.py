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
"""Converts the 5 CBS Mifkad .xls files in input_files/ into CSVs and copies existing CSVs to staged_inputs/."""

import argparse
from collections import defaultdict
import csv
import math
import os
import shutil

from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

MIFKAD_2008_AGE_ROWS_1_14 = {
    'Total': '',
    'סך הכל': '',
    '14-0': '_0To14Years',
    '0-14': '_0To14Years',
    '24-15': '_15To24Years',
    '15-24': '_15To24Years',
    '34-25': '_25To34Years',
    '25-34': '_25To34Years',
    '39-35': '_35To39Years',
    '35-39': '_35To39Years',
    '44-40': '_40To44Years',
    '40-44': '_40To44Years',
    '49-45': '_45To49Years',
    '45-49': '_45To49Years',
    '54-50': '_50To54Years',
    '50-54': '_50To54Years',
    '59-55': '_55To59Years',
    '55-59': '_55To59Years',
    '64-60': '_60To64Years',
    '60-64': '_60To64Years',
    '69-65': '_65To69Years',
    '65-69': '_65To69Years',
    '74-70': '_70To74Years',
    '70-74': '_70To74Years',
    '79-75': '_75To79Years',
    '75-79': '_75To79Years',
    '84-80': '_80To84Years',
    '80-84': '_80To84Years',
    '+85': '_85OrMoreYears',
    '85+': '_85OrMoreYears',
}

MIFKAD_2008_MARITAL_COLS_1_14 = (
    (1, ''),
    (2, '_NeverMarried'),
    (3, '_MarriedAndNotSeparated'),
    (4, '_Divorced'),
    (5, '_Widowed'),
    (6, '_Separated'),
)

MIFKAD_2008_DIST_MAP = {
    'TOTAL': 'ISR',
    'Jerusalem District': 'DIST_1',
    'Northern District': 'DIST_2',
    'Haifa District': 'DIST_3',
    'Central District': 'DIST_4',
    'Tel Aviv District': 'DIST_5',
    'Southern District': 'DIST_6',
    'Judea and Samaria Area': 'DIST_7',
}

MIFKAD_2008_URBAN_RURAL_COLS = (
    (1, 'Grand totalTotal'),
    (2, 'Grand totalMales'),
    (3, 'Grand totalFemales'),
    (4, 'Urban localitiesTotal'),
    (5, 'Urban localitiesMales'),
    (6, 'Urban localitiesFemales'),
    (7, 'Rural localitiesTotal'),
    (8, 'Rural localitiesMales'),
    (9, 'Rural localitiesFemales'),
)

MIFKAD_2008_EMP_MARITAL_ROWS = {
    'TOTAL': '',
    'Never married': '_NeverMarried',
    'Married': '_MarriedAndNotSeparated',
    'Divorced': '_Divorced',
    'Widowed': '_Widowed',
}

MIFKAD_2008_EMP_AGE_COLS = (
    (1, ''),
    (2, '_15To24Years'),
    (3, '_25To29Years'),
    (4, '_30To34Years'),
    (5, '_35To39Years'),
    (6, '_40To44Years'),
    (7, '_45To49Years'),
    (8, '_50To54Years'),
    (9, '_55To59Years'),
    (10, '_60To64Years'),
    (11, '_65OrMoreYears'),
)

EXPECTED_INPUT_TABLE_FILENAMES = (
    'isr_age_maritalstatus_2008.csv',
    'isr_agebracket_gender_aa1_2008.csv',
    'isr_causeofdeath_religion_1950_2020.csv',
    'isr_livebirth_infantdeath_deaths_religion_1996_2021.csv',
    'isr_menemployed_age_martialstatus_2008.csv',
    'isr_population_religion_1949_2021.csv',
    'isr_subdistrict_age_gender_2008.csv',
    'isr_subdistrict_population_gender_2008.csv',
    'isr_totalemployed_age_martialstatus_2008.csv',
    'isr_urban_rural_gender_aa1_2008.csv',
    'isr_womenemployed_age_martialstatus_2008.csv',
)


def _parse_number(val: str | None) -> float | None:
    """Parses a numeric string (handling commas and whitespace) into float."""
    if val is None:
        return None
    cleaned = str(val).replace(',', '').strip()
    if not cleaned or cleaned in ('-', '..', '...', '*'):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _format_number(val: float) -> str:
    """Formats integer-valued floats without trailing .0 and rounds decimals."""
    rounded = round(val, 4)
    if math.isclose(rounded, round(rounded), abs_tol=1e-9):
        return str(int(round(rounded)))
    return f'{rounded:.4f}'.rstrip('0').rstrip('.')


def _read_mifkad_table_rows(fpath: str) -> list[list[str]]:
    """Reads rows from a raw CBS Mifkad table (.xls/.xlsx binary or .csv text)."""
    if not os.path.exists(fpath):
        raise FileNotFoundError(f'Missing Mifkad table file: {fpath}')
    with open(fpath, 'rb') as fp:
        head = fp.read(8)
    if head.startswith(b'\xd0\xcf\x11\xe0') or head.startswith(b'PK\x03\x04'):
        import pandas as pd  # pylint: disable=g-import-not-at-top

        engine = 'openpyxl' if head.startswith(b'PK\x03\x04') else 'xlrd'
        df = pd.read_excel(fpath, header=None, dtype=str,
                           engine=engine).fillna('')
        return [[str(c) for c in row] for row in df.values.tolist()]
    with open(fpath, 'r', encoding='utf-8-sig', errors='replace') as fp:
        return list(csv.reader(fp))


def _convert_dem1_2_xls_to_csv(xls_path: str, dest_path: str) -> None:
    """Converts dem1_2.xls (in hundreds) into isr_urban_rural_gender_aa1_2008.csv."""
    headers = ['Region', 'Year'
              ] + [col_name for _, col_name in MIFKAD_2008_URBAN_RURAL_COLS]
    rows_by_reg: dict[str, list[str]] = {}
    for row in _read_mifkad_table_rows(xls_path):
        if len(row) < 10:
            continue
        dist_label = row[-1].strip() or row[0].strip()
        reg = MIFKAD_2008_DIST_MAP.get(dist_label)
        if not reg:
            continue
        vals: list[str] = []
        for col_idx, col_name in MIFKAD_2008_URBAN_RURAL_COLS:
            if reg == 'ISR' and col_name == 'Grand totalTotal':
                vals.append('')
                continue
            val = _parse_number(row[col_idx])
            vals.append('' if val is None else _format_number(val))
        if any(vals):
            rows_by_reg[reg] = vals

    if not rows_by_reg:
        raise RuntimeError(f'No data rows extracted from {xls_path}')

    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    with open(dest_path, 'w', encoding='utf-8', newline='') as fp:
        writer = csv.writer(fp, lineterminator='\n')
        writer.writerow(headers)
        for reg in sorted(rows_by_reg):
            writer.writerow([reg, '2008'] + rows_by_reg[reg])


def _convert_dem1_14_xls_to_csv(xls_path: str, dest_path: str) -> None:
    """Converts dem1_14.xls (in hundreds) into isr_age_maritalstatus_2008.csv."""
    age_order = (
        ('', 'All ages'),
        ('_0To14Years', '0-14'),
        ('_15To24Years', '15-24'),
        ('_25To34Years', '25-34'),
        ('_35To39Years', '35-39'),
        ('_40To44Years', '40-44'),
        ('_45To49Years', '45-49'),
        ('_50To54Years', '50-54'),
        ('_55To59Years', '55-59'),
        ('_60To64Years', '60-64'),
        ('_65To69Years', '65-69'),
        ('_70To74Years', '70-74'),
        ('_75To79Years', '75-79'),
        ('_80To84Years', '80-84'),
        ('_85OrMoreYears', '85+'),
    )
    marital_cols = (
        ('', 'Total'),
        ('_NeverMarried', 'Never married'),
        ('_MarriedAndNotSeparated', 'Married'),
        ('_Divorced', 'Divorced'),
        ('_Widowed', 'Widowed'),
        ('_Separated', 'Married but separated'),
    )

    cell_map: dict[tuple[str, str], str] = {}
    for row in _read_mifkad_table_rows(xls_path):
        if len(row) < 7:
            continue
        age_label = row[0].strip() or (row[-1].strip() if row else '')
        age_suf = MIFKAD_2008_AGE_ROWS_1_14.get(age_label)
        if age_suf is None:
            continue
        for col_idx, marital_suf in MIFKAD_2008_MARITAL_COLS_1_14:
            if age_suf == '' and marital_suf == '':
                continue
            val = _parse_number(row[col_idx])
            if val is not None:
                cell_map[(age_suf, marital_suf)] = _format_number(val)

    if not cell_map:
        raise RuntimeError(f'No data rows extracted from {xls_path}')

    headers = ['Year', 'Region', 'Age group'] + [m[1] for m in marital_cols]
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    with open(dest_path, 'w', encoding='utf-8', newline='') as fp:
        writer = csv.writer(fp, lineterminator='\n')
        writer.writerow(headers)
        for age_suf, age_label in age_order:
            vals = [
                cell_map.get((age_suf, m_suf), '') for m_suf, _ in marital_cols
            ]
            if any(vals):
                writer.writerow(['2008', 'ISR', age_label] + vals)


def _convert_emp_xls_to_csv(
    xls_path: str,
    dest_path: str,
    gender_suf: str,
    is_female: bool,
) -> None:
    """Converts a Mifkad employment .xls table (in hundreds) into its 2D CSV."""
    marital_rows = (
        ('', 'סך הכל'),
        ('_NeverMarried', 'רווקה' if is_female else 'רווק'),
        ('_MarriedAndNotSeparated', 'נשואה' if is_female else 'נשוי'),
        ('_Divorced', 'גרושה' if is_female else 'גרוש'),
        ('_Widowed', 'אלמנה' if is_female else 'אלמן'),
    )
    age_cols = (
        ('', 'סך הכל'),
        ('_15To24Years', '24-15'),
        ('_25To29Years', '29-25'),
        ('_30To34Years', '34-30'),
        ('_35To39Years', '39-35'),
        ('_40To44Years', '44-40'),
        ('_45To49Years', '49-45'),
        ('_50To54Years', '54-50'),
        ('_55To59Years', '59-55'),
        ('_60To64Years', '64-60'),
        ('_65OrMoreYears', '+65'),
    )

    cell_map: dict[tuple[str, str], str] = {}
    widowed_15_39: str = ''
    for row in _read_mifkad_table_rows(xls_path):
        if len(row) < 12:
            continue
        marital_label = row[-1].strip() or row[0].strip()
        marital_suf = MIFKAD_2008_EMP_MARITAL_ROWS.get(marital_label)
        if marital_suf is None:
            continue
        for col_idx, age_suf in MIFKAD_2008_EMP_AGE_COLS:
            val = _parse_number(row[col_idx])
            if val is None:
                continue
            if (gender_suf == '' and marital_suf == '_Widowed' and
                    age_suf == '_35To39Years'):
                widowed_15_39 = _format_number(val)
            else:
                cell_map[(marital_suf, age_suf)] = _format_number(val)

    if not cell_map and not widowed_15_39:
        raise RuntimeError(f'No data rows extracted from {xls_path}')

    headers = ['Year', 'Region', 'code'] + [a[1] for a in age_cols]
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    with open(dest_path, 'w', encoding='utf-8', newline='') as fp:
        writer = csv.writer(fp, lineterminator='\n')
        writer.writerow(headers)
        for m_suf, m_label in marital_rows:
            vals = [cell_map.get((m_suf, a_suf), '') for a_suf, _ in age_cols]
            if gender_suf and m_suf == '' and vals and vals[0]:
                base_val = vals[0]
                vals[0] = ''
                row_vals = [''] * len(age_cols)
                row_vals[0] = base_val
                writer.writerow(['2008', 'ISR', 'מועסקים'] + row_vals)
            if any(vals):
                writer.writerow(['2008', 'ISR', m_label] + vals)
        if gender_suf == '' and widowed_15_39:
            vals = [''] * len(age_cols)
            vals[0] = widowed_15_39
            writer.writerow(['2008', 'ISR', 'אלמן_15_39'] + vals)


def build_input_tables(raw_dir: str, output_dir: str) -> list[str]:
    """Converts the 5 .xls files in raw_dir into CSVs and copies existing CSV files into output_dir."""
    if not os.path.isdir(raw_dir):
        raise FileNotFoundError(f'Input directory does not exist: {raw_dir}')
    os.makedirs(output_dir, exist_ok=True)

    # 1. Convert only the 5 Mifkad .xls tables into .csv tables in output_dir
    dem1_2_path = os.path.join(raw_dir, 'dem1_2.xls')
    if os.path.exists(dem1_2_path):
        _convert_dem1_2_xls_to_csv(
            dem1_2_path,
            os.path.join(output_dir, 'isr_urban_rural_gender_aa1_2008.csv'),
        )
    dem1_14_path = os.path.join(raw_dir, 'dem1_14.xls')
    if os.path.exists(dem1_14_path):
        _convert_dem1_14_xls_to_csv(
            dem1_14_path,
            os.path.join(output_dir, 'isr_age_maritalstatus_2008.csv'),
        )
    emp_tables = (
        ('lab4_14.xls', 'isr_menemployed_age_martialstatus_2008.csv', '_Male',
         False),
        ('lab4_14_1.xls', 'isr_totalemployed_age_martialstatus_2008.csv', '',
         False),
        ('lab4_14_2.xls', 'isr_womenemployed_age_martialstatus_2008.csv',
         '_Female', True),
    )
    for xls_name, csv_name, gender_suf, is_female in emp_tables:
        xls_path = os.path.join(raw_dir, xls_name)
        if os.path.exists(xls_path):
            _convert_emp_xls_to_csv(
                xls_path,
                os.path.join(output_dir, csv_name),
                gender_suf=gender_suf,
                is_female=is_female,
            )

    # 2. Copy all .csv files from raw_dir into output_dir without processing them
    for fname in sorted(os.listdir(raw_dir)):
        if not fname.endswith('.csv'):
            continue
        src_csv = os.path.join(raw_dir, fname)
        dst_csv = os.path.join(output_dir, fname)
        if os.path.isfile(src_csv) and os.path.abspath(
                src_csv) != os.path.abspath(dst_csv):
            shutil.copy2(src_csv, dst_csv)

    expected_set = set(EXPECTED_INPUT_TABLE_FILENAMES)
    for existing_name in os.listdir(output_dir):
        existing_path = os.path.join(output_dir, existing_name)
        if existing_name not in expected_set and os.path.isfile(existing_path):
            logging.info('Removing stale staged file: %s', existing_path)
            os.remove(existing_path)

    staged_paths = [
        os.path.join(output_dir, fname)
        for fname in EXPECTED_INPUT_TABLE_FILENAMES
        if os.path.exists(os.path.join(output_dir, fname))
    ]
    if not staged_paths:
        raise RuntimeError(f'No staged CSV files generated in {output_dir}')
    for staged_path in staged_paths:
        with open(staged_path, 'r', encoding='utf-8') as fp:
            row_count = sum(1 for _ in csv.reader(fp))
        if row_count < 2:
            raise RuntimeError(
                f'Staged CSV file contains no data rows: {staged_path}')
    return staged_paths


def main(argv: list[str] | None = None) -> None:
    logging.set_verbosity(logging.INFO)
    parser = argparse.ArgumentParser(
        description=
        'Converts .xls files in input_files/ to CSVs and copies .csv files into staged_inputs/.'
    )
    parser.add_argument(
        '--input_dir',
        default=os.path.join(_SCRIPT_DIR, 'input_files'),
        help='Directory containing raw downloaded CBS .xls and .csv files.',
    )
    parser.add_argument(
        '--output_dir',
        default=os.path.join(_SCRIPT_DIR, 'staged_inputs'),
        help='Directory where the 11 CSV tables will be staged.',
    )
    args = parser.parse_args(argv)
    build_input_tables(args.input_dir, args.output_dir)


if __name__ == '__main__':
    main()
