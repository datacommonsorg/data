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
import time
import zipfile

from absl import app
from absl import logging
import pandas as pd
from retry import retry
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config


@retry(tries=3, delay=10, backoff=2)
def download_worldbank(url, download_dir):
    """Downloads data from the World Bank Databank URL by using Selenium.

    Args:
        url (str): The URL of the World Bank Databank page.
        download_dir (str): The directory where the downloaded file will be saved.
    """
    if not os.path.exists(download_dir):
        os.makedirs(download_dir, exist_ok=True)
        logging.info(f"Created download directory: {download_dir}")

    # Clear any stale partial, zip, or extracted CSV files before starting attempt
    for filename in os.listdir(download_dir):
        if filename.endswith((".crdownload", ".tmp", ".zip", ".csv")):
            os.remove(os.path.join(download_dir, filename))

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
        "safebrowsing.enabled": True,
    }

    chrome_options.add_experimental_option("prefs", prefs)
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)
        logging.info(f"Navigating to URL: {url}")
        driver.get(url)

        subnational = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="SubNAtionalButtonGrp"]/div/label[3]')
            )
        )
        subnational.click()
        country_xpath = (
            '//*[@id="newSelection_SPOP_Country_Dim"]'
            "/div/div/div/div/div[1]/div[3]/div[1]/div[1]/div/a[1]"
        )
        country = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, country_xpath))
        )
        country.click()
        time.sleep(10)
        all_tab = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="defaultSubnationalTab"]')
            )
        )
        all_tab.click()
        country.click()
        series = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="panel_SPOP_Series_Dim"]/div[1]/h4/a')
            )
        )
        series.click()
        pop_xpath = (
            '//input[@id="chk[SPOP_Series_Dim].[List].&[SP.POP.TOTL]"]'
        )
        population_chkbox = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, pop_xpath))
        )
        population_chkbox.click()
        time_selection = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="panel_SPOP_Time_Dim"]/div[1]/h4/a')
            )
        )
        time_selection.click()
        years_xpath = (
            '//*[@id="rowTimeDim"]/div/div/div[2]/div[3]/div[1]/div[1]/div/a[1]'
        )
        years = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, years_xpath))
        )
        driver.execute_script("arguments[0].click();", years)
        apply_changes = WebDriverWait(driver, 25).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="applyChangesNoPreview"]')
            )
        )
        driver.execute_script("arguments[0].click();", apply_changes)
        download_options = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//a[@title="Download options"]')
            )
        )
        download_options.click()
        csv = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//a[@title="Download CSV Format"]')
            )
        )
        csv.click()

        download_timeout = 90
        poll_interval = 2
        elapsed = 0
        downloaded = False
        while elapsed < download_timeout:
            time.sleep(poll_interval)
            elapsed += poll_interval
            files = os.listdir(download_dir)
            zip_files = [
                f
                for f in files
                if f.endswith(".zip")
                and os.path.getsize(os.path.join(download_dir, f)) > 0
            ]
            in_progress = [
                f
                for f in files
                if f.endswith(".crdownload") or f.endswith(".tmp")
            ]
            if zip_files and not in_progress:
                downloaded = True
                break

        if not downloaded:
            raise RuntimeError(
                f"Timed out after {download_timeout}s waiting for .zip "
                f"download in '{download_dir}'."
            )
        logging.info(
            f"File was Successfully downloaded into the directory '{download_dir}'."
        )

    except Exception as e:
        logging.error(f"An error occurred while downloading the file: {e}")
        raise RuntimeError("Failed to download the file") from e
    finally:
        if driver is not None:
            logging.info("Closing WebDriver.")
            try:
                driver.quit()
            except Exception as quit_err:
                logging.warning(f"Error while closing WebDriver: {quit_err}")


def unzip_inputfile(inputdir):
    try:
        logging.info(f"Unzip the files from the directory {inputdir}.")
        for filename in sorted(os.listdir(inputdir)):
            if filename.endswith(".csv"):
                os.remove(os.path.join(inputdir, filename))

        zip_found = False
        for filename in sorted(os.listdir(inputdir)):
            if str(filename).endswith(".zip"):
                zip_found = True
                zip_path = os.path.join(inputdir, filename)
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(inputdir)
        if not zip_found:
            raise FileNotFoundError(f"No .zip file found in {inputdir}")

        data_found = False
        for filename in sorted(os.listdir(inputdir)):
            if "_Data" in filename and filename.endswith(".csv"):
                src = os.path.join(inputdir, filename)
                dst = os.path.join(inputdir, "wb_subnational_input.csv")
                os.replace(src, dst)
                data_found = True
            elif "Metadata" in filename and filename.endswith(".csv"):
                os.remove(os.path.join(inputdir, filename))
        if not data_found:
            raise FileNotFoundError(
                f"No *_Data.csv file found after extracting zip in {inputdir}"
            )

    except Exception as e:
        logging.error(f"An error occurred while unzipping the file: {e}")
        raise RuntimeError("Failed to unzip the file") from e


def preprocess(inputdir):
    try:
        csv_path = os.path.join(inputdir, "wb_subnational_input.csv")
        df = pd.read_csv(csv_path, encoding="latin1")
        df.columns = df.columns.str.strip()
        df["Country Name"] = (
            df["Country Name"].str.replace(",", "-").str.strip()
        )
        df.to_csv(csv_path, index=False, encoding="utf-8")
        logging.info(
            f"Preprocessed {len(df)} rows into '{csv_path}'."
        )
    except Exception as e:
        logging.error(f"An error occurred while preprocessing the file: {e}")
        raise RuntimeError("Failed to process user data") from e


def main(_):
    worldbank_url = config.world_bank_url
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "input_files")

    download_worldbank(worldbank_url, input_dir)
    unzip_inputfile(input_dir)
    preprocess(input_dir)


if __name__ == "__main__":
    app.run(main)
