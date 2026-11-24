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

from collections import defaultdict
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

BPS_API_BASE_URL = 'https://webapi.bps.go.id/v1/api'
MAX_YEARS_PER_REQUEST = 3
MIN_YEARBOOK_EDITION = 2019

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

# BPS Statistik Indonesia (2019+) tables 4.1.2-4.1.9 layout:
# (table_number, table_code, per-page 3-column groups [each repeated for 2 academic years])
YEARBOOK_TABLE_SPECS: tuple[tuple[str, str, tuple[tuple[str, str, str], ...]],
                            ...] = (
                                ('4.1.2', 'RA', ((
                                    'Jumlah Sekolah Raudatul Athfal',
                                    'Jumlah Guru Raudatul Athfal',
                                    'Jumlah Murid Raudatul Athfal',
                                ),)),
                                ('4.1.3', 'SD', (
                                    (
                                        'Jumlah Sekolah SD (Negeri)',
                                        'Jumlah Sekolah SD (Swasta)',
                                        'Jumlah Sekolah SD (Negeri+Swasta)',
                                    ),
                                    (
                                        'Jumlah Guru SD (Negeri)',
                                        'Jumlah Guru SD (Swasta)',
                                        'Jumlah Guru SD (Negeri+Swasta)',
                                    ),
                                    (
                                        'Jumlah Murid SD (Negeri)',
                                        'Jumlah Murid SD (Swasta)',
                                        'Jumlah Murid SD (Negeri+Swasta)',
                                    ),
                                )),
                                ('4.1.4', 'MI', (
                                    (
                                        'Jumlah Sekolah MI (Negeri)',
                                        'Jumlah Sekolah MI (Swasta)',
                                        'Jumlah Sekolah MI (Negeri+Swasta)',
                                    ),
                                    (
                                        'Jumlah Guru MI (Negeri)',
                                        'Jumlah Guru MI (Swasta)',
                                        'Jumlah Guru MI (Negeri+Swasta)',
                                    ),
                                    (
                                        'Jumlah Murid MI (Negeri)',
                                        'Jumlah Murid MI (Swasta)',
                                        'Jumlah Murid MI (Negeri+Swasta)',
                                    ),
                                )),
                                ('4.1.5', 'SMP', (
                                    (
                                        'Jumlah Sekolah SMP (Negeri)',
                                        'Jumlah Sekolah SMP (Swasta)',
                                        'Jumlah Sekolah SMP (Negeri+Swasta)',
                                    ),
                                    (
                                        'Jumlah Guru SMP (Negeri)',
                                        'Jumlah Guru SMP (Swasta)',
                                        'Jumlah Guru SMP (Negeri+Swasta)',
                                    ),
                                    (
                                        'Jumlah Murid SMP (Negeri)',
                                        'Jumlah Murid SMP (Swasta)',
                                        'Jumlah Murid SMP (Negeri+Swasta)',
                                    ),
                                )),
                                ('4.1.6', 'MTs', (
                                    (
                                        'Jumlah Sekolah MTs (Negeri)',
                                        'Jumlah Sekolah MTs (Swasta)',
                                        'Jumlah Sekolah MTs (Negeri+Swasta)',
                                    ),
                                    (
                                        'Jumlah Guru MTs (Negeri)',
                                        'Jumlah Guru MTs (Swasta)',
                                        'Jumlah Guru MTs (Negeri+Swasta)',
                                    ),
                                    (
                                        'Jumlah Murid MTs (Negeri)',
                                        'Jumlah Murid MTs (Swasta)',
                                        'Jumlah Murid MTs (Negeri+Swasta)',
                                    ),
                                )),
                                ('4.1.7', 'SMA', (
                                    (
                                        'Jumlah Sekolah SMA (Negeri)',
                                        'Jumlah Sekolah SMA (Swasta)',
                                        'Jumlah Sekolah SMA (Negeri+Swasta)',
                                    ),
                                    (
                                        'Jumlah Guru SMA (Negeri)',
                                        'Jumlah Guru SMA (Swasta)',
                                        'Jumlah Guru SMA (Negeri+Swasta)',
                                    ),
                                    (
                                        'Jumlah Murid SMA (Negeri)',
                                        'Jumlah Murid SMA (Swasta)',
                                        'Jumlah Murid SMA (Negeri+Swasta)',
                                    ),
                                )),
                                ('4.1.8', 'SMK', (
                                    (
                                        'Jumlah Sekolah SMK (Negeri)',
                                        'Jumlah Sekolah SMK (Swasta)',
                                        'Jumlah Sekolah SMK (Negeri+Swasta)',
                                    ),
                                    (
                                        'Jumlah Guru SMK (Negeri)',
                                        'Jumlah Guru SMK (Swasta)',
                                        'Jumlah Guru SMK (Negeri+Swasta)',
                                    ),
                                    (
                                        'Jumlah Murid SMK (Negeri)',
                                        'Jumlah Murid SMK (Swasta)',
                                        'Jumlah Murid SMK (Negeri+Swasta)',
                                    ),
                                )),
                                ('4.1.9', 'MA', (
                                    (
                                        'Jumlah Sekolah MA (Negeri)',
                                        'Jumlah Sekolah MA (Swasta)',
                                        'Jumlah Sekolah MA (Negeri+Swasta)',
                                    ),
                                    (
                                        'Jumlah Guru MA (Negeri)',
                                        'Jumlah Guru MA (Swasta)',
                                        'Jumlah Guru MA (Negeri+Swasta)',
                                    ),
                                    (
                                        'Jumlah Murid MA (Negeri)',
                                        'Jumlah Murid MA (Swasta)',
                                        'Jumlah Murid MA (Negeri+Swasta)',
                                    ),
                                )),
                            )

TABLE_CODE_TO_COLUMNS: dict[str, tuple[str, ...]] = {
    code: tuple(col for grp in groups for col in grp)
    for _, code, groups in YEARBOOK_TABLE_SPECS
}
TABLE_CODE_TO_COLUMNS['Univ'] = (
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


def request_bps_bytes(
    url: str,
    timeout: int = 90,
    retries: int = 3,
    retry_secs: int = 5,
) -> bytes:
    """Downloads binary content (e.g. BPS yearbook PDF) with retries."""
    redacted_url = redact_api_key(url)
    logging.info('Downloading binary URL: %s', redacted_url)
    last_error: Exception | None = None
    for attempt in range(max(1, retries)):
        try:
            response = requests.get(url, timeout=timeout)
            if response.ok and response.content:
                return response.content
            last_error = RuntimeError(
                f'HTTP {response.status_code} from {redacted_url}')
        except requests.RequestException as exc:
            last_error = exc
        if attempt + 1 < max(1, retries):
            time.sleep(retry_secs)
    raise RuntimeError(
        f'Failed to download {redacted_url}: {redact_api_key(last_error)}')


def _load_valid_places(places_csv: str | None = None) -> set[str]:
    """Loads normalized valid Indonesian province/country names."""
    csv_path = places_csv or os.path.join(
        _CODEDIR, 'indonesia_education_places_resolved.csv')
    valid: set[str] = set()
    if os.path.exists(csv_path):
        with open(csv_path, mode='r', encoding='utf-8') as fp:
            for row in csv.DictReader(fp):
                place = normalize_place_label(row.get('place_name', ''))
                if place:
                    valid.add(place)
    return valid


def _count_table_year_values(
    table_data: dict[tuple[str, str], dict[str, str]],
    year_str: str,
    columns: set[str],
) -> int:
    """Counts populated cell values for a given year and column set."""
    if not columns:
        return 0
    count = 0
    for (_, yr), col_map in table_data.items():
        if yr == year_str:
            count += sum(1 for col in columns if col_map.get(col))
    return count


def fetch_simdasi_school_tables(
    api_key: str,
    table_data: dict[tuple[str, str], dict[str, str]],
    tables: tuple[tuple[str, str], ...] = SIMDASI_TABLES,
    delay_sec: float = 0.0,
) -> dict[str, set[str]]:
    """Downloads available academic years across the 9 BPS SIMDASI school tables.

    Returns a mapping of table_code -> set of year strings for which SIMDASI
    returned no populated values (e.g. when BPS returns `"variables": []`).
    """
    seed_year = 2022
    missing_by_code: dict[str, set[str]] = {}
    for code, table_id in tables:
        code_cols = set(TABLE_CODE_TO_COLUMNS.get(code, ()))
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
        if _count_table_year_values(table_data, str(seed_year), code_cols) == 0:
            missing_by_code.setdefault(code, set()).add(str(seed_year))
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
            if _count_table_year_values(table_data, str(yr), code_cols) == 0:
                missing_by_code.setdefault(code, set()).add(str(yr))
    return missing_by_code


def _is_yearbook_num_cell(text: str) -> bool:
    """Returns True if a PDF span text looks like a numeric cell or missing marker."""
    if text in ('-', '–', '—', '...', 'NA', 'N/A', '~0'):
        return True
    return bool(re.fullmatch(r'[\d.\s]+(?:,\d+)?', text))


def _cluster_spans_into_rows(
    spans: list[tuple[float, float, float, float, str]],
    y_tol: float = 3.0,
) -> list[list[tuple[float, float, float, float, str]]]:
    """Groups PDF text spans into horizontal rows by y-coordinate."""
    rows: list[list[tuple[float, float, float, float, str]]] = []
    for sp in sorted(spans, key=lambda item: (item[1], item[0])):
        if rows and abs(sp[1] - rows[-1][0][1]) <= y_tol:
            rows[-1].append(sp)
        else:
            rows.append([sp])
    for row in rows:
        row.sort(key=lambda item: item[0])
    return rows


def parse_yearbook_page_spans(
    spans: list[tuple[float, float, float, float, str]],
    col_names_3: tuple[str, str, str],
    valid_places: set[str],
) -> dict[tuple[str, str], dict[str, str]]:
    """Parses one BPS Statistik Indonesia education table page (6 academic-year cols)."""
    rows = _cluster_spans_into_rows(spans)
    yr_cols: list[tuple[float, float, str]] = []
    header_y: float | None = None
    for row in rows:
        found: list[tuple[float, float, str]] = []
        for x0, _, x1, _, txt in row:
            matches = list(re.finditer(r'20\d{2}/20\d{2}', txt))
            if len(matches) == 1 and txt.strip() == matches[0].group(0):
                found.append((x0, x1, matches[0].group(0)))
            elif matches:
                span_w = x1 - x0
                tlen = max(len(txt), 1)
                for match in matches:
                    found.append((
                        x0 + span_w * (match.start() / tlen),
                        x0 + span_w * (match.end() / tlen),
                        match.group(0),
                    ))
        if len(found) == 6:
            yr_cols = found
            header_y = row[0][1]
            break
    if len(yr_cols) != 6 or header_y is None:
        return {}

    # Each of the 3 column groups (Public/Private/Total or Schools/Teachers/Pupils)
    # holds the same older/newer academic year pair. Using the sorted unique pair
    # protects against occasional BPS header print typos (e.g. Statistik Indonesia
    # 2019 Table 4.1.3 Teachers where Swasta swapped 2016/2017 and 2017/2018).
    uniq_start_years = sorted({lbl.split('/')[0] for _, _, lbl in yr_cols})
    if len(uniq_start_years) == 2:
        col_years = [uniq_start_years[0], uniq_start_years[1]] * 3
    else:
        col_years = [lbl.split('/')[0] for _, _, lbl in yr_cols]

    col_centers = [(x0 + x1) / 2.0 for x0, x1, _ in yr_cols]
    col_map = [(col_names_3[i // 2], col_years[i]) for i in range(6)]
    first_col_x0 = yr_cols[0][0]

    extracted: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        if row[0][1] <= header_y + 5.0:
            continue
        place_parts: list[str] = []
        col_buckets: dict[int, list[tuple[float, str]]] = defaultdict(list)
        for x0, _, x1, _, txt in row:
            if x0 < first_col_x0 - 2.0 and not _is_yearbook_num_cell(txt):
                place_parts.append(txt)
            elif x0 >= first_col_x0 - 12.0 and _is_yearbook_num_cell(txt):
                xc = (x0 + x1) / 2.0
                best_i = min(range(6), key=lambda i: abs(xc - col_centers[i]))
                if abs(xc - col_centers[best_i]) <= 32.0:
                    col_buckets[best_i].append((x0, txt))
        if not place_parts:
            continue
        raw_place = re.sub(r'[\d*/]+$', '', ' '.join(place_parts)).strip()
        norm_place = normalize_place_label(raw_place)
        if valid_places and norm_place not in valid_places:
            continue
        for ci, toks in col_buckets.items():
            toks.sort(key=lambda item: item[0])
            joined = ''.join(tok[1].replace(' ', '') for tok in toks)
            cleaned = clean_simdasi_integer(joined)
            if cleaned:
                cname, yr = col_map[ci]
                extracted.setdefault((norm_place, yr), {})[cname] = cleaned
    return extracted


def _extract_horizontal_pdf_spans(
    page: Any,) -> list[tuple[float, float, float, float, str]]:
    """Extracts horizontal, non-superscript text spans from a PyMuPDF page."""
    spans: list[tuple[float, float, float, float, str]] = []
    page_dict = page.get_text('dict')
    for block in page_dict.get('blocks', []):
        for line in block.get('lines', []):
            # Strictly horizontal text excludes diagonal BPS watermarks.
            dx, dy = line.get('dir', (1.0, 0.0))
            if abs(dx - 1.0) > 0.05 or abs(dy) > 0.05:
                continue
            for span in line.get('spans', []):
                # Exclude superscript footnote markers (font size ~3.5-4.5pt vs >=6.5pt data).
                if span.get('size', 0.0) < 5.5:
                    continue
                txt = (span.get('text') or '').strip()
                if not txt:
                    continue
                x0, y0, x1, y1 = span['bbox']
                spans.append((x0, y0, x1, y1, txt))
    return spans


def extract_yearbook_pdf_tables(
    pdf_bytes: bytes,
    needed_codes: set[str],
    valid_places: set[str],
) -> dict[tuple[str, str], dict[str, str]]:
    """Extracts education tables 4.1.2-4.1.9 from a BPS Statistik Indonesia PDF."""
    try:
        import pymupdf
    except ImportError as exc:
        raise ImportError(
            'pymupdf is required for BPS Statistik Indonesia PDF fallback. '
            'Install dependencies via: pip install -r '
            'statvar_imports/indonesia_census/education/requirements.txt'
        ) from exc

    extracted: dict[tuple[str, str], dict[str, str]] = {}
    doc = pymupdf.open(stream=pdf_bytes, filetype='pdf')
    try:
        npages = len(doc)
        lo, hi = int(npages * 0.12), min(npages, int(npages * 0.50))
        start_idx: int | None = None
        for idx in range(lo, hi):
            txt = doc[idx].get_text('text')
            if '4.1.2' in txt and 'Raudatul' in txt and 'Aceh' in txt:
                start_idx = idx
                break
        if start_idx is None:
            logging.warning(
                'Could not locate Table 4.1.2 (Raudatul Athfal) in BPS yearbook PDF.'
            )
            return extracted

        offset = 0
        for _, code, groups in YEARBOOK_TABLE_SPECS:
            for g_cols in groups:
                page_idx = start_idx + offset
                offset += 1
                if code not in needed_codes or page_idx >= npages:
                    continue
                spans = _extract_horizontal_pdf_spans(doc[page_idx])
                page_data = parse_yearbook_page_spans(spans, g_cols,
                                                      valid_places)
                for key, col_vals in page_data.items():
                    extracted.setdefault(key, {}).update(col_vals)
    finally:
        doc.close()
    return extracted


def fetch_yearbook_publications(
    domain: str,
    api_key: str,
    candidate_editions: list[int] | None = None,
    min_edition: int = MIN_YEARBOOK_EDITION,
    max_pages_per_year: int = 3,
) -> list[tuple[int, str]]:
    """Discovers annual BPS 'Statistik Indonesia YYYY' publications via BPS WebAPI."""
    editions: dict[int, str] = {}
    years_to_query = (sorted(set(candidate_editions)) if candidate_editions else
                      list(range(min_edition,
                                 time.gmtime().tm_year + 2)))
    for edition_yr in years_to_query:
        if edition_yr < min_edition:
            continue
        target_title = f'Statistik Indonesia {edition_yr}'
        for page in range(1, max_pages_per_year + 1):
            url = (
                f'{BPS_API_BASE_URL}/list/model/publication/lang/ind/'
                f'domain/{domain}/keyword/Statistik+Indonesia/year/{edition_yr}'
                f'/page/{page}/key/{api_key}/')
            resp = request_bps_json(url)
            if not isinstance(resp, dict) or resp.get('status') != 'OK':
                raise RuntimeError(
                    f'Failed to list BPS Statistik Indonesia {edition_yr} '
                    f'publications (page={page}): {redact_api_key(resp)}')
            data = resp.get('data')
            if not isinstance(data, list) or len(data) < 2:
                break
            meta, items = data[0], data[1]
            if not isinstance(items, list) or not items:
                break
            found = False
            for item in items:
                if not isinstance(item, dict):
                    continue
                if str(item.get('title', '')).strip() == target_title:
                    pub_id = str(item.get('pub_id', '')).strip()
                    if pub_id:
                        editions[edition_yr] = pub_id
                        found = True
                        break
            if found:
                break
            total_pages = int(meta.get('pages', 1)) if isinstance(meta,
                                                                  dict) else 1
            if page >= total_pages:
                break
    return sorted(editions.items())


def select_yearbook_editions(
    editions: list[tuple[int, str]],
    missing_years: set[int],
) -> list[tuple[int, str]]:
    """Selects minimal chronological Statistik Indonesia editions covering missing_years."""
    if not editions or not missing_years:
        return []
    latest_ed = max(ed for ed, _ in editions)
    selected: list[tuple[int, str]] = []
    for ed, pub_id in sorted(editions):
        # Each edition E covers academic years (E-2, E-1) and occasionally E-3.
        covered = {ed - 3, ed - 2, ed - 1}
        if not (covered & missing_years):
            continue
        # Keep 2019 (covers 2016/2017), even editions (2020, 2022, 2024, 2026...),
        # 2025 (fills SD 2023/2024 omitted in 2024 edition), and latest edition.
        if ed == 2019 or ed == 2025 or ed % 2 == 0 or ed == latest_ed:
            selected.append((ed, pub_id))
    return selected


def fetch_yearbook_school_tables_fallback(
    domain: str,
    api_key: str,
    missing_by_code: dict[str, set[str]],
    table_data: dict[tuple[str, str], dict[str, str]],
    delay_sec: float = 0.0,
) -> None:
    """Fills missing SIMDASI school data from BPS Statistik Indonesia PDFs."""
    supported_codes = {code for _, code, _ in YEARBOOK_TABLE_SPECS}
    needed_missing = {
        code: yrs
        for code, yrs in missing_by_code.items()
        if code in supported_codes and yrs
    }
    if not needed_missing:
        return

    missing_years = {int(yr) for yrs in needed_missing.values() for yr in yrs}
    logging.warning(
        'SIMDASI returned empty values for tables %s; falling back to BPS '
        'Statistik Indonesia publications for years %s.',
        sorted(needed_missing.keys()),
        sorted(missing_years),
    )

    candidate_editions = sorted({
        yr + delta
        for yr in missing_years
        for delta in (1, 2, 3)
        if yr + delta >= MIN_YEARBOOK_EDITION
    })
    editions = fetch_yearbook_publications(
        domain=domain,
        api_key=api_key,
        candidate_editions=candidate_editions,
    )
    selected = select_yearbook_editions(editions, missing_years)
    if not selected:
        raise RuntimeError(
            f'No BPS Statistik Indonesia publications found covering years {sorted(missing_years)}.'
        )

    valid_places = _load_valid_places()
    needed_codes = set(needed_missing.keys())
    pdf_data: dict[tuple[str, str], dict[str, str]] = {}
    parsed_editions: set[int] = set()

    def _download_and_parse(
        ed_list: list[tuple[int, str]],
        overwrite: bool = True,
    ) -> None:
        for ed, pub_id in ed_list:
            if ed in parsed_editions:
                continue
            if delay_sec > 0:
                time.sleep(delay_sec)
            view_url = (
                f'{BPS_API_BASE_URL}/view/domain/{domain}/model/publication/'
                f'lang/ind/id/{pub_id}/key/{api_key}/')
            view_resp = request_bps_json(view_url)
            pub_obj = (view_resp.get('data')
                       if isinstance(view_resp, dict) else None)
            pdf_url = (pub_obj.get('pdf')
                       if isinstance(pub_obj, dict) else None)
            if not pdf_url:
                raise RuntimeError(
                    f'Missing PDF URL for Statistik Indonesia {ed} (pub_id={pub_id}).'
                )
            pdf_bytes = request_bps_bytes(pdf_url)
            ed_data = extract_yearbook_pdf_tables(pdf_bytes, needed_codes,
                                                  valid_places)
            for key, col_vals in ed_data.items():
                dest = pdf_data.setdefault(key, {})
                for col, val in col_vals.items():
                    if overwrite or not dest.get(col):
                        dest[col] = val
            parsed_editions.add(ed)

    _download_and_parse(selected, overwrite=True)

    # If any requested (code, year) is still missing, try remaining editions covering it.
    still_missing_years: set[int] = set()
    for code, yrs in needed_missing.items():
        code_cols = set(TABLE_CODE_TO_COLUMNS.get(code, ()))
        for yr in yrs:
            if _count_table_year_values(pdf_data, yr, code_cols) == 0:
                still_missing_years.add(int(yr))
    if still_missing_years:
        extra = [(ed, pid)
                 for ed, pid in reversed(editions)
                 if ed not in parsed_editions and ({ed - 3, ed - 2, ed - 1} &
                                                   still_missing_years)]
        if extra:
            _download_and_parse(extra, overwrite=False)

    # Merge PDF fallback values into table_data without overwriting live SIMDASI data.
    added = 0
    for key, col_vals in pdf_data.items():
        cell_map = table_data.setdefault(key, {})
        for col, val in col_vals.items():
            if col not in cell_map or not cell_map[col]:
                cell_map[col] = val
                added += 1
    logging.info(
        'Populated %d school observations from %d BPS Statistik Indonesia publications.',
        added,
        len(parsed_editions),
    )


def validate_school_tables_populated(
    table_data: dict[tuple[str, str], dict[str, str]],
    tables: tuple[tuple[str, str], ...] = SIMDASI_TABLES,
) -> None:
    """Raises RuntimeError if any configured school table yielded zero values."""
    empty_codes: list[str] = []
    for code, _ in tables:
        code_cols = set(TABLE_CODE_TO_COLUMNS.get(code, ()))
        if not code_cols:
            continue
        has_any = any(
            col_map.get(col)
            for col_map in table_data.values()
            for col in code_cols)
        if not has_any:
            empty_codes.append(code)
    if empty_codes:
        raise RuntimeError(
            f'No observations extracted for BPS school tables: {empty_codes}')


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
    missing_by_code = fetch_simdasi_school_tables(
        api_key=api_key,
        table_data=table_data,
        delay_sec=_FLAGS.request_delay_sec,
    )
    if missing_by_code and _FLAGS.enable_yearbook_fallback:
        fetch_yearbook_school_tables_fallback(
            domain=_FLAGS.domain,
            api_key=api_key,
            missing_by_code=missing_by_code,
            table_data=table_data,
            delay_sec=_FLAGS.request_delay_sec,
        )
    validate_school_tables_populated(table_data)
    os.makedirs(_FLAGS.output_dir, exist_ok=True)
    output_path = os.path.join(_FLAGS.output_dir, _FLAGS.output_filename)
    write_education_csv(
        output_path=output_path,
        table_data=table_data,
    )


def _define_flags() -> None:
    """Defines CLI flags when executed as a script."""
    flags.DEFINE_string(
        'output_dir',
        os.path.join(_CODEDIR, 'input_files'),
        'Directory path to save the downloaded input CSV file.',
    )
    flags.DEFINE_string(
        'output_filename',
        'indonesia_education_input.csv',
        'Filename for the combined Indonesia Education CSV table.',
    )
    flags.DEFINE_string(
        'domain',
        '0000',
        'BPS domain code (0000 for national/all-province tables).',
    )
    flags.DEFINE_integer(
        'literacy_province_var_id',
        1458,
        'BPS variable ID for Literacy Rate of Population Aged 15+ by Province.',
    )
    flags.DEFINE_integer(
        'literacy_sex_var_id',
        1460,
        'BPS variable ID for Literacy Rate of Population Aged 15+ by Sex.',
    )
    flags.DEFINE_string(
        'api_key',
        os.environ.get('BPS_API_KEY', ''),
        'BPS WebAPI key (loaded from GCS config.json if not set).',
    )
    flags.DEFINE_float(
        'request_delay_sec',
        0.5,
        'Delay in seconds between SIMDASI API requests to respect BPS rate limits.',
    )
    flags.DEFINE_boolean(
        'enable_yearbook_fallback',
        True,
        'Fall back to BPS Statistik Indonesia yearbook PDFs via BPS WebAPI '
        'when SIMDASI id/25 returns empty values for school tables.',
    )


if __name__ == '__main__':
    _define_flags()
    app.run(main)
