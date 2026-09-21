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
"""Downloads and shards Opportunity Insights (Opportunity Atlas) CSVs for stat_var_processor.py."""

import collections
import csv
import os
import re
import shutil
import urllib.request
import zipfile
from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'output_dir',
    'raw_data',
    'Directory where raw Opportunity Insights CSV files will be stored.',
)
flags.DEFINE_string(
    'shard_dir',
    'input_files',
    'Directory where sharded wide CSV files for stat_var_processor.py will be written.',
)
flags.DEFINE_bool(
    'download',
    True,
    'Whether to download missing raw CSV files from opportunityinsights.org/data/.',
)
flags.DEFINE_integer(
    'max_rows_per_shard',
    5_000,
    'Maximum wide rows per output CSV shard for stat_var_processor.py.',
)
flags.DEFINE_string(
    'source_page_url',
    'https://opportunityinsights.org/data/',
    'Opportunity Insights data catalog page URL to scrape for latest download links.',
)

USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
)

DEFAULT_SOURCE_FILES = {
    'commuting_zone_outcomes.csv': {
        'url': 'https://opportunityinsights.org/wp-content/uploads/2018/10/cz_outcomes.zip',
        'is_zip': True,
        'pattern': r'https://opportunityinsights\.org/wp-content/uploads/[^"\'\s>]+/cz_outcomes\.zip',
    },
    'county_outcomes.csv': {
        'url': 'https://opportunityinsights.org/wp-content/uploads/2018/10/county_outcomes.zip',
        'is_zip': True,
        'pattern': r'https://opportunityinsights\.org/wp-content/uploads/[^"\'\s>]+/county_outcomes\.zip',
    },
    'tract_outcomes.csv': {
        'url': 'https://opportunityinsights.org/wp-content/uploads/2018/10/tract_outcomes.zip',
        'is_zip': True,
        'pattern': r'https://opportunityinsights\.org/wp-content/uploads/[^"\'\s>]+/tract_outcomes\.zip',
    },
    'tract_outcomes_late_simple.csv': {
        'url': 'https://opportunityinsights.org/wp-content/uploads/2024/07/tract_outcomes_late_simple.csv',
        'is_zip': False,
        'pattern': r'https://opportunityinsights\.org/wp-content/uploads/[^"\'\s>]+/tract_outcomes_late_simple\.csv',
    },
    'county_by_cohort_outcomes.csv': {
        'url': 'https://opportunityinsights.org/wp-content/uploads/2024/07/county_outcomes_by_cohort.zip',
        'is_zip': True,
        'pattern': r'https://opportunityinsights\.org/wp-content/uploads/[^"\'\s>]+/county_outcomes_by_cohort\.zip',
    },
    'cz_by_cohort_outcomes.csv': {
        'url': 'https://opportunityinsights.org/wp-content/uploads/2024/07/cz_outcomes_by_cohort.zip',
        'is_zip': True,
        'pattern': r'https://opportunityinsights\.org/wp-content/uploads/[^"\'\s>]+/cz_outcomes_by_cohort\.zip',
    },
}

DATASET_CONFIGS = [
    ('commuting_zone_outcomes.csv', 'commuting_zone', 'baseline_1978_1983'),
    ('county_outcomes.csv', 'county', 'baseline_1978_1983'),
    ('tract_outcomes.csv', 'tract', 'baseline_1978_1983'),
    ('tract_outcomes_late_simple.csv', 'tract', 'late_cohort_1984_1989'),
    ('county_by_cohort_outcomes.csv', 'county', 'annual_cohort_1978_1992'),
    ('cz_by_cohort_outcomes.csv', 'commuting_zone', 'annual_cohort_1978_1992'),
]

_NON_DATA_COLUMNS = frozenset({
    'state',
    'county',
    'tract',
    'cz',
    'czname',
    'cohort',
    'state_name',
    'county_name',
    'cz_name',
})

_MISSING_VALUE_PLACEHOLDERS = frozenset({'', 'NA', 'N/A', '.', 'NAN', 'NULL'})


def discover_latest_urls(page_url: str) -> dict[str, str]:
    """Scrapes the Opportunity Insights data page for the latest URLs, falling back to canonical links."""
    discovered = {k: v['url'] for k, v in DEFAULT_SOURCE_FILES.items()}
    try:
        req = urllib.request.Request(page_url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8', errors='ignore')
        for filename, spec in DEFAULT_SOURCE_FILES.items():
            matches = re.findall(spec['pattern'], html)
            if matches:
                discovered[filename] = matches[0]
                logging.info('Discovered URL for %s: %s', filename, matches[0])
    except Exception as exc:  # pylint: disable=broad-except
        logging.warning(
            'Could not scrape %s (%s); using canonical fallback URLs.', page_url, exc
        )
    return discovered


def download_file(url: str, dest_path: str) -> None:
    """Downloads a URL to dest_path with a browser User-Agent."""
    logging.info('Downloading %s -> %s', url, dest_path)
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as response, open(
        dest_path, 'wb'
    ) as out_file:
        shutil.copyfileobj(response, out_file)


def extract_csv_from_zip(zip_path: str, target_csv_path: str) -> None:
    """Extracts the primary CSV file from a ZIP archive, or moves it if already uncompressed CSV."""
    if zipfile.is_zipfile(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zf:
            csv_members = [
                m
                for m in zf.namelist()
                if m.lower().endswith('.csv') and '__MACOSX' not in m
            ]
            if not csv_members:
                raise ValueError(f'No CSV file found inside archive: {zip_path}')
            member = csv_members[0]
            logging.info(
                'Extracting %s from %s -> %s', member, zip_path, target_csv_path
            )
            with zf.open(member) as src, open(target_csv_path, 'wb') as dst:
                shutil.copyfileobj(src, dst)
        os.remove(zip_path)
    else:
        logging.info(
            '%s is already an uncompressed CSV file; moving -> %s',
            zip_path,
            target_csv_path,
        )
        shutil.move(zip_path, target_csv_path)


def format_geo_id(row: dict, geo_level: str) -> str:
    """Returns the Data Commons geoId dcid for a CSV row."""
    if geo_level == 'county':
        state = str(int(float(str(row['state']).strip()))).zfill(2)
        county = str(int(float(str(row['county']).strip()))).zfill(3)
        return f'geoId/{state}{county}'
    if geo_level == 'tract':
        state = str(int(float(str(row['state']).strip()))).zfill(2)
        county = str(int(float(str(row['county']).strip()))).zfill(3)
        tract = str(int(float(str(row['tract']).strip()))).zfill(6)
        return f'geoId/{state}{county}{tract}'
    if geo_level == 'commuting_zone':
        cz = str(int(float(str(row['cz']).strip()))).zfill(5)
        return f'geoId/cz{cz}'
    raise ValueError(f'Unsupported geo_level: {geo_level}')


def normalize_column_header(
    col: str, dataset_mode: str = 'baseline_1978_1983', cohort_token: str = ''
) -> str:
    """Normalizes non-outcome count column prefixes and appends cohort token for PVMAP word_delimiter."""
    race_pat = 'pooled|aian|asian|black|hisp|natam|white|other'
    gender_pat = 'pooled|male|female'

    kid_n_match = re.fullmatch(
        f'(?:kid_)?(({race_pat})_({gender_pat}))_(?:n|count)', col
    )
    if kid_n_match:
        base_col = f'kid_n_{kid_n_match.group(1)}'
        if dataset_mode == 'late_cohort_1984_1989':
            return f'{base_col}_latekidn'
        return f'{base_col}_{cohort_token}' if cohort_token else base_col

    blw_p50_match = re.fullmatch(
        f'(?:kid_)?(({race_pat})_({gender_pat}))_blw_p50_(?:n|count)', col
    )
    if blw_p50_match:
        base_col = f'kid_blw_p50_{blw_p50_match.group(1)}'
        return f'{base_col}_{cohort_token}' if cohort_token else base_col

    if dataset_mode == 'late_cohort_1984_1989':
        if col.startswith('jail_'):
            return f'{col}_latejail'
        return f'{col}_late'

    if cohort_token:
        return f'{col}_{cohort_token}'
    return col


def _get_shard_path(output_csv: str, shard_idx: int, suffix_tag: str = '') -> str:
    """Returns the output path for a given 0-based shard index."""
    if output_csv.endswith('_cleaned.csv'):
        base = output_csv[: -len('_cleaned.csv')]
        tag = f'_{suffix_tag}' if suffix_tag else ''
        if shard_idx == 0 and not tag:
            return output_csv
        return f'{base}{tag}_part_{shard_idx:03d}_cleaned.csv'
    stem, ext = os.path.splitext(output_csv)
    if shard_idx == 0 and not suffix_tag:
        return output_csv
    return f'{stem}_{suffix_tag}_part_{shard_idx:03d}{ext}'


def shard_wide_csv(
    input_csv: str,
    output_csv: str,
    geo_level: str,
    dataset_mode: str = 'baseline_1978_1983',
    max_rows_per_shard: int = 5_000,
) -> int:
    """Prepends geo_id, strips missing placeholders, and shards a wide CSV for stat_var_processor.py."""
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(input_csv, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        data_cols = [
            c for c in (reader.fieldnames or []) if c not in _NON_DATA_COLUMNS
        ]

        if dataset_mode == 'annual_cohort_1978_1992':
            cohort_rows = collections.defaultdict(list)
            for row in reader:
                raw_cohort = (row.get('cohort') or '').strip()
                if not raw_cohort:
                    continue
                cohort_str = str(int(float(raw_cohort)))
                cohort_rows[cohort_str].append(row)

            total_rows = 0
            for cohort_str, rows in sorted(cohort_rows.items()):
                cohort_token = f'c{cohort_str}'
                header = ['geo_id'] + [
                    normalize_column_header(c, dataset_mode, cohort_token)
                    for c in data_cols
                ]
                for shard_idx in range(0, max(1, len(rows)), max(1, max_rows_per_shard)):
                    chunk = rows[shard_idx : shard_idx + max_rows_per_shard]
                    shard_path = _get_shard_path(
                        output_csv, shard_idx // max(1, max_rows_per_shard), cohort_token
                    )
                    with open(shard_path, mode='w', encoding='utf-8', newline='') as out:
                        writer = csv.writer(out)
                        writer.writerow(header)
                        for row in chunk:
                            cleaned_vals = [
                                ''
                                if (row.get(c) or '').strip().upper()
                                in _MISSING_VALUE_PLACEHOLDERS
                                else (row.get(c) or '').strip()
                                for c in data_cols
                            ]
                            if any(cleaned_vals):
                                writer.writerow([format_geo_id(row, geo_level)] + cleaned_vals)
                                total_rows += 1
            return total_rows

        header = ['geo_id'] + [
            normalize_column_header(c, dataset_mode) for c in data_cols
        ]
        rows_written = 0
        shard_idx = 0
        shard_rows = 0
        outfile = open(
            _get_shard_path(output_csv, shard_idx),
            mode='w',
            encoding='utf-8',
            newline='',
        )
        try:
            writer = csv.writer(outfile)
            writer.writeheader() if hasattr(writer, 'writeheader') else writer.writerow(header)
            for row in reader:
                cleaned_vals = [
                    ''
                    if (row.get(c) or '').strip().upper()
                    in _MISSING_VALUE_PLACEHOLDERS
                    else (row.get(c) or '').strip()
                    for c in data_cols
                ]
                if not any(cleaned_vals):
                    continue
                if max_rows_per_shard > 0 and shard_rows >= max_rows_per_shard:
                    outfile.close()
                    shard_idx += 1
                    shard_rows = 0
                    outfile = open(
                        _get_shard_path(output_csv, shard_idx),
                        mode='w',
                        encoding='utf-8',
                        newline='',
                    )
                    writer = csv.writer(outfile)
                    writer.writerow(header)
                writer.writerow([format_geo_id(row, geo_level)] + cleaned_vals)
                rows_written += 1
                shard_rows += 1
        finally:
            outfile.close()
        return rows_written


def download_all_sources(
    output_dir: str, page_url: str = 'https://opportunityinsights.org/data/'
) -> list[str]:
    """Downloads and extracts all Opportunity Insights outcome CSVs into output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    urls = discover_latest_urls(page_url)
    downloaded_csvs = []

    for target_csv_name, spec in DEFAULT_SOURCE_FILES.items():
        url = urls[target_csv_name]
        target_csv_path = os.path.join(output_dir, target_csv_name)

        if spec['is_zip']:
            zip_path = os.path.join(output_dir, f'{target_csv_name}.zip')
            if not os.path.exists(zip_path) and not os.path.exists(target_csv_path):
                download_file(url, zip_path)
            if os.path.exists(zip_path):
                extract_csv_from_zip(zip_path, target_csv_path)
        else:
            if not os.path.exists(target_csv_path):
                download_file(url, target_csv_path)

        downloaded_csvs.append(target_csv_path)

    return downloaded_csvs


def main(_):
    os.makedirs(FLAGS.output_dir, exist_ok=True)
    os.makedirs(FLAGS.shard_dir, exist_ok=True)

    if FLAGS.download:
        download_all_sources(FLAGS.output_dir, FLAGS.source_page_url)

    for filename, geo_level, dataset_mode in DATASET_CONFIGS:
        input_path = os.path.join(FLAGS.output_dir, filename)
        if not os.path.exists(input_path):
            raise FileNotFoundError(
                f'Required input file not found for {filename}: {input_path}'
            )
        stem = os.path.splitext(filename)[0]
        output_path = os.path.join(FLAGS.shard_dir, f'{stem}_cleaned.csv')
        shard_wide_csv(
            input_path,
            output_path,
            geo_level,
            dataset_mode,
            max_rows_per_shard=FLAGS.max_rows_per_shard,
        )


if __name__ == '__main__':
    app.run(main)
