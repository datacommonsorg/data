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

import os
import time, config, zipfile
from absl import logging, app
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from retry import retry
import pandas as pd

@retry(
    tries=3,
    delay=1000, 
    backoff=2
)
def download_worldbank(url, download_dir):
    """
    Downloads data from the World Bank Databank URL by using Selenium.

    Args:
        url (str): The URL of the World Bank Databank page.
        download_dir (str): The directory where the downloaded file will be saved.
    """
  
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        logging.info(f"Created download directory: {download_dir}")

    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--no-sandbox") 
    chrome_options.add_argument("--disable-dev-shm-usage") 
    chrome_options.add_argument("--window-size=1920,1080") 
    chrome_options.add_argument("--disable-gpu")
    
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
    }

    chrome_options.add_experimental_option("prefs", prefs)
    service = ChromeService(ChromeDriverManager().install())

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info(f"Navigating to URL: {url}")
        driver.get(url)

        subnational = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="SubNAtionalButtonGrp"]/div/label[3]'))
        )
        subnational.click()
        country = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="newSelection_SPOP_Country_Dim"]/div/div/div/div/div[1]/div[3]/div[1]/div[1]/div/a[1]'))
        )
        country.click()
        time.sleep(3)
        all = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="defaultSubnationalTab"]'))
        )
        all.click()
        country.click()
        time.sleep(3)
        series = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="panel_SPOP_Series_Dim"]/div[1]/h4/a'))
        )
        series.click()
        population_chkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@id="chk[SPOP_Series_Dim].[List].&[SP.POP.TOTL]"]'))
        )
        population_chkbox.click()
        time.sleep(3)
        time_selection = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="panel_SPOP_Time_Dim"]/div[1]/h4/a'))
        )
        time_selection.click()
        years = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="rowTimeDim"]/div/div/div[2]/div[3]/div[1]/div[1]/div/a[1]'))
        )
        years.click()
        apply_changes = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="applyChangesNoPreview"]'))
        )
        apply_changes.click()
        time.sleep(5)
        download_options = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//a[@title="Download options"]'))
        )
        download_options.click()
        time.sleep(5)
        csv = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//a[@title="Download CSV Format"]'))
        )
        csv.click()
        time.sleep(30)
        logging.info(f"File was Successfully downloaded into the directory '{download_dir}'.")

    except Exception as e:
        logging.fatal(f"An error occurred while downloading the file: {e}")
    finally:
        logging.info("Closing WebDriver.")
        driver.quit()

def unzip_inputfile(inputdir):
    try:
        logging.info(f"Unzip the files from the directory {inputdir}.")
        for filename in os.listdir(inputdir):
            if str(filename).endswith(".zip"):
                with zipfile.ZipFile(os.path.join(inputdir, filename), 'r') as zip_ref:
                    zip_ref.extractall(inputdir)
        
        for filename in os.listdir(inputdir):
            if "_Data" in filename and str(filename).endswith(".csv"):
                os.rename(os.path.join(inputdir, filename), os.path.join(inputdir, "subnational_input.csv"))

    except Exception as e:
        logging.fatal(f"An error occurred while unzipping the file: {e}")

def preprocess(inputdir):
    try:
        df = pd.read_csv(os.path.join(inputdir, "subnational_input.csv"), encoding='latin1')
        df['Country Name'] = df["Country Name"].str.replace(",","-")
        df.to_csv(os.path.join(inputdir, "subnational_input.csv"), index=False, encoding='utf-8')
    except Exception as e:
        logging.fatal(f"An error occurred while preprocessing the file: {e}")
    
def main(_):
    worldbank_url = config.world_bank_url
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "input_files")
    
    download_worldbank(worldbank_url, input_dir)
    unzip_inputfile(input_dir)
    preprocess(input_dir)

if __name__ == "__main__":
   app.run(main)
