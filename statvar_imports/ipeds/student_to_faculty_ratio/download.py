# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import re
import zipfile
import time
from absl import logging

# --- Configuration ---
START_YEAR = 2009
END_YEAR = 2024
BASE_URL = "https://nces.ed.gov/ipeds/datacenter/data/EF{}D.zip"
DOWNLOAD_DIR = "input_files"
# Pattern to match files ending in '_rv' followed by a file extension
# The pattern should match '_rv.txt', '_rv.csv', etc.
RV_PATTERN = re.compile(r'_rv\.[a-z0-9]+$', re.IGNORECASE)
# ---------------------

# --- Path Adjustment for Utility Import ---
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
# Correct path to the directory containing download_util_script.py:
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))

try:
    # IMPORT ONLY THE FUNCTION THAT EXISTS in the utility script
    from download_util_script import download_file
except ImportError as e:
    # Use logging.fatal for critical import errors and exit
    logging.fatal("Could not import 'download_file'. Please ensure the utility script is accessible. Original error: %s", e)


def process_and_filter_zip(zip_path: str, output_dir: str, filter_pattern: re.Pattern) -> bool:
    """
    Handles the custom unzipping, RV-pattern filtering, and cleanup.
    """
    zip_filename = os.path.basename(zip_path)
    logging.info("  Unzipping and filtering contents (keeping only files matching pattern: %s)...", filter_pattern.pattern)

    extraction_successful = False

    try:
        # 1. Unzip and filter
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            all_files = zip_ref.namelist()
            files_to_extract = []

            for file_name in all_files:
                base_name = os.path.basename(file_name)
                # Check if the file is at the root or within a single folder.
                if filter_pattern.search(base_name):
                    files_to_extract.append(file_name)

            if not files_to_extract:
                logging.info("  Warning: No files matching the pattern found in %s. Skipping extraction.", zip_filename)
                extraction_successful = True # Treat as successful if no relevant files, but the process was clean

            # Extract the filtered files
            for file_name in files_to_extract:
                zip_ref.extract(file_name, output_dir)
                logging.info("    Extracted: %s", file_name)

            if files_to_extract:
                logging.info("  Extraction successful.")
            extraction_successful = True

    except zipfile.BadZipFile:
        logging.info("  Warning: %s is a corrupted or empty zip file. Skipping.", zip_filename)
    except Exception as e:
        # Catch unexpected errors during unzipping/extraction
        logging.info("  An unexpected error occurred during unzipping/extraction of %s: %s", zip_filename, e)
    finally:
        # 2. Clean up the downloaded zip file manually, regardless of success
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
                logging.info("  Removed zip file: %s", zip_path)
            except OSError as e:
                # Use info for non-critical file removal errors
                logging.info("  Warning: Failed to remove zip file %s: %s", zip_path, e)

    return extraction_successful


def main():
    """
    Downloads IPEDS zip files using the utility, then handles custom unzipping/filtering locally.
    """

    # 1. Create the target directory if it doesn't exist
    if not os.path.exists(DOWNLOAD_DIR):
        try:
            os.makedirs(DOWNLOAD_DIR)
            logging.info("Created directory: %s", DOWNLOAD_DIR)
        except OSError as e:
            # Use logging.fatal for critical directory creation errors
            logging.fatal("FATAL ERROR: Could not create directory %s: %s", DOWNLOAD_DIR, e)

    # 2. Iterate through the required year range
    for year in range(START_YEAR, END_YEAR + 1):
        url = BASE_URL.format(year)
        zip_filename = f"EF{year}D.zip"
        download_path = os.path.join(DOWNLOAD_DIR, zip_filename)

        logging.info("\nProcessing year %d...", year)

        try:
            # 3. Call the utility function to DOWNLOAD ONLY (unzip=False)
            download_success = download_file(
                url=url,
                output_folder=DOWNLOAD_DIR,
                unzip=False, # <-- CRITICAL: Do not let the utility unzip the file
                tries=3,
                delay=5,
                backoff=2
            )

            if download_success:
                # 4. Handle custom processing (unzip, filter, and cleanup) locally
                process_and_filter_zip(download_path, DOWNLOAD_DIR, RV_PATTERN)

            else:
                logging.info("Warning: Download failed for year %d. Skipping filtering.", year)

        except Exception as e:
            # Catch unexpected errors during the main execution loop for a specific year
            logging.info("An unexpected error occurred for year %d during execution: %s", year, e)

        # Optional: Add a pause between years to respect NCES server requests
        time.sleep(5)


if __name__ == "__main__":
    logging.set_verbosity(logging.INFO) # This line might be needed depending on environment setup
    try:
        main()
        logging.info("\nScript finished. Filtered files extracted to the '%s' folder.", DOWNLOAD_DIR)
    except Exception as e:
        # Catch errors outside the main loop, although 'main' should handle most
        logging.fatal("\nFATAL ERROR in main execution: %s", e)