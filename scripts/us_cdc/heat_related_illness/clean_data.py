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
"""A script to download EPH Tracking data."""

import os
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

input_html_files = "./source_data/html_files/"
input_csv_files = "./source_data/csv_files"
combined_input_csv = "./input_files/"


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
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//*[@id='page-start']")))
    time.sleep(5)
    no_data_element = driver.find_elements(
        By.XPATH, "//h2[text()='Data does not exist for the above criteria.']")
    if no_data_element:
        logging.info(f"No data found for {url}")
        return
    html_content = driver.page_source
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    driver.quit()
    return True


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


def combine_csvs_by_string(directory, string_list):
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
            output_file = os.path.join(combined_input_csv, string + '.csv')
            merged_df.to_csv(output_file, index=False)
            logging.info(
                f"Successfully merged CSVs for '{string}' to {output_file}")


def main(argv):
    paths = [combined_input_csv, input_html_files, input_csv_files]
    for path in paths:
        try:
            os.makedirs(path)
        except FileExistsError:
            pass  # Directory already exists

    urls_list = [
        "https://ephtracking.cdc.gov/qr/370/1/ALL/ALL/1/{year}/0?apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
        "https://ephtracking.cdc.gov/qr/431/1/ALL/ALL/1/{year}/0?apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
        "https://ephtracking.cdc.gov/qr/431/3/ALL/ALL/1/{year}/0?AgeBandId=1,2,3,4,5&apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
        "https://ephtracking.cdc.gov/qr/431/4/ALL/ALL/1/{year}/0?GenderId=1,2&apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
        "https://ephtracking.cdc.gov/qr/431/37/ALL/ALL/1/{year}/0?AgeBandId=1,2,3,4,5&GenderId=1,2&apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
        "https://ephtracking.cdc.gov/qr/438/1/ALL/ALL/1/{year}/0?apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
        "https://ephtracking.cdc.gov/qr/438/3/ALL/ALL/1/{year}/0?AgeBandId=1,2,3,4,5&apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
        "https://ephtracking.cdc.gov/qr/438/4/ALL/ALL/1/{year}/0?GenderId=1,2&apiToken=637DD2EF-507F-4938-8380-54A179C3132A",
        "https://ephtracking.cdc.gov/qr/438/37/ALL/ALL/1/{year}/0?AgeBandId=1,2,3,4,5&GenderId=1,2&apiToken=637DD2EF-507F-4938-8380-54A179C3132A"
    ]

    current_year = datetime.now().year
    try:
        for url in urls_list:
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

            for file_name in os.listdir(input_html_files):
                if file_name.endswith('.html'):  # If file is a html file
                    file_path = os.path.join(input_html_files, file_name)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cleaned_csv_path = os.path.join(input_csv_files,
                                                        file_name[:-5] + '.csv')
                        table_to_csv(f.read(), cleaned_csv_path)

            string_to_match = [
                "deaths", "hospitalizations", "hospitalization_age",
                "hospitalizatin_gender", "hospitlizations_age_gender",
                "edVisits", "edVisit_age", "edVists_gender",
                "edVsits_age_gender"
            ]

            combine_csvs_by_string(input_csv_files, string_to_match)

    except Exception as e:
        logging.fatal(f"Download Error:{e}")


if __name__ == "__main__":
    app.run(main)
