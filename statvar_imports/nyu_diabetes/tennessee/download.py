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
from datetime import date
from pathlib import Path
import re
from urllib.parse import urlparse

from absl import app, logging
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from retry import retry
from tqdm import tqdm
from urllib3.util.retry import Retry

script_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(script_dir, "input_files")
Path(INPUT_DIR).mkdir(parents=True, exist_ok=True)

def get_session():
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    session.headers.update(headers)
    return session

@retry(tries=4, delay=3, backoff=2)
def _fetch_url(session, url):
    return session.get(url, timeout=60)

def download_files(url_list, save_folder):
    os.makedirs(os.path.join(save_folder), exist_ok=True)
    session = get_session()
    downloaded_count = 0

    for url in url_list:
        try:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            file_path = os.path.join(save_folder, filename)

            logging.info(f"Downloading: {filename}")

            response = _fetch_url(session, url)
            if response.status_code == 404:
                logging.info(f"File not yet available (HTTP 404): {url}")
                continue
            response.raise_for_status()

            with response as r:
                total_size = int(r.headers.get('content-length', 0))
                block_size = 1024
                with open(file_path, 'wb') as f, tqdm(
                    total=total_size, unit='B', unit_scale=True, desc=filename, leave=False
                ) as progress_bar:
                    for chunk in r.iter_content(block_size):
                        f.write(chunk)
                        progress_bar.update(len(chunk))
            logging.info(f"Saved: {file_path}\n")
            downloaded_count += 1
        except Exception as e:
            logging.error(f"Failed to download {url}: {e}\n")
            raise RuntimeError(f"Failed to download required file {url}: {e}") from e

    if downloaded_count == 0:
        raise RuntimeError("No files were successfully downloaded.")

def generate_urls(start_year, end_year, url_template):
    url_list = []
    for year in range(start_year,end_year+1):
        formatted_url = url_template.format(year,year)
        url_list.append(formatted_url)
    return url_list

def extract_year(filename):
    """Extracts a four-digit year from the filename using regex."""
    match = re.search(r'Diabetes_County_(\d{4}).xlsx', filename)
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
            year = extract_year(filename)
            
            if year is None:
                logging.warning(f"Could not find year for file in map: {relative_key}. Skipping processing.")
                continue

            try:
                df = pd.read_excel(file_path)
                df['year'] = year
                df.to_excel(file_path, index=False)
                
            except Exception as e:
                raise RuntimeError(f"Failed to process and save Excel file {filename}: {e}")

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
