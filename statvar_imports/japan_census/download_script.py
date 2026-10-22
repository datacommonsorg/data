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
"""Download script for Japan Census and socio-economic datasets from e-Stat Dashboard API."""

import concurrent.futures
import csv
import os
import sys
import tempfile
from typing import Any

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.join(_MODULE_DIR, '../../util/'))

from absl import app
from absl import flags
from absl import logging
import download_util
import file_util

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'output_dir',
    os.path.join(_MODULE_DIR, 'input_files'),
    'Directory path to save the downloaded CSV files.',
)
flags.DEFINE_integer(
    'max_workers',
    8,
    'Maximum number of parallel threads for e-Stat API requests.',
)
flags.DEFINE_string(
    'historical_gcs_path',
    'gs://unresolved_mcf/country/japan/deleted_historical_data.csv',
    'GCS path to the deleted historical data CSV file.',
)

ESTAT_JSON_API_URL = 'https://dashboard.e-stat.go.jp/api/1.0/Json/getData'

# 5-year age bracket suffixes: 010 (0-4 years) through 200 (95-99 years)
_AGE_5YR_SUFFIXES = [f'{i:03d}' for i in range(10, 210, 10)]

# Leading 3 columns (year, indicatorCd, regionCd) are mapped_columns=3 for stat_var_processor.
CSV_HEADER = [
    'year',
    'indicatorCd',
    'regionCd',
    'value',
    'indicatorName',
    'unitCd',
    'unitName',
    'statCd',
    'regionName',
    'timeCd',
    'cycle',
    'regionRank',
    'isSeasonal',
    'isProvisional',
]


def _build_population_5yr_indicators(
    gender_digits: tuple[str, ...] = ('0', '1', '2'),
    include_totals: bool = True,
) -> list[str]:
    """Builds e-Stat indicator codes for population totals and 5-year age brackets."""
    indicators: list[str] = []
    if include_totals:
        for g in gender_digits:
            indicators.append(f'0201010{g}00000010000')
    for g in gender_digits:
        for suffix in _AGE_5YR_SUFFIXES:
            indicators.append(f'0201010{g}20000010{suffix}')
        indicators.append(f'0201010{g}30000011000')
    return indicators


# Dataset configurations mapping output CSV filename to query parameters.
# RegionalRank: '2' = Country (Japan), '3' = Prefecture, '4' = Municipality.
# Cycle: '3' = Calendar Year.
DATASET_CONFIGS: dict[str, dict[str, Any]] = {
    'jpn_employement.csv': {
        'indicators': [
            '0301010000010010010',  # Employed persons (Both sexes)
            '0301010000020010010',  # Unemployed persons (Both sexes)
            '0301010000030010010',  # Not in labour force (Both sexes)
        ],
        'regional_ranks': ['2'],
        'batch_size': 3,
        'is_census': False,
    },
    'jpn_unemploymentrate.csv': {
        'indicators': [
            '0301010000020020010',  # Unemployment rate (Both sexes)
        ],
        'regional_ranks': ['2'],
        'batch_size': 1,
        'is_census': False,
    },
    'jpn_student.csv': {
        'indicators': [
            '1201050300000010000',  # Elementary school students
            '1201050400000010000',  # Lower secondary school students
            '1201050500000010000',  # Upper secondary school students
            '1201050800000010000',  # University students and graduate school students
        ],
        'regional_ranks': ['2'],
        'batch_size': 4,
        'is_census': False,
    },
    'jpn_aa1_teacher.csv': {
        'indicators': [
            '1201040100000010000',  # Teachers of kindergartens
            '1201040300000010000',  # Teachers of elementary schools
            '1201040500000010000',  # Teachers of senior high schools (mapped to Count_Teacher_UniversityAndCollegeTeacher)
        ],
        'regional_ranks': ['2', '3'],
        'batch_size': 3,
        'is_census': False,
    },
    'jpn_aa1_health.csv': {
        'indicators': [
            '1505130000000010030',  # Deaths by causes (diabetes mellitus)
            '1505130000000010050',  # Deaths by causes (heart diseases excl. hypertensive)
            '1505130000000010070',  # Deaths by causes (suicide)
        ],
        'regional_ranks': ['2', '3'],
        'batch_size': 3,
        'is_census': False,
    },
    'jpn_aa1_death.csv': {
        'indicators': [
            '0203020000000010000',  # Deaths (Both sexes)
            '0203020100000010000',  # Deaths (Male)
            '0203020200000010000',  # Deaths (Female)
        ],
        'regional_ranks': ['2', '3'],
        'batch_size': 3,
        'is_census': False,
    },
    'jpn_gender_age_total_population.csv': {
        'indicators': _build_population_5yr_indicators(),
        'regional_ranks': ['2'],
        'batch_size': 5,
        'is_census': True,
        'census_mode': 'national',
    },
    'jpn_aa1_gender_age_total_population.csv': {
        'indicators': _build_population_5yr_indicators(),
        'regional_ranks': ['3'],
        'batch_size': 5,
        'is_census': True,
        'census_mode': 'prefecture',
    },
    'jpn_aa1_aa2_age_gender.csv': {
        'indicators': _build_population_5yr_indicators(),
        'regional_ranks': ['4'],
        'batch_size': 3,
        'is_census': True,
        'census_mode': 'municipality',
    },
}


def _extract_class_lookup(
    class_objs: list[dict[str, Any]] | dict[str, Any], target_id: str
) -> dict[str, str]:
    """Extracts a code-to-name dictionary from e-Stat CLASS_INF.CLASS_OBJ."""
    if isinstance(class_objs, dict):
        class_objs = [class_objs]
    for obj in class_objs:
        if obj.get('@id') == target_id:
            classes = obj.get('CLASS', [])
            if isinstance(classes, dict):
                classes = [classes]
            return {
                str(c.get('@code', '')): str(
                    c.get('@name') if '@name' in c else c.get('$', '')
                )
                for c in classes
                if isinstance(c, dict)
            }
    return {}


def parse_estat_json_response(data: dict[str, Any]) -> list[dict[str, str]]:
    """Parses an e-Stat Dashboard API JSON response and extracts data rows with metadata.

    Args:
        data: Parsed JSON dictionary returned by the e-Stat Dashboard API.

    Returns:
        List of row dictionaries keyed by CSV_HEADER fields.

    Raises:
        RuntimeError: If the API returned an error status code or invalid payload.
    """
    if not isinstance(data, dict) or 'GET_STATS' not in data:
        raise RuntimeError('Invalid JSON response from e-Stat API: missing GET_STATS.')

    get_stats = data['GET_STATS']
    result = get_stats.get('RESULT', {})
    status_code = str(result.get('status', ''))
    error_msg = str(result.get('errorMsg', ''))

    if status_code not in ('0', '100'):
        raise RuntimeError(
            f'e-Stat API error (status={status_code}): {error_msg}'
        )

    if status_code == '100':
        return []

    stat_data = get_stats.get('STATISTICAL_DATA', {})
    class_objs = stat_data.get('CLASS_INF', {}).get('CLASS_OBJ', [])

    indicator_map = _extract_class_lookup(class_objs, 'indicator')
    unit_map = _extract_class_lookup(class_objs, 'unit')
    region_map = _extract_class_lookup(class_objs, 'regionCode')
    time_map = _extract_class_lookup(class_objs, 'time')

    data_objs = stat_data.get('DATA_INF', {}).get('DATA_OBJ', [])
    if isinstance(data_objs, dict):
        data_objs = [data_objs]

    parsed_records: list[dict[str, str]] = []
    for obj in data_objs:
        val_obj = obj.get('VALUE', {})
        if not isinstance(val_obj, dict):
            continue
        ind_cd = str(val_obj.get('@indicator', ''))
        unit_cd = str(val_obj.get('@unit', ''))
        reg_cd = str(val_obj.get('@regionCode', ''))
        time_cd = str(val_obj.get('@time', ''))
        year_str = time_map.get(
            time_cd, time_cd[:4] if len(time_cd) >= 4 else time_cd
        )

        parsed_records.append({
            'year': year_str,
            'indicatorCd': ind_cd,
            'regionCd': reg_cd,
            'value': str(val_obj.get('$', '')),
            'indicatorName': indicator_map.get(ind_cd, ''),
            'unitCd': unit_cd,
            'unitName': unit_map.get(unit_cd, ''),
            'statCd': str(val_obj.get('@stat', '')),
            'regionName': region_map.get(reg_cd, ''),
            'timeCd': time_cd,
            'cycle': str(val_obj.get('@cycle', '')),
            'regionRank': str(val_obj.get('@regionRank', '')),
            'isSeasonal': str(val_obj.get('@isSeasonal', '')),
            'isProvisional': str(val_obj.get('@isProvisional', '')),
        })

    return parsed_records


def fetch_indicator_batch(
    indicators: list[str],
    regional_rank: str,
    cycle: str = '3',
    is_seasonal: str = '1',
    time_from: str = '',
    time_to: str = '',
) -> list[dict[str, str]]:
    """Fetches a batch of indicators for a given regional rank from the e-Stat JSON API."""
    params: dict[str, str] = {
        'Lang': 'EN',
        'IndicatorCode': ','.join(indicators),
        'RegionalRank': regional_rank,
        'Cycle': cycle,
        'IsSeasonalAdjustment': is_seasonal,
        'MetaGetFlg': 'Y',
        'SectionHeaderFlg': '1',
    }
    if time_from:
        params['TimeFrom'] = time_from
    if time_to:
        params['TimeTo'] = time_to

    logging.info(
        'Requesting e-Stat JSON API: RegionalRank=%s, Indicators=%d (%s...)',
        regional_rank,
        len(indicators),
        indicators[0],
    )
    response_json = download_util.request_url(
        url=ESTAT_JSON_API_URL,
        params=params,
        method='GET',
        output='json',
        timeout=60,
        retries=3,
        retry_secs=5,
    )
    if not response_json or not isinstance(response_json, dict):
        raise RuntimeError(
            f'Invalid or empty JSON response from {ESTAT_JSON_API_URL} for params={params}'
        )
    return parse_estat_json_response(response_json)


def _derive_census_population_rows(
    records: list[dict[str, str]], mode: str
) -> list[dict[str, str]]:
    """Filters to 5-year census years and computes exact unrounded broad age sums.

    At National (RegionalRank=2) and Prefecture (RegionalRank=3) levels, direct
    broad-age indicators (0201010*100000100*) report rounded annual Population
    Estimates (in thousands), whereas summing the 5-year Census age brackets
    (0201010*20000010* + 0201010*30000011000) yields the exact unrounded Population
    Census counts for <15, 15-64, 65+, and 85+.
    """
    census_records = [
        r for r in records if r['year'].isdigit() and int(r['year']) % 5 == 0
    ]

    by_reg_yr_ind: dict[tuple[str, str, str], dict[str, str]] = {}
    reg_meta: dict[tuple[str, str], dict[str, str]] = {}
    for r in census_records:
        key = (r['regionCd'], r['year'], r['indicatorCd'])
        by_reg_yr_ind[key] = r
        reg_meta[(r['regionCd'], r['year'])] = r

    output_rows: list[dict[str, str]] = []
    # Keep total population (Both sexes, Male, Female) and 5-year brackets:
    # National keeps 010..230 (0-4 through 110+); Prefecture keeps 010..170 (0-4 through 80-84);
    # Municipality keeps only the 3 totals + 9 broad age sums (<15, 15-64, 65+ for Both/Male/Female = 12 StatVars).
    if mode == 'municipality':
        allowed_5yr: set[str] = set()
    else:
        max_5yr_suffix = 230 if mode == 'national' else 170
        allowed_5yr = {
            f'0201010{g}20000010{i:03d}'
            for g in ('0', '1', '2')
            for i in range(10, max_5yr_suffix + 10, 10)
        }
    allowed_totals = {
        '0201010000000010000',
        '0201010100000010000',
        '0201010200000010000',
    }

    for r in census_records:
        ind = r['indicatorCd']
        if ind in allowed_totals or ind in allowed_5yr:
            output_rows.append(r)

    # Derive exact Census counts for <15, 15-64, 65+, and (for National/Prefecture) 85+ from 5-year brackets.
    broad_Specs = [
        ('10000010010', 'Population (under 15)', [f'{i:03d}' for i in (10, 20, 30)], False),
        ('10000010020', 'Population (15-64)', [f'{i:03d}' for i in range(40, 140, 10)], False),
        ('10000010030', 'Population (65 and over)', [f'{i:03d}' for i in range(140, 210, 10)], True),
    ]
    if mode != 'municipality':
        broad_Specs.append(
            ('40000010070', 'Population (85 and over)', [f'{i:03d}' for i in (180, 190, 200)], True)
        )

    for reg_cd, yr in sorted(reg_meta.keys()):
        base = reg_meta[(reg_cd, yr)]
        for g in ('0', '1', '2'):
            for target_tail, desc, suffixes, include_100plus in broad_Specs:
                part_codes = [f'0201010{g}20000010{s}' for s in suffixes]
                if include_100plus:
                    part_codes.append(f'0201010{g}30000011000')
                vals: list[int] = []
                valid = True
                for c in part_codes:
                    rec = by_reg_yr_ind.get((reg_cd, yr, c))
                    if not rec or not rec['value'].lstrip('-').isdigit():
                        valid = False
                        break
                    vals.append(int(rec['value']))
                if valid:
                    new_row = dict(base)
                    new_row['indicatorCd'] = f'0201010{g}{target_tail}'
                    new_row['indicatorName'] = desc
                    new_row['value'] = str(sum(vals))
                    output_rows.append(new_row)

    return output_rows


_HISTORICAL_CACHE: dict[str, list[dict[str, str]]] = {}


def _load_historical_rows(historical_gcs_path: str) -> list[dict[str, str]]:
    """Loads and caches historical rows from GCS or local CSV."""
    if not historical_gcs_path:
        return []
    if historical_gcs_path in _HISTORICAL_CACHE:
        return _HISTORICAL_CACHE[historical_gcs_path]
    try:
        logging.info(
            'Reading historical deleted data from GCS: %s', historical_gcs_path
        )
        with file_util.FileIO(historical_gcs_path, 'r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        _HISTORICAL_CACHE[historical_gcs_path] = rows
        return rows
    except Exception as e:
        logging.warning(
            'Could not read historical deleted data from %s: %s. Proceeding with fresh data only.',
            historical_gcs_path,
            e,
        )
        _HISTORICAL_CACHE[historical_gcs_path] = []
        return []


def _apply_historical_supplement(
    dataset_filename: str,
    records: list[dict[str, str]],
    historical_gcs_path: str = '',
) -> list[dict[str, str]]:
    """Merges pre-1975 historical Census and exact archival rows from GCS CSV."""
    hist_rows = _load_historical_rows(historical_gcs_path)
    if not hist_rows:
        return records

    by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for r in records:
        by_key[(r['regionCd'], r['year'], r['indicatorCd'])] = r

    added_or_updated = 0
    for s in hist_rows:
        if s['dataset'] != dataset_filename:
            continue
        key = (s['regionCd'], s['year'], s['indicatorCd'])
        if key in by_key:
            by_key[key]['value'] = s['value']
        else:
            by_key[key] = {
                'year': s['year'],
                'indicatorCd': s['indicatorCd'],
                'regionCd': s['regionCd'],
                'value': s['value'],
                'indicatorName': '',
                'unitCd': '',
                'unitName': '',
                'statCd': '',
                'regionName': '',
                'timeCd': f"{s['year']}CY00",
                'cycle': '3',
                'regionRank': '2' if s['regionCd'] == '00000' else '3',
                'isSeasonal': '1',
                'isProvisional': '0',
            }
        added_or_updated += 1

    if added_or_updated:
        logging.info(
            'Applied %d historical supplement rows to %s',
            added_or_updated,
            dataset_filename,
        )
    return list(by_key.values())


def _write_csv_atomically(output_filepath: str, rows: list[dict[str, str]]) -> None:
    """Writes rows atomically to output_filepath and verifies non-empty output."""
    output_dir = os.path.dirname(output_filepath)
    os.makedirs(output_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix='.tmp_jpn_', suffix='.csv', dir=output_dir
    )
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER, lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
        if not (os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0):
            raise RuntimeError(
                f'Atomic write failed: {tmp_path} is empty or missing.'
            )
        os.replace(tmp_path, output_filepath)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def download_dataset(
    output_filepath: str,
    indicators: list[str],
    regional_ranks: list[str],
    batch_size: int,
    is_census: bool = False,
    census_mode: str = '',
    max_workers: int = 1,
    historical_gcs_path: str = '',
) -> int:
    """Downloads all batches for a dataset and writes atomically to output_filepath."""
    tasks: list[tuple[list[str], str]] = []
    for rank in regional_ranks:
        for i in range(0, len(indicators), batch_size):
            tasks.append((indicators[i : i + batch_size], rank))

    all_records: list[dict[str, str]] = []
    if max_workers > 1 and len(tasks) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(fetch_indicator_batch, batch, rank)
                for batch, rank in tasks
            ]
            for fut in futures:
                all_records.extend(fut.result())
    else:
        for batch, rank in tasks:
            all_records.extend(
                fetch_indicator_batch(
                    indicators=batch,
                    regional_rank=rank,
                )
            )

    if is_census:
        all_records = _derive_census_population_rows(all_records, census_mode)

    all_records = _apply_historical_supplement(
        os.path.basename(output_filepath),
        all_records,
        historical_gcs_path=historical_gcs_path,
    )

    if not all_records:
        raise RuntimeError(
            f'No records retrieved for dataset {os.path.basename(output_filepath)}'
        )

    if census_mode == 'municipality':
        # Split municipality census by year (matching CNS jpn_aa1_aa2_age_gender_{year}.csv)
        # so multi-core processing can run across all census years in parallel.
        output_dir = os.path.dirname(output_filepath)
        by_year: dict[str, list[dict[str, str]]] = {}
        for r in all_records:
            by_year.setdefault(r['year'], []).append(r)
        # Remove any old unsplit jpn_aa1_aa2_age_gender.csv if present
        if os.path.exists(output_filepath):
            os.remove(output_filepath)
        for yr, yr_rows in sorted(by_year.items()):
            yr_filepath = os.path.join(output_dir, f'jpn_aa1_aa2_age_gender_{yr}.csv')
            _write_csv_atomically(yr_filepath, yr_rows)
            logging.info('Saved %d rows to %s', len(yr_rows), yr_filepath)
        return len(all_records)

    _write_csv_atomically(output_filepath, all_records)
    logging.info(
        'Saved %d rows to %s', len(all_records), output_filepath
    )
    return len(all_records)


def download_all(
    output_dir: str,
    max_workers: int = 8,
    historical_gcs_path: str = '',
) -> None:
    """Downloads all configured Japan Census datasets into output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    total_rows = 0
    for filename, cfg in DATASET_CONFIGS.items():
        output_filepath = os.path.join(output_dir, filename)
        logging.info('Downloading dataset: %s', filename)
        count = download_dataset(
            output_filepath=output_filepath,
            indicators=cfg['indicators'],
            regional_ranks=cfg['regional_ranks'],
            batch_size=cfg['batch_size'],
            is_census=cfg.get('is_census', False),
            census_mode=cfg.get('census_mode', ''),
            max_workers=max_workers,
            historical_gcs_path=historical_gcs_path,
        )
        total_rows += count
    logging.info(
        'Successfully downloaded all %d datasets (%d total rows) to %s',
        len(DATASET_CONFIGS),
        total_rows,
        output_dir,
    )


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')
    output_dir = (
        _FLAGS.output_dir
        if os.path.isabs(_FLAGS.output_dir)
        else os.path.join(_MODULE_DIR, _FLAGS.output_dir)
    )
    try:
        download_all(
            output_dir,
            max_workers=_FLAGS.max_workers,
            historical_gcs_path=_FLAGS.historical_gcs_path,
        )
    except Exception as e:
        logging.fatal('%s', e, exc_info=True)


if __name__ == '__main__':
    app.run(main)
