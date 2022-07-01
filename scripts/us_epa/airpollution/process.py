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
from sre_constants import IN
from absl import app, flags
import pandas as pd
import numpy as np

FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

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
    "observationAbout: C:airpollution_emission_trends_tier1->geo_ID\n"
    "observationDate: C:airpollution_emission_trends_tier1->year\n"
    "scalingFactor: 1000\n"
    "value: C:airpollution_emission_trends_tier1->observation\n")


def _add_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates the columns based on SV

    Args: df (pd.DataFrame): df as the input, to aggregate values

    Returns: df (pd.DataFrame): modified df as output
    """

    df = df.drop(df[(df['SV'].str.contains('PrescribedFire')) |
                    (df['SV'].str.contains('Wildfire')) |
                    (df['SV'].str.contains('Miscellaneous'))].index)
    # Replacing the columns for grouping as per
    # StationaryFuelCombustion -    FuelCombustionElectricUtility
    #                               FuelCombustionIndustrial
    #                               FuelCombustionOther
    # IndustrialAndOtherProcesses - ChemicalAndAlliedProductManufacturing
    #                               MetalsProcessing
    #                               PetroleumAndRelatedIndustries
    #                               OtherIndustrialProcesses
    #                               SolventUtilization
    #                               StorageAndTransport
    #                               WasteDisposalAndRecycling
 	# Transportation -              OnRoadVehicles
    #                               NonRoadEnginesAndVehicles

    df['SV'] = (df['SV'].str.replace(
        'FuelCombustionElectricUtility',
        'StationaryFuelCombustion').str.replace(
            'FuelCombustionIndustrial', 'StationaryFuelCombustion').str.replace(
                'FuelCombustionOther', 'StationaryFuelCombustion').str.replace(
                    'ChemicalAndAlliedProductManufacturing',
                    'IndustrialAndOtherProcesses').str.replace(
                        'MetalsProcessing',
                        'IndustrialAndOtherProcesses').str.replace(
                            'PetroleumAndRelatedIndustries',
                            'IndustrialAndOtherProcesses').str.replace(
                                'OtherIndustrialProcesses',
                                'IndustrialAndOtherProcesses').str.replace(
                                    'SolventUtilization',
                                    'IndustrialAndOtherProcesses').str.replace(
                                        'StorageAndTransport',
                                        'IndustrialAndOtherProcesses').str.
                replace('WasteDisposalAndRecycling',
                        'IndustrialAndOtherProcesses').str.replace(
                            'OnRoadVehicles', 'Transportation').str.replace(
                                'NonRoadEnginesAndVehicles', 'Transportation'))
    df = df.groupby(['year', 'geo_ID', 'SV']).sum().reset_index()
    df['Measurement_Method'] = 'dcAggregate/EPA_NationalEmissionInventory'
    return df


def _replace_pollutant(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args: df (pd.DataFrame): df as the input, to change column values

    Returns: df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        column_name: {
            'CO': 'CarbonMonoxide',
            'NOX': 'OxidesOfNitrogen',
            'PM10Primary': 'PM10',
            'PM25Primary': 'PM2.5',
            'PM10-PRI': 'PM10',
            'PM25-PRI': 'PM2.5',
            'SO2': 'SulfurDioxide',
            'VOC': 'VolatileOrganicCompound',
            'NH3': 'Ammonia'
        }
    })
    return df

def _replace_source_category(df: pd.DataFrame, column_name: str) ->\
                            pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args: df (pd.DataFrame): df as the input, to change column values

    Returns: df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        column_name: {
            'FUEL COMB. ELEC. UTIL.':
                'FuelCombustionElectricUtility',
            'FUEL COMB. INDUSTRIAL':
                'FuelCombustionIndustrial',
            'FUEL COMB. OTHER':
                'FuelCombustionOther',
            'CHEMICAL & ALLIED PRODUCT MFG':
                'ChemicalAndAlliedProductManufacturing',
            'METALS PROCESSING':
                'MetalsProcessing',
            'PETROLEUM & RELATED INDUSTRIES':
                'PetroleumAndRelatedIndustries',
            'OTHER INDUSTRIAL PROCESSES':
                'OtherIndustrialProcesses',
            'SOLVENT UTILIZATION':
                'SolventUtilization',
            'STORAGE & TRANSPORT':
                'StorageAndTransport',
            'WASTE DISPOSAL & RECYCLING':
                'WasteDisposalAndRecycling',
            'HIGHWAY VEHICLES':
                'OnRoadVehicles',
            'OFF-HIGHWAY':
                'NonRoadEnginesAndVehicles',
            'MISCELLANEOUS':
                'MiscellaneousEmissionSource',
            'Wildfires':
                'Wildfire',
            'WILDFIRES':
                'Wildfire',
            'PRESCRIBED FIRES':
                'PrescribedFire'
        }
    })
    return df


def _state_emissions(file_path: str) -> pd.DataFrame:
    """
    Reads the file for state emissions data and cleans it for concatenation
    in Final CSV.

    Args:
        file_path (str): path to excel file as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    sheet = 'State_Trends'
    df = pd.read_excel(file_path, sheet, skiprows=1, header=0)
    # Adding geoId/ and making the State FIPS code of 2 numbers
    # Eg - 1 -> geoId/01
    df['geo_ID'] = [f'{x:02}' for x in df['State FIPS']]
    df['geo_ID'] = 'geoId/' + df['geo_ID']
    # Dropping Unwanted Columns
    df = df.drop(columns=['State FIPS', 'State', 'Tier 1 Code'])
    df = _replace_pollutant(df, 'Pollutant')
    df = _replace_source_category(df, 'Tier 1 Description')
    df['SV'] = 'Amount_Annual_Emissions_' + df['Tier 1 Description'] +\
            '_NonBiogenic_' + df['Pollutant']
    df = df.drop(columns=['Tier 1 Description', 'Pollutant'])
    # Changing the years present as columns into row values.
    df = df.melt(id_vars=['SV', 'geo_ID'],
                 var_name='year',
                 value_name='observation')
    df['year'] = (df['year'].str[-2:]).astype(int)
    # As 2001 is available as 01 and 1999 is available as 99,
    # Putting a logic to change it to proper year
    df['year'] = df['year'] + np.where(df['year'] >= 90, 1900, 2000)
    # Making copy and using group by to get Aggregated Values.
    df_agg = _add_missing_columns(df)
    df['Measurement_Method'] = 'EPA_NationalEmissionInventory'
    df = pd.concat([df, df_agg])
    return df


def _national_emissions(file_path: str) -> pd.DataFrame:
    """
    Reads the file for national emissions data and cleans it for concatenation
    in Final CSV.

    Args:
        file_path (str): path to excel file as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    _sheets_national = [
        'CO', 'NOX', 'PM10Primary', 'PM25Primary', 'SO2', 'VOC', 'NH3'
    ]
    final_df = pd.DataFrame()
    # Reading different sheets of Excel one at a time
    for sheet in _sheets_national:
        # Number of rows to skip vary by sheet, inserting if-else for the same.
        skiphead = 6 if sheet == 'NH3' else 5
        skipfoot = 0 if sheet in ['PM10Primary', 'PM25Primary'] else 5
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
        df = df.drop(
            df[(df['Source Category'] == 'Total') |
               (df['Source Category'] == 'Total without wildfires') |
               (df['Source Category'] == 'Miscellaneous without wildfires') |
               (df['Source Category'] == 'Total without miscellaneous') |
               (df['Source Category'] == 'Miscellaneous')].index)
        # Addition of pollutant type to the df by taking sheet name.
        df['pollutant'] = sheet
        df = _replace_pollutant(df, 'pollutant')
        df = _replace_source_category(df, 'Source Category')
        df['SV'] = 'Amount_Annual_Emissions_' + df['Source Category'] +\
                '_NonBiogenic_' + df['pollutant']
        df = df.drop(columns=['Source Category', 'pollutant'])
        # Changing the years present as columns into row values.
        df = df.melt(id_vars=['SV'], var_name='year', value_name='observation')
        final_df = pd.concat([final_df, df])

    final_df['geo_ID'] = 'country/USA'
    final_df_agg = _add_missing_columns(final_df)
    final_df['Measurement_Method'] = 'EPA_NationalEmissionInventory'
    final_df = pd.concat([final_df, final_df_agg])
    return final_df


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

    def _generate_tmcf(self) -> None:
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

    def _generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Args:
            df_cols (list) : List of DataFrame Columns

        Returns:
            None
        """

        final_mcf_template = ""
        for sv in sv_list:
            sv_property = sv.split("_")
            source = '\nemissionSource: dcs:' + sv_property[-3]
            pollutant = '\nemittedThing: dcs:' + sv_property[-1]
            final_mcf_template += _MCF_TEMPLATE.format(
                pv1=sv, pv2=source, pv3=pollutant) + "\n"

        # Writing Genereated MCF to local path.
        with open(self._mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))

    def process(self):
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.
        """

        final_df = pd.DataFrame(columns=['geo_ID', 'year', 'SV', 'observation'])
        # Creating Output Directory
        output_path = os.path.dirname(self._cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_list = []

        for file_path in self._input_files:
            # Taking the File name out of the complete file address
            # Used -1 to pickup the last part which is file name
            # Read till -5 inorder to remove the .tsv extension
            file_name = file_path.split("/")[-1][:-5]
            function_dict = {
                "national_tier1_caps": _national_emissions,
                "state_tier1_caps": _state_emissions
            }
            df = function_dict[file_name](file_path)
            final_df = pd.concat([final_df, df])
            sv_list += df["SV"].to_list()

        final_df = final_df.sort_values(
            by=['geo_ID', 'year', 'SV', 'observation'])
        final_df['observation'].replace('', np.nan, inplace=True)
        final_df.dropna(subset=['observation'], inplace=True)
        final_df.to_csv(self._cleaned_csv_file_path, index=False)
        sv_list = list(set(sv_list))
        sv_list.sort()
        self._generate_mcf(sv_list)
        self._generate_tmcf()


def main(_):
    input_path = FLAGS.input_path
    if not os.path.exists(input_path):
        os.mkdir(input_path)
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output")
    # Defining Output Files
    csv_name = "airpollution_emission_trends_tier1.csv"
    mcf_name = "airpollution_emission_trends_tier1.mcf"
    tmcf_name = "airpollution_emission_trends_tier1.tmcf"
    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    tmcf_path = os.path.join(data_file_path, tmcf_name)
    loader = USAirPollutionEmissionTrends(ip_files, cleaned_csv_path, mcf_path,\
        tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)
