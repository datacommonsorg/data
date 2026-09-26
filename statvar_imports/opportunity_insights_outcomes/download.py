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
"""Downloads Opportunity Insights (Opportunity Atlas) raw CSV files into raw_data/."""

import os
import re
import shutil
import time
import urllib.error
import urllib.request
import zipfile
from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

flags.DEFINE_string(
    'output_dir',
    os.path.join(_MODULE_DIR, 'raw_data'),
    'Directory where raw Opportunity Insights CSV files will be stored.',
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
        'url': 'https://opportunityinsights.org/wp-content/uploads/2018/10/cz_outcomes.csv',
        'pattern': r'https://opportunityinsights\.org/wp-content/uploads/[^"\'>\s]+/cz_outcomes\.csv',
        'is_zip': False,
    },
    'county_outcomes.csv': {
        'url': 'https://opportunityinsights.org/wp-content/uploads/2018/10/county_outcomes.zip',
        'pattern': r'https://opportunityinsights\.org/wp-content/uploads/[^"\'>\s]+/county_outcomes\.zip',
        'is_zip': True,
    },
    'tract_outcomes.csv': {
        'url': 'https://opportunityinsights.org/wp-content/uploads/2018/10/tract_outcomes.zip',
        'pattern': r'https://opportunityinsights\.org/wp-content/uploads/[^"\'>\s]+/tract_outcomes\.zip',
        'is_zip': True,
    },
    'tract_outcomes_late_simple.csv': {
        'url': 'https://opportunityinsights.org/wp-content/uploads/2024/08/tract_outcomes_late_simple.csv',
        'pattern': r'https://opportunityinsights\.org/wp-content/uploads/[^"\'>\s]+/tract_outcomes_late_simple\.csv',
        'is_zip': False,
    },
    'county_by_cohort_outcomes.csv': {
        'url': 'https://opportunityinsights.org/wp-content/uploads/2024/07/Table_3_County_by_Cohort_Estimates.csv',
        'pattern': r'https://opportunityinsights\.org/wp-content/uploads/[^"\'>\s]+/Table_3_County_by_Cohort_Estimates\.csv',
        'is_zip': False,
    },
    'cz_by_cohort_outcomes.csv': {
        'url': 'https://opportunityinsights.org/wp-content/uploads/2024/07/Table_4_cz_by_cohort_estimates.csv',
        'pattern': r'https://opportunityinsights\.org/wp-content/uploads/[^"\'>\s]+/Table_4_cz_by_cohort_estimates\.csv',
        'is_zip': False,
    },
}


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


def download_file(
    url: str,
    dest_path: str,
    max_retries: int = 3,
    retry_backoff_sec: float = 1.0,
) -> None:
    """Downloads a URL to dest_path atomically with bounded retries and a browser User-Agent."""
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    tmp_path = f'{dest_path}.tmp'
    for attempt in range(1, max_retries + 1):
        logging.info(
            'Downloading %s -> %s (attempt %d/%d)',
            url,
            dest_path,
            attempt,
            max_retries,
        )
        try:
            req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=300) as response, open(
                tmp_path, 'wb'
            ) as out_file:
                shutil.copyfileobj(response, out_file)
            os.replace(tmp_path, dest_path)
            return
        except Exception as exc:  # pylint: disable=broad-except
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if attempt >= max_retries:
                raise
            sleep_sec = retry_backoff_sec * (2 ** (attempt - 1))
            logging.warning(
                'Download failed for %s (%s); retrying in %.1fs...',
                url,
                exc,
                sleep_sec,
            )
            time.sleep(sleep_sec)


def extract_csv_from_zip(zip_path: str, target_csv_path: str) -> None:
    """Extracts the primary CSV file from a ZIP archive atomically, or moves it if already uncompressed CSV."""
    tmp_csv_path = f'{target_csv_path}.tmp'
    if zipfile.is_zipfile(zip_path):
        try:
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
                with zf.open(member) as src, open(tmp_csv_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
            os.replace(tmp_csv_path, target_csv_path)
            os.remove(zip_path)
        except Exception:
            if os.path.exists(tmp_csv_path):
                os.remove(tmp_csv_path)
            raise
    else:
        logging.info(
            '%s is already an uncompressed CSV file; moving -> %s',
            zip_path,
            target_csv_path,
        )
        os.replace(zip_path, target_csv_path)


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
    download_all_sources(FLAGS.output_dir, FLAGS.source_page_url)


if __name__ == '__main__':
    app.run(main)
