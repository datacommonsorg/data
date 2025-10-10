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
from urllib.parse import urlparse
from tqdm import tqdm  
from retry import retry
from pathlib import Path
from datetime import date
from absl import logging, app
import pandas as pd
import re

script_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(script_dir, "input_files")
Path(INPUT_DIR).mkdir(parents=True, exist_ok=True)

YEAR_REGEX = re.compile(r'/death/(\d{4})/')

@retry(tries=3, delay=5, backoff=2)
def retry_method(url, headers=None):
    response = requests.get(url, headers=headers, timeout=120)
    response.raise_for_status()
    return response

def download_files(url_list, save_folder):
    os.makedirs(os.path.join(save_folder), exist_ok=True)

    for url in url_list:
        try:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            file_path = os.path.join(save_folder, filename)

            logging.info(f"Downloading: {filename}")

            response = retry_method(url)
            with response as r:
                total_size = int(r.headers.get('content-length', 0))
                block_size = 1024
                with open(file_path, 'wb') as f, tqdm(
                    total=total_size, unit='B', unit_scale=True, desc=filename, leave=False
                ) as progress_bar:
                    for chunk in r.iter_content(block_size):
                        f.write(chunk)
                        progress_bar.update(len(chunk))
            logging.info(f"✅ Saved: {file_path}\n")
        except Exception as e:
            logging.error(f"❌ Failed to download {url} after retries: {e}\n")

def generate_urls(start_year, end_year, url_template):
    url_list = []
    for year in range(start_year,end_year+1):
        formatted_url = url_template.format(year,year)
        url_list.append(formatted_url)
    return url_list

def extract_year(url):
    """Extracts a four-digit year from the filename using regex."""
    match = YEAR_REGEX.search(url)
    if match:
        return int(match.group(1))
    return None

def process_excel_files(input_dir):
    """
    Iterates through downloaded Excel files, uses the provided map to determine 
    the year, adds a 'year' column, and saves the modified file.
    """
    logging.info("\nStarting Excel file processing: Adding 'year' column...")

    for root, _, files in os.walk(input_dir):
        excel_files = [f for f in files if f.endswith('.xlsx')]
        
        if not excel_files:
            continue
            
        logging.info(f"Processing {len(excel_files)} files in {os.path.basename(root)}...")

        for filename in tqdm(excel_files, desc=f"Adding Year Column to {os.path.basename(root)}"):
            file_path = os.path.join(root, filename)

            folder = os.path.basename(root)
            relative_key = os.path.join(folder, filename)
            
            year = extract_year(url)
            
            if year is None:
                logging.warning(f"Could not find year for file in map: {relative_key}. Skipping processing.")
                continue

            try:
                df = pd.read_excel(file_path)
                df['year'] = year
                df.to_excel(file_path, index=False)
                
            except Exception as e:
                logging.error(f"Failed to process and save Excel file {filename}: {e}")

    logging.info("\nExcel file processing complete. 'year' column added to all processed files.")

def main(_):
    url_template ="https://www.tn.gov/content/dam/tn/health/documents/vital-statistics/death/{}/Diabetes_County_{}.xlsx"
    start_year = 2019
    current_year = date.today().year
    final_urls = generate_urls(start_year, current_year,url_template)
    
    download_files(final_urls, save_folder=INPUT_DIR)

    process_excel_files(INPUT_DIR)

if __name__ == "__main__":
    app.run(main)
