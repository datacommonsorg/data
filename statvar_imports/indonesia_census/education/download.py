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
"""Downloads Indonesia Education (Literacy Rate & Schools/Teachers/Students) data from BPS WebAPI."""

import csv
import html
import json
import os
import re
import time
from typing import Any

from absl import app
from absl import flags
from absl import logging
import requests

_CODEDIR = os.path.dirname(os.path.abspath(__file__))

_FLAGS = flags.FLAGS
if 'output_dir' not in _FLAGS:
    flags.DEFINE_string(
        'output_dir',
        os.path.join(_CODEDIR, 'input_files'),
        'Directory path to save the downloaded input CSV file.',
    )
if 'output_filename' not in _FLAGS:
    flags.DEFINE_string(
        'output_filename',
        'indonesia_education_input.csv',
        'Filename for the combined Indonesia Education CSV table.',
    )
if 'domain' not in _FLAGS:
    flags.DEFINE_string(
        'domain',
        '0000',
        'BPS domain code (0000 for national/all-province tables).',
    )
if 'literacy_province_var_id' not in _FLAGS:
    flags.DEFINE_integer(
        'literacy_province_var_id',
        1458,
        'BPS variable ID for Literacy Rate of Population Aged 15+ by Province.',
    )
if 'literacy_sex_var_id' not in _FLAGS:
    flags.DEFINE_integer(
        'literacy_sex_var_id',
        1460,
        'BPS variable ID for Literacy Rate of Population Aged 15+ by Sex.',
    )
if 'api_key' not in _FLAGS:
    flags.DEFINE_string(
        'api_key',
        os.environ.get('BPS_API_KEY', ''),
        'BPS WebAPI key (loaded from GCS config.json if not set).',
    )
if 'request_delay_sec' not in _FLAGS:
    flags.DEFINE_float(
        'request_delay_sec',
        0.5,
        'Delay in seconds between SIMDASI API requests to respect BPS rate limits.',
    )

BPS_API_BASE_URL = 'https://webapi.bps.go.id/v1/api'
MAX_YEARS_PER_REQUEST = 3

# BPS SIMDASI table IDs for the 9 School, Teacher, and Student tables
SIMDASI_TABLES: tuple[tuple[str, str], ...] = (
    ('MTs', 'Uys0Mk9kelpxamVmMUYrMkRHSFcyZz09'),
    ('MA', 'UE1YYmk0TnR5TnoycHlYbzNnbkFIZz09'),
    ('MI', 'TE9sZFVvdVErcU9Ka0VreVUrNnZEQT09'),
    ('RA', 'SmNxWnFzemcvcUkvdndUbTJGc2RQdz09'),
    ('SD', 'UkJNaEl6ZHRVYXNaMzZhZG9BbS9ZZz09'),
    ('SMA', 'a1lFcnlHNXNYMFlueG8xL0ZOZnU0Zz09'),
    ('SMP', 'dzdoVmp3YWdGNU0yWEgraVIwbmRqZz09'),
    ('SMK', 'MU90V01YZ0RxenhmbFdsU21iUHh2Zz09'),
    ('Univ', 'cmdTdG5vU0IwKzBFR20rQnpuZEYzdz09'),
)

ORDERED_VALUE_COLUMNS: tuple[str, ...] = (
    'Literacy Rate (Total)',
    'Literacy Rate (Male)',
    'Literacy Rate (Female)',
    'Jumlah Sekolah MTs (Negeri)',
    'Jumlah Sekolah MTs (Swasta)',
    'Jumlah Sekolah MTs (Negeri+Swasta)',
    'Jumlah Guru MTs (Negeri)',
    'Jumlah Guru MTs (Swasta)',
    'Jumlah Guru MTs (Negeri+Swasta)',
    'Jumlah Murid MTs (Negeri)',
    'Jumlah Murid MTs (Swasta)',
    'Jumlah Murid MTs (Negeri+Swasta)',
    'Jumlah Sekolah MA (Negeri)',
    'Jumlah Sekolah MA (Swasta)',
    'Jumlah Sekolah MA (Negeri+Swasta)',
    'Jumlah Guru MA (Negeri)',
    'Jumlah Guru MA (Swasta)',
    'Jumlah Guru MA (Negeri+Swasta)',
    'Jumlah Murid MA (Negeri)',
    'Jumlah Murid MA (Swasta)',
    'Jumlah Murid MA (Negeri+Swasta)',
    'Jumlah Sekolah MI (Negeri)',
    'Jumlah Sekolah MI (Swasta)',
    'Jumlah Sekolah MI (Negeri+Swasta)',
    'Jumlah Guru MI (Negeri)',
    'Jumlah Guru MI (Swasta)',
    'Jumlah Guru MI (Negeri+Swasta)',
    'Jumlah Murid MI (Negeri)',
    'Jumlah Murid MI (Swasta)',
    'Jumlah Murid MI (Negeri+Swasta)',
    'Jumlah Sekolah Raudatul Athfal',
    'Jumlah Guru Raudatul Athfal',
    'Jumlah Murid Raudatul Athfal',
    'Jumlah Sekolah SD (Negeri)',
    'Jumlah Sekolah SD (Swasta)',
    'Jumlah Sekolah SD (Negeri+Swasta)',
    'Jumlah Guru SD (Negeri)',
    'Jumlah Guru SD (Swasta)',
    'Jumlah Guru SD (Negeri+Swasta)',
    'Jumlah Murid SD (Negeri)',
    'Jumlah Murid SD (Swasta)',
    'Jumlah Murid SD (Negeri+Swasta)',
    'Jumlah Sekolah SMA (Negeri)',
    'Jumlah Sekolah SMA (Swasta)',
    'Jumlah Sekolah SMA (Negeri+Swasta)',
    'Jumlah Guru SMA (Negeri)',
    'Jumlah Guru SMA (Swasta)',
    'Jumlah Guru SMA (Negeri+Swasta)',
    'Jumlah Murid SMA (Negeri)',
    'Jumlah Murid SMA (Swasta)',
    'Jumlah Murid SMA (Negeri+Swasta)',
    'Jumlah Sekolah SMP (Negeri)',
    'Jumlah Sekolah SMP (Swasta)',
    'Jumlah Sekolah SMP (Negeri+Swasta)',
    'Jumlah Guru SMP (Negeri)',
    'Jumlah Guru SMP (Swasta)',
    'Jumlah Guru SMP (Negeri+Swasta)',
    'Jumlah Murid SMP (Negeri)',
    'Jumlah Murid SMP (Swasta)',
    'Jumlah Murid SMP (Negeri+Swasta)',
    'Jumlah Sekolah SMK (Negeri)',
    'Jumlah Sekolah SMK (Swasta)',
    'Jumlah Sekolah SMK (Negeri+Swasta)',
    'Jumlah Guru SMK (Negeri)',
    'Jumlah Guru SMK (Swasta)',
    'Jumlah Guru SMK (Negeri+Swasta)',
    'Jumlah Murid SMK (Negeri)',
    'Jumlah Murid SMK (Swasta)',
    'Jumlah Murid SMK (Negeri+Swasta)',
    'Jumlah Perguruan Tinggi di Bawah Kementerian Riset, Teknologi dan Pendidikan Tinggi - Negeri',
    'Jumlah Perguruan Tinggi di Bawah Kementerian Riset, Teknologi dan Pendidikan Tinggi - Swasta',
    'Jumlah Perguruan Tinggi di Bawah Kementerian Riset, Teknologi dan Pendidikan Tinggi - Negeri + Swasta',
    'Jumlah Tenaga Pendidik di Bawah Kementerian Riset, Teknologi dan Pendidikan Tinggi - Negeri',
    'Jumlah Tenaga Pendidik di Bawah Kementerian Riset, Teknologi dan Pendidikan Tinggi - Swasta',
    'Jumlah Tenaga Pendidik di Bawah Kementerian Riset, Teknologi dan Pendidikan Tinggi - Negeri + Swasta',
    'Jumlah Mahasiswa di Bawah Kementerian Riset, Teknologi dan Pendidikan Tinggi - Negeri',
    'Jumlah Mahasiswa di Bawah Kementerian Riset, Teknologi dan Pendidikan Tinggi - Swasta',
    'Jumlah Mahasiswa di Bawah Kementerian Riset, Teknologi dan Pendidikan Tinggi - Negeri + Swasta',
)


def redact_api_key(text: Any) -> str:
    """Redacts any embedded /key/<api_key>/ segment from URLs or error messages."""
    return re.sub(r'/key/[^/\s]+/?', '/key/REDACTED/', str(text))


def request_bps_json(
    url: str,
    timeout: int = 30,
    retries: int = 3,
    retry_secs: int = 5,
) -> Any:
    """Fetches JSON from BPS WebAPI while redacting the API key from logs."""
    redacted_url = redact_api_key(url)
    logging.info('Downloading URL: %s', redacted_url)
    last_error: Exception | None = None
    for attempt in range(max(1, retries)):
        try:
            response = requests.get(url, timeout=timeout)
            if response.ok:
                return response.json()
            last_error = RuntimeError(
                f'HTTP {response.status_code} from {redacted_url}')
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
        if attempt + 1 < max(1, retries):
            time.sleep(retry_secs)
    raise RuntimeError(
        f'Failed to download {redacted_url}: {redact_api_key(last_error)}')


def normalize_place_label(raw_label: str) -> str:
    """Normalizes Indonesian province/country names to uppercase canonical labels."""
    cleaned = re.sub(r'<[^>]+>', '', html.unescape(str(raw_label or
                                                       ''))).strip().upper()
    aliases = {
        'KEP. BANGKA BELITUNG': 'KEPULAUAN BANGKA BELITUNG',
        'KEP. RIAU': 'KEPULAUAN RIAU',
        'DAERAH ISTIMEWA YOGYAKARTA': 'DI YOGYAKARTA',
    }
    return aliases.get(cleaned, cleaned)


def clean_simdasi_integer(raw_val: Any) -> str:
    """Cleans Indonesian dot-separated integer strings (e.g., '4.478' -> '4478')."""
    if raw_val is None:
        return ''
    s = str(raw_val).strip()
    if s in ('', '-', '–', '...', 'NA', 'N/A', '~0'):
        return ''
    s_nodot = s.replace('.', '').replace(',', '.').strip()
    try:
        fval = float(s_nodot)
        if fval.is_integer():
            return str(int(fval))
        return str(fval)
    except ValueError:
        return ''


def fetch_available_years(
    domain: str,
    var_id: int,
    api_key: str,
) -> list[dict[str, Any]]:
    """Fetches all available year definitions (th_id, th) for a BPS dynamic table."""
    years: list[dict[str, Any]] = []
    page = 1
    while True:
        url = (f'{BPS_API_BASE_URL}/list/model/th/lang/eng/domain/{domain}'
               f'/var/{var_id}/page/{page}/key/{api_key}/')
        resp = request_bps_json(url)
        if not isinstance(resp, dict) or resp.get('status') != 'OK':
            raise RuntimeError(
                f'Failed to fetch available years from BPS WebAPI (var={var_id}, page={page}): '
                f'{redact_api_key(resp)}')
        data = resp.get('data')
        if not isinstance(data, list) or len(data) < 2:
            raise RuntimeError(
                f'Malformed pagination data from BPS WebAPI (var={var_id}, page={page}): '
                f'{redact_api_key(resp)}')
        meta, items = data[0], data[1]
        if not isinstance(items, list) or not items:
            raise RuntimeError(
                f'Empty year items list from BPS WebAPI (var={var_id}, page={page}): '
                f'{redact_api_key(resp)}')
        years.extend(items)
        total_pages = int(meta.get('pages', 1)) if isinstance(meta, dict) else 1
        if page >= total_pages:
            break
        page += 1

    years.sort(key=lambda item: int(item['th_id']))
    return years


def fetch_literacy_by_province(
    domain: str,
    var_id: int,
    api_key: str,
    table_data: dict[tuple[str, str], dict[str, str]],
) -> None:
    """Downloads Literacy Rate of Population Aged 15+ by Province (var_id=1458)."""
    years = fetch_available_years(domain=domain, var_id=var_id, api_key=api_key)
    for idx in range(0, len(years), MAX_YEARS_PER_REQUEST):
        chunk = years[idx:idx + MAX_YEARS_PER_REQUEST]
        th_param = ';'.join(str(y['th_id']) for y in chunk)
        url = (f'{BPS_API_BASE_URL}/list/model/data/lang/eng/domain/{domain}'
               f'/var/{var_id}/th/{th_param}/key/{api_key}/')
        resp = request_bps_json(url)
        if not isinstance(resp, dict) or resp.get('status') != 'OK':
            raise RuntimeError(
                f'Failed to fetch BPS literacy province data for th={th_param}: '
                f'{redact_api_key(resp)}')

        var_list = resp.get('var') or []
        turvar_list = resp.get('turvar') or []
        turtahun_list = resp.get('turtahun') or []
        vervar_list = resp.get('vervar') or []
        tahun_list = resp.get('tahun') or []
        datacontent = resp.get('datacontent') or {}
        if not (var_list and turvar_list and turtahun_list and vervar_list and
                tahun_list and datacontent):
            raise RuntimeError(
                f'Incomplete metadata or datacontent in BPS literacy province response for th={th_param}.'
            )

        vid = var_list[0]['val']
        tv_val = turvar_list[0]['val']
        tt_val = turtahun_list[0]['val']
        for vv in vervar_list:
            place = normalize_place_label(vv.get('label', ''))
            if not place:
                continue
            for ty in tahun_list:
                year_str = str(ty.get('label', '')).strip()
                cell_key = f"{vv['val']}{vid}{tv_val}{ty['val']}{tt_val}"
                raw_val = datacontent.get(cell_key)
                if raw_val is not None and str(raw_val).strip() != '':
                    val_str = (str(int(raw_val))
                               if isinstance(raw_val, float) and
                               raw_val.is_integer() else str(raw_val).strip())
                    table_data.setdefault((place, year_str),
                                          {})['Literacy Rate (Total)'] = val_str


def fetch_literacy_by_sex(
    domain: str,
    var_id: int,
    api_key: str,
    table_data: dict[tuple[str, str], dict[str, str]],
) -> None:
    """Downloads National Literacy Rate of Population Aged 15+ by Sex (var_id=1460)."""
    years = fetch_available_years(domain=domain, var_id=var_id, api_key=api_key)
    sex_col_map = {
        'Male': 'Literacy Rate (Male)',
        'Female': 'Literacy Rate (Female)',
        'Male + Female': 'Literacy Rate (Total)',
    }
    for idx in range(0, len(years), MAX_YEARS_PER_REQUEST):
        chunk = years[idx:idx + MAX_YEARS_PER_REQUEST]
        th_param = ';'.join(str(y['th_id']) for y in chunk)
        url = (f'{BPS_API_BASE_URL}/list/model/data/lang/eng/domain/{domain}'
               f'/var/{var_id}/th/{th_param}/key/{api_key}/')
        resp = request_bps_json(url)
        if not isinstance(resp, dict) or resp.get('status') != 'OK':
            raise RuntimeError(
                f'Failed to fetch BPS literacy sex data for th={th_param}: '
                f'{redact_api_key(resp)}')

        var_list = resp.get('var') or []
        turvar_list = resp.get('turvar') or []
        turtahun_list = resp.get('turtahun') or []
        vervar_list = resp.get('vervar') or []
        tahun_list = resp.get('tahun') or []
        datacontent = resp.get('datacontent') or {}
        if not (var_list and turvar_list and turtahun_list and vervar_list and
                tahun_list and datacontent):
            raise RuntimeError(
                f'Incomplete metadata or datacontent in BPS literacy sex response for th={th_param}.'
            )

        vid = var_list[0]['val']
        tv_val = turvar_list[0]['val']
        tt_val = turtahun_list[0]['val']
        for vv in vervar_list:
            col_name = sex_col_map.get(str(vv.get('label', '')).strip())
            if not col_name:
                continue
            for ty in tahun_list:
                year_str = str(ty.get('label', '')).strip()
                cell_key = f"{vv['val']}{vid}{tv_val}{ty['val']}{tt_val}"
                raw_val = datacontent.get(cell_key)
                if raw_val is not None and str(raw_val).strip() != '':
                    val_str = (str(int(raw_val))
                               if isinstance(raw_val, float) and
                               raw_val.is_integer() else str(raw_val).strip())
                    cell_map = table_data.setdefault(('INDONESIA', year_str),
                                                     {})
                    if (col_name == 'Literacy Rate (Total)' and
                            col_name in cell_map):
                        continue
                    cell_map[col_name] = val_str


def _parse_simdasi_payload(
    payload: dict[str, Any],
    year_str: str,
    table_data: dict[tuple[str, str], dict[str, str]],
) -> list[int]:
    """Extracts rows from a single BPS SIMDASI table response and returns available years."""
    data = payload.get('data') or []
    if not isinstance(data, list) or len(data) < 2 or not isinstance(
            data[1], dict):
        return []
    table_obj = data[1]
    available_years = [int(y) for y in (table_obj.get('list_tahun_data') or [])]
    kolom = table_obj.get('kolom')
    rows = table_obj.get('data')
    if not isinstance(kolom, dict) or not isinstance(rows, list):
        return sorted(available_years)
    for row in rows:
        if not isinstance(row, dict):
            continue
        place = normalize_place_label(
            row.get('label_raw') or row.get('label') or '')
        if not place:
            continue
        variables = row.get('variables')
        if not isinstance(variables, dict):
            continue
        for col_id, col_meta in kolom.items():
            if not isinstance(col_meta, dict):
                continue
            col_name = str(col_meta.get('nama_variabel', '')).strip()
            if not col_name or col_id not in variables:
                continue
            cell = variables.get(col_id)
            if not isinstance(cell, dict):
                continue
            val_str = clean_simdasi_integer(
                cell.get('value_raw') if cell.
                get('value_raw') is not None else cell.get('value'))
            if val_str:
                table_data.setdefault((place, year_str), {})[col_name] = val_str
    return sorted(available_years)


def fetch_simdasi_school_tables(
    api_key: str,
    table_data: dict[tuple[str, str], dict[str, str]],
    tables: tuple[tuple[str, str], ...] = SIMDASI_TABLES,
    delay_sec: float = 0.0,
) -> None:
    """Downloads available academic years across the 9 BPS SIMDASI school tables."""
    seed_year = 2022
    for code, table_id in tables:
        seed_url = (
            f'{BPS_API_BASE_URL}/interoperabilitas/datasource/simdasi/id/25/'
            f'tahun/{seed_year}/id_tabel/{table_id}/wilayah/0000000/key/{api_key}/'
        )
        seed_resp = request_bps_json(seed_url)
        if not isinstance(seed_resp, dict) or seed_resp.get('status') != 'OK':
            raise RuntimeError(
                f'Failed to fetch SIMDASI table {code} (id={table_id}) seed year {seed_year}: '
                f'{redact_api_key(seed_resp)}')
        years = _parse_simdasi_payload(seed_resp, str(seed_year), table_data)
        if not years:
            raise RuntimeError(
                f'No available years returned for SIMDASI table {code} (id={table_id}).'
            )
        for yr in years:
            if yr == seed_year:
                continue
            if delay_sec > 0:
                time.sleep(delay_sec)
            yr_url = (
                f'{BPS_API_BASE_URL}/interoperabilitas/datasource/simdasi/id/25/'
                f'tahun/{yr}/id_tabel/{table_id}/wilayah/0000000/key/{api_key}/'
            )
            yr_resp = request_bps_json(yr_url)
            if not isinstance(yr_resp, dict) or yr_resp.get('status') != 'OK':
                raise RuntimeError(
                    f'Failed to fetch SIMDASI table {code} (id={table_id}) year {yr}: '
                    f'{redact_api_key(yr_resp)}')
            _parse_simdasi_payload(yr_resp, str(yr), table_data)


def write_education_csv(
    output_path: str,
    table_data: dict[tuple[str, str], dict[str, str]],
    value_columns: tuple[str, ...] = ORDERED_VALUE_COLUMNS,
) -> None:
    """Writes the combined Indonesia Education CSV compatible with stat_var_processor.py."""
    with open(output_path, 'w', newline='', encoding='utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(['Provinsi', 'observationDate'] + list(value_columns))
        for (place, year_str), col_values in sorted(table_data.items()):
            row = [place, year_str]
            for col in value_columns:
                row.append(col_values.get(col, ''))
            writer.writerow(row)
    logging.info(
        'Wrote %d (place, year) rows across %d columns to %s',
        len(table_data),
        len(value_columns),
        output_path,
    )


def get_bps_api_key(flag_key: str = '') -> str:
    """Retrieves the BPS API key from flag, env var, or GCS config.json."""
    key = flag_key or os.environ.get('BPS_API_KEY', '')
    if key:
        return key
    local_gcs_cfg = '/tmp/gcs/statvar_imports/indonesia_census/config.json'
    if os.path.exists(local_gcs_cfg):
        try:
            with open(local_gcs_cfg, mode='r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('bps_api_key'):
                    return data['bps_api_key']
        except (OSError, json.JSONDecodeError) as e:
            logging.warning('Could not read local BPS config %s: %s',
                            local_gcs_cfg, e)
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket('unresolved_mcf')
        blob = bucket.blob('country/indonesia/config.json')
        data = json.loads(blob.download_as_text())
        if data.get('bps_api_key'):
            return data['bps_api_key']
    except Exception as e:
        logging.warning('Could not read BPS API key from GCS: %s', e)
    raise ValueError(
        'BPS API key not provided via --api_key, BPS_API_KEY, or GCS config.json.'
    )


def main(_) -> None:
    logging.set_verbosity(logging.INFO)
    api_key = get_bps_api_key(_FLAGS.api_key)
    table_data: dict[tuple[str, str], dict[str, str]] = {}
    fetch_literacy_by_province(
        domain=_FLAGS.domain,
        var_id=_FLAGS.literacy_province_var_id,
        api_key=api_key,
        table_data=table_data,
    )
    fetch_literacy_by_sex(
        domain=_FLAGS.domain,
        var_id=_FLAGS.literacy_sex_var_id,
        api_key=api_key,
        table_data=table_data,
    )
    fetch_simdasi_school_tables(
        api_key=api_key,
        table_data=table_data,
        delay_sec=_FLAGS.request_delay_sec,
    )
    os.makedirs(_FLAGS.output_dir, exist_ok=True)
    output_path = os.path.join(_FLAGS.output_dir, _FLAGS.output_filename)
    write_education_csv(
        output_path=output_path,
        table_data=table_data,
    )


if __name__ == '__main__':
    app.run(main)
