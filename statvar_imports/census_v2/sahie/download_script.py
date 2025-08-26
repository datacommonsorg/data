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

import os
import sys
import shutil
from absl import app
from absl import logging
import datetime
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
    temp_file_path = file_path + ".tmp"
    try:
        logging.info(
            f"Reading {os.path.basename(file_path)} with UTF-8 encoding."
        )
        with open(file_path, 'r', encoding='utf-8') as infile, open(temp_file_path, 'w', encoding='utf-8') as outfile:
            found_header = False
            for line in infile:
                # The actual CSV data starts with the header row.
                if not found_header and all(
                    part in line for part in header_parts):
                    found_header = True

                if found_header:
                    outfile.write(line)
        
        shutil.move(temp_file_path, file_path)
        logging.info(f"Successfully cleaned file: {os.path.basename(file_path)}")

    except UnicodeDecodeError as e:
        logging.fatal(f"File {file_path} is not valid UTF-8. Please check the source file encoding. Error: {e}")
        raise RuntimeError(f"Failed to decode file {file_path} as UTF-8.") from e
    except Exception as e:
        logging.fatal(f"Error processing file {file_path}: {e}")
        raise RuntimeError(f"Failed to process file {file_path}") from e


_BASE_URL = "https://www2.census.gov/programs-surveys/sahie/datasets/time-series/estimates-acs/sahie-{year}-csv.zip"
_OUTPUT_DIRECTORY = "input_files"
_START_YEAR = 2018
_CURRENT_YEAR = datetime.datetime.now().year


def main(_):
    os.makedirs(_OUTPUT_DIRECTORY, exist_ok=True)
    logging.info(f"Base output directory '{_OUTPUT_DIRECTORY}' ensured to exist.")

    try:
        for year in range(_START_YEAR, _CURRENT_YEAR + 1):
            year_url = _BASE_URL.format(year=year)
            success = download_file(url=year_url,
                                    output_folder=_OUTPUT_DIRECTORY,
                                    unzip=True,
                                    tries=5,
                                    delay=10)

            if not success:
                logging.warning(
                    f"Failed to download or process data for year {year}. Stopping further downloads."
                )

                break
            else:
                logging.info(f"Successfully processed data for year {year}.")

    finally:
        # Clean all CSV files in the output directory
        for csv_file in glob.glob(os.path.join(_OUTPUT_DIRECTORY, "*.csv")):
            clean_csv_file(csv_file)

        for item in os.listdir(_OUTPUT_DIRECTORY):
            if item.endswith(".zip"):
                file_to_remove = os.path.join(_OUTPUT_DIRECTORY, item)
                os.remove(file_to_remove)
                logging.info(f"Removed zip file: {file_to_remove}")

        logging.info("Final cleanup complete")

if __name__ == '__main__':
  app.run(main)
