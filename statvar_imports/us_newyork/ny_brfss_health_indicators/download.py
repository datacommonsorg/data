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
"""Automated Multi-Year Downloader for NYS BRFSS Health Indicators by County and Region.

Downloads live county and region level health outcome indicators for New York State
from the NYSDOH Socrata Open Data API (jsy7-eb4n) across all survey years (2014, 2016,
2018, 2021, 2024), covering all 62 counties, 11 DSRIP regions, NYC, Rest of State,
and Statewide.
"""

import os
from absl import app
from absl import flags
from absl import logging
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'output_dir',
    'input_files',
    'Directory where downloaded input CSV files will be saved.',
)
flags.DEFINE_string(
    'endpoint',
    'https://health.data.ny.gov/resource/jsy7-eb4n.json',
    'Health Data NY BRFSS Socrata API endpoint.',
)


def create_session() -> requests.Session:
    """Creates a requests session configured with retries and connection pooling."""
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    session.headers.update({
        'User-Agent':
            'Mozilla/5.0 (DataCommons Ingestion; +https://datacommons.org)',
        'Accept':
            'application/json, text/csv, */*',
    })
    return session


def atomic_to_csv(df: pd.DataFrame, target_path: str) -> None:
    """Writes a DataFrame to a CSV file atomically via a temporary file."""
    temp_path = f'{target_path}.tmp'
    df.to_csv(temp_path, index=False)
    if not (os.path.exists(temp_path) and os.path.getsize(temp_path) > 0):
        raise RuntimeError(
            f'Atomic write failed: {temp_path} is empty or missing.'
        )
    os.replace(temp_path, target_path)


def download_health_indicators(endpoint: str,
                               output_dir: str) -> tuple[int, list[str]]:
    """Downloads all health indicators for all NY counties and regions."""
    os.makedirs(output_dir, exist_ok=True)

    records = []
    offset = 0
    limit = 50000

    with create_session() as session:
        while True:
            params = {
                '$limit': limit,
                '$offset': offset,
                '$order': ':id',
            }
            logging.info('GET %s with params %s', endpoint, params)
            resp = session.get(endpoint, params=params, timeout=60)
            if resp.status_code != 200:
                logging.error('Health Data NY API returned HTTP %d: %s',
                              resp.status_code, resp.text[:200])
                raise RuntimeError(
                    f'Health Data NY API returned HTTP {resp.status_code}: {resp.text[:200]}'
                )

            chunk = resp.json()
            if not chunk:
                break
            records.extend(chunk)
            logging.info('Fetched %d records (offset %d).', len(chunk), offset)
            offset += len(chunk)

    if not records:
        logging.error('Health Data NY API returned 0 records.')
        raise RuntimeError('Health Data NY API returned 0 records.')

    logging.info('Received %d total raw records from Health Data NY API.',
                 len(records))
    raw_df = pd.DataFrame(records)

    # Save complete raw unpivoted dataset (all 17,000+ API records)
    raw_file = os.path.join(output_dir, 'ny_brfss_health_indicators_raw.csv')
    atomic_to_csv(raw_df, raw_file)
    saved_files = [raw_file]
    logging.info('Wrote raw unpivoted dataset (%d records) -> %s', len(raw_df),
                 raw_file)

    return len(raw_df), saved_files


def main(_):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = (FLAGS.output_dir if os.path.isabs(FLAGS.output_dir) else
                  os.path.join(script_dir, FLAGS.output_dir))
    download_health_indicators(FLAGS.endpoint, output_dir)


if __name__ == '__main__':
    app.run(main)
