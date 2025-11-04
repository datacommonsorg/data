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
from absl import logging, app
from pathlib import Path
from datetime import date
from retry import retry

BASE_URL_TEMPLATE = "https://civilrightsdata.ed.gov/assets/ocr/docs/{}.zip"

HARDCODED_CONFIGS = {
    "2021-22": {"final_year": 2022},
    "2020-21": {"final_year": 2021},
    "2017-18": {"final_year": 2018},
    "2015-16": {"final_year": 2016},
    "2013-14": {"final_year": 2014},
    "2011-12": {"final_year": 2012, "search_constraint": "05 - Overall Enrollment.xlsx"},
    "2009-10": {"final_year": 2010}
}

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = SCRIPT_DIR / "input_files"


def add_year_column(file_path, year):
    """
    Reads the file (CSV or XLSX), adds the 'year' column with the final_year value, 
    and saves it back, preserving the original format.
    """
    try:
        if file_path.suffix == '.xlsx':
            df = pd.read_excel(file_path)
        elif file_path.suffix == '.csv':
            df = pd.read_csv(file_path, low_memory=False, encoding='latin1') 
        else:
            logging.info(f"Skipping year column addition for unsupported file format: {file_path.suffix}")
            return

        df['YEAR'] = year

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
        
        logging.info(f"-> Successfully added 'YEAR' column with value {year} to {file_path.name}")

    except Exception as e:
        raise RuntimeError(f"Failed to add year column to {file_path.name}: {e}")

def generate_future_configs(start_year):
    """
    Generates configuration dictionaries for future biennial CRDC years,
    assuming a consistent year pattern.
    """
    current_calendar_year = date.today().year
    generated_configs = {}
    
    for year in range(start_year, current_calendar_year + 1):
        end_year = year + 1
        year_range_key = f"{year}-{end_year % 100:02d}"
        
        generated_configs[year_range_key] = {
            "final_year": end_year
        }
        
    return generated_configs

@retry(tries=3, delay=5, backoff=2)
def download_url_with_retry(zip_url):
    """Handles downloading the ZIP content with retries and status checks."""
    head_response = requests.head(zip_url, allow_redirects=True, timeout=10)
    head_response.raise_for_status()
    
    response = requests.get(zip_url, stream=True, timeout=180)
    response.raise_for_status() 
    return response

def download_and_extract(config_key, config_data):
    """
    Downloads the ZIP archive and extracts the Enrollment file using a keyword search,
    then adds the year column.
    """
    final_year = config_data["final_year"]
    search_constraint = config_data.get("search_constraint", None)
    
    url_fragment = f"{config_key}-crdc-data"
    zip_url = BASE_URL_TEMPLATE.format(url_fragment)

    output_name = f"{final_year}_Enrollment.csv" 
    output_path = OUTPUT_DIR / output_name
    
    logging.info(f"\n--- Processing {config_key} data (Final Year: {final_year}) ---")

    try:
        logging.info(f"Source URL: {zip_url}")
        logging.info("Attempting to download ZIP archive...")
        response = download_url_with_retry(zip_url)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logging.info(f"File not found (404) for {config_key}. Assuming release is not yet available and skipping.")
            return
        raise RuntimeError(f"Failed to download archive after retries for {config_key}: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to connect and download archive after retries for {config_key}: {e}")

    logging.info("Download successful. Now extracting...")
    
    try:
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content) as zip_ref:
            keyword_search_pattern = r'Enrollment\.(csv|xlsx)$|School Data\.csv$|Pt 1-Enrollment\.xlsx$'
            target_member = None
            
            for name in zip_ref.namelist():
                normalized_name = name.replace('\\', '/').lower() 
                
                general_match = re.search(keyword_search_pattern, name, re.IGNORECASE) and \
                                ('enrollment' in normalized_name or 'school data' in normalized_name or 'pt 1-enrollment' in normalized_name)

                if general_match:
                    if search_constraint:
                        if search_constraint.lower() in name.lower():
                            if '$' not in name:
                                target_member = name
                                break
                    else:
                        target_member = name
                        break

            if not target_member:
                logging.info(f"Error: Could not find Enrollment data file using internal keyword search in archive {config_key}.")
                logging.info("Files found in ZIP (showing first 5):\n" + '\n'.join(zip_ref.namelist()[:5]))
                return

            if target_member.lower().endswith(".xlsx"):
                 output_path = OUTPUT_DIR / output_name.replace(".csv", ".xlsx")
            
            logging.info(f"Found internal file: {target_member}")

            with zip_ref.open(target_member) as source_file:
                target_content = source_file.read()
            
            with open(output_path, 'wb') as f:
                f.write(target_content)
            
            add_year_column(output_path, final_year)
                
            logging.info(f"Successfully extracted and saved: {output_path.name}")

    except Exception as e:
        raise RuntimeError(f"An error occurred during extraction/saving for {config_key}: {e}")


def main(_):
    """Main function to run the download process for all configured and future files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logging.info(f"Starting download process. Output directory: {OUTPUT_DIR}")

    full_config = HARDCODED_CONFIGS.copy()
    
    latest_known_year = 2023 
    
    future_configs = generate_future_configs(latest_known_year)
    full_config.update(future_configs)

    for year_range, config_data in full_config.items():
        download_and_extract(year_range, config_data)
        
    logging.info("\n--- All downloads complete ---")


if __name__ == '__main__':
    app.run(main)
