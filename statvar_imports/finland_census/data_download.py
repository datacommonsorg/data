#!/usr/bin/env python3
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
"""Downloader for Finland Census data from Statistics Finland PxWeb API using download_util."""

import csv
import io
import os
import sys

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.join(_CODEDIR, '../../util/'))

from absl import app
from absl import flags
from absl import logging
import download_util
from file_util import FileIO

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'output_path',
    None,
    'Local or GCS path to save the downloaded CSV.',
    required=True,
)

API_URL = 'https://pxdata.stat.fi/PXWeb/api/v1/en/StatFin/vaerak/11ra.px'


def get_variable_codes() -> tuple[str, str, str]:
    """Fetches table metadata and maps structural concepts to API codes."""
    logging.info('Fetching table metadata from %s...', API_URL)
    
    try:
        metadata = download_util.request_url(
            url=API_URL,
            output='json',
            retries=3,
            retry_secs=5,
        )
        if not metadata or not isinstance(metadata, dict):
            raise RuntimeError('Failed to fetch valid JSON metadata from PxWeb API.')
    except Exception as e:
        logging.error('Error fetching table metadata: %s', e)
        raise

    area_code = None
    info_code = None
    year_code = None

    # Cleaner matching using case-insensitive checks
    for var in metadata.get('variables', []):
        text = var.get('text', '').lower()
        code = var.get('code')

        if 'area' in text or 'alue' in text:
            area_code = code
        elif 'information' in text or 'tiedot' in text:
            info_code = code
        elif 'year' in text or 'vuosi' in text:
            year_code = code
    return area_code, info_code, year_code


def format_csv_content(raw_csv_content: str) -> str:
    """Safely prepends a title block to the CSV matching the pvmap layout."""
    clean_content = raw_csv_content.strip()
    header_line = clean_content.split('\n', 1)[0]
    num_columns = len(next(csv.reader([header_line])))

    title = "Key figures on population by Area, Information and Year"
    output = io.StringIO()
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow([title] + [''] * (num_columns - 1))
    writer.writerow([''] * num_columns)

    return output.getvalue() + clean_content + '\n'


def download_data(output_path: str) -> None:
    """Downloads, formats, and saves the Finland Census CSV data."""
    area_code, info_code, year_code = get_variable_codes()
    logging.info(
        'Mapped variable codes -> Area: %s, Info: %s, Year: %s',
        area_code, info_code, year_code,
    )

    query = {
        'query': [
            {
                'code': area_code,
                'selection': {'filter': 'item', 'values': ['SSS']}, # 'SSS' selects the 'WHOLE COUNTRY'
            },
            {
                'code': info_code,
                'selection': {'filter': 'all', 'values': ['*']}, # '*' selects all metrics
            },
            {
                'code': year_code,
                'selection': {'filter': 'all', 'values': ['*']}, # '*' selects all years
            },
        ],
        'response': {'format': 'csv'},
    }

    logging.info('Sending POST query to retrieve CSV data...')
    try:
        content_bytes = download_util.request_url(
            url=API_URL,
            params=query,
            method='POST',
            output='bytes',
            retries=3,
            retry_secs=5,
        )

        if not content_bytes:
            raise RuntimeError('Failed to download CSV data: empty response.')
    except Exception as e:
        logging.error('Error downloading CSV data: %s', e)
        raise

    content = content_bytes.decode('utf-8-sig')
    formatted_content = format_csv_content(content)

    with FileIO(output_path, 'w') as f:
        f.write(formatted_content)

    logging.info('Successfully downloaded data and saved to %s', output_path)


def main(_) -> None:
    download_data(_FLAGS.output_path)


if __name__ == '__main__':
    app.run(main)
