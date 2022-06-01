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
import os
import sys
import pandas as pd
import numpy as np
sys.path.insert(0, 'util')
#from alpha2_to_dcid import COUNTRY_MAP
from absl import app
from absl import flags

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_files"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

def hlth_ehis_al1e(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_al1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,frequenc,isced11,sex,age,geo', '2019', '2014']
    df.columns=cols
    col1 = "unit,frequenc,isced11,sex,age,geo"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns    
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    df['SV'] = 'Count_Person_'+df['isced11']+'_'+df['sex']+'_'+'AlcoholConsumption'+'_'+\
        df['frequenc']+'_'+'AsAFractionOf_Count_Person_'+\
        df['isced11']+'_'+df['sex']
    df.drop(columns=['unit','age','isced11','frequenc','sex'],inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    df.to_csv('sample.csv')


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
    from metadata returns the DF
    """
    _frequenc = {
        'DAY': 'EveryDay',
        'LT1M': 'LessThanOnceAMonth',
        'MTH': 'EveryMonth',
        'NM12': 'NotInTheLast12Months',
	    'NVR': 'Never',
	    'NVR_NM12': 'NeverOrNotInTheLast12Month',
        'WEEK': 'EveryWeek'}
    df = df.replace({'frequenc': _frequenc})
    return df

def _replace_sex(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _sex = {
        'F': 'Female',
        'M': 'Male',
        'T': 'Total'
        }
    df = df.replace({'sex': _sex})
    return df

def _replace_isced11(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """

    _isced11 = {
        'ED0-2': 'EducationalAttainment'+\
        'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
        'ED0_2': 'EducationalAttainment'+\
        'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
        'ED3-4': 'EducationalAttainment'+\
        'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
        'ED3_4': 'EducationalAttainment'+\
            'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
        'ED5-8': 'EducationalAttainmentTertiaryEducation',
        'ED5_8': 'EducationalAttainmentTertiaryEducation',
        'TOTAL': 'Total'
        }
    df = df.replace({'isced11': _isced11})
    return df
df = pd.read_csv('/Users/sanikap/Alcohol_Consumption/input_files'+\
    '/hlth_ehis_al1e.tsv', sep='\t',skiprows=1)
hlth_ehis_al1e(df)