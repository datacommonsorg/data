# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import re
import tempfile
import time
from absl import app, flags, logging
from google.cloud import storage
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_CONFIG_JSON = os.path.join(SCRIPT_DIR, 'configs.json')

flags.DEFINE_string('config_file_path', DEFAULT_CONFIG_JSON,
                    'Config file path (local json or gs:// path)')
flags.DEFINE_bool('force_download', False,
                  'If true, redownload files even if valid local copies exist.')

DEFAULT_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/124.0.0.0 Safari/537.36'),
    'Accept':
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language':
    'en-US,en;q=0.9',
    'Referer':
    'https://www.rbi.org.in/',
}


def reads_config_file():
    _FLAGS = flags.FLAGS
    config_file_path = _FLAGS.config_file_path
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"Failed to read local config file '{file_path}': {e}")
    return None



def download_files(URL_CONFIG):
    try:
        for config in URL_CONFIG:
            config_url = config.get("url")
            category_name = config.get("category")
            file_name = config.get("filename")
            file_path = os.path.join(INPUT_DIR, category_name, file_name)
            os.makedirs(os.path.join(INPUT_DIR, category_name), exist_ok=True)
            file_response = _retry_method(config_url,
                                          headers=None,
                                          tries=3,
                                          delay=5,
                                          backoff=2)
            if file_response:
                with open(file_path, 'wb') as f:
                    f.write(file_response.content)
                logging.info(f"Downloaded the file {file_name} successfully.")
    except Exception as e:
        logging.fatal(f"Download error: {str(e)}")


def preprocess_files(directory_path):
    if not os.path.isdir(directory_path):
        logging.info(f"Error: Directory not found at '{directory_path}'")
        return

    xlsx_files = [f for f in os.listdir(directory_path) if f.endswith('.xlsx')]

    if not xlsx_files:
        logging.error(
            f"No XLSX files found in the directory: {directory_path}")
        return [directory_path]

    logging.info(
        f"Found {len(xlsx_files)} XLSX files to process in '{directory_path}'."
    )

    logging.info(
        f"Found {len(xlsx_files)} XLSX files to process in '{directory_path}'.")

    for file_name in sorted(xlsx_files):
        file_path = os.path.join(directory_path, file_name)
        logging.info(f"Processing file: {file_path}")
        try:
            all_sheets_data = pd.read_excel(file_path,
                                            sheet_name=None,
                                            header=None)
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, df in all_sheets_data.items():
                    df = df.map(lambda x: str(x).replace('*', '').replace(
                        '@', '').strip())
                    mask = df.eq('State/Union Territory').any(axis=1)
                    state_positions = df[mask] == 'State/Union Territory'

                    def safe_to_numeric(val):
                        val_str = str(val)
                        if val_str.isdigit():
                            return int(val_str)
                        try:
                            float_val = float(val_str)
                            return float_val
                        except ValueError:
                            return val

                    df_num = df[mask].applymap(safe_to_numeric)
                    converted = df_num.mask(state_positions,
                                            'State/Union Territory')
                    df.loc[mask, :] = converted
                    df.to_excel(writer,
                                sheet_name=sheet_name,
                                index=False,
                                header=False)

        except Exception as e:
            logging.error(f"Error processing {file_name}: {e}")
            failed_files.append(file_name)

    if failed_files:
        logging.error(
            f"Failed to process {len(failed_files)} file(s) in '{directory_path}': {failed_files}"
        )
        return failed_files

    logging.info("All specified XLSX files have been processed.")
    return []


def main(argv):
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')
    configs = reads_config_file()
    RBI_URL = configs['URLS_CONFIG']
    failed_downloads = download_files(RBI_URL)
    if failed_downloads:
        logging.fatal(
            f"Download failed for {len(failed_downloads)} table(s): {failed_downloads}"
        )
    logging.info("Download process Completed successfully")
    directories = [
        'agriculture', 'environment', 'infrastructure', 'price_and_wages'
    ]
    for directory in directories:
        failed = preprocess_files(os.path.join(INPUT_DIR, directory))
        if failed:
            failed_preprocesses.extend(failed)
    if failed_preprocesses:
        logging.fatal(
            f"Preprocessing failed for {len(failed_preprocesses)} file(s): {failed_preprocesses}"
        )
    logging.info("Pre-process Completed successfully")


if __name__ == "__main__":
    app.run(main)
