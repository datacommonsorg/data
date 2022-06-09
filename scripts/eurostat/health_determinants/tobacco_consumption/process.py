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
from util.alpha2_to_dcid import COUNTRY_MAP
from absl import app
from absl import flags

# pd.set_option("display.max_columns", None)
# pd.set_option("display.max_rows", None)

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_files"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")


def health_determinant_eurostat_smoking_county_of_birth(
        df: pd.DataFrame) -> pd.DataFrame:
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
    df['SV'] = 'Count_Person_'+ df['c_birth']+'_'+df['sex']+\
        '_'+'SmokingTobaccoProducts'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['c_birth']+'_'+df['sex']
    df.drop(columns=['smoking', 'c_birth', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def health_determinant_eurostat_smoking_country_of_citizenship(
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
    df['SV'] = 'Count_Person_'+ df['citizen']+'_'+df['sex']+\
        '_'+'SmokingTobaccoProducts'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['citizen']+'_'+df['sex']
    df.drop(columns=['smoking', 'citizen', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def health_determinant_eurostat_smoking_education_attainment_level(
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
    df['SV'] = 'Count_Person_'+ df['isced11']+'_'+df['sex']+\
        '_'+'SmokingTobaccoProducts'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['smoking', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')

    return df


def health_determinant_eurostat_smoking_income_quintile(
        df: pd.DataFrame) -> pd.DataFrame:
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
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['quant_inc']+'_'+df['sex']+\
        '_'+'SmokingTobaccoProducts'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['quant_inc']+'_'+df['sex']
    df.drop(columns=['smoking', 'quant_inc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    return df


def health_determinant_eurostat_smoking_degree_of_urbanisation(
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
    df['SV'] = 'Count_Person_'+ df['deg_urb']+'_'+df['sex']+\
        '_'+'SmokingTobaccoProducts'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['deg_urb']+'_'+df['sex']
    df.drop(columns=['smoking', 'deg_urb', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def health_determinant_eurostat_former_daily_tobacco_smoker_income_quintile(
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
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020'], inplace=True)
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['quant_inc']+'_'+df['sex']+\
        '_'+'FormerDailyTobaccoSmoking'+\
        '_AsAFractionOf_Count_Person_'+df['quant_inc']+'_'+df['sex']
    df.drop(columns=['quant_inc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    df
    return df


def health_determinant_eurostat_former_daily_tobacco_smoker_education_attainment_level(
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
    df['SV'] = 'Count_Person_'+ df['isced11']+'_'+df['sex']+\
        '_'+'FormerDailyTobaccoSmoking'+\
        '_AsAFractionOf_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def health_determinant_eurostat_daily_smokers_education_attainment_level(
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
    df['SV'] = 'Count_Person_'+ df['isced11']+'_'+df['sex']+\
        '_'+'DailySmokers'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['smoking', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    return df


def health_determinant_eurostat_daily_smokers_income_quintile(
        df: pd.DataFrame) -> pd.DataFrame:
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
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['quant_inc']+'_'+df['sex']+\
        '_'+'DailySmokers'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['quant_inc']+'_'+df['sex']
    df.drop(columns=['smoking', 'quant_inc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    return df


def health_determinant_eurostat_daily_smokers_degree_of_urbanisation(
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
    df['SV'] = 'Count_Person_'+ df['deg_urb']+'_'+df['sex']+\
        '_'+'DailySmokers'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['deg_urb']+'_'+df['sex']
    df.drop(columns=['smoking', 'deg_urb', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def health_determinant_eurostat_daily_exposure_to_tobacco_smoke_indoors_education_attainment_level(
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
    df['SV'] = 'Count_Person_'+ df['isced11']+'_'+df['sex']+\
        '_'+'DailyExposureToTobaccoSmokeIndoors'+'_'+df['frequenc']+\
        '_AsAFractionOf_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['frequenc', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    return df


def health_determinant_eurostat_daily_exposure_to_tobacco_smoke_indoors_degree_of_urbanisation(
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
    df['SV'] = 'Count_Person_'+ df['deg_urb']+'_'+df['sex']+\
        '_'+'DailyExposureToTobaccoSmokeIndoors'+'_'+df['frequenc']+\
        '_AsAFractionOf_Count_Person_'+df['deg_urb']+'_'+df['sex']
    df.drop(columns=['frequenc', 'deg_urb', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def health_determinant_eurostat_duration_of_daily_tobacco_smoking_education_attainment_level(
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
    df['SV'] = 'Count_Person_'+ df['isced11']+'_'+df['sex']+\
        '_'+'DurationOfDailyTobaccoSmoking'+'_'+df['duration']+\
        '_AsAFractionOf_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['duration', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def health_determinant_eurostat_electronic_cigarettes_similar_electronic_devices_education_attainment_level(
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
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['isced11']+'_'+df['sex']+'_'\
        +'UsageOfElectronicCigarettesOrSimilarElectronicDevices'+'_'+df['frequenc']+\
        '_AsAFractionOf_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['frequenc', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def health_determinant_eurostat_daily_smokers_history_education_attainment_level(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'sex,age,isced97,time', 'BE', 'BG', 'CZ', 'DE', 'EE', 'EL', 'ES', 'CY',
        'LV', 'HU', 'MT', 'AT', 'PL', 'RO', 'SI', 'SK'
    ]
    df.columns = cols
    col1 = "sex,age,isced97,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = _replace_isced97(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['isced97']+'_'+df['sex']+'_'\
        +'DailySmokersHistory'+\
        '_AsAFractionOf_Count_Person_'+df['isced97']+'_'+df['sex']
    df.drop(columns=['isced97', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def health_determinant_eurostat_daily_smokers_history_income_quintile(
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
    df = df[df['age'] == 'TOTAL']
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['quant_inc']+'_'+df['sex']+\
        '_'+'DailySmokersHistory'+\
        '_AsAFractionOf_Count_Person_'+df['quant_inc']+'_'+df['sex']
    df.drop(columns=['quant_inc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def health_determinant_eurostat_daily_smokers_number_of_cigarettes_history_education_attainment_level(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'sex,age,smoking,isced97,time', 'BE', 'BG', 'CZ', 'DE', 'EE', 'EL',
        'ES', 'CY', 'LV', 'HU', 'MT', 'PL', 'RO', 'SI', 'SK'
    ]
    df.columns = cols
    col1 = "sex,age,smoking,isced97,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = _replace_isced97(df)
    df = _replace_smoking(df)
    df = _replace_sex(df)
    df.drop(columns=['age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['isced97']+'_'+df['sex']+\
        '_'+'DailySmokersByNumberOfCigarettesHistory'+'_'+\
        df['smoking']+'_AsAFractionOf_Count_Person_'+df['isced97']+'_'+df['sex']
    df.drop(columns=['smoking', 'isced97', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def _replace_sex(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {'F': 'Female', 'M': 'Male', 'T': 'Total'}
    df = df.replace({'sex': _dict})
    return df


def _replace_isced11(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df = df.replace({'isced11': {
        'ED0-2': 'EducationalAttainment'+\
        'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
        'ED0_2': 'EducationalAttainment'+\
        'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
        'ED3-4': 'EducationalAttainment'+\
        'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
        'ED3_4': 'EducationalAttainment'+\
            'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
        'ED5_6': 'EducationalAttainment'+\
            'FirstAndSecondStageOfTertiaryEducation',
        'ED5-8': 'EducationalAttainmentTertiaryEducation',
        'ED5_8': 'EducationalAttainmentTertiaryEducation',
        'TOTAL': 'Total'
        }})
    return df


def _replace_isced97(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df = df.replace({'isced97': {
        'ED0-2': 'EducationalAttainment'+\
        'PrePrimary_PrimaryAndLowerSecondaryEducation',
        'ED3_4': 'EducationalAttainment'+\
            'UpperSecondaryEducationAndPostSecondaryNonTertiaryEducation',
        'ED5_6': 'EducationalAttainment'+\
            'FirstAndSecondStageOfTertiaryEducation',
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
            'QU1': 'FirstQuintile',
            'QU2': 'SecondQuintile',
            'QU3': 'ThirdQuintile',
            'QU4': 'FourthQuintile',
            'QU5': 'FifthQuintile',
            'UNK': 'Unknown'
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
            'DEG1': 'Cities',
            'DEG2': 'TownsAndSuburbs',
            'DEG3': 'RuralAreas'
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
            'SM_CUR': 'CurrentSmoker',
            'SM_DAY': 'DailySmoker',
            'SM_OCC': 'OccasionalSmoker',
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
            'EU28_FOR': 'CountryOfBirthEU28CountriesExceptReportingCountry',
            'NEU28_FOR': 'CountryOfBirthNonEU28CountriesNorReportingCountry',
            'FOR': 'CountryOfBirthForeignCountry',
            'NAT': 'CountryOfBirthReportingCountry'
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
            'EU28_FOR': 'CitizenshipEU28CountriesExceptReportingCountry',
            'NEU28_FOR': 'CitizenshipNonEU28CountriesNorReportingCountry',
            'FOR': 'CitizenshipForeignCountry',
            'NAT': 'CitizenshipReportingCountry'
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
            'DAY_GE1HD': 'AtLeast1HourEveryDay',
            'DAY_LT1HD': 'LessThan1HourEveryDay',
            'LT1W': 'LessThanOnceAWeek',
            'GE1W': 'AtLeastOnceAWeek',
            'RAR_NVR': 'RarelyOrNever',
            'DAY': 'EveryDay',
            'FMR': 'Formerly',
            'OCC': 'Occasionally',
            'NVR': 'Never'
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

    def __init__(self, input_files: list, csv_file_path: str,
                 tmcf_file_path: str) -> None:
        #  mcf_file_path: str, )
        self.input_files = input_files
        self.cleaned_csv_file_path = csv_file_path
        # self.mcf_file_path = mcf_file_path
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
        with open(self.tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf_template.rstrip('\n'))

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
            df = pd.read_csv(file_path, sep='\t', skiprows=1)
            file_name = file_path.split("/")[-1][:-4]
            function_dict = {
                "hlth_ehis_sk1b":
                    health_determinant_eurostat_smoking_county_of_birth,
                "hlth_ehis_sk1c":
                    health_determinant_eurostat_smoking_country_of_citizenship,
                "hlth_ehis_sk1e":
                    health_determinant_eurostat_smoking_education_attainment_level,
                "hlth_ehis_sk1i":
                    health_determinant_eurostat_smoking_income_quintile,
                "hlth_ehis_sk1u":
                    health_determinant_eurostat_smoking_degree_of_urbanisation,
                "hlth_ehis_sk2i":
                    health_determinant_eurostat_former_daily_tobacco_smoker_income_quintile,
                "hlth_ehis_sk2e":
                    health_determinant_eurostat_former_daily_tobacco_smoker_education_attainment_level,
                "hlth_ehis_sk3e":
                    health_determinant_eurostat_daily_smokers_education_attainment_level,
                "hlth_ehis_sk3i":
                    health_determinant_eurostat_daily_smokers_income_quintile,
                "hlth_ehis_sk3u":
                    health_determinant_eurostat_daily_smokers_degree_of_urbanisation,
                "hlth_ehis_sk4e":
                    health_determinant_eurostat_daily_exposure_to_tobacco_smoke_indoors_education_attainment_level,
                "hlth_ehis_sk4u":
                    health_determinant_eurostat_daily_exposure_to_tobacco_smoke_indoors_degree_of_urbanisation,
                "hlth_ehis_sk5e":
                    health_determinant_eurostat_duration_of_daily_tobacco_smoking_education_attainment_level,
                "hlth_ehis_sk6e":
                    health_determinant_eurostat_electronic_cigarettes_similar_electronic_devices_education_attainment_level,
                "hlth_ehis_de3":
                    health_determinant_eurostat_daily_smokers_history_education_attainment_level,
                "hlth_ehis_de4":
                    health_determinant_eurostat_daily_smokers_history_income_quintile,
                "hlth_ehis_de5":
                    health_determinant_eurostat_daily_smokers_number_of_cigarettes_history_education_attainment_level
            }
            df = function_dict[file_name](df)
            df['SV'] = df['SV'].str.replace('_Total', '')
            df['Measurement_Method'] = np.where(
                df['observation'].str.contains('u'),
                'LowReliability/EurostatRegionalStatistics',
                'EurostatRegionalStatistics')
            df['observation'] = (df['observation'].str.replace(
                ':', '').str.replace(' ', '').str.replace('u', ''))
            df['observation'].replace('', np.nan, inplace=True)
            df.dropna(subset=['observation'], inplace=True)
            df['observation'] = pd.to_numeric(df['observation'],
                                              errors='coerce')
            final_df = pd.concat([final_df, df])
            sv_list += df["SV"].to_list()

        final_df = final_df.sort_values(by=['time', 'geo', 'SV'])
        final_df = final_df.replace({'geo': COUNTRY_MAP})
        final_df.to_csv(self.cleaned_csv_file_path, index=False)
        sv_list = list(set(sv_list))
        sv_list.sort()
        # self._generate_mcf(sv_list)
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
    # mcf_name = "eurostat_population_physicalactivity.mcf"
    tmcf_name = "eurostat_population_tobaccocunsumption.tmcf"
    cleaned_csv_path = data_file_path + os.sep + csv_name
    # mcf_path = data_file_path + os.sep + mcf_name
    tmcf_path = data_file_path + os.sep + tmcf_name
    loader = EuroStatTobaccoConsumption(ip_files, cleaned_csv_path, tmcf_path)
    # , mcf_path,\
    loader.process()


if __name__ == "__main__":
    app.run(main)
