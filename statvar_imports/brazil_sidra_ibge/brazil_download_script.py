# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import time
import sys
import glob
from absl import app, logging, flags
from pathlib import Path

# Import specific Selenium exceptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
BASE_URL = "https://sidra.ibge.gov.br/home/pnadct/"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(SCRIPT_DIR, "input_files")

# Mapping of panel index to subfolder name
PANEL_FOLDER_MAP = {
    1: "Employment_And_Unemployment_Labor_Force",
    2: "Population_Economic_sector",
    3: "Average_Real_Income",
    4: "Mass_Income"
}


def setup_driver():
    """Configures and returns a Selenium WebDriver."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safeBrowse.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    logging.info("WebDriver options configured.")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def wait_for_downloads(timeout=30):
    """Waits for all downloads to finish."""
    start_time = time.time()
    while True:
        if not any(f.endswith(".crdownload") for f in os.listdir(DOWNLOAD_DIR)):
            return True
        if time.time() - start_time > timeout:
            logging.fatal("Timeout waiting for downloads to complete. Exiting script.")
            raise RuntimeError("Timeout waiting for downloads.") 
        time.sleep(1)

def rename_and_move_downloaded_file(place_name, panel_index):
    """Renames the most recently downloaded file and moves it to the correct subfolder."""
    try:
        time.sleep(1) # Give a moment for the file system to update

        # Get the destination folder name from the map
        folder_name = PANEL_FOLDER_MAP.get(panel_index)
        if not folder_name:
            logging.warning(f"No folder mapping found for panel index {panel_index}. Skipping file move for {place_name}.")
            return

        # Find the latest downloaded file in the main DOWNLOAD_DIR
        list_of_files = glob.glob(os.path.join(DOWNLOAD_DIR, '*.xlsx'))
        if not list_of_files:
            logging.warning(f"No XLSX file found to rename for {place_name} (Panel {panel_index}).")
            return
            
        latest_file = max(list_of_files, key=os.path.getctime)
        
        # Construct the new filename
        new_filename = f"{place_name.replace(' ', '_')}_Panel_{panel_index}_{os.path.basename(latest_file)}"
        
        # Construct the destination path including the subfolder
        destination_dir = os.path.join(DOWNLOAD_DIR, folder_name)
        Path(destination_dir).mkdir(parents=True, exist_ok=True) # Ensure subfolder exists
        new_filepath = os.path.join(destination_dir, new_filename)

        # Move and rename the file
        os.rename(latest_file, new_filepath)
        logging.info(f"Moved and renamed file from '{os.path.basename(latest_file)}' to '{new_filepath}'")
    except Exception as e:
        logging.fatal(f"Failed to rename and move file for {place_name} (Panel {panel_index}): {e}. Exiting script.")
        raise RuntimeError(f"File operation failed: {e}")


def download_panel(driver, panel_index, place_name):
    """
    Locates a panel, opens the dropdown, clicks the download button,
    and then calls the rename and move function.
    """
    try:
        panel_id = f"pnadct-q{panel_index}"
        panel_div = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, panel_id))
        )

        dropdown_button = WebDriverWait(panel_div, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.janela-btn.dropdown span.dropdown-toggle"))
        )
        dropdown_button.click()

        export_option = WebDriverWait(panel_div, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.dropdown-menu li[data-item='0'] a"))
        )
        export_option.click()
        
        logging.info(f"  ✓ Downloading XLSX from panel {panel_id} for {place_name}")
        time.sleep(2) # Give a moment for the download to initiate
        rename_and_move_downloaded_file(place_name, panel_index)

    except (TimeoutException, NoSuchElementException) as e:
        logging.fatal(f"  ✖ Selenium element error during download from {panel_id} for {place_name}: {e}. Exiting script.")
        raise RuntimeError(f"Selenium element error: {e}") # Added raise
    except Exception as e:
        logging.fatal(f"  ✖ Critical download failure from {panel_id} for {place_name}: {e}. Exiting script.")
        raise RuntimeError(f"Critical download failure: {e}") # Added raise


def get_url_slug(place_name):
    """
    Generates a URL slug from the place name, matching the website's pattern.
    """
    slug = place_name.lower().replace(' ', '-')
    slug = re.sub(r'[áãâ]', 'a', slug)
    slug = re.sub(r'é', 'e', slug)
    slug = re.sub(r'[íî]', 'i', slug)
    slug = re.sub(r'[óôõ]', 'o', slug)
    slug = re.sub(r'ú', 'u', slug)
    slug = re.sub(r'ç', 'c', slug)
    return slug

def main(argv):
    """Main function to orchestrate the scraping and downloading."""
    del argv # Unused.
    logging.info("Script started.")
    
    # Create the main download directory and the four subfolders
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    for folder_name in PANEL_FOLDER_MAP.values():
        os.makedirs(os.path.join(DOWNLOAD_DIR, folder_name), exist_ok=True)
    
    driver = setup_driver()
    try:
        driver.get(BASE_URL)
        logging.info(f"Navigated to base URL: {BASE_URL}")

        select_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "codigolist-pnadct"))
        )
        select = Select(select_element)
        options_text = [option.text.strip() for option in select.options]

        logging.info("\n▶ Processing: Brasil")
        try:
            for panel_index in range(1, 5):
                download_panel(driver, panel_index, 'Brasil')
            wait_for_downloads()
        except (TimeoutException, NoSuchElementException) as e:
            logging.fatal(f"  ✖ Selenium element error processing 'Brasil' page. Exiting. Error: {e}")
            raise RuntimeError(f"Selenium error for 'Brasil' page: {e}") 
        except Exception as e:
            logging.fatal(f"  ✖ Critical failure processing 'Brasil' page. Exiting. Error: {e}")
            raise RuntimeError(f"Critical processing failure for 'Brasil' page: {e}") 

        for place_name in options_text:
            if not place_name:
                continue
            
            logging.info(f"\n▶ Processing: {place_name}")

            try:
                select_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.ID, "codigolist-pnadct"))
                )
                select = Select(select_element)

                select.select_by_visible_text(place_name)
                
                place_slug = get_url_slug(place_name)
                WebDriverWait(driver, 20).until(EC.url_contains(place_slug))
                time.sleep(5) # Give page time to load after selection

                for panel_index in range(1, 5):
                    download_panel(driver, panel_index, place_name)
                
                wait_for_downloads()

            except (TimeoutException, NoSuchElementException) as e:
                logging.fatal(f"  ✖ Selenium element error selecting or downloading for {place_name}. Exiting. Error: {e}")
                raise RuntimeError(f"Selenium error for {place_name}: {e}") 
            except Exception as e:
                logging.fatal(f"  ✖ Critical failure selecting or downloading for {place_name}. Exiting. Error: {e}")
                raise RuntimeError(f"Critical processing failure for {place_name}: {e}") 

    finally:
        driver.quit()
        logging.info("WebDriver closed.")
        logging.info("Script finished.")

if __name__ == "__main__":
    flags.FLAGS.log_dir = SCRIPT_DIR
    app.run(main)
