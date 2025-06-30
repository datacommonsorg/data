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

import os, configs
import csv
from bs4 import BeautifulSoup
import pandas as pd
from absl import app, logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions

current_year = datetime.now().year


def download_dynamic_page(url, filename):
    """
  Downloads HTML pages.
  Args:
    url: The url for download the html files.
    filename: The filename for saving the downloaded file.
  """
    chrome_options = ChromeOptions()

    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")

    service = ChromeService(ChromeDriverManager().install())

    driver_log_path = os.path.join(os.getcwd(), "chromedriver.log")

    service = ChromeService(ChromeDriverManager().install(),
                            log_path=driver_log_path)

    logging.info(
        f"ChromeDriver internal logs will be written to: {driver_log_path}")

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get(url)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='page-start']")))

        time.sleep(5)

        no_data_element = driver.find_elements(
            By.XPATH,
            "//h2[text()='Data does not exist for the above criteria.']")

        if no_data_element:
            logging.info(f"No data found for url: {url}")
            return False

        html_content = driver.page_source

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return True

    except Exception as e:
        logging.fatal(
            f"Error found while downloading the data for the url {url}")

    finally:
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


def combine_csv_files(directory, string_list):
    """
  Combines multiple CSV files within a directory into a single CSV file 
  based on a string present in their filenames.

  Args:
    directory: The path to the directory containing the CSV files.
    string_list: The list of strings that must be present in the filenames.
  """
    dataframes = {}  # Dictionary to store DataFrames for each string

    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            for string in string_list:
                if string in filename:
                    filepath = os.path.join(directory, filename)
                    try:
                        df = pd.read_csv(filepath)
                        if string not in dataframes:
                            dataframes[string] = []
                        dataframes[string].append(df)
                    except Exception as e:
                        logging.info(f"Error reading {filename}: {e}")
                    break  # Move to the next filename after a match

    for string, df_list in dataframes.items():
        if df_list:
            merged_df = pd.concat(df_list, ignore_index=True)
            output_file = os.path.join(configs.COMBINED_INPUT_CSV_FILE,
                                       string + '.csv')
            merged_df.to_csv(output_file, index=False)
            logging.info(
                f"Successfully merged CSVs for '{string}' to {output_file}")


def download_all_data(url):
    try:
        for year in range(2000, current_year + 1):
            base_url = url.format(year=year)
            if "370" in url:
                filename = f"./source_data/html_files/deaths_{year}.html"
            elif "431/1" in url:
                filename = f"./source_data/html_files/hospitalizations_{year}.html"
            elif "431/3/" in url:
                filename = f"./source_data/html_files/hospitalization_age_{year}.html"
            elif "431/4" in url:
                filename = f"./source_data/html_files/hospitalizatin_gender_{year}.html"
            elif "431/37" in url:
                filename = f"./source_data/html_files/hospitlizations_age_gender_{year}.html"
            elif "438/1" in url:
                filename = f"./source_data/html_files/edVisits_{year}.html"
            elif "438/3/" in url:
                filename = f"./source_data/html_files/edVisit_age_{year}.html"
            elif "438/4" in url:
                filename = f"./source_data/html_files/edVists_gender_{year}.html"
            elif "438/37" in url:
                filename = f"./source_data/html_files/edVsits_age_gender_{year}.html"
            else:
                logging.info("No Urls found!")

            download_dynamic_page(base_url, filename)
    except Exception as e:
        logging.fatal(f"Download Error for the url {url}: {e}")


def convert_html_to_csv():
    try:
        for file_name in os.listdir(configs.INPUT_HTML_FILES):
            if file_name.endswith('.html'):  # If file is a html file
                file_path = os.path.join(configs.INPUT_HTML_FILES, file_name)
                with open(file_path, 'r', encoding='utf-8') as f:
                    cleaned_csv_path = os.path.join(configs.INPUT_CSV_FILES,
                                                    file_name[:-5] + '.csv')
                    table_to_csv(f.read(), cleaned_csv_path)
    except Exception as e:
        logging.fatal(
            f"Error occured while converting the html file {file_name} to csv file: {e}"
        )


def main(_):
    paths = [
        configs.COMBINED_INPUT_CSV_FILE, configs.INPUT_HTML_FILES,
        configs.INPUT_CSV_FILES
    ]
    for path in paths:
        try:
            os.makedirs(path)
        except FileExistsError:
            pass  # Directory already exists

    URL_LIST = configs.URLS_CONFIG

    for url in URL_LIST:
        try:
            download_all_data(url)
            convert_html_to_csv()
            combine_csv_files(configs.INPUT_CSV_FILES, configs.STRING_TO_MATCH)

        except Exception as e:
            logging.fatal(f"Script terminated due to the exception: {e}")


if __name__ == "__main__":
    app.run(main)
