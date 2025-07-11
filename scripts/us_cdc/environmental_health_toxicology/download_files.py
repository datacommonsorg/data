# Copyright 2024 Google LLC
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

import json
import os
import requests
import sys
from absl import app, logging, flags
from retry import retry

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'config_file',
    'gs://unresolved_mcf/cdc/environmental/StandardizedPrecipitationEvapotranspirationIndex/latest/import_configs.json',
    'Config file path')

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_MODULE_DIR, '../../../util/'))
import file_util

record_count_query = '?$query=select%20count(*)%20as%20COLUMN_ALIAS_GUARD__count'


def download_files(importname, configs):

    @retry(tries=3, delay=2, backoff=2)
    def download_with_retry(url, input_file_name):
        logging.info(f"Downloading file from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        if response.status_code == 200:
            if not response.content:
                logging.fatal(f"No data available for URL: {url}")
                return
            with file_util.FileIO(input_file_name, 'wb') as f:
                f.write(response.content)
        else:
            logging.error(
                f"Failed to download file. Status code: {response.status_code}")

    try:
        for config in configs:
            if config["import_name"] == importname:
                for file_info in config["files"]:
                    url = file_info["url"]
                    input_file_name = file_info["input_file_name"]
                    logging.info(f"Downloading to file: {input_file_name}")

                    count_response = requests.get(
                        url.replace('.csv', record_count_query))
                    if count_response.status_code == 200:
                        record_count = json.loads(
                            count_response.text)[0]['COLUMN_ALIAS_GUARD__count']
                        full_url = f"{url}?$limit={record_count}&$offset=0"
                        download_with_retry(full_url, input_file_name)
                        logging.info(f"Finished downloading: {input_file_name}")
                    else:
                        logging.error(
                            f"Failed to get record count. Status code: {count_response.status_code}"
                        )

    except Exception as e:
        logging.fatal(f"Error during download: {e}")


def main(_):
    if len(sys.argv) < 2:
        logging.fatal("Import name must be provided as a command line argument")
        return

    importname = sys.argv[1]
    logging.info(f"Reading config file: {_FLAGS.config_file}")
    with file_util.FileIO(_FLAGS.config_file, 'r') as f:
        config = json.load(f)
    download_files(importname, config)


if __name__ == "__main__":
    app.run(main)
