# Copyright 2021 Google LLC
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
"""
Author: Padma Gundapaneni @padma-g
Date: 8/30/2021
Description: Utility to download all CDC 500 PLACES data.
URL: https://chronicdata.cdc.gov/browse?category=500+Cities+%26+Places

Files are stored in raw_data.

Run this script from this directory:
python3 download_bulk.py
"""

import os
import requests
import json
import sys

from absl import logging
from retry import retry
from absl import flags
from absl import app

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_MODULE_DIR, '../../../util/'))
import file_util

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'config_path', 'gs://unresolved_mcf/cdc/cdc500places/download_config.json',
    'Path to config file')


def read_config_file_from_gcs(file_path):
    with file_util.FileIO(file_path, 'r') as f:
        CONFIG_FILE = json.load(f)
    return CONFIG_FILE


@retry(tries=3, delay=5, backoff=5)
def retry_method(url):
    return requests.get(url)


def download_file(release_year, url: str, save_path: str):
    """
    Args:
        url: url to the file to be downloaded
        save_path: path for the downloaded file to be stored
    Returns:
        a downloaded csv file in the specified file path
    """
    logging.info(
        f'Downloading {url} for the year {release_year} to {save_path}')
    response = retry_method(url)
    if response.status_code != 200:
        logging.fatal(
            f'Failed to retrieve {url} for the year {release_year} to {save_path}'
        )
    with open(save_path, 'wb') as file:
        file.write(response.content)


def main(_):
    """Main function to download the files."""
    data_dir = os.path.join(os.getcwd(), 'raw_data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    logging.set_verbosity(2)
    _CONFIG_FILE = read_config_file_from_gcs(_FLAGS.config_path)
    for item in _CONFIG_FILE:
        release_year = item["release_year"]
        for url_dict in item["parameter"]:
            save_path = os.path.join(data_dir, url_dict['FILE_NAME'])
            download_file(release_year, url_dict['URL'], save_path)


if __name__ == '__main__':
    app.run(main)
