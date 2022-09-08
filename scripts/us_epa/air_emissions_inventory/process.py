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

from asyncio.log import logger
import os
import sys
from absl import app, flags
import pandas as pd
import numpy as np

sys.path.insert(
    1, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from util.statvar_dcid_generator import get_statvar_dcid

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))

from metadata import (sourcegroups, sourcepollutantmetadata, sheets_national,
                      skipfoot_others_national, skipfoot_pm_national,
                      skiphead_ammonia_national, skiphead_others_national,
                      sheet_state)

FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

# Data provided in 1000s of Tons.
_SCALING_FACTOR = 1000

_MCF_TEMPLATE = ("Node: dcid:{pv1}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Emissions\n"
                 "emissionSourceType: dcs:NonBiogenicEmissionSource\n"
                 "measurementQualifier: dcs:Annual{pv2}{pv3}\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:amount\n")

_TMCF_TEMPLATE = (
    "Node: E:airpollution_emission_trends_tier1->E0\n"
    "typeOf: dcs:StatVarObservation\n"
    "variableMeasured: C:airpollution_emission_trends_tier1->SV\n"
    "measurementMethod: C:airpollution_emission_trends_tier1->"
    "Measurement_Method\n"
    "observationAbout: C:airpollution_emission_trends_tier1->geo_Id\n"
    "observationDate: C:airpollution_emission_trends_tier1->year\n"
    "unit: Ton\n"
    "value: C:airpollution_emission_trends_tier1->observation\n")


class USAirPollutionEmissionTrends:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    def __init__(self, input_files: list, csv_file_path: str,
                 mcf_file_path: str, tmcf_file_path: str) -> None:
        self._input_files = input_files
        self._cleaned_csv_file_path = csv_file_path
        self._mcf_file_path = mcf_file_path
        self._tmcf_file_path = tmcf_file_path

    def aggregate_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates the columns based on SV

        Args: 
            df (pd.DataFrame): df as the input, to aggregate values

        Returns:
            df (pd.DataFrame): modified df as output
        """
        # Dropping the rows which contain PrescribedFire, Wildfire or Miscellaneous.
        # As they are not a part of StationaryFuelCombustion,
        # IndustrialAndOtherProcesses or Transportation group.
        df = df.drop(df[(df['SV'].str.contains('PrescribedFire')) |
                        (df['SV'].str.contains('Wildfire')) |
                        (df['SV'].str.contains('Miscellaneous'))].index)
        # Replacing the columns for grouping as per
        # StationaryFuelCombustion -    FuelCombustionElectricUtility
        #                               FuelCombustionIndustrial
        #                               EPA_FuelCombustionOther
        # IndustrialAndOtherProcesses - ChemicalAndAlliedProductManufacturing
        #                               MetalsProcessing
        #                               PetroleumAndRelatedIndustries
        #                               EPA_OtherIndustrialProcesses
        #                               SolventUtilization
        #                               StorageAndTransport
        #                               WasteDisposalAndRecycling
        # Transportation -              OnRoadVehicles
        #                               NonRoadEnginesAndVehicles
        df.loc[:, ('SV')] = df['SV'].replace(sourcegroups, regex=True)
        df = df.groupby(['year', 'geo_Id', 'SV']).sum().reset_index()
        df['Measurement_Method'] = 'dcAggregate/EPA_NationalEmissionInventory'
        return df

    def data_standardize(self, df: pd.DataFrame,
                         column_name: str) -> pd.DataFrame:
        """
        Replaces values of a single column into true values
        from metadata returns the DF.

        Args:
            df (pd.DataFrame): df as the input, to change column values

        Returns:
            df (pd.DataFrame): modified df as output
        """
        df = df.replace({column_name: sourcepollutantmetadata})
        return df

    def state_emissions(self, file_path: str) -> pd.DataFrame:
        """
        Reads the file for state emissions data and cleans it for concatenation
        in Final CSV.

        Args:
            file_path (str): path to excel file as the input

        Returns:
            df (pd.DataFrame): provides the cleaned df as output
        """
        df = pd.read_excel(file_path, sheet_state, skiprows=1, header=0)
        # Adding geoId/ and making the State FIPS code of 2 numbers
        # Eg - 1 -> geoId/01
        df['geo_Id'] = [f'{x:02}' for x in df['State FIPS']]
        df['geo_Id'] = 'geoId/' + df['geo_Id']
        # Dropping Unwanted Columns
        df = df.drop(columns=['State FIPS', 'State', 'Tier 1 Code'])
        df = self.data_standardize(df, 'Pollutant')
        df = self.data_standardize(df, 'Tier 1 Description')
        df['SV'] = df['Tier 1 Description'] + '-' + df['Pollutant']
        df = df.drop(columns=['Tier 1 Description', 'Pollutant'])
        # Changing the years present as columns into row values.
        df = df.melt(id_vars=['SV', 'geo_Id'],
                     var_name='year',
                     value_name='observation')
        df['year'] = (df['year'].str[-2:]).astype(int)
        # As 2001 is available as 01 and 1999 is available as 99,
        # Putting a logic to change it to proper year
        df['year'] = df['year'] + np.where(df['year'] >= 90, 1900, 2000)
        # Making copy and using group by to get Aggregated Values.
        df_agg = self.aggregate_columns(df)
        df['Measurement_Method'] = 'EPA_NationalEmissionInventory'
        df = pd.concat([df, df_agg])
        return df

    def national_emissions(self, file_path: str) -> pd.DataFrame:
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
        for sheet in sheets_national:
            # Number of rows to skip vary by sheet, inserting if-else for the same.
            skiphead = skiphead_ammonia_national if sheet == 'NH3' else skiphead_others_national
            skipfoot = skipfoot_pm_national if sheet in [
                'PM10Primary', 'PM25Primary'
            ] else skipfoot_others_national
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
            df = self.data_standardize(df, 'pollutant')
            df = self.data_standardize(df, 'Source Category')
            df['SV'] = df['Source Category'] + "-" + df['pollutant']
            df = df.drop(columns=['Source Category', 'pollutant'])
            # Changing the years present as columns into row values.
            df = df.melt(id_vars=['SV'],
                         var_name='year',
                         value_name='observation')
            final_df = pd.concat([final_df, df])

        final_df['geo_Id'] = 'country/USA'
        final_df_agg = self.aggregate_columns(final_df)
        final_df['Measurement_Method'] = 'EPA_NationalEmissionInventory'
        final_df = pd.concat([final_df, final_df_agg])
        return final_df

    def generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.

        Args:
            None

        Returns:
            None
        """
        # Writing Genereated TMCF to local path.
        with open(self._tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(_TMCF_TEMPLATE.rstrip('\n'))

    def generate_mcf(self, sv_list: list) -> dict:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Args:
            df_cols (list) : List of DataFrame Columns

        Returns:
            sv_replacement (dict) : Dictionary to replace SV names 
                                    with SV generator names
        """

        final_mcf_template = ""
        sv_replacement = {}
        sv_checker = {
            "typeOf": "dcs:StatisticalVariable",
            "populationType": "dcs:Emissions",
            "emissionSourceType": "dcs:NonBiogenicEmissionSource",
            "measurementQualifier": "dcs:Annual",
            "statType": "dcs:measuredValue",
            "measuredProperty": "dcs:amount"
        }
        for sv in sv_list:
            sv_property = sv.split("-")
            source = '\nemissionSource: dcs:' + sv_property[0]
            sv_checker['emissionSource'] = sv_property[0]
            pollutant = '\nemittedThing: dcs:' + sv_property[1]
            sv_checker['emittedThing'] = 'dcs:' + sv_property[1]
            generated_sv = get_statvar_dcid(sv_checker)
            sv_replacement[sv] = generated_sv
            final_mcf_template += _MCF_TEMPLATE.format(
                pv1=generated_sv, pv2=source, pv3=pollutant) + "\n"

        # Writing Genereated MCF to local path.
        with open(self._mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
        return sv_replacement

    def process(self):
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.

        Args:
            None
            
        Returns:
            None
        """

        final_df = pd.DataFrame(columns=['geo_Id', 'year', 'SV', 'observation'])
        # Creating Output Directory
        output_path = os.path.dirname(self._cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_list = []
        source_file_to_method_mapping = {
            "national_tier1_caps": self.national_emissions,
            "state_tier1_caps": self.state_emissions
        }
        for file_path in self._input_files:
            # Taking the File name out of the complete file address
            # Used -1 to pickup the last part which is file name
            # Read till -5 inorder to remove the .xlsx extension
            file_name = file_path.split("/")[-1][:-5]
            df = source_file_to_method_mapping[file_name](file_path)
            final_df = pd.concat([final_df, df])

        sv_list = final_df["SV"].to_list()
        final_df = final_df.sort_values(
            by=['geo_Id', 'year', 'SV', 'observation'])
        final_df['observation'].replace('', np.nan, inplace=True)
        final_df.dropna(subset=['observation'], inplace=True)
        sv_list = list(set(sv_list))
        sv_list.sort()
        sv_replacement = self.generate_mcf(sv_list)
        self.generate_tmcf()
        final_df.loc[:, ('SV')] = final_df['SV'].replace(sv_replacement,
                                                         regex=True)
        final_df['observation'] = final_df['observation'].astype(
            float) * _SCALING_FACTOR
        final_df.to_csv(self._cleaned_csv_file_path, index=False)


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
    loader = USAirPollutionEmissionTrends(ip_files, cleaned_csv_path, mcf_path,
                                          tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)
