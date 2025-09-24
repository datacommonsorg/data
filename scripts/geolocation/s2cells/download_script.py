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
import datetime
import requests
import time
from absl import app
from absl import logging
import re

logging.set_verbosity(logging.INFO)

BASE_ERDDAP_URL = "https://coastwatch.noaa.gov/erddap/griddap/noaacwBLENDEDsstDaily.csv?"

# Variables to retrieve from the dataset
VARIABLES = [
    "analysed_sst",
    "analysis_error",
    "mask",
    "sea_ice_fraction"
]

LAT_RANGE = "(-89.975):1:(89.975)"
LON_RANGE = "(-179.975):1:(179.975)"

# Time component for ERDDAP URL
TIME_PART = "T12:00:00Z"
# directory which will contain all daily CSV files
INPUT_FILES_DIRECTORY = "input_files_folders"

# if no other files are found, it should start from 2021-1-01 
INITIAL_START_DATE = datetime.date(2022, 1, 1)

MAX_URL_RETRIES = 5


def get_max_date_from_csv_files(directory_path):
    """
    Scans CSV files within a given directory, assuming filenames are in YYYYMMDD.csv format,
    and returns the latest date found.
    This function will be used to determine where to resume.

    Args:
        directory_path: The path to the directory containing the CSV files.

    Returns:
        The latest datetime.date found from CSV filenames, or None if no valid dates exist.
    """
    max_date = None
    if not os.path.exists(directory_path):
        logging.info(f"Directory '{directory_path}' does not exist.")
        return None
    
    # condition to match YYYYMMDD.csv format
    csv_date_pattern = re.compile(r'^(\d{8})\.csv$') # Changed regex to capture 8 digits

    for item in os.listdir(directory_path):
        match = csv_date_pattern.match(item)
        if match:
            date_str = match.group(1)
            try:
                file_date = datetime.datetime.strptime(date_str, "%Y%m%d").date() 
                if max_date is None or file_date > max_date:
                    max_date = file_date
            except ValueError:
                logging.warning(f"Skipping file '{item}' in '{directory_path}' as its date part is not a valid date.")
                continue
    
    if max_date:
        logging.info(f"Max date found from existing CSV files in '{directory_path}': {max_date}")
    else:
        logging.info(f"No valid dated CSV files found in '{directory_path}'.")
    return max_date


def download_data_for_day(date, target_output_dir):
    """
    Constructs the ERDDAP URL for a specific day and downloads the CSV data.
    Saves the data directly into the specified target_output_dir.

    Args:
        date: The date for which to download the data.
        target_output_dir: The directory where this day's CSV file should be saved.
                           This directory is expected to be already created by the caller.

    Returns:
        True if the download was successful, False otherwise.
    """
    
    date_str_url = date.strftime(f"%Y-%m-%d{TIME_PART}")
    # filename to store the data
    filename = date.strftime("%Y%m%d.csv") 
    filepath = os.path.join(target_output_dir, filename)
    query_parts = []
    for var in VARIABLES:
        # query parameter creation logic
        query_parts.append(f"{var}%5B({date_str_url}):1:({date_str_url})%5D%5B{LAT_RANGE}%5D%5B{LON_RANGE}%5D")

    full_url = BASE_ERDDAP_URL + ",".join(query_parts)

    logging.info(f"Attempting to download data for {date.strftime('%Y-%m-%d')} to: {target_output_dir}")

    for attempt in range(MAX_URL_RETRIES): 
        try:
            response = requests.get(full_url, stream=True, timeout=60)
            response.raise_for_status() #

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logging.info(f"Successfully downloaded {filename} to {target_output_dir}")
            return True 

        except requests.exceptions.HTTPError as e:
            
            if e.response.status_code == 404:
                logging.error(f"404 Not Found for {filename} ({date.strftime('%Y-%m-%d')}) on attempt {attempt + 1}/{MAX_URL_RETRIES}. Data for this specific day is missing. Skipping this file after this attempt.")
                
    return False # Safety return, though should be covered by loop returns


def main(_):

    os.makedirs(INPUT_FILES_DIRECTORY, exist_ok=True)
    
    effective_start_date = INITIAL_START_DATE
    latest_existing_csv_date = get_max_date_from_csv_files(INPUT_FILES_DIRECTORY)

    if latest_existing_csv_date:
        # If existing CSV are found, start from the day after the latest date
        effective_start_date = latest_existing_csv_date + datetime.timedelta(days=1)
        logging.info(f"Starting data download from: {effective_start_date} .")
    else:
        # No dated CSV files found, start from the defined INITIAL_START_DATE
        logging.info(f"No previous data CSV files found. Starting initial download from: {INITIAL_START_DATE}.")
    
    END_DATE = datetime.date.today() 
    current_date_to_download = effective_start_date

    logging.info(f"Proceeding to download data from {current_date_to_download} to {END_DATE}.")

    download_count = 0
    
    # The target directory for all downloads is now simply INPUT_FILES_DIRECTORY
    target_download_directory = INPUT_FILES_DIRECTORY
    logging.info(f"All downloads will be saved directly into: '{target_download_directory}'.")

    # Download each day's file into the main INPUT_FILES_DIRECTORY
    while current_date_to_download <= END_DATE:
        # checking if the file for this specific date already exists.
        
        expected_filepath = os.path.join(target_download_directory, current_date_to_download.strftime("%Y%m%d.csv")) # Changed format here too
        if os.path.exists(expected_filepath):
            logging.info(f"File for {current_date_to_download.strftime('%Y-%m-%d')} already exists at '{expected_filepath}'. Skipping download for this date.")
            # download_count += 1 
        else:
            success = download_data_for_day(current_date_to_download, target_download_directory)
            
            if success:
                download_count += 1
            else:
                logging.warning(f"Failed to download data for {current_date_to_download}. This file will be missing.")
                
        current_date_to_download += datetime.timedelta(days=1)
        time.sleep(0.5) # delay between requests

    logging.info(" Data Download Process Complete")
    
    if download_count > 0:
        logging.info(f"Successfully processed {download_count} file(s) into '{target_download_directory}'.")
    else:
        logging.warning(f"No new files were successfully downloaded into '{target_download_directory}'. This might indicate a problem or no data for the range {effective_start_date} to {END_DATE}.")

    logging.info(f"All processed data for this run is contained within the '{INPUT_FILES_DIRECTORY}' directory.")

if __name__ == '__main__':
  app.run(main)