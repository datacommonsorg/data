# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os
from absl import logging

# --- GCS and Local Configuration ---
GCS_BUCKET_NAME = "unresolved_mcf"
GCS_INPUT_PREFIX = "cdc/UnderlyingCause/Single_Race/latest/input_files"

# Get the directory of the current script
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the local working directory for downloaded files
# Changed from 'gcs_output' to 'input_files'
LOCAL_WORKING_DIR = os.path.join(_MODULE_DIR, 'input_files')

# --- Path Configuration for Module Imports ---
# Determine the project root from the script's location
PROJECT_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..', '..', '..'))
sys.path.insert(0, PROJECT_ROOT)
# Add the 'data/util' directory to sys.path to find file_util.py
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'data', 'util'))

# Now, directly import file_util.

import file_util

# --- Main Script Logic ---
def main():
    """
    Downloads all CSV files from a specified GCS bucket path to a local directory.
    """
    # Configure absl logging
    logging.use_absl_handler()
    logging.set_verbosity(logging.INFO)

    # List of the 88 files to download
    files_to_download = [f"UnderlyingCauseofDeath2018_2023SingleRace({i}).csv" for i in range(88)]

    # Create the local working directory if it doesn't exist
    os.makedirs(LOCAL_WORKING_DIR, exist_ok=True)
    logging.info(f"Local destination directory '{LOCAL_WORKING_DIR}' created or already exists.")
    
    logging.info("--- Starting GCS File Transfers using file_util module ---")
    
    for file_name in files_to_download:
        gcs_source_path = f"gs://{GCS_BUCKET_NAME}/{GCS_INPUT_PREFIX}/{file_name}"
        local_destination_path = os.path.join(LOCAL_WORKING_DIR, file_name)
        
        try:
            file_util.file_copy(gcs_source_path, local_destination_path)
            logging.info(f"Copied '{gcs_source_path}' to '{local_destination_path}'")
        except Exception as e:
            logging.fatal(
                f"Error copying '{gcs_source_path}' to '{local_destination_path}': {e}", 
                exc_info=True
            )
            # Exit on critical error to prevent partial downloads
            sys.exit(1)
            
    logging.info("--- GCS File Transfers Complete ---")

if __name__ == "__main__":
    main()