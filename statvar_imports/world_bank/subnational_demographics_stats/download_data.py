# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import pandas as pd
from absl import logging, app
import zipfile

# Set up module path to access the utility script
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.dirname(os.path.dirname(os.path.dirname(_MODULE_DIR)))
sys.path.append(data_dir)

from util.download_util_script import download_file

# The API URL to download the subnational population data as a CSV zip archive.
_API_URL = "http://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?downloadformat=csv"

def unzip_file(inputdir):
    """
    Unzips the downloaded file.
    """
    try:
        zip_path = os.path.join(inputdir, "P_Data_Extract_From_Subnational_Population.zip")
        os.rename(os.path.join(inputdir, "SP.POP.TOTL"), zip_path)
        logging.info(f"Renamed downloaded file to '{zip_path}'.")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(inputdir)
        logging.info(f"Successfully unzipped '{zip_path}'.")

    except Exception as e:
        logging.fatal(f"An error occurred while processing the downloaded file: {e}")
        raise RuntimeError("Failed to process downloaded files.") from e

def preprocess_files(inputdir):
    """
    Renames the data file, removes metadata files, and preprocesses the data.
    """
    try:
        data_file_path = None
        # Find and rename the main data file
        for filename in os.listdir(inputdir):
            if filename.startswith("API_") and filename.endswith(".csv"):
                original_path = os.path.join(inputdir, filename)
                new_path = os.path.join(inputdir, "wb_subnational_input.csv")
                os.rename(original_path, new_path)
                data_file_path = new_path
                logging.info(f"Renamed '{filename}' to 'wb_subnational_input.csv'.")
                break  # Assuming only one data file

        # Remove metadata files
        files_in_dir = os.listdir(inputdir)
        for filename in files_in_dir:
            if filename.startswith("Metadata_") and filename.endswith(".csv"):
                os.remove(os.path.join(inputdir, filename))
                logging.info(f"Removed metadata file: '{filename}'.")

        if data_file_path and os.path.exists(data_file_path):
            logging.info(f"Preprocessing '{data_file_path}'...")
            # The downloaded CSV from World Bank API has 4 lines of metadata at the top.
            df = pd.read_csv(data_file_path, skiprows=4, encoding='latin1')
            df['Country Name'] = df["Country Name"].str.replace(",", "-")
            df.to_csv(data_file_path, index=False, encoding='utf-8')
            logging.info("Preprocessing complete.")
        else:
            logging.warning("No data file found to preprocess.")

    except Exception as e:
        logging.fatal(f"An error occurred during preprocessing: {e}")
        raise RuntimeError("Failed to preprocess data.") from e

def main(_):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "input_files")

    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        logging.info(f"Created input_files directory: {input_dir}")

    logging.info("Downloading World Bank subnational population data via API...")
    download_success = download_file(
        url=_API_URL,
        output_folder=input_dir,
        unzip=False  # We will handle unzipping manually
    )

    if download_success:
        logging.info("Download complete. Unzipping and preprocessing files...")
        unzip_file(input_dir)
        preprocess_files(input_dir)
        logging.info("Script finished successfully. Processed file is in the 'input_files' directory.")
    else:
        logging.fatal("Failed to download the data file.")
        raise RuntimeError("Download failed.")

if __name__ == "__main__":
   app.run(main)