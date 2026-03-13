# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This script downloads data for India NSS Health Ailments from NSS Report No. 556."""

import json
import os
import sys
from typing import List, Tuple

from absl import app
from absl import flags
from absl import logging
import pandas as pd
from google.cloud import storage

_FLAGS = flags.FLAGS

flags.DEFINE_string(
    'config_file_path',
    'gs://unresolved_mcf/india_ndap/NDAP_NSS_Health/latest/download_config.json',
    'Input directory where config files are downloaded.')

# --- ROBUST PATH RESOLUTION START ---
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

def _add_util_to_path():
    """Adds the repo 'util' directory to sys.path dynamically."""
    path_3_up = os.path.abspath(os.path.join(_SCRIPT_PATH, '../../../util/'))
    path_2_up = os.path.abspath(os.path.join(_SCRIPT_PATH, '../../util/'))
    
    if os.path.exists(os.path.join(path_3_up, 'file_util.py')):
        sys.path.append(path_3_up)
    elif os.path.exists(os.path.join(path_2_up, 'file_util.py')):
        sys.path.append(path_2_up)
    else:
        curr = _SCRIPT_PATH
        for _ in range(5):
            potential = os.path.join(curr, 'util')
            if os.path.exists(os.path.join(potential, 'file_util.py')):
                sys.path.append(potential)
                return
            curr = os.path.dirname(curr)
        logging.error("Could not find 'util' directory containing file_util.py")

_add_util_to_path()

try:
    from download_util_script import _retry_method
    import file_util
except ImportError as e:
    logging.fatal(f"Import Error: Could not find utility scripts. {e}")
# --- ROBUST PATH RESOLUTION END ---

_OUTPUT_COLUMNS = [
    'srcStateName',
    'TRU',
    'GENDER',
    'Broad ailment category',
    'Age group',
    ('Ailments reported for each Broad ailment category per 100000 persons'
     ' during last 15 days by different age groups'),
    'Estimated number of ailments under broad ailment category',
    'Sample number of ailments under broad ailment category',
    'srcYear',
    'futureYear',
    'YearCode',
    'Year',
]

def load_config(path: str) -> dict:
    """Loads configuration from GCS or local disk."""
    if path.startswith('gs://'):
        client = storage.Client()
        bucket_name = path.split('/')[2]
        blob_name = '/'.join(path.split('/')[3:])
        blob = client.get_bucket(bucket_name).blob(blob_name)
        return json.loads(blob.download_as_string())
    return file_util.file_load_py_dict(path)

def download_data(config_file_path: str) -> Tuple[List[Tuple], str]:
    """Downloads data using configuration."""
    file_config = load_config(config_file_path)
    url = file_config.get('url')
    # We ignore the 'input_files' from config to save in the current directory
    output_dir = '' 
    
    if not url:
        return [], ''

    all_data = []
    page_num = 1
    while True:
        api_url = f'{url}&pageno={page_num}'
        response = _retry_method(api_url, None, 3, 5, 2)
        if not response:
            logging.fatal('Failed to retrieve data from page %d', page_num)

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
    """Saves data to CSV directly in the script directory."""
    if not data:
        logging.info('No data was retrieved from the API.')
        return

    df = pd.DataFrame(data, columns=_OUTPUT_COLUMNS)
    
    # Save directly in _SCRIPT_PATH (statvar_imports/india_ndap/india_nss_health_ailments)
    output_path = os.path.join(_SCRIPT_PATH, 'india_nss_health_ailments.csv')  
    df.to_csv(output_path, index=False)
    logging.info('Data saved to %s', output_path)
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
  output_path = os.path.join(output_dir, 'india_nss_health_ailments.csv')  
  df.to_csv(output_path, index=False)
  logging.info('Data saved to %s', output_path)


def main(_) -> None:
    raw_data, output_dir = download_data(_FLAGS.config_file_path)
    if raw_data:
        preprocess_and_save(raw_data, output_dir)

if __name__ == '__main__':
    app.run(main)