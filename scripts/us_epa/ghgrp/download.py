import io
import logging
import os
import ssl
import re
import requests
from datetime import datetime
import pandas as pd
import zipfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    """
    if re.match(_DIRECT_EMITTERS_SHEET, sheet_name):
        return 'direct_emitters.csv'
    return SHEET_NAMES_TO_CSV_FILENAMES.get(sheet_name)

class Downloader:
    """
    Handles downloading, extracting, and processing data files.
    """

    def __init__(self, save_path):
        self.years = list(range(2010, datetime.now().year))
        self.current_year = None
        self.files = []  # list of (year, filename) of all extracted files
        self.save_path = save_path

        # Ensure the save directory exists
        os.makedirs(self.save_path, exist_ok=True)

    def check_url(self, url):
        """
        Checks if a given URL is accessible.
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
        """
        url = template.format(**kwargs)
        if not self.check_url(url):
            raise ValueError(f"URL not valid: {url}")
        return url

    def download_data(self, year, year_minus_1):
        """
        Downloads and unzips Excel files from dynamically generated DOWNLOAD_URI.
        """
        uri = self.generate_and_validate(download_url, year = year, year_minus_1 = year_minus_1)
        logging.info(f'Downloading data from {uri}')
        try:
            r = requests.get(uri)
            r.raise_for_status()  # Raise an error for unsuccessful responses
            z = zipfile.ZipFile(io.BytesIO(r.content))
            for file in z.namelist():
                # Skip directories
                if not file.endswith('/'):
                    target_path = os.path.join(self.save_path, os.path.basename(file))
                    with z.open(file) as source, open(target_path, 'wb') as target:
                        target.write(source.read())
        except Exception as e:
            logging.error(f"Failed to download or extract data for {year}: {e}")

    def extract_all_years(self):
        """
        Saves relevant sheets from each year's Excel file to a CSV.
        """
        headers = {}
        for sheet, _ in SHEET_NAMES_TO_CSV_FILENAMES.items():
            headers[sheet] = {}
        for current_year in self.years:
            logging.info(f'Extracting data for {current_year}')
            self.current_year = current_year
            self._extract_data(headers)
        for sheet, csv_name in SHEET_NAMES_TO_CSV_FILENAMES.items():
            headers_df = pd.DataFrame.from_dict(headers[sheet], orient='index')
            headers_df.transpose().to_csv(os.path.join(self.save_path, f'cols_{csv_name}'), index=None)
        return self.files

    def save_all_crosswalks(self, filepath):
        """
        Builds individual year crosswalks, as well as a joint crosswalk for all years.
        """
        logging.info('Saving all ID crosswalks')
        crosswalks = []
        for current_year in self.years:
            crosswalks.append(self._gen_crosswalk())
        all_crosswalks_df = pd.concat(crosswalks, join='outer')
        all_crosswalks_df = all_crosswalks_df.sort_values(
            by=[GHGRP_ID_COL, 'FRS Id', 'ORIS CODE'])
        all_crosswalks_df = all_crosswalks_df.drop_duplicates()
        all_crosswalks_df.to_csv(filepath, header=True, index=None)
        return all_crosswalks_df

    def _csv_path(self, csv_filename, year=None):
        if not year:
            year = self.current_year
        return os.path.join(self.save_path, f'{year}_{csv_filename}')

    def _extract_data(self, headers):
        summary_filename = os.path.join(
                self.save_path, YEAR_DATA_FILENAME.format(year=self.current_year)
                        )
        
        xl = pd.ExcelFile(summary_filename, engine='openpyxl')
        logging.info(f"Available sheets in {summary_filename}: {xl.sheet_names}")
        check_list=[]
        for sheet in xl.sheet_names:
            csv_filename = get_csv_filename(sheet)
            check_list.append(csv_filename)
            if not csv_filename:
                logging.info(f'Skipping sheet: {sheet}')
                continue
            summary_file = xl.parse(sheet, header=HEADER_ROW, dtype=str)
            csv_path = self._csv_path(csv_filename)
            summary_file.to_csv(csv_path, index=None, header=True)
            headers.setdefault(sheet, {})[self.current_year] = summary_file.columns
            self.files.append((self.current_year, csv_path))
        if "direct_emitters.csv" not in check_list:
                logging.error(f"'direct_emitters.csv' not found in the sheets for {self.current_year}. Aborting!")
                raise SystemExit(f"Missing required sheet for 'direct_emitters.csv' in year {self.current_year}. Exiting.")
            

    def _gen_crosswalk(self):
        ssl._create_default_https_context = ssl._create_unverified_context
        try:
            oris_df = pd.read_excel(
                self.generate_and_validate(crosswalk_url, yr=self.current_year),
                'ORIS Crosswalk',
                header=0,
                dtype=str,
                usecols=CROSSWALK_COLS_TO_KEEP,
                engine='openpyxl'
            )
        except Exception:
            logging.warning(f"Using fallback CROSSWALK_URI for 2022")
            oris_df = pd.read_excel(
                self.generate_and_validate(crosswalk_url, yr=2022),
                'ORIS Crosswalk',
                header=0,
                dtype=str,
                usecols=CROSSWALK_COLS_TO_KEEP,
                engine='openpyxl'
            )

        oris_df = oris_df.rename(columns={'GHGRP Facility ID': GHGRP_ID_COL})
        all_facilities_df = pd.DataFrame()
        for sheet, csv_filename in SHEET_NAMES_TO_CSV_FILENAMES.items():
            csv_path = self._csv_path(csv_filename)
            if not os.path.exists(csv_path):
                continue
            df = pd.read_csv(csv_path, usecols=[GHGRP_ID_COL, 'FRS Id'], dtype=str)
            all_facilities_df = pd.concat([all_facilities_df, df], ignore_index=True)
        all_facilities_df = all_facilities_df.join(
            oris_df.set_index(GHGRP_ID_COL), on=GHGRP_ID_COL, how='left')
        return all_facilities_df


if __name__ == '__main__':
    downloader = Downloader('tmp_data')
    url_year= datetime.now().year
    if url_year < 2030:
        downloader.download_data(url_year,url_year-1)
    downloader.extract_all_years()
    downloader.save_all_crosswalks(os.path.join(downloader.save_path, 'crosswalks.csv'))
