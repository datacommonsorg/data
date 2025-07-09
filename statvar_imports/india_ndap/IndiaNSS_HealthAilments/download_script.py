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

# How to run the script to download the files:
# python3 download_script.py

import json
import os
import pandas as pd
import sys
from absl import app
from absl import flags
from absl import logging
from google.cloud import storage


flags.DEFINE_string(
    'config_file_path',
    'gs://unresolved_mcf/india_ndap/NDAP_NSS_Health/latest/download_config.json',
    'Input directory where config files downloaded.')

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))
from download_util_script import _retry_method


def download_data(config_file_path):
    """Download and return raw JSON data from paginated API using config file."""
    all_data = []

    storage_client = storage.Client()
    bucket_name = config_file_path.split('/')[2]
    blob_name = '/'.join(config_file_path.split('/')[3:])
    file_contents = storage_client.bucket(bucket_name).blob(blob_name).download_as_text()

    try:
        file_config = json.loads(file_contents)
        url = file_config.get('url')
        input_files = file_config.get('input_files')
    except json.JSONDecodeError:
        logging.fatal("Cannot extract url and input files path.")
        return [], ""

    page_num = 1
    while True:
        api_url = f"{url}&pageno={page_num}"
        response = _retry_method(api_url, None, 3, 5, 2)
        response_data = response.json()

        if response_data and 'Data' in response_data and len(response_data['Data']) > 0:
            for i in response_data['Data']:
                a = (
                    i['StateName'], i['TRU'], i['D7300_3'], i['D7300_4'], i['D7300_5'],
                    i['I7300_6']['TotalPopulationWeight'], i['I7300_7']['avg'], i['I7300_8']['avg'],
                    i['Year'].split(",")[-1].strip(),
                    str(int(i['Year'].split(",")[-1].strip()) + 1),
                    i['Year'].split(",")[-1].strip(),
                    i['Year']
                )
                all_data.append(a)
            page_num += 1
        else:
            logging.error(f"Failed to retrieve data from page {page_num}")
            break

    return all_data, input_files


def preprocess_and_save(data, output_dir):
    """Convert data to DataFrame and save as CSV."""
    if not data:
        logging.info("No data was retrieved from the API.")
        return

    df = pd.DataFrame(data, columns=[
        'srcStateName', 'TRU', 'GENDER', 'Broad ailment category', 'Age group',
        'Ailments reported for each Broad caliment category per 100000 persons during last 15 days by different age groups',
        'Estimated number of ailments under broad ailment category',
        'Sample number of ailments under broad ailment category',
        'srcYear', 'future year', 'YearCode', 'Year'
    ])

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'IndiaNSS_HealthAilments.csv')
    df.to_csv(output_path, index=False)
    logging.info("Data saved to IndiaNSS_HealthAilments_input.csv")


def main(_):
    _FLAGS = flags.FLAGS
    config_file_path = _FLAGS.config_file_path
    raw_data, output_dir = download_data(config_file_path)
    preprocess_and_save(raw_data, output_dir)


if __name__ == "__main__":
    app.run(main)

