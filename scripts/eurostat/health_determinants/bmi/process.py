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
Before running this module, run download_input_files.py script, it downloads
required input files, creates necessary folders for processing.
Folder information
input_files - downloaded files (from US census website) are placed here
output_files - output files (mcf, tmcf and csv are written here)
"""
import os
import sys
import pandas as pd
import numpy as np
from absl import app, flags

# For import common.replacement_functions
_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
# pylint: disable=wrong-import-position
# pylint: disable=import-error
from common.replacement_functions import (_split_column, _replace_col_values)
from common.denominator_mcf_generator import (generate_mcf_template,
                                              write_to_mcf_path)

# For import util.alpha2_to_dcid
_COMMON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(1, _COMMON_PATH)

from util.alpha2_to_dcid import COUNTRY_MAP
# pylint: enable=wrong-import-position
# pylint: enable=import-error

_FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

_MCF_TEMPLATE = ("Node: dcid:{dcid}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Person\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:count\n"
                 "{xtra_pvs}\n")

_TMCF_TEMPLATE = (
    "Node: E:eurostat_population_bmi->E0\n"
    "typeOf: dcs:StatVarObservation\n"
    "variableMeasured: C:eurostat_population_bmi->SV\n"
    "measurementMethod: C:eurostat_population_bmi->Measurement_Method\n"
    "observationAbout: C:eurostat_population_bmi->geo\n"
    "observationDate: C:eurostat_population_bmi->time\n"
    "value: C:eurostat_population_bmi->observation\n")

file_to_sv_mapping = {
        "hlth_ehis_bm1e": "'Percent_' + df['bmi']"+\
                          " + '_In_Count_Person_' + df['isced11']"+\
                          "+ '_' + df['sex']",
        "hlth_ehis_de1": "'Percent_' + df['bmi']"+\
                         " + '_In_Count_Person_' + df['isced11']"+\
                         "+ '_' + df['sex']",
        "hlth_ehis_bm1i": "'Percent_' + df['bmi']"+\
                          " + '_In_Count_Person_' + df['sex']"+\
                          "+ '_' + df['quant_inc']",
        "hlth_ehis_de2": "'Percent_' + df['bmi']"+\
                         " + '_In_Count_Person_' + df['sex']"+\
                         "+ '_' + df['quant_inc']",
        "hlth_ehis_bm1u": "'Percent_' + df['bmi']"+\
                          " + '_In_Count_Person_' + df['deg_urb']"+\
                          "+ '_' + df['sex']",
        "hlth_ehis_bm1b": "'Percent_' + df['bmi']"+\
                          " + '_In_Count_Person_' + df['sex']"+\
                          "+ '_' + df['c_birth']",

        "hlth_ehis_bm1c": "'Percent_' + df['bmi']"+\
                          " + '_In_Count_Person_' + df['citizen']"+\
                          "+ '_' + df['sex']",
        "hlth_ehis_bm1d": "'Percent_' + df['bmi']"+\
                          " + '_In_Count_Person_' + df['sex']"+\
                          "+ '_' + df['lev_limit']",
}

_SV_DENOMINATOR = 1
_EXISTING_SV_DEG_URB_GENDER = {
    "Count_Person_Female_Rural": "Count_Person_Rural_Female",
    "Count_Person_Male_Rural": "Count_Person_Rural_Male",
    "Count_Person_Female_Urban": "Count_Person_Urban_Female",
    "Count_Person_Male_Urban": "Count_Person_Urban_Male",
}


class EuroStatAlcoholConsumption:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """
    def __init__(self, input_files: list, csv_file_path: str,\
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

    def _generate_mcf(self, sv_list: list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template
        Args:
            sv_list (list): List of Statistical Variables
            mcf_file_path (str): Output MCF File Path
        """
        mcf_nodes = []
        for sv in sv_list:
            pvs = []
            sv_denominator = sv.split("_In_")[_SV_DENOMINATOR]
            denominator_value = _EXISTING_SV_DEG_URB_GENDER.get(
                sv_denominator, sv_denominator)
            pvs.append(f"measurementDenominator: dcs:{denominator_value}")
            mcf_node = generate_mcf_template(sv, _MCF_TEMPLATE, pvs)
            mcf_nodes.append(mcf_node)
        write_to_mcf_path(mcf_nodes, self._mcf_file_path)

    # pylint: disable=anomalous-backslash-in-string
    # pylint: disable=duplicate-key
    # pylint: disable=eval-used
    def parse_file(self, file_name: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parsing the EuroStat Datasets
        Args:
            file_name (str): Input File Name
            df (pd.DataFrame): Input DataFrame

        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        split_columns = df.columns.values.tolist()[0]
        df = _split_column(df, split_columns)
        split_columns = split_columns.replace('frequenc', 'frequenc_alcohol')\
            .replace('isced97', 'isced11').replace('geo\time','geo')\
                .replace('geo\\time','geo').replace('time\geo','time')\
                    .replace('time\\geo','time')\
                        .replace('quantile', 'quant_inc')
        df.rename(columns={
            'geo\time': 'geo',
            'geo\\time': 'geo',
            'time\geo': 'time',
            'time\\geo': 'time',
            'frequenc': 'frequenc_alcohol',
            'isced97': 'isced11',
            'quantile': 'quant_inc'
        },
                  inplace=True)
        df = df[df['age'] == 'TOTAL']

        if 'quant_inc' in df.columns.values.tolist():
            df = df[(~(df['quant_inc'] == 'UNK'))]

        for col in [
                'sex', 'quant_inc', 'frequenc_alcohol', 'isced11', 'deg_urb',
                'c_birth', 'citizen', 'bmi', 'deg_urb', 'lev_limit'
        ]:
            if col in df.columns.values.tolist():
                df = _replace_col_values(df, col)

        df['SV'] = eval(file_to_sv_mapping[file_name])

        split_columns_list = split_columns.split(',')
        if 'time' in split_columns_list:
            split_columns_list.remove('time')
            id_vars = ['SV', 'time']
            var_name = 'geo'
        if 'geo' in split_columns_list:
            split_columns_list.remove('geo')
            id_vars = ['SV', 'geo']
            var_name = 'time'

        df.drop(columns=split_columns_list, inplace=True)
        df = df.melt(id_vars=id_vars,
                     var_name=var_name,
                     value_name='observation')
        df = df[df['geo'] != 'EU27_2020']
        df = df[df['geo'] != 'EU28']
        return df

    # pylint: enable=anomalous-backslash-in-string
    # pylint: enable=duplicate-key
    # pylint: enable=eval-used

    def process(self):
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.

        Args:
            None

        Returns:
            None
        """

        final_df = pd.DataFrame(
            columns=['time', 'geo', 'SV', 'observation', 'Measurement_Method'])

        # # Creating Output Directory
        output_path = os.path.dirname(self._cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_list = []

        for file_path in self._input_files:

            df = pd.read_csv(file_path, sep='\t', header=0)
            file_name = file_path.split("/")[-1][:-4]
            df.columns = df.columns.str.strip()
            df = self.parse_file(file_name, df)
            df['SV'] = df['SV'].str.replace('_Total', '')
            final_df = pd.concat([final_df, df])
            sv_list += df["SV"].to_list()

        final_df = final_df.sort_values(by=['time', 'geo', 'SV', 'observation'])
        final_df = final_df.drop_duplicates(subset=['time', 'geo', 'SV'],
                                            keep='first')
        final_df['observation'] = final_df['observation'].astype(
            str).str.strip()
        # derived_df generated to get the year/SV/location sets
        # where 'u' exist
        derived_df = final_df[final_df['observation'].astype(str).str.contains(
            'u')]
        u_rows = list(derived_df['SV'] + derived_df['geo'])
        final_df['info'] = final_df['SV'] + final_df['geo']
        # Adding Measurement Method based on a condition, whereever u is found
        # in an observation. The corresponding measurement method for all the
        # years of that perticular SV/Country is made as Low Reliability.
        # Eg: 2014
        #   country/BEL
        #   Percent_AlcoholConsumption_Daily_In_Count_Person
        #   14.2 u,
        # so measurement method for all 2008, 2014 and 2019 years shall be made
        # low reliability.
        final_df['Measurement_Method'] = np.where(
            final_df['info'].isin(u_rows),
            'EurostatRegionalStatistics_LowReliability',
            'EurostatRegionalStatistics')
        derived_df = final_df[final_df['observation'].astype(str).str.contains(
            'd')]
        u_rows = list(derived_df['SV'] + derived_df['geo'])
        final_df['info'] = final_df['SV'] + final_df['geo']
        # Adding Measurement Method based on a condition, whereever d is found
        # in an observation. The corresponding measurement method for all the
        # years of that perticular SV/Country is made as Definition Differs.
        # Eg: 2014
        #   country/ITA
        #   Percent_AlcoholConsumption_Daily_In_Count_Person
        #   14.1 d,
        # so measurement method for both 2014 and 2019 years shall be made
        # Definition Differs.
        final_df['Measurement_Method'] = np.where(
            final_df['info'].isin(u_rows),
            'EurostatRegionalStatistics_DefinitionDiffers',
            final_df['Measurement_Method'])
        final_df.drop(columns=['info'], inplace=True)
        final_df['observation'] = (
            final_df['observation'].astype(str).str.replace(
                ':', '').str.replace(' ',
                                     '').str.replace('u',
                                                     '').str.replace('d', ''))
        final_df['observation'] = pd.to_numeric(final_df['observation'],
                                                errors='coerce')
        final_df = final_df.replace({'geo': COUNTRY_MAP})
        final_df = final_df.sort_values(by=['geo', 'SV'])
        final_df['observation'].replace('', np.nan, inplace=True)
        final_df.dropna(subset=['observation'], inplace=True)
        final_df.to_csv(self._cleaned_csv_file_path, index=False)
        sv_list = list(set(sv_list))
        sv_list.sort()
        self._generate_mcf(sv_list)
        self._generate_tmcf()


def main(_):
    input_path = _FLAGS.input_path
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output")
    # Defining Output Files
    csv_name = "eurostat_population_bmi.csv"
    mcf_name = "eurostat_population_bmi.mcf"
    tmcf_name = "eurostat_population_bmi.tmcf"
    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    tmcf_path = os.path.join(data_file_path, tmcf_name)
    loader = EuroStatAlcoholConsumption(ip_files, cleaned_csv_path,\
        mcf_path, tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)
