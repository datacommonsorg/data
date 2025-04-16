# Copyright 2024 Google LLC
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

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, logging, os, shutil
import pandas as pd
from pathlib import Path
import config

# logging configuration
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  
handler = logging.StreamHandler()  
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def download_file(url, input_file_path):
    """
    Downloads a file from a given URL using Selenium.

    Args:
        url: The URL of the file to download.
        input_file_path: The directory where the file should be downloaded.

    """

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)

    logger.info(driver)
    driver.get(url)
    try:
        excel_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Download Excel')]"))  
        )
        excel_link.click()
        logger.info("Excel link clicked.")
        time.sleep(5)  
        download_dir = os.path.expanduser("~/Downloads")
        latest_file = None
        latest_modified_time = 0
        for filename in os.listdir(download_dir):
            if filename.endswith((".xlsx", ".xls")):  
                file_path = os.path.join(download_dir, filename)
                modified_time = os.path.getmtime(file_path) 
                if modified_time > latest_modified_time:
                    latest_modified_time = modified_time
                    latest_file = file_path
        if latest_file:
            logger.info(f"Latest Excel file found: {latest_file}")
            destination_path = os.path.join(input_file_path, os.path.basename(latest_file))

            if not os.path.exists(input_file_path):
                os.makedirs(input_file_path)
                logger.info(f"Created directory: {input_file_path}")
            shutil.move(latest_file, destination_path)
            logger.info(f"Excel file moved to: {destination_path}")

        else:
            logger.info("No Excel files found in the Downloads directory.")
    except Exception as e:
        logger.exception(f"Error clicking Excel link or verifying download: {e}")

if __name__ == "__main__":
    url = config.url
    inputdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_files")
    Path(inputdir).mkdir(parents=True, exist_ok=True)
    download_file(url, inputdir)