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

import os
import sys
import re
import zipfile
import time
from datetime import date 
from absl import logging

# --- Configuration ---
START_YEAR = 2009
# Set END_YEAR dynamically to the current calendar year
END_YEAR = date.today().year

BASE_URL_LEGACY = "https://nces.ed.gov/ipeds/datacenter/data/EF{year}D.zip"
BASE_URL_COMPLETE = "https://nces.ed.gov/ipeds/complete-data-files/EF{year}D.zip"
BASE_URL_RV = "https://nces.ed.gov/ipeds/data-generator?year={year}&tableName=EF{year}D&HasRV=1&type=csv"
BASE_URL_PROV = "https://nces.ed.gov/ipeds/data-generator?year={year}&tableName=EF{year}D&HasRV=0&type=csv"

BASE_URL_TEMPLATES = [
    BASE_URL_LEGACY,
    BASE_URL_COMPLETE,
    BASE_URL_RV,
    BASE_URL_PROV,
]

DOWNLOAD_DIR = "input_files"
# Pattern to match files ending in '_rv' followed by a file extension
RV_PATTERN = re.compile(r'_rv\.[a-z0-9]+$', re.IGNORECASE)
# Pattern to match provisional files (e.g. ef2023d.csv, ef2024d.csv)
PROVISIONAL_PATTERN = re.compile(r'^ef\d{4}d\.[a-z0-9]+$', re.IGNORECASE)
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
    raise RuntimeError(f"FATAL: Missing utility script dependency: {e}")


def process_and_filter_zip(zip_path: str, output_dir: str, require_rv: bool) -> bool:
    """
    Unzips and filters contents of zip_path.
    If require_rv is True, extracts only files matching RV_PATTERN.
    If require_rv is False, extracts files matching PROVISIONAL_PATTERN.
    Returns True if matching file(s) were found and extracted, False otherwise.
    """
    zip_filename = os.path.basename(zip_path)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            all_files = zip_ref.namelist()
            target_pattern = RV_PATTERN if require_rv else PROVISIONAL_PATTERN

            files_to_extract = [
                f for f in all_files if target_pattern.search(os.path.basename(f))
            ]

            if not files_to_extract:
                return False

            for file_name in files_to_extract:
                zip_ref.extract(file_name, output_dir)
                logging.info("    Extracted (%s): %s", "REVISED" if require_rv else "PROVISIONAL", file_name)

            return True

    except zipfile.BadZipFile:
        logging.fatal("  FATAL ERROR: %s is a corrupted or empty zip file. Cannot proceed.", zip_filename)
        raise RuntimeError(f"Corrupted or empty zip file encountered: {zip_filename}")
    except Exception as e:
        logging.fatal("  FATAL ERROR: An unexpected error occurred during unzipping/extraction of %s: %s", zip_filename, e)
        raise RuntimeError(f"Extraction failed for {zip_filename}: {e}")
    finally:
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except OSError:
                pass


def download_for_year(year: int) -> bool:
    """
    Downloads data for a given year following strict precedence:
    1. Checks candidate URLs to see if a REVISED dataset (_rv) is available.
    2. ONLY IF no revised dataset is available across any candidate URL,
       checks candidate URLs to download a PROVISIONAL dataset.
    """
    logging.info("\nProcessing year %d...", year)

    # --- Phase 1: Try to download REVISED dataset across candidate URLs ---
    for url_template in BASE_URL_TEMPLATES:
        if "{year}" in url_template:
            url = url_template.format(year=year)
        else:
            url = url_template.format(year)

        zip_filename = f"EF{year}D.zip"
        download_path = os.path.join(DOWNLOAD_DIR, zip_filename)

        try:
            download_success = download_file(
                url=url,
                output_folder=DOWNLOAD_DIR,
                unzip=False, # <-- CRITICAL: Do not let utility unzip file
                tries=1,
                delay=1,
                backoff=1
            )

            if download_success and os.path.exists(download_path) and zipfile.is_zipfile(download_path):
                if process_and_filter_zip(download_path, DOWNLOAD_DIR, require_rv=True):
                    logging.info("  Successfully fetched REVISED dataset for year %d.", year)
                    return True
        except Exception as e:
            logging.info("  Candidate URL %s (REVISED check) failed: %s", url, e)

    logging.info("  No REVISED dataset available for year %d. Checking for PROVISIONAL dataset...", year)

    # --- Phase 2: ONLY if REVISED is not available, try to download PROVISIONAL dataset ---
    for url_template in BASE_URL_TEMPLATES:
        if "{year}" in url_template:
            url = url_template.format(year=year)
        else:
            url = url_template.format(year)

        zip_filename = f"EF{year}D.zip"
        download_path = os.path.join(DOWNLOAD_DIR, zip_filename)

        try:
            download_success = download_file(
                url=url,
                output_folder=DOWNLOAD_DIR,
                unzip=False,
                tries=1,
                delay=1,
                backoff=1
            )

            if download_success and os.path.exists(download_path) and zipfile.is_zipfile(download_path):
                if process_and_filter_zip(download_path, DOWNLOAD_DIR, require_rv=False):
                    logging.info("  Successfully fetched PROVISIONAL dataset for year %d.", year)
                    return True
        except Exception as e:
            logging.info("  Candidate URL %s (PROVISIONAL check) failed: %s", url, e)

    logging.info("Warning: Neither REVISED nor PROVISIONAL dataset found for year %d across candidate URLs.", year)
    return False


def main():
    """
    Iterates through year range downloading datasets (preferring revised, falling back to provisional).
    """

    # 1. Create target directory if it doesn't exist
    if not os.path.exists(DOWNLOAD_DIR):
        try:
            os.makedirs(DOWNLOAD_DIR)
            logging.info("Created directory: %s", DOWNLOAD_DIR)
        except OSError as e:
            logging.fatal("FATAL ERROR: Could not create directory %s: %s", DOWNLOAD_DIR, e)
            raise RuntimeError(f"FATAL: Directory creation failed for {DOWNLOAD_DIR}: {e}")

    # 2. Iterate through required year range
    for year in range(START_YEAR, END_YEAR + 1):
        download_for_year(year)
        time.sleep(2)


if __name__ == "__main__":
    logging.set_verbosity(logging.INFO)
    try:
        main()
        logging.info("\nScript finished. Filtered files extracted to the '%s' folder.", DOWNLOAD_DIR)
    except Exception as e:
        # Catch errors that prevent main from starting or critical errors like directory creation
        logging.fatal("\nFATAL ERROR in main execution: %s", e)