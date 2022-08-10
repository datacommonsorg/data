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
from sre_constants import IN
from absl import app, flags
import pandas as pd
import numpy as np

sys.path.insert(
    1, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from util.statvar_dcid_generator import get_statvar_dcid

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))

from metadata import replace_metadata

FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

_MCF_TEMPLATE = ("Node: dcid:{pv1}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Emissions\n"
                 "measurementQualifier: dcs:Annual{pv2}{pv3}{pv4}\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:amount\n")

_TMCF_TEMPLATE = ("Node: E:national_emission_onroad->E0\n"
                  "typeOf: dcs:StatVarObservation\n"
                  "variableMeasured: C:national_emission_onroad->SV\n"
                  "measurementMethod: C:national_emission_onroad->"
                  "Measurement_Method\n"
                  "observationAbout: C:national_emission_onroad->geo_Id\n"
                  "observationDate: C:national_emission_onroad->year\n"
                  "unit: C:national_emission_onroad->unit\n"
                  "value: C:national_emission_onroad->observation\n")


def _replace_metadata(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata and returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values,
        column_name (str): column_name as a string, which has to be changed

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({column_name: replace_metadata})
    return df


def _regularize_columns(df: pd.DataFrame, file_path: str) -> pd.DataFrame:
    """
    Reads the file for national emissions data and regularizes the files into a 
    single structure so that it can be processed at once. This includes dropping
    additional columns, renaming the columns and adding the columns with null if
    not present.

    Args:
        df (pd.DataFrame): provides the df as input
        file_path (str): path to excel file as the input

    Returns:
        df (pd.DataFrame): provides the regularized df as output
    """
    if '2008' in file_path or '2011' in file_path:
        df.rename(columns={
            'state_and_county_fips_code': 'fips code',
            'data_set_short_name': 'data set',
            'pollutant_cd': 'pollutant code',
            'uom': 'emissions uom',
            'total_emissions': 'total emissions'
        },
                  inplace=True)
        df = df.drop(columns=[
            'tribal_name', 'st_usps_cd', 'county_name', 'data_category_cd',
            'description', 'emissions_type_code', 'aircraft_engine_type_cd',
            'emissions_op_type_code'
        ])
        df['pollutant type(s)'] = 'nan'
    elif '2017' in file_path:
        df = df.drop(columns=[
            'epa region code', 'state', 'fips state code', 'county',
            'emissions type code', 'aetc', 'reporting period',
            'emissions operating type', 'sector', 'tribal name',
            'pollutant desc', 'data category'
        ])
    elif 'tribes' in file_path:
        df.rename(columns={'tribal name': 'fips code'}, inplace=True)
        df = df.drop(columns=[
            'state', 'fips state code', 'data category', 'reporting period',
            'emissions operating type', 'emissions type code', 'pollutant desc'
        ])
        df = _replace_metadata(df, 'fips code')
        df['pollutant type(s)'] = 'nan'
    else:
        df.rename(columns={
            'state_and_county_fips_code': 'fips code',
            'data_set': 'data set',
            'pollutant_cd': 'pollutant code',
            'uom': 'emissions uom',
            'total_emissions': 'total emissions'
        },
                  inplace=True)
        df = df.drop(columns=[
            'tribal_name', 'fips_state_code', 'st_usps_cd', 'county_name',
            'data_category', 'emission_operating_type', 'pollutant_desc',
            'emissions_type_code', 'emissions_operating_type'
        ])
        df['pollutant type(s)'] = 'nan'
    return df


def _onroad(file_path: str) -> pd.DataFrame:
    """
    Reads the file for national emissions data and cleans it for concatenation
    in Final CSV.

    Args:
        file_path (str): path to excel file as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    df = pd.read_csv(file_path, header=0, low_memory=False)
    df = _regularize_columns(df, file_path)
    df['pollutant code'] = df['pollutant code'].astype(str)
    df['geo_Id'] = ([f'{x:05}' for x in df['fips code']])
    # 
    # Remove if Tribal Details are needed
    # 
    df['geo_Id'] = df['geo_Id'].astype(int)
    df = df.drop(df[df.geo_Id > 80000].index)
    df['geo_Id'] = ([f'{x:05}' for x in df['geo_Id']])
    df['geo_Id'] = df['geo_Id'].astype(str)
    #
    # Remove if Tribal Details are needed
    # 
    df['geo_Id'] = 'geoId/' + df['geo_Id']
    df.rename(columns={
        'emissions uom': 'unit',
        'total emissions': 'observation',
        'data set': 'year'
    },
              inplace=True)
    df['year'] = df['year'].str[:4]
    df = _replace_metadata(df, 'unit')
    df = _replace_metadata(df, 'scc')
    df = _replace_metadata(df, 'pollutant code')
    df['SV'] = ('Annual_Amount_Emissions_' + df['scc'].astype(str) + '_' +
                df['pollutant code'].astype(str))
    df['SV'] = df['SV'].str.replace('_nan', '')
    df = df.drop(
        columns=['scc', 'pollutant code', 'pollutant type(s)', 'fips code'])

    return df


class USAirEmissionTrends:
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
            sv_checker = {
                "typeOf": "dcs:StatisticalVariable",
                "populationType": "dcs:Emissions",
                "measurementQualifier": "dcs:Annual",
                "statType": "dcs:measuredValue",
                "measuredProperty": "dcs:amount"
            }
            emission_type = pollutant = ''
            sv_property = sv.split("_")
            source = '\nemissionSource: dcs:' + sv_property[3]
            sv_checker['emissionSource'] = 'dcs:' + sv_property[3]
            for i in sv_property[4:]:
                pollutant = pollutant + i + '_'
            sv_checker['emittedThing'] = 'dcs:' + pollutant.rstrip('_')
            pollutant = '\nemittedThing: dcs:' + pollutant.rstrip('_')
            generated_sv = get_statvar_dcid(sv_checker)
            if (generated_sv != sv):
                print(generated_sv)
                print(sv)
                print()
            final_mcf_template += _MCF_TEMPLATE.format(
                pv1=sv, pv2=source, pv3=pollutant, pv4=emission_type) + "\n"

        # Writing Genereated MCF to local path.
        with open(self._mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))

    def process(self):
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.
        """

        final_df = pd.DataFrame(
            columns=['geo_Id', 'year', 'SV', 'observation', 'unit'])
        # Creating Output Directory
        output_path = os.path.dirname(self._cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_list = []

        for file_path in self._input_files:
            # Taking the File name out of the complete file address
            # Used -1 to pickup the last part which is file name
            # Read till -4 inorder to remove the .csv extension
            file_name = file_path.split("/")[-1][:-4]
            df = _onroad(file_path)
            final_df = pd.concat([final_df, df])
            sv_list += df["SV"].to_list()

        final_df = final_df.sort_values(
            by=['geo_Id', 'year', 'SV', 'observation'])
        final_df['observation'].replace('', np.nan, inplace=True)
        final_df.dropna(subset=['observation'], inplace=True)
        final_df['Measurement_Method'] = 'EPA_NationalEmissionInventory'
        final_df.to_csv(self._cleaned_csv_file_path, index=False)
        sv_list = list(set(sv_list))
        sv_list.sort()
        self._generate_mcf(sv_list)
        self._generate_tmcf()


def main(_):
    input_path = FLAGS.input_path
    try:
        ip_files = os.listdir(input_path)
    except:
        print("Run the download script first.\n")
        sys.exit(1)
    ip_files = [input_path + os.sep + file for file in ip_files]
    output_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "output")
    # Defining Output Files
    csv_name = "national_emission_onroad.csv"
    mcf_name = "national_emission_onroad.mcf"
    tmcf_name = "national_emission_onroad.tmcf"
    cleaned_csv_path = os.path.join(output_file_path, csv_name)
    mcf_path = os.path.join(output_file_path, mcf_name)
    tmcf_path = os.path.join(output_file_path, tmcf_name)
    loader = USAirEmissionTrends(ip_files, cleaned_csv_path, mcf_path,\
        tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)
