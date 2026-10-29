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
"""Downloads and merges MoSPI eSankhyiki PLFS Daily Wages data.

Loads the historical baseline CSV staged in GCS and merges it with live records
from the official MoSPI eSankhyiki PLFS REST API so new releases are ingested
automatically while preserving all historical observations.
"""

import os
import ssl
import sys
import tempfile
import time
from typing import Any

from absl import app
from absl import flags
from absl import logging
import pandas as pd
import requests
from requests.adapters import HTTPAdapter

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..', '..', '..'))
if os.path.join(_REPO_ROOT, 'util') not in sys.path:
    sys.path.append(os.path.join(_REPO_ROOT, 'util'))

import file_util  # pylint: disable=wrong-import-position

DEFAULT_API_URL = 'https://api.mospi.gov.in/api/plfs/getData'
DEFAULT_GCS_BASELINE = (
    'gs://unresolved_mcf/india_mospi/daily_wages/input_files/daily_wages_input.csv'
)
DEFAULT_OUTPUT_FILE = os.path.join(_SCRIPT_DIR, 'input_files',
                                   'daily_wages_input.csv')

# MoSPI PLFS indicator_code=7:
# "Average wage earnings (Rs. 0.00) per day from casual labour work other than public works"
INDICATOR_CODE = 7
FREQUENCY_CODE = 1
YEAR_TYPE_CODES = '1,2'
MAX_PAGE_SIZE = 200

COLUMNS = [
    'year_type',
    'year',
    'frequency',
    'indicator',
    'state',
    'gender',
    'sector',
    'quarter',
    'month',
    'value',
    'unit',
]

KEY_COLUMNS = [
    'year_type',
    'year',
    'frequency',
    'indicator',
    'state',
    'gender',
    'sector',
    'quarter',
    'month',
]

_RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

FLAGS = flags.FLAGS
flags.DEFINE_string('api_url', DEFAULT_API_URL,
                    'MoSPI eSankhyiki PLFS getData REST endpoint.')
flags.DEFINE_string(
    'gcs_baseline_path',
    DEFAULT_GCS_BASELINE,
    'GCS URI (or local path) of the staged historical baseline CSV.',
)
flags.DEFINE_string('output_file', DEFAULT_OUTPUT_FILE,
                    'Destination CSV path for merged raw input data.')
flags.DEFINE_integer('page_size', MAX_PAGE_SIZE,
                     'Records per API page (MoSPI enforces <= 200).')
flags.DEFINE_integer('timeout_seconds', 30, 'Per-request HTTP timeout.')
flags.DEFINE_integer(
    'max_retries', 3,
    'Maximum retry attempts for transient HTTP/network errors.')
flags.DEFINE_float('retry_delay_seconds', 5.0,
                   'Initial backoff delay in seconds between retries.')
flags.DEFINE_float('retry_backoff', 2.0,
                   'Exponential backoff multiplier between retry attempts.')
flags.DEFINE_bool(
    'skip_live_api',
    False,
    'If true, only stage the GCS baseline without querying the live MoSPI API.',
)


class _LegacyTLSAdapter(HTTPAdapter):
    """HTTPS adapter enabling OpenSSL OP_LEGACY_SERVER_CONNECT for api.mospi.gov.in.

    Keeps full certificate and hostname verification enabled while permitting
    legacy renegotiation required by MoSPI's upstream TLS terminator.
    """

    @staticmethod
    def _build_ssl_context() -> ssl.SSLContext:
        ctx = ssl.create_default_context()
        ctx.options |= getattr(ssl, 'OP_LEGACY_SERVER_CONNECT', 0x4)
        return ctx

    def init_poolmanager(self, *args: Any, **kwargs: Any) -> Any:
        kwargs['ssl_context'] = self._build_ssl_context()
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args: Any, **kwargs: Any) -> Any:
        kwargs['ssl_context'] = self._build_ssl_context()
        return super().proxy_manager_for(*args, **kwargs)


def create_session() -> requests.Session:
    """Creates a requests.Session configured for MoSPI eSankhyiki HTTPS calls."""
    session = requests.Session()
    session.mount('https://', _LegacyTLSAdapter())
    return session


def _fetch_page(
    session: requests.Session,
    api_url: str,
    params: dict[str, Any],
    timeout_seconds: int = 30,
    max_retries: int = 3,
    retry_delay_seconds: float = 5.0,
    retry_backoff: float = 2.0,
) -> dict[str, Any]:
    """Fetches one JSON page from MoSPI PLFS API with bounded retries."""
    delay = retry_delay_seconds
    for attempt in range(1, max_retries + 1):
        logging.info('GET %s params=%s (attempt %d/%d)', api_url, params,
                     attempt, max_retries)
        try:
            response = session.get(api_url,
                                   params=params,
                                   timeout=timeout_seconds)
            if response.status_code in _RETRYABLE_STATUS_CODES:
                raise requests.HTTPError(
                    f'Retryable HTTP {response.status_code} from {api_url}',
                    response=response,
                )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError(
                    f'Expected JSON object from {api_url}, got {type(payload).__name__}'
                )
            if payload.get('statusCode') is False:
                raise RuntimeError(
                    f'MoSPI API returned statusCode=False for params={params}: '
                    f"{payload.get('msg')}")
            return payload
        except (requests.Timeout, requests.ConnectionError) as exc:
            if attempt >= max_retries:
                raise RuntimeError(
                    f'Exhausted {max_retries} attempts fetching {api_url} '
                    f'params={params}') from exc
            logging.warning(
                'Transient network error on %s params=%s (%s); retrying in %.1fs',
                api_url, params, exc, delay)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status not in _RETRYABLE_STATUS_CODES or attempt >= max_retries:
                raise
            logging.warning(
                'Transient HTTP %s on %s params=%s; retrying in %.1fs', status,
                api_url, params, delay)
        time.sleep(delay)
        delay *= retry_backoff
    raise RuntimeError(f'Unreachable retry state for {api_url}')


def fetch_mospi_daily_wages(
    session: requests.Session,
    api_url: str = DEFAULT_API_URL,
    page_size: int = MAX_PAGE_SIZE,
    timeout_seconds: int = 30,
    max_retries: int = 3,
    retry_delay_seconds: float = 5.0,
    retry_backoff: float = 2.0,
) -> pd.DataFrame:
    """Downloads all PLFS daily wages pages from MoSPI eSankhyiki API."""
    if page_size <= 0 or page_size > MAX_PAGE_SIZE:
        raise ValueError(
            f'page_size must be in 1..{MAX_PAGE_SIZE}, got {page_size}')

    all_rows: list[dict[str, str]] = []
    page = 1
    total_pages = 1
    expected_total_records: int | None = None

    while page <= total_pages:
        params = {
            'indicator_code': INDICATOR_CODE,
            'frequency_code': FREQUENCY_CODE,
            'year_type_code': YEAR_TYPE_CODES,
            'limit': page_size,
            'page': page,
            'Format': 'JSON',
        }
        payload = _fetch_page(
            session=session,
            api_url=api_url,
            params=params,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
            retry_backoff=retry_backoff,
        )
        records = payload.get('data')
        meta = payload.get('meta_data')
        if not isinstance(records, list) or not isinstance(meta, dict):
            raise RuntimeError(
                f'Malformed MoSPI API payload on page {page}: missing data/meta_data'
            )

        if expected_total_records is None:
            expected_total_records = int(meta.get('totalRecords', 0))
            total_pages = int(meta.get('totalPages', 0))
            if expected_total_records <= 0 or total_pages <= 0:
                raise RuntimeError(
                    f'MoSPI API returned zero records: meta_data={meta}')
            logging.info(
                'MoSPI PLFS API reported totalRecords=%d across %d pages',
                expected_total_records, total_pages)

        if not records:
            raise RuntimeError(
                f'MoSPI API returned empty data list on page {page}/{total_pages}'
            )

        for item in records:
            missing_cols = [col for col in COLUMNS if col not in item]
            if missing_cols:
                raise RuntimeError(
                    f'MoSPI API record on page {page} missing columns {missing_cols}'
                )
            all_rows.append({
                col: '' if item[col] is None else str(item[col])
                for col in COLUMNS
            })
        page += 1

    if expected_total_records is not None and len(
            all_rows) != expected_total_records:
        raise RuntimeError(
            f'Fetched record count ({len(all_rows)}) does not match '
            f'meta_data.totalRecords ({expected_total_records})')

    logging.info('Successfully fetched %d live records from MoSPI API.',
                 len(all_rows))
    return pd.DataFrame(all_rows, columns=COLUMNS, dtype=str)


def load_baseline_csv(baseline_path: str) -> pd.DataFrame:
    """Loads the historical baseline CSV from GCS or local disk."""
    logging.info('Loading historical baseline CSV from %s', baseline_path)
    matching = file_util.file_get_matching(baseline_path)
    if not matching:
        raise FileNotFoundError(
            f'Baseline CSV not found at path: {baseline_path}')
    with file_util.FileIO(matching[0], 'r') as csv_file:
        df = pd.read_csv(csv_file, dtype=str, keep_default_na=False)
    missing = [col for col in COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f'Baseline CSV {baseline_path} missing required columns: {missing}')
    if df.empty:
        raise ValueError(f'Baseline CSV {baseline_path} is empty.')
    logging.info('Loaded %d historical baseline rows from %s', len(df),
                 matching[0])
    return df[COLUMNS].copy()


def merge_records(baseline_df: pd.DataFrame,
                  live_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Merges live MoSPI records over historical baseline without losing keys."""
    if live_df is None or live_df.empty:
        merged = baseline_df[COLUMNS].drop_duplicates(subset=KEY_COLUMNS,
                                                      keep='last')
        return merged.reset_index(drop=True)

    combined = pd.concat([baseline_df[COLUMNS], live_df[COLUMNS]],
                         ignore_index=True)
    merged = combined.drop_duplicates(subset=KEY_COLUMNS, keep='last')
    return merged.reset_index(drop=True)


def write_csv_atomically(df: pd.DataFrame, output_file: str) -> None:
    """Writes DataFrame to output_file atomically via temp file + os.replace."""
    output_dir = os.path.dirname(os.path.abspath(output_file))
    os.makedirs(output_dir, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w',
                                         encoding='utf-8',
                                         newline='',
                                         dir=output_dir,
                                         prefix='.daily_wages_tmp_',
                                         suffix='.csv',
                                         delete=False) as tmp_file:
            tmp_path = tmp_file.name
            df.to_csv(tmp_file, index=False)
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, output_file)
        logging.info('Wrote %d merged rows atomically to %s', len(df),
                     output_file)
    except Exception:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def run_download(
    gcs_baseline_path: str = DEFAULT_GCS_BASELINE,
    api_url: str = DEFAULT_API_URL,
    output_file: str = DEFAULT_OUTPUT_FILE,
    page_size: int = MAX_PAGE_SIZE,
    timeout_seconds: int = 30,
    max_retries: int = 3,
    retry_delay_seconds: float = 5.0,
    retry_backoff: float = 2.0,
    skip_live_api: bool = False,
) -> pd.DataFrame:
    """Executes baseline load, live MoSPI API fetch, merge, and atomic write."""
    baseline_df = load_baseline_csv(gcs_baseline_path)
    live_df = None
    if not skip_live_api:
        with create_session() as session:
            live_df = fetch_mospi_daily_wages(
                session=session,
                api_url=api_url,
                page_size=page_size,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                retry_delay_seconds=retry_delay_seconds,
                retry_backoff=retry_backoff,
            )
    merged_df = merge_records(baseline_df, live_df)
    write_csv_atomically(merged_df, output_file)
    return merged_df


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError(f'Unexpected positional arguments: {argv[1:]}')
    run_download(
        gcs_baseline_path=FLAGS.gcs_baseline_path,
        api_url=FLAGS.api_url,
        output_file=FLAGS.output_file,
        page_size=FLAGS.page_size,
        timeout_seconds=FLAGS.timeout_seconds,
        max_retries=FLAGS.max_retries,
        retry_delay_seconds=FLAGS.retry_delay_seconds,
        retry_backoff=FLAGS.retry_backoff,
        skip_live_api=FLAGS.skip_live_api,
    )


if __name__ == '__main__':
    app.run(main)
