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
and generates cleaned CSV, MCF, TMCF file
"""
from sys import path
# For import common.replacement_functions
# path.insert(1, '../')
# from common.replacement_functions import (_replace_sex, _replace_frequenc,
#                                           _replace_isced11, _replace_quant_inc,
#                                           _replace_deg_urb, _replace_c_birth,
#                                           _replace_citizen, _split_column)
# For import util.alpha2_to_dcid
path.insert(1, '../../../../')

import os
import pandas as pd
import numpy as np
from util.alpha2_to_dcid import COUNTRY_MAP
from absl import app
from absl import flags

_FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_files"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

#health_determinant_eurostat_alcoholconsumption_education_attainment
def hlth_ehis_al1e(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_al1e for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,frequenc,isced11,sex,age,geo', '2019', '2014']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,frequenc,isced11,sex,age,geo"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns    
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    # giving proper statvar name
    df['SV'] = 'Count_Person_'+df['isced11']+'_'+df['sex']+'_AlcoholConsumption_'+\
        df['frequenc']+'_AsAFractionOf_Count_Person_'+\
            df['isced11']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['unit','age','isced11','frequenc','sex'],inplace=True)
    # ask
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df

#health_determinant_eurostat_alcoholconsumption_income_quintile
def hlth_ehis_al1i(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_al1i for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,quant_inc,frequenc,sex,age,geo', '2019', '2014']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,quant_inc,frequenc,sex,age,geo"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]    
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_quant_inc(df)
    # giving proper statvar name
    df['SV'] = 'Count_Person_'+df['quant_inc']+'_'+df['sex']\
        +'_AlcoholConsumption_'+df['frequenc']\
            +'_AsAFractionOf_Count_Person_'+df['quant_inc']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['quant_inc','frequenc','sex','age','unit'],inplace=True)
    # ask
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    return df

#health_determinant_eurostat_alcoholconsumption_degree_of_urbanisation
def hlth_ehis_al1u(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_al1u for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['frequenc,deg_urb,sex,age,unit,time','EU27_2020','EU28','BE','BG',
    'CZ','DK','DE','EE','IE','EL','ES','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "frequenc,deg_urb,sex,age,unit,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_frequenc(df)
    # giving proper statvar name
    df['SV'] = 'Count_Person_'+df['sex']+'_'+'AlcoholConsumption'+\
        '_'+df['deg_urb']+'_'+df['frequenc']+'_AsAFractionOf_Count_Person_'+\
        df['sex']+'_'+df['deg_urb']
    # dropping unwanted columns
    df.drop(columns=['frequenc','deg_urb','sex','unit','age'],inplace=True)
    # ask
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

#health_determinant_eurostat_bingedrinking_education_attainment
def hlth_ehis_al3e(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_al3e for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,frequenc,isced11,sex,age,geo', '2019', '2014']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,frequenc,isced11,sex,age,geo"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    # giving proper statvar name
    df['SV'] = 'Count_Person_'+df['isced11']+'_'+df['sex']+'_BingeDrinking_'+\
        df['frequenc']+'_'+'AsAFractionOf_Count_Person_'+\
            df['isced11']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['unit','age','isced11','frequenc','sex'],inplace=True)
    # ask
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df

#health_determinant_eurostat_bingedrinking_income_quintile
def hlth_ehis_al3i(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_al3i for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,quant_inc,frequenc,sex,age,geo', '2019', '2014']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,quant_inc,frequenc,sex,age,geo"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_quant_inc(df)
    # giving proper statvar name
    df['SV'] = 'Count_Person_'+df['sex']+'_BingeDrinking_'+\
        +df['quant_inc']+'_'+df['frequenc']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['quant_inc']
    # dropping unwanted columns
    df.drop(columns=['unit','age','quant_inc','frequenc','sex'],inplace=True)
    # ask
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df

#health_determinant_eurostat_bingedrinking_degree_of_urbanisation
def hlth_ehis_al3u(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_al3u for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['frequenc,deg_urb,sex,age,unit,time','EU27_2020','EU28','BE','BG',
    'CZ','DK','DE','EE','IE','EL','ES','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "frequenc,deg_urb,sex,age,unit,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_frequenc(df)
    # giving proper statvar name
    df['SV'] = 'Count_Person_'+df['sex']+'_'+'BingeDrinking'+\
        '_'+df['deg_urb']+'_'+df['frequenc']+'_AsAFractionOf_Count_Person_'+\
            df['sex']+'_'+df['deg_urb']
    # dropping unwanted columns
    df.drop(columns=['frequenc','deg_urb','sex','unit','age'],inplace=True)
    # ask
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

#health_determinant_eurostat_hazardousalcoholconsumption_education_attainment
def hlth_ehis_al2e(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_al2e for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,isced11,sex,age,time', 'EU27_2020', 'EU28', 'BE', 'BG', 'CZ', 'DK'
    ,'DE', 'EE', 'IE', 'EL', 'ES', 'HR', 'IT', 'CY', 'LV', 'LT', 'LU', 'HU', 'MT',
    'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS', 'NO', 'UK', 'TR' ]
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,isced11,sex,age,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    # giving proper statvar name
    df['SV'] = 'Count_Person_'+df['isced11']+'_'+df['sex']\
        +'_HazardousAlcoholConsumption_AsAFractionOf_Count_Person_'\
            +df['isced11']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['unit','age','isced11','sex'],inplace=True)
    # ask
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df

#health_determinant_eurostat_hazardousalcoholconsumption_income_quintile
def hlth_ehis_al2i(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_al2i for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,quant_inc,sex,age,time','EU27_2020','EU28','BE','BG',
    'CZ','DK','DE','EE','IE','EL','ES','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,quant_inc,sex,age,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_sex(df)
    df = _replace_quant_inc(df)
    # giving proper statvar name
    df['SV'] = 'Count_Person_'+df['sex']+'_'+\
        +df['quant_inc']+'_'+'HazardousAlcoholConsumption'+'_'+\
            'AsAFractionOf_Count_Person_'+df['sex']+'_'+df['quant_inc']
    # dropping unwanted columns
    df.drop(columns=['unit','age' ,'quant_inc','sex'],inplace=True)
    # ask
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df

#health_determinant_eurostat_hazardousalcoholconsumption_degree_of_urbanisation
def hlth_ehis_al2u(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_al2u for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['deg_urb,sex,age,unit,time','EU27_2020','EU28','BE','BG',
    'CZ','DK','DE','EE','IE','EL','ES','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "deg_urb,sex,age,unit,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    # giving proper statvar name
    df['SV'] = 'Count_Person_'+df['sex']+'_'+'HazardousAlcoholConsumption'+\
        '_'+df['deg_urb']+'_AsAFractionOf_Count_Person_'+\
        df['sex']+'_'+df['deg_urb']
    # dropping unwanted columns
    df.drop(columns=['deg_urb','sex','unit','age'],inplace=True)
    # ask
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

#health_determinant_eurostat_alcoholconsumption_country_of_birth
def hlth_ehis_al1b(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_al1b for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,frequenc,sex,age,c_birth,time','EU27_2020','EU28','BE','BG',
    'CZ','DK','DE','EE','IE','EL','ES','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,frequenc,sex,age,c_birth,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_c_birth(df)
    # giving proper statvar name
    df['SV'] = 'Count_Person_'+df['frequenc']+'_'+df['sex']\
        +'_'+'AlcoholConsumption'+'_'+df['c_birth']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['c_birth']
    # dropping unwanted columns
    df.drop(columns=['frequenc','c_birth','sex','unit','age'],inplace=True)
    # ask
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

#health_determinant_eurostat_alcoholconsumption_citizen
def hlth_ehis_al1c(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_al1c for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,frequenc,sex,age,citizen,time','EU27_2020','EU28','BE','BG',
    'CZ','DK','DE','EE','IE','EL','ES','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,frequenc,sex,age,citizen,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_citizen(df)
    # giving proper statvar name
    df['SV'] = 'Count_Person_'+df['citizen']+'_'+df['frequenc']+'_'+\
        df['sex']+'_AlcoholConsumption'+\
        '_AsAFractionOf_Count_Person_'+df['citizen']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['frequenc','citizen','sex','unit','age'],inplace=True)
    # ask
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

#health_determinant_eurostat_historical_alcoholconsumption_education_attainment
def hlth_ehis_de10(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_de10 for concatenation in Final CSV.
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['sex,age,isced11,frequenc,unit,time','BE','BG','CZ','EL',
        'ES','FR','CY','LV','HU','MT','PL','RO','SI','SK','TR']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "sex,age,isced11,frequenc,unit,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df = _replace_isced11(df)
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    # giving proper statvar name
    df['SV'] = 'Count_Person_'+df['isced11']+'_'+df['sex']+'_AlcoholConsumption_'+\
        df['frequenc']+'_AsAFractionOf_Count_Person_'+\
            df['isced11']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['isced11','sex','age','frequenc','unit'],inplace=True)
    # ask
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

#health_determinant_eurostat_historical_bingedrinking_education_attainment
def hlth_ehis_de6(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_de6 for concatenation in Final CSV.
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['frequenc,sex,age,isced11,time','BE','BG','CZ','EL',
        'ES','CY','LV','HU','MT','RO','SI','SK']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "frequenc,sex,age,isced11,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df = _replace_isced11(df)
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    # giving proper statvar name
    df['SV'] = 'Count_Person_'+df['isced11']+'_'+df['sex']+'_BingeDrinking_'+\
        df['frequenc']+'_AsAFractionOf_Count_Person_'+\
            df['isced11']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['isced11','sex','age','frequenc'],inplace=True)
    # ask
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def _split_column(df: pd.DataFrame,col: str) -> pd.DataFrame:
    """
    Divides a single column into multiple columns and returns the DF
    """
    info = col.split(",")
    df[info] = df[col].str.split(',', expand=True)
    df.drop(columns=[col],inplace=True)
    return df

def _replace_frequenc(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.
    Args: 
        df (pd.DataFrame): df as the input, to change column values
    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({'frequenc': {
        'DAY': 'DailyUsage',
        'LT1M': 'LessThanOnceAMonth',
        'MTH': 'EveryMonth',
        'NM12': 'NotUsedInTheLast12Months',
	    'NVR': 'NeverUsed',
	    'NVR_NM12': 'NeverUsedOrNotUsedInTheLast12Months',
        'WEEK': 'EveryWeek',
        'GE1W': 'AtLeastOnceAWeek',
        'NVR_OCC': 'NeverUsedOrOccasionallyUsage',
        'NBINGE': 'NeverUsed'}})
    return df

def _replace_sex(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df = df.replace({'sex': {
        'F': 'Female',
        'M': 'Male',
        'T': 'Total'}})
    return df

def _replace_isced11(df:pd.DataFrame) -> pd.DataFrame:
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
        'ED5_6' : 'TertiaryEducationStageOneOrTertiaryEducationStageTwo',
        'ED5-8': 'EducationalAttainmentTertiaryEducation',
        'ED5_8': 'EducationalAttainmentTertiaryEducation',
        'TOTAL': 'Total'
        }})
    return df

def _replace_quant_inc(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.
    Args: 
        df (pd.DataFrame): df as the input, to change column values
    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({'quant_inc': {
        'TOTAL': 'Total',
        'QU1': 'IncomeOf0To20Percentile',
        'QU2': 'IncomeOf20To40Percentile',
        'QU3': 'IncomeOf40To60Percentile',
        'QU4': 'IncomeOf60To80Percentile',
        'QU5': 'IncomeOf80To100Percentile'
        }})
    return df

def _replace_deg_urb(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df = df.replace({'deg_urb': {
        'TOTAL':'Total',
        'DEG1':'Urban',
        'DEG2':'SemiUrban',
        'DEG3':'Rural',
        }})
    return df

def _replace_c_birth(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df = df.replace({'c_birth': {
        'EU28_FOR': 'ForeignBornWithinEU28',
        'NEU28_FOR': 'ForeignBornOutsideEU28',
        'FOR': 'ForeignBorn',
        'NAT': 'Native'
    }})
    return df

def _replace_citizen(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df = df.replace({'citizen': {
        'EU28_FOR': 'ForeignWithinEU28',
        'NEU28_FOR': 'ForeignOutsideEU28',
        'FOR': 'NotACitizen',
        'NAT': 'Citizen'
    }})
    return df

class EuroStatAlcoholConsumption:
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
            "Node: E:EuroStat_Population_AlcoholConsumption->E0\n"
            "typeOf: dcs:StatVarObservation\n"
            "variableMeasured: C:EuroStat_Population_AlcoholConsumption->SV\n"
            "measurementMethod: C:EuroStat_Population_AlcoholConsumption->"
            "Measurement_Method\n"
            "observationAbout: C:EuroStat_Population_AlcoholConsumption->geo\n"
            "observationDate: C:EuroStat_Population_AlcoholConsumption->time\n"
            "value: C:EuroStat_Population_AlcoholConsumption->observation\n")
        # Writing Genereated TMCF to local path.
        with open(self.tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf_template.rstrip('\n'))

    def _generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template
        Arguments:
            df_columns (list) : List of DataFrame Columns
        Returns:
            None
        """
        # pylint: disable=R0914
        # pylint: disable=R0912
        # pylint: disable=R0915
        mcf_template = ("Node: dcid:{}\n"
                        "typeOf: dcs:StatisticalVariable\n"
                        "populationType: dcs:Person{}{}{}{}{}{}{}{}\n"
                        "statType: dcs:measuredValue\n"
                        "measuredProperty: dcs:count\n")
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            incomequin = gender = education = frequenc = healthbehavior =\
            residence = countryofbirth = citizenship = ''

            sv_temp = sv.split("_AsAFractionOf_")
            denominator = "\nmeasurementDenominator: dcs:" + sv_temp[1]
            sv_prop = sv_temp[0].split("_")

            for prop in sv_prop:
                if prop in ["Count", "Person"]:
                    continue
                if "AlcoholConsumption" in prop or "BingeDrinking" in prop\
                    or "HazardousAlcoholConsumption" in prop:
                    healthbehavior = "\nhealthBehavior: dcs:" + prop
                elif "Male" in prop or "Female" in prop:
                    gender = "\ngender: dcs:" + prop
                elif "DailyUsage" in prop or "LessThanOnceAMonth" in prop \
                    or "EveryMonth" in prop or "NotUsedInTheLast12Months" in prop\
                    or "NeverUsed" in prop or "NeverUsedOrNotUsedInTheLast12Months" in prop \
                    or "EveryWeek" in prop or "AtLeastOnceAWeek" in prop\
                    or "NeverUsedOrOccasionallyUsage" in prop:
                    frequenc = "\nsubstanceUsageFrequency: dcs:" + prop\
                        .replace("Or","__")
                elif "Education" in prop:
                    education = "\neducationalAttainment: dcs:" + \
                        prop.replace("EducationalAttainment","")\
                        .replace("Or","__")
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
                    citizenship = "\ncitizenship: dcs:" + \
                        prop.replace("Citizenship","")

            final_mcf_template += mcf_template.format(
                sv, denominator, healthbehavior, gender,
                frequenc, education, incomequin,
                residence, countryofbirth,
                citizenship) + "\n"

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
            df = pd.read_csv(file_path, sep='\t', skiprows=1)
            file_name = file_path.split("/")[-1][:-4]
            function_dict = {
                "hlth_ehis_al1b": hlth_ehis_al1b,
                "hlth_ehis_al1c": hlth_ehis_al1c,
                "hlth_ehis_al1e": hlth_ehis_al1e,
                "hlth_ehis_al1i": hlth_ehis_al1i,
                "hlth_ehis_al1u": hlth_ehis_al1u,
                "hlth_ehis_al2e": hlth_ehis_al2e,
                "hlth_ehis_al2i": hlth_ehis_al2i,
                "hlth_ehis_al2u": hlth_ehis_al2u,
                "hlth_ehis_al3e": hlth_ehis_al3e,
                "hlth_ehis_al3i": hlth_ehis_al3i,
                "hlth_ehis_al3u": hlth_ehis_al3u,
                "hlth_ehis_de6": hlth_ehis_de6,
                "hlth_ehis_de10": hlth_ehis_de10
            }
            df = function_dict[file_name](df)
            df['SV'] = df['SV'].str.replace('_Total', '')
            df['Measurement_Method'] = 'EurostatRegionalStatistics'
            df['Measurement_Method'] = np.where(
                df['observation'].str.contains('u'),
                'LowReliability/EurostatRegionalStatistics',
                df['Measurement_Method'])
            df['Measurement_Method'] = np.where(
                df['observation'].str.contains('d'),
                'DefinitionDiffers/EurostatRegionalStatistics',
                df['Measurement_Method'])
            df['observation'] = (df['observation'].str.replace(
                ':', '').str.replace(' ', '').str.replace('u', '')
                .str.replace('d', ''))
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
    input_path = _FLAGS.input_path
    if not os.path.exists(input_path):
        os.mkdir(input_path)
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]
    data_file_path = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "output"
    # Defining Output Files
    csv_name = "eurostat_population_alcoholconsumption.csv"
    mcf_name = "eurostat_population_alcoholconsumption.mcf"
    tmcf_name = "eurostat_population_alcoholconsumption.tmcf"
    cleaned_csv_path = data_file_path + os.sep + csv_name
    mcf_path = data_file_path + os.sep + mcf_name
    tmcf_path = data_file_path + os.sep + tmcf_name
    loader = EuroStatAlcoholConsumption(ip_files, cleaned_csv_path,\
        mcf_path, tmcf_path) 
    loader.process()

if __name__ == "__main__":
    app.run(main)
