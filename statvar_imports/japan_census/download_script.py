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
"""Download script for Japan Census and socio-economic datasets from e-Stat Dashboard API.

Downloads raw dataset files as-is from the official e-Stat Dashboard API into input_files/
without any preprocessing or business logic derivations.
"""

import concurrent.futures
import csv
import os
import sys
import tempfile
import threading
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

from absl import app
from absl import flags
from absl import logging

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
    'jpn_employment.csv': {
        'indicators': [
            '0301010000010010010',  # Employed persons (Both sexes)
            '0301010000020010010',  # Unemployed persons (Both sexes)
            '0301010000030010010',  # Not in labour force (Both sexes)
        ],
        'regional_ranks': ['2'],
        'batch_size':
        3,
    },
    'jpn_unemploymentrate.csv': {
        'indicators': [
            '0301010000020020010',  # Unemployment rate (Both sexes)
        ],
        'regional_ranks': ['2'],
        'batch_size': 1,
    },
    'jpn_student.csv': {
        'indicators': [
            '1201050300000010000',  # Elementary school students
            '1201050400000010000',  # Lower secondary school students
            '1201050500000010000',  # Upper secondary school students
            '1201050800000010000',  # University students and graduate school students
        ],
        'regional_ranks': ['2'],
        'batch_size':
        4,
    },
    'jpn_aa1_teacher.csv': {
        'indicators': [
            '1201040100000010000',  # Teachers of kindergartens
            '1201040300000010000',  # Teachers of elementary schools
            '1201040500000010000',  # Teachers of senior high schools
        ],
        'regional_ranks': ['2', '3'],
        'batch_size':
        3,
    },
    'jpn_aa1_health.csv': {
        'indicators': [
            '1505130000000010030',  # Deaths by causes (diabetes mellitus)
            '1505130000000010050',  # Deaths by causes (heart diseases excl. hypertensive)
            '1505130000000010070',  # Deaths by causes (suicide)
        ],
        'regional_ranks': ['2', '3'],
        'batch_size':
        3,
    },
    'jpn_aa1_death.csv': {
        'indicators': [
            '0203020000000010000',  # Deaths (Both sexes)
            '0203020100000010000',  # Deaths (Male)
            '0203020200000010000',  # Deaths (Female)
        ],
        'regional_ranks': ['2', '3'],
        'batch_size':
        3,
    },
    'jpn_gender_age_total_population.csv': {
        'indicators': _build_population_5yr_indicators(),
        'regional_ranks': ['2'],
        'batch_size': 5,
    },
    'jpn_aa1_gender_age_total_population.csv': {
        'indicators': _build_population_5yr_indicators(),
        'regional_ranks': ['3'],
        'batch_size': 5,
    },
    'jpn_aa1_aa2_age_gender.csv': {
        'indicators': _build_population_5yr_indicators(),
        'regional_ranks': ['4'],
        'batch_size': 3,
    },
}


def _extract_class_lookup(class_objs: list[dict[str, Any]] | dict[str, Any],
                          target_id: str) -> dict[str, str]:
    """Extracts a code-to-name dictionary from e-Stat CLASS_INF.CLASS_OBJ."""
    if isinstance(class_objs, dict):
        class_objs = [class_objs]
    for obj in class_objs:
        if obj.get('@id') == target_id:
            classes = obj.get('CLASS', [])
            if isinstance(classes, dict):
                classes = [classes]
            return {
                str(c.get('@code', '')):
                str(c.get('@name') if '@name' in c else c.get('$', ''))
                for c in classes if isinstance(c, dict)
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
        raise RuntimeError(
            'Invalid JSON response from e-Stat API: missing GET_STATS.')

    get_stats = data['GET_STATS']
    result = get_stats.get('RESULT', {})
    status_code = str(result.get('status', ''))
    error_msg = str(result.get('errorMsg', ''))

    if status_code != '0':
        raise RuntimeError(
            f'e-Stat API error (status={status_code}): {error_msg}')

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
        year_str = time_map.get(time_cd,
                                time_cd[:4] if len(time_cd) >= 4 else time_cd)

        parsed_records.append({
            'year':
            year_str,
            'indicatorCd':
            ind_cd,
            'regionCd':
            reg_cd,
            'value':
            str(val_obj.get('$', '')),
            'indicatorName':
            indicator_map.get(ind_cd, ''),
            'unitCd':
            unit_cd,
            'unitName':
            unit_map.get(unit_cd, ''),
            'statCd':
            str(val_obj.get('@stat', '')),
            'regionName':
            region_map.get(reg_cd, ''),
            'timeCd':
            time_cd,
            'cycle':
            str(val_obj.get('@cycle', '')),
            'regionRank':
            str(val_obj.get('@regionRank', '')),
            'isSeasonal':
            str(val_obj.get('@isSeasonal', '')),
            'isProvisional':
            str(val_obj.get('@isProvisional', '')),
        })

    if not parsed_records:
        raise RuntimeError('e-Stat API returned 0 data records.')

    return parsed_records


_THREAD_LOCAL = threading.local()


def _get_http_session() -> requests.Session:
    """Returns a thread-local requests.Session configured with automatic retries."""
    session = getattr(_THREAD_LOCAL, 'session', None)
    if session is None:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            connect=3,
            read=3,
            status=3,
            backoff_factor=2.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(['GET']),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        _THREAD_LOCAL.session = session
    return session


def _request_estat_json(url: str,
                        params: dict[str, str],
                        timeout: int = 60) -> dict[str, Any]:
    """Performs a thread-safe GET request to the e-Stat JSON API with retries."""
    session = _get_http_session()
    resp = session.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


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
    response_json = _request_estat_json(
        url=ESTAT_JSON_API_URL,
        params=params,
        timeout=60,
    )
    if not response_json or not isinstance(response_json, dict):
        raise RuntimeError(
            f'Invalid or empty JSON response from {ESTAT_JSON_API_URL} for params={params}'
        )
    return parse_estat_json_response(response_json)


def _write_csv_atomically(output_filepath: str, rows: list[dict[str,
                                                                str]]) -> None:
    """Writes rows atomically to output_filepath and verifies non-empty output."""
    output_dir = os.path.dirname(output_filepath)
    os.makedirs(output_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix='.tmp_jpn_',
                                    suffix='.csv',
                                    dir=output_dir)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f,
                                    fieldnames=CSV_HEADER,
                                    lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
        if not (os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0):
            raise RuntimeError(
                f'Atomic write failed: {tmp_path} is empty or missing.')
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
    max_workers: int = 1,
) -> int:
    """Downloads all batches for a dataset and writes as-is atomically to output_filepath."""
    tasks: list[tuple[list[str], str]] = []
    for rank in regional_ranks:
        for i in range(0, len(indicators), batch_size):
            tasks.append((indicators[i:i + batch_size], rank))

    all_records: list[dict[str, str]] = []
    if max_workers > 1 and len(tasks) > 1:
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers) as executor:
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
                ))

    if not all_records:
        raise RuntimeError(
            f'No records retrieved for dataset {os.path.basename(output_filepath)}'
        )

    _write_csv_atomically(output_filepath, all_records)
    logging.info('Saved %d rows to %s', len(all_records), output_filepath)
    return len(all_records)


def _cleanup_stale_csvs(output_dir: str) -> None:
    """Removes any stale CSV files in output_dir not produced by DATASET_CONFIGS."""
    expected_files = set(DATASET_CONFIGS.keys())
    for entry in os.listdir(output_dir):
        if not entry.endswith('.csv'):
            continue
        if entry not in expected_files:
            stale_path = os.path.join(output_dir, entry)
            if os.path.isfile(stale_path):
                logging.info('Removing stale CSV file: %s', stale_path)
                os.remove(stale_path)


def download_all(
    output_dir: str,
    max_workers: int = 8,
) -> None:
    """Downloads all configured Japan Census datasets as-is into output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    _cleanup_stale_csvs(output_dir)
    total_rows = 0
    for filename, cfg in DATASET_CONFIGS.items():
        output_filepath = os.path.join(output_dir, filename)
        logging.info('Downloading dataset: %s', filename)
        count = download_dataset(
            output_filepath=output_filepath,
            indicators=cfg['indicators'],
            regional_ranks=cfg['regional_ranks'],
            batch_size=cfg['batch_size'],
            max_workers=max_workers,
        )
        total_rows += count
    _cleanup_stale_csvs(output_dir)
    logging.info(
        'Successfully downloaded all %d datasets (%d total rows) to %s',
        len(DATASET_CONFIGS),
        total_rows,
        output_dir,
    )


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')
    output_dir = (_FLAGS.output_dir if os.path.isabs(_FLAGS.output_dir) else
                  os.path.join(_MODULE_DIR, _FLAGS.output_dir))
    try:
        download_all(
            output_dir,
            max_workers=_FLAGS.max_workers,
        )
    except Exception as e:
        logging.fatal('%s', e, exc_info=True)


if __name__ == '__main__':
    app.run(main)
