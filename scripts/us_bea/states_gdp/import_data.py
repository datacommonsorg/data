# Copyright 2025 Google LLC
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
"""Pulls data from the US Bureau of Economic Analysis (BEA) on quarterly GDP
per US state. Saves output as a CSV file.

The output CSV contains three measurement methods of GDP per quarter per US
state from the years 2005-2019.
    Typical usage:

    python3 import_data.py
"""
import csv
import io
import re
import os
import zipfile

from urllib.request import urlopen
from absl import app
import pandas as pd

# Suppress annoying pandas DF copy warnings.
pd.options.mode.chained_assignment = None  # default='warn'


class StateGDPDataLoader:
    """Pulls per-state GDP data from the BEA.

    Attributes:
        df: DataFrame (DF) with the cleaned data.
    """
    US_STATES = [
        'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
        'Connecticut', 'Delaware', 'District of Columbia', 'Florida', 'Georgia',
        'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky',
        'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan',
        'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
        'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
        'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
        'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
        'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
        'West Virginia', 'Wisconsin', 'Wyoming'
    ]
    _ZIP_LINK = 'https://apps.bea.gov/regional/zip/SQGDP.zip'
    _STATE_QUARTERLY_GDP_FILE = 'SQGDP1__ALL_AREAS_2005_2024.csv'
    _QUARTER_MONTH_MAP = {'Q1': '03', 'Q2': '06', 'Q3': '09', 'Q4': '12'}

    def __init__(self):
        """Initializes instance, assigning member data frames to None."""
        self.raw_df = None
        self.clean_df = None

    def process_data(self, raw_data=None, input_file="SQGDP1__ALL_AREAS_2005_2024.csv", input_folder="input_folders"):
        file_path = os.path.join(input_folder, input_file)
        print(f"Processing data from file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                data = list(reader)
                if data:
                    self.raw_df = pd.DataFrame(data, columns=header)
                    print(f"Successfully loaded data from: {input_file}")
                else:
                    self.raw_df = None
                    raise ValueError(f"Error: No data found in '{input_file}'.")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Error: File not found at: {file_path}")
        except Exception as e:
            print(f"An error occurred while reading '{input_file}': {e}")
            self.raw_df = None
            raise ValueError(f"Error loading data from '{input_file}': {e}")

        if self.raw_df is not None:
            df = self.raw_df.copy()
            if 'GeoName' in df.columns:
                df = df[df['GeoName'].isin(self.US_STATES)]
            else:
                print("Warning: 'GeoName' column not found, skipping state filtering.")
            all_quarters = [q for q in df.columns if re.match(r'....:Q.', str(q))]
            if all_quarters:
                df_melted = pd.melt(df, id_vars=['GeoFIPS', 'Unit'], value_vars=all_quarters, var_name='Quarter')
                df_melted['Quarter'] = df_melted['Quarter'].apply(self.date_to_obs_date)
                df_melted['GeoId'] = df_melted['GeoFIPS'].apply(self.convert_geoid)
                one_million = 1000000
                self.clean_df = df_melted[df_melted['Unit'] == 'Millions of chained 2017 dollars'].copy()
                if not self.clean_df.empty:
                    self.clean_df = self.clean_df.set_index(['GeoId', 'Quarter'])
                    self.clean_df['chained_2017_dollars'] = self.clean_df['value'].astype(float)
                    self.clean_df['chained_2017_dollars'] *= one_million

                quality_indices = df_melted[df_melted['Unit'] == 'Quantity index'].copy()
                if not quality_indices.empty:
                    quality_indices['GeoId'] = quality_indices['GeoFIPS'].apply(self.convert_geoid)
                    quality_indices = quality_indices.set_index(['GeoId', 'Quarter'])
                    self.clean_df['quantity_index'] = quality_indices['value'].reindex(self.clean_df.index).values.astype(float)

                current_usd = df_melted[df_melted['Unit'] == 'Millions of current dollars'].copy()
                if not current_usd.empty:
                    current_usd['GeoId'] = current_usd['GeoFIPS'].apply(self.convert_geoid)
                    current_usd = current_usd.set_index(['GeoId', 'Quarter'])
                    self.clean_df['current_dollars'] = current_usd['value'].reindex(self.clean_df.index).values.astype(float) * one_million

                self.clean_df = self.clean_df.drop(['GeoFIPS', 'Unit', 'value'], axis=1, errors='ignore')
                
            else:
                print("Warning: No quarter columns found for melting.")
        else:
            print("No data to process.")


    @classmethod
    def date_to_obs_date(cls, date):
        return date[:4] + '-' + cls._QUARTER_MONTH_MAP[date[5:]]

    @staticmethod
    def convert_geoid(fips_code):
        fips_code = fips_code.replace('"', '').replace(' ', '')
        return 'geoId/' + fips_code[:2]

    def save_csv(self, filename='states_gdp.csv'):
        """Saves instance data frame to specified CSV file."""
        if self.clean_df is None:
            raise ValueError('Uninitialized value of clean data frame. Please check process_data.')

        # Reset the index to make 'GeoId' and 'Quarter' regular columns
        self.clean_df = self.clean_df.reset_index()
        new_index = pd.Index(range(0, len(self.clean_df) * 3, 3))
        self.clean_df.index = new_index
        desired_order = ['Quarter', 'GeoId', 'chained_2017_dollars', 'quantity_index', 'current_dollars']
        self.clean_df = self.clean_df[desired_order]
        self.clean_df.to_csv(filename, index=True)
        print(self.clean_df)
        

def main(_):
    """Runs the program."""
    loader = StateGDPDataLoader()
    loader.process_data()
    loader.save_csv()


if __name__ == '__main__':
    app.run(main)
