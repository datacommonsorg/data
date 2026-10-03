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
"""
This script downloads and processes the annual GDP data from the Bureau of Economic Analysis (BEA).

It performs the following steps:
1. Downloads a zip file containing GDP data from a specified URL.
2. Extracts the contents of the zip file into an 'input_files' directory.
3. Retains the downloaded zip file.
4. Filters the extracted files, retaining only those that contain 'ALL_AREAS' in their filenames.

This script relies on a shared 'download_util' module for handling file downloads.
"""

import os
import sys
import zipfile
import pandas as pd
from absl import app
from absl import logging

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../'))
from util import download_util

logging.set_verbosity(logging.INFO)

# URL for the BEA annual GDP data zip file.
_DOWNLOAD_URL = "https://apps.bea.gov/regional/zip/SAGDP.zip"

# Directory to store the downloaded and extracted files.
_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "input_files")


def clean_up_files(directory: str) -> None:
  """
    Removes files from a specified directory that do not contain 'ALL_AREAS' in their filenames.

    Args:
        directory: The path to the directory to clean up.
    """
  logging.info(f"Cleaning up files in directory: {directory}")
  for filename in os.listdir(directory):
    if "ALL_AREAS" not in filename and not filename.endswith(".zip"):
      file_path = os.path.join(directory, filename)
      try:
        if os.path.isfile(file_path):
          os.remove(file_path)
          logging.info(f"Removed file: {file_path}")
      except OSError as e:
        logging.error(f"Error removing file {file_path}: {e}")


def _process_csv_data(directory: str) -> None:
    """
    Processes all CSV files in the specified directory to remove spaces from specific columns.
    """
    logging.info(f"Starting to process CSV data in: {directory}")
    columns_to_process = ["GeoName", "Description", "Unit", "IndustryClassification"]

    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            file_path = os.path.join(directory, filename)
            logging.info(f"Processing file: {file_path}")
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
                for col in columns_to_process:
                    if col in df.columns:
                        # Ensure the column is of string type before applying string operations
                        df[col] = df[col].astype(str).str.strip() 
                # Save the modified dataframe back to the CSV
                df.to_csv(file_path, index=False)
                logging.info(f"Successfully processed {filename}")

            except FileNotFoundError:
                logging.error(f"Error: File not found at {file_path}")
                raise RuntimeError(f"File not found: {file_path}")
            except pd.errors.EmptyDataError:
                logging.warning(f"Warning: {filename} is empty and was skipped.")
            except (pd.errors.ParserError, KeyError) as e:
                logging.error(f"Error processing {filename}: {e}")
            except OSError as e:
                logging.error(f"An OS error occurred while processing {filename}: {e}")

def download_and_extract_data() -> None:
  """
    Downloads and extracts the BEA annual GDP data.

    This function handles the entire process of downloading the data, extracting it,
    and cleaning up the extracted files.
    """
  # Ensure the output directory exists.
  os.makedirs(_OUTPUT_DIR, exist_ok=True)
  logging.info(f"Ensured output directory exists: {_OUTPUT_DIR}")

  # Define the local path for the downloaded zip file.
  zip_file_path = os.path.join(_OUTPUT_DIR, "SAGDP.zip")

  # Download the file using the utility function, overwriting if it already exists.
  downloaded_file = download_util.download_file_from_url(
      _DOWNLOAD_URL, output_file=zip_file_path, overwrite=True)

  if downloaded_file and os.path.exists(downloaded_file):
    logging.info(f"Successfully downloaded file to: {downloaded_file}")
    try:
      # Extract the contents of the zip file.
      with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
        zip_ref.extractall(_OUTPUT_DIR)
      logging.info(f"Successfully extracted zip file to: {_OUTPUT_DIR}")

      # The downloaded zip file is retained in the input_files directory.
      # os.remove(downloaded_file)
      # logging.info(f"Removed temporary zip file: {downloaded_file}")

      # Remove any files that do not contain "ALL_AREAS".
      clean_up_files(_OUTPUT_DIR)

      # Convert all filenames in _OUTPUT_DIR to lowercase
      for filename in os.listdir(_OUTPUT_DIR):
          if not filename.endswith(".zip"):
              old_file_path = os.path.join(_OUTPUT_DIR, filename)
              new_file_path = os.path.join(_OUTPUT_DIR, filename.lower())
              if old_file_path != new_file_path:
                  try:
                      os.rename(old_file_path, new_file_path)
                      logging.info(f"Renamed: {old_file_path} -> {new_file_path}")
                  except OSError as e:
                      logging.error(f"Error renaming file {old_file_path}: {e}")

      _process_csv_data(_OUTPUT_DIR)
      
    except zipfile.BadZipFile:
      logging.error(
          f"Error: Downloaded file '{downloaded_file}' is not a valid zip file."
      )
    except OSError as e:
      logging.error(
          f"An unexpected error occurred during file operations: {e}")
  else:
    logging.error("Failed to download the file.")

def main() -> None:
  """
    Main function to orchestrate the download and extraction process.
    """
  download_and_extract_data()

if __name__ == "__main__":
  main()
