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
# For import common.replacement_functions
path.insert(1, '../')
from common.replacement_functions import (_replace_sex, _replace_physact,
                                          _replace_isced11, _replace_quant_inc,
                                          _replace_deg_urb, _replace_levels,
                                          _replace_duration, _replace_c_birth,
                                          _replace_citizen, _replace_lev_limit,
                                          _replace_bmi, _split_column)
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


def healthenhancing_by_sex_education(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file healthenhancing_by_sex_education for concatenation
    in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = ['unit,physact,isced11,sex,age,geo', '2019', '2014']
    df.columns = cols
    col1 = "unit,physact,isced11,sex,age,geo"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    df['SV'] = 'Count_Person_'+df['isced11']+'_'+ df['physact'] +'_'+df['sex']+\
        '_'+'HealthEnhancingPhysicalActivity_AsAFractionOf_Count_Person_'+\
        df['isced11']+'_'+df['sex']
    df.drop(columns=['unit', 'age', 'isced11', 'physact', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df


def healthenhancing_by_sex_income(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file healthenhancing_by_sex_income for concatenation
    in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'unit,physact,quant_inc,sex,age,time', 'EU27_2020', 'EU28', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS',
        'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "unit,physact,quant_inc,sex,age,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_quant_inc(df)
    df['SV'] = 'Count_Person_'+ df['physact'] +'_'+df['sex']+\
        '_'+'HealthEnhancingPhysicalActivity'+'_'+df['quant_inc']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['quant_inc']
    df.drop(columns=['unit', 'age', 'quant_inc', 'physact', 'sex'],
            inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def healthenhancing_by_sex_urbanisation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file healthenhancing_by_sex_urbanisation
    for concatenation in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'physact,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS',
        'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "physact,deg_urb,sex,age,unit,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_deg_urb(df)
    df['SV'] = 'Count_Person_'+ df['physact'] +'_'+df['sex']+\
        '_'+'HealthEnhancingPhysicalActivity'+'_'+df['deg_urb']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['deg_urb']
    df.drop(columns=['unit', 'age', 'deg_urb', 'physact', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def workrelated_by_sex_education(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file workrelated_by_sex_education for concatenation in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'unit,levels,isced11,sex,age,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE',
        'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "unit,levels,isced11,sex,age,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_isced11(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df['SV'] = 'Count_Person_'+ df['isced11']+'_'+df['sex']+\
        '_'+'WorkRelatedPhysicalActivity'+'_'+df['levels']+\
        '_AsAFractionOf_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['unit', 'age', 'levels', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def workrelated_by_sex_income(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file workrelated_by_sex_income for concatenation
    in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'unit,levels,quant_inc,sex,age,time', 'EU27_2020', 'EU28', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS',
        'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "unit,levels,quant_inc,sex,age,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df['SV'] = 'Count_Person_'+df['sex']+\
        '_'+'WorkRelatedPhysicalActivity'+'_'+df['quant_inc']+'_'+df['levels']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['quant_inc']
    df.drop(columns=['unit', 'age', 'levels', 'quant_inc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def workrelated_by_sex_urbanisation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file workrelated_by_sex_urbanisation for concatenation
    in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'levels,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS',
        'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "levels,deg_urb,sex,age,unit,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+df['sex']+'_'+'WorkRelatedPhysicalActivity'+\
        '_'+df['levels']+'_'+df['deg_urb']+'_AsAFractionOf_Count_Person_'+\
        df['sex']+'_'+df['deg_urb']
    df.drop(columns=['levels', 'deg_urb', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def nonworkrelated_by_sex_education(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file nonworkrelated_by_sex_education for concatenation 
    in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = ['unit,physact,isced11,sex,age,geo', '2019', '2014']
    df.columns = cols
    col1 = "unit,physact,isced11,sex,age,geo"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    df['SV'] = 'Count_Person_'+df['isced11']+'_'+ df['physact'] +'_'+df['sex']+\
        '_'+'NonWorkRelatedPhysicalActivity'+'_AsAFractionOf_Count_Person_'+\
        df['isced11']+'_'+df['sex']
    df.drop(columns=['unit', 'age', 'isced11', 'physact', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df


def nonworkrelated_by_sex_income(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file nonworkrelated_by_sex_income for concatenation in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = ['unit,physact,quant_inc,sex,age,geo', '2019', '2014']
    df.columns = cols
    col1 = "unit,physact,quant_inc,sex,age,geo"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_quant_inc(df)
    df['SV'] = 'Count_Person_'+df['physact']+'_'+df['sex']+\
        '_'+'NonWorkRelatedPhysicalActivity'+'_'+df['quant_inc']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['quant_inc']
    df.drop(columns=['unit', 'age', 'quant_inc', 'physact', 'sex'],
            inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    df = df.drop(
        df[(df['SV'] == 'Count_Person_Cycling_Female_NonWorkRelated'
            'PhysicalActivity_Total_AsAFractionOf_Count_Person_Female_Total') &
           (df['geo'] == 'BE') & (df['time'] == '2014')].index)
    return df


def nonworkrelated_by_sex_urbanisation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file nonworkrelated_by_sex_urbanisation
    for concatenation in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'physact,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS',
        'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "physact,deg_urb,sex,age,unit,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_physact(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+df['physact']+'_'+df['sex']+'_'+\
        'NonWorkRelatedPhysicalActivity'+'_'+df['deg_urb']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['deg_urb']
    df.drop(columns=['physact', 'deg_urb', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def healthenhancing_nonworkrelated_by_sex_education(df: pd.DataFrame)\
                                                -> pd.DataFrame:
    """
    Cleans the file healthenhancing_nonworkrelated_by_sex_education
    for concatenation in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = ['unit,duration,isced11,sex,age,geo', '2019', '2014']
    df.columns = cols
    col1 = "unit,duration,isced11,sex,age,geo"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_duration(df)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    df['SV'] = 'Count_Person_'+df['duration']+'_'+df['isced11']+'_'+df['sex']+\
        '_'+'HealthEnhancingPhysicalActivity'+'_AsAFractionOf_Count_Person_'+\
        df['isced11']+'_'+df['sex']
    df.drop(columns=['unit', 'age', 'duration', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df


def healthenhancing_nonworkrelated_by_sex_income(df: pd.DataFrame)\
                                                -> pd.DataFrame:
    """
    Cleans the file healthenhancing_nonworkrelated_by_sex_income
    for concatenation in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = ['unit,quant_inc,duration,sex,age,geo', '2019', '2014']
    df.columns = cols
    col1 = "unit,quant_inc,duration,sex,age,geo"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_duration(df)
    df = _replace_sex(df)
    df = _replace_quant_inc(df)
    df['SV'] = 'Count_Person_'+df['duration']+'_'+df['sex']+\
        '_'+'HealthEnhancingPhysicalActivity'+'_'+df['quant_inc']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['quant_inc']
    df.drop(columns=['unit', 'age', 'duration', 'quant_inc', 'sex'],
            inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df


def healthenhancing_nonworkrelated_by_sex_urbanisation(df: pd.DataFrame)\
                                                    -> pd.DataFrame:
    """
    Cleans the file healthenhancing_nonworkrelated_by_sex_urbanisation
    for concatenation in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'duration,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS',
        'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "duration,deg_urb,sex,age,unit,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_duration(df)
    df['SV'] = 'Count_Person_'+df['duration']+'_'+df['sex']+'_'+\
        'HealthEnhancingPhysicalActivity'+'_'+df['deg_urb']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['deg_urb']
    df.drop(columns=['unit', 'age', 'duration', 'deg_urb', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def healthenhancing_by_sex_nativity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file healthenhancing_by_sex_nativity for concatenation
    in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'unit,physact,c_birth,sex,age,time', 'EU27_2020', 'EU28', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS',
        'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "unit,physact,c_birth,sex,age,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_c_birth(df)
    df['SV'] = 'Count_Person_'+df['physact']+'_'+df['sex']\
        +'_'+'HealthEnhancingPhysicalActivity'+'_'+df['c_birth']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['c_birth']
    df.drop(columns=['unit', 'age', 'physact', 'c_birth', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def healthenhancing_by_sex_citizenship(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file healthenhancing_by_sex_citizenship
    for concatenation in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'unit,physact,sex,age,citizen,time', 'EU27_2020', 'EU28', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS',
        'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "unit,physact,sex,age,citizen,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_citizen(df)
    df['SV'] = 'Count_Person_'+df['citizen']+'_'+df['physact']+'_'+\
        df['sex']+'_'+'HealthEnhancingPhysicalActivity'+\
        '_AsAFractionOf_Count_Person_'+df['citizen']+'_'+df['sex']
    df.drop(columns=['unit', 'age', 'physact', 'citizen', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def healthenhancing_by_sex_activitylimitation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file healthenhancing_by_sex_activitylimitation
    for concatenation in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'unit,physact,sex,age,lev_limit,time', 'EU27_2020', 'EU28', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS',
        'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "unit,physact,sex,age,lev_limit,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_lev_limit(df)
    df['SV'] = 'Count_Person_'+df['physact']+'_'+df['sex']\
        +'_'+'HealthEnhancingPhysicalActivity'+'_'+df['lev_limit']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['lev_limit']
    df.drop(columns=['unit', 'age', 'physact', 'lev_limit', 'sex'],
            inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def healthenhancing_nonworkrelated_by_sex_bmi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file healthenhancing_nonworkrelated_by_sex_bmi
    for concatenation in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'unit,duration,bmi,sex,age,time', 'EU27_2020', 'BE', 'BG', 'CZ', 'DK',
        'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT', 'LU',
        'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'SE', 'IS', 'NO',
        'RS', 'TR'
    ]
    df.columns = cols
    col1 = "unit,duration,bmi,sex,age,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020'], inplace=True)
    df = _replace_duration(df)
    df = _replace_sex(df)
    df = _replace_bmi(df)
    df['SV'] = 'Count_Person_'+df['duration']+'_'+df['sex']\
        +'_'+'NonWorkRelatedPhysicalActivity'+'_'+df['bmi']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['bmi']
    df.drop(columns=['unit', 'age', 'bmi', 'duration', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def dailypractice_by_sex_education(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file dailypractice_by_sex_education for concatenation
    in Final CSV.

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'sex,age,isced11,time', 'BG', 'CZ', 'EL', 'ES', 'CY', 'LV', 'HU', 'MT',
        'AT', 'PL', 'RO', 'SK'
    ]
    df.columns = cols
    col1 = "sex,age,isced11,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df = _replace_isced11(df)
    df = _replace_sex(df)
    df['SV'] = 'Count_Person_'+df['isced11']+'_'+df['sex']+'_'+\
        'PhysicalActivity'+'_AsAFractionOf_Count_Person_'+df['sex']
    df.drop(columns=['isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['age','SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


class EuroStatPhysicalActivity:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    def __init__(self, input_files: list, csv_file_path: str,
                 mcf_file_path: str, tmcf_file_path: str) -> None:
        self.input_files = input_files
        self.cleaned_csv_file_path = csv_file_path
        self.mcf_file_path = mcf_file_path
        self.tmcf_file_path = tmcf_file_path

    def _generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.
        Args:
            None
        Returns:
            None
        """
        tmcf_template = (
            "Node: E:EuroStat_Population_PhysicalActivity->E0\n"
            "typeOf: dcs:StatVarObservation\n"
            "variableMeasured: C:EuroStat_Population_PhysicalActivity->SV\n"
            "measurementMethod: C:EuroStat_Population_PhysicalActivity->"
            "Measurement_Method\n"
            "observationAbout: C:EuroStat_Population_PhysicalActivity->geo\n"
            "observationDate: C:EuroStat_Population_PhysicalActivity->time\n"
            "value: C:EuroStat_Population_PhysicalActivity->observation\n")
        # Writing Genereated TMCF to local path.
        with open(self.tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf_template.rstrip('\n'))

    def _generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Args:
            df_cols (list) : List of DataFrame Columns

        Returns:
            None
        """
        # pylint: disable=R0914
        # pylint: disable=R0912
        # pylint: disable=R0915
        mcf_template = ("Node: dcid:{inp1}\n"
                        "typeOf: dcs:StatisticalVariable\n"
                        "populationType: dcs:Person{inp2}{inp3}{inp4}{inp5}"
                        "{inp6}{inp7}{inp8}{inp9}{inp10}{inp11}{inp12}{inp13}\n"
                        "statType: dcs:measuredValue\n"
                        "measuredProperty: dcs:count\n")
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            incomequin = gender = education = healthbehavior = exercise = ''
            residence = activity = duration = countryofbirth = citizenship = ''
            lev_limit = bmi = ''

            sv_temp = sv.split("_AsAFractionOf_")
            denominator = "\nmeasurementDenominator: dcs:" + sv_temp[1]
            sv_prop = sv_temp[0].split("_")

            for prop in sv_prop:
                if prop in ["Count", "Person"]:
                    continue
                if "PhysicalActivity" in prop:
                    healthbehavior = "\nhealthBehavior: dcs:" + prop
                elif "Male" in prop or "Female" in prop:
                    gender = "\ngender: dcs:" + prop
                elif "Aerobic" in prop or "MuscleStrengthening" in prop \
                    or "Walking" in prop or "Cycling" in prop:
                    exercise = "\nexerciseType: dcs:" + prop.replace("Or", "__")
                elif "Education" in prop:
                    education = "\neducationalAttainment: dcs:" + \
                        prop.replace("EducationalAttainment","")\
                        .replace("Or","__")
                elif "Percentile" in prop:
                    incomequin = "\nincome: ["+prop.replace("IncomeOf","")\
                        .replace("To"," ").replace("Percentile"," Percentile")\
                        +"]"
                elif "Urban" in prop or "Rural" in prop:
                    residence = "\nplaceOfResidenceClassification: dcs:" + prop
                elif "Limitation" in prop:
                    lev_limit = "\nglobalActivityLimitationindicator: dcs:"\
                        + prop
                elif "ModerateActivity" in prop or "HeavyActivity" in prop\
                    or "NoActivity" in prop:
                    activity = "\nphysicalActivityEffortLevel: dcs:"\
                        + prop.replace("ModerateActivityOrHeavyActivity",\
                        "ModerateActivity__HeavyActivity")
                elif "Minutes" in prop:
                    if "OrMoreMinutes" in prop:
                        duration = "\nactivityDuration: [" + prop.replace\
                            ("OrMoreMinutes","") + " - Minutes]"
                    elif "To" in prop:
                        duration = "\nactivityDuration: [" + prop.replace\
                            ("Minutes", "").replace("To", " ") + " Minutes]"
                    else:
                        duration = "\nactivityDuration: [Minutes " +\
                            prop.replace("Minutes","") + "]"
                elif "ForeignBorn" in prop or "Native" in prop:
                    countryofbirth = "\nnativity: dcs:" + \
                        prop.replace("CountryOfBirth","")
                elif "Citizen" in prop:
                    citizenship = "\ncitizenship: dcs:" + \
                        prop.replace("Citizenship","")
                elif "weight" in prop or "Normal" in prop \
                    or "Obese" in prop or "Obesity" in prop:
                    bmi = "__" + prop
                    healthbehavior = healthbehavior + bmi

            final_mcf_template += mcf_template.format(inp1=sv,
                                                      inp2=denominator,
                                                      inp3=incomequin,
                                                      inp4=education,
                                                      inp5=healthbehavior,
                                                      inp6=exercise,
                                                      inp7=residence,
                                                      inp8=activity,
                                                      inp9=duration,
                                                      inp10=gender,
                                                      inp11=countryofbirth,
                                                      inp12=citizenship,
                                                      inp13=lev_limit) + "\n"

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
        """

        final_df = pd.DataFrame(columns=['time','geo','SV','observation',\
            'Measurement_Method'])
        # Creating Output Directory
        output_path = os.path.dirname(self.cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_list = []

        for file_path in self.input_files:
            df = pd.read_csv(file_path, sep='\t', header=0)
            # Taking the File name out of the complete file address
            # Used -1 to pickup the last part which is file name
            # Read till -4 inorder to remove the .tsv extension
            file_name = file_path.split("/")[-1][:-4]
            function_dict = {
                "hlth_ehis_pe9e":
                    healthenhancing_by_sex_education,
                "hlth_ehis_pe9i":
                    healthenhancing_by_sex_income,
                "hlth_ehis_pe9u":
                    healthenhancing_by_sex_urbanisation,
                "hlth_ehis_pe1e":
                    workrelated_by_sex_education,
                "hlth_ehis_pe1i":
                    workrelated_by_sex_income,
                "hlth_ehis_pe1u":
                    workrelated_by_sex_urbanisation,
                "hlth_ehis_pe3e":
                    nonworkrelated_by_sex_education,
                "hlth_ehis_pe3i":
                    nonworkrelated_by_sex_income,
                "hlth_ehis_pe3u":
                    nonworkrelated_by_sex_urbanisation,
                "hlth_ehis_pe2e":
                    healthenhancing_nonworkrelated_by_sex_education,
                "hlth_ehis_pe2i":
                    healthenhancing_nonworkrelated_by_sex_income,
                "hlth_ehis_pe2u":
                    healthenhancing_nonworkrelated_by_sex_urbanisation,
                "hlth_ehis_pe9b":
                    healthenhancing_by_sex_nativity,
                "hlth_ehis_pe9c":
                    healthenhancing_by_sex_citizenship,
                "hlth_ehis_pe9d":
                    healthenhancing_by_sex_activitylimitation,
                "hlth_ehis_pe2m":
                    healthenhancing_nonworkrelated_by_sex_bmi,
                "hlth_ehis_de9":
                    dailypractice_by_sex_education
            }
            df = function_dict[file_name](df)
            df['SV'] = df['SV'].str.replace('_Total', '')
            df['Measurement_Method'] = np.where(
                df['observation'].str.contains('u'),
                'EurostatRegionalStatistics_LowReliability',
                'EurostatRegionalStatistics')
            df['observation'] = (df['observation'].astype(str).str.replace(
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
    csv_name = "eurostat_population_physicalactivity.csv"
    mcf_name = "eurostat_population_physicalactivity.mcf"
    tmcf_name = "eurostat_population_physicalactivity.tmcf"
    cleaned_csv_path = data_file_path + os.sep + csv_name
    mcf_path = data_file_path + os.sep + mcf_name
    tmcf_path = data_file_path + os.sep + tmcf_name
    loader = EuroStatPhysicalActivity(ip_files, cleaned_csv_path, mcf_path,\
        tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)
