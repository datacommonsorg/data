# Copyright 2022 Google LLC
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
This Python Script Load the datasets, cleans it
and generates cleaned CSV, MCF, TMCF file.
"""

import os
import sys
from absl import app, flags, logging
import pandas as pd
import numpy as np
import re

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))
from common.us_air_pollution_emission_trends import USAirPollutionEmissionTrends

# Add the path to the 'util' directory to sys.path
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../../../../../data/util')))

# importing from util
from statvar_dcid_generator import get_statvar_dcid

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))

from metadata import (SHEETS_NATIONAL, SKIPHEAD_AMMONIA_NATIONAL,
                      SKIPHEAD_OTHERS_NATIONAL, SHEET_STATE, SOURCE, POLLUTANT)

FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

# Data provided in 1000s of Tons.
_SCALING_FACTOR = 1000


class USAirPollutionEmissionTrendsNationalAndState(USAirPollutionEmissionTrends
                                                  ):
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    _mcf_template = ("Node: dcid:{sv}\n"
                     "typeOf: dcs:StatisticalVariable\n"
                     "populationType: dcs:Emissions\n"
                     "emissionSourceType: dcs:NonBiogenicEmissionSource\n"
                     "measurementQualifier: dcs:Annual{source}{pollutant}\n"
                     "statType: dcs:measuredValue\n"
                     "measuredProperty: dcs:amount\n")

    _tmcf_template = (
        "Node: E:airpollution_emission_trends_tier1->E0\n"
        "typeOf: dcs:StatVarObservation\n"
        "variableMeasured: C:airpollution_emission_trends_tier1->SV\n"
        "measurementMethod: C:airpollution_emission_trends_tier1->"
        "Measurement_Method\n"
        "observationAbout: C:airpollution_emission_trends_tier1->geo_Id\n"
        "observationDate: C:airpollution_emission_trends_tier1->year\n"
        "unit: Ton\n"
        "value: C:airpollution_emission_trends_tier1->observation\n")

    def _add_sv_and_mcf_column_to_final_df(self):
        """
        Generates the MCF data from the provided SV columns
        based on the properties.

        Args:
            None

        Returns:
            None
        """
        try:
            self._final_df['SV'] = self._final_df['SV_TEMP']
            self._final_df['mcf'] = self._final_df['SV_TEMP']

            # Created to store current SV values as keys and names generated
            # from sv generator as values for replacement.
            sv_replacement = {}
            # Created to store Property and Values for each unique SV.
            mcf = {}
            sv_checker = {
                "typeOf": "dcs:StatisticalVariable",
                "populationType": "dcs:Emissions",
                "emissionSourceType": "dcs:NonBiogenicEmissionSource",
                "measurementQualifier": "dcs:Annual",
                "statType": "dcs:measuredValue",
                "measuredProperty": "dcs:amount"
            }

            sv_list = pd.unique(self._final_df['SV'])
            sv_list = [
                item for item in sv_list if not (pd.isnull(item)) == True
            ]
            logging.info("===========sv List==========" + str(sv_list))
            sv_list.sort()

            for sv in sv_list:
                sv_property = sv.split("-")
                sv_checker['emissionSource'] = sv_property[0]
                sv_checker['emittedThing'] = 'dcs:' + sv_property[1]
                generated_sv = get_statvar_dcid(sv_checker)

                # Split the generated_sv by underscore to check for 'Total'
                generated_sv_parts = generated_sv.split('_')

                # Check for the presence of 'Total' in the parts
                if 'Total' in generated_sv_parts:
                    # If 'Total' is found, remove it from the parts
                    generated_sv_parts = [
                        part for part in generated_sv_parts if part != 'Total'
                    ]

                # Reconstruct the generated_sv without 'Total' if it was removed
                cleaned_generated_sv = '_'.join(generated_sv_parts)

                # Skip emissionSource in the mcf if 'Total' is in the generated_sv
                if 'Total' in sv_property[0]:
                    source = ''  # Don't add emissionSource if 'Total' is part of emissionSource
                else:
                    source = '\nemissionSource: dcs:' + sv_property[0]

                # Construct the pollutant string
                pollutant = '\nemittedThing: dcs:' + sv_property[1]

                # Update the replacement mappings
                sv_replacement[sv] = cleaned_generated_sv
                mcf[sv] = self._mcf_template.format(sv=cleaned_generated_sv,
                                                    source=source,
                                                    pollutant=pollutant) + "\n"

            # Replace SV and mcf columns with the newly generated data
            self._final_df.loc[:, ('SV')] = self._final_df['SV'].replace(
                sv_replacement, regex=True)
            self._final_df.loc[:, ('mcf')] = self._final_df['mcf'].replace(
                mcf, regex=True)
        except Exception as e:
            logging.fatal(f"Missing column during SV and MCF generation: {e}")

    def _state_emissions(self, file_path: str) -> pd.DataFrame:
        """
        Reads the file for state emissions data and cleans it for concatenation
        in Final CSV.

        Args:
            file_path (str): path to excel file as the input

        Returns:
            df (pd.DataFrame): provides the cleaned df as output
        """
        try:
            df = pd.read_excel(file_path, SHEET_STATE, skiprows=1, header=0)
            # Adding geoId/ and making the State FIPS code of 2 numbers
            # Eg - 1 -> geoId/01
            df['geo_Id'] = [f'{x:02}' for x in df['State FIPS']]
            df['geo_Id'] = 'geoId/' + df['geo_Id']
            # Dropping Unwanted Columns
            df = df.drop(columns=['State FIPS', 'State', 'Tier 1 Code'])
            # Convert 'Tier 1 Description' and 'Pollutant' columns to uppercase
            df['Tier 1 Description'] = df['Tier 1 Description'].str.upper()
            df['Pollutant'] = df['Pollutant'].str.upper()
            df = self.data_standardize(df, 'Pollutant', POLLUTANT)
            df = self.data_standardize(df, 'Tier 1 Description', SOURCE)
            df['SV_TEMP'] = df['Tier 1 Description'] + '-' + df['Pollutant']
            df = df.drop(columns=['Tier 1 Description', 'Pollutant'])
            # Changing the years present as columns into row values.
            df = df.melt(id_vars=['SV_TEMP', 'geo_Id'],
                         var_name='year',
                         value_name='observation')
            df['year'] = (df['year'].str[-2:]).astype(int)
            # As 2001 is available as 01 and 1999 is available as 99,
            # Putting a logic to change it to proper year
            df['year'] = df['year'] + np.where(df['year'] >= 90, 1900, 2000)
            # Making copy and using group by to get Aggregated Values.
            df_agg = self.aggregate_columns(
                df, ['PrescribedFire', 'Wildfire', 'Miscellaneous'],
                'dcAggregate/EPA_NationalEmissionInventory')
            df['Measurement_Method'] = 'EPA_NationalEmissionInventory'
            df = pd.concat([df, df_agg])
            return df
        except FileNotFoundError as e:
            logging.fatal(f"File not found: {file_path}")
        except Exception as e:
            logging.fatal(f"Missing column in state emissions file: {e}")

    def _national_emissions(self, file_path: str) -> pd.DataFrame:
        """
        Reads the file for national emissions data and cleans it for concatenation
        in Final CSV.

        Args:
            file_path (str): path to excel file as the input

        Returns:
            df (pd.DataFrame): provides the cleaned df as output
        """
        try:
            final_df = pd.DataFrame()
            # Reading different sheets of Excel one at a time
            for sheet in SHEETS_NATIONAL:
                # Number of rows to skip vary by sheet, inserting if-else for the same.
                skiphead = SKIPHEAD_AMMONIA_NATIONAL if sheet == 'NH3' else SKIPHEAD_OTHERS_NATIONAL
                skipfoot = 1
                df = pd.read_excel(file_path,
                                   sheet,
                                   skiprows=skiphead,
                                   skipfooter=skipfoot,
                                   header=0)
                # NA values are present as 'NA ' and also as '', removing 'NA '
                # to process the column.
                df = df.replace('NA ', np.nan)
                # Dropping rows with only Null Values.
                df = df.dropna(how='all')
                # Clean the 'Source Category' column to handle any formatting issues
                df['Source Category'] = df['Source Category'].str.strip()
                # Drop only specific unwanted rows, ensuring important ones are retained
                df = df.drop(
                    df[(df['Source Category'] == 'Miscellaneous') |
                       (df['Source Category'] == 'Total without wildfires') |
                       (df['Source Category'] ==
                        'Miscellaneous without wildfires') |
                       (df['Source Category'] == 'Total without miscellaneous'
                       )].index)

                # Addition of pollutant type to the df by taking sheet name.
                df['pollutant'] = sheet
                df = self.data_standardize(df, 'pollutant', POLLUTANT)
                df = self.data_standardize(df, 'Source Category', SOURCE)

                df['SV_TEMP'] = df['Source Category'] + "-" + df['pollutant']
                df = df.drop(columns=['Source Category', 'pollutant'])
                # Changing the years present as columns into row values.
                df = df.melt(id_vars=['SV_TEMP'],
                             var_name='year',
                             value_name='observation')
                final_df = pd.concat([final_df, df])

            final_df['geo_Id'] = 'country/USA'
            final_df['Measurement_Method'] = 'EPA_NationalEmissionInventory'
            return final_df
        except FileNotFoundError as e:
            logging.fatal(f"File not found: {file_path}")
        except Exception as e:
            logging.fatal(f"Missing column in national emissions file: {e}")

    def _parse_source_files(self):
        """
        Reads the files present in the input folder. Calls the appropriate
        function based on the type of file and procceses it.

        Args:
            None

        Returns:
            None
        """
        try:
            logging.info("Starting to parse source files.")
            # Define regex patterns for file identification
            source_file_to_method_mapping = {
                r".*state.*":
                    self._state_emissions,  # Matches files containing "state"
                r".*national.*":
                    self.
                    _national_emissions  # Matches files containing "national"
            }
            for file_path in self._input_files:
                # Extract filename without extension
                file_name = file_path.split("/")[-1][:-5]
                logging.info(f"Processing file: {file_name}")
                # Initialize a variable to store the matched method
                matched_method = None
                # Check if the filename matches any pattern
                for pattern, method in source_file_to_method_mapping.items():
                    if re.match(pattern, file_name):
                        matched_method = method
                        break  # Exit the loop as soon as a match is found
                # If no match is found, log the error and break the loop
                if not matched_method:
                    logging.fatal(
                        f"No parsing method found for file: {file_name}. Stopping execution."
                    )
                    break

                # Process the file using the matched method
                df = matched_method(file_path)
                self._final_df = pd.concat([self._final_df, df])
                logging.info(f"Successfully processed file: {file_name}")

            self._final_df = self._final_df.sort_values(
                by=['geo_Id', 'year', 'SV_TEMP', 'observation'])
            self._final_df['observation'].replace('', np.nan, inplace=True)
            self._final_df.dropna(subset=['observation'], inplace=True)
            self._final_df.dropna(subset=['SV_TEMP'], inplace=True)
            self._final_df['observation'] = self._final_df[
                'observation'].astype(float) * _SCALING_FACTOR
            self._add_sv_and_mcf_column_to_final_df()
        except Exception as e:
            logging.fatal(f"Error parsing source files: {e}")
            raise


def main(_):
    input_path = FLAGS.input_path
    logging.info(f"Input path: {input_path}")
    try:
        ip_files = os.listdir(input_path)
        logging.info(f"Found {len(ip_files)} files in input path.")

        ip_files = [input_path + os.sep + file for file in ip_files]
        output_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "output")
        # Defining Output Files
        csv_name = "airpollution_emission_trends_tier1.csv"
        mcf_name = "airpollution_emission_trends_tier1.mcf"
        tmcf_name = "airpollution_emission_trends_tier1.tmcf"
        cleaned_csv_path = os.path.join(output_file_path, csv_name)
        mcf_path = os.path.join(output_file_path, mcf_name)
        tmcf_path = os.path.join(output_file_path, tmcf_name)

        # Create output directory if it doesn't exist
        if not os.path.exists(output_file_path):
            os.makedirs(output_file_path)
            logging.info(f"Created output directory: {output_file_path}")

        loader = USAirPollutionEmissionTrendsNationalAndState(
            ip_files, cleaned_csv_path, mcf_path, tmcf_path)

        try:
            logging.info("Starting to generate CSV.")
            loader.generate_csv()
            logging.info(f"Cleaned CSV generated: {cleaned_csv_path}")

            logging.info("Starting to generate MCF.")
            loader.generate_mcf()
            logging.info(f"MCF file generated: {mcf_path}")

            logging.info("Starting to generate TMCF.")
            loader.generate_tmcf()
            logging.info(f"TMCF file generated: {tmcf_path}")
        except Exception as e:
            logging.fatal(f"Error generating outputs: {e}")
            raise

    except Exception:
        logging.fatal(
            f"There are no files in the input path: {input_path} to download.")
        raise


if __name__ == "__main__":
    app.run(main)
