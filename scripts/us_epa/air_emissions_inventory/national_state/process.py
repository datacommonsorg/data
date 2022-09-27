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
from absl import app, flags
import pandas as pd
import numpy as np

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))
from common.us_air_pollution_emission_trends import USAirPollutionEmissionTrends

sys.path.insert(
    1, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from util.statvar_dcid_generator import get_statvar_dcid

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))

from metadata import (SHEETS_NATIONAL, SKIPFOOT_OTHERS_NATIONAL,
                      SKIPFOOT_PM_NATIONAL, SKIPHEAD_AMMONIA_NATIONAL,
                      SKIPHEAD_OTHERS_NATIONAL, SHEET_STATE, SOURCE_POLLUTANT)

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
        sv_list.sort()

        for sv in sv_list:
            sv_property = sv.split("-")
            sv_checker['emissionSource'] = sv_property[0]
            sv_checker['emittedThing'] = 'dcs:' + sv_property[1]
            generated_sv = get_statvar_dcid(sv_checker)

            source = '\nemissionSource: dcs:' + sv_property[0]
            pollutant = '\nemittedThing: dcs:' + sv_property[1]

            sv_replacement[sv] = generated_sv
            mcf[sv] = self._mcf_template.format(
                sv=generated_sv, source=source, pollutant=pollutant) + "\n"

        self._final_df.loc[:, ('SV')] = self._final_df['SV'].replace(
            sv_replacement, regex=True)
        self._final_df.loc[:,
                           ('mcf')] = self._final_df['mcf'].replace(mcf,
                                                                    regex=True)

    def _state_emissions(self, file_path: str) -> pd.DataFrame:
        """
        Reads the file for state emissions data and cleans it for concatenation
        in Final CSV.

        Args:
            file_path (str): path to excel file as the input

        Returns:
            df (pd.DataFrame): provides the cleaned df as output
        """
        df = pd.read_excel(file_path, SHEET_STATE, skiprows=1, header=0)
        # Adding geoId/ and making the State FIPS code of 2 numbers
        # Eg - 1 -> geoId/01
        df['geo_Id'] = [f'{x:02}' for x in df['State FIPS']]
        df['geo_Id'] = 'geoId/' + df['geo_Id']
        # Dropping Unwanted Columns
        df = df.drop(columns=['State FIPS', 'State', 'Tier 1 Code'])
        df = self.data_standardize(df, 'Pollutant', SOURCE_POLLUTANT)
        df = self.data_standardize(df, 'Tier 1 Description', SOURCE_POLLUTANT)
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

    def _national_emissions(self, file_path: str) -> pd.DataFrame:
        """
        Reads the file for national emissions data and cleans it for concatenation
        in Final CSV.

        Args:
            file_path (str): path to excel file as the input

        Returns:
            df (pd.DataFrame): provides the cleaned df as output
        """
        final_df = pd.DataFrame()
        # Reading different sheets of Excel one at a time
        for sheet in SHEETS_NATIONAL:
            # Number of rows to skip vary by sheet, inserting if-else for the same.
            skiphead = SKIPHEAD_AMMONIA_NATIONAL if sheet == 'NH3' else SKIPHEAD_OTHERS_NATIONAL
            skipfoot = SKIPFOOT_PM_NATIONAL if sheet in [
                'PM10Primary', 'PM25Primary'
            ] else SKIPFOOT_OTHERS_NATIONAL
            df = pd.read_excel(file_path,
                               sheet,
                               skiprows=skiphead,
                               skipfooter=skipfoot,
                               header=0)
            # NA values are present as 'NA ' and also as '', removing 'NA '
            # to process the column.
            df = df.replace('NA ', np.NaN)
            # Dropping rows with only Null Values.
            df = df.dropna(how='all')
            # Dropping unwanted rows left.
            df = df.drop(df[
                (df['Source Category'] == 'Total') |
                (df['Source Category'] == 'Total without wildfires') |
                (df['Source Category'] == 'Miscellaneous without wildfires') |
                (df['Source Category'] == 'Total without miscellaneous') |
                (df['Source Category'] == 'Miscellaneous')].index)
            # Addition of pollutant type to the df by taking sheet name.
            df['pollutant'] = sheet
            df = self.data_standardize(df, 'pollutant', SOURCE_POLLUTANT)
            df = self.data_standardize(df, 'Source Category', SOURCE_POLLUTANT)
            df['SV_TEMP'] = df['Source Category'] + "-" + df['pollutant']
            df = df.drop(columns=['Source Category', 'pollutant'])
            # Changing the years present as columns into row values.
            df = df.melt(id_vars=['SV_TEMP'],
                         var_name='year',
                         value_name='observation')
            final_df = pd.concat([final_df, df])

        final_df['geo_Id'] = 'country/USA'
        final_df_agg = self.aggregate_columns(
            final_df, ['PrescribedFire', 'Wildfire', 'Miscellaneous'],
            'dcAggregate/EPA_NationalEmissionInventory')
        final_df['Measurement_Method'] = 'EPA_NationalEmissionInventory'
        final_df = pd.concat([final_df, final_df_agg])
        return final_df

    def _parse_source_files(self):
        """
        Reads the files present in the input folder. Calls the appropriate
        function based on the type of file and procceses it.

        Args:
            None

        Returns:
            None
        """
        source_file_to_method_mapping = {
            "national_tier1_caps": self._national_emissions,
            "state_tier1_caps": self._state_emissions
        }
        for file_path in self._input_files:
            # Taking the File name out of the complete file address
            # Used -1 to pickup the last part which is file name
            # Read till -5 inorder to remove the .xlsx extension
            file_name = file_path.split("/")[-1][:-5]
            df = source_file_to_method_mapping[file_name](file_path)
            self._final_df = pd.concat([self._final_df, df])

        self._final_df = self._final_df.sort_values(
            by=['geo_Id', 'year', 'SV_TEMP', 'observation'])
        self._final_df['observation'].replace('', np.nan, inplace=True)
        self._final_df.dropna(subset=['observation'], inplace=True)
        self._final_df['observation'] = self._final_df['observation'].astype(
            float) * _SCALING_FACTOR
        self._add_sv_and_mcf_column_to_final_df()


def main(_):
    input_path = FLAGS.input_path
    try:
        ip_files = os.listdir(input_path)
    except Exception:
        download_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "download.py")
        os.system("python " + download_file)
        ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]
    output_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "output")
    # Defining Output Files
    csv_name = "airpollution_emission_trends_tier1.csv"
    mcf_name = "airpollution_emission_trends_tier1.mcf"
    tmcf_name = "airpollution_emission_trends_tier1.tmcf"
    cleaned_csv_path = os.path.join(output_file_path, csv_name)
    mcf_path = os.path.join(output_file_path, mcf_name)
    tmcf_path = os.path.join(output_file_path, tmcf_name)
    loader = USAirPollutionEmissionTrendsNationalAndState(
        ip_files, cleaned_csv_path, mcf_path, tmcf_path)
    loader.generate_csv()
    loader.generate_mcf()
    loader.generate_tmcf()


if __name__ == "__main__":
    app.run(main)
