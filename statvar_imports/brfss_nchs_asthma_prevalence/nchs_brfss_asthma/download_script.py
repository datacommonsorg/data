# Copyright 2025 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#      https://www.apache.org/licenses/LICENSE-2.0

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
from datetime import date
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
    'by_race_and_state': 'by_race_and _state',
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
        # Handle 2-digit vs 4-digit year in URL path
        url_year = str(year) if year >= 2010 else str(year)[2:]
        
        # Handle .htm vs .html file extension
        file_ext = 'html' if year >= 2018 else 'htm'
        
        base_path = f"https://www.cdc.gov/asthma/brfss/{url_year}"
        adult_url = f"{base_path}/brfssdata.{file_ext}"
        
        # Handle the change in URL structure for child data
        if year >= 2015:
            child_url = f"{base_path}/child/brfsschilddata.{file_ext}"
        else:
            child_url = f"{base_path}/brfsschilddata.{file_ext}"
            
        generated_urls.extend([adult_url, child_url])
        
    return generated_urls


def get_link_text_and_normalize(element):
    """
    Extracts and sanitizes text from a BeautifulSoup element.
    """
    if element and element.get_text(strip=True):
        raw_text = element.get_text(strip=True).replace(':', '').strip().lower()
        # Clean up text by replacing non-alphanumeric characters with underscores
        sanitized_text = re.sub(r'[^a-zA-Z0-9_]+', '_', raw_text).strip('_')
        return sanitized_text
    return None


def get_table_links(url):
    """
    Fetches a webpage and extracts links to data tables along with associated
    text for use as folder names by searching for li, br, and div tags.
    
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
        all_links = soup.find_all('a', href=re.compile(r'\.htm(l)?$'))
        
        for link in all_links:
            absolute_url = urllib.parse.urljoin(url, link['href'])
            folder_name = None
            
            # Strategy 1: Find text in the parent <li> tag
            li_tag = link.find_parent('li')
            if li_tag:
                full_text = li_tag.get_text(strip=True)
                link_text = link.get_text(strip=True)
                raw_text = full_text.replace(link_text, '', 1).strip()
                if raw_text:
                    folder_name = re.sub(r'Table L\d+:\s*', '', raw_text, flags=re.IGNORECASE).strip().lower()
                    folder_name = re.sub(r'[^a-zA-Z0-9_]+', '_', folder_name).strip('_')

            # Strategy 2: Find text after a <br> tag
            if not folder_name:
                br_tag = link.find('br')
                if br_tag and br_tag.next_sibling and br_tag.next_sibling.strip():
                    folder_name = get_link_text_and_normalize(br_tag.next_sibling)

            # Strategy 3: Find text in a sibling <div> tag
            if not folder_name:
                next_sibling = link.find_next_sibling('div')
                if next_sibling:
                    folder_name = get_link_text_and_normalize(next_sibling)
            
            # Fallback: Use link text and URL basename
            if not folder_name:
                link_text = link.get_text(strip=True).lower()
                folder_name = re.sub(r'[^a-zA-Z0-9_]+', '_', link_text + '_' + os.path.basename(absolute_url)).strip('_')

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
    """
    Moves files from the old `by_race_and_state` directory to the new
    `by_race_ethnicity_and_state` directory and then removes the old directory.
    This handles a naming change in the datasets.
    """
    source_folder = os.path.join(root_dir, 'by_race_and _state')
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
    Downloads, processes, and saves a single data table from a given URL.
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
        logging.fatal(f"Error processing {url}: {e}")
        raise RuntimeError(e)


def main(_):
    root_dir = 'input_files'
    current_year = date.today().year
    urls = generate_urls(2001, current_year)
    
    for main_url in urls:
        logging.info(f"Processing main URL: {main_url}")
        
        year, life_stage = get_metadata_from_url(main_url)
        all_urls_and_folders = get_table_links(main_url)
        
        processed_unified_names = set()
        
        for url, original_folder_name in all_urls_and_folders:
            unified_folder_name = None
            for keyword, unified_name in required_dataset.items():
                if original_folder_name.startswith(keyword):
                    unified_folder_name = unified_name
                    break
            
            if unified_folder_name:
                if unified_folder_name in processed_unified_names:
                    logging.warning(f"Skipping {original_folder_name}. '{unified_folder_name}' already processed for {year}.")
                    continue
                
                # Create the directory for the unified name
                tag_folder_path = os.path.join(root_dir, unified_folder_name)
                os.makedirs(tag_folder_path, exist_ok=True)
                
                # Generate a unique filename and download
                filename = generate_filename(original_folder_name, year, life_stage)
                save_path = os.path.join(tag_folder_path, filename)
                download_table(url, year, life_stage, save_path)
                
                processed_unified_names.add(unified_folder_name)

    logging.info("All URL processing complete.")
    move_and_remove_files_compact(root_dir)
    logging.info("Files moved successfully.")


if __name__ == "__main__":
    app.run(main)