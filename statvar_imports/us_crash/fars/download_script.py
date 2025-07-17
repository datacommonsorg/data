# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 20 ('License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#           https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# How to run the script to download the files:
# python3 download_script.py

import os
import requests
import shutil
import sys
import zipfile

from absl import app
from absl import logging
import config
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/')) 
from download_util_script import _retry_method


def download_and_extract_data(url, input_folder, year):
    """Downloads zip, extracts ACCIDENT.CSV (handling nested dirs), with retry"""
    try:
        response = _retry_method(url, None, 3, 5, 2)
        filename = os.path.basename(url)
        filepath = os.path.join(input_folder, filename)

        if not os.path.exists(input_folder):
            os.makedirs(input_folder)
            logging.info(f"Created directory: {input_folder}")

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Downloaded: {filename} to {input_folder}")

        if filename.endswith(".zip"):
            try:
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    if zip_ref.namelist(): 
                        found_accident_csv = False
                        for item in zip_ref.infolist():
                            if item.filename.upper().endswith("ACCIDENT.CSV"):
                                parts = item.filename.split("/")
                                if len(parts) > 1: 
                                    output_filename = f"ACCIDENT_{year}.csv"
                                    output_filepath = os.path.join(input_folder, output_filename)
                                else:  
                                    output_filename = f"ACCIDENT_{year}.csv"
                                    output_filepath = os.path.join(input_folder, output_filename)

                                with zip_ref.open(item) as source, open(output_filepath, "wb") as target:
                                    shutil.copyfileobj(source, target)
                                logging.info(f"Extracted {output_filename} from {filename}")
                                found_accident_csv = True
                                
                        if not found_accident_csv:
                            logging.info(f"ACCIDENT.CSV not found in {filename}")
                        
                    else:
                        logging.info(f"Zip file {filename} is empty.")
                
                os.remove(filepath)
                
            except Exception as e:
                logging.exception(f"An error occurred during extraction from {filename}: {e}")
    except requests.exceptions.HTTPError as e:
       
        if e.response.status_code == 404:
            return "no_data_at_url" 
       
    
def main(argv):
    
    year = config.start_year 
    while True:
        url = config.base_url.format(year=year)
        logging.info(f"Attempting to download data for {year} from: {url}")

        expected_output_filepath = os.path.join(config.input_folder, f"ACCIDENT_{year}.csv")
        if os.path.exists(expected_output_filepath):
            logging.info(f"ACCIDENT_{year}.csv already exists. Skipping download for {year}.")
            
        status = download_and_extract_data(url, config.input_folder, year)

        if status == "no_data_at_url":
            logging.info(f"No data found at URL for year {year}. This indicates the end of available data")
            break 
    
        year += 1 

    logging.info("Download and extraction process complete.")

if __name__=="__main__":
    app.run(main)