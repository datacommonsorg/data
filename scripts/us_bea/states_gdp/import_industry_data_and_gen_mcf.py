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
import io
import zipfile
import csv
import re
from absl import app
import pandas as pd
import import_data

# Suppress annoying pandas DF copy warnings.
pd.options.mode.chained_assignment = None # default='warn'

class StateGDPIndustryDataLoader(import_data.StateGDPDataLoader):
    """Pulls GDP industry-level state data from BEA.

    Attributes:
        df: DataFrame (DF) with the cleaned data.
    """
    _STATE_QUARTERLY_INDUSTRY_GDP_FILE = "SQGDP2__ALL_AREAS_2005_2020.csv"

    def download_data(self):
        """Downloads ZIP file, extracts the desired CSV, and puts it into a data
        frame. Stores that data frame in the instance raw_df variable.
        """
        # Open zip file from link.
        resp = urlopen(self._ZIP_LINK)

        # Read the file, interpret it as bytes, and create a ZipFile instance
        # from it for easy handling.
        zip_file = zipfile.ZipFile(io.BytesIO(resp.read()))

        # Open the specific desired file (CSV) from the folder, and decode it.
        # This results in a string representation of the file. Interpret that
        # as a CSV, and read it into a DF.
        data = zip_file.open(self._STATE_QUARTERLY_INDUSTRY_GDP_FILE).read()
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
        all_quarters = [q for q in df.columns if re.match(r"\d\d\d\d:Q\d", q)]

        # Convert table from wide to long format.
        df = pd.melt(df, id_vars=['GeoFIPS', 'IndustryClassification'],
                     value_vars=all_quarters,
                     var_name='Quarter')

        df['Quarter'] = df['Quarter'].apply(self._date_to_obs_date)
        df['GeoId'] = df['GeoFIPS'].apply(self._convert_geoid)

        df = df[df['IndustryClassification'] != "..."]

        df['NAICS'] = df['IndustryClassification'].apply(self._convert_industry_class)
        df['value'] = df['value'].apply(self._value_converter)
        df = df[df['value'] >= 0]

        self.clean_df = df.drop(["GeoFIPS", "IndustryClassification"], axis=1)

    @staticmethod
    def _value_converter(val):
        """Converts value to float type, and filters out missing values. Missing
        values are marked by a latter enclosed in parentheses, e.g., "(D)".
        """
        if not isinstance(val, str):
            return val
        if '(' in val or ')' in val:
            return -1
        return float(val)


    @staticmethod
    def _convert_industry_class(naics_code):
        """Filters out aggregate NAICS codes and assigns them their Data
        Commons codes.
        """
        if naics_code == "321,327-339":
            naics_code = "JOLTS_320000"
        if naics_code == "311-316,322-326":
            naics_code = "JOLTS_340000"
        naics_code = naics_code.replace("-", "_")
        return f"dcs:USSateQuarterlyIndustryGDP_NAICS_{naics_code}"

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
        mcf_temp = ('Node: dcid:USStateQuarterlyIndustryGDP_NAICS_{naics}\n'
                    'typeOf: dcs:StatisticalVariable\n'
                    'populationType: dcs:EconomicActivity\n'
                    'activitySource: dcs:GrossDomesticProduction\n'
                    'measuredProperty: dcs:amount\n'
                    'measurementQualifier: dcs:Nominal\n'
                    'naics: dcid:NAICS/{naics}\n\n')

        with open('states_gdp_industry_statvars.mcf', 'w') as mcf_f:
            for naics_code in self.clean_df['NAICS'].unique():
                code = naics_code[37:]
                mcf_f.write(mcf_temp.format(naics=code))

def main(_):
    loader = StateGDPIndustryDataLoader()
    loader.download_data()
    loader.process_data()
    loader.save_csv()
    loader.generate_mcf()


if __name__ == '__main__':
    app.run(main)
