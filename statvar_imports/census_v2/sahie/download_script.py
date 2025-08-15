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
# python3 download_script.py

import shutil
import os
import sys
from absl import app
from absl import logging
import datetime
import tempfile
import json
from google.cloud import storage
import glob

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))
from download_util_script import download_file

logging.set_verbosity(logging.INFO)


def clean_csv_file(file_path):
    """
    Cleans a single CSV file by removing the header description in-place.
    It reads and writes the file using UTF-8 encoding.
    """
    # List of required header columns to identify the start of the CSV data.
    header_parts = ['year', 'version', 'statefips', 'countyfips', 'geocat']
    lines_to_write = []

    try:
        logging.info(
            f"Reading {os.path.basename(file_path)} with UTF-8 encoding."
        )
        with open(file_path, 'r', encoding='utf-8') as infile:
            found_header = False
            for line in infile:
                # The actual CSV data starts with the header row.
                if not found_header and all(
                    part in line for part in header_parts):
                    found_header = True

                if found_header:
                    lines_to_write.append(line)
        
        content_to_write = "".join(lines_to_write)

        # Write the cleaned content back to the original file path using UTF-8
        with open(file_path, 'w', encoding='utf-8') as outfile:
            outfile.write(content_to_write)
        logging.info(f"Successfully cleaned file: {os.path.basename(file_path)}")

    except UnicodeDecodeError as e:
        logging.fatal(f"File {file_path} is not valid UTF-8. Please check the source file encoding. Error: {e}")
        raise RuntimeError(f"Failed to decode file {file_path} as UTF-8.") from e
    except Exception as e:
        logging.fatal(f"Error processing file {file_path}: {e}")
        raise RuntimeError(f"Failed to process file {file_path}") from e


def main(_):
    gcs_config_path = 'gs://unresolved_mcf/census_v2/sahie/latest/import_configs.json'
    configs = {}

    logging.info(f"Reading config from GCS path: {gcs_config_path}")
    try:
        storage_client = storage.Client()
        bucket_name, blob_name = gcs_config_path[5:].split('/', 1)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        configs = json.loads(blob.download_as_string())
    except Exception as e:
        logging.fatal(f"Failed to read config from GCS: {e}")
        sys.exit(1)

    BASE_URL = configs['CensusSAHIE']['source_url']
    OUTPUT_DIRECTORY = os.path.join(_SCRIPT_PATH, "input_files")
    START_YEAR = 2018
    CURRENT_YEAR = datetime.datetime.now().year

    # Clean up previous runs and create the output directory
    if os.path.exists(OUTPUT_DIRECTORY):
        shutil.rmtree(OUTPUT_DIRECTORY)
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    logging.info(f"Base output directory '{OUTPUT_DIRECTORY}' ensured to exist.")

    failed_downloads = []
    try:
        for year in range(START_YEAR, CURRENT_YEAR + 1):
            # Create a temporary directory for each year's download to isolate files
            with tempfile.TemporaryDirectory() as temp_dir:
                year_url = BASE_URL.format(year=year)
                success = download_file(url=year_url,
                                        output_folder=temp_dir,
                                        unzip=True,
                                        tries=5,
                                        delay=10)

                if not success:
                    logging.warning(
                        f"Failed to download or process data for year {year}. Stopping further downloads."
                    )
                    failed_downloads.append(year)
                    break

                logging.info(
                    f"Successfully downloaded and unzipped data for year {year}."
                )

                # Dynamically find the unzipped CSV file.
                # This is more robust than assuming a filename.
                unzipped_csv_paths = glob.glob(os.path.join(temp_dir, '*.csv'))

                if len(unzipped_csv_paths) == 1:
                    unzipped_csv_path = unzipped_csv_paths[0]
                    logging.info(
                        f"Found CSV file to process: {os.path.basename(unzipped_csv_path)}"
                    )

                    # Clean the file in place
                    clean_csv_file(unzipped_csv_path)

                    # Move the cleaned file to the final output directory with a standard name
                    final_csv_name = f"sahie_{year}.csv"
                    final_csv_path = os.path.join(OUTPUT_DIRECTORY,
                                                  final_csv_name)
                    shutil.move(unzipped_csv_path, final_csv_path)
                    logging.info(f"Moved cleaned file to {final_csv_path}")

                elif len(unzipped_csv_paths) == 0:
                    logging.warning(
                        f"No CSV file found in the archive for year {year}. Skipping."
                    )
                else:
                    logging.warning(
                        f"Found multiple CSV files for year {year}: {unzipped_csv_paths}. Skipping this year."
                    )

    except Exception as e:
        logging.fatal(
            f"An unexpected error occurred during the download and processing loop: {e}"
        )
        sys.exit(1)
    finally:
        # With temp directories, explicit cleanup of zips is no longer needed.
        if failed_downloads:
            logging.info(
                f"Could not download data for the following years (likely not yet available): {failed_downloads}"
            )

        logging.info("Script finished.")


if __name__ == '__main__':
    app.run(main)