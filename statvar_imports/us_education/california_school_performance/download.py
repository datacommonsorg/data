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
and streams normalization into a unified format ready for processing by process.py.

Usage:
  python3 download.py --years=all
  python3 download.py --years=2015-2024
  python3 download.py --years=2024
  python3 download.py --test_mode
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime
import io
import json
import os
import shutil
import sys
import tempfile
import time
import zipfile
from absl import app
from absl import flags
from absl import logging
import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '../../../'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from util.download_util_script import download_file

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'years',
    '2023-present',
    'Years to download: "2023-present" (post-2022 active years; 2015-2022 are in GCS historic/), "all" (2015-present, skipping 2020), range e.g. "2015-2024", or comma-separated "2023,2024".',
)
flags.DEFINE_enum(
    'data_mode',
    'all_groups',
    ['all_students', 'all_groups'],
    'Data scope: "all_groups" downloads all 55 demographic subgroups (~100MB/yr); "all_students" downloads group 1 only (~5MB/yr).',
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
    True,
    'If true, keeps all entities (State, Counties, School Districts, and Schools). Defaults to True.',
)

BASE_URL = 'https://caaspp-elpac.ets.org/caaspp/researchfiles/'
USER_AGENT = 'Mozilla/5.0 (DataCommons Ingestion Bot)'

_HTTP_SESSION: requests.Session | None = None
_SCHOOL_CODE_MAP: dict[str, str] | None = None


def _get_http_session() -> requests.Session:
    """Returns a shared requests.Session for HTTP connection pooling."""
    global _HTTP_SESSION
    if _HTTP_SESSION is None:
        _HTTP_SESSION = requests.Session()
        _HTTP_SESSION.headers.update({'User-Agent': USER_AGENT})
    return _HTTP_SESSION


def get_school_code_map() -> dict[str, str]:
    """Loads and caches the CDS-to-DCID place mapping from config/school_code_mapping.json."""
    global _SCHOOL_CODE_MAP
    if _SCHOOL_CODE_MAP is None:
        map_path = os.path.join(_SCRIPT_DIR, 'config',
                                'school_code_mapping.json')
        if os.path.exists(map_path):
            with open(map_path, 'r', encoding='utf-8') as f:
                _SCHOOL_CODE_MAP = json.load(f)
        else:
            logging.warning('School code mapping file not found at %s',
                            map_path)
            _SCHOOL_CODE_MAP = {}
    return _SCHOOL_CODE_MAP


# Known historical official zip filename per year: (all_subgroups_zip, all_students_zip).
# Recent years (>=2022) and future years (>2025) also support dynamic version probing
# from v4 down to v1 via discover_year_urls().
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
    'District Code',
    'School Code',
    'Place',
    'Test Year',
    'Student Group ID',
    'Grade',
    'Test ID',
    'Total Students Tested',
    'Mean Scale Score',
    'Percentage Standard Exceeded',
    'Percentage Standard Met',
    'Percentage Standard Met and Above',
    'Percentage Standard Nearly Met',
    'Percentage Standard Not Met',
]


def probe_url_exists(url: str, timeout: int = 10, max_retries: int = 3) -> bool:
    """Checks if a remote URL exists using an HTTP HEAD probe with retries for transient errors."""
    session = _get_http_session()
    for attempt in range(max_retries):
        try:
            resp = session.head(url,
                                headers={'User-Agent': USER_AGENT},
                                allow_redirects=True,
                                timeout=timeout)
            if resp.status_code == 200:
                return True
            if resp.status_code == 404:
                return False
            logging.warning('HTTP error %d probing %s (attempt %d/%d)',
                            resp.status_code, url, attempt + 1, max_retries)
            if attempt < max_retries - 1 and resp.status_code in (429, 500, 502,
                                                                  503, 504):
                time.sleep(2**attempt)
                continue
            return False
        except requests.exceptions.RequestException as e:
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


def discover_year_urls(
    year: int,
    data_mode: str = 'all_students',
    probe_latest: bool = False,
) -> tuple[str, str] | None:
    """Discovers or resolves zip filenames for a given year and data_mode."""
    if year in KNOWN_YEAR_URL_MAP and not probe_latest:
        return KNOWN_YEAR_URL_MAP[year]

    # Probe standard version naming in descending order (v4 down to v1)
    # so that the highest available revision (e.g. v2 superseding v1) is selected.
    for v in range(4, 0, -1):
        all_groups = f'sb_ca{year}_all_csv_v{v}.zip'
        all_students = f'sb_ca{year}_1_csv_v{v}.zip'
        target_file = all_groups if data_mode == 'all_groups' else all_students
        if probe_url_exists(BASE_URL + target_file):
            logging.info('Discovered CAASPP data files for year %d: %s, %s',
                         year, all_groups, all_students)
            return (all_groups, all_students)

    if year in KNOWN_YEAR_URL_MAP:
        return KNOWN_YEAR_URL_MAP[year]
    return None


def get_all_available_years(data_mode: str = 'all_groups') -> list[int]:
    """Returns all known historical years plus any dynamically discovered newer years."""
    available = set(KNOWN_YEAR_URL_MAP.keys())
    current_year = datetime.now().year
    # Probe any years beyond known historical years up to current year + 1
    for y in range(max(available) + 1, current_year + 2):
        if discover_year_urls(y, data_mode=data_mode):
            available.add(y)
    return sorted(available)


def parse_years(years_str: str, data_mode: str = 'all_groups') -> list[int]:
    """Parses year specification into a sorted list of ints."""
    stripped = years_str.strip().lower()
    if stripped in ('all', '*'):
        return get_all_available_years(data_mode=data_mode)

    all_years: list[int] | None = None

    def _is_year_available(y: int) -> bool:
        if y in KNOWN_YEAR_URL_MAP:
            return True
        if all_years is not None:
            return y in all_years
        return bool(discover_year_urls(y, data_mode=data_mode))

    years = set()
    for part in years_str.split(','):
        part = part.strip()
        if '-' in part:
            try:
                start_str, end_str = part.split('-', 1)
                start_year = int(start_str.strip())
                end_token = end_str.strip().lower()
                if end_token in ('', 'present', 'latest', 'now'):
                    if all_years is None:
                        all_years = get_all_available_years(data_mode=data_mode)
                    end_year = (max(all_years)
                                if all_years else datetime.now().year)
                else:
                    end_year = int(end_token)
                for y in range(start_year, end_year + 1):
                    if _is_year_available(y):
                        years.add(y)
            except ValueError:
                logging.warning('Invalid year range format: %s', part)
        elif part.isdigit():
            y = int(part)
            if _is_year_available(y):
                years.add(y)
            else:
                logging.warning('Year %d not available from source.', y)
    return sorted(years)


def resolve_place_dcid(county_code: str,
                       district_code: str,
                       school_code: str,
                       school_map: dict[str, str] | None = None) -> str:
    """Resolves a California CDS code triplet to its Data Commons place DCID."""
    if school_map is None:
        school_map = get_school_code_map()
    c_code = county_code.strip().zfill(2) if county_code.strip() else '00'
    d_code = district_code.strip().zfill(
        5) if district_code.strip() else '00000'
    s_code = school_code.strip().zfill(7) if school_code.strip() else '0000000'
    ca_id = f'CA-{c_code}{d_code}-{s_code}'
    if ca_id in school_map:
        return school_map[ca_id]
    if d_code == '00000' and s_code == '0000000':
        if c_code == '00':
            return 'geoId/06'
        if c_code.isdigit() and 1 <= int(c_code) <= 58:
            return f'geoId/06{int(c_code) * 2 - 1:03d}'
    return ca_id


def normalize_and_filter_stream(text_stream, keep_all_entities: bool = True):
    """Yields normalized CAASPP records row-by-row from a text stream."""
    first_line = text_stream.readline()
    if not first_line:
        return

    delim = '^' if '^' in first_line else ','
    text_stream.seek(0)
    reader = csv.reader(text_stream, delimiter=delim)
    raw_header = next(reader, None)
    if not raw_header:
        return

    col_map = {
        col.strip().strip('"'): idx for idx, col in enumerate(raw_header)
    }

    def _idx(*names: str) -> int:
        for name in names:
            if name in col_map:
                return col_map[name]
        return -1

    c_idx = _idx('County Code')
    d_idx = _idx('District Code')
    s_idx = _idx('School Code')
    type_idx = _idx('Type ID')
    place_idx = _idx('Place')
    yr_idx = _idx('Test Year')
    gid_idx = _idx('Student Group ID', 'Subgroup ID')
    gr_idx = _idx('Grade')
    tid_idx = _idx('Test ID', 'Test Id')
    tested_idx = _idx(
        'Total Students Tested',
        'Students Tested',
        'Total Students Tested with Scores',
        'Students with Scores',
    )
    mean_idx = _idx('Mean Scale Score')
    exc_idx = _idx('Percentage Standard Exceeded')
    met_idx = _idx('Percentage Standard Met')
    met_abv_idx = _idx('Percentage Standard Met and Above')
    nearly_idx = _idx('Percentage Standard Nearly Met')
    not_met_idx = _idx('Percentage Standard Not Met')

    missing_cols = []
    if place_idx < 0 and (c_idx < 0 or d_idx < 0 or s_idx < 0):
        missing_cols.append(
            'Place or (County Code, District Code, School Code)')
    if yr_idx < 0:
        missing_cols.append('Test Year')
    if gid_idx < 0:
        missing_cols.append('Student Group ID / Subgroup ID')
    if gr_idx < 0:
        missing_cols.append('Grade')
    if tid_idx < 0:
        missing_cols.append('Test ID / Test Id')
    if all(idx < 0 for idx in (
            tested_idx,
            mean_idx,
            exc_idx,
            met_idx,
            met_abv_idx,
            nearly_idx,
            not_met_idx,
    )):
        missing_cols.append('assessment metric columns')
    if missing_cols:
        raise ValueError(
            f'Missing required CAASPP columns {missing_cols} in header: {raw_header}'
        )

    school_map = get_school_code_map()

    def _clean_metric(idx: int, n_cols: int, row: list[str]) -> str:
        if 0 <= idx < n_cols:
            val = row[idx].strip().strip('"')
            return '' if val == '*' else val
        return ''

    for r in reader:
        n_cols = len(r)
        if n_cols == 0:
            continue

        c_code = r[c_idx].strip().strip('"') if 0 <= c_idx < n_cols else ''
        d_code = r[d_idx].strip().strip('"') if 0 <= d_idx < n_cols else ''
        s_code = r[s_idx].strip().strip('"') if 0 <= s_idx < n_cols else ''

        if not keep_all_entities:
            type_id = (r[type_idx].strip().strip('"')
                       if 0 <= type_idx < n_cols else '')
            if type_id:
                if type_id not in ('4', '5'):
                    continue
            else:
                if not (d_code and s_code and set(d_code) == {'0'} and
                        set(s_code) == {'0'}):
                    continue

        place = (r[place_idx].strip().strip('"')
                 if 0 <= place_idx < n_cols else '')
        if not place:
            place = resolve_place_dcid(c_code, d_code, s_code, school_map)

        yield [
            c_code.zfill(2) if c_code else '',
            d_code.zfill(5) if d_code else '',
            s_code.zfill(7) if s_code else '',
            place,
            r[yr_idx].strip().strip('"') if 0 <= yr_idx < n_cols else '',
            r[gid_idx].strip().strip('"') if 0 <= gid_idx < n_cols else '',
            r[gr_idx].strip().strip('"') if 0 <= gr_idx < n_cols else '',
            r[tid_idx].strip().strip('"') if 0 <= tid_idx < n_cols else '',
            _clean_metric(tested_idx, n_cols, r),
            _clean_metric(mean_idx, n_cols, r),
            _clean_metric(exc_idx, n_cols, r),
            _clean_metric(met_idx, n_cols, r),
            _clean_metric(met_abv_idx, n_cols, r),
            _clean_metric(nearly_idx, n_cols, r),
            _clean_metric(not_met_idx, n_cols, r),
        ]


def normalize_and_filter_records(raw_bytes: bytes,
                                 keep_all_entities: bool = True
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
    urls = discover_year_urls(
        year,
        data_mode=data_mode,
        probe_latest=(year >= 2022),
    )
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

    if not (os.path.exists(raw_zip_path) and zipfile.is_zipfile(raw_zip_path)):
        if os.path.exists(raw_zip_path):
            logging.warning(
                'Corrupt or incomplete archive detected; re-downloading: %s',
                raw_zip_path)
            try:
                os.unlink(raw_zip_path)
            except OSError:
                pass
        logging.info('Fetching Year %d raw zip: %s', year, url)
        if not download_file(url=url,
                             output_folder=raw_dir,
                             unzip=False,
                             headers={'User-Agent': USER_AGENT}):
            raise RuntimeError(f'Failed to download {url}')
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
        try:
            test_file = download_and_process_year(
                2024,
                'all_students',
                output_dir,
                FLAGS.keep_all_entities,
                raw_dir=raw_dir,
                out_filename='sb_ca_test_normalized.txt',
            )
        except Exception as e:
            logging.fatal('Test mode download failed: %s', e)
        logging.info('Test mode completed. Created test file: %s', test_file)
        logging.info('Master all-years file was not modified in test mode.')
        return

    years = parse_years(FLAGS.years, data_mode=FLAGS.data_mode)
    logging.info('Target years to download and process: %s', years)

    year_to_file: dict[int, str] = {}
    failed_years = []
    max_workers = min(len(years), 6) if years else 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_year = {
            executor.submit(
                download_and_process_year,
                year,
                FLAGS.data_mode,
                output_dir,
                FLAGS.keep_all_entities,
                raw_dir,
            ):
                year for year in years
        }
        for future in as_completed(future_to_year):
            year = future_to_year[future]
            try:
                res = future.result()
                if res:
                    year_to_file[year] = res
            except Exception as e:
                logging.error('Error processing year %d: %s', year, e)
                failed_years.append((year, str(e)))

    if failed_years:
        logging.fatal(
            'Import aborted due to download failures for years: %s',
            sorted(failed_years),
        )

    all_normalized_files = [
        year_to_file[y] for y in sorted(year_to_file.keys())
    ]
    if not all_normalized_files:
        logging.fatal('No files were successfully downloaded and processed.')

    master_file = os.path.join(output_dir, 'sb_ca_all_years_normalized.txt')
    if (FLAGS.years.strip().lower() in ('all', '*') or '-' in FLAGS.years or
            len(all_normalized_files) > 1):
        temp_master = tempfile.NamedTemporaryFile('w',
                                                  dir=output_dir,
                                                  delete=False,
                                                  encoding='utf-8',
                                                  newline='',
                                                  suffix='.tmp')
        try:
            temp_master.write('^'.join(UNIFIED_HEADER) + '\n')
            for nf in all_normalized_files:
                with open(nf, 'r', encoding='utf-8') as f_in:
                    f_in.readline()  # Skip header line
                    shutil.copyfileobj(f_in, temp_master, length=1024 * 1024)
            temp_master.flush()
            os.fsync(temp_master.fileno())
            temp_master.close()
            os.replace(temp_master.name, master_file)
            for nf in all_normalized_files:
                if nf != master_file and os.path.exists(nf):
                    try:
                        os.unlink(nf)
                    except OSError:
                        pass
        except Exception as e:
            temp_master.close()
            if os.path.exists(temp_master.name):
                os.unlink(temp_master.name)
            logging.fatal('Failed to write master normalized file %s: %s',
                          master_file, e)

        logging.info('Created master multi-year file: %s across %d years',
                     master_file, len(all_normalized_files))
    else:
        single_file = all_normalized_files[0]
        if single_file != master_file:
            temp_link = f'{master_file}.tmp'
            if os.path.exists(temp_link):
                os.unlink(temp_link)
            try:
                os.link(single_file, temp_link)
            except OSError:
                shutil.copyfile(single_file, temp_link)
            os.replace(temp_link, master_file)
        logging.info(
            'Single-year processing completed: %s (also updated %s)',
            single_file,
            master_file,
        )


if __name__ == '__main__':
    app.run(main)
