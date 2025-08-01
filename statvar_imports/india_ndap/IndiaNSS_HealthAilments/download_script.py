# Copyright 2025 Google LLC
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
"""This script downloads data for India NSS Health Ailments.

This script downloads data from the NDAP API, processes it, and saves it as a
CSV file.

How to run the script:
python3 download_script.py
"""

import json
import os
import sys
from typing import List, Tuple

import pandas as pd
from absl import app
from absl import flags
from absl import logging
from google.cloud import storage

# pylint: disable=g-bad-import-order


_FLAGS = flags.FLAGS

flags.DEFINE_string(
    'config_file_path',
    'gs://unresolved_mcf/india_ndap/NDAP_NSS_Health/latest/download_config.json',
    'Input directory where config files are downloaded.')

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))
import file_util
from download_util_script import _retry_method
_OUTPUT_COLUMNS = [
    'srcStateName',
    'TRU',
    'GENDER',
    'Broad ailment category',
    'Age group',
    ('Ailments reported for each Broad caliment category per 100000 persons'
     ' during last 15 days by different age groups'),
    'Estimated number of ailments under broad ailment category',
    'Sample number of ailments under broad ailment category',
    'srcYear',
    'future year',
    'YearCode',
    'Year',
]


def download_data(config_file_path: str) -> Tuple[List[Tuple], str]:
  """Downloads and returns raw JSON data from a paginated API.

  Args:
    config_file_path: The GCS path to the config file.

  Returns:
    A tuple containing the downloaded data as a list of tuples and the output
    directory.
  """
  file_config = file_util.file_load_py_dict(config_file_path)
  url = file_config.get('url')
  output_dir = file_config.get('input_files')
  if not url:
    return [], ''

  all_data = []
  page_num = 1
  while True:
    api_url = f'{url}&pageno={page_num}'
    response = _retry_method(api_url, None, 3, 5, 2)
    if not response:
      logging.fatal('Failed to retrieve data from page %d', page_num)
      break

    try:
      response_data = response.json()
    except json.JSONDecodeError:
      logging.error('Failed to parse JSON from page %d', page_num)
      break

    if response_data and 'Data' in response_data and response_data['Data']:
      for item in response_data['Data']:
        year = item['Year'].split(',')[-1].strip()
        row = (
            item['StateName'],
            item['TRU'],
            item['D7300_3'],
            item['D7300_4'],
            item['D7300_5'],
            item['I7300_6']['TotalPopulationWeight'],
            item['I7300_7']['avg'],
            item['I7300_8']['avg'],
            year,
            str(int(year) + 1),
            year,
            item['Year'],
        )
        all_data.append(row)
      page_num += 1
    else:
      logging.info('No more data found on page %d.', page_num)
      break

  return all_data, output_dir


def preprocess_and_save(data: List[Tuple], output_dir: str) -> None:
  """Converts data to a DataFrame and saves it as a CSV file.

  Args:
    data: The data to be processed, as a list of tuples.
    output_dir: The directory where the output CSV will be saved.
  """
  if not data:
    logging.info('No data was retrieved from the API.')
    return

  df = pd.DataFrame(data, columns=_OUTPUT_COLUMNS)

  os.makedirs(output_dir, exist_ok=True)
  output_path = os.path.join(output_dir, 'IndiaNSS_HealthAilments.csv')
  df.to_csv(output_path, index=False)
  logging.info('Data saved to %s', output_path)


def main(_) -> None:
  """Main function to download, process, and save the data."""
  raw_data, output_dir = download_data(_FLAGS.config_file_path)
  if raw_data and output_dir:
    preprocess_and_save(raw_data, output_dir)


if __name__ == '__main__':
  app.run(main)