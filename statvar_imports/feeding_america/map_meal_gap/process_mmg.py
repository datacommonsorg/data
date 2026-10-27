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
"""Processes Feeding America Map the Meal Gap state, county, and district data.

Merges the preserved 2018-2019 FeedingAmerica_MMG.csv baseline with multi-year
Feeding America Map the Meal Gap partner Excel workbooks (.xlsx) and/or state,
county, and congressional district CSV exports to generate
output/FeedingAmerica_MMG.csv and output/FeedingAmerica_MMG.tmcf.
"""

import csv
import glob
import os
import re
import shutil
import tempfile
from typing import Any, Optional

from absl import app
from absl import flags
from absl import logging
import openpyxl

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

FLAGS = flags.FLAGS
flags.DEFINE_string(
    'input_dir',
    os.path.join(_SCRIPT_DIR, 'input_files'),
    'Directory containing preserved baseline CSV and partner workbooks/CSVs.',
)
flags.DEFINE_string(
    'output_dir',
    os.path.join(_SCRIPT_DIR, 'output'),
    'Directory where cleaned FeedingAmerica_MMG.csv and .tmcf are written.',
)
flags.DEFINE_string(
    'tmcf_path',
    os.path.join(_SCRIPT_DIR, 'FeedingAmerica_MMG.tmcf'),
    'Path to template MCF file.',
)

OUTPUT_COLUMNS = [
    'observationAbout',
    'observationDate',
    'Count_Person_FoodInsecure',
    'Count_Person_FoodInsecure_EligibleForAllFederalBenefits',
    'Count_Person_FoodInsecure_EligibleForSomeFederalBenefits',
    'Count_Person_FoodInsecure_IneligibleForFederalBenefits',
    'Count_Child_FoodInsecure',
    'Count_Child_FoodInsecure_EligibleForManyChildNutritionBenefits',
    'Count_Child_FoodInsecure_IneligibleForChildNutritionBenefits',
    'Mean_MealCost_Person_FoodSecure',
    'Annual_FoodBudgetShortfall',
]

STATVAR_COLUMNS = OUTPUT_COLUMNS[2:]

_MISSING_TOKENS = frozenset({'', 'n/a', 'na', 'null', 'none', '-', '*', '.'})


def _normalize_header(header: Any) -> str:
    """Normalizes a column header for resilient lookup across years/tabs."""
    if header is None:
        return ''
    text = str(header).strip().lower()
    text = text.replace('<=', '≤').replace('w/hh', 'w/ hh')
    text = re.sub(r'\s+', ' ', text)
    return text


def _parse_number(value: Any) -> Optional[float]:
    """Parses an integer or float from a raw cell value, or returns None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).strip()
    if cleaned.lower() in _MISSING_TOKENS:
        return None
    cleaned = cleaned.replace('$', '').replace(',', '').replace(' ', '')
    if cleaned.lower() in _MISSING_TOKENS:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_fraction(value: Any) -> Optional[float]:
    """Parses a percentage or decimal fraction in [0, 1] from a raw cell value.

    In partner .xlsx files, percentages are stored as decimals in [0, 1] (e.g.,
    0.5029876), whereas in exported CSVs they are formatted with '%' (e.g.,
    '50.3%'). Values > 1.0 without '%' are also treated as percentages and
    divided by 100.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        num = float(value)
        return num / 100.0 if num > 1.0 else num
    cleaned = str(value).strip()
    if cleaned.lower() in _MISSING_TOKENS:
        return None
    has_percent = cleaned.endswith('%')
    if has_percent:
        cleaned = cleaned[:-1].strip()
    num = _parse_number(cleaned)
    if num is None:
        return None
    if has_percent or num > 1.0:
        return num / 100.0
    return num


def format_fips_dcid(
    fips_value: Any,
    is_state: Optional[bool] = None,
    geo_type: Optional[str] = None,
) -> str:
    """Formats a state, county, or congressional district FIPS into a geoId."""
    if fips_value is None:
        return ''
    text = str(fips_value).strip()
    if text.startswith('geoId/'):
        return text
    num = _parse_number(text)
    if num is None:
        return ''
    fips_int = int(round(num))
    if fips_int <= 0:
        return ''
    if geo_type == 'cong_dist':
        if 100 <= fips_int <= 9999:
            return f'geoId/{fips_int:04d}'
        return ''
    if geo_type == 'state' or is_state is True or (
            geo_type is None and is_state is None and fips_int < 100):
        return f'geoId/{fips_int:02d}'
    if 1000 <= fips_int <= 99999:
        return f'geoId/{fips_int:05d}'
    return ''


def _format_int(value: Optional[float]) -> str:
    """Formats a numeric value as a rounded integer string."""
    if value is None:
        return ''
    return str(int(round(value)))


def _format_derived_count(total_count: Optional[float],
                          fraction: Optional[float]) -> str:
    """Computes and formats round(total_count * fraction, 2)."""
    if total_count is None or fraction is None:
        return ''
    return str(round(round(total_count) * fraction, 2))


def _format_meal_cost(value: Optional[float]) -> str:
    """Formats meal cost rounded to 2 decimal places without trailing .0."""
    if value is None:
        return ''
    rounded = round(value, 2)
    if rounded == int(rounded):
        return str(int(rounded))
    return str(rounded)


def parse_partner_row(
    norm_row: dict[str, Any],
    is_state: Optional[bool] = None,
    geo_type: Optional[str] = None,
) -> Optional[dict[str, str]]:
    """Transforms a normalized State, County, or Cong District row."""
    place_dcid = format_fips_dcid(
        norm_row.get('fips'), is_state=is_state, geo_type=geo_type)
    if not place_dcid:
        return None

    year_num = _parse_number(norm_row.get('year'))
    if year_num is None:
        return None
    year_str = str(int(round(year_num)))

    person_fi = _parse_number(norm_row.get('# of food insecure persons overall'))
    child_fi = _parse_number(norm_row.get('# of food insecure children'))
    meal_cost = _parse_number(norm_row.get('cost per meal'))
    shortfall = _parse_number(
        norm_row.get('weighted annual food budget shortfall'))

    frac_le_low = _parse_fraction(norm_row.get('% fi ≤ low threshold'))
    frac_btwn = _parse_fraction(norm_row.get('% fi btwn thresholds'))
    frac_gt_high = _parse_fraction(norm_row.get('% fi > high threshold'))
    frac_gt_low = _parse_fraction(norm_row.get('% fi > low threshold'))

    # When High Threshold == Low Threshold (states without broad-based
    # categorical eligibility) or when only Low Threshold is reported (e.g.
    # 2021), '% FI Btwn Thresholds' is blank/'n/a'; fall back to '% FI > Low
    # Threshold' when '% FI > High Threshold' is not populated.
    frac_ineligible = frac_gt_high if frac_gt_high is not None else frac_gt_low

    frac_child_le_185 = _parse_fraction(
        norm_row.get('% food insecure children in hh w/ hh incomes below 185 fpl'
                    ))
    frac_child_gt_185 = _parse_fraction(
        norm_row.get('% food insecure children in hh w/ hh incomes above 185 fpl'
                    ))

    out_row = {
        'observationAbout':
            place_dcid,
        'observationDate':
            year_str,
        'Count_Person_FoodInsecure':
            _format_int(person_fi),
        'Count_Person_FoodInsecure_EligibleForAllFederalBenefits':
            _format_derived_count(person_fi, frac_le_low),
        'Count_Person_FoodInsecure_EligibleForSomeFederalBenefits':
            _format_derived_count(person_fi, frac_btwn),
        'Count_Person_FoodInsecure_IneligibleForFederalBenefits':
            _format_derived_count(person_fi, frac_ineligible),
        'Count_Child_FoodInsecure':
            _format_int(child_fi),
        'Count_Child_FoodInsecure_EligibleForManyChildNutritionBenefits':
            _format_derived_count(child_fi, frac_child_le_185),
        'Count_Child_FoodInsecure_IneligibleForChildNutritionBenefits':
            _format_derived_count(child_fi, frac_child_gt_185),
        'Mean_MealCost_Person_FoodSecure':
            _format_meal_cost(meal_cost),
        'Annual_FoodBudgetShortfall':
            _format_int(shortfall),
    }

    if not any(out_row[col] != '' for col in STATVAR_COLUMNS):
        return None
    return out_row


def _merge_row(
    records: dict[tuple[str, str], dict[str, str]],
    new_row: dict[str, str],
) -> None:
    """Merges a wide output row into records keyed by (place, year)."""
    key = (new_row['observationAbout'], new_row['observationDate'])
    if key not in records:
        records[key] = dict(new_row)
        return
    existing = records[key]
    for col in STATVAR_COLUMNS:
        val = new_row.get(col, '')
        if val != '':
            existing[col] = val


def load_baseline_csv(
    csv_path: str,
    records: dict[tuple[str, str], dict[str, str]],
) -> int:
    """Loads a wide FeedingAmerica_MMG.csv baseline file into records."""
    count = 0
    with open(csv_path, mode='r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            place = (row.get('observationAbout') or row.get('dcid') or
                     '').strip()
            year = (row.get('observationDate') or '').strip()
            if not place or not year:
                continue
            normalized = {
                'observationAbout': place,
                'observationDate': year,
            }
            for col in STATVAR_COLUMNS:
                normalized[col] = (row.get(col) or '').strip()
            _merge_row(records, normalized)
            count += 1
    logging.info('Loaded %d baseline rows from %s', count, csv_path)
    return count


def load_partner_csv(
    csv_path: str,
    records: dict[tuple[str, str], dict[str, str]],
    is_state: Optional[bool] = None,
    geo_type: Optional[str] = None,
) -> int:
    """Loads a partner State, County, or Cong Dist CSV export into records."""
    count = 0
    with open(csv_path, mode='r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for raw_row in reader:
            norm_row = {_normalize_header(k): v for k, v in raw_row.items()}
            parsed = parse_partner_row(
                norm_row, is_state=is_state, geo_type=geo_type)
            if parsed is not None:
                _merge_row(records, parsed)
                count += 1
    logging.info('Loaded %d partner CSV rows from %s', count, csv_path)
    return count


def load_partner_excel(
    xlsx_path: str,
    records: dict[tuple[str, str], dict[str, str]],
) -> int:
    """Loads State, County, and Cong District sheets from a .xlsx workbook."""
    count = 0
    sheet_geo_types = (
        ('State', True, 'state'),
        ('County', False, 'county'),
        ('Cong District', False, 'cong_dist'),
    )
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    try:
        for sheet_name, is_state, geo_type in sheet_geo_types:
            if sheet_name not in wb.sheetnames:
                continue
            ws = wb[sheet_name]
            rows_iter = ws.iter_rows(values_only=True)
            try:
                raw_headers = next(rows_iter)
            except StopIteration:
                continue
            headers = [_normalize_header(h) for h in raw_headers]
            sheet_count = 0
            for raw_values in rows_iter:
                norm_row = dict(zip(headers, raw_values))
                parsed = parse_partner_row(
                    norm_row, is_state=is_state, geo_type=geo_type)
                if parsed is not None:
                    _merge_row(records, parsed)
                    sheet_count += 1
            logging.info(
                'Loaded %d rows from sheet %s in %s',
                sheet_count,
                sheet_name,
                xlsx_path,
            )
            count += sheet_count
    finally:
        wb.close()
    return count


def process_data(input_dir: str, output_dir: str, tmcf_path: str) -> str:
    """Processes all baseline and partner files in input_dir into output_dir."""
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f'Input directory does not exist: {input_dir}')
    if not os.path.isfile(tmcf_path):
        raise FileNotFoundError(f'Template MCF file does not exist: {tmcf_path}')

    records: dict[tuple[str, str], dict[str, str]] = {}

    # 1. Load preserved baseline CSV(s) first (2018-2019 FeedingAmerica_MMG.csv).
    baseline_candidates = [
        os.path.join(input_dir, 'table', 'FeedingAmerica_MMG.csv'),
        os.path.join(input_dir, 'FeedingAmerica_MMG.csv'),
    ]
    baseline_candidates.extend(
        sorted(glob.glob(os.path.join(input_dir, '*baseline*.csv'))))
    seen_files = set()
    for path in baseline_candidates:
        abs_path = os.path.abspath(path)
        if os.path.isfile(abs_path) and abs_path not in seen_files:
            seen_files.add(abs_path)
            load_baseline_csv(abs_path, records)

    # 2. Load partner State, County, and Cong District CSV exports (if present).
    csv_files = sorted(glob.glob(os.path.join(input_dir, '*.csv')))
    for csv_path in csv_files:
        abs_path = os.path.abspath(csv_path)
        if abs_path in seen_files:
            continue
        lower_name = os.path.basename(abs_path).lower()
        if 'cong_dist' in lower_name or 'congdistrict' in lower_name:
            seen_files.add(abs_path)
            load_partner_csv(
                abs_path, records, is_state=False, geo_type='cong_dist')
        elif 'state' in lower_name:
            seen_files.add(abs_path)
            load_partner_csv(
                abs_path, records, is_state=True, geo_type='state')
        elif 'county' in lower_name:
            seen_files.add(abs_path)
            load_partner_csv(
                abs_path, records, is_state=False, geo_type='county')

    # 3. Load partner Excel workbooks (.xlsx) sorted by name so newer releases
    # take precedence and provide full floating-point threshold precision.
    xlsx_files = sorted(glob.glob(os.path.join(input_dir, '*.xlsx')))
    for xlsx_path in xlsx_files:
        abs_path = os.path.abspath(xlsx_path)
        if os.path.basename(abs_path).startswith('~$'):
            continue
        seen_files.add(abs_path)
        load_partner_excel(abs_path, records)

    if not records:
        raise RuntimeError(
            f'No valid Feeding America records processed from {input_dir}')

    os.makedirs(output_dir, exist_ok=True)
    output_csv_path = os.path.join(output_dir, 'FeedingAmerica_MMG.csv')
    output_tmcf_path = os.path.join(output_dir, 'FeedingAmerica_MMG.tmcf')

    # Sort deterministically: states first (len 8 e.g. geoId/01), then
    # congressional districts (len 10 e.g. geoId/0101), then counties
    # (len 11 e.g. geoId/01001), by observationDate descending then DCID.
    sorted_keys = sorted(
        records.keys(),
        key=lambda k: (len(k[0]), -int(k[1]), k[0]),
    )

    tmp_fd, tmp_csv_path = tempfile.mkstemp(
        prefix='FeedingAmerica_MMG_', suffix='.csv', dir=output_dir)
    try:
        with os.fdopen(tmp_fd, mode='w', encoding='utf-8', newline='') as out_f:
            writer = csv.DictWriter(out_f, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            for key in sorted_keys:
                writer.writerow(records[key])
        os.replace(tmp_csv_path, output_csv_path)
    except Exception:
        if os.path.exists(tmp_csv_path):
            os.remove(tmp_csv_path)
        raise

    if os.path.abspath(tmcf_path) != os.path.abspath(output_tmcf_path):
        tmp_tmcf_fd, tmp_tmcf_path = tempfile.mkstemp(
            prefix='FeedingAmerica_MMG_', suffix='.tmcf', dir=output_dir)
        os.close(tmp_tmcf_fd)
        try:
            shutil.copyfile(tmcf_path, tmp_tmcf_path)
            os.replace(tmp_tmcf_path, output_tmcf_path)
        except Exception:
            if os.path.exists(tmp_tmcf_path):
                os.remove(tmp_tmcf_path)
            raise

    logging.info(
        'Wrote %d place-year rows to %s', len(sorted_keys), output_csv_path
    )
    return output_csv_path


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        logging.warning('Ignoring unexpected command-line arguments: %s',
                        argv[1:])
    try:
        process_data(
            input_dir=FLAGS.input_dir,
            output_dir=FLAGS.output_dir,
            tmcf_path=FLAGS.tmcf_path,
        )
    except Exception as exc:  # pylint: disable=broad-except
        logging.fatal('Failed to process FeedingAmerica_MapMealGap: %s', exc)


if __name__ == '__main__':
    app.run(main)
