# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Downloads NITI India Population Projection datasets (7208 & 7209) from NDAP API."""

import hashlib
import json
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from absl import app
from absl import flags
from absl import logging
from google.cloud import storage
import pandas as pd

_FLAGS = flags.FLAGS

_DEFAULT_CONFIG_PATH = (
    'gs://unresolved_mcf/india_ndap/niti_india_population_projection/download_config.json'
)

flags.DEFINE_string(
    'download_config_path',
    _DEFAULT_CONFIG_PATH,
    'GCS or local path to download_config.json.',
)
flags.DEFINE_string(
    'config_file_path',
    None,
    'Optional alias for --download_config_path.',
)

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

_STATE_POP_COLUMN = 'Projected Population (UOM:Number), Scaling Factor:1000'
_URBAN_POP_COLUMN = (
    'Projected Urban Population (UOM:Number), Scaling Factor:1000')

_SENSITIVE_QUERY_KEYS = frozenset({
    'api_key',
    'apikey',
    'key',
    'token',
    'access_token',
})


def _add_util_to_path() -> None:
    """Adds the repository 'util' directory to sys.path dynamically."""
    curr = _SCRIPT_PATH
    for _ in range(5):
        potential = os.path.join(curr, 'util')
        if os.path.exists(os.path.join(potential, 'file_util.py')):
            if potential not in sys.path:
                sys.path.append(potential)
            return
        curr = os.path.dirname(curr)
    logging.error("Could not find 'util' directory containing file_util.py")


_add_util_to_path()

try:
    from download_util_script import _retry_method
    import file_util
except ImportError as e:
    logging.fatal('Import Error: Could not find utility scripts: %s', e)


def _sanitize_url(url: str) -> str:
    """Redacts sensitive query parameters such as API_Key from a URL before logging."""
    try:
        parts = urlsplit(url)
        query_items = parse_qsl(parts.query, keep_blank_values=True)
        redacted_items = [
            (k, 'REDACTED' if k.lower() in _SENSITIVE_QUERY_KEYS else v)
            for k, v in query_items
        ]
        return urlunsplit((
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(redacted_items, safe=','),
            parts.fragment,
        ))
    except Exception:
        return '<redacted_url>'


def _build_paginated_url(base_url: str, page_num: int) -> str:
    """Sets or replaces the pageno query parameter on base_url."""
    clean_url = ''.join(base_url.split())
    parts = urlsplit(clean_url)
    query_items = [(k, v)
                   for k, v in parse_qsl(parts.query, keep_blank_values=True)
                   if k.lower() != 'pageno']
    query_items.append(('pageno', str(page_num)))
    return urlunsplit((
        parts.scheme,
        parts.netloc,
        parts.path,
        urlencode(query_items, safe=','),
        parts.fragment,
    ))


def load_config(path: str) -> Dict[str, Any]:
    """Loads configuration JSON from GCS or local disk."""
    if path.startswith('gs://'):
        client = storage.Client()
        bucket_name = path.split('/')[2]
        blob_name = '/'.join(path.split('/')[3:])
        blob = client.bucket(bucket_name).blob(blob_name)
        return json.loads(blob.download_as_text())
    return file_util.file_load_py_dict(path)


def normalize_datasets_config(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalizes download_config.json into a list of dataset specifications."""
    if 'datasets' in config and isinstance(config['datasets'], list):
        return config['datasets']

    input_files_dir = config.get('input_files', 'input_files/')
    state_pop_url = (config.get('state_population_url') or
                     config.get('url_7208'))
    urban_pop_url = (config.get('state_urban_population_url') or
                     config.get('url_7209'))

    if not state_pop_url and not urban_pop_url and isinstance(
            config.get('url'), list):
        for u in config['url']:
            if '7208' in u:
                state_pop_url = u
            elif '7209' in u:
                urban_pop_url = u

    datasets: List[Dict[str, Any]] = []
    if state_pop_url:
        datasets.append({
            'name':
                'state_population',
            'url':
                state_pop_url,
            'output_file':
                config.get(
                    'state_population_output_file',
                    os.path.join(input_files_dir,
                                 'india_state_population_input.csv'),
                ),
            'gender_key':
                config.get('state_population_gender_key', 'D7208_3'),
            'value_key':
                config.get('state_population_value_key', 'I7208_4'),
            'value_column':
                _STATE_POP_COLUMN,
        })
    if urban_pop_url:
        datasets.append({
            'name':
                'state_urban_population',
            'url':
                urban_pop_url,
            'output_file':
                config.get(
                    'state_urban_population_output_file',
                    os.path.join(input_files_dir,
                                 'india_state_urban_population_input.csv'),
                ),
            'gender_key':
                config.get('state_urban_population_gender_key', 'D7209_3'),
            'value_key':
                config.get('state_urban_population_value_key', 'I7209_4'),
            'value_column':
                _URBAN_POP_COLUMN,
        })
    return datasets


def _extract_indicator_value(raw_val: Any) -> Any:
    """Unwraps NDAP indicator value objects (e.g., TotalPopulationWeight or avg)."""
    val = raw_val
    if isinstance(raw_val, dict):
        for key in ('TotalPopulationWeight', 'avg', 'value', 'sum'):
            if key in raw_val and raw_val[key] is not None:
                val = raw_val[key]
                break
    if isinstance(val, float) and val.is_integer():
        return int(val)
    return val


def _resolve_keys_from_headers(
    headers: Optional[Dict[str, Any]],
    sample_item: Dict[str, Any],
    configured_gender_key: Optional[str],
    configured_value_key: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """Resolves gender dimension key and indicator key from config, Headers, or item keys."""
    gender_key = (configured_gender_key
                  if configured_gender_key in sample_item else None)
    value_key = (configured_value_key
                 if configured_value_key in sample_item else None)

    if headers and isinstance(headers.get('Items'), list):
        for item in headers['Items']:
            item_id = item.get('ID')
            display_name = str(item.get('DisplayName', '')).strip().lower()
            ind_dim = item.get('indicator_dimension')
            if not gender_key and (display_name == 'gender' or
                                   (ind_dim == 'Dimension' and
                                    'gender' in display_name)):
                gender_key = item_id
            if not value_key and ind_dim == 'Indicator':
                value_key = item_id

    if not gender_key:
        if 'Gender' in sample_item:
            gender_key = 'Gender'
        else:
            d_keys = sorted(k for k in sample_item if k.startswith('D'))
            if d_keys:
                gender_key = d_keys[0]

    if not value_key:
        for col in (_STATE_POP_COLUMN, _URBAN_POP_COLUMN):
            if col in sample_item:
                value_key = col
                break
        if not value_key:
            i_keys = sorted(k for k in sample_item if k.startswith('I'))
            if i_keys:
                value_key = i_keys[0]

    return gender_key, value_key


def _hash_records(records: List[Dict[str, Any]]) -> str:
    """Computes a deterministic MD5 hash for a page of records to detect duplicate pages."""
    digest = hashlib.md5()
    for rec in records:
        serialized = json.dumps(rec, sort_keys=True, default=str)
        digest.update(serialized.encode('utf-8'))
    return digest.hexdigest()


def download_dataset(dataset_cfg: Dict[str, Any]) -> List[Tuple[Any, ...]]:
    """Downloads all paginated rows for one NDAP dataset specification."""
    dataset_name = dataset_cfg.get('name', 'unknown_dataset')
    url = dataset_cfg.get('url')
    if not url:
        raise ValueError(f'Missing URL in dataset config for {dataset_name}')

    rows: List[Tuple[Any, ...]] = []
    seen_page_hashes = set()
    page_num = 1
    gender_key = dataset_cfg.get('gender_key')
    value_key = dataset_cfg.get('value_key')

    while True:
        api_url = _build_paginated_url(url, page_num)
        sanitized_url = _sanitize_url(api_url)
        logging.info('Fetching %s page %d from GET %s', dataset_name, page_num,
                     sanitized_url)

        response = _retry_method(api_url, None, 3, 5, 2)
        if not response:
            raise RuntimeError(
                f'Failed to retrieve data for {dataset_name} on page {page_num} '
                f'from {sanitized_url}')

        try:
            response_data = response.json()
        except ValueError as e:
            raise RuntimeError(
                f'Failed to parse JSON for {dataset_name} on page {page_num} '
                f'from {sanitized_url}: {e}') from e

        if not isinstance(response_data, dict):
            raise RuntimeError(
                f'Unexpected JSON payload type for {dataset_name} on page {page_num}'
            )

        records = response_data.get('Data')
        if not records:
            logging.info('No more records on page %d for %s.', page_num,
                         dataset_name)
            break

        if not isinstance(records, list):
            raise RuntimeError(
                f"Expected 'Data' to be a list for {dataset_name} on page {page_num}"
            )

        page_hash = _hash_records(records)
        if page_hash in seen_page_hashes:
            logging.info(
                'Duplicate page %d detected for %s; stopping pagination.',
                page_num, dataset_name)
            break
        seen_page_hashes.add(page_hash)

        gender_key, value_key = _resolve_keys_from_headers(
            response_data.get('Headers'),
            records[0],
            gender_key,
            value_key,
        )
        if not gender_key or not value_key:
            raise RuntimeError(
                f'Could not resolve gender_key ({gender_key}) or value_key '
                f'({value_key}) for {dataset_name}')

        for item in records:
            country = item.get('Country', 'India')
            state = item.get('StateName') or item.get('State')
            year = item.get('Year')
            gender = item.get(gender_key)
            raw_val = item.get(value_key)
            if state is None or year is None or gender is None or raw_val is None:
                raise RuntimeError(
                    f'Missing required fields in record for {dataset_name} on '
                    f'page {page_num}: state={state}, year={year}, gender={gender}'
                )
            rows.append((
                country,
                state,
                year,
                gender,
                _extract_indicator_value(raw_val),
            ))

        page_num += 1

    return rows


def save_dataset(rows: List[Tuple[Any, ...]], dataset_cfg: Dict[str,
                                                                Any]) -> str:
    """Atomically writes downloaded rows to the configured output CSV file."""
    dataset_name = dataset_cfg.get('name', 'unknown_dataset')
    if not rows:
        raise RuntimeError(
            f'No data rows were retrieved for dataset {dataset_name}')

    value_column = dataset_cfg.get('value_column', _STATE_POP_COLUMN)
    output_rel_path = dataset_cfg.get(
        'output_file', 'input_files/india_state_population_input.csv')
    output_path = (output_rel_path if os.path.isabs(output_rel_path) else
                   os.path.join(_SCRIPT_PATH, output_rel_path))
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    columns = ['Country', 'State', 'Year', 'Gender', value_column]
    df = pd.DataFrame(rows, columns=columns)

    temp_fd, temp_path = tempfile.mkstemp(dir=output_dir, suffix='.tmp.csv')
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8', newline='') as tmp_file:
            df.to_csv(tmp_file, index=False)
        os.replace(temp_path, output_path)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise

    logging.info('Saved %d rows for %s to %s', len(df), dataset_name,
                 output_path)
    return output_path


def main(_) -> None:
    config_path = _FLAGS.config_file_path or _FLAGS.download_config_path
    config = load_config(config_path)
    datasets = normalize_datasets_config(config)
    if not datasets:
        raise RuntimeError(
            f'No datasets configured in {_sanitize_url(config_path)}')

    for dataset_cfg in datasets:
        rows = download_dataset(dataset_cfg)
        save_dataset(rows, dataset_cfg)


if __name__ == '__main__':
    app.run(main)
