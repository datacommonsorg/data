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

Before running this module, run input_files.py script, it downloads required
input files, creates necessary folders for processing.
Folder information
input_files - downloaded files (from US census website) are placed here
output_files - output files (mcf, tmcf and csv are written here)
"""

import os
import sys
import pandas as pd
import numpy as np
from absl import app
from absl import flags

COMMON_MODULE_DIR = os.path.dirname(__file__) + os.sep + '..' + os.sep
sys.path.insert(1, COMMON_MODULE_DIR)
# pylint: disable=import-error
# pylint: disable=wrong-import-position
from common.replacement_functions import (_replace_sex, _replace_isced11,
                                          _replace_quant_inc, _replace_deg_urb,
                                          _replace_c_birth, _replace_citizen,
                                          _replace_lev_limit, _replace_bmi,
                                          _split_column)

# For import util.alpha2_to_dcid
UTIL_MODULE_DIR = os.path.dirname(__file__) + os.sep + '..' + \
                  os.sep + '..' + os.sep + '..' + os.sep + '..' + os.sep
sys.path.insert(1, UTIL_MODULE_DIR)

from util.alpha2_to_dcid import COUNTRY_MAP
# pylint: enable=import-error
# pylint: enable=wrong-import-position

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_files"

flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

_MCF_TEMPLATE = """Node: dcid:{dcid}
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
statType: dcs:measuredValue
measuredProperty: dcs:count
{xtra_pvs}
"""

_TMCF_TEMPLATE = """Node: E:EuroStat_Population_PhysicalActivity->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:EuroStat_Population_PhysicalActivity->SV
measurementMethod: C:EuroStat_Population_PhysicalActivity->Measurement_Method
observationAbout: C:EuroStat_Population_PhysicalActivity->geo
observationDate: C:EuroStat_Population_PhysicalActivity->time
value: C:EuroStat_Population_PhysicalActivity->observation
"""

_INCOME_QUINTILE_VALUES = {
    "IncomeOf0To20Percentile": "[0 20 Percentile]",
    "IncomeOf20To40Percentile": "[20 40 Percentile]",
    "IncomeOf40To60Percentile": "[40 60 Percentile]",
    "IncomeOf60To80Percentile": "[60 80 Percentile]",
    "IncomeOf80To100Percentile": "[80 100 Percentile]",
}

_EXISTING_SV_DEG_URB_GENDER = {
    "Count_Person_Female_Rural": "Count_Person_Rural_Female",
    "Count_Person_Male_Rural": "Count_Person_Rural_Male",
    "Count_Person_Female_Urban": "Count_Person_Urban_Female",
    "Count_Person_Male_Urban": "Count_Person_Urban_Male",
}

_SV_DENOMINATOR = 1


def _replace_prop(sv: str):
    return sv.replace("CountryOfBirth", "")\
             .replace("Citizenship", "")\
             .replace("In_", "")\
             .replace("Count_", "")\
             .replace("Person_", "")\
             .replace("Percent_", "")


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
    multiple_cols = "unit,bmi,isced11,sex,age,geo"
    # Splits the DataFrame having mulitple column data
    # in a single column and creates them as Individual Columns
    data_df = _split_column(data_df, multiple_cols)
    # Filtering out the required rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df = data_df[~(data_df['geo'].isin(['EU27_2020', 'EU28']))]
    data_df = _replace_bmi(data_df)
    data_df = _replace_sex(data_df)
    data_df = _replace_isced11(data_df)
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
    # Splits the DataFrame having mulitple column data
    # in a single column and creates them as Individual Columns
    data_df = _split_column(data_df, df_cols[0])
    # Filtering out the required rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df = _replace_bmi(data_df)
    data_df = _replace_sex(data_df)
    data_df = _replace_isced11(data_df)
    data_df['SV'] = 'Percent_'+ data_df['bmi'] +'_' + \
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
    # Splits the DataFrame having mulitple column data
    # in a single column and creates them as Individual Columns
    data_df = _split_column(data_df, df_cols[0])
    # Filtering out the wanted rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df = data_df[~(data_df['geo'].isin(['EU27_2020', 'EU28']))]
    data_df = _replace_bmi(data_df)
    data_df = _replace_sex(data_df)
    data_df = _replace_quant_inc(data_df)
    data_df['SV'] = 'Percent_'+ data_df['bmi'] +'_' + \
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
    # Splits the DataFrame having mulitple column data
    # in a single column and creates them as Individual Columns
    data_df = _split_column(data_df, df_cols[0])
    # Filtering out the required rows and columns
    data_df = data_df[(data_df['age'] == 'TOTAL') &
                      (~(data_df['quant_inc'] == 'UNK'))]
    data_df = _replace_bmi(data_df)
    data_df = _replace_sex(data_df)
    data_df = _replace_quant_inc(data_df)
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
    # Splits the DataFrame having mulitple column data
    # in a single column and creates them as Individual Columns
    data_df = _split_column(data_df, df_cols[0])
    # Filtering out the wanted rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df = data_df.drop(columns=['EU27_2020', 'EU28'])
    data_df = _replace_bmi(data_df)
    data_df = _replace_sex(data_df)
    data_df = _replace_deg_urb(data_df)
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
    # Splits the DataFrame having mulitple column data
    # in a single column and creates them as Individual Columns
    data_df = _split_column(data_df, df_cols[0])
    # Filtering out the wanted rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df = data_df.drop(columns=['EU27_2020', 'EU28'])
    data_df = _replace_bmi(data_df)
    data_df = _replace_sex(data_df)
    data_df = _replace_c_birth(data_df)
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
    # Splits the DataFrame having mulitple column data
    # in a single column and creates them as Individual Columns
    data_df = _split_column(data_df, df_cols[0])
    # Filtering out the wanted rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df = data_df.drop(columns=['EU27_2020', 'EU28'])
    data_df = _replace_bmi(data_df)
    data_df = _replace_sex(data_df)
    data_df = _replace_citizen(data_df)

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
    # Splits the DataFrame having mulitple column data
    # in a single column and creates them as Individual Columns
    data_df = _split_column(data_df, df_cols[0])
    # Filtering out the wanted rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df = data_df.drop(columns=['EU27_2020', 'EU28'])
    data_df = _replace_bmi(data_df)
    data_df = _replace_sex(data_df)
    data_df = _replace_lev_limit(data_df)
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
        dcid = sv
        sv_denominator = sv.split("_In_")[_SV_DENOMINATOR]
        denominator_value = _EXISTING_SV_DEG_URB_GENDER.get(
            sv_denominator, sv_denominator)
        pvs.append(f"measurementDenominator: dcs:{denominator_value}")
        sv = _replace_prop(sv)
        sv_prop = [prop for prop in sv.split("_") if sv.strip()]
        for prop in sv_prop:
            if "Male" in prop or "Female" in prop:
                pvs.append(f"gender: dcs:{prop}")
            elif "Education" in prop:
                pvs.append(
                    f"educationalAttainment: dcs:{prop.replace('Or', '__')}")
            elif "Percentile" in prop:
                income_quin = _INCOME_QUINTILE_VALUES[prop]
                pvs.append(f"income: {income_quin}")
            elif "Urban" in prop or "SemiUrban" in prop \
                or "Rural" in prop:
                pvs.append(f"placeOfResidenceClassification: dcs:{prop}")
            elif "ForeignBorn" in prop or "Native" in prop:
                pvs.append(f"nativity: dcs:{prop}")
            elif "ForeignWithin" in prop or "ForeignOutside" in prop\
                or "Citizen" in prop:
                pvs.append(f"citizenship: dcs:{prop}")
            elif "Activity" in prop:
                pvs.append(f"globalActivityLimitationindicator: dcs:{prop}")
            elif "weight" in prop \
                or "Obese" in prop or "Obesity" in prop:
                pvs.append(f"healthBehavior: dcs:{prop}")

        node = _MCF_TEMPLATE.format(dcid=dcid, xtra_pvs='\n'.join(pvs))
        mcf_nodes.append(node)
    mcf = '\n'.join(mcf_nodes)
    # Writing Genereated MCF to local path.
    with open(mcf_file_path, 'w+', encoding='utf-8') as f_out:
        f_out.write(mcf.rstrip('\n'))


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
    # Adding Measurement Method based on a condition
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
    input_path = FLAGS.input_path
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]
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
    process(ip_files, cleaned_csv_path, mcf_path,\
        tmcf_path)


if __name__ == "__main__":
    app.run(main)
