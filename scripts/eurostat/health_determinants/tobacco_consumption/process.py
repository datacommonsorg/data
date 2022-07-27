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
The Python script loads the datasets, 
cleans them and generates the cleaned CSV, MCF and TMCF file.
"""
import os
import sys
import re
import pandas as pd
import numpy as np
from absl import app, flags
# For import common.replacement_functions
_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
# pylint: disable=import-error
# pylint: disable=wrong-import-position
from common.replacement_functions import (_replace_sex, _replace_isced11,
                                          _replace_deg_urb, _replace_quant_inc,
                                          _replace_duration, _replace_c_birth,
                                          _replace_citizen, _replace_smoking,
                                          _replace_smoking_frequenc,
                                          _split_column)
# For import util.alpha2_to_dcid
_COMMON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(1, _COMMON_PATH)
from util.alpha2_to_dcid import COUNTRY_MAP
# pylint: enable=import-error
# pylint: enable=wrong-import-position

_FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

_MCF_TEMPLATE = ("Node: dcid:{pv1}\n"
                 "{pv14}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Person{pv2}{pv3}{pv4}{pv5}"
                 "{pv6}{pv7}{pv8}{pv9}{pv10}{pv11}{pv12}{pv13}\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:count\n"
                 "")

_TMCF_TEMPLATE = (
    "Node: E:EuroStat_Population_TobaccoConsumption->E0\n"
    "typeOf: dcs:StatVarObservation\n"
    "variableMeasured: C:EuroStat_Population_TobaccoConsumption->SV\n"
    "measurementMethod: C:EuroStat_Population_TobaccoConsumption->"
    "Measurement_Method\n"
    "observationAbout: C:EuroStat_Population_TobaccoConsumption->geo\n"
    "observationDate: C:EuroStat_Population_TobaccoConsumption->time\n"
    "scalingFactor: 100\n"
    "value: C:EuroStat_Population_TobaccoConsumption->observation\n")


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
    df = df.drop(columns=['EU27_2020', 'EU28'])
    df = _replace_c_birth(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent'+\
        '_'+df['smoking']+"_"+'TobaccoProducts'+\
        '_In_Count_Person_'+df['sex']+'_'+df['c_birth']
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
    df = df.drop(columns=['EU27_2020', 'EU28'])
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
    df = df[(df['age'] == 'TOTAL') & (~(df['quant_inc'] == 'UNK'))]
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent'+\
        '_'+df['smoking']+'_TobaccoProducts'+\
        '_In_Count_Person_'+df['sex']+'_'+df['quant_inc']
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
    df = df.drop(columns=['EU27_2020', 'EU28'])
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
    df = df[(df['age'] == 'TOTAL') & (~(df['quant_inc'] == 'UNK'))]
    df = df.drop(columns=['EU27_2020'])
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_FormerSmoker_Daily_TobaccoProducts'+\
        '_In_Count_Person_'+df['sex']+'_'+df['quant_inc']
    df.drop(columns=['quant_inc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
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
    df = df.drop(columns=['EU27_2020'])
    df = _replace_isced11(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_FormerSmoker_Daily_TobaccoProducts'+\
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
    df['SV'] = 'Percent_Daily_'+df['smoking']+'_TobaccoSmoking'+'_Cigarettes'+\
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
    df = df[(df['age'] == 'TOTAL') & (~(df['quant_inc'] == 'UNK'))]
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_Daily'+'_'+df['smoking']+'_TobaccoSmoking'+\
        '_Cigarettes'+\
        '_In_Count_Person_'+df['sex']+'_'+df['quant_inc']
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
    df = df.drop(columns=['EU27_2020', 'EU28'])
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_Daily'+'_'+df['smoking']+'_TobaccoSmoking'+\
        '_Cigarettes'+\
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
    df = _replace_smoking_frequenc(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent'+'_'+df['frequenc']+'_ExposureToTobaccoSmoke'+\
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
    df = df.drop(columns=['EU27_2020', 'EU28'])
    df = _replace_deg_urb(df)
    df = _replace_smoking_frequenc(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent'+'_'+df['frequenc']+'_ExposureToTobaccoSmoke'+\
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
    df = df.drop(columns=['EU27_2020'])
    df = _replace_isced11(df)
    df = _replace_duration(df)
    df = _replace_sex(df)
    df = _replace_smoking(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_Daily_TobaccoSmoking_'+\
        df['duration']+'_TobaccoProducts'+\
        '_In_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['duration', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def ecigarettes_similar_elecdevices_education_attainment_level(
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
    df = df.drop(columns=['EU27_2020'])
    df = _replace_isced11(df)
    df = _replace_smoking_frequenc(df)
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
    df['SV'] = 'Percent_Daily_TobaccoSmoking'+\
        '_Cigarettes'+\
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
    df = df[(df['age'] == 'TOTAL') & (~(df['quant_inc'] == 'UNK'))]
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df.drop(columns=['age'], inplace=True)
    df['SV'] = 'Percent_Daily_TobaccoSmoking'+\
        '_Cigarettes'+\
        '_In_Count_Person_'+df['sex']+'_'+df['quant_inc']
    df.drop(columns=['quant_inc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def dsmokers_number_of_cigarettes_history_education_attainment_level(
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
    df['SV'] = 'Percent_Daily'+'_'+df['smoking']+'_TobaccoSmoking'+\
        '_Cigarettes'+\
        '_In_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['smoking', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
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
        # Writing Genereated TMCF to local path.
        with open(self.tmcf_file_path, 'w+', encoding="UTF-8") as f_out:
            f_out.write(_TMCF_TEMPLATE.rstrip('\n'))

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
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            incomequin = gender = education = frequenc = activity =\
            residence = countryofbirth = citizenship = substance\
            = quantity = history = sv_name = ''

            sv_temp = sv.split("_In_")
            denominator = "\nmeasurementDenominator: dcs:" + sv_temp[1]
            sv_prop = sv_temp[0].split("_")
            sv_prop1 = sv_temp[1].split("_")
            for prop in sv_prop:
                if prop in ["Percent"]:
                    sv_name = sv_name + "Percentage"
                elif  "TobaccoSmoking" in prop or "NonSmoker" in prop or\
                    "ExposureToTobaccoSmoke" in prop or "FormerSmoker" in prop:
                    activity = "\nhealthBehavior: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Daily" in prop or "Occasional" in prop\
                     or "AtLeastOneHourPerDay" in prop or \
                    "LessThanOneHourPerDay" in prop:
                    frequenc = "\nactivityFrequency: dcs:" + prop.replace(
                        "Or", "__")
                    sv_name = sv_name + prop + ", "
                elif "LessThanOnceAWeek" in prop or "AtLeastOnceAWeek" in\
                    prop or "RarelyOrNever" in prop :
                    frequenc = "\nactivityFrequency: dcs:" + prop.replace(
                        "Or", "__")
                    sv_name = sv_name + prop + ", "
                elif "LessThan20CigarettesPerDay"in prop or \
                    "20OrMoreCigarettesPerDay" in prop \
                    or "DailyCigaretteSmoker20OrMorePerDay" in prop or \
                    "DailyCigaretteSmokerLessThan20PerDay" in prop:
                    quantity = "\nconsumptionQuantity: "+prop.replace\
                    ("LessThan20CigarettesPerDay","[- 20 Cigarettes]")\
                    .replace("20OrMoreCigarettesPerDay","[20 - Cigarettes]")\
                    .replace("DailyCigaretteSmoker20OrMorePerDay",\
                    "[20 - Cigarettes]").replace\
                    ("DailyCigaretteSmokerLessThan20PerDay","[- 20 Cigarettes]")
                    sv_name = sv_name + prop + ", "
                elif "Cigarette" in prop or "ECigarettes" in prop:
                    substance = "\ntobaccoUsageType: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif 'LessThan1Year' in prop or 'From1To5Years' in prop or \
                    'From5To10Years' in prop or '10YearsOrOver' in prop:
                    history = "\nactivityDuration: " + prop.replace\
                    ("LessThan1Year","[- 1 Year]").replace\
                    ("From1To5Years","[Years 1 5]")\
                    .replace("From5To10Years","[Years 5 10]").\
                    replace("10YearsOrOver","[10 - Years]")
                    sv_name = sv_name + prop.replace("From","From ").\
                        replace("To"," To ").replace("Years"," Years").\
                            replace("Than","Than ")+ ", "

            sv_name = sv_name + "Among"
            for prop in sv_prop1:
                if prop in ["Count", "Person"]:
                    continue
                if "Male" in prop or "Female" in prop:
                    gender = "\ngender: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Education" in prop:
                    education = "\neducationalAttainment: dcs:" + \
                        prop.replace("Or","__")
                    sv_name = sv_name + prop + ", "
                elif "Percentile" in prop:
                    incomequin = "\nincome: ["+prop.replace("Percentile",
                        "").replace("IncomeOf","").replace("To"," ")+\
                            " Percentile]"
                    sv_name = sv_name + prop.replace("Of","Of ")\
                        .replace("To"," To ") + ", "
                elif "Urban" in prop or "SemiUrban" in prop \
                    or "Rural" in prop:
                    residence = "\nplaceOfResidenceClassification: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "ForeignBorn" in prop or "Native" in prop:
                    countryofbirth = "\nnativity: dcs:" + \
                        prop.replace("CountryOfBirth","")
                    sv_name = sv_name + prop + ", "
                elif "WithinEU28AndNotACitizen" in prop or \
                    "CitizenOutsideEU28" in prop\
                    or "Citizen" in prop or "NotACitizen" in prop:
                    citizenship = "\ncitizenship: dcs:"+\
                    prop.replace("Citizenship","")
                    sv_name = sv_name + prop + ", "

            sv_name = sv_name.replace(", Among", " Among")
            sv_name = sv_name.rstrip(', ')
            sv_name = sv_name.rstrip('with')
            # Adding spaces before every capital letter,
            # to make SV look more like a name.
            sv_name = re.sub(r"(\w)([A-Z])", r"\1 \2", sv_name)
            sv_name = "name: \"" + sv_name + " Population\""
            sv_name = sv_name.replace("AWeek","A Week")\
            .replace("Than20","Than 20").replace("ACitizen","A Citizen")
            final_mcf_template += _MCF_TEMPLATE.format(pv1=sv,
                                                       pv14=sv_name,
                                                       pv2=denominator,
                                                       pv3=frequenc,
                                                       pv4=gender,
                                                       pv5=activity,
                                                       pv6=education,
                                                       pv7=incomequin,
                                                       pv8=residence,
                                                       pv9=countryofbirth,
                                                       pv10=citizenship,
                                                       pv11=substance,
                                                       pv12=quantity,
                                                       pv13=history) + "\n"

        # Writing Genereated MCF to local path.
        with open(self.mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
        # pylint: enable=R0914

    def process(self):
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.
        Arguments: None
        Returns: None
        """

        final_df = pd.DataFrame(columns=['time','geo','SV','observation',
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
            tobbaco_consumption = {
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
                    ecigarettes_similar_elecdevices_education_attainment_level,
                "hlth_ehis_de3":
                    daily_smokers_cigarettes_history_education_attainment_level,
                "hlth_ehis_de4":
                    daily_smokers_cigarettes_history_income_quintile,
                "hlth_ehis_de5":
                    dsmokers_number_of_cigarettes_history_education_attainment_level
            }
            df = tobbaco_consumption[file_name](df)
            # df['file_name'] = file_name
            df['SV'] = df['SV'].str.replace('_Total', '')
            # df["file_name"] = file_name_without_ext
            final_df = pd.concat([final_df, df])
            sv_list += df["SV"].to_list()

        final_df = final_df.sort_values(by=['time', 'geo', 'SV', 'observation'])
        final_df = final_df.drop_duplicates(subset=['time','geo','SV'],
            keep='first')
        final_df['observation'] = final_df['observation'].astype(str)\
            .str.strip()
        # derived_df generated to get the year/SV/location sets
        # where 'u' exist
        derived_df = final_df[final_df['observation'].astype(str).str.contains(
            'u')]
        u_rows = list(derived_df['SV'] + derived_df['geo'])
        final_df['info'] = final_df['SV'] + final_df['geo']
        # Adding Measurement Method based on a condition
        final_df['Measurement_Method'] = np.where(
            final_df['info'].isin(u_rows),
            'EurostatRegionalStatistics_LowReliability',
            'EurostatRegionalStatistics')
        final_df.drop(columns=['info'], inplace=True)
        final_df['observation'] = (
            final_df['observation'].astype(str).str.replace(
                ':', '').str.replace(' ', '').str.replace('u', ''))
        final_df['observation'] = pd.to_numeric(final_df['observation'],
                                                errors='coerce')
        final_df = final_df.replace({'geo': COUNTRY_MAP})
        final_df = final_df.sort_values(by=['geo', 'SV'])
        final_df['observation'].replace('', np.nan, inplace=True)
        final_df.dropna(subset=['observation'], inplace=True)
        final_df = final_df.rename(
            columns={
                'time': 'Time',
                'geo': 'Geo',
                'SV': 'SV',
                'observation': 'Observation',
                'Measurement_Method': 'Measurement_Method'
            })
        final_df.to_csv(self.cleaned_csv_file_path, index=False)
        sv_list = list(set(sv_list))
        sv_list.sort()
        self._generate_mcf(sv_list)
        self._generate_tmcf()


def main(_):
    input_path = _FLAGS.input_path
    if not os.path.exists(input_path):
        os.mkdir(input_path)
    ip_files = os.listdir(input_path)
    ip_files = [os.path.join(input_path, file) for file in ip_files]
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output")
    # Defining Output Files
    csv_name = "eurostat_population_tobaccoconsumption.csv"
    mcf_name = "eurostat_population_tobaccoconsumption.mcf"
    tmcf_name = "eurostat_population_tobaccoconsumption.tmcf"
    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    tmcf_path = os.path.join(data_file_path, tmcf_name)
    loader = EuroStatTobaccoConsumption(ip_files, cleaned_csv_path, mcf_path,
                                        tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)
