# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#             https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# How to run the script to download the files:
# For production (using default GCS path):
# python3 download_script.py
#
# For local testing (overriding with a local path):
# python3 download_script.py --config_file_path=import_configs.json

import os
import sys
from absl import app
from absl import flags
from absl import logging
import datetime
import tempfile
import json
from google.cloud import storage

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))
from download_util_script import download_file

logging.set_verbosity(logging.INFO)

FLAGS = flags.FLAGS
flags.DEFINE_string(
    'config_file_path',
    'gs://unresolved_mcf/census_v2/sahie/latest/import_configs.json',
    'Path to the import config file. Can be a local path or a GCS path (gs://...).')


def clean_csv_file(file_path):
    """
    Cleans a single CSV file by removing the header description in-place.
    """
    try:
        # Create a temporary file to write the cleaned data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding='latin-1') as temp_file:
            with open(file_path, 'r', encoding='latin-1') as infile:
                found_header = False
                for line in infile:
                    # The actual CSV data starts with the header row 'year,version,...'
                    if not found_header and line.strip().startswith('year,version,statefips,countyfips,geocat'):
                        found_header = True
                    
                    if found_header:
                        temp_file.write(line)

            # Replace the original file with the cleaned temporary file
            os.replace(temp_file.name, file_path)
            logging.info(f"Successfully cleaned file: {file_path}")

    except Exception as e:
        logging.error(f"Error cleaning file {file_path}: {e}")
        # If temp_file was created, it will be automatically removed if an error occurs before os.replace
        # If os.replace fails, the temp file might be left behind, but NamedTemporaryFile tries to clean up.


def main(_):
    config_path = FLAGS.config_file_path
    configs = {}

    if config_path.startswith('gs://'):
        logging.info(f"Reading config from GCS path: {config_path}")
        try:
            storage_client = storage.Client()
            bucket_name, blob_name = config_path[5:].split('/', 1)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            configs = json.loads(blob.download_as_string())
        except Exception as e:
            logging.fatal(f"Failed to read config from GCS: {e}")
    else:
        logging.info(f"Reading config from local path: {config_path}")
        try:
            with open(config_path, 'r') as f:
                configs = json.load(f)
        except FileNotFoundError:
            logging.fatal(f"Config file not found at local path: {config_path}")

    BASE_URL = configs['CensusSAHIE']['source_url']
    OUTPUT_DIRECTORY = "input_files"
    START_YEAR = 2018
    CURRENT_YEAR = datetime.datetime.now().year
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    logging.info(f"Base output directory '{OUTPUT_DIRECTORY}' ensured to exist.")

    failed_downloads = []
    try:
        for year in range(START_YEAR, CURRENT_YEAR + 1):
            year_url = BASE_URL.format(year=year)
            success = download_file(
                url=year_url,
                output_folder=OUTPUT_DIRECTORY,
                unzip=True,
                tries=5,
                delay=10
            )

            if not success:
                logging.warning(f"Failed to download or process data for year {year}.")
                failed_downloads.append(year)
            else:
                logging.info(f"Successfully processed data for year {year}.")
                # After unzipping, find the CSV and clean it
                unzipped_csv_name = f"sahie_{year}.csv"
                unzipped_csv_path = os.path.join(OUTPUT_DIRECTORY, unzipped_csv_name)
                if os.path.exists(unzipped_csv_path):
                    clean_csv_file(unzipped_csv_path)
                else:
                    logging.warning(f"Could not find expected CSV file to clean: {unzipped_csv_path}")

    finally:
        for item in os.listdir(OUTPUT_DIRECTORY):
            if item.endswith(".zip"):
                file_to_remove = os.path.join(OUTPUT_DIRECTORY, item)
                os.remove(file_to_remove)
                logging.info(f"Removed zip file: {file_to_remove}")
        
        if failed_downloads:
            logging.fatal(f"Failed to download data for the following years: {failed_downloads}")

        logging.info("Final cleanup complete")

if __name__ == '__main__':
  app.run(main)