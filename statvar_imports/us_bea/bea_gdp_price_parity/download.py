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
"""Downloads live BEA Regional ZIP archives and historical MSA GDP GCS baselines.

Uses a dedicated downloader rather than util/download_util_script.py so that
corrupted or soft-404 HTML responses fail via explicit exceptions (instead of
boolean return values / logging.fatal), raw .zip archives and extracted CSVs
are published atomically, and superseded year-ranged CSVs are cleaned up.
All downloaded source files are preserved untouched for stat_var_processor.py.
"""

import glob
import io
import os
from pathlib import Path
import time
from urllib.parse import urlparse
import zipfile

from absl import app
from absl import flags
from absl import logging
from google.api_core import exceptions as google_exceptions
from google.cloud import storage
import requests
from retry import retry

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

FLAGS = flags.FLAGS


def _define_flags() -> None:
    """Registers CLI flags when running download.py as a script."""
    flags.DEFINE_string(
        'bea_raw_dir',
        os.path.join(_SCRIPT_DIR, 'input_files', 'raw'),
        'Directory to store downloaded live BEA ZIP archives and extracted CSVs.',
    )
    flags.DEFINE_string(
        'bea_baseline_dir',
        os.path.join(_SCRIPT_DIR, 'input_files', 'baseline'),
        'Directory to store historical MSA GDP baseline CSV files from GCS.',
    )
    flags.DEFINE_boolean(
        'bea_copy_historical',
        True,
        'Whether to fetch historical MSA GDP baseline CSV files from GCS.',
    )


BEA_LIVE_ZIPS = {
    'MARPP': ('https://apps.bea.gov/regional/zip/MARPP.zip', 'MARPP_MSA_'),
    'SARPP': ('https://apps.bea.gov/regional/zip/SARPP.zip', 'SARPP_STATE_'),
    'CAGDP1': (
        'https://apps.bea.gov/regional/zip/CAGDP1.zip',
        'CAGDP1__ALL_AREAS_',
    ),
    'CAGDP11': (
        'https://apps.bea.gov/regional/zip/CAGDP11.zip',
        'CAGDP11__ALL_AREAS_',
    ),
}

GCS_BUCKET_NAME = 'datacommons_public'
GCS_HISTORICAL_PREFIX = 'unresolved_mcf/bea'
HISTORICAL_FILENAMES = (
    'metro_gdp.csv',
    'metro_nominal_gdp.csv',
)

_RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})
_TRANSIENT_GCS_EXCEPTIONS = (
    google_exceptions.GatewayTimeout,
    google_exceptions.InternalServerError,
    google_exceptions.RetryError,
    google_exceptions.ServiceUnavailable,
    google_exceptions.TooManyRequests,
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    TimeoutError,
)


def _write_bytes_atomic(target_path: str, payload: bytes) -> None:
    """Writes payload to a temporary sibling file and atomically replaces target_path."""
    tmp_path = f'{target_path}.tmp'
    try:
        with open(tmp_path, 'wb') as out_f:
            out_f.write(payload)
        os.replace(tmp_path, target_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def _has_data_rows(filepath: Path) -> bool:
    """Returns True if filepath exists and has at least one data row after header."""
    if not filepath.exists() or filepath.stat().st_size == 0:
        return False
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            header = f.readline()
            if not header:
                return False
            for line in f:
                if line.strip():
                    return True
    except OSError:
        return False
    return False


@retry(tries=3, delay=5, backoff=2, exceptions=_TRANSIENT_GCS_EXCEPTIONS)
def copy_historical_data_from_gcs(
    output_dir: str,
    gcs_bucket: str = GCS_BUCKET_NAME,
    gcs_prefix: str = GCS_HISTORICAL_PREFIX,
    skip_existing: bool = True,
) -> list[str]:
    """Copies historical MSA GDP baseline CSVs untouched from GCS to output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    prefix = gcs_prefix.rstrip('/')
    copied_files: list[str] = []
    client = None

    for filename in HISTORICAL_FILENAMES:
        dest_path = Path(output_dir) / filename
        if skip_existing and _has_data_rows(dest_path):
            logging.info(
                'Skipping GCS copy for historical BEA baseline: %s already exists in %s.',
                filename,
                output_dir,
            )
            copied_files.append(str(dest_path))
            continue

        blob_path = f'{prefix}/{filename}'
        logging.info(
            'Copying historical BEA baseline from gs://%s/%s to %s...',
            gcs_bucket,
            blob_path,
            dest_path,
        )
        temp_path = Path(f'{dest_path}.tmp')
        try:
            if client is None:
                client = storage.Client()
            bucket = client.bucket(gcs_bucket)
            blob = bucket.blob(blob_path)
            blob.download_to_filename(str(temp_path), timeout=300)
            if not _has_data_rows(temp_path):
                raise ValueError(
                    f'Downloaded GCS file gs://{gcs_bucket}/{blob_path} contains no observation data.'
                )
            os.replace(temp_path, dest_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

        logging.info('Copied gs://%s/%s -> %s', gcs_bucket, blob_path,
                     dest_path)
        copied_files.append(str(dest_path))

    return copied_files


def download_and_extract(
    url: str,
    file_prefix: str,
    output_dir: str,
    retries: int = 3,
    delay: int = 5,
    session: requests.Session | None = None,
) -> list[str]:
    """Downloads a live BEA ZIP archive, saves it raw, and atomically extracts CSVs."""
    os.makedirs(output_dir, exist_ok=True)
    req_lib = session if session is not None else requests
    headers = {'User-Agent': 'DataCommons-Import/1.0'}
    last_err: Exception | None = None

    zip_bytes: bytes | None = None
    for attempt in range(1, retries + 1):
        try:
            logging.info('Sending GET request to %s (attempt %d/%d)...', url,
                         attempt, retries)
            resp = req_lib.get(url, headers=headers, timeout=60)
            logging.info('GET %s -> HTTP %d', url, resp.status_code)
            if resp.status_code in _RETRYABLE_STATUS_CODES:
                raise requests.exceptions.HTTPError(
                    f'Transient HTTP {resp.status_code} for GET {url}',
                    response=resp,
                )
            resp.raise_for_status()
            zip_bytes = resp.content
            break
        except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.ChunkedEncodingError,
                TimeoutError,
        ) as err:
            last_err = err
        except requests.exceptions.HTTPError as err:
            if (err.response is not None and
                    err.response.status_code in _RETRYABLE_STATUS_CODES):
                last_err = err
            else:
                raise

        logging.warning('Transient failure on GET %s (attempt %d/%d): %s', url,
                        attempt, retries, last_err)
        if attempt < retries:
            time.sleep(delay * (2**(attempt - 1)))
    else:
        raise RuntimeError(
            f'Failed to download {url} after {retries} attempts') from last_err

    assert zip_bytes is not None
    if not zipfile.is_zipfile(io.BytesIO(zip_bytes)):
        raise ValueError(
            f'Downloaded payload from {url} is not a valid ZIP archive.')

    members_to_extract: list[tuple[str, bytes]] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for member in zf.namelist():
            basename = os.path.basename(member)
            if basename.startswith(file_prefix) and basename.endswith('.csv'):
                members_to_extract.append((basename, zf.read(member)))

    if not members_to_extract:
        raise RuntimeError(
            f'No CSV matching prefix {file_prefix!r} found in {url}')

    archive_name = os.path.basename(urlparse(url).path) or f'{file_prefix}.zip'
    raw_zip_path = os.path.join(output_dir, archive_name)
    _write_bytes_atomic(raw_zip_path, zip_bytes)
    logging.info('Saved raw BEA archive %s (%d bytes)', raw_zip_path,
                 len(zip_bytes))

    extracted: list[str] = []
    for basename, csv_bytes in members_to_extract:
        target_path = os.path.join(output_dir, basename)
        _write_bytes_atomic(target_path, csv_bytes)
        logging.info('Extracted raw BEA CSV %s', target_path)
        extracted.append(target_path)

    extracted_set = {os.path.abspath(p) for p in extracted}
    for existing_csv in glob.glob(
            os.path.join(output_dir, f'{file_prefix}*.csv')):
        if os.path.abspath(existing_csv) not in extracted_set:
            os.unlink(existing_csv)
            logging.info('Removed superseded raw BEA CSV %s', existing_csv)

    return extracted


def main(argv):
    del argv
    if FLAGS.bea_copy_historical:
        copy_historical_data_from_gcs(output_dir=FLAGS.bea_baseline_dir,
                                      skip_existing=False)
    with requests.Session() as session:
        for name, (url, prefix) in BEA_LIVE_ZIPS.items():
            logging.info('Downloading live BEA archive %s...', name)
            download_and_extract(url,
                                 prefix,
                                 FLAGS.bea_raw_dir,
                                 session=session)


if __name__ == '__main__':
    _define_flags()
    app.run(main)
