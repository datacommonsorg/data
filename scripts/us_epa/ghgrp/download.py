# Copyright 2021 Google LLC
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
"""Module to download and do light processing on import data."""
# TODO(beets): Add tests

import io
from absl import logging
import os
import ssl
import re
import requests
from datetime import datetime
import pandas as pd
import zipfile
from retry import retry

logging.set_verbosity(logging.INFO)

# URL templates
download_url = 'https://www.epa.gov/system/files/other-files/{year}-10/{year_minus_1}_data_summary_spreadsheets.zip'
crosswalk_url = 'https://www.epa.gov/system/files/documents/{yr}-04/ghgrp_oris_power_plant_crosswalk_12_13_21.xlsx'

# Constants
YEAR_DATA_FILENAME = 'ghgp_data_{year}.xlsx'
HEADER_ROW = 3
CROSSWALK_COLS_TO_KEEP = [
    'GHGRP Facility ID', 'ORIS CODE', 'ORIS CODE 2', 'ORIS CODE 3',
    'ORIS CODE 4', 'ORIS CODE 5'
]
GHGRP_ID_COL = 'Facility Id'

_DIRECT_EMITTERS_SHEET = r"^Direct.*Emitters$"

SHEET_NAMES_TO_CSV_FILENAMES = {
    'Onshore Oil & Gas Prod.': 'oil_and_gas.csv',
    'Gathering & Boosting': 'gathering_and_boosting.csv',
    'LDC - Direct Emissions': 'local_distribution.csv',
    'SF6 from Elec. Equip.': 'elec_equip.csv',
}


def get_csv_filename(sheet_name):
    """
    Determines the CSV filename for a given sheet name.
    Sheets matching the DIRECT_EMITTERS_PATTERN are saved as 'direct_emitters.csv'.

    Args:
        sheet_name (str): Name of the Excel sheet to map to a CSV filename.

    Returns:
        str: The corresponding CSV filename or None if no match is found.
    """
    try:
        if re.match(_DIRECT_EMITTERS_SHEET, sheet_name):
            return 'direct_emitters.csv'
        return SHEET_NAMES_TO_CSV_FILENAMES.get(sheet_name)
    except Exception as e:
        logging.fatal(
            f"Error occured while mapping the sheet Direct Emitters: {e}")


class Downloader:
    """
    Handles downloading, extracting, and processing data files.
    """

    def __init__(self, save_path, url_year):
        self.years = list(range(2010, url_year - 1))
        self.current_year = None
        self.files = []  # list of (year, filename) of all extracted files
        self.save_path = save_path

        # Ensure the save directory exists
        os.makedirs(self.save_path, exist_ok=True)

    def check_url(self, url):
        """
        Checks if a given URL is accessible.

        Args:
            url (str): The URL to check.

        Returns:
            bool: True if the URL is accessible, False otherwise.
        """

        try:
            response = requests.head(url)
            response.raise_for_status()
            logging.info(f"URL is valid: {url}")
            return True
        except requests.RequestException as e:
            logging.warning(f"URL check failed: {url}. Error: {e}")
            return False

    def generate_and_validate(self, template, **kwargs):
        """
        Generates a URL using a template and validates its existence.
        Args:
            template (str): The URL template with placeholders.
            **kwargs: Key-value pairs for placeholders in the template.

        Returns:
            str: The validated URL.

        Raises:
            ValueError: If the URL is not valid.
        """
        try:
            url = template.format(**kwargs)
            if self.check_url(url):
                logging.info(f"Valid URL found: {url}")
                return url  # Return the valid URL and stop further processing
            logging.info(f"URL not valid: {url}")
            return None
        except Exception as e:
            logging.fatal(
                f"Error occured while generating and validating the url: {e}")

    @retry(tries=3, delay=2, backoff=2, exceptions=(requests.RequestException,))
    def download_data(self, year, year_minus_1):
        """
        Download a file from the specified URL with retry logic.
        Downloads and unzips Excel files from dynamically generated DOWNLOAD_URI.
        Args:
            year (int): The current year for the data.
            year_minus_1 (int): The previous year for the data.
        """
        uri = self.generate_and_validate(download_url,
                                         year=year,
                                         year_minus_1=year_minus_1)
        logging.info(f'Downloading data from {uri}')
        try:
            r = requests.get(uri)
            r.raise_for_status()  # Raise an error for unsuccessful responses
            z = zipfile.ZipFile(io.BytesIO(r.content))
            for file in z.namelist():
                # Skip directories
                if not file.endswith('/'):
                    target_path = os.path.join(self.save_path,
                                               os.path.basename(file))
                    with z.open(file) as source, open(target_path,
                                                      'wb') as target:
                        target.write(source.read())
            logging.info(f"Successfully downloaded data for year: {year}")
        except Exception as e:
            logging.fatal(f"Failed to download or extract data for {year}: {e}")

    def extract_all_years(self):
        """
        Saves relevant sheets from each year's Excel file to a CSV.
        Returns:
            list: A list of tuples containing (year, filename) for extracted files.
        """
        try:
            headers = {}
            for sheet, _ in SHEET_NAMES_TO_CSV_FILENAMES.items():
                headers[sheet] = {}
            for current_year in self.years:
                logging.info(f'Extracting data for {current_year}')
                self.current_year = current_year
                self._extract_data(headers)
            for sheet, csv_name in SHEET_NAMES_TO_CSV_FILENAMES.items():
                headers_df = pd.DataFrame.from_dict(headers[sheet],
                                                    orient='index')
                headers_df.transpose().to_csv(os.path.join(
                    self.save_path, f'cols_{csv_name}'),
                                              index=None)
            return self.files
        except Exception as e:
            logging.fatal(
                f"Error occured while extracting the years from the file: {e}")

    def save_all_crosswalks(self, filepath):
        """
        Builds individual year crosswalks, as well as a joint crosswalk for all years.
        Args:
            filepath (str): The path where the combined crosswalk CSV will be saved.

        Returns:
            pd.DataFrame: A DataFrame containing all combined crosswalks.
        """
        logging.info('Saving all ID crosswalks')
        try:
            crosswalks = []
            for current_year in self.years:
                crosswalks.append(self._gen_crosswalk())
            all_crosswalks_df = pd.concat(crosswalks, join='outer')
            all_crosswalks_df = all_crosswalks_df.sort_values(
                by=[GHGRP_ID_COL, 'FRS Id', 'ORIS CODE'])
            all_crosswalks_df = all_crosswalks_df.drop_duplicates()
            all_crosswalks_df.to_csv(filepath, header=True, index=None)
            return all_crosswalks_df
        except Exception as e:
            logging.fatal(f"Error occured while saving all cross walks: {e}")

    def _csv_path(self, csv_filename, year=None):
        """
        Generates the full path for a CSV file.

        Args:
            csv_filename (str): The base filename for the CSV.
            year (int, optional): The year associated with the file. Defaults to the current year.

        Returns:
            str: The full path to the CSV file.
        """
        if not year:
            year = self.current_year
        return os.path.join(self.save_path, f'{year}_{csv_filename}')

    def _extract_data(self, headers):
        """
        Extracts relevant sheets from an Excel file for the current year.

        Args:
            headers (dict): A dictionary to store header information for each sheet.

        """
        try:
            summary_filename = os.path.join(
                self.save_path,
                YEAR_DATA_FILENAME.format(year=self.current_year))

            xl = pd.ExcelFile(summary_filename, engine='openpyxl')
            logging.info(
                f"Available sheets in {summary_filename}: {xl.sheet_names}")
            check_list = []
            for sheet in xl.sheet_names:
                csv_filename = get_csv_filename(sheet)
                check_list.append(csv_filename)
                if not csv_filename:
                    logging.info(f'Skipping sheet: {sheet}')
                    continue
                summary_file = xl.parse(sheet, header=HEADER_ROW, dtype=str)
                csv_path = self._csv_path(csv_filename)
                summary_file.to_csv(csv_path, index=None, header=True)
                headers.setdefault(sheet,
                                   {})[self.current_year] = summary_file.columns
                self.files.append((self.current_year, csv_path))
            if "direct_emitters.csv" not in check_list:
                logging.fatal(
                    f"'direct_emitters.csv' not found in the sheets for {self.current_year}. Aborting!"
                )
        except Exception as e:
            logging.fatal(
                f"Error occured while processing the sheet names: {e}")

    def _gen_crosswalk(self):
        """
        Generates a crosswalk DataFrame for the current year.

        Returns:
            pd.DataFrame: A DataFrame containing crosswalk data for the current year.
        """
        ssl._create_default_https_context = ssl._create_unverified_context
        try:
            oris_df = pd.read_excel(self.generate_and_validate(
                crosswalk_url, yr=self.current_year),
                                    'ORIS Crosswalk',
                                    header=0,
                                    dtype=str,
                                    usecols=CROSSWALK_COLS_TO_KEEP,
                                    engine='openpyxl')
        except Exception:
            logging.warning(f"Using fallback CROSSWALK_URI for 2022")
            oris_df = pd.read_excel(self.generate_and_validate(crosswalk_url,
                                                               yr=2022),
                                    'ORIS Crosswalk',
                                    header=0,
                                    dtype=str,
                                    usecols=CROSSWALK_COLS_TO_KEEP,
                                    engine='openpyxl')

        oris_df = oris_df.rename(columns={'GHGRP Facility ID': GHGRP_ID_COL})
        all_facilities_df = pd.DataFrame()
        for sheet, csv_filename in SHEET_NAMES_TO_CSV_FILENAMES.items():
            csv_path = self._csv_path(csv_filename)
            if not os.path.exists(csv_path):
                continue
            df = pd.read_csv(csv_path,
                             usecols=[GHGRP_ID_COL, 'FRS Id'],
                             dtype=str)
            all_facilities_df = pd.concat([all_facilities_df, df],
                                          ignore_index=True)
        all_facilities_df = all_facilities_df.join(
            oris_df.set_index(GHGRP_ID_COL), on=GHGRP_ID_COL, how='left')
        return all_facilities_df


if __name__ == '__main__':
    try:
        # Initialize downloader
        url_year = datetime.now().year
        downloader = Downloader('tmp_data', url_year)

        # Loop through years to download data
        for year in range(2024, 2050):
            if year <= datetime.now().year:
                logging.info(f"Downloading data for year: {year}")
                try:
                    downloader.download_data(year, year - 1)
                except Exception as e:
                    logging.fatal(
                        f"Failed to download data for year {year}. Error: {e}")

    except Exception as e:
        logging.fatal(f"An unexpected error occurred: {e}")
