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
# How to run the script to download the files:
# python3 rbi_sdp_download.py

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from absl import logging
import json
import time
import re

# Configure absl Logging
logging.set_verbosity(logging.INFO)

# Retry method
def retry_request(url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logging.warning(f"Attempt {attempt + 1}/{retries} failed: {str(e)}")
            time.sleep(delay)
    logging.fatal(f"Failed to fetch URL after {retries} attempts: {url}")
    return None

def extract_table_number(table_name):
    match = re.search(r'Table\s+(\d+)', table_name)
    return int(match.group(1)) if match else None

def download_state_tables():
    try:
        # Get the directory where the script is located to build absolute paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config.json")

        with open(config_path) as f:
            config = json.load(f)
    
        base_url = config["base_url"]
        # Ensure download_dir is also relative to the script location
        download_dir = os.path.join(script_dir, config["download_dir"])  # Save in 'source_files'
        
        os.makedirs(download_dir, exist_ok=True)
        
        response = retry_request(base_url)
        if not response:
            logging.fatal("Main page request failed")
            return
        
        # Save raw HTML to 'raw_html.html'
        html_path = os.path.join(download_dir, "raw_html.html")
        with open(html_path, "w", encoding="utf-8") as html_file:
            html_file.write(response.text)
        logging.info(f"Saved raw HTML to {html_path}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        section_header = soup.find('td', class_='tableheader', string=lambda t: t and 'STATE DOMESTIC PRODUCT' in t.upper())
        
        if not section_header:
            logging.fatal("STATE DOMESTIC PRODUCT section not found")
            return
        
        logging.info("Successfully located STATE DOMESTIC PRODUCT section")
        
        main_table = section_header.find_parent('table')
        if not main_table:
            logging.fatal("Main data container table not found")
            return
        
        downloaded_files = 0
        for row in main_table.find_all('tr'):
            title_link = row.find('a', class_='link2')
            xls_link = row.find('a', href=lambda href: href and any(ext in href.upper() for ext in ['.XLS', '.XLSX']))
            
            if not title_link or not xls_link:
                continue
            
            table_name = title_link.text.strip()
            table_number = extract_table_number(table_name)
            
            if not table_number:
                logging.warning(f"Skipping unparseable table: {table_name}")
                continue
            
            if not (19 <= table_number <= 52):
                logging.debug(f"Skipping table {table_number} (out of range)")
                continue
            
            file_url = urljoin(base_url, xls_link['href'])
            clean_name = re.sub(r'[\\/*?:"<>|]', "", table_name)
            filename = f"{clean_name}.xlsx"
            filepath = os.path.join(download_dir, filename)
            
            if os.path.exists(filepath):
                logging.info(f"Skipping existing file: {filename}")
                continue
            
            file_response = retry_request(file_url)
            if file_response:
                with open(filepath, 'wb') as f:
                    f.write(file_response.content)
                downloaded_files += 1
                logging.info(f"Downloaded Table {table_number}: {filename}")
            
        logging.info(f"Total files downloaded: {downloaded_files}")
        
    except Exception as e:
        logging.fatal(f"Critical error: {str(e)}")
        raise
    
if __name__ == "__main__":
    download_state_tables()
    logging.info("Process Completed successfully")