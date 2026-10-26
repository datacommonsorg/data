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
import math
import os
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from absl import app
from absl import flags
from absl import logging
from google.cloud import storage
import pandas as pd
import requests

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

_DEFAULT_RETRY_TRIES = 3
_DEFAULT_RETRY_DELAY_SECONDS = 5.0
_DEFAULT_RETRY_BACKOFF = 2.0
_DEFAULT_REQUEST_TIMEOUT_SECONDS = 30
_NON_RETRYABLE_REQUEST_EXCEPTIONS = (
    requests.exceptions.MissingSchema,
    requests.exceptions.InvalidSchema,
    requests.exceptions.InvalidURL,
    requests.exceptions.InvalidHeader,
)


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
    if not path or not path.strip():
        raise ValueError('Configuration path must be non-empty.')
    if path.startswith('gs://'):
        parts = urlsplit(path)
        bucket_name = parts.netloc.strip()
        blob_name = parts.path.lstrip('/')
        if not bucket_name or not blob_name or blob_name.endswith('/'):
            raise ValueError(
                'Invalid GCS configuration URI (expected gs://<bucket>/<object>): '
                f'{_sanitize_url(path)}')
        client = storage.Client()
        blob = client.bucket(bucket_name).blob(blob_name)
        return json.loads(blob.download_as_text())
    return file_util.file_load_py_dict(path)


def normalize_datasets_config(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalizes download_config.json into a list of dataset specifications."""
    if not isinstance(config, dict):
        raise ValueError('Configuration payload must be a JSON object.')

    if 'datasets' in config:
        if not isinstance(config['datasets'], list):
            raise ValueError("'datasets' in configuration must be a list.")
        return config['datasets']

    input_files_dir = config.get('input_files', 'input_files/')
    state_pop_url = (config.get('state_population_url') or
                     config.get('url_7208'))
    urban_pop_url = (config.get('state_urban_population_url') or
                     config.get('url_7209'))

    if (not state_pop_url or not urban_pop_url) and isinstance(
            config.get('url'), list):
        for u in config['url']:
            if not isinstance(u, str):
                continue
            if not state_pop_url and '7208' in u:
                state_pop_url = u
            elif not urban_pop_url and '7209' in u:
                urban_pop_url = u

    state_pop_url = (state_pop_url.strip()
                     if isinstance(state_pop_url, str) else '')
    urban_pop_url = (urban_pop_url.strip()
                     if isinstance(urban_pop_url, str) else '')

    missing_datasets: List[str] = []
    if not state_pop_url:
        missing_datasets.append('state_population_url (dataset 7208)')
    if not urban_pop_url:
        missing_datasets.append('state_urban_population_url (dataset 7209)')
    if missing_datasets:
        raise ValueError(
            'Missing required dataset URL(s) in download configuration: ' +
            ', '.join(missing_datasets))

    return [
        {
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
        },
        {
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
        },
    ]


def _is_missing_dimension(val: Any) -> bool:
    """Returns True if a required dimension field is null, blank, or non-scalar."""
    if val is None or isinstance(val, (bool, dict, list)):
        return True
    if isinstance(val, str):
        return not val.strip()
    return False


def _extract_indicator_value(raw_val: Any) -> Optional[Any]:
    """Unwraps NDAP indicator value objects into a validated numeric scalar."""
    val = raw_val
    if isinstance(raw_val, dict):
        val = None
        for key in ('TotalPopulationWeight', 'avg', 'value', 'sum'):
            if key in raw_val and raw_val[key] is not None:
                val = raw_val[key]
                break
    if val is None or isinstance(val, (bool, dict, list)):
        return None
    if isinstance(val, str):
        stripped = val.strip()
        if not stripped:
            return None
        try:
            numeric = float(stripped)
        except ValueError:
            return None
        if not math.isfinite(numeric):
            return None
        return int(numeric) if numeric.is_integer() else numeric
    if isinstance(val, (int, float)):
        if isinstance(val, float):
            if not math.isfinite(val):
                return None
            if val.is_integer():
                return int(val)
        return val
    return None


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


def _is_retryable_request_exception(
    exc: requests.exceptions.RequestException,) -> bool:
    """Returns True when a RequestException is transient and should be retried."""
    if isinstance(exc, _NON_RETRYABLE_REQUEST_EXCEPTIONS):
        return False
    if isinstance(exc, requests.exceptions.HTTPError):
        resp = getattr(exc, 'response', None)
        status_code = (getattr(resp, 'status_code', None)
                       if resp is not None else None)
        if isinstance(status_code, int):
            return status_code in (408, 429) or 500 <= status_code < 600
    return True


def _format_request_error(exc: requests.exceptions.RequestException) -> str:
    """Formats a credential-safe summary of a requests exception."""
    err_type = type(exc).__name__
    resp = getattr(exc, 'response', None)
    status_code = (getattr(resp, 'status_code', None)
                   if resp is not None else None)
    if isinstance(status_code, int):
        return f'{err_type} (HTTP {status_code})'
    return err_type


def _fetch_page_json(
    session: requests.Session,
    api_url: str,
    sanitized_url: str,
    dataset_name: str,
    page_num: int,
    tries: int = _DEFAULT_RETRY_TRIES,
    delay: float = _DEFAULT_RETRY_DELAY_SECONDS,
    backoff: float = _DEFAULT_RETRY_BACKOFF,
    timeout: int = _DEFAULT_REQUEST_TIMEOUT_SECONDS,
) -> Any:
    """Fetches and decodes one JSON page with bounded retries and safe logging."""
    max_attempts = max(1, tries)
    current_delay = delay
    failure_message: Optional[str] = None

    for attempt in range(1, max_attempts + 1):
        logging.info(
            'Fetching %s page %d (attempt %d/%d) from GET %s',
            dataset_name,
            page_num,
            attempt,
            max_attempts,
            sanitized_url,
        )
        try:
            response = session.get(api_url, stream=False, timeout=timeout)
            response.raise_for_status()
            try:
                return response.json()
            except ValueError as exc:
                failure_message = (
                    f'Failed to parse JSON for {dataset_name} on page '
                    f'{page_num} from {sanitized_url}: {type(exc).__name__}')
                break
        except requests.exceptions.RequestException as exc:
            error_summary = _format_request_error(exc)
            should_retry = (attempt < max_attempts and
                            _is_retryable_request_exception(exc))
            if not should_retry:
                failure_message = (
                    f'Failed to retrieve data for {dataset_name} on page '
                    f'{page_num} from {sanitized_url} after {attempt} '
                    f'attempt(s): {error_summary}')
                break
            logging.warning(
                'Transient error fetching %s page %d (attempt %d/%d) from '
                'GET %s (%s); retrying in %.1fs.',
                dataset_name,
                page_num,
                attempt,
                max_attempts,
                sanitized_url,
                error_summary,
                current_delay,
            )
            time.sleep(current_delay)
            current_delay *= backoff

    raise RuntimeError(
        failure_message or
        f'Failed to retrieve data for {dataset_name} on page {page_num} '
        f'from {sanitized_url}') from None


def download_dataset(
    dataset_cfg: Dict[str, Any],
    session: Optional[requests.Session] = None,
) -> List[Tuple[Any, ...]]:
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

    owns_session = session is None
    active_session = requests.Session() if owns_session else session
    try:
        while True:
            api_url = _build_paginated_url(url, page_num)
            sanitized_url = _sanitize_url(api_url)
            response_data = _fetch_page_json(
                session=active_session,
                api_url=api_url,
                sanitized_url=sanitized_url,
                dataset_name=dataset_name,
                page_num=page_num,
            )

            if not isinstance(response_data, dict):
                raise RuntimeError(
                    f'Unexpected JSON payload type for {dataset_name} on page '
                    f'{page_num}')

            records = response_data.get('Data')
            if not records:
                logging.info('No more records on page %d for %s.', page_num,
                             dataset_name)
                break

            if not isinstance(records, list):
                raise RuntimeError(
                    f"Expected 'Data' to be a list for {dataset_name} on page "
                    f'{page_num}')

            page_hash = _hash_records(records)
            if page_hash in seen_page_hashes:
                logging.info(
                    'Duplicate page %d detected for %s; stopping pagination.',
                    page_num, dataset_name)
                break
            seen_page_hashes.add(page_hash)

            if not isinstance(records[0], dict):
                raise RuntimeError(
                    f'Expected record items to be objects for {dataset_name} '
                    f'on page {page_num}')

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
                if not isinstance(item, dict):
                    raise RuntimeError(
                        f'Expected record item to be an object for '
                        f'{dataset_name} on page {page_num}')
                raw_country = item.get('Country')
                country = (raw_country.strip()
                           if isinstance(raw_country, str) and
                           raw_country.strip() else 'India')
                state = item.get('StateName')
                if _is_missing_dimension(state):
                    state = item.get('State')
                year = item.get('Year')
                gender = item.get(gender_key)
                raw_val = item.get(value_key)
                extracted_val = _extract_indicator_value(raw_val)
                if (_is_missing_dimension(state) or
                        _is_missing_dimension(year) or
                        _is_missing_dimension(gender) or extracted_val is None):
                    raise RuntimeError(
                        f'Missing or invalid required fields in record for '
                        f'{dataset_name} on page {page_num}: state={state!r}, '
                        f'year={year!r}, gender={gender!r}, value={raw_val!r}')
                rows.append((
                    country,
                    state,
                    year,
                    gender,
                    extracted_val,
                ))

            page_num += 1
    finally:
        if owns_session:
            active_session.close()

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

    temp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                newline='',
                dir=output_dir,
                suffix='.tmp.csv',
                delete=False,
        ) as tmp_file:
            temp_path = tmp_file.name
            df.to_csv(tmp_file, index=False)
        os.replace(temp_path, output_path)
    except BaseException:
        if temp_path and os.path.exists(temp_path):
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

    session = requests.Session()
    try:
        for dataset_cfg in datasets:
            rows = download_dataset(dataset_cfg, session=session)
            save_dataset(rows, dataset_cfg)
    finally:
        session.close()


if __name__ == '__main__':
    app.run(main)
