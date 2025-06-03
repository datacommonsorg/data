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
import io
import os
import re
import sys
from absl import app
from absl import flags
from absl import logging
import pandas as pd

logging.set_verbosity(logging.INFO)
# Allows the following module import to work when running as a script
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from us_bea.states_gdp import import_data
import csv

FLAGS = flags.FLAGS
flags.DEFINE_integer('latest_year_industry', None,
                     'The latest year to look for in the filename (optional).')

# Suppress annoying pandas DF copy warnings.
pd.options.mode.chained_assignment = None  # default='warn'


class StateGDPIndustryDataLoader(import_data.StateGDPDataLoader):
    """Pulls GDP industry-level state data from BEA.

    Attributes:
        df: DataFrame (DF) with the cleaned data.
    """

    def process_data(self, raw_data=None, input_folder='input_data'):
        """Cleans data from a specified CSV file in the input folder
        and converts it from wide to long format.

        Args:
            raw_data (optional): raw data frame to be used as starting point.
            input_folder (str, optional): The folder containing the CSV file.
                                        Defaults to the value of the --input_folder flag.

        Raises:
            FileNotFoundError: If the specified CSV file is not found.
            ValueError: If no data could be loaded from the specified file.
        """
        if raw_data is not None:
            logging.info("Processing data from provided raw data.")
            csvfile = io.StringIO(raw_data)
            reader = csv.reader(csvfile)
            header = next(reader)
            data = list(reader)
            if data:
                self.raw_df = pd.DataFrame(data, columns=header)
                logging.info(
                    f"Successfully loaded data from provided raw data.")
            else:
                self.raw_df = None
                raise ValueError("Error: No data found in provided raw data.")
            self._input_file = 'provided_data'

        else:
            try:
                _STATE_QUARTERLY_GDP_FILE_PATTERN1 = r'SQGDP2__ALL_AREAS_(\d{4})_(\d{4})\.csv'
                self._input_file = self._find_gdp_file_in_folder(
                    input_folder, _STATE_QUARTERLY_GDP_FILE_PATTERN1,
                    FLAGS.latest_year_industry)
                file_path = os.path.join(input_folder, self._input_file)
                logging.info(f"Processing data from file: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    header = next(reader)
                    data = list(reader)
                    if data:
                        self.raw_df = pd.DataFrame(data, columns=header)
                        logging.info(
                            f"Successfully loaded data from: {self._input_file}"
                        )
                    else:
                        self.raw_df = None
                        raise ValueError(
                            f"Error: No data found in '{self._input_file}'.")
            except FileNotFoundError as e:
                raise FileNotFoundError(f"Error: {e}")
            except Exception as e:
                logging.error(f"An error occurred while reading data: {e}")
                self.raw_df = None
                raise ValueError(f"Error loading data: {e}")

        if self.raw_df is not None:
            df = self.raw_df.copy()

            # Filters out columns that are not US states (e.g. New England).
            if 'GeoName' in df.columns:
                df = df[df['GeoName'].isin(self.US_STATES)]
            else:
                logging.warning(
                    "Warning: 'GeoName' column not found, skipping state filtering."
                )

            # Gets columns that represent quarters, e.g. 2015:Q2, by matching
            # against a regular expression.
            all_quarters = [
                q for q in df.columns if re.match(r'\d\d\d\d:Q\d', str(q))
            ]

            if all_quarters:
                # Convert table from wide to long format.
                df = pd.melt(df,
                             id_vars=['GeoFIPS', 'IndustryClassification'],
                             value_vars=all_quarters,
                             var_name='Quarter')

                df['Quarter'] = df['Quarter'].apply(self.date_to_obs_date)
                df['GeoId'] = df['GeoFIPS'].apply(self.convert_geoid)

                if 'IndustryClassification' in df.columns:
                    df = df[df['IndustryClassification'] != '...']
                    df['NAICS'] = df['IndustryClassification'].apply(
                        self.convert_industry_class)
                else:
                    logging.warning(
                        "Warning: 'IndustryClassification' column not found.")

                if 'value' in df.columns:
                    df['value'] = df['value'].apply(self.value_converter)
                    df = df[df['value'] >= 0]
                    # Convert from millions of current USD to current USD.
                    df['value'] *= 1000000
                else:
                    logging.warning("Warning: 'value' column not found.")

                self.clean_df = df.drop(['GeoFIPS', 'IndustryClassification'],
                                        axis=1,
                                        errors='ignore')
            else:
                logging.warning(
                    "Warning: No quarter columns found for melting.")
        else:
            logging.fatal("No data to process.")

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
            naics_code = naics_code.replace('-', '_').replace(',', '_')
        return f"dcs:USStateQuarterlyIndustryGDP_NAICS_{naics_code}"

    def save_csv(self, filename='states_industry_gdp.csv'):
        """Saves instance data frame to specified CSV file.

        Raises:
            ValueError: The instance clean_df data frame has not been
            initialized. This is probably caused by not having called
            process_data.
        """
        if self.clean_df is None:
            raise ValueError('Uninitialized value of clean data frame. Please '
                             'check you are calling process_data before '
                             'save_csv.')
        self.clean_df.to_csv(filename)

    def generate_mcf(self):
        """Generates MCF StatVars for each industry code."""
        mcf_temp = ('Node: dcid:USStateQuarterlyIndustryGDP_NAICS_{title}\n'
                    'typeOf: dcs:StatisticalVariable\n'
                    'populationType: dcs:EconomicActivity\n'
                    'activitySource: dcs:GrossDomesticProduction\n'
                    'measuredProperty: dcs:amount\n'
                    'measurementQualifier: dcs:Nominal\n'
                    'naics: dcid:NAICS/{naics}\n'
                    'statType: dcid:measuredValue\n\n')

        with open('States_gdp_industry_statvars.mcf', 'w') as mcf_f:
            for naics_code in self.clean_df['NAICS'].unique():
                code_title = naics_code[38:]
                code = code_title.replace('_', '-')
                # Apply specific replacements to align with historical NAICS DCID patterns
                code = code.replace("311-316-322-326", "311-316_322-326")
                code = code.replace("321-327-339", "321_327-339")
                mcf_f.write(mcf_temp.format(title=code_title, naics=code))


def main(_):
    """Runs the program."""
    loader = StateGDPIndustryDataLoader()
    # loader.download_data()
    loader.process_data()
    loader.save_csv()
    loader.generate_mcf()


if __name__ == '__main__':
    app.run(main)
