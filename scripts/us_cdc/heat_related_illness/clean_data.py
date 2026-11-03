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
import shutil
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG = None
with open(os.path.join(_SCRIPT_DIR, "config.json"), 'r',
          encoding='utf-8') as config_f:
    _CONFIG = json.load(config_f)


def _resolve_script_path(path: str) -> str:
    if not path or os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(_SCRIPT_DIR, path))


for _path_key in ('INPUT_HTML_FILES', 'INPUT_CSV_FILES',
                  'COMBINED_INPUT_CSV_FILE', 'OUTPUT_PATH'):
    if _path_key in _CONFIG:
        _CONFIG[_path_key] = _resolve_script_path(_CONFIG[_path_key])


def _sanitize_url(url: str) -> str:
    """Redacts sensitive token query parameters from URLs before logging."""
    return re.sub(r'(?i)(apiToken=)[^&\s]+', r'\1REDACTED', str(url))


flags.DEFINE_string(
    'config_file_path',
    'gs://unresolved_mcf/cdc/environmental_public_health/heat_stress/latest/configs.py',
    'Config file path')

current_year = datetime.now().year

# Minimum published historical end year per category (starting from 2000)
MIN_PUBLISHED_YEAR_BY_CATEGORY = {
    "deaths": 2022,
}
DEFAULT_MIN_PUBLISHED_YEAR = 2023


@retry(exceptions=(WebDriverException, RuntimeError, ValueError, OSError),
       tries=6,
       delay=10,
       backoff=2)
def download_dynamic_page(url, filename, require_data=False):
    """
  Downloads HTML pages.
  Args:
    url: The url for download the html files.
    filename: The filename for saving the downloaded file.
    require_data: If True, raises an error when NO_DATA_ELEMENT is returned
      so transient backend failures on known historical years are retried.
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
    driver = None
    safe_url = _sanitize_url(url)

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get(url)

        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located(
                (By.XPATH, _CONFIG.get('PAGE_START'))))

        WebDriverWait(driver, 60).until(
            lambda d: d.find_elements(By.XPATH, _CONFIG.get('NO_DATA_ELEMENT'))
            or d.find_elements(By.CSS_SELECTOR, "table tr td"))

        time.sleep(5)

        no_data_element = driver.find_elements(By.XPATH,
                                               _CONFIG.get('NO_DATA_ELEMENT'))

        if no_data_element:
            if require_data:
                raise RuntimeError(
                    f"Unexpected 'No data found' on required historical url: {safe_url}"
                )
            logging.info(f"No data found for url: {safe_url}")
            return False

        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.select_one("table")
        data_rows = table.select("tr + tr") if table is not None else []
        if not data_rows:
            raise ValueError(
                f"Populated data table rows not found for url: {safe_url}")

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logging.info(
            f"Successfully downloaded {len(data_rows)} data rows from {safe_url} to {filename}"
        )
        return True

    except Exception as e:
        logging.error(
            f"Error found while downloading the data for the url {safe_url}: {_sanitize_url(str(e))}"
        )
        raise

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
    if table is None:
        raise ValueError(f"No <table> element found when converting {csv_path}")
    data_rows = table.select("tr + tr")
    if not data_rows:
        raise ValueError(
            f"No data rows found in <table> when converting {csv_path}")
    headers = [th.text for th in table.select("tr th")]

    with open(csv_path, "w", encoding='utf-8') as csv_f:
        writer = csv.writer(csv_f)
        writer.writerow(headers)
        writer.writerows(
            [[td.text for td in row.find_all("td")] for row in data_rows])


def combine_csv_files(directory, category_string):
    """
    Combines multiple CSV files within a directory into a single CSV file 
    based on a string present in their filenames.

    Args:
        directory: The path to the directory containing the CSV files.
        category_string: A string that must be present in the filenames.
    """
    dataframes_to_combine = []
    matched_filenames = set()

    pattern = re.compile(rf"^{re.escape(category_string)}(_\d{{4}})?\.csv$")

    logging.info(
        f"Looking for CSV files matching category '{category_string}' pattern in '{directory}'..."
    )
    logging.debug(f"Matching pattern used: {pattern.pattern}")

    for filename in sorted(os.listdir(directory)):
        if pattern.match(filename):
            filepath = os.path.join(directory, filename)
            try:
                df = pd.read_csv(filepath)
                if df.empty:
                    raise ValueError(f"CSV file '{filename}' is empty.")
                dataframes_to_combine.append(df)
                matched_filenames.add(filename)
                logging.info(f"  - Added '{filename}' for combining.")
            except Exception as e:
                logging.error(f"Error reading CSV file '{filename}': {e}")
                raise

    min_published_year = MIN_PUBLISHED_YEAR_BY_CATEGORY.get(
        category_string, DEFAULT_MIN_PUBLISHED_YEAR)
    expected_yearly_files = {
        f"{category_string}_{year}.csv"
        for year in range(2000, min_published_year + 1)
    }
    missing_yearly_files = sorted(expected_yearly_files - matched_filenames)

    if not dataframes_to_combine:
        raise RuntimeError(
            f"No CSV files found matching category '{category_string}' in '{directory}' to combine."
        )
    if missing_yearly_files:
        raise RuntimeError(
            f"Incomplete CSV files for category '{category_string}': missing "
            f"{len(missing_yearly_files)} required yearly file(s): {missing_yearly_files}."
        )

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


def download_all_data(url, filename, category_string=None):
    min_published_year = MIN_PUBLISHED_YEAR_BY_CATEGORY.get(
        category_string, DEFAULT_MIN_PUBLISHED_YEAR)
    resolved_filename = _resolve_script_path(filename)
    try:
        # All categories of source data originate from the year 2000.
        for year in range(2000, current_year + 1):
            base_url = url.format(year)
            file_name = resolved_filename.format(year)
            logging.info(f"Base url: {_sanitize_url(base_url)}")
            logging.info(f"File name: {file_name}")
            download_dynamic_page(base_url,
                                  file_name,
                                  require_data=(year <= min_published_year))
    except Exception as e:
        logging.error(
            f"Download Error for the url {_sanitize_url(url)}: {_sanitize_url(str(e))}"
        )
        raise


def convert_html_to_csv(category_string=None):
    html_pattern = (
        re.compile(rf"^{re.escape(category_string)}(_\d{{4}})?\.html$")
        if category_string else None)
    for file_name in sorted(os.listdir(_CONFIG.get('INPUT_HTML_FILES'))):
        if file_name.endswith('.html') and (html_pattern is None or
                                            html_pattern.match(file_name)):
            try:
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
                raise


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
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)

    configs = reads_config_file()
    URL_LIST = configs['URLS_CONFIG']

    for urls in URL_LIST:
        url = urls["url_template"]
        file_name = urls["filename"]
        string_to_match = urls["STRING_TO_MATCH"]
        try:
            download_all_data(url, file_name, string_to_match)
            convert_html_to_csv(string_to_match)
            combine_csv_files(_CONFIG.get('INPUT_CSV_FILES'), string_to_match)
        except Exception as e:
            logging.fatal(
                f"Fatal error: Context: Url: {_sanitize_url(url)}; Filename: {file_name}; Exception: {_sanitize_url(str(e))}"
            )


if __name__ == "__main__":
    app.run(main)
