# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import requests
import zipfile
import io
import pandas as pd
from absl import logging, app, flags
from pathlib import Path
from retry import retry
import sys

# reusing configs from the main script
from download_ap_ib_gt import DATA_CONFIGS, SCRIPT_DIR, add_year_column, get_file_keywords, get_req_cols_from_config, download_url_with_retry, BASE_URL_TEMPLATE

FLAGS = flags.FLAGS




def download_and_extract_2015_16(data_type, output_dir):
    """
    Downloads the ZIP archive for 2015-16 and extracts the target file.
    """
    config_key = "2015-16"
    final_year = 2016
    
    keywords, search_constraint, output_name_fragment, pvmap_config = get_file_keywords(data_type, config_key)

    url_fragment = f"{config_key}-crdc-data"
    zip_url = BASE_URL_TEMPLATE.format(url_fragment)

    logging.info(f"\n--- Processing {config_key} data ({data_type.capitalize()}) (Final Year: {final_year}) ---")

    try:
        logging.info(f"Source URL: {zip_url}")
        logging.info("Attempting to download ZIP archive...")
        response = download_url_with_retry(zip_url)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logging.info(f"File not found (404) for {config_key}. Assuming release is not yet available and skipping.")
            return
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to connect/download archive after retries for {config_key}: {e}")

    logging.info("Download successful. Now extracting...")
    
    try:
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content) as zip_ref:
            output_name = f"{final_year}_{output_name_fragment}.csv"
            output_path = output_dir / output_name
            
            if output_path.exists():
                logging.info(f"'{output_path.name}' already exists. Skipping download for 2015-16.")
                return

            logging.info("--- Applying special handling for 2015-16 data ---")
            main_csv_path = 'Data Files and Layouts/CRDC 2015-16 School Data.csv'
            if main_csv_path not in zip_ref.namelist():
                logging.warning(f"Could not find '{main_csv_path}' in archive {config_key}. Skipping.")
                return

            logging.info(f"Extracting full file: {main_csv_path} to read in memory")
            with zip_ref.open(main_csv_path) as source_file:
                df = pd.read_csv(source_file, low_memory=False, encoding='latin1')

            config_file_path = SCRIPT_DIR / 'config' / pvmap_config
            req_cols = get_req_cols_from_config(config_file_path)

            if req_cols:
                existing_cols = [col for col in req_cols if col in df.columns]
                missing_cols = set(req_cols) - set(existing_cols)
                if missing_cols:
                    logging.warning(f"Columns not found in 2015-16 data and will be skipped: {missing_cols}")
                
                logging.info(f"Filtering 2015-16 data to {len(existing_cols)} columns for {data_type}.")
                df = df[existing_cols]

            logging.info(f"Saving filtered data to {output_path}")
            df.to_csv(output_path, index=False)
            
            add_year_column(output_path, final_year)
            logging.info(f"Successfully extracted and processed: {output_path.name}")
            return

    except zipfile.BadZipFile:
        logging.warning(f"Downloaded content for {config_key} is not a valid ZIP file. Skipping.")
        return
    except Exception as e:
        raise RuntimeError(f"An unhandled error occurred during extraction/processing for {config_key}: {e}")

def main(_):
    """
    Main function to run the download process for 2015-16 AP, IB, and GT data.
    """
    BASE_OUTPUT_DIR = SCRIPT_DIR

    data_types_to_download = []
    if FLAGS.ap:
        data_types_to_download.append("ap")
    if FLAGS.ib:
        data_types_to_download.append("ib")
    if FLAGS.gt:
        data_types_to_download.append("gt")

    if not data_types_to_download:
        data_types_to_download = list(DATA_CONFIGS.keys())

    for data_type in data_types_to_download:
        config = DATA_CONFIGS[data_type]
        output_dir_name = config["output_dir_name"]
        OUTPUT_DIR = BASE_OUTPUT_DIR / output_dir_name
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        download_and_extract_2015_16(data_type, OUTPUT_DIR)
            
    logging.info(f"\n--- All 2015-16 downloads complete ---")

if __name__ == '__main__':
    app.run(main)
