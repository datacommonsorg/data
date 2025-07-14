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

import os
from absl import app, logging, flags
import sys
from google.cloud import storage
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, '../../../util'))
INPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")

from download_util_script import _retry_method

flags.DEFINE_string(
    'config_file_path',
    'gs://datcom-import-test/statvar_imports/database_on_indian_economy/india_rbi_state_statistics/configs.py',
    'Config file path')

def reads_config_file():
    _FLAGS = flags.FLAGS
    config_file_path = _FLAGS.config_file_path
    try:
        storage_client = storage.Client()
        bucket_name = config_file_path.split('/')[2]
        bucket = storage_client.bucket(bucket_name)
        blob_name = '/'.join(config_file_path.split('/')[3:])
        blob = bucket.blob(blob_name)
        file_contents = blob.download_as_text()
        local_vars = {}
        exec(file_contents, {}, local_vars)
        return local_vars
    except Exception as e:
        logging.fatal(f"Cannot extract url and related configs: {e}")

def download_files(URL_CONFIG):
    try:
        for config in URL_CONFIG:
            config_url = config.get("url")
            category_name = config.get("category")
            file_name = config.get("filename")
            file_path = os.path.join(INPUT_DIR, category_name, file_name)
            os.makedirs(os.path.join(INPUT_DIR, category_name), exist_ok=True)
            file_response = _retry_method(config_url, headers=None, tries=3, delay=5, backoff=2)
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
        logging.info(f"No XLSX files found in the directory: {directory_path}")
        return

    logging.info(f"Found {len(xlsx_files)} XLSX files to process in '{directory_path}'.")

    for file_name in xlsx_files:
        file_path = os.path.join(directory_path, file_name)
        logging.info(f"Processing file: {file_path}")

        try:
            all_sheets_data = pd.read_excel(file_path, sheet_name=None, header=None)
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, df in all_sheets_data.items():
                    df_cleaned = df.map(lambda x: str(x).replace('*', '').strip())
                    df_cleaned.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        except Exception as e:
            logging.error(f"Error processing {file_name}: {e}")

    logging.info("All specified XLSX files have been processed.")


def main(_):
    configs = reads_config_file()
    RBI_URL = configs['URLS_CONFIG']
    download_files(RBI_URL)
    logging.info("Download process Completed successfully")
    directories = ['agriculture', 'environment', 'infrastructure', 'price_and_wages']
    for directory in directories:
        preprocess_files(os.path.join(INPUT_DIR, directory))
    logging.info("Pre-process Completed successfully")


if __name__ == "__main__":  
    app.run(main)
