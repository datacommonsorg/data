# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#           https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# How to run the script to download the files:
# python3 download.py
import requests
from bs4 import BeautifulSoup
import os
import zipfile
from absl import app
from absl import logging
from retry import retry

@retry(tries=3, delay=2)
def download_retry(url):
    response = requests.get(url, stream=True, timeout=30)
    return response

def download_xlsx_from_ncses_table(url, current_year):
    """
    Downloads a specific ZIP file from a given URL, identified by its filename.
    The ZIP file is stored uniquely in 'source_files'.
    A specific XLSX file is extracted to 'input_files' (overwriting previous year's data there).

    Args:
        url (str): The URL of the web page to scrape.

    Returns:
        bool: True if the URL was fetched successfully, False otherwise.
    """

    logging.info(f"Fetching URL: {url}")
    try:
        response = download_retry(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        #used loggings.warning to prevent its overall execution
        logging.warning(f"Error fetching the page: {e}")
        return False

    soup = BeautifulSoup(response.text, 'html.parser')
    desired_zip_filename = 'data-tables-tables-excels.zip'
    required_data = 'tab004-002.xlsx'
    download_link = None
    all_zip_links_found_on_page = []

    # Iterate over all a tags to find the required static ZIP link
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        # check the required filename
        if href and desired_zip_filename.lower() in href.lower():
            if href.lower().endswith('.zip'):
                all_zip_links_found_on_page.append(link)
                if os.path.basename(href).lower() == desired_zip_filename.lower():
                    download_link = link
                    break

    if not download_link and len(all_zip_links_found_on_page) == 1:
        download_link = all_zip_links_found_on_page[0]
        logging.info(f"Found a single ZIP link containing '{desired_zip_filename}' in its href: {download_link.get('href')}")
    elif not download_link:
        logging.warning(f"No suitable download link found for {desired_zip_filename} on {url}")
        return False


    xlsx_url = download_link.get('href')
    # If the URL is relative, make it absolute
    if not xlsx_url.startswith('http'):
        xlsx_url = requests.compat.urljoin(url, xlsx_url)

    logging.info(f"Found target ZIP file URL: {xlsx_url}")

    logging.info(f"Downloading ZIP file from: {xlsx_url}")
    zip_filepath = None

    try:
        download_response = requests.get(xlsx_url, stream=True, timeout=30)
        download_response.raise_for_status()
        source_files_zip_base_dir = "source_files"
        os.makedirs(source_files_zip_base_dir, exist_ok=True)
        unique_zip_filename = f"{current_year}_{desired_zip_filename}"
        zip_filepath = os.path.join(source_files_zip_base_dir, unique_zip_filename)
        with open(zip_filepath, 'wb') as f:
            for chunk in download_response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Successfully downloaded: {zip_filepath}")

        # unzipping the zip file
        if zipfile.is_zipfile(zip_filepath):
            logging.info(f"Unzipping {zip_filepath}...")
            extract_path = os.path.join("input_files")
            os.makedirs(extract_path, exist_ok=True)
            with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            logging.info(f"Extracted to: {extract_path}")

            # file extraction logic
            logging.info(f"Processing extracted files in: {extract_path}")
            extracted_files = os.listdir(extract_path)
            for f in extracted_files:
                full_file_path = os.path.join(extract_path, f)
                # Check if it's a file and an XLSX, and if it contains the desired fragment
                if os.path.isfile(full_file_path) and f.lower().endswith('.xlsx'):
                    if required_data.lower() in f.lower():
                        logging.info(f"Keeping target XLSX file: {full_file_path}")
                    else:
                        # removing unnecessary xlsx files
                        os.remove(full_file_path)
                        logging.info(f"Removed non-target XLSX file: {full_file_path}")

                elif os.path.isfile(full_file_path): # Remove other non-XLSX file like pdfs
                    os.remove(full_file_path)
                    logging.info(f"Removed non-XLSX file: {full_file_path}")
        else:
            logging.fatal("Downloaded file is not a valid ZIP archive (or could not be identified as such).")

    except (requests.exceptions.RequestException, zipfile.BadZipFile, OSError) as e:  
        logging.fatal(f"An unexpected error occurred during file processing: {e}")
        return False # Return False to indicate failure for this year

    return True

def main(argv):
    # In the UI data is available from 2021 only.
    start_year = 2021

    base_url="https://ncses.nsf.gov/surveys/national-survey-college-graduates/{year}#data"

    failure = 0
    failure_threshold = 3 

    while True: 
        target_url = base_url.format(year=start_year)
        logging.info(f"Attempting to process data for year: {start_year}")

        if download_xlsx_from_ncses_table(target_url, start_year):
            logging.info(f"Successfully processed data for year: {start_year}")
            failure = 0 
        else:
            logging.warning(f"No data available or error fetching URL for year {start_year}.")
            failure += 1 

     
        if failure >= failure_threshold:
            logging.fatal(f"Reached {failure_threshold} consecutive years with no data.Exiting.")
            break 
        #getting data on every 2 years
        start_year += 2

if __name__=="__main__":
    app.run(main)