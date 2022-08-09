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
from util.county_to_dcid import COUNTY_MAP

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
    "observationAbout: C:airpollution_emission_trends_tier1->geo_Id\n"
    "observationDate: C:airpollution_emission_trends_tier1->year\n"
    "unit: Ton\n"
    "value: C:airpollution_emission_trends_tier1->observation\n")


def _add_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
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
    df = df.drop(df[(df['SV'].str.contains('NaturalResources')) |
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
    sourcegroups = {
        'FuelCombustionElectricUtility': 'StationaryFuelCombustion',
        'FuelCombustionIndustrial': 'StationaryFuelCombustion',
        'EPA_FuelCombustionOther': 'StationaryFuelCombustion',
        'ChemicalAndAlliedProductManufacturing': 'IndustrialAndOtherProcesses',
        'MetalsProcessing': 'IndustrialAndOtherProcesses',
        'PetroleumAndRelatedIndustries': 'IndustrialAndOtherProcesses',
        'EPA_OtherIndustrialProcesses': 'IndustrialAndOtherProcesses',
        'SolventUtilization': 'IndustrialAndOtherProcesses',
        'StorageAndTransport': 'IndustrialAndOtherProcesses',
        'WasteDisposalAndRecycling': 'IndustrialAndOtherProcesses',
        'OnRoadVehicles': 'Transportation',
        'NonRoadEnginesAndVehicles': 'Transportation'
    }
    df.loc[:, ('SV')] = df['SV'].replace(sourcegroups, regex=True)
    df = df.groupby(['year', 'geo_Id', 'SV']).sum().reset_index()
    df['Measurement_Method'] = 'dcAggregate/EPA_NationalEmissionInventory'
    return df


def _replace_pollutant(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        column_name: {
            'Carbon Monoxide': 'CarbonMonoxide',
            'Nitrogen Oxides': 'OxidesOfNitrogen',
            'PM10 Primary (Filt + Cond)': 'PM10',
            'PM2.5 Primary (Filt + Cond)': 'PM2.5',
            'Sulfur Dioxide': 'SulfurDioxide',
            'Volatile Organic Compounds': 'VolatileOrganicCompound',
            'Ammonia': 'Ammonia'
        }
    })
    return df

def _replace_source_category(df: pd.DataFrame, column_name: str) ->\
                            pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        column_name: {
            'Fuel Comb. Elec. Util.':
                'FuelCombustionElectricUtility',
            'Fuel Comb. Industrial':
                'FuelCombustionIndustrial',
            'Fuel Comb. Other':
                'EPA_FuelCombustionOther',
            'Chemical & Allied Product Mfg':
                'ChemicalAndAlliedProductManufacturing',
            'Metals Processing':
                'MetalsProcessing',
            'Petroleum & Related Industries':
                'PetroleumAndRelatedIndustries',
            'Other Industrial Processes':
                'EPA_OtherIndustrialProcesses',
            'Solvent Utilization':
                'SolventUtilization',
            'Storage & Transport':
                'StorageAndTransport',
            'Waste Disposal & Recycling':
                'WasteDisposalAndRecycling',
            'Highway Vehicles':
                'OnRoadVehicles',
            'Off-Highway':
                'NonRoadEnginesAndVehicles',
            'Miscellaneous':
                'EPA_MiscellaneousEmissionSource',
            'Natural Resources':
                'NaturalResources'
        }
    })
    return df


def _county_emissions(file_path: str, year:str) -> pd.DataFrame:
    """
    Reads the file for state emissions data and cleans it for concatenation
    in Final CSV.

    Args:
        file_path (str): path to excel file as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    df = pd.read_csv(file_path, header=0)
    df['year'] = year
    # df['County'] = df['County'].astype(str) + " "
    df['geo_Id'] = ''
    for index, row in df.iterrows():
        temp = [val for key, val in COUNTY_MAP[row["Address"]].items() if row["County"] == key.replace(' County', '').replace(' Parish', '')]
        df['geo_Id'][index] = df['geo_Id'][index] + (str(temp[:1]))
    # Dropping Unwanted Columns
    df = df.drop(columns=['Address','County',' Unit of Measure','Pollutant Type'])
    df = _replace_pollutant(df, 'Pollutant')
    df = _replace_source_category(df, 'Tier')
    df['SV'] = 'Annual_Amount_Emissions_' + df['Tier'] +\
            '_NonBiogenicEmissionSource_' + df['Pollutant']
    # Making copy and using group by to get Aggregated Values.
    df_agg = _add_missing_columns(df)
    df['Measurement_Method'] = 'EPA_NationalEmissionInventory'
    df = pd.concat([df, df_agg])
    return df


class USCountyAirPollutionEmissionTrends:
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
            pollutant = '\nemittedThing: dcs:' + sv_property[-1]
            sv_checker['emittedThing'] = 'dcs:' + sv_property[-1]
            generated_sv = get_statvar_dcid(sv_checker)
            if (generated_sv != sv):
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

        for file_path in self._input_files:
            # Taking the File name out of the complete file address
            # Used -1 to pickup the last part which is file name
            # Read till -4 inorder to remove the .csv extension
            # and get the year.
            year = file_path.split("/")[-1][:-4]
            df = _county_emissions(file_path,year)
            final_df = pd.concat([final_df, df])
            sv_list += df["SV"].to_list()

        final_df = final_df.sort_values(
            by=['geo_Id', 'year', 'SV', 'observation'])
        final_df['observation'].replace('', np.nan, inplace=True)
        final_df.dropna(subset=['observation'], inplace=True)
        sv_list = list(set(sv_list))
        sv_list.sort()
        sv_replacement = self._generate_mcf(sv_list)
        self._generate_tmcf()
        final_df.loc[:, ('SV')] = final_df['SV'].replace(sv_replacement,
                                                         regex=True)
        final_df.to_csv(self._cleaned_csv_file_path, index=False)


def main(_):
    input_path = FLAGS.input_path
    try:
        ip_files = os.listdir(input_path)
    except Exception:
        logger.info("Run the download.py script first.")
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
    loader = USCountyAirPollutionEmissionTrends(ip_files, cleaned_csv_path, mcf_path,\
        tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)
