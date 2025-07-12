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

import json
import os
import requests
import sys
from absl import app, logging, flags
from urllib.parse import urlparse 

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'config_file',
    'gs://unresolved_mcf/cdc/environmental/StandardizedPrecipitationEvapotranspirationIndex/latest/import_configs.json',
    'Config file path'
)

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
# Append parent directory to sys.path to find utility modules like file_util and download_util_script.
sys.path.append(os.path.join(_MODULE_DIR, '../../../util/'))

# Import the necessary utility modules
import file_util
import download_util_script as download_util 

# Query string for retrieving record count from Socrata-like APIs
record_count_query = '?$query=select%20count(*)%20as%20COLUMN_ALIAS_GUARD__count'


def download_files(importname, configs):
    """
    Downloads files based on the provided configuration, using the download utility.

    Args:
        importname: The specific import name to process from the configurations.
        configs: A list of dictionaries containing file download configurations.
    """
    try:
        for config in configs:
            # Find the relevant configuration by import_name
            if config["import_name"] == importname:
                for file_info in config["files"]:
                    url = file_info["url"]
                    # `target_full_path` is the desired local path including filename
                    target_full_path = file_info["input_file_name"]
                    target_dir = os.path.dirname(target_full_path)
                    
                    # Fix: If target_dir is empty, it means the file should be saved in the current directory.
                    # Set it to '.' to explicitly refer to the current directory, avoiding empty path issues.
                    if not target_dir:
                        target_dir = '.'
                        
                    target_filename = os.path.basename(target_full_path)

                    logging.info(f"Preparing to download file for config '{importname}' to: {target_full_path}")

                    # Ensure the target directory exists before attempting to download
                    os.makedirs(target_dir, exist_ok=True)

                    # Step 1: Get the record count to construct the full URL (specific to this data source)
                    count_url = url.replace('.csv', record_count_query)
                    full_url = url # Default to original URL if count retrieval fails

                    try:
                        count_response = requests.get(count_url)
                        count_response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
                        record_count = json.loads(count_response.text)[0]['COLUMN_ALIAS_GUARD__count']
                        full_url = f"{url}?$limit={record_count}&$offset=0"
                        logging.info(f"Generated full download URL with record count ({record_count}): {full_url}")
                    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                        logging.error(f"Failed to get record count from '{count_url}'. Proceeding with original URL. Error: {e}")
                    except Exception as e:
                        logging.error(f"An unexpected error occurred during record count retrieval for '{count_url}'. Error: {e}")
                        # If any other error, fallback to original URL.

                    success = download_util.download_file(
                        url=full_url,
                        output_folder=target_dir,
                        unzip=False # Assuming these are CSVs, not zip files based on the context
                    )

                    if success:
                        parsed_download_url = urlparse(full_url)
                        inferred_filename = os.path.basename(parsed_download_url.path)

                        # Account for download_util's specific logic for appending .xlsx
                        # if no extension is present and it's not a zip file.
                        if '.' not in inferred_filename and not False: # `unzip` is False here
                            inferred_filename += '.xlsx'

                        # Construct the actual path where download_util saved the file
                        actual_downloaded_file_path = os.path.join(target_dir, inferred_filename)

                        # If the inferred filename differs from the desired target_filename, rename the file.
                        if inferred_filename != target_filename:
                            logging.info(f"Renaming downloaded file from '{actual_downloaded_file_path}' to '{target_full_path}' to match configuration.")
                            if os.path.exists(actual_downloaded_file_path):
                                os.rename(actual_downloaded_file_path, target_full_path)
                                logging.info(f"Successfully downloaded and renamed to: {target_full_path}")
                            else:
                                logging.error(f"Error: Expected downloaded file at '{actual_downloaded_file_path}' not found for renaming. Original target was '{target_full_path}'.")
                        else:
                            logging.info(f"Finished downloading to: {target_full_path}")
                    else:
                        logging.error(f"Download utility reported a failure for URL: {full_url}. Target: {target_full_path}")

    except Exception as e:
        logging.fatal(f"An unhandled error occurred during the overall download process: {e}")


def main(_):
    """
    Main entry point for the download script.
    Parses command-line arguments and initiates the download process.
    """
    if len(sys.argv) < 2:
        logging.fatal("Import name must be provided as a command line argument")
        sys.exit(1) # Exit with an error code

    importname = sys.argv[1]
    logging.info(f"Reading configuration file from: {_FLAGS.config_file}")

    try:
        with file_util.FileIO(_FLAGS.config_file, 'r') as f:
            config = json.load(f)
        download_files(importname, config)
    except Exception as e:
        logging.fatal(f"Failed to load or parse config file '{_FLAGS.config_file}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    app.run(main)


