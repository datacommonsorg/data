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
"""Downloads the WHO Adolescent Birth Rate dataset and normalizes values."""

import csv
import os
import re
import tempfile
import time

from absl import app
from absl import flags
from absl import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_BACKOFF_FACTOR = 1.0
DEFAULT_INDICATOR_ID = '27D371A'
DEFAULT_MAX_RETRIES = 3
DEFAULT_OUTPUT_DIR = os.path.join(_SCRIPT_DIR, 'input_files')
DEFAULT_TIMEOUT_SECONDS = 300
OUTPUT_FILENAME = 'adolescent_birth_rate_input.csv'
RATE_COLUMN = 'RATE_PER_1000_N'
RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)
SOURCE_URL_TEMPLATE = (
    'https://srhdpeuwpubsa.blob.core.windows.net/whdh/DATADOT/INDICATOR/'
    '{indicator_id}_ALL_LATEST.csv')

_INT_SCI_RE = re.compile(r'^([+-]?\d+)([eE][+-]?\d+)$')

FLAGS = flags.FLAGS


def _define_flags() -> None:
    """Defines command-line flags for the download script."""
    flags.DEFINE_string(
        'indicator_id',
        DEFAULT_INDICATOR_ID,
        'WHO indicator ID used to construct the source CSV URL.',
        allow_override=True,
    )
    flags.DEFINE_string(
        'input_url',
        '',
        'Optional CSV URL override; defaults to --indicator_id template.',
        allow_override=True,
    )
    flags.DEFINE_string(
        'output_dir',
        DEFAULT_OUTPUT_DIR,
        'Directory where the downloaded CSV will be saved.',
        allow_override=True,
    )


def build_source_url(
    indicator_id: str = DEFAULT_INDICATOR_ID,
    input_url: str = '',
) -> str:
    """Returns the source CSV URL from --input_url or --indicator_id."""
    explicit_url = input_url.strip()
    if explicit_url:
        return explicit_url
    clean_indicator = indicator_id.strip()
    if not clean_indicator:
        raise ValueError(
            'Either non-empty indicator_id or input_url must be provided.')
    return SOURCE_URL_TEMPLATE.format(indicator_id=clean_indicator)


def create_retry_session(
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
) -> requests.Session:
    """Creates a requests.Session with retry/backoff for transient errors."""
    retry_strategy = Retry(
        total=max_retries,
        connect=max_retries,
        read=max_retries,
        status=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=RETRYABLE_STATUS_CODES,
        allowed_methods=frozenset(['GET']),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http_session = requests.Session()
    http_session.mount('https://', adapter)
    http_session.mount('http://', adapter)
    return http_session


def _is_permanent_4xx(err: requests.exceptions.RequestException) -> bool:
    """Returns True for non-429 4xx HTTP errors that must not be retried."""
    if not isinstance(err, requests.exceptions.HTTPError):
        return False
    resp = err.response
    status = resp.status_code if resp is not None else None
    return status is not None and 400 <= status < 500 and status != 429


def _download_to_path(
    http_session: requests.Session,
    source_url: str,
    dest_path: str,
    timeout_seconds: int,
    max_retries: int,
    backoff_factor: float,
) -> None:
    """Streams source_url to dest_path, retrying mid-stream interruptions."""
    total_attempts = max(max_retries, 0) + 1
    for attempt in range(total_attempts):
        headers_received = False
        resp_ctx = http_session.get(
            source_url,
            stream=True,
            timeout=timeout_seconds,
        )
        try:
            with resp_ctx as resp:
                resp.raise_for_status()
                headers_received = True
                with open(dest_path, 'wb') as out_file:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            out_file.write(chunk)
            return
        except requests.exceptions.RequestException as err:
            can_retry = headers_received and not _is_permanent_4xx(err)
            if not can_retry or attempt + 1 >= total_attempts:
                raise
            delay = backoff_factor * (2**attempt)
            logging.warning(
                'Stream interrupted from %s (attempt %d/%d): %s; '
                'retrying in %.1fs...',
                source_url,
                attempt + 1,
                total_attempts,
                err,
                delay,
            )
            if delay > 0:
                time.sleep(delay)


def normalize_rate_value(val: str) -> str:
    """Adds '.0' to integer-mantissa scientific notation so SVP parses it."""
    return _INT_SCI_RE.sub(r'\1.0\2', val.strip())


def normalize_who_csv(input_path: str, output_path: str) -> int:
    """Validates UTF-8 CSV data and normalizes RATE_PER_1000_N values."""
    data_rows = 0
    with open(input_path, 'r', encoding='utf-8', newline='') as in_file:
        reader = csv.reader(in_file)
        header = next(reader, None)
        if not header:
            raise RuntimeError(f'No data fetched: {input_path} is empty.')
        if RATE_COLUMN not in header:
            raise RuntimeError(
                f'Missing expected column {RATE_COLUMN!r} in {input_path}; '
                f'got header={header}')
        rate_idx = header.index(RATE_COLUMN)

        with open(output_path, 'w', encoding='utf-8', newline='') as out_file:
            writer = csv.writer(out_file, lineterminator='\n')
            writer.writerow(header)
            for row in reader:
                if not row:
                    continue
                if rate_idx < len(row):
                    row[rate_idx] = normalize_rate_value(row[rate_idx])
                writer.writerow(row)
                data_rows += 1

    if data_rows == 0:
        raise RuntimeError(
            f'No data fetched: {input_path} contained only the header row.')
    return data_rows


def _remove_if_exists(path: str | None) -> None:
    """Deletes a temporary file if it exists on disk."""
    if path and os.path.exists(path):
        os.remove(path)


def download_full_who_data(
    indicator_id: str = DEFAULT_INDICATOR_ID,
    input_url: str = '',
    output_dir: str = DEFAULT_OUTPUT_DIR,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    session: requests.Session | None = None,
) -> str:
    """Downloads, validates, and normalizes the WHO Adolescent Birth Rate CSV."""
    source_url = build_source_url(
        indicator_id=indicator_id,
        input_url=input_url,
    )
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, OUTPUT_FILENAME)

    logging.info('Requesting full historical CSV from %s...', source_url)
    raw_tmp_path: str | None = None
    norm_tmp_path: str | None = None
    owned_session: requests.Session | None = None
    active_session = session
    if active_session is None:
        owned_session = create_retry_session(
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )
        active_session = owned_session

    try:
        raw_fd, raw_tmp_path = tempfile.mkstemp(
            dir=output_dir,
            prefix='.raw_who_',
            suffix='.csv',
        )
        os.close(raw_fd)

        _download_to_path(
            http_session=active_session,
            source_url=source_url,
            dest_path=raw_tmp_path,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )

        norm_fd, norm_tmp_path = tempfile.mkstemp(
            dir=output_dir,
            prefix='.norm_who_',
            suffix='.csv',
        )
        os.close(norm_fd)

        data_rows = normalize_who_csv(raw_tmp_path, norm_tmp_path)
        os.replace(norm_tmp_path, filename)
        norm_tmp_path = None
        logging.info(
            'Successfully saved %d data rows to %s',
            data_rows,
            filename,
        )
        return filename
    except requests.exceptions.RequestException as err:
        logging.error('Error fetching WHO data from %s: %s', source_url, err)
        raise RuntimeError(
            f'Error fetching WHO data from {source_url}: {err}') from err
    finally:
        _remove_if_exists(raw_tmp_path)
        _remove_if_exists(norm_tmp_path)
        if owned_session is not None:
            owned_session.close()


def main(argv: list[str]) -> None:
    """Parses CLI flags and downloads the WHO Adolescent Birth Rate dataset."""
    if len(argv) > 1:
        raise app.UsageError(f'Unexpected positional arguments: {argv[1:]}')
    download_full_who_data(
        indicator_id=FLAGS.indicator_id,
        input_url=FLAGS.input_url,
        output_dir=FLAGS.output_dir,
    )


if __name__ == '__main__':
    _define_flags()
    app.run(main)
