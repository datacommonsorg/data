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
import os
import ssl

import pandas as pd
import requests
import zipfile

DOWNLOAD_URI = 'https://www.epa.gov/sites/default/files/2020-11/2019_data_summary_spreadsheets.zip'
YEAR_DATA_FILENAME = 'ghgp_data_{year}.xlsx'
HEADER_ROW = 3
SAVE_PATH = 'tmp_data'
CROSSWALK_URI = 'https://www.epa.gov/sites/default/files/2020-12/ghgrp_oris_power_plant_crosswalk_11_24_20.xlsx'
CROSSWALK_COLS_TO_KEEP = [
    'GHGRP Facility ID', 'ORIS CODE', 'ORIS CODE 2', 'ORIS CODE 3',
    'ORIS CODE 4', 'ORIS CODE 5'
]
GHGRP_ID_COL = 'Facility Id'

_DIRECT_EMITTERS_SHEET = 'Direct Emitters'
SHEET_NAMES_TO_CSV_FILENAMES = {
    _DIRECT_EMITTERS_SHEET: 'direct_emitters.csv',
    'Onshore Oil & Gas Prod.': 'oil_and_gas.csv',
    'Gathering & Boosting': 'gathering_and_boosting.csv',
    'LDC - Direct Emissions': 'local_distribution.csv',
    'SF6 from Elec. Equip.': 'elec_equip.csv',
    # Needs schema:
    # - 'Transmission Pipelines',
    # The following sheets are skipped due to sparse data:
    # - 'Suppliers',
    # - 'CO2 Injection',
    # - 'Geologic Sequestration of CO2',
}


class Downloader:
    """
    The following must be called in order. Earlier steps can be skipped if it has successfully completed in a previous run.
    - download_data
    - extract_all_years
    - save_all_crosswalks
    """

    def __init__(self):
        self.years = list(range(2010, 2020))
        self.current_year = None
        self.files = {}  # sheet name -> list of files
        for sheet, _ in SHEET_NAMES_TO_CSV_FILENAMES.items():
            self.files[sheet] = {}

    def download_data(self):
        """Downloads and unzips excel files from DOWNLOAD_URI."""
        print(f'Downloading data')
        r = requests.get(DOWNLOAD_URI)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(SAVE_PATH)

    def extract_all_years(self):
        """Saves relevant sheets from each year's Excel file to a csv."""
        headers = {}
        for sheet, _ in SHEET_NAMES_TO_CSV_FILENAMES.items():
            headers[sheet] = {}
        for current_year in self.years:
            print(f'Extracting data for {current_year}')
            self.current_year = current_year
            self._extract_data(headers)
        for sheet, csv_name in SHEET_NAMES_TO_CSV_FILENAMES.items():
            headers_df = pd.DataFrame.from_dict(headers[sheet], orient='index')
            headers_df.transpose().to_csv(os.path.join(SAVE_PATH,
                                                       f'cols_{csv_name}'),
                                          index=None)

    def save_all_crosswalks(self):
        """Builds individual year crosswalks, as well as a join crosswalk for all years."""
        print(f'Saving all ID crosswalks')
        crosswalks = []
        for current_year in self.years:
            crosswalks.append(downloader._save_crosswalk())
        all_crosswalks_df = pd.concat(crosswalks, join='outer')
        all_crosswalks_df = all_crosswalks_df.sort_values(
            by=[GHGRP_ID_COL, 'FRS Id', 'ORIS CODE'])
        all_crosswalks_df = all_crosswalks_df.drop_duplicates()
        all_crosswalks_df.to_csv(os.path.join(SAVE_PATH, 'crosswalks.csv'),
                                 header=True,
                                 index=None)
        return all_crosswalks_df

    def get_direct_emitter_files(self):
        return self.files[_DIRECT_EMITTERS_SHEET]

    def _csv_path(self, csv_filename, year=None):
        if not year:
            year = self.current_year
        return os.path.join(SAVE_PATH, f'{year}_{csv_filename}')

    def _extract_data(self, headers):
        summary_filename = os.path.join(
            SAVE_PATH, YEAR_DATA_FILENAME.format(year=self.current_year))
        xl = pd.ExcelFile(summary_filename, engine='openpyxl')
        for sheet in xl.sheet_names:
            csv_filename = SHEET_NAMES_TO_CSV_FILENAMES.get(sheet, None)
            if not csv_filename:
                print(f'Skipping sheet: {sheet}')
                continue
            summary_file = xl.parse(sheet, header=HEADER_ROW, dtype=str)
            csv_filename = self._csv_path(csv_filename)
            summary_file.to_csv(csv_filename, index=None, header=True)
            headers[sheet][self.current_year] = summary_file.columns
            self.files[sheet][self.current_year] = csv_filename

    def _save_crosswalk(self):
        # Per https://stackoverflow.com/a/56230607
        ssl._create_default_https_context = ssl._create_unverified_context

        oris_df = pd.read_excel(CROSSWALK_URI,
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
            all_facilities_df = all_facilities_df.append(df)
        all_facilities_df = all_facilities_df.join(
            oris_df.set_index(GHGRP_ID_COL), on=GHGRP_ID_COL, how='left')
        return all_facilities_df


if __name__ == '__main__':
    downloader = Downloader()
    downloader.download_data()
    downloader.extract_all_years()
    downloader.save_all_crosswalks()
