# Copyright 2025 Google LLC
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
"""A script to download EPH Tracking data."""

import os
import csv
from bs4 import BeautifulSoup
import pandas as pd
from absl import app, logging, flags
from datetime import datetime
import time
from retry import retry
import re
import json
import sys
from google.cloud import storage
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions

_CONFIG = None
with open("./config.json", 'r', encoding='utf-8') as config_f:
    _CONFIG = json.load(config_f)

flags.DEFINE_string(
    'config_file_path',
    'gs://unresolved_mcf/cdc/environmental_public_health/heat_stress/latest/configs.py',
    'Config file path')

current_year = datetime.now().year


@retry(tries=3, delay=1000, backoff=2)
def download_dynamic_page(url, filename):
    """
  Downloads HTML pages.
  Args:
    url: The url for download the html files.
    filename: The filename for saving the downloaded file.
  """
    chrome_options = ChromeOptions()
    prefs = {"safebrowsing.enabled": True}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")

    #Attaching the chromelog in the main log file using sys.stderr
    service = ChromeService(log_path=sys.stderr)

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get(url)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, _CONFIG.get('PAGE_START'))))

        time.sleep(5)

        no_data_element = driver.find_elements(By.XPATH,
                                               _CONFIG.get('NO_DATA_ELEMENT'))

        if no_data_element:
            logging.info(f"No data found for url: {url}")
            return False

        html_content = driver.page_source

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return True

    except Exception as e:
        logging.error(
            f"Error found while downloading the data for the url {url}")

    finally:
        if driver is not None:
            driver.quit()
            logging.info("Web driver closed.")


def table_to_csv(html, csv_path: str):
    """
    Converts the HTML page to a CSV file.
    Args:
    csv_path (str): path of csv files to be saved
    """
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.select_one("table")
    headers = [th.text for th in table.select("tr th")]

    with open(csv_path, "w", encoding='utf-8') as csv_f:
        writer = csv.writer(csv_f)
        writer.writerow(headers)
        writer.writerows([[td.text
                           for td in row.find_all("td")]
                          for row in table.select("tr + tr")])


def combine_csv_files(directory, category_string):
    """
    Combines multiple CSV files within a directory into a single CSV file 
    based on a string present in their filenames.

    Args:
        directory: The path to the directory containing the CSV files.
        category_string: A string that must be present in the filenames.
    """
    dataframes_to_combine = []

    pattern = re.compile(rf"^{re.escape(category_string)}(_\d{{4}})?\.csv$")

    logging.info(
        f"Looking for CSV files matching category '{category_string}' pattern in '{directory}'..."
    )
    logging.debug(f"Matching pattern used: {pattern.pattern}")

    for filename in os.listdir(directory):
        if pattern.match(filename):
            filepath = os.path.join(directory, filename)
            try:
                df = pd.read_csv(filepath)
                dataframes_to_combine.append(df)
                logging.info(f"  - Added '{filename}' for combining.")
            except Exception as e:
                logging.error(f"Error reading CSV file '{filename}': {e}")

    if dataframes_to_combine:
        merged_df = pd.concat(dataframes_to_combine, ignore_index=True)

        output_dir = _CONFIG.get('COMBINED_INPUT_CSV_FILE')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"Created output directory: {output_dir}")

        output_file = os.path.join(output_dir, category_string + '.csv')
        merged_df.to_csv(output_file, index=False)
        logging.info(
            f"Successfully merged CSVs for category '{category_string}' to '{output_file}'. Total files combined: {len(dataframes_to_combine)}"
        )
    else:
        logging.warning(
            f"No CSV files found matching category '{category_string}' in '{directory}' to combine."
        )


def download_all_data(url, filename):
    try:
        # All categories of source data originate from the year 2000.
        for year in range(2000, current_year + 1):
            base_url = url.format(year)
            file_name = filename.format(year)
            logging.info(f"Base url: {base_url}")
            logging.info(f"File name: {file_name}")
            download_dynamic_page(base_url, file_name)
    except Exception as e:
        logging.error(f"Download Error for the url {url}: {e}")


def convert_html_to_csv():
    try:
        for file_name in os.listdir(_CONFIG.get('INPUT_HTML_FILES')):
            if file_name.endswith('.html'):  # If file is a html file
                file_path = os.path.join(_CONFIG.get('INPUT_HTML_FILES'),
                                         file_name)
                with open(file_path, 'r', encoding='utf-8') as f:
                    cleaned_csv_path = os.path.join(
                        _CONFIG.get('INPUT_CSV_FILES'), file_name[:-5] + '.csv')
                    table_to_csv(f.read(), cleaned_csv_path)
    except Exception as e:
        logging.error(
            f"Error occured while converting the html file {file_name} to csv file: {e}"
        )


def reads_config_file():
    _FLAGS = flags.FLAGS
    config_file_path = _FLAGS.config_file_path
    storage_client = storage.Client()
    bucket_name = config_file_path.split('/')[2]
    bucket = storage_client.bucket(bucket_name)
    blob_name = '/'.join(config_file_path.split('/')[3:])
    blob = bucket.blob(blob_name)
    file_contents = blob.download_as_text()
    local_vars = {}
    exec(file_contents, {}, local_vars)
    return local_vars


def main(_):
    paths = [
        _CONFIG.get('COMBINED_INPUT_CSV_FILE'),
        _CONFIG.get('INPUT_HTML_FILES'),
        _CONFIG.get('INPUT_CSV_FILES')
    ]
    for path in paths:
        try:
            os.makedirs(path)
        except FileExistsError:
            pass  # Directory already exists

    configs = reads_config_file()
    URL_LIST = configs['URLS_CONFIG']

    for urls in URL_LIST:
        url = urls["url_template"]
        file_name = urls["filename"]
        string_to_match = urls["STRING_TO_MATCH"]
        try:
            download_all_data(url, file_name)
            convert_html_to_csv()
            combine_csv_files(_CONFIG.get('INPUT_CSV_FILES'), string_to_match)
        except Exception as e:
            logging.fatal(
                f"Fatal error: Context: Url: {url}; Filename: {file_name}; Exception: {e}"
            )


if __name__ == "__main__":
    app.run(main)
