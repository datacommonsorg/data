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

def download_files(url_dict, save_folder):
    os.makedirs(os.path.join(save_folder, "race"), exist_ok=True)
    os.makedirs(os.path.join(save_folder, "race_male"), exist_ok=True)
    os.makedirs(os.path.join(save_folder, "race_female"), exist_ok=True)

    for url,folder in url_dict.items():
        try:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            file_path = os.path.join(save_folder, folder, filename)

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

def generate_urls(start_year, end_year):
    urls = {
        "https://www.tn.gov/content/dam/tn/health/documents/vital-statistics/death/{}/AllCauseMort_CountyRace_{}.xlsx":"race",
        "https://www.tn.gov/content/dam/tn/health/documents/vital-statistics/death/{}/AllCauseMort_CountyRaceMale_{}.xlsx":"race_male",
        "https://www.tn.gov/content/dam/tn/health/documents/vital-statistics/death/{}/AllCauseMort_CountyRaceFemale_{}.xlsx":"race_female",
    }
    url_dict = {}
    for url_template, folder in urls.items():
        for year in range(start_year,end_year+1):
            formatted_url = url_template.format(year,year)
            url_dict[formatted_url] = folder
    return url_dict

def extract_year(url):
    """Extracts a four-digit year from the filename using regex."""
    match = YEAR_REGEX.search(url)
    if match:
        return int(match.group(1))
    return None

def process_excel_files(input_dir, file_year_map):
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
            
            # Construct the unique identifier used as key in file_year_map: folder/filename
            folder = os.path.basename(root)
            relative_key = os.path.join(folder, filename)
            
            # Lookup the year using the reliable map
            year = file_year_map.get(relative_key)
            
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
    fixed_urls = {
        "https://www.tn.gov/content/dam/tn/health/documents/vital-statistics/death/2018/TN%20Deaths%20-%202018.xlsx":"race",
        "https://www.tn.gov/content/dam/tn/health/documents/vital-statistics/death/2020/AllCauseMort-CountyRace-2020.xlsx":"race",
        "https://www.tn.gov/content/dam/tn/health/documents/vital-statistics/death/2020/AllCauseMort-CntyRaceMale-2020.xlsx":"race_male",
        "https://www.tn.gov/content/dam/tn/health/documents/vital-statistics/death/2019/AllCauseMort_CntyRaceMale_2019.xlsx":"race_male",
        "https://www.tn.gov/content/dam/tn/health/documents/vital-statistics/death/2020/AllCauseMort-CntyRaceFemale-2020.xlsx":"race_female",
        "https://www.tn.gov/content/dam/tn/health/documents/vital-statistics/death/2019/AllCauseMort_CntyRaceFemale_2019.xlsx":"race_female"
    }
    start_year = 2021
    current_year = date.today().year
    formatted_urls = generate_urls(start_year, current_year)
    final_url_dict = fixed_urls.copy()
    final_url_dict.update(formatted_urls)
    formatted_2019_2020_urls = generate_urls(2019, 2020)
    for url, folder in formatted_2019_2020_urls.items():
        if url not in final_url_dict:
            final_url_dict[url] = folder
    
    file_year_map = {}
    for url, folder in final_url_dict.items():
        year = extract_year(url)
        if year is not None:
            # Create the key for the map: folder/filename (e.g., 'race/TN%20Deaths%20-%202018.xlsx')
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            relative_key = os.path.join(folder, filename)
            file_year_map[relative_key] = year
        else:
            logging.error(f"Could not extract year from URL: {url}. This file will not have the 'year' column added.")  

    download_files(final_url_dict, save_folder=INPUT_DIR)

    process_excel_files(INPUT_DIR, file_year_map)

if __name__ == "__main__":
    app.run(main)
