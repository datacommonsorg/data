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

# Set logging level
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


class Downloader:
    """Downloader class to fetch, extract, and process EPA emission data and crosswalk files."""

    def __init__(self, save_path, url_year):
        """
        Initialize Downloader instance.

        Args:
            save_path (str): Path to save downloaded and processed files.
            url_year (int): Maximum year to attempt downloads.
        """
        self.years = list(range(2010, url_year - 1))
        self.current_year = None
        self.files = []
        self.save_path = save_path
        os.makedirs(self.save_path, exist_ok=True)

    def _check_url(self, url):
        """
        Check if a given URL is valid.

        Args:
            url (str): URL to check.

        Returns:
            bool: True if URL is reachable, False otherwise.
        """
        try:
            response = requests.head(url)
            response.raise_for_status()
            logging.info(f"URL is valid: {url}")
            return True
        except requests.RequestException as e:
            logging.warning(f"URL check failed: {url}. Error: {e}")
            return False

    def _generate_and_validate(self, template, **kwargs):
        """
        Generate and validate a URL from a template.

        Args:
            template (str): URL template with placeholders.
            **kwargs: Values to substitute in the template.

        Returns:
            str or None: Valid URL if found, else None.
        """
        try:
            url = template.format(**kwargs)
            if self._check_url(url):
                logging.info(f"Valid URL found: {url}")
                return url
            logging.info(f"URL not valid: {url}")
            return None
        except Exception as e:
            logging.fatal(
                f"Error occurred while generating and validating the URL: {e}")

    @retry(tries=3, delay=2, backoff=2, exceptions=(requests.RequestException,))
    def download_data(self, year, year_minus_1):
        """
        Download and extract the ZIP data file for a given year.

        Args:
            year (int): Year for which to download data.
            year_minus_1 (int): Year used in the URL format.

        Returns:
            bool: True if download and extraction are successful, False otherwise.
        """
        uri = self._generate_and_validate(download_url,
                                          year=year,
                                          year_minus_1=year_minus_1)
        if not uri:
            logging.warning(f"Skipping download for {year} due to missing URL.")
            return False
        logging.info(f'Downloading data from {uri}')
        try:
            r = requests.get(uri)
            r.raise_for_status()
            z = zipfile.ZipFile(io.BytesIO(r.content))
            for file in z.namelist():
                if not file.endswith('/'):
                    target_path = os.path.join(self.save_path,
                                               os.path.basename(file))
                    with z.open(file) as source, open(target_path,
                                                      'wb') as target:
                        target.write(source.read())
            logging.info(f"Successfully downloaded data for year: {year}")
            return True
        except Exception as e:
            logging.fatal(f"Failed to download or extract data for {year}: {e}")
            return False

    def extract_all_years(self):
        """
        Extract and save data from downloaded Excel files for all years.

        Returns:
            list: List of (year, csv_path) tuples for processed files.
        """
        try:
            headers = {sheet: {} for sheet in SHEET_NAMES_TO_CSV_FILENAMES}
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
                f"Error occurred while extracting the years from the file: {e}")

    def save_all_crosswalks(self, filepath):
        """
        Generate and save merged crosswalk files for all years.

        Args:
            filepath (str): Output path for the merged crosswalk CSV.

        Returns:
            pd.DataFrame: Combined crosswalk DataFrame.
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
            logging.fatal(f"Error occurred while saving all crosswalks: {e}")

    def _csv_path(self, csv_filename, year=None):
        """
        Construct the path to save a CSV file for a given year.

        Args:
            csv_filename (str): Name of the CSV file.
            year (int, optional): Year to include in the filename.

        Returns:
            str: Full path for the CSV file.
        """
        if not year:
            year = self.current_year
        return os.path.join(self.save_path, f'{year}_{csv_filename}')

    def _extract_data(self, headers):
        """
        Extract data from Excel sheets and save them as CSV.

        Args:
            headers (dict): Dictionary to store column headers per sheet and year.
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
                csv_filename = self.__get_csv_filename(sheet)
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
                f"Error occurred while processing the sheet names: {e}")

    def _gen_crosswalk(self):
        """
        Generate a crosswalk DataFrame for the current year.

        Returns:
            pd.DataFrame: Crosswalk mapping GHGRP ID to ORIS codes.
        """
        ssl._create_default_https_context = ssl._create_unverified_context
        try:
            oris_df = pd.read_excel(self._generate_and_validate(
                crosswalk_url, yr=self.current_year),
                                    'ORIS Crosswalk',
                                    header=0,
                                    dtype=str,
                                    usecols=CROSSWALK_COLS_TO_KEEP,
                                    engine='openpyxl')
        except Exception:
            logging.warning(f"Using fallback CROSSWALK_URI for 2022")
            oris_df = pd.read_excel(self._generate_and_validate(crosswalk_url,
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

    def __get_csv_filename(self, sheet_name):
        """
        Map Excel sheet name to corresponding CSV filename.

        Args:
            sheet_name (str): Sheet name from Excel file.

        Returns:
            str or None: CSV filename if matched, else None.
        """
        try:
            if re.match(_DIRECT_EMITTERS_SHEET, sheet_name):
                return 'direct_emitters.csv'
            return SHEET_NAMES_TO_CSV_FILENAMES.get(sheet_name)
        except Exception as e:
            logging.fatal(
                f"Error occurred while mapping the sheet Direct Emitters: {e}")


if __name__ == '__main__':

    try:
        url_year = datetime.now().year
        downloader = Downloader('tmp_data', url_year)

        for year in range(url_year, 2020, -1):
            if year <= datetime.now().year:
                logging.info(f"Starting download attempt for year: {year}")
                try:
                    success = downloader.download_data(year, year - 1)

                    # Try to extract or infer the URL if it's accessible
                    url = downloader.get_url(year, year - 1) if hasattr(downloader, 'get_url') else 'URL not available'

                    if success:
                        logging.info(f"Successfully downloaded data for year {year} from {url}")
                        break
                    else:
                        logging.warning(f"Download failed for year {year} from {url}, continuing with earlier year...")
                except Exception as e:
                    logging.fatal(f"Exception during download for year {year}. Error: {e}")
    except Exception as e:
        logging.fatal(f"Unexpected error occurred during setup or iteration. Error: {e}")

