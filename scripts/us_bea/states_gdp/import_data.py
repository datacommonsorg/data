# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Pulls data from the US Bureau of Economic Analysis (BEA) on quarterly GDP
per US state. Saves output as a CSV file. The output CSV contains three
measurement methods of GDP per quarter per US state from the years 2005-2019.

    Typical usage:

    python3 import_data.py
"""
import io
import zipfile
import csv
import re
from urllib.request import urlopen
from absl import app
import pandas as pd

# Suppress annoying pandas DF copy warnings.
pd.options.mode.chained_assignment = None # default='warn'

class StateGDPDataLoader:
    """Pulls per-state GDP data from the BEA.

    Attributes:
        df: DataFrame (DF) with the cleaned data.
    """
    _US_STATES = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California',
                  'Colorado', 'Connecticut', 'Delaware', 'District of Columbia',
                  'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana',
                  'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland',
                  'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi',
                  'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire',
                  'New Jersey', 'New Mexico', 'New York', 'North Carolina',
                  'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania',
                  'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee',
                  'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
                  'West Virginia', 'Wisconsin', 'Wyoming']
    _ZIP_LINK = "https://apps.bea.gov/regional/zip/SQGDP.zip"
    _STATE_QUARTERLY_GDP_FILE = "SQGDP1__ALL_AREAS_2005_2019.csv"
    _QUARTER_MONTH_MAP = {
        'Q1':'03',
        'Q2':'06',
        'Q3':'09',
        'Q4':'12'
    }

    def __init__(self):
        """Initializes instance, assigning member data frames to None."""
        self.raw_df = None
        self.clean_df = None

    def download_data(self, file=None, zip_link=None):
        """Downloads ZIP file, extracts the desired CSV, and puts it into a data
        frame. Stores that data frame in the instance raw_df variable.
        """
        if zip_link is None:
            zip_link = self._ZIP_LINK
        if file is None:
            file = self._STATE_QUARTERLY_GDP_FILE
        # Open zip file from link.
        resp = urlopen(zip_link)

        # Read the file, interpret it as bytes, and create a ZipFile instance
        # from it for easy handling.
        zip_file = zipfile.ZipFile(io.BytesIO(resp.read()))

        # Open the specific desired file (CSV) from the folder, and decode it.
        # This results in a string representation of the file. Interpret that
        # as a CSV, and read it into a DF.
        data = zip_file.open(file).read()
        data = data.decode('utf-8')
        data = list(csv.reader(data.splitlines()))
        self.raw_df = pd.DataFrame(data[1:], columns=data[0])

    def process_data(self, raw_data=None):
        """Cleans raw_df and converts it from wide to long format.

        Args:
            raw_data (optional): raw data frame to be used as starting point
            for cleaning. If argument is left unspecified, instance self.raw_df
            is used instead.

        Raises:
            ValueError: The instance raw_df data frame has not been initialized
            and no other raw_data was passed as argument. This is probably
            caused by not having called download_data.
        """
        if raw_data is not None:
            self.raw_df = raw_data
        if self.raw_df is None:
            raise ValueError("Uninitialized value of raw data frame. Please "
                             "check you are calling download_data before "
                             "process_data.")
        df = self.raw_df.copy()

        # Filters out columns that are not US states (e.g. New England).
        df = df[df['GeoName'].isin(self._US_STATES)]

        # Gets columns that represent quarters, e.g. 2015:Q2, by matching
        # against a regular expression.
        all_quarters = [q for q in df.columns if re.match(r"....:Q.", q)]

        # Convert table from wide to long format.
        df = pd.melt(df, id_vars=['GeoFIPS', 'Unit'],
                     value_vars=all_quarters,
                     var_name='Quarter')

        df['Quarter'] = df['Quarter'].apply(self._date_to_obs_date)
        df['GeoId'] = df['GeoFIPS'].apply(self._convert_geoid)

        # Set the instance DF to have one row per geoId/quarter pair, with
        # different measurement methods as columns. This facilitates the
        # design of TMCFs. Also convert values from millions of USD to USD.
        one_million = 1000000
        self.clean_df = df[df["Unit"] == "Millions of chained 2012 dollars"]
        self.clean_df.set_index(["GeoId", "Quarter"])
        self.clean_df["chained_2012_dollars"] = self.clean_df["value"].astype(float)
        self.clean_df["chained_2012_dollars"] *= one_million
        quality_indices = df[df["Unit"] == "Quantity index"]
        self.clean_df["quantity_index"] = quality_indices["value"].values.astype(float)
        current_usd = df[df["Unit"] == "Millions of current dollars"]["value"]
        self.clean_df["current_dollars"] = current_usd.values.astype(float)
        self.clean_df["current_dollars"] *= one_million
        self.clean_df = self.clean_df.drop(["GeoFIPS", "Unit", "value"], axis=1)

    @classmethod
    def _date_to_obs_date(cls, date):
        """Converts date format from YEAR:QUARTER to YEAR-MONTH,
        where the recorded month is the last month in the given quarter.
        For example: "2005:Q3" to "2005-09".
        """
        return date[:4] + "-" + cls._QUARTER_MONTH_MAP[date[5:]]

    @staticmethod
    def _convert_geoid(fips_code):
        """Creates GeoId column. We get lucky that Data Commons's geoIds
        equal US FIPS state codes. We slice out zero-padding.
        """
        fips_code = fips_code.replace('"', "")
        fips_code = fips_code.replace(" ", "")
        return "geoId/" + fips_code[:2]

    def save_csv(self, filename='states_gdp.csv'):
        """Saves instance data frame to specified CSV file.

        Raises:
            ValueError: The instance clean_df data frame has not been
            initialized. This is probably caused by not having called
            process_data.
        """
        if self.clean_df is None:
            raise ValueError("Uninitialized value of clean data frame. Please "
                             "check you are calling process_data before "
                             "save_csv.")
        self.clean_df.to_csv(filename)


def main(argv):
    del argv # unused
    loader = StateGDPDataLoader()
    loader.download_data()
    loader.process_data()
    loader.save_csv()


if __name__ == '__main__':
    app.run(main)
