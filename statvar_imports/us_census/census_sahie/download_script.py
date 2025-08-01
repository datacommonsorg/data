# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (your 'License');
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
from absl import app
from absl import logging
import datetime

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))
from download_util_script import download_file
logging.set_verbosity(logging.INFO)


def main(_):
    BASE_URL = "https://www2.census.gov/programs-surveys/sahie/datasets/time-series/estimates-acs/sahie-{year}-csv.zip"
    OUTPUT_DIRECTORY = "downloaded_census_data"
    START_YEAR = 2008
    CURRENT_YEAR = datetime.datetime.now().year 
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    logging.info(f"Base output directory '{OUTPUT_DIRECTORY}' ensured to exist.")

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
                logging.warning(f"Failed to download or process data for year {year}. Stopping further downloads.")
                
                break
            else:
                logging.info(f"Successfully processed data for year {year}.")

    finally:
      
        for item in os.listdir(OUTPUT_DIRECTORY):
            if item.endswith(".zip"):
                file_to_remove = os.path.join(OUTPUT_DIRECTORY, item)
                os.remove(file_to_remove)
                logging.info(f"Removed zip file: {file_to_remove}")
               
        logging.info("Final cleanup complete")

if __name__ == '__main__':
  app.run(main)