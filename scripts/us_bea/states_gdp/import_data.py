# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Pulls data from the US Bureau of Economic Analysis (BEA) on quarterly GDP
per US state. Saves output as a CSV file.

The output CSV contains three measurement methods of GDP per quarter per US
state from the years 2005 onwards, based on the available file in the input folder.
    Typical usage:

    python3 import_data.py --latest_year 2024 --input_folder my_data
    or
    python3 import_data.py --input_folder my_data # To automatically get the latest year
"""
import csv
import io
import os
import re
from urllib.request import urlopen
from absl import app
from absl import flags
from absl import logging
import pandas as pd

logging.set_verbosity(logging.INFO)

# Suppress annoying pandas DF copy warnings.
pd.options.mode.chained_assignment = None

FLAGS = flags.FLAGS
flags.DEFINE_integer('latest_year', None,
                     'The latest year to look for in the filename (optional).')


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
    _QUARTER_MONTH_MAP = {'Q1': '03', 'Q2': '06', 'Q3': '09', 'Q4': '12'}

    def __init__(self):
        """Initializes instance, assigning member data frames to None."""
        self.raw_df = None
        self.clean_df = None

    def _find_gdp_file_in_folder(self,
                                 input_folder,
                                 file_pattern,
                                 target_year=None):
        """Finds the latest file in the specified folder matching a given pattern.

        Args:
            input_folder (str): The path to the directory to search.
            file_pattern (str): A regular expression pattern to match filenames.
                            It should contain a capturing group for the end year.
            target_year (int, optional): The specific end year to prioritize. Defaults to None.

        Returns:
            str: The name of the file found.

        Raises:
            FileNotFoundError: If no file matching the pattern is found in the folder.
        """
        matching_files = {}
        for filename in os.listdir(input_folder):
            match = re.match(file_pattern, filename)
            if match:
                try:
                    end_year = int(match.group(2))
                    matching_files[filename] = end_year
                except IndexError:
                    "Log as a warning if group(2) is missing. This indicates a potential  mismatch between the file_pattern and the expected structure"
                    logging.warning(
                        f"Warning: Year capturing group (group 2) not found in "
                        f"pattern '{file_pattern}' for file '{filename}'. Skipping."
                    )
                except ValueError:
                    " Log as a warning if the captured year cannot be converted to an integer "
                    logging.warning(
                        f"Warning: Could not convert captured year to integer for file '{filename}'. Skipping."
                    )
                    continue

        if not matching_files:
            raise FileNotFoundError(
                f"Error: No file matching pattern '{file_pattern}' found in '{input_folder}'."
            )

        if target_year:
            candidate_files = {
                k: v for k, v in matching_files.items() if v == target_year
            }
            if candidate_files:
                return next(iter(candidate_files))
            else:
                logging.warning(
                    f"Warning: No file found ending with year {target_year} in '{input_folder}'. "
                    f"Falling back to the file with the latest end year available."
                )

        return max(matching_files, key=matching_files.get)

    def process_data(self, raw_data=None, input_folder='input_data'):
        """Processes the state quarterly GDP data from the input folder.

        Args:
            raw_data: Raw data to process (optional, if not provided, it will
                      look for the latest file in the input folder).
            input_folder: The folder containing the input CSV files. If None,
                          it defaults to the value of the --input_folder flag.
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
                _STATE_QUARTERLY_GDP_FILE_PATTERN = r'SQGDP1__ALL_AREAS_(\d{4})_(\d{4})\.csv'
                self._input_file = self._find_gdp_file_in_folder(
                    input_folder, _STATE_QUARTERLY_GDP_FILE_PATTERN,
                    FLAGS.latest_year)
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
            if 'GeoName' in df.columns:
                df = df[df['GeoName'].isin(self.US_STATES)]
            else:
                logging.warning(
                    "Warning: 'GeoName' column not found, skipping state filtering."
                )
            all_quarters = [
                q for q in df.columns if re.match(r'....:Q.', str(q))
            ]
            if all_quarters:
                df_melted = pd.melt(df,
                                    id_vars=['GeoFIPS', 'Unit'],
                                    value_vars=all_quarters,
                                    var_name='Quarter')
                df_melted['Quarter'] = df_melted['Quarter'].apply(
                    self.date_to_obs_date)
                df_melted['GeoId'] = df_melted['GeoFIPS'].apply(
                    self.convert_geoid)
                one_million = 1000000
                self.clean_df = df_melted[
                    df_melted['Unit'] ==
                    'Millions of chained 2017 dollars'].copy()
                if not self.clean_df.empty:
                    self.clean_df = self.clean_df.set_index(
                        ['GeoId', 'Quarter'])
                    self.clean_df['chained_2017_dollars'] = self.clean_df[
                        'value'].astype(float)
                    self.clean_df['chained_2017_dollars'] *= one_million

                quality_indices = df_melted[df_melted['Unit'] ==
                                            'Quantity index'].copy()
                if not quality_indices.empty:
                    quality_indices['GeoId'] = quality_indices['GeoFIPS'].apply(
                        self.convert_geoid)
                    quality_indices = quality_indices.set_index(
                        ['GeoId', 'Quarter'])
                    self.clean_df['quantity_index'] = quality_indices[
                        'value'].reindex(
                            self.clean_df.index).values.astype(float)

                current_usd = df_melted[df_melted['Unit'] ==
                                        'Millions of current dollars'].copy()
                if not current_usd.empty:
                    current_usd['GeoId'] = current_usd['GeoFIPS'].apply(
                        self.convert_geoid)
                    current_usd = current_usd.set_index(['GeoId', 'Quarter'])
                    self.clean_df['current_dollars'] = current_usd[
                        'value'].reindex(self.clean_df.index).values.astype(
                            float) * one_million

                self.clean_df = self.clean_df.drop(['GeoFIPS', 'Unit', 'value'],
                                                   axis=1,
                                                   errors='ignore')

            else:
                logging.warning(
                    "Warning: No quarter columns found for melting.")
        else:
            logging.fatal("No data to process.")

    @classmethod
    def date_to_obs_date(cls, date):
        """Converts date format from YEAR:QUARTER to YEAR-MONTH.

        Args:
            date: A string representing the date in "YEAR:QUARTER" format (e.g., "2024:Q1").

        Returns:
            A string representing the date in "YEAR-MONTH" format (e.g., "2024-03" for Q1).
        """
        return date[:4] + '-' + cls._QUARTER_MONTH_MAP[date[5:]]

    @staticmethod
    def convert_geoid(fips_code):
        fips_code = fips_code.replace('"', '').replace(' ', '')
        return 'geoId/' + fips_code[:2]

    def save_csv(self, filename='states_gdp.csv'):
        """Saves instance data frame to specified CSV file."""
        if self.clean_df is None:
            raise ValueError(
                'Uninitialized value of clean data frame. Please check process_data.'
            )

        # Reset the index to make 'GeoId' and 'Quarter' regular columns
        self.clean_df = self.clean_df.reset_index()
        new_index = pd.Index(range(0, len(self.clean_df) * 3, 3))
        self.clean_df.index = new_index
        desired_order = [
            'Quarter', 'GeoId', 'chained_2017_dollars', 'quantity_index',
            'current_dollars'
        ]
        self.clean_df = self.clean_df[desired_order]
        self.clean_df.to_csv(filename, index=True)
        logging.info(self.clean_df)


def main(argv):
    """Runs the program."""
    loader = StateGDPDataLoader()
    loader.process_data()
    loader.save_csv()


if __name__ == '__main__':
    app.run(main)
