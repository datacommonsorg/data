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
This module creates CSV files used for importing data into DC.
Below are list of files processed -

National
    2008, 2014,2019 - BMI, Age, Sex, Education Combination
    2008, 2014,2019 - BMI, Age, Sex, Income Quintile Combination
    2014, 2019 -      BMI, Age, Sex, Degree Of Urbanisation Combination
    2014, 2019 -      BMI, Age, Sex, Birth Country Combination
    2014, 2019 -      BMI, Age, Sex, Citizenship Country Combination
    2014, 2019 -      BMI, Age, Sex, Level Of Activity Limitation Combination

Before running this module, run download_input_files.py script, it downloads
required input files, creates necessary folders for processing.
Folder information
input_files - downloaded files (from US census website) are placed here
output_files - output files (mcf, tmcf and csv are written here)
"""

import os
from pyclbr import Function
import sys
import pandas as pd
import numpy as np
from absl import app
from absl import flags

_COMMON_MODULE_DIR = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(1, _COMMON_MODULE_DIR)
# pylint: disable=import-error
# pylint: disable=wrong-import-position
from common.replacement_functions import (_replace_sex, _replace_isced11,
                                          _replace_quant_inc, _replace_deg_urb,
                                          _replace_c_birth, _replace_citizen,
                                          _replace_lev_limit, _replace_bmi,
                                          _split_column)

from common.denominator_mcf_generator import (generate_mcf_template,
                                              write_to_mcf_path)

# For import util.alpha2_to_dcid
_UTIL_MODULE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                '..')
sys.path.insert(1, _UTIL_MODULE_DIR)

from util.alpha2_to_dcid import COUNTRY_MAP
# pylint: enable=import-error
# pylint: enable=wrong-import-position

_FLAGS = flags.FLAGS
_DEFAULT_INPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "input_files")

flags.DEFINE_string("input_path", _DEFAULT_INPUT_PATH,
                    "Import Data File's List")

MCF_TEMPLATE = ("Node: dcid:{dcid}\n"
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

_EXISTING_SV_DEG_URB_GENDER = {
    "Count_Person_Female_Rural": "Count_Person_Rural_Female",
    "Count_Person_Male_Rural": "Count_Person_Rural_Male",
    "Count_Person_Female_Urban": "Count_Person_Urban_Female",
    "Count_Person_Male_Urban": "Count_Person_Urban_Male",
}

_SV_DENOMINATOR = 1


def _common_transformations(data_df: pd.DataFrame, split_mulit_cols: str,
                            replace_func: Function) -> pd.DataFrame:
    """
    Process the input dataframe data_df and applies transformations
    such as replacing values, splitting mulitple columns.

    Args:
        data_df (pd.DataFrame): Input DataFrame
        split_mulit_cols (str): Multiple Columns List
        replace_func (Function): Replace Function

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    # Splits the DataFrame having mulitple column data
    # in a single column and creates them as Individual Columns
    data_df = _split_column(data_df, split_mulit_cols)
    # Filtering out the required rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df = _replace_bmi(data_df)
    data_df = _replace_sex(data_df)
    data_df = replace_func(data_df)
    return data_df


def _age_sex_education(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    education with bmi,age,and sex combination data for the year 2014, 2019.
    Args:
        data_df (pd.DataFrame): DataFrame having raw data

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df_cols = ['unit,bmi,isced11,sex,age,geo', '2019', '2014']
    data_df.columns = df_cols
    data_df = _common_transformations(data_df=data_df,
                                      split_mulit_cols=df_cols[0],
                                      replace_func=_replace_isced11)
    # Filtering out the required rows and columns
    data_df = data_df[~(data_df['geo'].isin(['EU27_2020', 'EU28']))]
    # Creating SV using the DataFrame Values
    data_df['SV'] = 'Percent_' + data_df['bmi'] + '_' + \
                    'In_Count_Person_' + data_df['isced11'] +\
                    '_' + data_df['sex']
    data_df = data_df.drop(columns=['unit', 'age', 'isced11', 'bmi', 'sex'])
    data_df = data_df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return data_df


def _age_sex_education_history(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    education with bmi,age,and sex combination data for the year 2008.
    Args:
        data_df (pd.DataFrame): DataFrame having raw data

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df_cols = [
        'isced11,bmi,sex,age,time', 'BE', 'BG', 'CZ', 'DE', 'EE', 'EL', 'ES',
        'FR', 'CY', 'LV', 'HU', 'MT', 'AT', 'PL', 'RO', 'SI', 'SK', 'TR'
    ]
    data_df.columns = df_cols
    data_df = _common_transformations(data_df=data_df,
                                      split_mulit_cols=df_cols[0],
                                      replace_func=_replace_isced11)
    data_df['SV'] = 'Percent_' + data_df['bmi'] +'_' + \
                    'In_Count_Person_' + data_df['isced11'] + \
                    '_' + data_df['sex']
    data_df = data_df.drop(columns=['isced11', 'bmi', 'sex', 'age'])
    data_df = data_df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return data_df


def _age_sex_income(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    income quintile with bmi,age,and sex combination data
    for the year 2014, 2019.
    Args:
        data_df (pd.DataFrame): DataFrame having raw data

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df_cols = ['unit,bmi,quant_inc,sex,age,geo', '2019', '2014']
    data_df.columns = df_cols
    data_df = _common_transformations(data_df=data_df,
                                      split_mulit_cols=data_df.columns[0],
                                      replace_func=_replace_quant_inc)
    # Filtering out the wanted rows and columns
    data_df = data_df[~(data_df['geo'].isin(['EU27_2020', 'EU28']))]
    data_df['SV'] = 'Percent_' + data_df['bmi'] +'_' + \
                    'In_Count_Person_' + data_df['sex'] + \
                    '_' + data_df['quant_inc']

    data_df = data_df.drop(columns=['unit', 'age', 'quant_inc', 'bmi', 'sex'])
    data_df = data_df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return data_df


def _age_sex_income_history(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    income quintile with bmi,age,and sex combination data
    for the year 2008.
    Args:
        data_df (pd.DataFrame): DataFrame having raw data

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df_cols = [
        'bmi,sex,age,quant_inc,time', 'BE', 'BG', 'CZ', 'DE', 'EE', 'EL', 'ES',
        'FR', 'CY', 'LV', 'HU', 'MT', 'AT', 'PL', 'RO', 'SI', 'SK', 'TR'
    ]
    data_df.columns = df_cols
    data_df = _common_transformations(data_df=data_df,
                                      split_mulit_cols=df_cols[0],
                                      replace_func=_replace_quant_inc)
    # Filtering out the required rows and columns
    data_df = data_df[(~(data_df['quant_inc'] == 'UNK'))]
    data_df['SV'] = 'Percent_' + data_df['bmi'] + '_' + \
                    'In_Count_Person_' + data_df['sex'] + \
                    '_' + data_df['quant_inc']

    data_df = data_df.drop(columns=['quant_inc', 'bmi', 'sex', 'age'])
    data_df = data_df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return data_df


def _age_sex_degree_urbanisation(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    degree of urbanisation with bmi,age,and sex combination data
    for the year 2014.
    Args:
        data_df (pd.DataFrame): DataFrame having raw data

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df_cols = [
        'bmi,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28', 'BE', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE',
        'IS', 'NO', 'UK', 'TR'
    ]
    data_df.columns = df_cols
    # Filtering out the wanted rows and columns
    data_df = data_df.drop(columns=['EU27_2020', 'EU28'])
    data_df = _common_transformations(data_df=data_df,
                                      split_mulit_cols=df_cols[0],
                                      replace_func=_replace_deg_urb)
    data_df = data_df.drop(columns=['unit', 'age'])
    data_df['SV'] = 'Percent_' + data_df['bmi'] +'_' + \
                    'In_Count_Person_' + data_df['deg_urb'] + \
                    '_' + data_df['sex']

    data_df = data_df.drop(columns=['deg_urb', 'bmi', 'sex'])
    data_df = data_df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return data_df


def _age_sex_birth_country(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    country of birth with bmi,age,and sex combination data
    for the year 2014.
    Args:
        data_df (pd.DataFrame): DataFrame having raw data

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df_cols = [
        'unit,bmi,sex,age,c_birth,time', 'EU27_2020', 'EU28', 'BE', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE',
        'IS', 'NO', 'UK', 'TR'
    ]
    data_df.columns = df_cols
    # Filtering out the wanted rows and columns
    data_df = data_df.drop(columns=['EU27_2020', 'EU28'])
    data_df = _common_transformations(data_df=data_df,
                                      split_mulit_cols=df_cols[0],
                                      replace_func=_replace_c_birth)
    data_df = data_df.drop(columns=['unit', 'age'])
    data_df['SV'] = 'Percent_' + data_df['bmi'] + '_' + \
                    'In_Count_Person_' + data_df['sex'] + \
                    '_' + data_df['c_birth']
    data_df.drop(columns=['c_birth', 'bmi', 'sex'], inplace=True)
    data_df = data_df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return data_df


def _age_sex_citizenship_country(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    country of citizenship with bmi,age,and sex combination data
    for the year 2014.
    Args:
        data_df (pd.DataFrame): DataFrame having raw data

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df_cols = [
        'unit,bmi,sex,age,citizen,time', 'EU27_2020', 'EU28', 'BE', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE',
        'IS', 'NO', 'UK', 'TR'
    ]
    data_df.columns = df_cols
    # Filtering out the wanted rows and columns
    data_df = data_df.drop(columns=['EU27_2020', 'EU28'])
    data_df = _common_transformations(data_df=data_df,
                                      split_mulit_cols=df_cols[0],
                                      replace_func=_replace_citizen)
    data_df = data_df.drop(columns=['unit', 'age'])
    data_df['SV'] = 'Percent_' + data_df['bmi'] + '_' + \
                    'In_Count_Person_' + \
                    data_df['citizen'] + '_' + data_df['sex']
    data_df.drop(columns=['citizen', 'bmi', 'sex'], inplace=True)
    data_df = data_df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return data_df


def _age_sex_acitivity_limitation(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the Cleaned DataFrame consists
    degree of urbanisation with bmi,age,and sex combination data
    for the year 2014.
    Args:
        data_df (pd.DataFrame): DataFrame having raw data

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df_cols = [
        'bmi,lev_limit,sex,age,unit,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    data_df.columns = df_cols
    # Filtering out the wanted rows and columns
    data_df = data_df.drop(columns=['EU27_2020', 'EU28'])
    data_df = _common_transformations(data_df=data_df,
                                      split_mulit_cols=df_cols[0],
                                      replace_func=_replace_lev_limit)
    data_df = data_df.drop(columns=['unit', 'age'])
    data_df['SV'] = 'Percent_' + data_df['bmi'] + '_' + \
                    'In_Count_Person_' + \
                    data_df['sex'] + '_' + data_df['lev_limit']
    data_df = data_df.drop(columns=['lev_limit', 'bmi', 'sex'])
    data_df = data_df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return data_df


def _generate_tmcf(tmcf_file_path: str) -> None:
    """
    This method generates TMCF file w.r.t
    dataframe headers and defined TMCF template.
    Args:
        tmcf_file_path (str): Output TMCF File Path
    """
    # Writing Genereated TMCF to local path.
    with open(tmcf_file_path, 'w+', encoding='utf-8') as f_out:
        f_out.write(_TMCF_TEMPLATE.rstrip('\n'))


def _generate_mcf(sv_list: list, mcf_file_path: str) -> None:
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
        mcf_node = generate_mcf_template(sv, MCF_TEMPLATE, pvs)
        mcf_nodes.append(mcf_node)
    write_to_mcf_path(mcf_nodes, mcf_file_path)


def process(input_files: list, cleaned_csv_file_path: str, mcf_file_path: str,
            tmcf_file_path: str):
    """
    Process Input Raw Files and apply transformations to generate final
    CSV, MCF and TMCF files.
    """

    final_df = pd.DataFrame()
    sv_list = []
    f_names = []
    for file_path in input_files:
        file_name_with_ext = os.path.basename(file_path)
        f_names.append(file_name_with_ext)
        file_name_without_ext = os.path.splitext(file_name_with_ext)[0]
        file_to_function_mapping = {
            "hlth_ehis_bm1e": _age_sex_education,
            "hlth_ehis_bm1i": _age_sex_income,
            "hlth_ehis_bm1u": _age_sex_degree_urbanisation,
            "hlth_ehis_bm1b": _age_sex_birth_country,
            "hlth_ehis_bm1c": _age_sex_citizenship_country,
            "hlth_ehis_bm1d": _age_sex_acitivity_limitation,
            "hlth_ehis_de1": _age_sex_education_history,
            "hlth_ehis_de2": _age_sex_income_history
        }
        df = pd.read_csv(file_path, sep='\t', header=0)
        df = file_to_function_mapping[file_name_without_ext](df)
        df['SV'] = df['SV'].str.replace('_Total', '')
        final_df = pd.concat([final_df, df])
        sv_list += df["SV"].to_list()

    final_df.sort_values(by=['time', 'geo', 'SV', 'observation'], inplace=True)
    final_df = final_df.drop_duplicates(subset=['time','geo','SV'],\
        keep='first')
    final_df['observation'] = final_df['observation'].astype(str)\
        .str.strip()
    # derived_df generated to get the year/SV/location sets
    # where 'u' exist
    derived_df = final_df[final_df['observation'].astype(str).str.contains('u')]
    u_rows = list(derived_df['SV'] + derived_df['geo'])
    final_df['info'] = final_df['SV'] + final_df['geo']
    # Promoting Measurement Method based on a condition
    final_df['Measurement_Method'] = np.where(
        final_df['info'].isin(u_rows),
        'EurostatRegionalStatistics_LowReliability',
        'EurostatRegionalStatistics')
    final_df = final_df.drop(columns=['info'])
    final_df['observation'] = (final_df['observation'].astype(str).str.replace(
        ':', '').str.replace(' ', '').str.replace('u', ''))
    final_df['observation'] = pd.to_numeric(final_df['observation'],
                                            errors='coerce')
    final_df = final_df.replace({'geo': COUNTRY_MAP})
    final_df = final_df.sort_values(by=['geo', 'SV'])
    final_df['observation'].replace('', np.nan, inplace=True)
    final_df.dropna(subset=['observation'], inplace=True)
    final_df.to_csv(cleaned_csv_file_path, index=False)
    sv_list = list(set(sv_list))
    sv_list.sort()
    _generate_mcf(sv_list, mcf_file_path)
    _generate_tmcf(tmcf_file_path)


def main(_):
    input_path = _FLAGS.input_path
    input_files = os.listdir(input_path)
    input_files = [input_path + os.sep + file for file in input_files]
    data_file_path = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "output_files"
    # Creating Output Directory
    if not os.path.exists(data_file_path):
        os.mkdir(data_file_path)
    # Defining Output Files
    cleaned_csv_path = data_file_path + os.sep + \
        "eurostat_population_bmi.csv"
    mcf_path = data_file_path + os.sep + \
        "eurostat_population_bmi.mcf"
    tmcf_path = data_file_path + os.sep + \
        "eurostat_population_bmi.tmcf"
    process(input_files, cleaned_csv_path, mcf_path,\
        tmcf_path)


if __name__ == "__main__":
    app.run(main)
