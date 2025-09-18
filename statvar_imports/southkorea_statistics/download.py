# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from google.cloud import storage
import os
from absl import logging
import sys

# To increase verbosity to DEBUG level
logging.set_verbosity(logging.DEBUG)

def download_gcs_files(json_file_path, destination_directory):
    """
    Downloads files from Google Cloud Storage based on paths in a JSON file.

    Args:
        json_file_path (str): The path to the JSON file containing the file paths.
        destination_directory (str): The local directory to save the downloaded files.
    """
    # Initialize a client
    client = storage.Client()

    # The destination directory is relative to the current working directory.
    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)
        logging.info(f"Created directory: {destination_directory}")

    try:
        # Read the JSON file from the current working directory.
        with open(json_file_path, 'r') as f:
            file_data = json.load(f)

        if not isinstance(file_data, list):
            logging.fatal("Error: The JSON file should contain a list of file paths.")
            return

        for file_path in file_data:
            parts = file_path.split('/', 1)
            if len(parts) != 2:
                logging.info(f"Skipping invalid path: {file_path}")
                continue

            bucket_name, source_blob_name = parts
            destination_file_path = os.path.join(destination_directory, os.path.basename(source_blob_name))
            
            logging.info(f"Downloading {source_blob_name} from bucket {bucket_name}...")

            bucket = client.bucket(bucket_name)
            blob = bucket.blob(source_blob_name)

            try:
                blob.download_to_filename(destination_file_path)
                logging.info(f"Successfully downloaded to {destination_file_path}")
            except Exception as e:
                logging.fatal(f"Failed to download {source_blob_name}: {e}")

    except FileNotFoundError:
        # This will now correctly report if the file is missing in the current directory.
        logging.fatal(f"Error: The JSON file was not found at {json_file_path}")
    except json.JSONDecodeError:
        logging.fatal(f"Error: Could not decode JSON from the file at {json_file_path}")
    except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")

# --- How to use the function ---
if __name__ == '__main__':
    # Define the JSON file path as a relative path.
    json_file = 'gcs_files.json'
    local_download_dir = 'source_files'
    
    # Call the download function
    download_gcs_files(json_file, local_download_dir)