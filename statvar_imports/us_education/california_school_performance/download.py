#!/usr/bin/env python3
# Copyright 2025 Google LLC
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
"""Download, normalization, and extraction script for California School Performance (CAASPP) data.

This script fetches CAASPP research data files directly from the official
California Department of Education / Educational Testing Service (ETS) research portal
(https://caaspp-elpac.ets.org/caaspp/ResearchFileListSB) for all available years
(2015–2019, 2021–present; 2020 was cancelled statewide due to COVID-19).

It automatically handles differences in delimiter (comma vs caret) and column naming across
eras, filters State and County aggregate records, preserves raw source archives in raw_files/,
and streams normalization into a unified format ready for processing by Data Commons stat_var_processor.py.

Usage:
  python3 download.py --years=all
  python3 download.py --years=2015-2024
  python3 download.py --years=2024
  python3 download.py --test_mode
"""

import csv
from datetime import datetime
import io
import os
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'years',
    'all',
    'Years to download: "all" (2015-present, skipping 2020), range e.g. "2015-2024", or comma-separated "2023,2024".',
)
flags.DEFINE_enum(
    'data_mode',
    'all_students',
    ['all_students', 'all_groups'],
    'Data scope: "all_students" downloads group 1 only (~5MB/yr); "all_groups" downloads all 55 demographic subgroups (~100MB/yr).',
)
flags.DEFINE_string(
    'output_dir',
    '',
    'Directory to extract files into. Defaults to input_files/ under the script directory.',
)
flags.DEFINE_string(
    'raw_dir',
    '',
    'Directory to store downloaded raw zip files. Defaults to raw_files/ under the script directory.',
)
flags.DEFINE_boolean(
    'test_mode',
    False,
    'If true, downloads a small test sample for pipeline verification.',
)
flags.DEFINE_boolean(
    'clean',
    False,
    'If true, deletes existing files in output_dir before downloading.',
)
flags.DEFINE_boolean(
    'keep_all_entities',
    False,
    'If true, keeps all entities (including schools and districts). Defaults to False (State & County only).',
)

BASE_URL = 'https://caaspp-elpac.ets.org/caaspp/researchfiles/'
USER_AGENT = 'Mozilla/5.0 (DataCommons Ingestion Bot)'

# Known historical official zip filename per year: (all_subgroups_zip, all_students_zip)
KNOWN_YEAR_URL_MAP = {
    2015: ('sb_ca2015_all_csv_v3.zip', 'sb_ca2015_1_csv_v3.zip'),
    2016: ('sb_ca2016_all_csv_v3.zip', 'sb_ca2016_1_csv_v3.zip'),
    2017: ('sb_ca2017_all_csv_v2.zip', 'sb_ca2017_1_csv_v2.zip'),
    2018: ('sb_ca2018_all_csv_v3.zip', 'sb_ca2018_1_csv_v3.zip'),
    2019: ('sb_ca2019_all_csv_v4.zip', 'sb_ca2019_1_csv_v4.zip'),
    2021: ('sb_ca2021_all_csv_v2.zip', 'sb_ca2021_1_csv_v2.zip'),
    2022: ('sb_ca2022_all_csv_v1.zip', 'sb_ca2022_1_csv_v1.zip'),
    2023: ('sb_ca2023_all_csv_v1.zip', 'sb_ca2023_1_csv_v1.zip'),
    2024: ('sb_ca2024_all_csv_v1.zip', 'sb_ca2024_1_csv_v1.zip'),
    2025: ('sb_ca2025_all_csv_v1.zip', 'sb_ca2025_1_csv_v1.zip'),
}

UNIFIED_HEADER = [
    'County Code',
    'Test Year',
    'Student Group ID',
    'Grade',
    'Test ID',
    'Total Students Tested with Scores',
    'Mean Scale Score',
    'Percentage Standard Exceeded',
    'Percentage Standard Met',
    'Percentage Standard Met and Above',
    'Percentage Standard Nearly Met',
    'Percentage Standard Not Met',
]


def probe_url_exists(url: str, timeout: int = 10, max_retries: int = 3) -> bool:
    """Checks if a remote URL exists using an HTTP HEAD probe with retries for transient errors."""
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url,
                                         headers={'User-Agent': USER_AGENT},
                                         method='HEAD')
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status == 200
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            logging.warning('HTTP error %d probing %s (attempt %d/%d)', e.code,
                            url, attempt + 1, max_retries)
            if attempt < max_retries - 1 and e.code in (429, 500, 502, 503,
                                                        504):
                time.sleep(2**attempt)
                continue
            return False
        except urllib.error.URLError as e:
            logging.warning('Network error probing %s (attempt %d/%d): %s', url,
                            attempt + 1, max_retries, e)
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
                continue
            return False
        except Exception as e:
            logging.warning('Unexpected error probing %s: %s', url, e)
            return False
    return False


def download_url_with_retries(url: str,
                              target_file: str,
                              timeout: int = 180,
                              max_retries: int = 3) -> None:
    """Downloads a remote URL to target_file atomically with retry and exponential backoff."""
    target_dir = os.path.dirname(os.path.abspath(target_file))
    os.makedirs(target_dir, exist_ok=True)

    for attempt in range(max_retries):
        temp_file = tempfile.NamedTemporaryFile(dir=target_dir,
                                                suffix='.zip.tmp',
                                                delete=False)
        try:
            req = urllib.request.Request(url,
                                         headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                shutil.copyfileobj(resp, temp_file)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_file.close()
            os.replace(temp_file.name, target_file)
            return
        except Exception as e:
            temp_file.close()
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            logging.warning('Download attempt %d/%d failed for %s: %s',
                            attempt + 1, max_retries, url, e)
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
            else:
                raise


def discover_year_urls(year: int) -> tuple[str, str] | None:
    """Discovers or resolves zip filenames for a given year."""
    if year in KNOWN_YEAR_URL_MAP:
        return KNOWN_YEAR_URL_MAP[year]

    # For subsequent calendar years, probe standard version naming (v1 through v4)
    for v in range(1, 5):
        all_groups = f'sb_ca{year}_all_csv_v{v}.zip'
        all_students = f'sb_ca{year}_1_csv_v{v}.zip'
        if probe_url_exists(BASE_URL + all_students):
            logging.info('Discovered CAASPP data files for year %d: %s, %s',
                         year, all_groups, all_students)
            return (all_groups, all_students)
    return None


def get_all_available_years() -> list[int]:
    """Returns all known historical years plus any dynamically discovered newer years."""
    available = set(KNOWN_YEAR_URL_MAP.keys())
    current_year = datetime.now().year
    # Probe any years beyond known historical years up to current year + 1
    for y in range(max(available) + 1, current_year + 2):
        if discover_year_urls(y):
            available.add(y)
    return sorted(available)


def parse_years(years_str: str) -> list[int]:
    """Parses year specification into a sorted list of ints."""
    all_years = get_all_available_years()
    if years_str.strip().lower() in ('all', '*'):
        return all_years

    years = set()
    for part in years_str.split(','):
        part = part.strip()
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                for y in range(int(start.strip()), int(end.strip()) + 1):
                    if y in all_years or discover_year_urls(y):
                        years.add(y)
            except ValueError:
                logging.warning('Invalid year range format: %s', part)
        elif part.isdigit():
            y = int(part)
            if y in all_years or discover_year_urls(y):
                years.add(y)
            else:
                logging.warning('Year %d not available from source.', y)
    return sorted(years)


def normalize_and_filter_stream(text_stream, keep_all_entities: bool = False):
    """Yields normalized CAASPP records row-by-row from a text stream."""
    first_line = text_stream.readline()
    if not first_line:
        return

    delim = '^' if '^' in first_line else ','
    text_stream.seek(0)
    reader = csv.DictReader(text_stream, delimiter=delim)

    for r in reader:
        # Strip quotes and whitespace from all keys/values
        cleaned = {
            k.strip().strip('"'): (v.strip().strip('"') if v else '')
            for k, v in r.items()
            if k
        }

        # Check entity level:
        # In CAASPP research files, Type ID 4 = State, 5 = County.
        # State and County aggregates have District Code 00000 and School Code 0000000.
        if not keep_all_entities:
            type_id = cleaned.get('Type ID', '').strip()
            if type_id:
                if type_id not in ('4', '5'):
                    continue
            else:
                d_code = cleaned.get('District Code', '').strip()
                s_code = cleaned.get('School Code', '').strip()
                if not (d_code and s_code and set(d_code) == {'0'} and
                        set(s_code) == {'0'}):
                    continue

        # Handle subgroup ID variations across eras
        gid = cleaned.get('Student Group ID') or cleaned.get(
            'Subgroup ID') or ''
        # Handle test ID variations
        tid = cleaned.get('Test ID') or cleaned.get('Test Id') or ''
        # Handle count of tested with scores variations
        scores = cleaned.get('Total Students Tested with Scores'
                            ) or cleaned.get('Students with Scores') or ''

        row = [
            cleaned.get('County Code', ''),
            cleaned.get('Test Year', ''),
            gid,
            cleaned.get('Grade', ''),
            tid,
            scores,
            cleaned.get('Mean Scale Score', ''),
            cleaned.get('Percentage Standard Exceeded', ''),
            cleaned.get('Percentage Standard Met', ''),
            cleaned.get('Percentage Standard Met and Above', ''),
            cleaned.get('Percentage Standard Nearly Met', ''),
            cleaned.get('Percentage Standard Not Met', ''),
        ]
        yield row


def normalize_and_filter_records(raw_bytes: bytes,
                                 keep_all_entities: bool = False
                                ) -> list[list[str]]:
    """Normalizes raw CAASPP records across all eras into unified columns."""
    text_io = io.StringIO(raw_bytes.decode('latin1'))
    return list(
        normalize_and_filter_stream(text_io,
                                    keep_all_entities=keep_all_entities))


def download_and_process_year(
    year: int,
    data_mode: str,
    output_dir: str,
    keep_all_entities: bool,
    raw_dir: str = '',
    out_filename: str = '',
) -> str:
    """Downloads and preserves raw zip, streams normalized records, and saves output atomically."""
    urls = discover_year_urls(year)
    if not urls:
        raise RuntimeError(f'Year {year} is not available from CAASPP portal.')

    all_groups_file, all_students_file = urls
    filename = all_groups_file if data_mode == 'all_groups' else all_students_file
    url = BASE_URL + filename

    if not raw_dir:
        raw_dir = os.path.join(os.path.dirname(os.path.abspath(output_dir)),
                               'raw_files')
    os.makedirs(raw_dir, exist_ok=True)
    raw_zip_path = os.path.join(raw_dir, filename)

    if not os.path.exists(raw_zip_path) or os.path.getsize(raw_zip_path) == 0:
        logging.info('Fetching Year %d raw zip: %s', year, url)
        download_url_with_retries(url, raw_zip_path)
    else:
        logging.info('Year %d: Using preserved raw archive: %s', year,
                     raw_zip_path)

    out_name = out_filename or f'sb_ca{year}_normalized.txt'
    out_file = os.path.join(output_dir, out_name)
    temp_out = tempfile.NamedTemporaryFile('w',
                                           dir=output_dir,
                                           delete=False,
                                           encoding='utf-8',
                                           newline='',
                                           suffix='.tmp')
    row_count = 0

    try:
        with zipfile.ZipFile(raw_zip_path, 'r') as z:
            candidates = [
                f for f in z.namelist()
                if f.startswith(f'sb_ca{year}') and 'entities' not in f
            ]
            if not candidates:
                raise RuntimeError(
                    f'No matching data file found in zip for year {year}')

            writer = csv.writer(temp_out, delimiter='^')
            writer.writerow(UNIFIED_HEADER)
            with z.open(candidates[0]) as member_file:
                text_stream = io.TextIOWrapper(member_file, encoding='latin1')
                for row in normalize_and_filter_stream(
                        text_stream, keep_all_entities=keep_all_entities):
                    writer.writerow(row)
                    row_count += 1

        temp_out.flush()
        os.fsync(temp_out.fileno())
        temp_out.close()
        os.replace(temp_out.name, out_file)
    except Exception:
        temp_out.close()
        if os.path.exists(temp_out.name):
            os.unlink(temp_out.name)
        raise

    logging.info('Year %d: Extracted %d normalized rows -> %s', year, row_count,
                 out_file)
    return out_file


def main(argv):
    del argv  # Unused.

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = FLAGS.output_dir or os.path.join(script_dir, 'input_files')
    raw_dir = FLAGS.raw_dir or os.path.join(script_dir, 'raw_files')
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(raw_dir, exist_ok=True)

    if FLAGS.clean:
        logging.info('Cleaning output directory: %s', output_dir)
        for item in os.listdir(output_dir):
            p = os.path.join(output_dir, item)
            if os.path.isfile(p) or os.path.islink(p):
                os.unlink(p)
            elif os.path.isdir(p):
                shutil.rmtree(p)

    if FLAGS.test_mode:
        logging.info('Test mode: downloading 2024 sample...')
        test_file = download_and_process_year(
            2024,
            'all_students',
            output_dir,
            FLAGS.keep_all_entities,
            raw_dir=raw_dir,
            out_filename='sb_ca_test_normalized.txt',
        )
        logging.info('Test mode completed. Created test file: %s', test_file)
        logging.info('Master all-years file was not modified in test mode.')
        return

    years = parse_years(FLAGS.years)
    logging.info('Target years to download and process: %s', years)

    all_normalized_files = []
    failed_years = []
    for year in years:
        try:
            res = download_and_process_year(
                year,
                FLAGS.data_mode,
                output_dir,
                FLAGS.keep_all_entities,
                raw_dir=raw_dir,
            )
            if res:
                all_normalized_files.append(res)
        except Exception as e:
            logging.error('Error processing year %d: %s', year, e)
            failed_years.append((year, str(e)))

    if failed_years:
        raise RuntimeError(
            f'Import aborted due to download failures for years: {failed_years}'
        )

    if not all_normalized_files:
        raise RuntimeError(
            'No files were successfully downloaded and processed.')

    # Only combine into master multi-year file if all years were requested.
    # Single-year or subset downloads must NOT overwrite the consolidated master dataset.
    if FLAGS.years.strip().lower() in ('all', '*'):
        master_file = os.path.join(output_dir, 'sb_ca_all_years_normalized.txt')
        temp_master = tempfile.NamedTemporaryFile('w',
                                                  dir=output_dir,
                                                  delete=False,
                                                  encoding='utf-8',
                                                  newline='',
                                                  suffix='.tmp')
        total_master_rows = 0
        try:
            writer = csv.writer(temp_master, delimiter='^')
            writer.writerow(UNIFIED_HEADER)
            for nf in all_normalized_files:
                with open(nf, 'r', encoding='utf-8') as f_in:
                    reader = csv.reader(f_in, delimiter='^')
                    next(reader)  # Skip header
                    for row in reader:
                        writer.writerow(row)
                        total_master_rows += 1
            temp_master.flush()
            os.fsync(temp_master.fileno())
            temp_master.close()
            os.replace(temp_master.name, master_file)
        except Exception:
            temp_master.close()
            if os.path.exists(temp_master.name):
                os.unlink(temp_master.name)
            raise

        logging.info(
            'Created master multi-year file: %s (%d records across %d years)',
            master_file, total_master_rows, len(all_normalized_files))
    else:
        logging.info(
            'Individual year processing completed for: %s. Master multi-year file was not modified.',
            [os.path.basename(f) for f in all_normalized_files])


if __name__ == '__main__':
    app.run(main)
