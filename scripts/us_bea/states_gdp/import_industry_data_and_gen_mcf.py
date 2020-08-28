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
"""Pulls data from the US Bureau of Economic Analysis (BEA) on quarterly GDP
per US state per industry.

Saves output as a CSV file.

Also generates the MCF nodes for the data schema.
    Typical usage:

    python3 import_industry_data_and_gen_mcf.py
"""
import os
import re
import sys

from absl import app
import pandas as pd

# Allows the following module import to work when running as a script
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from us_bea.states_gdp import import_data

# Suppress annoying pandas DF copy warnings.
pd.options.mode.chained_assignment = None  # default='warn'


class StateGDPIndustryDataLoader(import_data.StateGDPDataLoader):
    """Pulls GDP industry-level state data from BEA.

    Attributes:
        df: DataFrame (DF) with the cleaned data.
    """
    _STATE_QUARTERLY_INDUSTRY_GDP_FILE = 'SQGDP2__ALL_AREAS_2005_2020.csv'

    def download_data(self, zip_link=None, file=None):
        """Downloads ZIP file, extracts the desired CSV, and puts it into a data

        frame. Stores that data frame in the instance raw_df variable.
        """
        super().download_data(file=self._STATE_QUARTERLY_INDUSTRY_GDP_FILE)

    def process_data(self, raw_data=None):
        """Cleans raw_df and converts it from wide to long format.

        Args:
            raw_data (optional): raw data frame to be used as starting point for
              cleaning. If argument is left unspecified, instance self.raw_df is
              used instead.

        Raises:
            ValueError: The instance raw_df data frame has not been initialized
            and no other raw_data was passed as argument. This is probably
            caused by not having called download_data.
        """
        if raw_data is not None:
            self.raw_df = raw_data
        if self.raw_df is None:
            raise ValueError('Uninitialized value of raw data frame. Please '
                             'check you are calling download_data before '
                             'process_data.')
        df = self.raw_df.copy()

        # Filters out columns that are not US states (e.g. New England).
        df = df[df['GeoName'].isin(self.US_STATES)]

        # Gets columns that represent quarters, e.g. 2015:Q2, by matching
        # against a regular expression.
        all_quarters = [q for q in df.columns if re.match(r'\d\d\d\d:Q\d', q)]

        # Convert table from wide to long format.
        df = pd.melt(df,
                     id_vars=['GeoFIPS', 'IndustryClassification'],
                     value_vars=all_quarters,
                     var_name='Quarter')

        df['Quarter'] = df['Quarter'].apply(self.date_to_obs_date)
        df['GeoId'] = df['GeoFIPS'].apply(self.convert_geoid)

        df = df[df['IndustryClassification'] != '...']

        df['NAICS'] = df['IndustryClassification'].apply(
            self.convert_industry_class)
        df['value'] = df['value'].apply(self.value_converter)
        df = df[df['value'] >= 0]

        # Convert from millions of current USD to current USD.
        df['value'] *= 1000000
        self.clean_df = df.drop(['GeoFIPS', 'IndustryClassification'], axis=1)

    @staticmethod
    def value_converter(val):
        """Converts value to float type, and filters out missing values.

    Missing
        values are marked by a letter enclosed in parentheses, e.g., "(D)".
        """
        try:
            return float(val)
        except ValueError:
            return -1

    @staticmethod
    def convert_industry_class(naics_code):
        """Filters out aggregate NAICS codes and assigns them their Data

        Commons codes.
        """
        if isinstance(naics_code, str):
            naics_code = naics_code.replace('-', '_').replace(',', '&')
        return f"dcs:USStateQuarterlyIndustryGDP_NAICS_{naics_code}"

    def save_csv(self, filename='states_industry_gdp.csv'):
        """Saves instance data frame to specified CSV file.

        Raises:
            ValueError: The instance clean_df data frame has not been
            initialized. This is probably caused by not having called
            process_data.
        """
        super().save_csv(filename)

    def generate_mcf(self):
        """Generates MCF StatVars for each industry code."""
        mcf_temp = ('Node: dcid:USStateQuarterlyIndustryGDP_NAICS_{title}\n'
                    'typeOf: dcs:StatisticalVariable\n'
                    'populationType: dcs:EconomicActivity\n'
                    'activitySource: dcs:GrossDomesticProduction\n'
                    'measuredProperty: dcs:amount\n'
                    'measurementQualifier: dcs:Nominal\n'
                    'naics: dcid:NAICS/{naics}\n\n')

        with open('states_gdp_industry_statvars.mcf', 'w') as mcf_f:
            for naics_code in self.clean_df['NAICS'].unique():
                code_title = naics_code[38:]
                code = code_title.replace('_', '-')
                code = code.replace('&', '&NAICS/')
                mcf_f.write(mcf_temp.format(title=code_title, naics=code))


def main(_):
    """Runs the program."""
    loader = StateGDPIndustryDataLoader()
    loader.download_data()
    loader.process_data()
    loader.save_csv()
    loader.generate_mcf()


if __name__ == '__main__':
    app.run(main)
