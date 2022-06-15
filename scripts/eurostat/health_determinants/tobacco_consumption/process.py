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
from sys import path
# For import util.alpha2_to_dcid
path.insert(1, '../../../../')

import os
import pandas as pd
import numpy as np
# import mcf_generator
from util.alpha2_to_dcid import COUNTRY_MAP
from absl import app
from absl import flags
# from mcf_generator import generate_mcf
# pd.set_option("display.max_columns", None)
# pd.set_option("display.max_rows", None)

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_files"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")


def smoking_tobaccoproducts_county_of_birth(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'unit,smoking,sex,age,c_birth,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "unit,smoking,sex,age,c_birth,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_c_birth(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent'+\
        '_'+df['smoking']+"_"+'TobaccoProducts'+\
        '_In_Count_Person_'+df['c_birth']+'_'+df['sex']
    df.drop(columns=['smoking', 'c_birth', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def smoking_tobaccoproducts_country_of_citizenship(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'unit,smoking,sex,age,citizen,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "unit,smoking,sex,age,citizen,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_citizen(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent'+\
        '_'+df['smoking']+"_"+'TobaccoProducts'+\
        '_In_Count_Person_'+df['citizen']+'_'+df['sex']
    df.drop(columns=['smoking', 'citizen', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def smoking_tobaccoproducts_education_attainment_level(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,smoking,isced11,sex,age,geo', '2019', '2014']
    df.columns = cols
    col1 = "unit,smoking,isced11,sex,age,geo"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_isced11(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent'+\
        '_'+df['smoking']+'_TobaccoProducts'+\
        '_In_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['smoking', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')

    return df


def smoking_tobaccoproducts_income_quintile(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,smoking,quant_inc,sex,age,geo', '2019', '2014']
    df.columns = cols
    col1 = "unit,smoking,quant_inc,sex,age,geo"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[(df['age'] == 'TOTAL') &
                      (~(df['quant_inc'] == 'UNK'))]
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent'+\
        '_'+df['smoking']+'_TobaccoProducts'+\
        '_In_Count_Person_'+df['quant_inc']+'_'+df['sex']
    df.drop(columns=['smoking', 'quant_inc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    return df


def smoking_tobaccoproducts_degree_of_urbanisation(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'smoking,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "smoking,deg_urb,sex,age,unit,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent'+\
        '_'+df['smoking']+'_TobaccoProducts'+\
        '_In_Count_Person_'+df['deg_urb']+'_'+df['sex']
    df.drop(columns=['smoking', 'deg_urb', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def former_daily_tobacco_smoker_income_quintile(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'unit,sex,age,quant_inc,time', 'EU27_2020', 'BE', 'BG', 'CZ', 'DK',
        'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT', 'LU',
        'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS',
        'NO', 'RS', 'TR'
    ]
    df.columns = cols
    col1 = "unit,sex,age,quant_inc,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[(df['age'] == 'TOTAL') &
                      (~(df['quant_inc'] == 'UNK'))]
    df.drop(columns=['EU27_2020'], inplace=True)
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_FormerSmoker_DailyUsage_TobaccoSmoking'+\
        '_In_Count_Person_'+df['quant_inc']+'_'+df['sex']
    df.drop(columns=['quant_inc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    df
    return df


def former_daily_tobacco_smoker_education_attainment_level(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'unit,sex,age,isced11,time', 'EU27_2020', 'BE', 'BG', 'CZ', 'DK', 'DE',
        'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT', 'LU', 'HU',
        'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS', 'NO',
        'RS', 'TR'
    ]
    df.columns = cols
    col1 = "unit,sex,age,isced11,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020'], inplace=True)
    df = _replace_isced11(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_FormerSmoker_DailyUsage_TobaccoSmoking'+\
        '_In_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def daily_smokers_cigarettes_education_attainment_level(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,smoking,isced11,sex,age,geo', '2019', '2014']
    df.columns = cols
    col1 = "unit,smoking,isced11,sex,age,geo"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_isced11(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_Smoking'+\
        '_'+df['smoking']+'_DailyUsage_Cigarettes'+\
        '_In_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['smoking', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    return df


def daily_smokers_cigarettes_income_quintile(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,smoking,quant_inc,sex,age,geo', '2019', '2014']
    df.columns = cols
    col1 = "unit,smoking,quant_inc,sex,age,geo"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[(df['age'] == 'TOTAL') &
                      (~(df['quant_inc'] == 'UNK'))]
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_Smoking'+\
        '_'+df['smoking']+'_DailyUsage_Cigarettes'+\
        '_In_Count_Person_'+df['quant_inc']+'_'+df['sex']
    df.drop(columns=['smoking', 'quant_inc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    return df


def daily_smokers_cigarettes_degree_of_urbanisation(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'smoking,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "smoking,deg_urb,sex,age,unit,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_Smoking'+\
        '_'+df['smoking']+'_DailyUsage_Cigarettes'+\
        '_In_Count_Person_'+df['deg_urb']+'_'+df['sex']
    df.drop(columns=['smoking', 'deg_urb', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def daily_exposure_tobacco_smoke_indoors_education_attainment_level(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,frequenc,isced11,sex,age,geo', '2019', '2014']
    df.columns = cols
    col1 = "unit,frequenc,isced11,sex,age,geo"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_isced11(df)
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_ExposureToTobaccoSmoke'+\
        '_'+df['frequenc']+\
        '_In_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['frequenc', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    return df


def daily_exposure_tobacco_smoke_indoors_degree_of_urbanisation(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'frequenc,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "frequenc,deg_urb,sex,age,unit,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_deg_urb(df)
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_ExposureToTobaccoSmoke'+\
        '_'+df['frequenc']+\
        '_In_Count_Person_'+df['deg_urb']+'_'+df['sex']
    df.drop(columns=['frequenc', 'deg_urb', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def duration_daily_tobacco_smoking_education_attainment_level(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'unit,duration,sex,age,isced11,time', 'EU27_2020', 'BE', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE',
        'IS', 'NO', 'RS', 'TR'
    ]
    df.columns = cols
    col1 = "unit,duration,sex,age,isced11,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020'], inplace=True)
    df = _replace_isced11(df)
    df = _replace_duration(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_Smoking_'+\
        df['duration']+'_DailyUsage_TobaccoProducts'+\
        '_In_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['duration', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def electronic_cigarettes_similar_electronic_devices_education_attainment_level(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'unit,frequenc,sex,age,isced11,time', 'EU27_2020', 'BE', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE',
        'IS', 'NO', 'RS', 'TR'
    ]
    df.columns = cols
    col1 = "unit,frequenc,sex,age,isced11,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020'], inplace=True)
    df = _replace_isced11(df)
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_'\
        +df['frequenc']+'_'+'ECigarettes'+\
        '_In_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['frequenc', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def daily_smokers_cigarettes_history_education_attainment_level(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'sex,age,isced11,time', 'BE', 'BG', 'CZ', 'DE', 'EE', 'EL', 'ES', 'CY',
        'LV', 'HU', 'MT', 'AT', 'PL', 'RO', 'SI', 'SK'
    ]
    df.columns = cols
    col1 = "sex,age,isced11,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = _replace_isced11(df)
    df = _replace_sex(df)
    df.drop(columns=['age'], inplace=True)
    df['SV'] = 'Percent_Smoking'+\
        '_DailyUsage_Cigarettes'+\
        '_In_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def daily_smokers_cigarettes_history_income_quintile(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'sex,age,quant_inc,time', 'BE', 'BG', 'CZ', 'DE', 'EE', 'EL', 'ES',
        'CY', 'LV', 'HU', 'MT', 'AT', 'PL', 'RO', 'SI', 'SK'
    ]
    df.columns = cols
    col1 = "sex,age,quant_inc,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[(df['age'] == 'TOTAL') &
                      (~(df['quant_inc'] == 'UNK'))]
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df.drop(columns=['age'], inplace=True)
    df['SV'] = 'Percent_Smoking'+\
        '_DailyUsage_Cigarettes'+\
        '_In_Count_Person_'+df['quant_inc']+'_'+df['sex']
    df.drop(columns=['quant_inc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def daily_smokers_number_of_cigarettes_history_education_attainment_level(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'sex,age,smoking,isced11,time', 'BE', 'BG', 'CZ', 'DE', 'EE', 'EL',
        'ES', 'CY', 'LV', 'HU', 'MT', 'PL', 'RO', 'SI', 'SK'
    ]
    df.columns = cols
    col1 = "sex,age,smoking,isced11,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = _replace_isced11(df)
    df = _replace_smoking(df)
    df = _replace_sex(df)
    df.drop(columns=['age'], inplace=True)
    df['SV'] = 'Percent_Smoking'+\
        '_'+df['smoking']+'_DailyUsage_Cigarettes'+\
        '_In_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['smoking', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def _replace_sex(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df = df.replace({'sex': {
        'F': 'Female',
        'M': 'Male',
        'T': 'Total'}})
    return df


def _replace_isced11(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df = df.replace({'isced11': {
        'ED0-2': 'LessThanPrimaryEducation'+\
        'OrPrimaryEducationOrLowerSecondaryEducation',
        'ED0_2': 'LessThanPrimaryEducation'+\
        'OrPrimaryEducationOrLowerSecondaryEducation',
        'ED3-4': 'UpperSecondaryEducation'+\
        'OrPostSecondaryNonTertiaryEducation',
        'ED3_4': 'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
        'ED5_6' : 'TertiaryEducationStageOneOrTertiaryEducationStageTwo',
        'ED5-8': 'TertiaryEducation',
        'ED5_8': 'TertiaryEducation',
        'TOTAL': 'Total'
        }})
    return df

def _replace_quant_inc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df = df.replace({
        'quant_inc': {
            'TOTAL': 'Total',
            'QU1': 'IncomeOf0To20Percentile',
            'QU2': 'IncomeOf20To40Percentile',
            'QU3': 'IncomeOf40To60Percentile',
            'QU4': 'IncomeOf60To80Percentile',
            'QU5': 'IncomeOf80To100Percentile',
        }
    })
    return df


def _replace_deg_urb(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df = df.replace({
        'deg_urb': {
            'TOTAL': 'Total',
            'DEG1': 'Urban',
            'DEG2': 'SemiUrban',
            'DEG3': 'Rural'
        }
    })
    return df


def _replace_smoking(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """

    df = df.replace({
        'smoking': {
            'TOTAL': 'Total',
            'NSM': 'NonSmoker',
            'SM_CUR': 'Smoking',
            'SM_DAY': 'Smoking_DailyUsage',
            'SM_OCC': 'Smoking_OccasionalUsage',
            'SM_LT20D': 'LessThan20CigarettesPerDay',
            'SM_GE20D': '20OrMoreCigarettesPerDay',
            'DSM_GE20': 'DailyCigaretteSmoker20OrMorePerDay',
            'DSM_LT20': 'DailyCigaretteSmokerLessThan20PerDay'
        }
    })
    return df


def _replace_c_birth(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df = df.replace({
        'c_birth': {
            'EU28_FOR': 'ForeignBornWithinEU28',
            'NEU28_FOR': 'ForeignBornOutsideEU28',
            'FOR': 'ForeignBorn',
            'NAT': 'Native'
        }
    })
    return df


def _replace_citizen(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df = df.replace({
        'citizen': {
            'EU28_FOR': 'WithinEU28AndNotACitizen',
            'NEU28_FOR': 'CitizenOutsideEU28',
            'FOR': 'NotACitizen',
            'NAT': 'Citizen'
        }
    })
    return df


def _replace_duration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df = df.replace({
        'duration': {
            'Y_LT1': 'LessThan1Year',
            'Y1-5': 'From1To5Years',
            'Y5-10': 'From5To10Years',
            'Y_GE10': '10YearsOrOver'
        }
    })
    return df


def _replace_frequenc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df = df.replace({
        'frequenc': {
            'DAY_GE1HD': 'AtLeastOneHourPerDay',
            'DAY_LT1HD': 'LessThanOneHourPerDay',
            'LT1W': 'LessThanOnceAWeek',
            'GE1W': 'AtLeastOnceAWeek',
            'RAR_NVR': 'RarelyOrNever',
            'DAY': 'Smoking_DailyUsage',
            'FMR': 'FormerSmoker_Formerly',
            'OCC': 'Smoking_OccasionalUsage',
            'NVR': 'Smoking_NeverUsed'
        }
    })
    return df


def _split_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Divides a single column into multiple columns and returns the DF
    """
    info = col.split(",")
    df[info] = df[col].str.split(',', expand=True)
    df.drop(columns=[col], inplace=True)
    return df


class EuroStatTobaccoConsumption:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    def __init__(self, input_files: list, csv_file_path: str,\
        mcf_file_path: str, tmcf_file_path: str) -> None:
        self.input_files = input_files
        self.cleaned_csv_file_path = csv_file_path
        self.mcf_file_path = mcf_file_path
        self.tmcf_file_path = tmcf_file_path

    def _generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.
        Arguments:
            None
        Returns:
            None
        """
        tmcf_template = (
            "Node: E:EuroStat_Population_TobaccoConsumption->E0\n"
            "typeOf: dcs:StatVarObservation\n"
            "variableMeasured: C:EuroStat_Population_TobaccoConsumption->SV\n"
            "measurementMethod: C:EuroStat_Population_TobaccoConsumption->"
            "Measurement_Method\n"
            "observationAbout: C:EuroStat_Population_TobaccoConsumption->geo\n"
            "observationDate: C:EuroStat_Population_TobaccoConsumption->time\n"
            "value: C:EuroStat_Population_TobaccoConsumption->observation\n")
        # Writing Genereated TMCF to local path.
        with open(self.tmcf_file_path, 'w+', encoding="UTF-8") as f_out:
            f_out.write(tmcf_template.rstrip('\n'))
# ----------------------------------------------------------------------------------------------------------------------------------
    def _generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template
        Args:
            df_columns (list) : List of DataFrame Columns
        Returns:
            None
        """
        # pylint: disable=R0914
        # pylint: disable=R0912
        # pylint: disable=R0915
        mcf_template = ("Node: dcid:{ip1}\n"
                        "typeOf: dcs:StatisticalVariable\n"
                        "populationType: dcs:Person{ip2}{ip3}{ip4}{ip5}"
                        "{ip6}{ip7}{ip8}{ip9}{ip10}{ip11}{ip12}{ip13}\n"
                        "statType: dcs:measuredValue\n"
                        "measuredProperty: dcs:count\n"
                        "")
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            incomequin = gender = education = frequenc = healthbehavior =\
            residence = countryofbirth = citizenship = substance = quantity = history = ''

            sv_temp = sv.split("_In_")
            denominator = "\nmeasurementDenominator: dcs:" + sv_temp[1]
            sv_prop = sv_temp[0].split("_")
            sv_prop1 = sv_temp[1].split("_")
            for prop in sv_prop:
                if prop in ["Percent"]:
                    continue
                if  "Smoking" in prop:\
                    healthbehavior = "\nhealthBehavior: dcs:" + prop
                elif "NonSmoker" in prop:
                    healthbehavior = "\nhealthBehavior: dcs:" + prop
                elif "ExposureToTobaccoSmoke" in prop:
                      healthbehavior = "\nhealthBehavior: dcs:" + prop
          

                if "DailyUsage" in prop or "OccasionalUsage" in prop\
                     or "AtLeastOneHourPerDay" in prop or "LessThanOneHourPerDay" in prop\
                      or "LessThanOnceAWeek" in prop or "AtLeastOnceAWeek" in prop\
                      or "RarelyOrNever" in prop :
                    frequenc = "\nsubstanceUsageFrequency: dcs:" + prop

                if "LessThan20CigarettesPerDay"in prop or "20OrMoreCigarettesPerDay" in prop \
                    or "DailyCigaretteSmoker20OrMorePerDay" in prop or "DailyCigaretteSmokerLessThan20PerDay" in prop:
                    quantity = "\nsubstanceUsageQuantity: dcs:" + prop
                if "TobaccoProducts" in prop or "Cigarette" in prop or "ECigarettes" in prop:
                    substance = "\nsubstanceUsed: dcs:" + prop
                if 'LessThan1Year'in prop or 'From1To5Years'in prop or 'From5To10Years'in prop or'10YearsOrOver'in prop:
                      history = "\nsubstanceUsageHistory: dcs:" + prop

                for prop in sv_prop1:
                    if prop in ["Count","Person"]:
                        continue
                    if "Male" in prop or "Female" in prop:
                        gender = "\ngender: dcs:" + prop
                    elif "Education" in prop:
                        education = "\neducationalAttainment: dcs:" + \
                            prop.replace("Or","__")
                        #prop.replace("EducationalAttainment","")
                        prop.replace("Or","__")
                    elif "Percentile" in prop:
                        incomequin = "\nincome: ["+prop.replace("Percentile",\
                            "").replace("IncomeOf","").replace("To"," ")+" Percentile]"
                    elif "Urban" in prop or "SemiUrban" in prop \
                        or "Rural" in prop:
                        residence = "\nplaceOfResidenceClassification: dcs:" + prop
                    elif "ForeignBorn" in prop or "Native" in prop:
                        countryofbirth = "\nnativity: dcs:" + \
                            prop.replace("CountryOfBirth","")
                    elif "ForeignWithinEU28" in prop or "ForeignOutsideEU28" in prop\
                        or "Citizen" in prop or "NotACitizen" in prop:
                        citizenship = "\ncitizenship: dcs:"+\
                        prop.replace("Citizenship","")

            final_mcf_template += mcf_template.format(ip1=sv,
                                                      ip2=denominator,
                                                      ip3=healthbehavior,
                                                      ip4=gender,
                                                      ip5=frequenc,
                                                      ip6=education,
                                                      ip7=incomequin,
                                                      ip8=residence,
                                                      ip9=countryofbirth,
                                                      ip10=citizenship,
                                                      ip11=substance,
                                                      ip12=quantity,
                                                      ip13=history) + "\n"


        # Writing Genereated MCF to local path.
        with open(self.mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
        # pylint: enable=R0914
        # pylint: enable=R0912
        # pylint: enable=R0915

    def process(self):
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.
        Arguments: None
        Returns: None
        """

        final_df = pd.DataFrame(columns=['time','geo','SV','observation',\
            'Measurement_Method'])
        # Creating Output Directory
        output_path = os.path.dirname(self.cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_list = []

        for file_path in self.input_files:
            print(file_path)
            df = pd.read_csv(file_path, sep='\t', header=0)
            file_name = file_path.split("/")[-1][:-4]
            function_dict = {
                "hlth_ehis_sk1b":
                    smoking_tobaccoproducts_county_of_birth,
                "hlth_ehis_sk1c":
                    smoking_tobaccoproducts_country_of_citizenship,
                "hlth_ehis_sk1e":
                    smoking_tobaccoproducts_education_attainment_level,
                "hlth_ehis_sk1i":
                    smoking_tobaccoproducts_income_quintile,
                "hlth_ehis_sk1u":
                    smoking_tobaccoproducts_degree_of_urbanisation,
                "hlth_ehis_sk2i":
                    former_daily_tobacco_smoker_income_quintile,
                "hlth_ehis_sk2e":
                    former_daily_tobacco_smoker_education_attainment_level,
                "hlth_ehis_sk3e":
                    daily_smokers_cigarettes_education_attainment_level,
                "hlth_ehis_sk3i":
                    daily_smokers_cigarettes_income_quintile,
                "hlth_ehis_sk3u":
                    daily_smokers_cigarettes_degree_of_urbanisation,
                "hlth_ehis_sk4e":
                    daily_exposure_tobacco_smoke_indoors_education_attainment_level,
                "hlth_ehis_sk4u":
                    daily_exposure_tobacco_smoke_indoors_degree_of_urbanisation,
                "hlth_ehis_sk5e":
                    duration_daily_tobacco_smoking_education_attainment_level,
                "hlth_ehis_sk6e":
                    electronic_cigarettes_similar_electronic_devices_education_attainment_level,
                "hlth_ehis_de3":
                    daily_smokers_cigarettes_history_education_attainment_level,
                "hlth_ehis_de4":
                    daily_smokers_cigarettes_history_income_quintile,
                "hlth_ehis_de5":
                    daily_smokers_number_of_cigarettes_history_education_attainment_level
            }
            df = function_dict[file_name](df)
            df['SV'] = df['SV'].str.replace('_Total', '')
            # df["file_name"] = file_name_without_ext
            final_df = pd.concat([final_df, df])
            sv_list += df["SV"].to_list()

        final_df = final_df.sort_values(by=['time', 'geo', 'SV', 'observation'])
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
        final_df.drop(columns=['info'], inplace=True)
        final_df['observation'] = (final_df['observation'].astype(str).str.replace(
            ':', '').str.replace(' ', '').str.replace('u', ''))
        final_df['observation'] = pd.to_numeric(final_df['observation'],
                                                errors='coerce')
        final_df = final_df.replace({'geo': COUNTRY_MAP})
        final_df = final_df.sort_values(by=['geo', 'SV'])
        final_df['observation'].replace('', np.nan, inplace=True)
        final_df.dropna(subset=['observation'], inplace=True)
        final_df.to_csv(self.cleaned_csv_file_path, index=False)
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
    data_file_path = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "output"
    # Defining Output Files
    csv_name = "eurostat_population_tobaccocunsumption.csv"
    mcf_name = "eurostat_population_tobaccocunsumption.mcf"
    tmcf_name = "eurostat_population_tobaccocunsumption.tmcf"
    cleaned_csv_path = data_file_path + os.sep + csv_name
    mcf_path = data_file_path + os.sep + mcf_name
    tmcf_path = data_file_path + os.sep + tmcf_name
    loader = EuroStatTobaccoConsumption(ip_files, cleaned_csv_path, mcf_path,
                                        tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)
