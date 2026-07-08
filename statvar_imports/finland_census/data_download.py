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

import os
import sys

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, _CODEDIR)
sys.path.insert(1, os.path.join(_CODEDIR, '../../util/'))

from absl import app
from absl import flags
from absl import logging
import download_util

try:
  from file_util import FileIO
except ImportError:
  FileIO = None

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'output_path',
    None,
    'Local or GCS path to save the downloaded CSV.',
    required=True,
)

API_URL = 'https://pxdata.stat.fi/PXWeb/api/v1/en/StatFin/vaerak/11ra.px'


def get_variable_codes() -> tuple[str, str, str]:
  """Fetches table metadata and maps standard concepts to API codes using download_util.

  Returns:
    A tuple of strings (area_code, info_code, year_code).

  Raises:
    RuntimeError: If API request fails or variables cannot be mapped.
  """
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

    area_code = None
    info_code = None
    year_code = None

    for var in metadata.get('variables', []):
      text = var.get('text', '').upper()
      code = var.get('code')

      if 'AREA' in text:
        area_code = code
      elif 'INFORMATION' in text:
        info_code = code
      elif 'YEAR' in text:
        year_code = code

    if not area_code or not info_code or not year_code:
      raise RuntimeError(
          f'Could not map all variables. Detected area: {area_code}, '
          f'info: {info_code}, year: {year_code}'
      )
    return area_code, info_code, year_code
  except Exception as e:
    raise RuntimeError(f'Error fetching variable codes: {e}') from e


def format_csv_content(raw_csv_content: str) -> str:
  """Formats raw PxWeb CSV to match title and header layout expected by processor.

  Args:
    raw_csv_content: The raw CSV string returned by the PxWeb API.

  Returns:
    The formatted CSV string with title block and preserved column headers.
  """
  if not raw_csv_content or not raw_csv_content.strip():
    return raw_csv_content
  lines = raw_csv_content.strip().replace('\r\n', '\n').split('\n')

  header_line = lines[0]
  num_columns = len(header_line.split(','))

  title = '"Key figures on population by Area, Information and Year"'
  title_line = title + ',' * (num_columns - 1)
  blank_line = ',' * (num_columns - 1)

  output_lines = [title_line, blank_line, header_line] + lines[1:]
  return '\n'.join(output_lines)


def download_data(output_path: str) -> None:
  """Downloads, formats, and saves the Finland Census CSV data using download_util.

  Args:
    output_path: Local or GCS path where the formatted CSV will be saved.

  Raises:
    RuntimeError: If data download or file saving fails.
  """
  area_code, info_code, year_code = get_variable_codes()
  logging.info(
      'Mapped variable codes -> Area: %s, Info: %s, Year: %s',
      area_code,
      info_code,
      year_code,
  )

  query = {
      'query': [
          {
              'code': area_code,
              'selection': {'filter': 'item', 'values': ['SSS']},
          },
          {
              'code': info_code,
              'selection': {'filter': 'all', 'values': ['*']},
          },
          {
              'code': year_code,
              'selection': {'filter': 'all', 'values': ['*']},
          },
      ],
      'response': {'format': 'csv'},
  }

  logging.info('Sending POST query via download_util to retrieve CSV data...')
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

    content = content_bytes.decode('utf-8-sig')
    formatted_content = format_csv_content(content)

    if FileIO:
      with FileIO(output_path, 'w') as f:
        f.write(formatted_content)
    else:
      os.makedirs(
          os.path.dirname(os.path.abspath(output_path)), exist_ok=True
      )
      with open(output_path, 'w', encoding='utf-8') as f:
        f.write(formatted_content)

    logging.info('Successfully downloaded data and saved to %s', output_path)
  except Exception as e:
    raise RuntimeError(f'Error downloading data: {e}') from e


def main(_) -> None:
  download_data(_FLAGS.output_path)


if __name__ == '__main__':
  app.run(main)
