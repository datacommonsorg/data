# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Downloads and extracts CRDC Maths and Science enrollment source files."""

from datetime import datetime
import json
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Optional
import zipfile

from absl import app
from absl import flags
from absl import logging
import pandas as pd
import requests

FLAGS = flags.FLAGS
if 'force_download' not in FLAGS:
    flags.DEFINE_bool(
        'force_download',
        False,
        'Re-download and overwrite existing files in input_files/ without '
        'checking upstream ETag or Last-Modified headers.',
    )

# Base URL template
BASE_URL_TEMPLATE = (
    'https://civilrightsdata.ed.gov/assets/ocr/docs/{}-{}-crdc-data.zip')
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
SAVE_FOLDER = os.path.join(SCRIPT_DIR, 'input_files')

# Confirmed historical/current CRDC survey year ranges required by run.sh.
# Note: 2013-14 is intentionally omitted because run.sh processes 2010/2012,
# 2016, and 2018 onwards.
REQUIRED_SURVEY_RANGES = (
    (2009, 2010),
    (2011, 2012),
    (2015, 2016),
    (2017, 2018),
    (2020, 2021),
    (2021, 2022),
    (2023, 2024),
)
LATEST_REQUIRED_END_YEAR = max(end for _, end in REQUIRED_SURVEY_RANGES)

COURSE_SUBJECTS = (
    'Advanced_Mathematics',
    'Physics',
    'Calculus',
    'Geometry',
    'Algebra_II',
    'Chemistry',
    'Biology',
)

# Keyword patterns (case-insensitive)
KEYWORDS = {
    'Advanced Mathematics': r'Advanced Mathematics\.(csv|xlsx)$',
    'Physics': r'Physics\.(csv|xlsx)$',
    'Calculus': r'Calculus\.(csv|xlsx)$',
    'Geometry': r'Geometry\.(csv|xlsx)$',
    'Algebra II': r'Algebra II\.(csv|xlsx)$',
    'Chemistry': r'Chemistry\.(csv|xlsx)$',
    'Biology': r'Biology\.(csv|xlsx)$',
    'School Data': r'School Data\.csv$',
}

filename_configs = {
    'Advanced Mathematics': 'Advanced_Mathematics',
    'Physics': 'Physics',
    'Calculus': 'Calculus',
    'Geometry': 'Geometry',
    'Algebra II': 'Algebra_II',
    'Chemistry': 'Chemistry',
    'Biology': 'Biology',
    'School Data': 'School_data',
}

_CONNECT_TIMEOUT_SECS = 30
_READ_TIMEOUT_SECS = 180
_CHUNK_SIZE_BYTES = 1024 * 1024
_MAX_ATTEMPTS = 4
_INITIAL_BACKOFF_SECS = 5


class UnreleasedArchiveError(FileNotFoundError):
    """Raised when an optional future CRDC archive is not yet published."""


def detect_subject(filename: str) -> Optional[str]:
    """Return the subject key that matches the filename."""
    basename = os.path.basename(filename)
    if basename.startswith('~$') or basename.startswith('.'):
        return None
    for subject, pattern in KEYWORDS.items():
        if re.search(pattern, basename, re.IGNORECASE):
            return subject
    return None


def expected_output_filenames(end_year: int) -> list[str]:
    """Returns expected output filenames in input_files/ for a survey end year."""
    if end_year in (2010, 2012):
        return [f'{end_year}_{subj}.xlsx' for subj in COURSE_SUBJECTS]
    if end_year == 2016:
        return ['2016_School_data.csv']
    return [f'{end_year}_{subj}.csv' for subj in COURSE_SUBJECTS]


def _all_expected_files_exist(end_year: int, save_folder: str) -> bool:
    """Returns True if all expected extracted files exist and are non-empty."""
    expected = expected_output_filenames(end_year)
    return bool(expected) and all(
        os.path.isfile(os.path.join(save_folder, name)) and
        os.path.getsize(os.path.join(save_folder, name)) > 0
        for name in expected)


def _metadata_sidecar_path(end_year: int, save_folder: str) -> str:
    """Returns hidden HTTP cache-metadata sidecar path for a survey year."""
    return os.path.join(save_folder, f'.{end_year}_crdc_meta.json')


def _write_cache_metadata(end_year: int, save_folder: str,
                          headers_meta: dict[str, str]) -> None:
    """Atomically records upstream ETag and Last-Modified headers."""
    etag = (headers_meta.get('etag') or '').strip()
    last_modified = (headers_meta.get('last_modified') or '').strip()
    if not etag and not last_modified:
        return
    meta_path = _metadata_sidecar_path(end_year, save_folder)
    fd, tmp_meta_path = tempfile.mkstemp(prefix=f'.{end_year}_crdc_meta.',
                                         suffix='.json',
                                         dir=save_folder)
    os.close(fd)
    try:
        with open(tmp_meta_path, 'w', encoding='utf-8') as f:
            json.dump({'etag': etag, 'last_modified': last_modified}, f)
        os.replace(tmp_meta_path, meta_path)
    finally:
        if os.path.exists(tmp_meta_path):
            os.remove(tmp_meta_path)


def _is_cached_archive_fresh(
        url: str,
        end_year: int,
        save_folder: str,
        session: Optional[requests.Session] = None) -> bool:
    """Returns True only when expected files exist and HTTP headers match."""
    if not _all_expected_files_exist(end_year, save_folder):
        return False

    meta_path = _metadata_sidecar_path(end_year, save_folder)
    if not os.path.isfile(meta_path):
        return False

    try:
        with open(meta_path, encoding='utf-8') as f:
            cached = json.load(f)
    except (OSError, ValueError, TypeError):
        return False

    if not isinstance(cached, dict):
        return False
    cached_etag = (cached.get('etag') or '').strip()
    cached_lm = (cached.get('last_modified') or '').strip()
    if not cached_etag and not cached_lm:
        return False

    own_session = session is None
    http = session or requests.Session()
    try:
        response = http.head(
            url,
            allow_redirects=True,
            timeout=(_CONNECT_TIMEOUT_SECS, _CONNECT_TIMEOUT_SECS),
        )
        if response.status_code != 200:
            return False
        remote_etag = (response.headers.get('ETag') or '').strip()
        remote_lm = (response.headers.get('Last-Modified') or '').strip()
    except requests.exceptions.RequestException as exc:
        logging.warning(
            f'HEAD freshness check failed for {url}: {exc}; re-downloading.')
        return False
    finally:
        if own_session:
            http.close()

    compared = False
    if cached_etag and remote_etag:
        if cached_etag != remote_etag:
            return False
        compared = True
    if cached_lm and remote_lm:
        if cached_lm != remote_lm:
            return False
        compared = True
    return compared


def add_year_ncesid_column(file_path: str,
                           year: int,
                           output_path: Optional[str] = None) -> None:
    """Open CSV/XLSX, add YEAR and ncesid columns, and write to output_path."""
    target_path = output_path or file_path
    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path,
                             dtype=str,
                             low_memory=False,
                             encoding='latin1')
        elif file_path.lower().endswith('.xlsx'):
            df = pd.read_excel(file_path, dtype=str, engine='openpyxl')
        else:
            logging.warning(f'Skipping non-tabular file: {file_path}')
            return

        df['YEAR'] = year
        if all(col in df.columns for col in ['LEAID', 'SCHID']):
            df['LEAID'] = df['LEAID'].astype(str).str.zfill(7)
            df['SCHID'] = df['SCHID'].astype(str).str.zfill(5)
            df['ncesid'] = df['LEAID'] + df['SCHID']
        else:
            logging.warning(
                'Warning: Missing LEAID or SCHID columns for NCESID creation '
                f'in {os.path.basename(target_path)}')

        if target_path.lower().endswith('.csv'):
            df.to_csv(target_path, index=False)
        else:
            df.to_excel(target_path, index=False)
        logging.info(f'YEAR and nces id columns are added ({year}) -> '
                     f'{os.path.basename(target_path)}')

    except Exception as e:
        raise RuntimeError(
            f'Failed to add YEAR and nces id columns to {target_path}: {e}'
        ) from e


def download_zip_to_path(
        zip_url: str,
        dest_zip_path: str,
        required: bool = True,
        session: Optional[requests.Session] = None,
        max_attempts: int = _MAX_ATTEMPTS,
        initial_backoff_secs: float = _INITIAL_BACKOFF_SECS) -> dict[str, str]:
    """Streams zip_url to dest_zip_path and validates ZIP integrity with retries.

    Full body transfer and zipfile.is_zipfile() validation happen inside the
    retry loop so mid-stream resets or truncated archives are retried.
    """
    own_session = session is None
    http = session or requests.Session()
    timeout = (_CONNECT_TIMEOUT_SECS, _READ_TIMEOUT_SECS)
    delay = initial_backoff_secs

    try:
        for attempt in range(1, max_attempts + 1):
            try:
                logging.info(
                    f'Downloading URL (attempt {attempt}/{max_attempts}): '
                    f'{zip_url}')
                with http.get(zip_url,
                              stream=True,
                              allow_redirects=True,
                              timeout=timeout) as response:
                    if response.status_code == 404:
                        if not required:
                            raise UnreleasedArchiveError(
                                f'Optional future URL returned 404: {zip_url}')
                        response.raise_for_status()

                    response.raise_for_status()
                    content_type = (response.headers.get('Content-Type') or
                                    '').lower()
                    etag = (response.headers.get('ETag') or '').strip()
                    last_modified = (response.headers.get('Last-Modified') or
                                     '').strip()

                    with open(dest_zip_path, 'wb') as out_f:
                        for chunk in response.iter_content(
                                chunk_size=_CHUNK_SIZE_BYTES):
                            if chunk:
                                out_f.write(chunk)

                if not zipfile.is_zipfile(dest_zip_path):
                    # civilrightsdata.ed.gov returns HTTP 200 text/html SPA
                    # fallback pages for unreleased future archive URLs.
                    if not required and 'text/html' in content_type:
                        raise UnreleasedArchiveError(
                            f'Optional future URL returned HTML instead of ZIP: '
                            f'{zip_url}')
                    raise zipfile.BadZipFile(
                        f'Downloaded payload is not a valid ZIP archive '
                        f'(Content-Type={content_type!r}): {zip_url}')

                return {'etag': etag, 'last_modified': last_modified}
            except UnreleasedArchiveError:
                raise
            except Exception as exc:
                if os.path.exists(dest_zip_path):
                    os.remove(dest_zip_path)
                if attempt >= max_attempts:
                    raise RuntimeError(
                        f'Failed to download valid ZIP from {zip_url} after '
                        f'{max_attempts} attempts: {exc}') from exc
                logging.warning(
                    f'Attempt {attempt}/{max_attempts} failed for {zip_url}: '
                    f'{exc}. Retrying in {delay}s...')
                time.sleep(delay)
                delay *= 2
    finally:
        if own_session:
            http.close()

    return {'etag': '', 'last_modified': ''}


def download_and_extract_zip(
        start_year: int,
        end_year: int,
        required: bool = True,
        save_folder: str = SAVE_FOLDER,
        force_download: bool = False,
        session: Optional[requests.Session] = None) -> list[str]:
    """Download and extract matching files for a CRDC survey year range."""
    os.makedirs(save_folder, exist_ok=True)
    zip_name = f'{start_year}-{str(end_year)[-2:]}-crdc-data.zip'
    url = BASE_URL_TEMPLATE.format(start_year, str(end_year)[-2:])

    if not force_download and _is_cached_archive_fresh(
            url, end_year, save_folder, session=session):
        logging.info(
            f'All expected files for {end_year} in {save_folder} match '
            f'upstream HTTP headers; skipping download.')
        return [
            os.path.join(save_folder, name)
            for name in expected_output_filenames(end_year)
        ]

    logging.info(f'Processing {zip_name} (required={required}) ...')

    fd, tmp_zip_path = tempfile.mkstemp(prefix=f'.{end_year}_crdc_',
                                        suffix='.zip',
                                        dir=save_folder)
    os.close(fd)
    staged_outputs: dict[str, str] = {}

    try:
        try:
            headers_meta = download_zip_to_path(url,
                                                tmp_zip_path,
                                                required=required,
                                                session=session)
        except UnreleasedArchiveError as exc:
            logging.info(
                f'Skipping unreleased future archive {zip_name}: {exc}')
            return []

        with zipfile.ZipFile(tmp_zip_path) as zf:
            for file_name in zf.namelist():
                if file_name.endswith('/'):
                    continue
                subject = detect_subject(file_name)
                if not subject:
                    continue

                base_output = filename_configs[subject]
                ext = os.path.splitext(file_name)[1].lower()
                output_filename = f'{end_year}_{base_output}{ext}'

                raw_fd, raw_tmp_path = tempfile.mkstemp(
                    prefix=f'.{output_filename}.raw.',
                    suffix=ext,
                    dir=save_folder)
                os.close(raw_fd)
                proc_fd, proc_tmp_path = tempfile.mkstemp(
                    prefix=f'.{output_filename}.proc.',
                    suffix=ext,
                    dir=save_folder)
                os.close(proc_fd)

                try:
                    with zf.open(file_name) as source, open(raw_tmp_path,
                                                            'wb') as target:
                        while True:
                            chunk = source.read(_CHUNK_SIZE_BYTES)
                            if not chunk:
                                break
                            target.write(chunk)
                    add_year_ncesid_column(raw_tmp_path,
                                           end_year,
                                           output_path=proc_tmp_path)
                    if os.path.getsize(proc_tmp_path) == 0:
                        raise RuntimeError(
                            f'Post-processed file is empty: {output_filename}')
                    prev_staged = staged_outputs.pop(output_filename, None)
                    if prev_staged and os.path.exists(prev_staged):
                        os.remove(prev_staged)
                    staged_outputs[output_filename] = proc_tmp_path
                except Exception:
                    if os.path.exists(proc_tmp_path):
                        os.remove(proc_tmp_path)
                    raise
                finally:
                    if os.path.exists(raw_tmp_path):
                        os.remove(raw_tmp_path)

        if not staged_outputs:
            raise RuntimeError(
                f'No matching course files found inside {zip_name} ({url}).')

        expected_names = expected_output_filenames(end_year)
        missing = [
            name for name in expected_names if name not in staged_outputs or
            os.path.getsize(staged_outputs[name]) == 0
        ]
        if missing:
            raise RuntimeError(
                f'Missing expected extracted files from {zip_name}: {missing}')

        extracted_paths: list[str] = []
        for output_filename, proc_tmp_path in list(staged_outputs.items()):
            output_path = os.path.join(save_folder, output_filename)
            os.replace(proc_tmp_path, output_path)
            del staged_outputs[output_filename]
            extracted_paths.append(output_path)
            logging.info(f'Extracted and processed: {output_filename}')

        _write_cache_metadata(end_year, save_folder, headers_meta)
        logging.info(
            f'Completed {zip_name}: saved {len(extracted_paths)} file(s) into '
            f'{save_folder}.')
        return extracted_paths
    finally:
        for path in staged_outputs.values():
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(tmp_zip_path):
            os.remove(tmp_zip_path)


def build_survey_schedule(current_year: int) -> list[tuple[int, int, bool]]:
    """Builds ordered (start_year, end_year, required) tuples up to current_year."""
    schedule = [(start, end, True) for start, end in REQUIRED_SURVEY_RANGES]
    for end_year in range(LATEST_REQUIRED_END_YEAR + 1, current_year + 1):
        schedule.append((end_year - 1, end_year, False))
    return schedule


def main(_) -> None:
    current_year = datetime.now().year
    schedule = build_survey_schedule(current_year)
    with requests.Session() as session:
        for start_year, end_year, required in schedule:
            download_and_extract_zip(start_year,
                                     end_year,
                                     required=required,
                                     save_folder=SAVE_FOLDER,
                                     force_download=FLAGS.force_download,
                                     session=session)


if __name__ == '__main__':
    app.run(main)
