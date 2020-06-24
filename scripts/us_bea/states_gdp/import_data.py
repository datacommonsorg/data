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
per US state. Saves output as a CSV file.

    Typical usage:

    python3 import_data.py
"""
from urllib.request import urlopen
import pandas as pd
import io
import zipfile
import csv
import re

US_STATES = ['Alabama', 'Alaska', 'Arizona', 'Arkansas',
             'California', 'Colorado', 'Connecticut', 'Delaware',
             'District of Columbia', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
             'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
             'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
             'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
             'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
             'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
             'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
             'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
             'West Virginia', 'Wisconsin', 'Wyoming']


class StateGDPDataLoader:
    """Pulls GDP state data from BEA.

    Attributes:
        df: DataFrame (DF) with the cleaned data.
    """
    ZIP_LINK = "https://apps.bea.gov/regional/zip/SQGDP.zip"
    FILE = "SQGDP1__ALL_AREAS_2005_2019.csv"

    def __init__(self):
        """Downloads the data, cleans it and stores it in instance DF."""
        # Open zip file from link.
        resp = urlopen(self.ZIP_LINK)

        # Read the file, interpret it as bytes, and create a ZipFile instance
        # from it for easy handling.
        zip_file = zipfile.ZipFile(io.BytesIO(resp.read()))

        # Open the specific desired file (CSV) from the folder, and decode it.
        # This results in a string representation of the file. Interpret that
        # as a CSV, and read it into a DF.
        data = zip_file.open(self.FILE).read().decode('utf-8')
        data = list(csv.reader(data.splitlines()))
        df = pd.DataFrame(data[1:], columns=data[0])

        # Filters out columns that are not US States (e.g. New England).
        # TODO(fpernice): Add non-state entities.
        df = df[df['GeoName'].isin(US_STATES)]

        # Gets columns that represent quarters, e.g. 2015:Q2, by matching
        # against a regular expression.
        all_quarters = [q for q in df.columns if re.match(r"....:Q.", q)]

        # Convert table from wide to long format.
        df = pd.melt(df, id_vars=['GeoFIPS', 'Unit'],
                     value_vars=all_quarters,
                     var_name='Quarter')

        qtr_month_map = {
            'Q1':'03',
            'Q2':'06',
            'Q3':'09',
            'Q4':'12'
        }

        def date_to_obs_date(date):
            """Converts date format e.g. 2005:Q3 to e.g. 2005-09."""
            date = date.replace("\r", "")
            return date[:4] + "-" + qtr_month_map[date[5:]]
        df['Quarter'] = df['Quarter'].apply(date_to_obs_date)

        def clean_data_val(data):
            """Removes '\r' characters in value column and converts to float."""
            return float(data.replace("\r", ""))
        df['value'] = df['value'].apply(clean_data_val)

        def convert_geoid(fips_code):
            """Creates GeoId column. We get lucky that Data Commons's geoIds
            equal US FIPS state codes.
            """
            fips_code = fips_code.replace('"', "")
            fips_code = fips_code.replace(" ", "")
            return "geoId/" + fips_code[:2]
        df['GeoId'] = df['GeoFIPS'].apply(convert_geoid)

        # Set the instance DF to have one row per geoId/Quarter pair, with
        # different measurement methods as columns. This facilitates the
        # design of TMCFs.
        self.df = df[df['Unit'] == "Millions of chained 2012 dollars"]
        self.df.set_index(['GeoId', 'Quarter'])
        self.df["millions_of_chained_2012_dollars"] = self.df['value']
        quality_indices = df[df['Unit'] == "Quantity index"]
        self.df["Quantity_index"] = quality_indices['value'].values
        current_usd = df[df['Unit'] == "Millions of current dollars"]['value']
        self.df["millions_of_current_dollars"] = current_usd.values
        self.df = self.df.drop(["GeoFIPS", "Unit", "value"], axis=1)

    def save_csv(self, filename='states_gdp.csv'):
        """Saves instance DF to specified csv file."""
        self.df.to_csv(filename)


def main():
    loader = StateGDPDataLoader()
    loader.save_csv()


if __name__ == '__main__':
    main()
