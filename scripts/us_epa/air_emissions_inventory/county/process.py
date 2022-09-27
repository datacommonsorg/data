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
import logging
import pandas as pd
import numpy as np

from absl import app, flags

sys.path.insert(
    1, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))
from util.statvar_dcid_generator import get_statvar_dcid

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..')))
from common.us_air_pollution_emission_trends import USAirPollutionEmissionTrends
from metadata import SOURCE_POLLUTANT, SOURCE_CATEGORY

sys.path.insert(
    1, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")


class USAirPollutionEmissionTrendsCounty(USAirPollutionEmissionTrends):
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    _mcf_template = (
        "Node: dcid:{sv}\n"
        "typeOf: dcs:StatisticalVariable\n"
        "populationType: dcs:Emissions\n"
        "measurementQualifier: dcs:Annual{source}{pollutant}{emissiontype}\n"
        "statType: dcs:measuredValue\n"
        "measuredProperty: dcs:amount\n")

    _tmcf_template = (
        "Node: E:airpollution_emission_trends_county_tier1->E0\n"
        "typeOf: dcs:StatVarObservation\n"
        "variableMeasured: C:airpollution_emission_trends_county_tier1->SV\n"
        "measurementMethod: C:airpollution_emission_trends_county_tier1->"
        "measurement_method\n"
        "observationAbout: C:airpollution_emission_trends_county_tier1->geo_Id\n"
        "observationDate: C:airpollution_emission_trends_county_tier1->year\n"
        "unit: Ton\n"
        "value: C:airpollution_emission_trends_county_tier1->observation\n")

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
        mcf = {}
        # Created to store Property and Values for each unique SV.
        sv_checker = {
            "typeOf": "dcs:StatisticalVariable",
            "populationType": "dcs:Emissions",
            "measurementQualifier": "dcs:Annual",
            "statType": "dcs:measuredValue",
            "measuredProperty": "dcs:amount"
        }

        sv_list = pd.unique(self._final_df['SV'])
        sv_list.sort()

        for sv in sv_list:
            sv_property = sv.split("_")

            if ("OtherIndustrialProcesses" in sv_property[-3] or
                    "MiscellaneousEmissionSource" in sv_property[-3] or
                    "FuelCombustionOther" in sv_property[-3]):
                source = ('\nemissionSource: dcs:' + sv_property[-4] + "_" +
                          sv_property[-3])
                sv_checker['emissionSource'] = 'dcs:' + sv_property[
                    -4] + "_" + sv_property[-3]
            else:
                source = '\nemissionSource: dcs:' + sv_property[-3]
                sv_checker['emissionSource'] = sv_property[-3]
            if "BiogenicEmissionSource" in sv_property[-2]:
                emissiontype = '\nemissionSourceType: dcs:' + sv_property[-2]
                sv_checker['emissionSourceType'] = sv_property[-2]
            pollutant = '\nemittedThing: dcs:' + sv_property[-1]
            sv_checker['emittedThing'] = 'dcs:' + sv_property[-1]
            generated_sv = get_statvar_dcid(sv_checker)
            if (generated_sv != sv):
                sv_replacement[sv] = generated_sv

            mcf[sv] = self._mcf_template.format(
                sv=generated_sv,
                source=source,
                pollutant=pollutant,
                emissiontype=emissiontype) + "\n"

        self._final_df.loc[:, ('SV')] = self._final_df['SV'].replace(
            sv_replacement, regex=True)
        self._final_df.loc[:,
                           ('mcf')] = self._final_df['mcf'].replace(mcf,
                                                                    regex=True)

    def _county_emissions(self, file_path: str, year: str) -> pd.DataFrame:
        """
        Reads the file for state emissions data and cleans it for concatenation
        in Final CSV.

        Args:
            file_path (str): path to excel file as the input

        Returns:
            df (pd.DataFrame): provides the cleaned df as output
        """
        df = pd.read_csv(file_path, header=0, encoding='utf-8')
        df['year'] = year
        df_final = pd.DataFrame()
        df['geo_Id'] = ''

        df = self.data_standardize(df, 'POLLUTANT', SOURCE_POLLUTANT)
        df = self.data_standardize(df, 'TIER', SOURCE_CATEGORY)

        df = df.rename(columns={'EMISSIONS': 'observation'})
        df['geo_Id'] = 'geoId/' + (df['STATE_FIPS'].map(str)).str.zfill(2)\
                    + (df['COUNTY_FIPS'].map(str)).str.zfill(3)
        df['Measurement_Method'] = 'EPA_NationalEmissionInventory_Tier1Summary'
        # df = process_file(df)
        df['emissionsourcetype'] = np.where(df['TIER'] == 'NaturalResources',
                                            'BiogenicEmissionSource',
                                            'NonBiogenicEmissionSource')
        df['SV_TEMP'] = 'Annual_Amount_Emissions_' + df['TIER'] +'_'+\
            df['emissionsourcetype'] +'_'+ df['POLLUTANT']
        # Making copy and using group by to get Aggregated Values.
        df_agg = self.aggregate_columns(
            df, ['NaturalResources', 'Miscellaneous'],
            'dcAggregate/EPA_NationalEmissionInventory_Tier1Summary')
        df = pd.concat([df, df_agg])
        df = df.drop(columns=[
            'STATE', 'STATE_FIPS', 'UNIT OF MEASURE', 'POLLUTANT TYPE',
            'COUNTY_FIPS', 'POLLUTANT', 'TIER', 'emissionsourcetype', 'COUNTY'
        ])
        return df

    def _parse_source_files(self):
        """
        Reads the files present in the input folder. Calls the appropriate
        function based on the type of file and procceses it.

        Args:
            None

        Returns:
            None
        """
        sv_list = []
        for file_path in self._input_files:
            # Taking the year out of the complete file address
            # Used -18 and -14 to pickup year which is file name
            # and get the year.
            year = file_path[-18:-14].strip()
            df = self._county_emissions(file_path, year)
            self._final_df = pd.concat([self._final_df, df])
            sv_list += self._final_df['SV_TEMP'].to_list()

        self._final_df = self._final_df.sort_values(
            by=['geo_Id', 'year', 'SV_TEMP', 'observation'])
        self._final_df['observation'].replace('', np.nan, inplace=True)
        self._final_df.dropna(subset=['observation'], inplace=True)
        self._add_sv_and_mcf_column_to_final_df()


def main(_):
    ip_files = ""
    input_path = FLAGS.input_path
    try:
        ip_files = os.listdir(input_path)
    except Exception:
        logging.info("Run the download.py script first.")
        sys.exit(1)
    ip_files = [input_path + os.sep + file for file in ip_files]

    output_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "output")
    # Defining Output Files
    csv_name = "airpollution_emission_trends_county_tier1.csv"
    mcf_name = "airpollution_emission_trends_county_tier1.mcf"
    tmcf_name = "airpollution_emission_trends_county_tier1.tmcf"
    cleaned_csv_path = os.path.join(output_file_path, csv_name)
    mcf_path = os.path.join(output_file_path, mcf_name)
    tmcf_path = os.path.join(output_file_path, tmcf_name)
    loader = USAirPollutionEmissionTrendsCounty(ip_files, cleaned_csv_path, mcf_path,\
        tmcf_path)
    loader.generate_csv()
    loader.generate_mcf()
    loader.generate_tmcf()


if __name__ == "__main__":
    app.run(main)
