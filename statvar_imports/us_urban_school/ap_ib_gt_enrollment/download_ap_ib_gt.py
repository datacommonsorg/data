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
import re
from absl import logging, app, flags
from pathlib import Path
from datetime import date
from retry import retry
import sys

FLAGS = flags.FLAGS

flags.DEFINE_boolean('ap', False, 'Download Advanced Placement data only.')
flags.DEFINE_boolean('ib', False, 'Download International Baccalaureate data only.')
flags.DEFINE_boolean('gt', False, 'Download Gifted and Talented data only.')

BASE_URL_TEMPLATE = "https://civilrightsdata.ed.gov/assets/ocr/docs/{}.zip"

DATA_CONFIGS = {

    # Advanced Placement Data Keywords

    "ap": {

        "keywords": [r'AP', r'Advanced Placement'],

        "search_constraint": {

            "2009-10": "CRDC-data_SCH_Pt 1-Advanced Placement.xlsx"

        },

        "output_name_fragment": "AP_Enrollment",

        "output_dir_name": "advanced_placements/input_files",

        "pvmap_config": "ap_enrollment_pvmap.csv"

    },

    # International Baccalaureate Data Keywords

    "ib": {

        "keywords": [r'IB', r'International Baccalaureate'],

        "search_constraint": {

            "2009-10": "CRDC-data_SCH_Pt 1-Enrollment_Pt 1-Students enrolled in IB Diploma Programme.xlsx"

        },

        "output_name_fragment": "IB_Enrollment",

        "output_dir_name": "international_baccalaureate/input_files",

        "pvmap_config": "ib_enrollment_pvmap.csv"

    },

    # Gifted and Talented Data Keywords

    "gt": {

        "keywords": [r'Gifted', r'Talented'],

        "search_constraint": {

            "2009-10": "CRDC-data_SCH_Pt 1-Enrollment_Pt 1-Students enrolled in Gifted-Talented Programs.xlsx"

        },

        "output_name_fragment": "GT_Enrollment",

        "output_dir_name": "gifted_and_talented/input_files",

        "pvmap_config": "gt_enrollment_pvmap.csv"

    }

}

HARDCODED_CONFIGS = {
    "2021-22": {"final_year": 2022},
    "2020-21": {"final_year": 2021},
    "2017-18": {"final_year": 2018},
    "2015-16": {"final_year": 2016},
    "2013-14": {"final_year": 2014},
    "2011-12": {"final_year": 2012},
    "2009-10": {"final_year": 2010}

}

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

def add_year_column(file_path, year):

    """
    Reads the file (CSV or XLSX), adds the 'YEAR' and 'ncesid' columns,
    and saves it back, using 'latin1' encoding for robustness.
    If the file is empty or contains no data rows, it is deleted.
    """
    logging.info(f"-> Starting post-processing for {file_path.name}")

    df = pd.DataFrame()

    try:

        if file_path.suffix == '.xlsx':

            df = pd.read_excel(file_path, engine='openpyxl')

        elif file_path.suffix == '.csv':

            try:

                df = pd.read_csv(file_path, low_memory=False, encoding='latin1')

            except pd.errors.EmptyDataError:

                logging.warning(f"Warning: No data found in {file_path.name}. Deleting empty file.")

                os.remove(file_path) # Delete the empty file

                return

        else:

            logging.info(f"Skipping year column addition for unsupported file format: {file_path.suffix}")

            return

        if df.empty:

            logging.warning(f"Warning: DataFrame is empty after reading {file_path.name}. Deleting empty file.")

            os.remove(file_path) # Delete the empty file

            return

        # Add YEAR column

        df['YEAR'] = year

        # Create NCESID column

        if all(col in df.columns for col in ["LEAID", "SCHID"]):

            df["LEAID"] = df["LEAID"].astype(str).str.zfill(7)

            df["SCHID"] = df["SCHID"].astype(str).str.zfill(5)

            df["ncesid"] = df["LEAID"] + df["SCHID"]

        else:

            logging.warning(f"-> Warning: Missing LEAID or SCHID columns for NCESID creation in {file_path.name}")

        # Reorder columns to place 'YEAR', 'ncesid', and 'JJ' (if present) at the beginning

        cols = df.columns.tolist()

        desired_first_cols = ['YEAR', 'ncesid']

        if 'JJ' in cols:

            desired_first_cols.append('JJ')

        # Remove desired_first_cols from their original positions

        for col in desired_first_cols:
            if col in cols:
                cols.remove(col)

        # Construct the new column order

        new_column_order = desired_first_cols + cols

        df = df[new_column_order]

        if file_path.suffix == '.xlsx':

            df.to_excel(file_path, index=False)

        elif file_path.suffix == '.csv':

            df.to_csv(file_path, index=False)

        logging.info(f"-> Successfully added 'YEAR' and 'ncesid' columns to {file_path.name}")

    except Exception as e:

        # If an error occurs during processing but after the file was created, attempt to delete it.

        if file_path.exists():

            os.remove(file_path)

            logging.error(f"Deleted incomplete/corrupted file {file_path.name} due to error: {e}")

        raise RuntimeError(f"Failed to add year/ncesid column to {file_path.name}: {e}")

def generate_future_configs(start_year):

    """
    Generates configuration dictionaries for future biennial CRDC years.
    """
    current_calendar_year = date.today().year

    generated_configs = {}

    for year in range(start_year, current_calendar_year + 1):
        end_year = year + 1
        year_range_key = f"{year}-{end_year % 100:02d}"

        if year_range_key in HARDCODED_CONFIGS:
            continue

        generated_configs[year_range_key] = {

            "final_year": end_year
        }

    return generated_configs

@retry(tries=3, delay=5, backoff=2)

def download_url_with_retry(zip_url):
    """
    Handles downloading the ZIP content with retries and status checks.
    """
    head_response = requests.head(zip_url, allow_redirects=True, timeout=10)
    head_response.raise_for_status()
    response = requests.get(zip_url, stream=True, timeout=180)
    response.raise_for_status()
    return response

def get_file_keywords(data_type, config_key):

    """

    Retrieves the relevant keywords and constraints for the file extraction.

    """

    config = DATA_CONFIGS.get(data_type, {})

    keywords = config.get("keywords", [])

    search_constraints = config.get("search_constraint", {})

    specific_constraint = search_constraints.get(config_key, None)

    # Get output name fragment (e.g., "Enrollment" or "Teachers")

    output_name_fragment = config.get("output_name_fragment", "Data")

    pvmap_config = config.get("pvmap_config")

    return keywords, specific_constraint, output_name_fragment, pvmap_config

def get_req_cols_from_config(config_path):

    """
    Reads a CSV config file to extract a list of required column names.
    It takes the first column, filters out specific values ('YEAR', 'ncesid', ''),
    and adds 'LEAID' and 'SCHID'.
    """

    try:

        df = pd.read_csv(config_path, header=None, usecols=[0], on_bad_lines='skip')
        # Get first column as a list
        req_cols = df[0].tolist()
        # Remove header 'key'
        if 'key' in req_cols:
            req_cols.remove('key')
        # Filter out values
        req_cols = [col for col in req_cols if col not in ['YEAR', 'ncesid', ''] and pd.notna(col)]
        # Add necessary columns for ncesid creation
        req_cols.extend(['LEAID', 'SCHID'])
        return req_cols

    except Exception as e:

        logging.error(f"Failed to read or process config file {config_path}: {e}")

        return None

def download_and_extract(config_key, config_data, data_type, output_dir):
    """
    Downloads the ZIP archive and extracts the target file using keyword search,
    then adds the year column and ncesid.
    """
    final_year = config_data["final_year"]
    
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
            if data_type == 'ap' and config_key in ["2009-10", "2011-12"]:
                logging.info(f"--- Applying special AP subject handling for {config_key} data ---")
                
                math_file_name, science_file_name = None, None
                
                # Find the math and science files in the zip
                for name in zip_ref.namelist():
                    normalized_name = name.lower()
                    # For 2011-12, the files are more specific, e.g., "...Students who are taking AP Science.xlsx"
                    if 'ap' in normalized_name and 'mathematics' in normalized_name and 'students' in normalized_name and not '$' in name:
                        math_file_name = name
                    elif 'ap' in normalized_name and 'science' in normalized_name and 'students' in normalized_name and not '$' in name:
                        science_file_name = name
                
                if not math_file_name or not science_file_name:
                    logging.warning(f"Could not find both AP Mathematics and Science files for {config_key}.")
                    return
                    
                # Read both files into pandas dataframes
                with zip_ref.open(math_file_name) as math_file:
                    df_math = pd.read_excel(math_file)
                with zip_ref.open(science_file_name) as science_file:
                    df_science = pd.read_excel(science_file)
                
                # Merge the dataframes
                merged_df = pd.merge(df_math, df_science, on=['LEAID', 'SCHID'], how='outer')
                
                # Save the merged dataframe
                output_name = f"{final_year}_{output_name_fragment}.xlsx"
                output_path = output_dir / output_name
                merged_df.to_excel(output_path, index=False)
                
                add_year_column(output_path, final_year)
                logging.info(f"Successfully extracted, merged, and saved: {output_path.name}")
                return

            output_name = f"{final_year}_{output_name_fragment}.csv"
            output_path = output_dir / output_name

            target_member = None
            for name in zip_ref.namelist():
                normalized_name = name.replace('\\', '/').lower()
                
                general_match = False
                for pattern in keywords:
                    if re.search(pattern, name, re.IGNORECASE):
                        general_match = True
                        break

                if general_match:
                    if search_constraint:
                        if search_constraint.lower() in name.lower():
                            if '$' not in name:
                                target_member = name
                                break
                    else:
                        if '$' not in name:
                            target_member = name
                            break

            if not target_member:
                logging.warning(f"Error: Could not find '{output_name_fragment}' data file using keyword search in archive {config_key}.")
                logging.info("Files found in ZIP (showing first 5):\n" + '\n'.join(zip_ref.namelist()[:5]))
                return

            if target_member.lower().endswith(".xlsx"):
                output_path = output_dir / output_name.replace(".csv", ".xlsx")
            
            logging.info(f"Found internal file: {target_member}")

            with zip_ref.open(target_member) as source_file:
                target_content = source_file.read()
            
            with open(output_path, 'wb') as f:
                f.write(target_content)

            add_year_column(output_path, final_year)
                
            logging.info(f"Successfully extracted and saved: {output_path.name}")

    except zipfile.BadZipFile:
        logging.warning(f"Downloaded content for {config_key} is not a valid ZIP file. Skipping.")
        return
    except Exception as e:
        raise RuntimeError(f"An unhandled error occurred during extraction/processing for {config_key}: {e}")

def main(_):
    """
    Main function to run the download process for AP, IB, and GT data.
    This script is designed to be run once to download and prepare all files.
    Processing is triggered within download_and_extract for each file.
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

    all_configs = HARDCODED_CONFIGS.copy()
    latest_known_year = max(int(k.split('-')[0]) for k in HARDCODED_CONFIGS.keys()) + 2
    future_configs = generate_future_configs(latest_known_year)
    all_configs.update(future_configs)
    sorted_configs = sorted(all_configs.items(), key=lambda item: int(item[0].split('-')[0]))

    for year_range, config_data in sorted_configs:
        for data_type in data_types_to_download:
            config = DATA_CONFIGS[data_type]
            output_dir_name = config["output_dir_name"]
            OUTPUT_DIR = BASE_OUTPUT_DIR / output_dir_name
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            
            download_and_extract(year_range, config_data, data_type, OUTPUT_DIR)
            
    logging.info(f"\n--- All downloads complete ---")

if __name__ == '__main__':

    app.run(main)
