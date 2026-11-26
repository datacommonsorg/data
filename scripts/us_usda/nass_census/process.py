# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Import USDA Census of Agriculture."""

import csv
import gzip
from html.parser import HTMLParser
import os
import re
import sys
from urllib.parse import urljoin
from urllib.parse import urlparse

from absl import app
from absl import flags
from absl import logging
import requests
from retry import retry

# Define flags
_FLAGS = flags.FLAGS

# Constants
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..', '..'))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.join(_REPO_ROOT, 'util'))

import file_util

DATASETS_PAGE_URL = 'https://www.nass.usda.gov/datasets'
CENSUS_START_YEAR = 2002
CENSUS_INTERVAL_YEARS = 5
DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1 MiB
CONNECT_TIMEOUT_SECS = 30
READ_TIMEOUT_SECS = 120

EXPECTED_SECTORS = (
    'animals_products',
    'crops',
    'demographics',
    'economics',
    'environmental',
)

_SECTOR_FILENAME_RE = re.compile(
    r'^qs\.(animals_products|crops|demographics|economics|environmental)'
    r'(?:_(\d{8}))?\.txt\.gz$',
    re.IGNORECASE,
)

CSV_COLUMNS = [
    'variableMeasured',
    'observationAbout',
    'value',
    'unit',
    'observationDate',
]

REQUIRED_TSV_COLUMNS = frozenset({
    'SOURCE_DESC',
    'SHORT_DESC',
    'DOMAINCAT_DESC',
    'AGG_LEVEL_DESC',
    'STATE_FIPS_CODE',
    'COUNTY_CODE',
    'YEAR',
    'VALUE',
})

SKIPPED_VALUES = frozenset({
    '(D)',
    '(Z)',
    '(NA)',
    '(X)',
    '(S)',
})


class TransientDownloadError(Exception):
    """Raised when an HTTP download fails with a retryable condition."""


class _DatasetLinkParser(HTMLParser):
    """Extracts anchor href attributes from the USDA NASS datasets page."""

    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str,
                                                          str | None]]) -> None:
        if tag.lower() != 'a':
            return
        for attr_name, attr_val in attrs:
            if attr_name.lower() == 'href' and attr_val:
                self.hrefs.append(attr_val.strip())


def _define_flags() -> None:
    """Defines command-line flags for this script."""
    flags.DEFINE_string(
        'output',
        os.path.join(_SCRIPT_DIR, 'output', 'agriculture.csv'),
        'Output CSV file',
    )
    flags.DEFINE_string(
        'input_dir',
        os.path.join(_SCRIPT_DIR, 'input'),
        'Directory to store downloaded raw source archives',
    )
    flags.DEFINE_string(
        'mode',
        '',
        'Mode to run: "download", "process", or "" (both)',
    )


def is_census_year(year_str: str) -> bool:
    """Returns True if year_str is a 5-year Census of Agriculture year (>= 2002)."""
    if not year_str or not year_str.isdigit():
        return False
    year = int(year_str)
    return (year >= CENSUS_START_YEAR and
            (year - CENSUS_START_YEAR) % CENSUS_INTERVAL_YEARS == 0)


def _raise_for_http_status(response: requests.Response, url: str) -> None:
    """Raises TransientDownloadError on retryable statuses, HTTPError otherwise."""
    status = response.status_code
    if status in (408, 429) or status >= 500:
        raise TransientDownloadError(f'Transient HTTP {status} from {url}')
    response.raise_for_status()


@retry(
    tries=3,
    delay=2,
    backoff=2,
    exceptions=(
        requests.ConnectionError,
        requests.Timeout,
        TransientDownloadError,
    ),
)
def fetch_datasets_html(datasets_url: str = DATASETS_PAGE_URL,
                        session: requests.Session | None = None) -> str:
    """Fetches the USDA NASS datasets index HTML page."""
    client = session or requests
    logging.info(f'GET {datasets_url}')
    response = client.get(
        datasets_url,
        timeout=(CONNECT_TIMEOUT_SECS, READ_TIMEOUT_SECS),
    )
    _raise_for_http_status(response, datasets_url)
    return response.text


def discover_sector_urls(html_text: str,
                         base_url: str = DATASETS_PAGE_URL) -> list[str]:
    """Parses the USDA datasets page and returns one .txt.gz URL per sector."""
    parser = _DatasetLinkParser()
    parser.feed(html_text)

    best_by_sector: dict[str, tuple[str, str]] = {}
    for href in parser.hrefs:
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        hostname = (parsed.hostname or '').lower()
        if parsed.scheme != 'https' or (
                hostname != 'nass.usda.gov' and
                not hostname.endswith('.nass.usda.gov')):
            continue
        filename = os.path.basename(parsed.path)
        match = _SECTOR_FILENAME_RE.match(filename)
        if not match:
            continue
        sector = match.group(1).lower()
        date_tag = match.group(2) or ''
        prev = best_by_sector.get(sector)
        if prev is None or date_tag >= prev[0]:
            best_by_sector[sector] = (date_tag, full_url)

    # Check all 5 sector links before downloading; validation_config.json runs
    # post-MCF and cannot detect missing sector links or soft-404 HTML pages at
    # source-discovery time.
    missing = [s for s in EXPECTED_SECTORS if s not in best_by_sector]
    if missing:
        raise RuntimeError(
            f'Missing expected Quick Stats sector archives on {base_url}: '
            f'missing={missing}, found={sorted(best_by_sector.keys())}')

    return [best_by_sector[sector][1] for sector in EXPECTED_SECTORS]


def download_file(url: str,
                  output_path: str,
                  session: requests.Session | None = None) -> None:
    """Downloads a file atomically with retry and HTTP Range resume support.

    Custom streaming downloader used instead of util/download_util.py (which
    loads and decompresses multi-GB .gz files in memory) and
    util/download_util_script.py (which retries permanent 404s and lacks HTTP
    Range resume for 1+ GB archives).
    """
    client = session or requests
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    part_path = f'{output_path}.part'
    if os.path.exists(part_path):
        os.remove(part_path)

    validator: str | None = None

    @retry(
        tries=4,
        delay=2,
        backoff=2,
        exceptions=(
            requests.ConnectionError,
            requests.Timeout,
            requests.exceptions.ChunkedEncodingError,
            TransientDownloadError,
        ),
    )
    def _download_with_resume() -> None:
        nonlocal validator
        existing_bytes = (os.path.getsize(part_path)
                          if os.path.exists(part_path) else 0)
        headers: dict[str, str] = {}
        if existing_bytes > 0:
            headers['Range'] = f'bytes={existing_bytes}-'
            if validator:
                headers['If-Range'] = validator
            logging.info(f'GET {url} (resuming from byte {existing_bytes})')
        else:
            logging.info(f'GET {url}')

        with client.get(
                url,
                headers=headers or None,
                stream=True,
                timeout=(CONNECT_TIMEOUT_SECS, READ_TIMEOUT_SECS),
        ) as response:
            if existing_bytes > 0 and response.status_code == 416:
                os.remove(part_path)
                raise TransientDownloadError(
                    f'HTTP 416 Range Not Satisfiable for {url}; restarting')

            _raise_for_http_status(response, url)

            if existing_bytes > 0 and response.status_code == 206:
                mode = 'ab'
            else:
                mode = 'wb'
                existing_bytes = 0
                validator = (response.headers.get('ETag') or
                             response.headers.get('Last-Modified'))

            expected_chunk_bytes = response.headers.get('Content-Length')
            written_bytes = 0
            with open(part_path, mode) as f_out:
                for chunk in response.iter_content(
                        chunk_size=DOWNLOAD_CHUNK_SIZE):
                    if chunk:
                        f_out.write(chunk)
                        written_bytes += len(chunk)

            if (expected_chunk_bytes is not None and
                    written_bytes != int(expected_chunk_bytes)):
                raise TransientDownloadError(
                    f'Incomplete transfer from {url}: received {written_bytes} '
                    f'of {expected_chunk_bytes} bytes')

    try:
        _download_with_resume()
        # Verify non-empty payload and gzip magic bytes at download time to
        # catch truncated transfers or HTTP-200 HTML soft-404 error pages before
        # downstream processing (cannot be expressed in validation_config.json).
        if not os.path.exists(part_path) or os.path.getsize(part_path) == 0:
            raise RuntimeError(f'Downloaded empty file from {url}')
        if output_path.endswith('.gz'):
            with open(part_path, 'rb') as f_check:
                if f_check.read(2) != b'\x1f\x8b':
                    raise RuntimeError(
                        f'Downloaded file from {url} is not a valid gzip archive'
                    )
        os.replace(part_path, output_path)
        logging.info(f'Downloaded file: {output_path}')
    except Exception:
        if os.path.exists(part_path):
            os.remove(part_path)
        raise


def get_statvars(filename: str) -> dict[str, tuple[str, ...]]:
    """Loads normalized SHORT_DESC[%%DOMAINCAT_DESC] -> (StatVar, [Unit]) map."""
    d: dict[str, tuple[str, ...]] = {}
    with open(filename, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('^')
            d[parts[0].strip().upper()] = tuple(parts[1:])
    return d


def _format_observation(
    short_desc: str,
    domaincat_desc: str,
    agg_level_desc: str,
    state_fips: str,
    county_code: str,
    year_str: str,
    raw_value: str,
    statvars_map: dict[str, tuple[str, ...]],
) -> tuple[str, str, int, str, str] | None:
    """Converts one Quick Stats TSV record into a CSV row tuple, or None."""
    short_clean = short_desc.strip()
    domaincat_clean = domaincat_desc.strip()
    key = (f'{short_clean}%%{domaincat_clean}'
           if domaincat_clean else short_clean).upper()
    statvar_def = statvars_map.get(key)
    if statvar_def is None:
        return None

    cleaned_val = raw_value.strip()
    if not cleaned_val or cleaned_val.upper() in SKIPPED_VALUES:
        return None

    agg_level = agg_level_desc.strip().upper()
    if agg_level == 'NATIONAL':
        observation_about = 'dcid:country/USA'
    elif agg_level == 'STATE':
        observation_about = 'dcid:geoId/' + state_fips.strip()
    elif agg_level == 'COUNTY':
        observation_about = ('dcid:geoId/' + state_fips.strip() +
                             county_code.strip())
    else:
        return None

    try:
        numeric_value = int(cleaned_val.replace(',', ''))
    except ValueError as exc:
        raise ValueError(
            f'Invalid integer VALUE={raw_value!r} for key={key!r}, '
            f'year={year_str!r}') from exc
    unit = 'dcs:' + statvar_def[1] if len(statvar_def) > 1 else ''
    return (
        'dcs:' + statvar_def[0],
        observation_about,
        numeric_value,
        unit,
        year_str,
    )


def _process_tsv_stream(
    text_stream,
    source_name: str,
    statvars_map: dict[str, tuple[str, ...]],
    year_writers: dict[str, tuple[str, object, csv.writer]],
    output_dir: str,
) -> int:
    """Streams a Quick Stats TSV and routes matching Census rows by year."""
    tsv_reader = csv.reader(text_stream, delimiter='\t')
    try:
        header = next(tsv_reader)
    except StopIteration as exc:
        raise ValueError(f'Empty TSV input in {source_name}') from exc

    col_idx = {col: idx for idx, col in enumerate(header)}
    missing_cols = REQUIRED_TSV_COLUMNS - set(col_idx.keys())
    if missing_cols:
        raise ValueError(f'Missing required TSV columns in {source_name}: '
                         f'{sorted(missing_cols)}')

    source_idx = col_idx['SOURCE_DESC']
    short_desc_idx = col_idx['SHORT_DESC']
    domaincat_idx = col_idx['DOMAINCAT_DESC']
    agg_idx = col_idx['AGG_LEVEL_DESC']
    state_fips_idx = col_idx['STATE_FIPS_CODE']
    county_idx = col_idx['COUNTY_CODE']
    year_idx = col_idx['YEAR']
    value_idx = col_idx['VALUE']
    max_required_idx = max(
        source_idx,
        short_desc_idx,
        domaincat_idx,
        agg_idx,
        state_fips_idx,
        county_idx,
        year_idx,
        value_idx,
    )

    written = 0
    for line_num, row in enumerate(tsv_reader, start=2):
        if not row:
            continue
        if len(row) <= max_required_idx:
            raise ValueError(
                f'Malformed TSV row at {source_name}:{line_num}: '
                f'expected >{max_required_idx} columns, got {len(row)}')
        if row[source_idx].strip().upper() != 'CENSUS':
            continue
        year_str = row[year_idx].strip()
        if not is_census_year(year_str):
            continue

        obs_tuple = _format_observation(
            short_desc=row[short_desc_idx],
            domaincat_desc=row[domaincat_idx],
            agg_level_desc=row[agg_idx],
            state_fips=row[state_fips_idx],
            county_code=row[county_idx],
            year_str=year_str,
            raw_value=row[value_idx],
            statvars_map=statvars_map,
        )
        if obs_tuple is None:
            continue

        year_entry = year_writers.get(year_str)
        if year_entry is None:
            tmp_year_path = os.path.join(output_dir,
                                         f'agriculture_{year_str}.csv.tmp')
            f_year = open(tmp_year_path, 'w', encoding='utf-8', newline='')
            csv_writer = csv.writer(f_year, lineterminator='\n')
            csv_writer.writerow(CSV_COLUMNS)
            year_entry = (tmp_year_path, f_year, csv_writer)
            year_writers[year_str] = year_entry

        year_entry[2].writerow(obs_tuple)
        written += 1

    logging.info(f'Processed {source_name}: {written} matching census rows.')
    return written


def merge_csv_files(output_file: str, input_files: list[str]) -> None:
    """Atomically merges per-year CSV files into output_file."""
    output_dir = os.path.dirname(os.path.abspath(output_file))
    os.makedirs(output_dir, exist_ok=True)
    tmp_output = f'{output_file}.tmp'
    try:
        with open(tmp_output, 'w', encoding='utf-8', newline='') as out_f:
            writer = None
            for input_file in input_files:
                with open(input_file, 'r', encoding='utf-8',
                          newline='') as in_f:
                    reader = csv.DictReader(in_f)
                    if writer is None:
                        writer = csv.DictWriter(
                            out_f,
                            fieldnames=reader.fieldnames,
                            lineterminator='\n',
                        )
                        writer.writeheader()
                    for row in reader:
                        writer.writerow(row)
        os.replace(tmp_output, output_file)
        logging.info(f'Merged output written to: {output_file}')
    except Exception:
        if os.path.exists(tmp_output):
            os.remove(tmp_output)
        raise


def download_sector_files(
    input_dir: str,
    session: requests.Session | None = None,
) -> list[str]:
    """Discovers and downloads datasets.html and the 5 sector .txt.gz archives."""
    os.makedirs(input_dir, exist_ok=True)
    html_text = fetch_datasets_html(DATASETS_PAGE_URL, session=session)
    sector_urls = discover_sector_urls(html_text, base_url=DATASETS_PAGE_URL)

    # Retain the raw index HTML in input_dir so manifest source_files ("input/*")
    # preserves every original file downloaded from the source, including HTML.
    html_filename = 'datasets.html'
    html_tmp_path = os.path.join(input_dir, f'{html_filename}.part')
    html_dest_path = os.path.join(input_dir, html_filename)
    with open(html_tmp_path, 'w', encoding='utf-8') as f_html:
        f_html.write(html_text)
    os.replace(html_tmp_path, html_dest_path)

    downloaded_paths: list[str] = []
    expected_basenames: set[str] = {html_filename}
    for url in sector_urls:
        basename = os.path.basename(urlparse(url).path)
        expected_basenames.add(basename)
        dest_path = os.path.join(input_dir, basename)
        download_file(url, dest_path, session=session)
        downloaded_paths.append(dest_path)

    # Remove stale archives or leftover artifacts from earlier runs so input_dir
    # retains only the exact source files for this execution.
    for existing_name in os.listdir(input_dir):
        if existing_name not in expected_basenames:
            stale_path = os.path.join(input_dir, existing_name)
            if os.path.isfile(stale_path):
                os.remove(stale_path)
                logging.info(f'Removed stale input file: {stale_path}')

    return downloaded_paths


def process_input_files(
    input_paths: list[str],
    output_file: str,
    statvars_map: dict[str, tuple[str, ...]],
) -> list[str]:
    """Streams .txt.gz/.txt input files, writes per-year CSVs, and merges them."""
    if not input_paths:
        raise FileNotFoundError('No input files provided for processing.')

    output_dir = os.path.dirname(os.path.abspath(output_file))
    os.makedirs(output_dir, exist_ok=True)

    # Remove stale per-year CSVs before generating fresh outputs.
    for existing_name in os.listdir(output_dir):
        if re.match(r'^agriculture_\d{4}\.csv(?:\.tmp)?$', existing_name):
            os.remove(os.path.join(output_dir, existing_name))

    year_writers: dict[str, tuple[str, object, csv.writer]] = {}
    total_rows = 0
    try:
        for path in input_paths:
            if path.endswith('.gz'):
                with gzip.open(
                        path,
                        mode='rt',
                        encoding='utf-8',
                        errors='replace',
                        newline='',
                ) as gz_stream:
                    total_rows += _process_tsv_stream(
                        gz_stream,
                        os.path.basename(path),
                        statvars_map,
                        year_writers,
                        output_dir,
                    )
            else:
                with file_util.FileIO(
                        path,
                        'r',
                        encoding='utf-8',
                        errors='replace',
                        newline='',
                ) as txt_stream:
                    total_rows += _process_tsv_stream(
                        txt_stream,
                        os.path.basename(path),
                        statvars_map,
                        year_writers,
                        output_dir,
                    )
    except Exception:
        for tmp_path, handle, _ in year_writers.values():
            handle.close()
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        raise

    year_files: list[str] = []
    try:
        for year_str in sorted(year_writers.keys(), key=int):
            tmp_path, handle, _ = year_writers[year_str]
            handle.close()
            final_year_path = os.path.join(output_dir,
                                           f'agriculture_{year_str}.csv')
            os.replace(tmp_path, final_year_path)
            year_files.append(final_year_path)
    finally:
        for tmp_path, handle, _ in year_writers.values():
            if not handle.closed:
                handle.close()
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # Guard standalone CLI runs (--mode=process) before MCF generation; in
    # automated runs validation_config.json also enforces EMPTY_IMPORT_CHECK.
    if total_rows == 0 or not year_files:
        raise RuntimeError(
            'No census observations were produced from the input files.')

    merge_csv_files(output_file, year_files)
    return year_files


def _find_local_input_files(input_dir: str) -> list[str]:
    """Finds .txt.gz archives (preferred) or .txt files in input_dir."""
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f'Input directory does not exist: {input_dir}. '
                                'Run with --mode=download first.')
    gz_files = sorted(
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.endswith('.txt.gz'))
    if gz_files:
        return gz_files
    txt_files = sorted(
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.endswith('.txt'))
    if txt_files:
        return txt_files
    raise FileNotFoundError(
        f'No .txt.gz or .txt input files found in {input_dir}.')


def main(_) -> None:
    output_dir = os.path.dirname(os.path.abspath(_FLAGS.output))
    os.makedirs(output_dir, exist_ok=True)

    statvars_map = get_statvars(os.path.join(_SCRIPT_DIR, 'statvars'))
    mode = _FLAGS.mode
    if mode not in ('', 'download', 'process'):
        raise ValueError(
            f'Unsupported --mode={mode!r}; expected "", "download", or "process".'
        )

    if mode in ('download', ''):
        with requests.Session() as session:
            input_paths = download_sector_files(_FLAGS.input_dir,
                                                session=session)
        if mode == '':
            process_input_files(input_paths, _FLAGS.output, statvars_map)
    elif mode == 'process':
        input_paths = _find_local_input_files(_FLAGS.input_dir)
        process_input_files(input_paths, _FLAGS.output, statvars_map)


if __name__ == '__main__':
    _define_flags()
    app.run(main)
