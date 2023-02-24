# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pandas as pd
from datetime import datetime
from os import path
import zipfile

module_dir = os.path.dirname(__file__)

# AQI_STATIONS_FILE has list of Air Quality stations along with its DCIDs
AQI_STATIONS_FILE = "CPCB_AirQualitySites.csv"


class AQIDataLoader:
    """
    This class is responsible for loading and processing the unclean data into a clean by a series of steps
    and then finally appending it into the result CSV file.

    Instance Attributes:
    source: The path of the CSV file whose data is later on processed and 
            stored in the final CSV
    raw_df: Original AQI pandas dataframe that undergoes preprocessing in order 
            to become a clean dataframe
    clean_df: Cleaned dataframe that has properly named columns, and compatible 
            data types as per the column
    """

    def __init__(self, source: str):
        """
        Inits AQIDataLoader with the respective CSV File Path(s) and data frame(s) variables for processing.
        """
        self.source_file = source
        self.clean_df = None

        # Dictionary map to rename column names in preprocessed dataframe
        # to its counterparts in TMCF file
        self.clean_column_names = {
            'pm25': 'PM25',
            'pm10': 'PM10',
            'no2': 'NO2',
            'nh3': 'NH3',
            'so2': 'SO2',
            'co': 'CO',
            'o3': 'O3',
            'at': 'AT',
            'bp': 'BP',
            'sr': 'SR',
            'rh': 'RH',
            'wd': 'WD',
            'no': 'NO',
            'nox': 'NOx',
            'benzene': 'Benzene',
            'toluene': 'Toluene',
            'xylene': 'Xylene',
            'mp_xylene': 'MP_Xylene',
            'eth_benzene': 'Eth_Benzene'
        }

    def _iso_format(self, date: str, time: str) -> str:
        """
        Helper function to return the date in the required ISO format.
        """

        # This is the date and time format given in the source data
        format_data = "%d/%b/%Y %H:%M"
        date_time = "{} {}".format(date.replace('-', '/'), time)

        return datetime.strptime(date_time, format_data).isoformat()

    def _make_column_numerical(self, column: str):
        """
        This function converts the columns that are of string data type into numeric data type.
        """
        self.clean_df[column] = self.clean_df[column].astype(str).str.replace(
            ',', '')
        self.clean_df[column] = pd.to_numeric(self.clean_df[column],
                                              errors="ignore")

    def _delete_extracted_files(self, extracted_path: str):
        """
        Helper function to remove all the extracted files after the preprocessing step
        """
        for file in os.listdir(extracted_path):
            # All the extracted files are in CSV format and filename starts with 'Table'
            if file.startswith('Table'):
                os.remove(os.path.join(extracted_path, file))

    def load(self):
        """
        This function reads the source file, and loads and transforms the source data
        as a part of the pre processing step. 
        """
        df = pd.read_csv(self.source_file)
        dcid_file_path = os.path.join(module_dir, 'data', AQI_STATIONS_FILE)
        dcid_df = pd.read_csv(dcid_file_path)

        # Converting the date and time columns in source data to
        # ISO format (yyyy-mm-ddThh:mm:ss)
        df['Date'] = df.apply(
            lambda x: self._iso_format(x['from_date'], x['from_time']), axis=1)

        # AirQualitySite DCIDs are already imported into DC
        # Example: datacommons.org/browser/cpcbAq/482_BandraKurlaComplex_Mumbai
        site_dcid_map = pd.Series(dcid_df['dcid'].values,
                                  index=dcid_df['site_id']).to_dict()
        # Mapping the Site IDs of Air Quality stations to its corresponding DCIDs
        df['dcid'] = df['site'].map(site_dcid_map)

        # Renaming columns to match the names in TMCF and dropping unwanted columns
        df.rename(columns=self.clean_column_names, inplace=True)
        df.drop([
            'query_name', 'from_date', 'from_time', 'to_date', 'to_time', 'id',
            'site'
        ],
                axis=1,
                inplace=True)

        self.raw_df = df

    def process(self):
        """ This function is responsible for processes the raw data frame and
        converts it into the clean data frame whose data is to be appended in the result data frame. 
        """
        self.clean_df = self.raw_df  # Assigns a copy of raw dataframe to clean dataframe for cleaning

        # Converting the data columns into numerical format
        for column in self.clean_column_names.values():
            self._make_column_numerical(column)

    def save(self, csv_file_path: str):
        """
        This function appends the cleaned data into the result data frame in order to generate 
        the final CSV file.
        """
        if path.exists(csv_file_path):
            self.clean_df.to_csv(csv_file_path,
                                 mode='a',
                                 index=False,
                                 header=False)
        else:
            self.clean_df.to_csv(csv_file_path, index=False, header=True)


def main():
    csv_file_path = os.path.join(module_dir, "India_AQI.csv")
    extract_path = os.path.join(module_dir, "data/")
    source_zip = os.path.join(extract_path, 'India_AQI.zip')

    # Extract the zipfile in data/ folder and iterate through the extracted files
    z = zipfile.ZipFile(source_zip)
    z.extractall(extract_path)

    for file in os.listdir(extract_path):
        source_file = os.path.join(extract_path, file)
        # All the extracted data file names start with 'Table'
        if file.startswith('Table'):
            loader = AQIDataLoader(source=source_file)
            loader.load()
            loader.process()
            loader.save(csv_file_path)

    # Deleting the extracted data files and keeping only the zip file
    loader._delete_extracted_files(extract_path)


if __name__ == "__main__":
    main()
