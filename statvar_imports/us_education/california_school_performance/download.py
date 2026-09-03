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
(2015–2019, 2021–2025; 2020 was cancelled statewide due to COVID-19).

It automatically handles differences in delimiter (comma vs caret) and column naming across
eras, filters State and County aggregate records, and normalizes them into a unified format
ready for processing by Data Commons stat_var_processor.py.

Usage:
  python3 download.py --years=all
  python3 download.py --years=2015-2024
  python3 download.py --years=2024
  python3 download.py --test_mode
"""

import csv
import io
import os
import shutil
import sys
import urllib.request
import zipfile
from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'years',
    'all',
    'Years to download: "all" (2015-2025, skipping 2020), range e.g. "2015-2024", or comma-separated "2023,2024".',
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

# Exact official zip filename per year: (all_subgroups_zip, all_students_zip)
YEAR_URL_MAP = {
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

ALL_AVAILABLE_YEARS = sorted(YEAR_URL_MAP.keys())

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


def parse_years(years_str: str) -> list[int]:
    """Parses year specification into a sorted list of ints."""
    if years_str.strip().lower() in ('all', '*'):
        return list(ALL_AVAILABLE_YEARS)

    years = set()
    for part in years_str.split(','):
        part = part.strip()
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                for y in range(int(start.strip()), int(end.strip()) + 1):
                    if y in YEAR_URL_MAP:
                        years.add(y)
            except ValueError:
                logging.warning('Invalid year range format: %s', part)
        elif part.isdigit() and int(part) in YEAR_URL_MAP:
            years.add(int(part))
    return sorted(years)


def normalize_and_filter_records(raw_bytes: bytes, keep_all_entities: bool = False) -> list[list[str]]:
    """Normalizes raw CAASPP records across all eras into unified columns."""
    text_io = io.StringIO(raw_bytes.decode('latin1'))
    first_line = text_io.readline()
    if not first_line:
        return []

    delim = '^' if '^' in first_line else ','
    text_io.seek(0)
    reader = csv.DictReader(text_io, delimiter=delim)

    rows = []
    for r in reader:
        # Strip quotes and whitespace from all keys/values
        cleaned = {k.strip().strip('"'): (v.strip().strip('"') if v else '') for k, v in r.items() if k}

        # Check entity level: State and County have District Code 00000 and School Code 0000000
        d_code = cleaned.get('District Code', '')
        s_code = cleaned.get('School Code', '')
        if not keep_all_entities and (
            d_code.strip().lstrip('0') or s_code.strip().lstrip('0')
        ):
            continue

        # Handle subgroup ID variations across eras
        gid = cleaned.get('Student Group ID') or cleaned.get('Subgroup ID') or ''
        # Handle test ID variations
        tid = cleaned.get('Test ID') or cleaned.get('Test Id') or ''
        # Handle count of tested with scores variations
        scores = cleaned.get('Total Students Tested with Scores') or cleaned.get('Students with Scores') or ''

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
        rows.append(row)

    return rows


def download_and_process_year(year: int, data_mode: str, output_dir: str, keep_all_entities: bool) -> str:
    """Downloads zip for a given year, normalizes records, and saves sb_ca{year}_normalized.txt."""
    if year not in YEAR_URL_MAP:
        logging.warning('Year %d not supported.', year)
        return ''

    all_groups_file, all_students_file = YEAR_URL_MAP[year]
    filename = all_groups_file if data_mode == 'all_groups' else all_students_file
    url = BASE_URL + filename

    logging.info('Fetching Year %d: %s', year, url)
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            content = resp.read()
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                # Find the main data file in zip
                candidates = [f for f in z.namelist() if f.startswith(f'sb_ca{year}') and 'entities' not in f]
                if not candidates:
                    logging.error('No matching data file found in zip for year %d', year)
                    return ''
                raw_bytes = z.read(candidates[0])
    except Exception as e:
        logging.error('Failed to download %s: %s', url, e)
        return ''

    normalized_rows = normalize_and_filter_records(raw_bytes, keep_all_entities=keep_all_entities)
    logging.info('Year %d: Extracted %d normalized rows', year, len(normalized_rows))

    out_file = os.path.join(output_dir, f'sb_ca{year}_normalized.txt')
    with open(out_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='^')
        writer.writerow(UNIFIED_HEADER)
        writer.writerows(normalized_rows)

    return out_file


def download_lookups(target_dir: str):
    """Downloads common metadata lookup tables (Student Groups and Tests)."""
    for lookup in ['StudentGroups.zip', 'Tests.zip']:
        url = BASE_URL + lookup
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                with zipfile.ZipFile(io.BytesIO(resp.read())) as z:
                    z.extractall(target_dir)
        except Exception as e:
            logging.warning('Could not download lookup %s: %s', lookup, e)


def main(argv):
    del argv  # Unused.

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = FLAGS.output_dir or os.path.join(script_dir, 'input_files')
    os.makedirs(output_dir, exist_ok=True)

    if FLAGS.clean:
        logging.info('Cleaning output directory: %s', output_dir)
        for item in os.listdir(output_dir):
            p = os.path.join(output_dir, item)
            if os.path.isfile(p) or os.path.islink(p):
                os.unlink(p)
            elif os.path.isdir(p):
                shutil.rmtree(p)

    logging.info('Downloading CAASPP metadata lookups...')
    download_lookups(output_dir)

    if FLAGS.test_mode:
        logging.info('Test mode: downloading 2024 sample...')
        download_and_process_year(2024, 'all_students', output_dir, FLAGS.keep_all_entities)
        return

    years = parse_years(FLAGS.years)
    logging.info('Target years to download and process: %s', years)

    all_normalized_files = []
    for year in years:
        res = download_and_process_year(year, FLAGS.data_mode, output_dir, FLAGS.keep_all_entities)
        if res:
            all_normalized_files.append(res)

    if not all_normalized_files:
        raise RuntimeError('No files were successfully downloaded and processed.')

    # Combine all downloaded years into a unified master file
    master_file = os.path.join(output_dir, 'sb_ca_all_years_normalized.txt')
    total_master_rows = 0
    with open(master_file, 'w', encoding='utf-8', newline='') as f_out:
        writer = csv.writer(f_out, delimiter='^')
        writer.writerow(UNIFIED_HEADER)
        for nf in all_normalized_files:
            with open(nf, 'r', encoding='utf-8') as f_in:
                reader = csv.reader(f_in, delimiter='^')
                next(reader)  # Skip header
                for row in reader:
                    writer.writerow(row)
                    total_master_rows += 1

    logging.info('Created master multi-year file: %s (%d records across %d years)',
                 master_file, total_master_rows, len(all_normalized_files))


if __name__ == '__main__':
    app.run(main)
