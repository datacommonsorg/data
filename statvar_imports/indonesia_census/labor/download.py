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
"""Downloads Indonesia Labor (LFPR by Sex & Formal Labor Share) data from BPS WebAPI."""

import csv
import html
import json
import os
import re
import sys
import tempfile
import time
from typing import Any

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.join(_CODEDIR, '../../../util/'))

from absl import app
from absl import flags
from absl import logging
import file_util
import requests

DEFAULT_LOCAL_CONFIG_PATH = (
    '/tmp/gcs/statvar_imports/indonesia_census/config.json')
DEFAULT_GCS_CONFIG_PATH = 'gs://unresolved_mcf/country/indonesia/config.json'

_FLAGS = flags.FLAGS
if 'output_dir' not in _FLAGS:
    flags.DEFINE_string(
        'output_dir',
        os.path.join(_CODEDIR, 'input_files'),
        'Directory path to save the downloaded input CSV and raw JSON files.',
    )
if 'lfpr_filename' not in _FLAGS:
    flags.DEFINE_string(
        'lfpr_filename',
        'labor_force_participation_rate_by_sex.csv',
        'Filename for the Labor Force Participation Rate by Sex CSV table.',
    )
if 'formal_labor_filename' not in _FLAGS:
    flags.DEFINE_string(
        'formal_labor_filename',
        'percentage_of_formal_labor_by_province.csv',
        'Filename for the Percentage of Formal Labor by Province CSV table.',
    )
if 'domain' not in _FLAGS:
    flags.DEFINE_string(
        'domain',
        '0000',
        'BPS domain code (0000 for national/all-province tables).',
    )
if 'lfpr_var_id' not in _FLAGS:
    flags.DEFINE_integer(
        'lfpr_var_id',
        2200,
        'BPS variable ID for Labor Force Participation Rate by Sex.',
    )
if 'formal_labor_var_id' not in _FLAGS:
    flags.DEFINE_integer(
        'formal_labor_var_id',
        1168,
        'BPS variable ID for Percentage of Formal Labor by Province.',
    )
if 'api_key' not in _FLAGS:
    flags.DEFINE_string(
        'api_key',
        os.environ.get('BPS_API_KEY', ''),
        'BPS WebAPI key (loaded from GCS config.json if not set).',
    )

BPS_API_BASE_URL = 'https://webapi.bps.go.id/v1/api/list'
MAX_YEARS_PER_REQUEST = 3

LFPR_PLACE_HEADER = 'Province/Regency/City'
YEAR_HEADER = 'Year'
FORMAL_LABOR_TITLE = 'Percentage of Formal Labor by Province (Percent)'
FORMAL_LABOR_PLACE_HEADER = 'Province'

# In the legacy Indonesia_Census Labor workbook, these 7 cities were omitted
# because their corresponding regency names in places_resolved_csv already map
# to the shared Wikidata DCIDs in Data Commons.
SKIPPED_LFPR_CITY_LABELS = frozenset({
    'Kota Magelang',
    'Kota Semarang',
    'Kota Malang',
    'Kota Mojokerto',
    'Kota Kupang',
    'Kota Sorong',
    'Kota Jayapura',
})

PLACE_NAME_REWRITES = {
    'Toli-Toli': 'ToliToli',
    'Tojo Una-Una': 'Tojo UnaUna',
    'KEP. RIAU': 'KEPULAUAN RIAU',
    'DI YOGYAKARTA': 'D I YOGYAKARTA',
}

_SESSION = requests.Session()


def redact_api_key(text: Any) -> str:
    """Redacts any embedded /key/<api_key>/ segment from URLs or error messages."""
    return re.sub(r'/key/[^/\s]+/?', '/key/REDACTED/', str(text))


def request_bps_json(
    url: str,
    timeout: int = 30,
    retries: int = 3,
    retry_secs: float = 2.0,
    session: requests.Session | None = None,
) -> Any:
    """Fetches JSON from BPS WebAPI with exponential backoff and redacted logging."""
    http_session = session or _SESSION
    redacted_url = redact_api_key(url)
    logging.info('Downloading URL: %s', redacted_url)
    max_attempts = max(1, retries)
    last_error: Exception | None = None

    for attempt in range(max_attempts):
        try:
            response = http_session.get(url, timeout=timeout)
            if response.ok:
                return response.json()
            status_code = response.status_code
            last_error = RuntimeError(f'HTTP {status_code} from {redacted_url}')
            if 400 <= status_code < 500 and status_code != 429:
                raise RuntimeError(
                    f'Permanent HTTP {status_code} from {redacted_url}'
                ) from last_error
        except (requests.RequestException, ValueError) as exc:
            last_error = exc

        if attempt + 1 < max_attempts:
            backoff = retry_secs * (2**attempt)
            time.sleep(backoff)

    raise RuntimeError(
        f'Failed to download {redacted_url}: {redact_api_key(last_error)}'
    ) from last_error


def write_json_atomic(output_path: str, payload: Any) -> None:
    """Writes a JSON payload atomically via a temporary file in the same directory."""
    abs_output_path = os.path.abspath(output_path)
    out_dir = os.path.dirname(abs_output_path)
    os.makedirs(out_dir, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=out_dir,
        prefix='.tmp_raw_',
        suffix='.json',
    )
    try:
        with os.fdopen(tmp_fd, 'w', encoding='utf-8') as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)
        os.replace(tmp_path, abs_output_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def clean_place_label(vervar_val: int, raw_label: Any) -> str:
    """Strips HTML tags/entities and normalizes BPS place labels."""
    text = re.sub(r'<[^>]+>', '', html.unescape(str(raw_label))).strip()
    if int(vervar_val) == 7500 and text.upper() == 'GORONTALO':
        return 'GORONTALO aa1'
    return PLACE_NAME_REWRITES.get(text, text)


def format_cell_value(raw_val: Any) -> str:
    """Formats a numeric or string cell value from BPS datacontent."""
    if raw_val is None or str(raw_val).strip() == '':
        return ''
    if isinstance(raw_val, float) and raw_val.is_integer():
        return str(int(raw_val))
    return str(raw_val).strip()


def fetch_available_years(
    domain: str,
    var_id: int,
    api_key: str,
) -> list[dict[str, Any]]:
    """Fetches all available year definitions (th_id, th) for a BPS variable."""
    years: list[dict[str, Any]] = []
    page = 1
    while True:
        url = (f'{BPS_API_BASE_URL}/model/th/lang/eng/domain/{domain}'
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

    years.sort(
        key=lambda item: (int(str(item['th']).strip()), int(item['th_id'])))
    return years


def fetch_lfpr_table(
    domain: str,
    var_id: int,
    api_key: str,
    raw_output_path: str | None = None,
) -> tuple[list[str], list[str], list[str], dict[tuple[str, str, str], str]]:
    """Downloads all year chunks for LFPR by Sex (var_id=2200)."""
    years = fetch_available_years(domain=domain, var_id=var_id, api_key=api_key)
    if not years:
        raise RuntimeError(f'No years returned for BPS var_id={var_id}.')

    places: list[str] = []
    seen_places: set[str] = set()
    sex_labels: list[str] = []
    year_labels: list[str] = [str(y['th']).strip() for y in years]
    values_by_place_sex_year: dict[tuple[str, str, str], str] = {}
    raw_chunks: list[dict[str, Any]] = []

    for idx in range(0, len(years), MAX_YEARS_PER_REQUEST):
        chunk = years[idx:idx + MAX_YEARS_PER_REQUEST]
        th_param = ';'.join(str(y['th_id']) for y in chunk)
        url = (f'{BPS_API_BASE_URL}/model/data/lang/eng/domain/{domain}'
               f'/var/{var_id}/th/{th_param}/key/{api_key}/')
        resp = request_bps_json(url)
        if not isinstance(resp, dict) or resp.get('status') != 'OK':
            raise RuntimeError(f'Failed to fetch LFPR data for th={th_param}: '
                               f'{redact_api_key(resp)}')
        raw_chunks.append(resp)

        var_list = resp.get('var') or []
        turvar_list = resp.get('turvar') or []
        turtahun_list = resp.get('turtahun') or []
        vervar_list = resp.get('vervar') or []
        tahun_list = resp.get('tahun') or []
        datacontent = resp.get('datacontent') or {}

        if not (var_list and turvar_list and turtahun_list and vervar_list and
                tahun_list and datacontent):
            raise RuntimeError(
                f'Incomplete metadata or datacontent in BPS LFPR response for th={th_param}.'
            )

        vid = var_list[0]['val']
        tt_val = turtahun_list[0]['val']
        if not sex_labels:
            sex_labels = [str(tv['label']).strip() for tv in turvar_list]

        for vv in vervar_list:
            place_label = clean_place_label(vv['val'], vv['label'])
            if place_label in SKIPPED_LFPR_CITY_LABELS:
                continue
            if place_label not in seen_places:
                seen_places.add(place_label)
                places.append(place_label)
            for tv in turvar_list:
                sex_label = str(tv['label']).strip()
                tv_val = tv['val']
                for ty in tahun_list:
                    year_str = str(ty['label']).strip()
                    cell_key = f"{vv['val']}{vid}{tv_val}{ty['val']}{tt_val}"
                    formatted = format_cell_value(datacontent.get(cell_key))
                    if formatted != '':
                        values_by_place_sex_year[(place_label, sex_label,
                                                  year_str)] = formatted

    if raw_output_path:
        write_json_atomic(raw_output_path, {
            'years': years,
            'chunks': raw_chunks
        })

    return places, sex_labels, year_labels, values_by_place_sex_year


def write_lfpr_csv(
    output_path: str,
    places: list[str],
    sex_labels: list[str],
    year_labels: list[str],
    values_by_place_sex_year: dict[tuple[str, str, str], str],
) -> None:
    """Writes the long-format LFPR by Sex CSV atomically for stat_var_processor.py."""
    abs_output_path = os.path.abspath(output_path)
    out_dir = os.path.dirname(abs_output_path)
    os.makedirs(out_dir, exist_ok=True)

    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=out_dir,
        prefix='.tmp_lfpr_',
        suffix='.csv',
    )
    row_count = 0
    try:
        with os.fdopen(tmp_fd, 'w', newline='', encoding='utf-8') as fp:
            writer = csv.writer(fp)
            writer.writerow([LFPR_PLACE_HEADER, YEAR_HEADER] + sex_labels)
            for place in places:
                for year in year_labels:
                    sex_vals = [
                        values_by_place_sex_year.get((place, sex, year), '')
                        for sex in sex_labels
                    ]
                    if any(v != '' for v in sex_vals):
                        writer.writerow([place, year] + sex_vals)
                        row_count += 1
        os.replace(tmp_path, abs_output_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    logging.info(
        'Wrote %d LFPR rows across %d places, %d sexes, and %d years (%s-%s) to %s',
        row_count,
        len(places),
        len(sex_labels),
        len(year_labels),
        year_labels[0] if year_labels else 'N/A',
        year_labels[-1] if year_labels else 'N/A',
        output_path,
    )


def fetch_formal_labor_table(
    domain: str,
    var_id: int,
    api_key: str,
    raw_output_path: str | None = None,
) -> tuple[list[str], list[str], dict[tuple[str, str], str]]:
    """Downloads all year chunks for Formal Labor by Province (var_id=1168)."""
    years = fetch_available_years(domain=domain, var_id=var_id, api_key=api_key)
    if not years:
        raise RuntimeError(f'No years returned for BPS var_id={var_id}.')

    provinces: list[str] = []
    seen_provinces: set[str] = set()
    year_labels: list[str] = [str(y['th']).strip() for y in years]
    values_by_place_year: dict[tuple[str, str], str] = {}
    raw_chunks: list[dict[str, Any]] = []

    for idx in range(0, len(years), MAX_YEARS_PER_REQUEST):
        chunk = years[idx:idx + MAX_YEARS_PER_REQUEST]
        th_param = ';'.join(str(y['th_id']) for y in chunk)
        url = (f'{BPS_API_BASE_URL}/model/data/lang/eng/domain/{domain}'
               f'/var/{var_id}/th/{th_param}/key/{api_key}/')
        resp = request_bps_json(url)
        if not isinstance(resp, dict) or resp.get('status') != 'OK':
            raise RuntimeError(
                f'Failed to fetch Formal Labor data for th={th_param}: '
                f'{redact_api_key(resp)}')
        raw_chunks.append(resp)

        var_list = resp.get('var') or []
        turvar_list = resp.get('turvar') or []
        turtahun_list = resp.get('turtahun') or []
        vervar_list = resp.get('vervar') or []
        tahun_list = resp.get('tahun') or []
        datacontent = resp.get('datacontent') or {}

        if not (var_list and turvar_list and turtahun_list and vervar_list and
                tahun_list and datacontent):
            raise RuntimeError(
                f'Incomplete metadata or datacontent in BPS Formal Labor response for th={th_param}.'
            )

        vid = var_list[0]['val']
        tv_val = turvar_list[0]['val']
        tt_val = turtahun_list[0]['val']

        for vv in vervar_list:
            place_label = clean_place_label(vv['val'], vv['label'])
            if place_label not in seen_provinces:
                seen_provinces.add(place_label)
                provinces.append(place_label)
            for ty in tahun_list:
                year_str = str(ty['label']).strip()
                cell_key = f"{vv['val']}{vid}{tv_val}{ty['val']}{tt_val}"
                formatted = format_cell_value(datacontent.get(cell_key))
                if formatted != '':
                    values_by_place_year[(place_label, year_str)] = formatted

    if raw_output_path:
        write_json_atomic(raw_output_path, {
            'years': years,
            'chunks': raw_chunks
        })

    return provinces, year_labels, values_by_place_year


def write_formal_labor_csv(
    output_path: str,
    provinces: list[str],
    year_labels: list[str],
    values_by_place_year: dict[tuple[str, str], str],
) -> None:
    """Writes the long-format Formal Labor by Province CSV atomically for stat_var_processor.py."""
    abs_output_path = os.path.abspath(output_path)
    out_dir = os.path.dirname(abs_output_path)
    os.makedirs(out_dir, exist_ok=True)

    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=out_dir,
        prefix='.tmp_formal_labor_',
        suffix='.csv',
    )
    row_count = 0
    try:
        with os.fdopen(tmp_fd, 'w', newline='', encoding='utf-8') as fp:
            writer = csv.writer(fp)
            writer.writerow(
                [FORMAL_LABOR_PLACE_HEADER, YEAR_HEADER, FORMAL_LABOR_TITLE])
            for province in provinces:
                for year in year_labels:
                    val = values_by_place_year.get((province, year), '')
                    if val != '':
                        writer.writerow([province, year, val])
                        row_count += 1
        os.replace(tmp_path, abs_output_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    logging.info(
        'Wrote %d Formal Labor rows across %d provinces and %d years (%s-%s) to %s',
        row_count,
        len(provinces),
        len(year_labels),
        year_labels[0] if year_labels else 'N/A',
        year_labels[-1] if year_labels else 'N/A',
        output_path,
    )


def get_bps_api_key(
    flag_key: str = '',
    local_config_path: str = DEFAULT_LOCAL_CONFIG_PATH,
    gcs_config_path: str = DEFAULT_GCS_CONFIG_PATH,
) -> str:
    """Retrieves the BPS API key from flag, env var, local config, or GCS config."""
    key = flag_key or os.environ.get('BPS_API_KEY', '')
    if key:
        return key

    last_error: Exception | None = None
    if local_config_path and os.path.exists(local_config_path):
        try:
            with open(local_config_path, mode='r', encoding='utf-8') as fp:
                data = json.load(fp)
            if isinstance(data, dict) and data.get('bps_api_key'):
                return str(data['bps_api_key']).strip()
        except (OSError, ValueError) as exc:
            last_error = exc
            logging.warning(
                'Could not read local BPS config at %s: %s',
                local_config_path,
                exc,
            )

    if gcs_config_path:
        try:
            with file_util.FileIO(gcs_config_path, 'r') as fp:
                data = json.load(fp)
            if isinstance(data, dict) and data.get('bps_api_key'):
                return str(data['bps_api_key']).strip()
        except Exception as exc:
            last_error = exc
            logging.warning(
                'Could not read BPS API key from GCS (%s): %s',
                gcs_config_path,
                exc,
            )

    raise ValueError(
        'BPS API key not provided via --api_key, BPS_API_KEY, or GCS config.json.'
    ) from last_error


def main(_) -> None:
    logging.set_verbosity(logging.INFO)
    api_key = get_bps_api_key(_FLAGS.api_key)
    lfpr_raw_path = os.path.join(_FLAGS.output_dir, 'raw_lfpr_2200.json')
    places, sex_labels, lfpr_years, lfpr_values = fetch_lfpr_table(
        domain=_FLAGS.domain,
        var_id=_FLAGS.lfpr_var_id,
        api_key=api_key,
        raw_output_path=lfpr_raw_path,
    )
    lfpr_path = os.path.join(_FLAGS.output_dir, _FLAGS.lfpr_filename)
    write_lfpr_csv(
        output_path=lfpr_path,
        places=places,
        sex_labels=sex_labels,
        year_labels=lfpr_years,
        values_by_place_sex_year=lfpr_values,
    )

    fl_raw_path = os.path.join(_FLAGS.output_dir, 'raw_formal_labor_1168.json')
    provinces, fl_years, fl_values = fetch_formal_labor_table(
        domain=_FLAGS.domain,
        var_id=_FLAGS.formal_labor_var_id,
        api_key=api_key,
        raw_output_path=fl_raw_path,
    )
    fl_path = os.path.join(_FLAGS.output_dir, _FLAGS.formal_labor_filename)
    write_formal_labor_csv(
        output_path=fl_path,
        provinces=provinces,
        year_labels=fl_years,
        values_by_place_year=fl_values,
    )


if __name__ == '__main__':
    app.run(main)
