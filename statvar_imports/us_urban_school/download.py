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
flags.DEFINE_string('data_type', None, 'The type of data to download: "enrollment" or "teachers".')
flags.mark_flag_as_required('data_type')

BASE_URL_TEMPLATE = "https://civilrightsdata.ed.gov/assets/ocr/docs/{}.zip"

DATA_CONFIGS = {
    # Enrollment Data Keywords
    "enrollment": {
        "keywords": [r'Enrollment\.(csv|xlsx)$', r'Pt 1-Enrollment\.xlsx$', r'School Data\.csv$'],
        "search_constraint": {
            "2011-12": "05 - Overall Enrollment.xlsx"
        },
        "output_name_fragment": "Enrollment",
    },
    # Teachers/Staff Data Keywords
    "teachers": {
        "keywords": [
            r'School Support\.(csv|xlsx)$', 
            r'School Support and Security Staff.*\.xlsx$',
            r'Pt 1-Teachers.*Teachers\.xlsx$',
            r'School Data\.csv$' 
        ],
        "search_constraint": {
            "2011-12": "22 - Teachers.xlsx",
            "2015-16": "School Data.csv",
        },
        "output_name_fragment": "Teachers",
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
    """
    logging.info(f"-> Starting post-processing for {file_path.name}")
    try:
        if file_path.suffix == '.xlsx':
            df = pd.read_excel(file_path, engine='openpyxl')
        elif file_path.suffix == '.csv':
            df = pd.read_csv(file_path, low_memory=False, encoding='latin1')
        else:
            logging.info(f"Skipping year column addition for unsupported file format: {file_path.suffix}")
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

        if file_path.suffix == '.xlsx':
            df.to_excel(file_path, index=False)
        elif file_path.suffix == '.csv':
            df.to_csv(file_path, index=False)
            
        logging.info(f"-> Successfully added 'YEAR' and 'ncesid' columns to {file_path.name}")

    except Exception as e:
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
    """Handles downloading the ZIP content with retries and status checks."""
    try:
        head_response = requests.head(zip_url, allow_redirects=True, timeout=10)
        head_response.raise_for_status() 
        response = requests.get(zip_url, stream=True, timeout=180)
        response.raise_for_status() 
        return response
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise requests.exceptions.FileExistsError(f"URL returned 404: {zip_url}") from e
        raise

def get_file_keywords(data_type, config_key):
    """Retrieves the relevant keywords and constraints for the file extraction."""
    config = DATA_CONFIGS.get(data_type, {})
    keywords = config.get("keywords", [])
    search_constraints = config.get("search_constraint", {})
    specific_constraint = search_constraints.get(config_key, None)
    # Get output name fragment (e.g., "Enrollment" or "Teachers")
    output_name_fragment = config.get("output_name_fragment", "Data")
    return keywords, specific_constraint, output_name_fragment


def download_and_extract(config_key, config_data, data_type, output_dir):
    """
    Downloads the ZIP archive and extracts the target file using keyword search,
    then adds the year column and ncesid.
    """
    final_year = config_data["final_year"]
    
    keywords, search_constraint, output_name_fragment = get_file_keywords(data_type, config_key)

    url_fragment = f"{config_key}-crdc-data"
    zip_url = BASE_URL_TEMPLATE.format(url_fragment)

    output_name = f"{final_year}_{output_name_fragment}.csv"
    output_path = output_dir / output_name
    
    logging.info(f"\n--- Processing {config_key} data ({data_type.capitalize()}) (Final Year: {final_year}) ---")

    try:
        logging.info(f"Source URL: {zip_url}")
        logging.info("Attempting to download ZIP archive...")
        response = download_url_with_retry(zip_url)
    except requests.exceptions.FileExistsError:
        logging.info(f"File not found (404) for {config_key}. Assuming release is not yet available and skipping.")
        return
    except Exception as e:
        raise RuntimeError(f"Failed to connect/download archive after retries for {config_key}: {e}")

    logging.info("Download successful. Now extracting...")
    
    try:
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content) as zip_ref:
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

    except Exception as e:
        raise RuntimeError(f"An unhandled error occurred during extraction/processing for {config_key}: {e}")


def main(_):
    """Main function to run the download process for the specified data type."""
    data_type = FLAGS.data_type.lower()
    if data_type not in DATA_CONFIGS:
        sys.exit(f"Invalid data_type '{data_type}'. Must be 'enrollment' or 'teachers'.")

    OUTPUT_DIR = SCRIPT_DIR / data_type / "input_files"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logging.info(f"Starting download process for '{data_type.upper()}' data. Output directory: {OUTPUT_DIR}")

    full_config = HARDCODED_CONFIGS.copy()

    latest_known_year = max(int(k.split('-')[0]) for k in HARDCODED_CONFIGS.keys()) + 2
    
    future_configs = generate_future_configs(latest_known_year)
    full_config.update(future_configs)

    sorted_configs = sorted(full_config.items(), key=lambda item: int(item[0].split('-')[0]))

    for year_range, config_data in sorted_configs:
        download_and_extract(year_range, config_data, data_type, OUTPUT_DIR)
        
    logging.info(f"\n--- All {data_type.upper()} downloads complete ---")

if __name__ == '__main__':
    app.run(main)
