# Copyright 2025 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#      https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import requests
from bs4 import BeautifulSoup
import urllib.parse
import pandas as pd
import warnings
import shutil
from datetime import date # Import the date class
from absl import logging
from absl import app


# Suppress pandas FutureWarnings
warnings.simplefilter(action='ignore', category=FutureWarning)

logging.set_verbosity(logging.INFO)

required_dataset = {
    'by_race_ethnicity': 'by_race_ethnicity_and_state',
    'overall': 'overall_by_state',
    'by_sex': 'by_sex_and_state',
    'by_age': 'by_age_and_state',
    'by_race_and_state': 'by_race_and_state',
    'by_education': 'by_education_and_state',
    'by_income': 'by_income_and_state',
}

def generate_urls(start_year, end_year):
    """
    Generates a list of CDC Asthma BRFSS URLs for a given range of years.
    
    Args:
        start_year (int): The starting year for the URL generation.
        end_year (int): The ending year (inclusive) for the URL generation.
        
    Returns:
        list: A list of dynamically generated URLs.
    """
    generated_urls = []
    for year in range(start_year, end_year + 1):
        year_str = str(year)
        # Handle the transition from 2-digit to 4-digit years in the URL path
        if year >= 2010:
            url_year = year_str
        else:
            url_year = year_str[2:]
        
        # Handle the change from .htm to .html in 2018
        file_ext = 'html' if year >= 2018 else 'htm'
        
        # Handle the change in URL structure for child data in 2015
        if year >= 2015:
            adult_url = f"https://www.cdc.gov/asthma/brfss/{url_year}/brfssdata.{file_ext}"
            child_url = f"https://www.cdc.gov/asthma/brfss/{url_year}/child/brfsschilddata.{file_ext}"
        elif year == 2002:
            adult_url = f"https://www.cdc.gov/asthma/brfss/{url_year}/brfssdata.{file_ext}"
            child_url = f"https://www.cdc.gov/asthma/brfss/{url_year}/brfsschilddata.{file_ext}"
        else:
            adult_url = f"https://www.cdc.gov/asthma/brfss/{url_year}/brfssdata.{file_ext}"
            child_url = f"https://www.cdc.gov/asthma/brfss/{url_year}/brfsschilddata.{file_ext}"

        generated_urls.append(adult_url)
        if year >= 2002 and year != 2017:
            generated_urls.append(child_url)

    return generated_urls

current_year = date.today().year
urls = generate_urls(2001, current_year)

def get_table_links(url):
    """
    Fetches a webpage and extracts links to data tables along with associated
    text from a <br> tag or the entire <a> tag for use as folder names.
    
    Args:
        url (str): The URL of the webpage.
        
    Returns:
        list: A list of tuples, where each tuple contains (absolute_url, folder_name).
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urllib.parse.urljoin(url, href)
            
            br_tag = link.find('br')
            folder_name = 'default_folder'

            if absolute_url.lower().endswith(('.htm', '.html')):
                if br_tag:
                    raw_text = br_tag.next_sibling
                    if raw_text and raw_text.strip():
                        sanitized_text = raw_text.strip().lower()
                        folder_name = re.sub(r'[^a-zA-Z0-9_]+', '_', sanitized_text)
                        folder_name = folder_name.replace(' ', '_').strip('_')
                else:
                    # Text is in a sibling <div>
                    next_sibling = link.next_sibling
                    if next_sibling and next_sibling.name == 'div':
                        raw_text = next_sibling.get_text(strip=True)
                        if raw_text:
                            sanitized_text = raw_text.lower()
                            folder_name = re.sub(r'[^a-zA-Z0-9_]+', '_', sanitized_text)
                            folder_name = folder_name.replace(' ', '_').strip('_')
            
            if (absolute_url, folder_name) not in table_links:
                table_links.append((absolute_url, folder_name))
        return table_links
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching the URL {url}: {e}")
        return []


def generate_filename(folder_name, year, life_stage):
    """
    Generates a dynamic filename based on the folder name (which is now unique), 
    year, and life stage.
    """
    return f"{folder_name}_{year}_{life_stage}.csv"

def get_metadata_from_url(url):
    """
    Extracts year and life stage information from a URL.
    """
    match = re.search(r'/(20\d{2}|\d{2})/', url)
    year = match.group(1) if match else 'unknown'
    if len(year) == 2:
        year = '19' + year if int(year) > 50 else '20' + year
    life_stage = 'child' if 'child' in url.lower() else 'adult'
    return year, life_stage

def move_and_remove_files_compact(root_dir):
    source_folder = os.path.join(root_dir, 'by_race_and_state')
    destination_folder = os.path.join(root_dir, 'by_race_ethnicity_and_state')

    if not os.path.exists(source_folder):
        logging.warning(f"Source '{source_folder}' not found. Skipping.")
        return

    os.makedirs(destination_folder, exist_ok=True)
    
    for filename in os.listdir(source_folder):
        shutil.move(os.path.join(source_folder, filename), destination_folder)
        logging.info(f"Moved {filename}.")

    os.rmdir(source_folder)
    logging.info(f"Removed source folder '{source_folder}'.")
    
def download_table(url, year, life_stage, save_path):
    """
    Downloads, processes, and saves a single data table.
    """
    try:
        logging.info(f"Processing {url}...")
        tables = pd.read_html(url, header=0, encoding='utf-8')
        if tables:
            df = tables[0]
            df['year'] = year
            df['life_stage'] = life_stage
            df.to_csv(save_path, index=False)
            logging.info(f"Successfully saved table from {url} to {save_path}")
        else:
            logging.warning(f"No tables found on page: {url}")
    except Exception as e:
        logging.error(f"Error processing {url}: {e}")

def main(_):
    
    root_dir = 'input_files'
    # Main loop to process each top-level URL
    for main_url in urls:
        logging.info(f"Processing main URL: {main_url}")
        
        year, life_stage = get_metadata_from_url(main_url)
        all_urls_and_folders = get_table_links(main_url)
        
        filtered_and_mapped_urls_with_original_name = []
        processed_unified_names = set()
        
        for url, original_folder_name in all_urls_and_folders:
            
            unified_folder_name = None
            # Use the prioritized list for partial matching
            for keyword, unified_name in required_dataset.items():
                if original_folder_name.startswith(keyword):
                    unified_folder_name = unified_name
                    break
            
            if unified_folder_name:
                # NEW LOGIC: Check if this unified category has already been processed for this main_url/year.
                if unified_folder_name in processed_unified_names:
                    logging.warning(
                        f"Skipping file name candidate: {original_folder_name}. Category '{unified_folder_name}' "
                        f"has already been processed for {year} (First match wins)."
                    )
                    continue

                # Store original_folder_name for unique filename, and unified_folder_name for directory grouping
                filtered_and_mapped_urls_with_original_name.append((url, original_folder_name, unified_folder_name))
                processed_unified_names.add(unified_folder_name) # Add the unified name to tracking set
        
        if filtered_and_mapped_urls_with_original_name:
            for url, original_folder_name, unified_folder_name in filtered_and_mapped_urls_with_original_name:
                
                # 1. Use the unified name for the directory (grouping)
                tag_folder_path = os.path.join(root_dir, unified_folder_name)
                
                if not os.path.exists(tag_folder_path):
                    os.makedirs(tag_folder_path)
                    logging.info(f"Created directory: {tag_folder_path}")
                    
                # 2. Use the original_folder_name for the file name (uniqueness)
                filename = generate_filename(original_folder_name, year, life_stage)
                save_path = os.path.join(tag_folder_path, filename)
                
                download_table(url, year, life_stage, save_path)
        else:
            logging.warning(f"No desired tables found on page: {main_url}.")

    logging.info("All URL processing complete.")
    move_and_remove_files_compact(root_dir)
    #To  use the common pvmap for race and race_ethinicity
    logging.info("file moved successfully")

if __name__=="__main__":
    app.run(main)