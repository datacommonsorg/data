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

import json, os, requests, sys
from pathlib import Path
from absl import app, logging, flags
from retry import retry

_FLAGS = flags.FLAGS
flags.DEFINE_string('input_file_path', 'input_files', 'Input files path')
flags.DEFINE_string(
    'config_file', 'gs://unresolved_mcf/cdc/environmental/import_configs.json',
    'Config file path')

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = None
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
                logging.fatal(
                    f"No data available for URL: {url}. Aborting download.")
                return
            filename = os.path.join(_INPUT_FILE_PATH, input_file_name)
            with file_util.FileIO(filename, 'wb') as f:
                f.write(response.content)
        else:
            logging.error(
                f"Failed to download file from URL: {url}. Status code: {response.status_code}"
            )

    try:
        for config in configs:
            if config["import_name"] == importname:
                files = config["files"]
                for file_info in files:
                    url_new = file_info["url"]
                    logging.info(f"URL from config file {url_new}")
                    input_file_name = file_info["input_file_name"]
                    logging.info(f"Input File Name {input_file_name}")

                    get_record_count = requests.get(
                        url_new.replace('.csv', record_count_query))
                    if get_record_count.status_code == 200:
                        record_count = json.loads(
                            get_record_count.text
                        )[0]['COLUMN_ALIAS_GUARD__count']
                        logging.info(
                            f"Numbers of records found for the URL {url_new} is {record_count}"
                        )
                        url_new = f"{url_new}?$limit={record_count}&$offset=0"
                        download_with_retry(url_new, input_file_name)
                        logging.info(
                            "Successfully downloaded the source data...!!!!")
                    else:
                        logging.error(
                            f"Failed to download files, Status code: {get_record_count.status_code}"
                        )

    except Exception as e:
        logging.fatal(f"Error downloading URL {url_new} - {e}")


def main(_):
    """Main function to download the csv files."""
    global _INPUT_FILE_PATH
    _INPUT_FILE_PATH = os.path.join(_FLAGS.input_file_path)
    _INPUT_FILE_PATH = os.path.join(_MODULE_DIR, _FLAGS.input_file_path)
    Path(_INPUT_FILE_PATH).mkdir(parents=True, exist_ok=True)
    importname = sys.argv[1]
    logging.info(f'Loading config: {_FLAGS.config_file}')
    with file_util.FileIO(_FLAGS.config_file, 'r') as f:
        config = json.load(f)
    download_files(importname, config)


if __name__ == "__main__":
    app.run(main)
