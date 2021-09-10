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

import io
import os
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

SHEET_NAMES_TO_CSV_FILENAMES = {
    'Direct Emitters': 'direct_emitters.csv',
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

    def __init__(self, year):
        self.year = year

    def csv_path(self, csv_filename):
        return os.path.join(SAVE_PATH, f'{self.year}_{csv_filename}')

    def download_data(self):
        r = requests.get(DOWNLOAD_URI)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(SAVE_PATH)

    def extract_data(self):
        summary_filename = os.path.join(
            SAVE_PATH, YEAR_DATA_FILENAME.format(year=self.year))
        for sheet, csv_filename in SHEET_NAMES_TO_CSV_FILENAMES.items():
            summary_file = pd.read_excel(summary_filename,
                                         sheet,
                                         header=HEADER_ROW,
                                         dtype=str)
            summary_file.to_csv(self.csv_path(csv_filename),
                                index=None,
                                header=True)

    def save_crosswalk(self):
        oris_df = pd.read_excel(CROSSWALK_URI,
                                'ORIS Crosswalk',
                                header=0,
                                dtype=str,
                                usecols=CROSSWALK_COLS_TO_KEEP)
        oris_df = oris_df.set_index('GHGRP Facility ID')
        all_facilities_df = pd.DataFrame()
        for sheet, csv_filename in SHEET_NAMES_TO_CSV_FILENAMES.items():
            df = pd.read_csv(self.csv_path(csv_filename),
                             usecols=[GHGRP_ID_COL, 'FRS Id'],
                             dtype=str)
            all_facilities_df = all_facilities_df.append(df)
        all_facilities_df = all_facilities_df.set_index('Facility Id')
        all_facilities_df = all_facilities_df.join(oris_df)
        all_facilities_df.to_csv(self.csv_path('crosswalk.csv'),
                                 header=True,
                                 index_label=GHGRP_ID_COL)


if __name__ == '__main__':
    downloader = Downloader('2019')
    downloader.download_data()
    downloader.extract_data()
    downloader.save_crosswalk()
