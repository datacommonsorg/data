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
"""Downloads Ethiopia Statistics datasets from Open Data for Africa.

Fetches the five Ethiopia Statistics datasets directly from the
ethiopia.opendataforafrica.org Knoema REST API using util/download_util.py:
  - udghlsf: Regional Population Distribution and Daily per Capita Calorie Intake
  - xtqdbuc: Ethiopia Statistics, 2011 (Population all years)
  - teakvke: Population and Households of Ethiopia, 2007
  - xpcyhcf: Population Projection by Region and Sex (2022)
  - yusibcg: Demographic and Health Survey, 2014, Ethiopia

Raw API JSON responses are preserved verbatim in --raw_dir and normalized CSVs
ready for stat_var_processor.py are written to --output_dir.
"""

import csv
import json
import math
import os
import sys
import tempfile
from typing import Any

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_UTIL_DIR = os.path.abspath(os.path.join(_MODULE_DIR, '../../../util'))
if _UTIL_DIR not in sys.path:
    sys.path.insert(0, _UTIL_DIR)

from absl import app
from absl import flags
from absl import logging
import download_util

_FLAGS = flags.FLAGS

API_BASE_URL = 'https://ethiopia.opendataforafrica.org/api/1.0'
DEFAULT_HEADERS = {
    'Accept':
        'application/json',
    'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'),
}
MAX_RAW_PAGES = 100

ALL_DATASET_IDS = ('udghlsf', 'xtqdbuc', 'teakvke', 'xpcyhcf', 'yusibcg')

DATASET_OUTPUT_FILENAMES = {
    'udghlsf': 'ethiopia_demographics.csv',
    'xtqdbuc': 'ethiopia_population_all_year.csv',
    'teakvke': 'ethiopia_population_2007.csv',
    'xpcyhcf': 'ethiopia_population_projection_2022.csv',
    'yusibcg': 'ethiopia_yusibcg.csv',
}

XTQDBUC_POPULATION_INDICATORS = frozenset({
    'Rural population',
    'Urban population',
    'Total Population - Both sexes',
    'Total Population - Female',
    'Total Population - Male',
})

TEAKVKE_POPULATION_VARIABLES = frozenset({
    'Population, Both Sexes',
    'Population, Male',
    'Population, Female',
})


def _define_flags() -> None:
    """Defines command-line flags for the download script."""
    flags.DEFINE_string(
        'raw_dir',
        os.path.join(_MODULE_DIR, 'raw_files'),
        'Directory to store verbatim raw API JSON responses.',
    )
    flags.DEFINE_string(
        'output_dir',
        os.path.join(_MODULE_DIR, 'input_files'),
        'Directory to store processed CSV input files for stat_var_processor.',
    )
    flags.DEFINE_list(
        'datasets',
        list(ALL_DATASET_IDS),
        'Comma-separated Knoema dataset IDs to download.',
    )
    flags.DEFINE_integer(
        'timeout',
        60,
        'HTTP request timeout in seconds.',
    )
    flags.DEFINE_integer(
        'retries',
        3,
        'Number of HTTP retry attempts per request.',
    )
    flags.DEFINE_integer(
        'retry_secs',
        5,
        'Delay in seconds between HTTP retries.',
    )


def _atomic_write_text(file_path: str, content: str) -> None:
    """Writes text content atomically via a temporary file in the target dir."""
    target_dir = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(target_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=target_dir, prefix='.tmp_')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as fp:
            fp.write(content)
        os.replace(tmp_path, file_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _atomic_write_csv(file_path: str, headers: list[str],
                      rows: list[list[Any]]) -> None:
    """Writes CSV rows atomically via a temporary file in the target dir."""
    target_dir = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(target_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=target_dir, prefix='.tmp_')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as fp:
            writer = csv.writer(fp)
            writer.writerow(headers)
            writer.writerows(rows)
        os.replace(tmp_path, file_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _format_number(value: Any) -> str:
    """Formats numeric values cleanly without trailing .0 for integers."""
    if value is None:
        return ''
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        if math.isnan(value) or math.isinf(value):
            return ''
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return f'{value:.15g}'
    return str(value).strip()


def _request_json(
    url: str,
    method: str = 'GET',
    params: dict[str, Any] | None = None,
    timeout: int = 60,
    retries: int = 3,
    retry_secs: int = 5,
) -> dict[str, Any]:
    """Issues an HTTP request via download_util and validates JSON dict output.

    Note: util/download_util.request_url checks response.ok (HTTP 2xx)
    internally, logs the raw requests.Response object at DEBUG level, and
    returns parsed JSON only on HTTP 2xx success.
    """
    log_payload = (f'query_params={params}' if method.upper() == 'GET' else
                   f'body_keys={sorted((params or {}).keys())}, '
                   f'dataset={(params or {}).get("Dataset")}')
    logging.info('HTTP %s %s (%s)', method.upper(), url, log_payload)

    response = download_util.request_url(
        url=url,
        params=params,
        method=method,
        headers=DEFAULT_HEADERS,
        output='json',
        timeout=timeout,
        retries=retries,
        retry_secs=retry_secs,
        use_cache=False,
    )
    if response is None:
        raise RuntimeError(
            f'HTTP {method.upper()} request failed (non-2xx or empty response) '
            f'for URL {url} ({log_payload}).')
    if not isinstance(response, dict):
        raise RuntimeError(
            f'Unexpected non-object JSON response from {url} ({log_payload}): '
            f'{str(response)[:200]!r}')
    logging.info('HTTP %s %s -> 2xx OK (response_keys=%s)', method.upper(), url,
                 sorted(response.keys()))
    return response


def _filter_dimension_items(
        dataset_id: str, dim_id: str,
        items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Selects dimension member items required for each dataset."""
    if dataset_id == 'xtqdbuc' and dim_id == 'indicator':
        filtered = [
            item for item in items
            if item.get('name') in XTQDBUC_POPULATION_INDICATORS
        ]
        if not filtered:
            raise RuntimeError(
                'No matching population indicators found in xtqdbuc metadata.')
        return filtered

    if dataset_id == 'teakvke':
        if dim_id == 'variable':
            filtered = [
                item for item in items
                if item.get('name') in TEAKVKE_POPULATION_VARIABLES
            ]
            if not filtered:
                raise RuntimeError(
                    'No matching population variables found in teakvke metadata.'
                )
            return filtered
        if dim_id == 'region':
            # Keep country (level 0) and AdministrativeArea1 regions (level 1).
            filtered = [
                item for item in items
                if (item.get('level') if item.get('level') is not None else 0
                   ) <= 1
            ]
            if not filtered:
                raise RuntimeError(
                    'No level <= 1 regions found in teakvke metadata.')
            return filtered

    return [item for item in items if item.get('hasData', True)]


def fetch_dataset_raw(
    dataset_id: str,
    timeout: int = 60,
    retries: int = 3,
    retry_secs: int = 5,
) -> dict[str, Any]:
    """Fetches dataset metadata, dimension metadata, and all raw data pages."""
    meta_url = f'{API_BASE_URL}/meta/dataset/{dataset_id}'
    dataset_meta = _request_json(
        meta_url,
        method='GET',
        timeout=timeout,
        retries=retries,
        retry_secs=retry_secs,
    )
    dimensions = dataset_meta.get('dimensions')
    if not isinstance(dimensions, list) or not dimensions:
        raise RuntimeError(
            f'Dataset {dataset_id} metadata is missing dimensions: '
            f'{list(dataset_meta.keys())}')

    dim_metadata: dict[str, list[dict[str, Any]]] = {}
    stub: list[dict[str, Any]] = []
    for dim in dimensions:
        dim_id = dim['id']
        dim_url = f'{API_BASE_URL}/meta/dataset/{dataset_id}/dimension/{dim_id}'
        dim_resp = _request_json(
            dim_url,
            method='GET',
            timeout=timeout,
            retries=retries,
            retry_secs=retry_secs,
        )
        items = dim_resp.get('items', [])
        if not isinstance(items, list) or not items:
            raise RuntimeError(
                f'Dimension {dim_id} for dataset {dataset_id} returned no items.'
            )
        dim_metadata[dim_id] = items
        selected = _filter_dimension_items(dataset_id, dim_id, items)
        stub.append({
            'DimensionId': dim_id,
            'Members': [item['key'] for item in selected],
        })

    raw_url = f'{API_BASE_URL}/data/raw'
    request_body = {
        'Dataset': dataset_id,
        'Header': [{
            'DimensionId': 'Time',
            'Members': [],
            'UiMode': 'allData',
        }],
        'Stub': stub,
        'Filter': [],
        'Frequencies': ['A'],
    }
    first_page = _request_json(
        raw_url,
        method='POST',
        params=request_body,
        timeout=timeout,
        retries=retries,
        retry_secs=retry_secs,
    )

    pages: list[dict[str, Any]] = [first_page]
    first_data = first_page.get('data') or []
    if not isinstance(first_data, list):
        raise RuntimeError(
            f'Dataset {dataset_id} page 1 returned non-list data field: '
            f'{type(first_data).__name__}')
    all_series: list[dict[str, Any]] = list(first_data)
    token = first_page.get('continuationToken')
    page_num = 1

    while token:
        page_num += 1
        if page_num > MAX_RAW_PAGES:
            raise RuntimeError(
                f'Pagination exceeded {MAX_RAW_PAGES} pages for dataset '
                f'{dataset_id}; aborting to prevent infinite loop.')
        next_page = _request_json(
            raw_url,
            method='GET',
            params={'continuationToken': token},
            timeout=timeout,
            retries=retries,
            retry_secs=retry_secs,
        )
        pages.append(next_page)
        next_data = next_page.get('data') or []
        if not isinstance(next_data, list):
            raise RuntimeError(
                f'Dataset {dataset_id} page {page_num} returned non-list data '
                f'field: {type(next_data).__name__}')
        all_series.extend(next_data)
        token = next_page.get('continuationToken')

    if not all_series:
        raise RuntimeError(
            f'Dataset {dataset_id} returned zero data series across '
            f'{page_num} page(s).')

    logging.info(
        'Downloaded dataset %s: %d series across %d page(s).',
        dataset_id,
        len(all_series),
        page_num,
    )
    return {
        'dataset_id': dataset_id,
        'metadata': dataset_meta,
        'dimensions': dim_metadata,
        'pages': pages,
        'series': all_series,
    }


def _require_dim_dict(series: dict[str, Any], dim_key: str,
                      dataset_id: str) -> dict[str, Any]:
    """Validates and returns a required dimension object from a series entry."""
    dim = series.get(dim_key)
    if not isinstance(dim, dict):
        raise ValueError(
            f'Dataset {dataset_id} series tsKey={series.get("tsKey")} is '
            f'missing required dimension dict {dim_key!r} (got {dim!r}).')
    return dim


def _require_dim_name(series: dict[str, Any], dim_key: str,
                      dataset_id: str) -> str:
    """Validates and returns a non-empty dimension name string."""
    dim = _require_dim_dict(series, dim_key, dataset_id)
    name = dim.get('name')
    if not isinstance(name, str) or not name.strip():
        raise ValueError(
            f'Dataset {dataset_id} series tsKey={series.get("tsKey")} has '
            f'missing or invalid name for dimension {dim_key!r} (got {name!r}).'
        )
    return name


def _extract_annual_values(series: dict[str, Any]) -> dict[int, Any]:
    """Maps annual series values to integer years using startDate/endDate."""
    freq = series.get('frequency', 'A')
    if freq != 'A':
        raise ValueError(
            f'Unsupported frequency {freq!r} in series tsKey={series.get("tsKey")}'
        )
    start_date = series.get('startDate') or ''
    end_date = series.get('endDate') or ''
    values = series.get('values')
    if values is None:
        values = []
    if (not isinstance(start_date, str) or not isinstance(end_date, str) or
            len(start_date) < 4 or len(end_date) < 4):
        raise ValueError(
            f'Invalid startDate/endDate ({start_date!r}, {end_date!r}) '
            f'in series tsKey={series.get("tsKey")}')
    if not isinstance(values, list):
        raise ValueError(f'Invalid values type ({type(values).__name__}) '
                         f'in series tsKey={series.get("tsKey")}')
    start_year = int(start_date[:4])
    end_year = int(end_date[:4])
    expected_len = end_year - start_year + 1
    if len(values) != expected_len:
        raise ValueError(
            f'Values length {len(values)} does not match year span '
            f'{start_year}-{end_year} ({expected_len}) for tsKey={series.get("tsKey")}'
        )
    return {
        start_year + idx: val
        for idx, val in enumerate(values)
        if val is not None
    }


def transform_udghlsf(
        series_list: list[dict[str, Any]]) -> tuple[list[str], list[list[str]]]:
    """Transforms udghlsf (Demographics) into wide CSV format."""
    all_years: set[int] = set()
    records: list[tuple[str, str, str, dict[int, Any]]] = []
    for series in series_list:
        region_name = _require_dim_name(series, 'region', 'udghlsf')
        var_name = _require_dim_name(series, 'variable', 'udghlsf')
        unit = series.get('unit') or ''
        year_vals = _extract_annual_values(series)
        if not year_vals:
            continue
        all_years.update(year_vals.keys())
        records.append((region_name, var_name, unit, year_vals))

    sorted_years = sorted(all_years)
    headers = ['Region', 'Variable', 'Units'] + [str(y) for y in sorted_years]
    rows: list[list[str]] = []
    for region_name, var_name, unit, year_vals in records:
        row = [region_name, var_name, unit
              ] + [_format_number(year_vals.get(y)) for y in sorted_years]
        rows.append(row)
    return headers, rows


def transform_xtqdbuc(
        series_list: list[dict[str, Any]]) -> tuple[list[str], list[list[str]]]:
    """Transforms xtqdbuc (Population all year) into wide CSV format.

    Knoema API returns values in units of thousands with scale=1000. The
    existing pvmap multiplies by 1,000,000 on Units/Scale='thousands' (matching
    Knoema UI Excel exports where displayed values are divided by scale=1000).
    We preserve that exact numeric representation here.
    """
    all_years: set[int] = set()
    records: list[tuple[str, str, str, str, dict[int, Any]]] = []
    for series in series_list:
        region_name = _require_dim_name(series, 'region', 'xtqdbuc')
        ind_name = _require_dim_name(series, 'indicator', 'xtqdbuc')
        unit = series.get('unit') or ''
        scale = series.get('scale')
        if scale is None:
            scale = 1
        if scale not in (1, 1000):
            raise ValueError(
                f'Unexpected scale {scale!r} for xtqdbuc {region_name}/{ind_name}'
            )
        scale_label = 'thousands' if scale == 1000 else '1'
        divisor = float(scale) if scale == 1000 else 1.0
        year_vals = _extract_annual_values(series)
        if not year_vals:
            continue
        scaled_vals: dict[int, float] = {}
        for y, val in year_vals.items():
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise ValueError(f'Non-numeric value {val!r} for xtqdbuc '
                                 f'{region_name}/{ind_name} year={y} '
                                 f'(tsKey={series.get("tsKey")})')
            scaled_vals[y] = val / divisor
        all_years.update(scaled_vals.keys())
        records.append((region_name, ind_name, unit, scale_label, scaled_vals))

    sorted_years = sorted(all_years)
    headers = ['Region', 'Indicator', 'Units', 'Scale'
              ] + [str(y) for y in sorted_years]
    rows: list[list[str]] = []
    for region_name, ind_name, unit, scale_label, year_vals in records:
        row = [region_name, ind_name, unit, scale_label
              ] + [_format_number(year_vals.get(y)) for y in sorted_years]
        rows.append(row)
    return headers, rows


def transform_teakvke(
        series_list: list[dict[str, Any]]) -> tuple[list[str], list[list[str]]]:
    """Transforms teakvke (Population 2007) into CSV with combined mapper column."""
    all_years: set[int] = set()
    records: list[tuple[str, str, str, str, str, dict[int, Any]]] = []
    for series in series_list:
        region_name = _require_dim_name(series, 'region', 'teakvke')
        var_name = _require_dim_name(series, 'variable', 'teakvke')
        residence = _require_dim_name(series, 'residence', 'teakvke')
        mapper = f'{var_name} {residence}'
        unit = series.get('unit') or 'Persons'
        year_vals = _extract_annual_values(series)
        if not year_vals:
            continue
        all_years.update(year_vals.keys())
        records.append(
            (region_name, var_name, residence, mapper, unit, year_vals))

    sorted_years = sorted(all_years)
    headers = ['Region', 'Variable', 'Residence', 'mapper', 'Units'
              ] + [str(y) for y in sorted_years]
    rows: list[list[str]] = []
    for region_name, var_name, residence, mapper, unit, year_vals in records:
        row = [region_name, var_name, residence, mapper, unit
              ] + [_format_number(year_vals.get(y)) for y in sorted_years]
        rows.append(row)
    return headers, rows


def transform_xpcyhcf(
        series_list: list[dict[str, Any]]) -> tuple[list[str], list[list[str]]]:
    """Transforms xpcyhcf (Population Projection 2022) into pivoted Sex x Area CSV."""
    areas_order: list[str] = []
    sexes_order: list[str] = []
    years_seen: set[int] = set()
    table: dict[tuple[str, str], Any] = {}

    for series in series_list:
        sex_name = _require_dim_name(series, 'sex', 'xpcyhcf')
        area_name = _require_dim_name(series, 'area', 'xpcyhcf')
        year_vals = _extract_annual_values(series)
        if not year_vals:
            continue
        if area_name not in areas_order:
            areas_order.append(area_name)
        if sex_name not in sexes_order:
            sexes_order.append(sex_name)
        years_seen.update(year_vals.keys())
        if 2022 in year_vals:
            table[(sex_name, area_name)] = year_vals[2022]

    extra_years = sorted(y for y in years_seen if y != 2022)
    if extra_years:
        logging.warning(
            'Dataset xpcyhcf contains additional years beyond 2022: %s. '
            'The existing 2022 pvmap only maps observationDate=2022.',
            extra_years,
        )
    if 2022 not in years_seen:
        raise RuntimeError(
            f'Expected year 2022 in xpcyhcf data, found years: {sorted(years_seen)}'
        )

    headers = [''] + areas_order
    rows: list[list[str]] = []
    for sex_name in sexes_order:
        row = [sex_name] + [
            _format_number(table.get((sex_name, area))) for area in areas_order
        ]
        rows.append(row)
    return headers, rows


def transform_yusibcg(
        series_list: list[dict[str, Any]]) -> tuple[list[str], list[list[str]]]:
    """Transforms yusibcg (DHS 2014) into SDMX-style long CSV format."""
    headers = [
        'REGION',
        'ID_REGION',
        'REGIONID_REGION',
        'VARIABLE',
        'ID_VARIABLE',
        'UNIT_VARIABLE',
        'WEALTH_INDEX',
        'ID_WEALTH_X0020_INDEX',
        'AGE',
        'ID_AGE',
        'SEX',
        'ID_SEX',
        'FREQ',
        'TIME_PERIOD',
        'OBS_VALUE',
    ]
    rows: list[list[str]] = []
    for series in series_list:
        region = _require_dim_dict(series, 'region', 'yusibcg')
        variable = _require_dim_dict(series, 'variable', 'yusibcg')
        wealth = _require_dim_dict(series, 'wealth-index', 'yusibcg')
        age = _require_dim_dict(series, 'age', 'yusibcg')
        sex = _require_dim_dict(series, 'sex', 'yusibcg')

        region_id = region.get('id') or ''
        region_iso = region.get('RegionId') or ''
        var_id = variable.get('id') or ''
        unit = variable.get('unit') or series.get('unit') or ''
        wealth_id = wealth.get('id') or ''
        age_id = age.get('id') or ''
        sex_id = sex.get('id') or ''
        freq = series.get('frequency') or 'A'

        year_vals = _extract_annual_values(series)
        for year in sorted(year_vals.keys()):
            val_str = _format_number(year_vals[year])
            if not val_str:
                continue
            rows.append([
                region_id,
                region_id,
                region_iso,
                var_id,
                var_id,
                unit,
                wealth_id,
                wealth_id,
                age_id,
                age_id,
                sex_id,
                sex_id,
                freq,
                str(year),
                val_str,
            ])
    return headers, rows


TRANSFORMERS = {
    'udghlsf': transform_udghlsf,
    'xtqdbuc': transform_xtqdbuc,
    'teakvke': transform_teakvke,
    'xpcyhcf': transform_xpcyhcf,
    'yusibcg': transform_yusibcg,
}


def download_and_transform_dataset(
    dataset_id: str,
    raw_dir: str,
    output_dir: str,
    timeout: int = 60,
    retries: int = 3,
    retry_secs: int = 5,
) -> str:
    """Downloads one dataset, saves raw JSON, and writes normalized CSV."""
    if dataset_id not in TRANSFORMERS:
        raise ValueError(f'Unsupported dataset_id {dataset_id!r}. '
                         f'Expected one of {sorted(TRANSFORMERS.keys())}.')

    raw_payload = fetch_dataset_raw(
        dataset_id=dataset_id,
        timeout=timeout,
        retries=retries,
        retry_secs=retry_secs,
    )

    raw_path = os.path.join(raw_dir, f'{dataset_id}_raw.json')
    raw_json_record = {
        'dataset_id': raw_payload['dataset_id'],
        'metadata': raw_payload['metadata'],
        'dimensions': raw_payload['dimensions'],
        'pages': raw_payload['pages'],
    }
    _atomic_write_text(raw_path, json.dumps(raw_json_record, indent=2))
    logging.info('Saved raw source response to %s', raw_path)

    headers, rows = TRANSFORMERS[dataset_id](raw_payload['series'])
    if not rows:
        raise RuntimeError(
            f'Transformation produced zero CSV rows for dataset {dataset_id}.')

    csv_path = os.path.join(output_dir, DATASET_OUTPUT_FILENAMES[dataset_id])
    _atomic_write_csv(csv_path, headers, rows)
    logging.info('Wrote %d rows to %s', len(rows), csv_path)
    return csv_path


def download_all(
    dataset_ids: list[str],
    raw_dir: str,
    output_dir: str,
    timeout: int = 60,
    retries: int = 3,
    retry_secs: int = 5,
) -> dict[str, str]:
    """Downloads and transforms all specified Ethiopia Statistics datasets."""
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    outputs: dict[str, str] = {}
    for dataset_id in dataset_ids:
        ds = dataset_id.strip()
        if not ds:
            continue
        outputs[ds] = download_and_transform_dataset(
            dataset_id=ds,
            raw_dir=raw_dir,
            output_dir=output_dir,
            timeout=timeout,
            retries=retries,
            retry_secs=retry_secs,
        )
    if not outputs:
        raise RuntimeError('No datasets were specified for download.')
    return outputs


def main(argv: list[str]) -> None:
    del argv
    logging.set_verbosity(logging.INFO)
    outputs = download_all(
        dataset_ids=list(_FLAGS.datasets),
        raw_dir=_FLAGS.raw_dir,
        output_dir=_FLAGS.output_dir,
        timeout=_FLAGS.timeout,
        retries=_FLAGS.retries,
        retry_secs=_FLAGS.retry_secs,
    )
    logging.info('Completed download for %d datasets: %s', len(outputs),
                 sorted(outputs.keys()))


if __name__ == '__main__':
    _define_flags()
    app.run(main)
