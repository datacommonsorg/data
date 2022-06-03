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
from alpha2_to_dcid import COUNTRY_MAP
from absl import app
from absl import flags

# pd.set_option("display.max_columns", None)
# pd.set_option("display.max_rows", None)

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_files"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

def hlth_ehis_pe9e(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,physact,isced11,sex,age,geo', '2019', '2014']
    df.columns=cols
    col1 = "unit,physact,isced11,sex,age,geo"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns    
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    df['SV'] = 'Count_Person_'+df['isced11']+'_'+ df['physact'] +'_'+df['sex']+\
        '_'+'HealthEnhancingPhysicalActivity_AsAFractionOf_Count_Person_'+\
        df['isced11']+'_'+df['sex']
    df.drop(columns=['unit','age','isced11','physact','sex'],inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df

def hlth_ehis_pe9i(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9i for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,physact,quant_inc,sex,age,time','EU27_2020','EU28','BG','CZ',
    'DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU','MT',
    'AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=cols
    col1 = "unit,physact,quant_inc,sex,age,time"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_quant_inc(df)
    df.drop(columns=['unit','age'],inplace=True)
    df['SV'] = 'Count_Person_'+ df['physact'] +'_'+df['sex']+\
        '_'+'HealthEnhancingPhysicalActivity'+'_'+df['quant_inc']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['quant_inc']
    df.drop(columns=['quant_inc','physact','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def hlth_ehis_pe9u(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9u for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['physact,deg_urb,sex,age,unit,time','EU27_2020','EU28','BG','CZ',
    'DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU','MT',
    'AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=cols
    col1 = "physact,deg_urb,sex,age,unit,time"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_deg_urb(df)
    df.drop(columns=['unit','age'],inplace=True)
    df['SV'] = 'Count_Person_'+ df['physact'] +'_'+df['sex']+\
        '_'+'HealthEnhancingPhysicalActivity'+'_'+df['deg_urb']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['deg_urb']
    df.drop(columns=['deg_urb','physact','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def hlth_ehis_sk1e(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,levels,isced11,sex,age,time','EU27_2020','EU28','BE','BG',
    'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=cols
    col1 = "unit,levels,isced11,sex,age,time"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_isced11(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df.drop(columns=['unit','age'],inplace=True)
    df['SV'] = 'Count_Person_'+ df['isced11']+'_'+df['sex']+\
        '_'+'WorkRelatedPhysicalActivity'+'_'+df['levels']+\
        '_AsAFractionOf_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['levels','isced11','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def hlth_ehis_pe1i(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1i for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,levels,quant_inc,sex,age,time','EU27_2020','EU28','BG',
    'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=cols
    col1 = "unit,levels,quant_inc,sex,age,time"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df.drop(columns=['unit','age'],inplace=True)
    df['SV'] = 'Count_Person_'+df['sex']+\
        '_'+'WorkRelatedPhysicalActivity'+'_'+df['quant_inc']+'_'+df['levels']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['quant_inc']
    df.drop(columns=['levels','quant_inc','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def hlth_ehis_pe1u(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1u for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['levels,deg_urb,sex,age,unit,time','EU27_2020','EU28','BG',
    'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=cols
    col1 = "levels,deg_urb,sex,age,unit,time"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df.drop(columns=['unit','age'],inplace=True)
    df['SV'] = 'Count_Person_'+df['sex']+'_'+'WorkRelatedPhysicalActivity'+\
        '_'+df['levels']+'_'+df['deg_urb']+'_AsAFractionOf_Count_Person_'+\
        df['sex']+'_'+df['deg_urb']
    df.drop(columns=['levels','deg_urb','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def hlth_ehis_pe3e(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe3e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,physact,isced11,sex,age,geo', '2019', '2014']
    df.columns=cols
    col1 = "unit,physact,isced11,sex,age,geo"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    df['SV'] = 'Count_Person_'+df['isced11']+'_'+ df['physact'] +'_'+df['sex']+\
        '_'+'NonWorkRelatedPhysicalActivity'+'_AsAFractionOf_Count_Person_'+\
        df['isced11']+'_'+df['sex']
    df.drop(columns=['unit','age','isced11','physact','sex'],inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df

def hlth_ehis_pe3i(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe3i for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,physact,quant_inc,sex,age,geo', '2019', '2014']
    df.columns=cols
    col1 = "unit,physact,quant_inc,sex,age,geo"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_quant_inc(df)
    df['SV'] = 'Count_Person_'+df['physact']+'_'+df['sex']+\
        '_'+'NonWorkRelatedPhysicalActivity'+'_'+df['quant_inc']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['quant_inc']
    df.drop(columns=['unit','age','quant_inc','physact','sex'],inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df

def hlth_ehis_pe3u(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe3u for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['physact,deg_urb,sex,age,unit,time','EU27_2020','EU28','BG',
    'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=cols
    col1 = "physact,deg_urb,sex,age,unit,time"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_physact(df)
    df.drop(columns=['unit','age'],inplace=True)
    df['SV'] = 'Count_Person_'+df['physact']+'_'+df['sex']+'_'+\
        'NonWorkRelatedPhysicalActivity'+'_'+df['deg_urb']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['deg_urb']
    df.drop(columns=['physact','deg_urb','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def hlth_ehis_pe2e(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe2e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,duration,isced11,sex,age,geo', '2019', '2014']
    df.columns=cols
    col1 = "unit,duration,isced11,sex,age,geo"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_duration(df)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    df['SV'] = 'Count_Person_'+df['duration']+'_'+df['isced11']+'_'+df['sex']+\
        '_'+'HealthEnhancingPhysicalActivity'+'_AsAFractionOf_Count_Person_'+\
        df['isced11']+'_'+df['sex']
    df.drop(columns=['unit','age','duration','isced11','sex'],inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df

def hlth_ehis_pe2i(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe2i for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,quant_inc,duration,sex,age,geo', '2019', '2014']
    df.columns=cols
    col1 = "unit,quant_inc,duration,sex,age,geo"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_duration(df)
    df = _replace_sex(df)
    df = _replace_quant_inc(df)
    df['SV'] = 'Count_Person_'+df['duration']+'_'+df['sex']+\
        '_'+'HealthEnhancingPhysicalActivity'+'_'+df['quant_inc']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['quant_inc']
    df.drop(columns=['unit','age','duration','quant_inc','sex'],inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df

def hlth_ehis_pe2u(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe2u for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['duration,deg_urb,sex,age,unit,time','EU27_2020','EU28','BG',
    'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=cols
    col1 = "duration,deg_urb,sex,age,unit,time"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_duration(df)
    df.drop(columns=['unit','age'],inplace=True)
    df['SV'] = 'Count_Person_'+df['duration']+'_'+df['sex']+'_'+\
        'HealthEnhancingPhysicalActivity'+'_'+df['deg_urb']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['deg_urb']
    df.drop(columns=['duration','deg_urb','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def hlth_ehis_pe9b(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9b for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,physact,c_birth,sex,age,time','EU27_2020','EU28','BG',
    'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=cols
    col1 = "unit,physact,c_birth,sex,age,time"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_c_birth(df)
    df.drop(columns=['unit','age'],inplace=True)
    df['SV'] = 'Count_Person_'+df['physact']+'_'+df['sex']\
        +'_'+'HealthEnhancingPhysicalActivity'+'_'+df['c_birth']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['c_birth']
    df.drop(columns=['physact','c_birth','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def hlth_ehis_pe9c(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9c for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,physact,sex,age,citizen,time','EU27_2020','EU28','BG',
    'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=cols
    col1 = "unit,physact,sex,age,citizen,time"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_physact(df)
    df = _replace_sex(df)
    df = _replace_citizen(df)
    df.drop(columns=['unit','age'],inplace=True)
    df['SV'] = 'Count_Person_'+df['citizen']+'_'+df['physact']+'_'+\
        df['sex']+'_'+'HealthEnhancingPhysicalActivity'+\
        '_AsAFractionOf_Count_Person_'+df['citizen']+'_'+df['sex']
    df.drop(columns=['physact','citizen','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def _replace_sex(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {
        'F': 'Female',
        'M': 'Male',
        'T': 'Total'
        }
    df = df.replace({'sex': _dict})
    return df

def _replace_physact(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {
        'MV_AERO': 'Aerobic',
        'MV_MSC': 'MuscleStrengthening',
        'MV_AERO_MSC': 'AerobicAndMuscleStrengthening',
        'MV_WALK_GET': 'Walking',
	    'MV_CYCL_GET':'Cycling',
	    'MV_AERO_SPRT':'AerobicSports'
        }
    df = df.replace({'physact': _dict})
    return df

def _replace_isced11(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """

    _dict = {
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
    df = df.replace({'isced11': _dict})
    return df

def _replace_quant_inc(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """

    _dict = {
        'TOTAL':'Total',
	    'QU1':'FirstQuintile',
	    'QU2':'SecondQuintile',
        'QU3':'ThirdQuintile',
	    'QU4':'FourthQuintile',
        'QU5':'FifthQuintile'
        }
    df = df.replace({'quant_inc': _dict})
    return df

def _replace_deg_urb(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {
        'TOTAL':'Total',
        'DEG1':'Cities',
        'DEG2':'TownsAndSuburbs',
        'DEG3':'RuralAreas',
        }
    df = df.replace({'deg_urb': _dict})
    return df

def _replace_levels(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {
        'HVY':'HeavyActivity',
        'MOD':'ModerateActivity',
        'MOD_HVY':'ModerateActivityOrHeavyActivity',
        'NONE_LGHT':'NoneActivityOrLightActivity'
        }
    df = df.replace({'levels': _dict})
    return df

def _replace_duration(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {
        'MN0':'0Minutes',
        'MN1-149':'1To149Minutes',
        'MN150-299':'150To299Minutes',
        'MN_GE150':'150OrMoreMinutes',
        'MN_GE300':'300OrMoreMinutes'
        }
    df = df.replace({'duration': _dict})
    return df

def _replace_c_birth(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {
        'EU28_FOR':	'CountryOfBirthEU28CountriesExceptReportingCountry',
	    'NEU28_FOR': 'CountryOfBirthNonEU28CountriesNorReportingCountry',
	    'FOR': 'CountryOfBirthForeignCountry',
	    'NAT': 'CountryOfBirthReportingCountry'
        }
    df = df.replace({'c_birth': _dict})
    return df

def _replace_citizen(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {
        'EU28_FOR':	'CitizenshipEU28CountriesExceptReportingCountry',
	    'NEU28_FOR': 'CitizenshipNonEU28CountriesNorReportingCountry',
	    'FOR': 'CitizenshipForeignCountry',
	    'NAT': 'CitizenshipReportingCountry'
        }
    df = df.replace({'citizen': _dict})
    return df

def _replace_lev_limit(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {
        'MOD':	'Moderate',
	    'SEV': 'Severe',
	    'SM_SEV': 'SomeOrSevere',
	    'NONE': 'None'
        }
    df = df.replace({'lev_limit': _dict})
    return df

def _replace_bmi(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {
        'BMI_LT18P5':'Underweight',
	    'BMI18P5-24':'Normal',
	    'BMI_GE25':'Overweight',
	    'BMI25-29':'PreObese',
        'BMI_GE30':'Obese'
        }
    df = df.replace({'bmi': _dict})
    return df

def _split_column(df: pd.DataFrame,col: str) -> pd.DataFrame:
    """
    Divides a single column into multiple columns and returns the DF
    """
    info = col.split(",")
    df[info] = df[col].str.split(',', expand=True)
    df.drop(columns=[col],inplace=True)
    return df

class EuroStatPhysicalActivity:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files
    """
    def __init__(self, input_files: list, csv_file_path: str,
                 mcf_file_path: str, tmcf_file_path: str) -> None:
        self.input_files = input_files
        self.cleaned_csv_file_path = csv_file_path
        self.mcf_file_path = mcf_file_path
        self.tmcf_file_path = tmcf_file_path
        self.df = None
        self.file_name = None
        self.scaling_factor = 1

    def __generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template
        Arguments:
            None
        Returns:
            None
        """
        tmcf_template = """Node: E:EuroStat_Population_PhysicalActivity->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:EuroStat_Population_PhysicalActivity->SV
measurementMethod: C:EuroStat_Population_PhysicalActivity->Measurement_Method
observationAbout: C:EuroStat_Population_PhysicalActivity->geo
observationDate: C:EuroStat_Population_PhysicalActivity->time
value: C:EuroStat_Population_PhysicalActivity->observation 
"""
        # Writing Genereated TMCF to local path.
        with open(self.tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf_template.rstrip('\n'))

    def __generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template
        Arguments:
            df_cols (list) : List of DataFrame Columns
        Returns:
            None
        """
        mcf_template = """Node: dcid:{}
typeOf: dcs:StatisticalVariable
populationType: dcs:Person{}{}{}{}{}{}{}{}{}{}{}{}{}
statType: dcs:measuredValue
measuredProperty: dcs:count
"""
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            incomequin = ''
            gender = ''
            education = ''
            healthBehavior = ''
            exercise = ''
            residence = ''
            activity = ''
            duration = ''
            countryofbirth = ''
            citizenship = ''
            lev_limit= ''
            bmi = ''
            sv_temp = sv.split("_AsAFractionOf_")
            denominator = "\nmeasurementDenominator: "+sv_temp[1]
            sv_prop = sv_temp[0].split("_")
            for prop in sv_prop:
                if prop in ["Count", "Person"]:
                    continue
                if "PhysicalActivity" in prop:
                    healthBehavior = "\nhealthBehavior: " + prop
                elif "Male" in prop or "Female" in prop:
                    gender = "\ngender: dcs:" + prop
                elif "Aerobic" in prop or "MuscleStrengthening" in prop \
                    or "Walking" in prop or "Cycling" in prop:
                    exercise = "\nexerciseType: " + prop
                elif "Education" in prop:
                    education = "\neducationalAttainment: " + \
                        prop.replace("EducationalAttainment","")\
                        .replace("Or","__")
                elif "Quintile" in prop:
                    incomequin = "\nincome: ["+prop.replace("Quintile",\
                        " Quintile").replace("First","1").replace("Second","2")\
                        .replace("Third","3").replace("Fourth","4")\
                        .replace("Fifth","5")+"]"
                elif "Cities" in prop or "TownsAndSuburbs" in prop \
                    or "RuralAreas" in prop:
                    residence = "\nplaceofResidenceClassification: " + prop
                elif "Activity" in prop:
                    activity = "\nphysicalActivityEffortLevel: " + prop
                elif "Minutes" in prop:
                    if "OrMoreMinutes" in prop:
                        duration = "\nduration: [" + prop.replace\
                            ("OrMoreMinutes","") + " - Minutes]"
                    elif "To" in prop:
                        duration = "\nduration: [" + prop.replace("Minutes",\
                             "").replace("To", " ") + " Minutes]"
                    else:
                        duration = "\nduration: [Minutes " + prop.replace\
                            ("Minutes","") + "]"
                elif "CountryOfBirth" in prop:
                    countryofbirth = "\nnativity: " + prop
                elif "Citizenship" in prop:
                    citizenship = "\ncitizenship: " + prop
                elif "Moderate" in prop or "Severe" in prop \
                    or "None" in prop:
                    lev_limit = "\nglobalActivityLimitationIndicator: "+prop
                elif "weight" in prop or "Normal" in prop \
                    or "Obese" in prop:
                    lev_limit = "\nbmi: " + prop
            final_mcf_template += mcf_template.format(sv,denominator,incomequin,
                education,healthBehavior,exercise,residence,activity,duration,
                gender,countryofbirth,citizenship,lev_limit,bmi) + "\n"

        # Writing Genereated MCF to local path.
        with open(self.mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))

    def process(self):
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file
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
            df = pd.read_csv(file_path, sep='\t',skiprows=1)
            if 'hlth_ehis_sk1e' in file_path:
                df = hlth_ehis_sk1e(df)
            elif 'hlth_ehis_sk1i' in file_path:
                df = hlth_ehis_sk1i(df)
            elif 'hlth_ehis_sk1u' in file_path:
                df = hlth_ehis_sk1u(df)
            elif 'hlth_ehis_sk3e' in file_path:
                df = hlth_ehis_sk3e(df)
            elif 'hlth_ehis_sk3i' in file_path:
                df = hlth_ehis_sk3i(df)
            elif 'hlth_ehis_sk3u' in file_path:
                df = hlth_ehis_sk3u(df)
            elif 'hlth_ehis_sk4e' in file_path:
                df = hlth_ehis_sk4e(df)
            elif 'hlth_ehis_sk4u' in file_path:
                df = hlth_ehis_sk4u(df)
            elif 'hlth_ehis_sk1b' in file_path:
                df = hlth_ehis_sk1b(df)
            elif 'hlth_ehis_sk1c' in file_path:
                df = hlth_ehis_sk1c(df)
            elif 'hlth_ehis_sk2i' in file_path:
                df = hlth_ehis_sk2i(df)
            elif 'hlth_ehis_sk2e' in file_path:
                df = hlth_ehis_sk2e(df)
            elif 'hlth_ehis_sk5e' in file_path:
                df = hlth_ehis_sk5e(df)
            elif 'hlth_ehis_sk6e' in file_path:
                df = hlth_ehis_sk6e(df)
            df['SV'] = df['SV'].str.replace('_Total','')
            df['Measurement_Method'] = np.where(df['observation']\
                .str.contains('u'),'LowReliability/EurostatRegionalStatistics',\
                'EurostatRegionalStatistics')
            df['observation'] = df['observation'].str.replace(':','')\
                .str.replace(' ','').str.replace('u','')
            df['observation']= pd.to_numeric(df['observation'], errors='coerce')
            final_df = pd.concat([final_df, df])
            sv_list += df["SV"].to_list()
        final_df = final_df.sort_values(by=['time', 'geo','SV'])
        final_df = final_df.replace({'geo': COUNTRY_MAP})
        final_df.to_csv(self.cleaned_csv_file_path, index=False)
        sv_list = list(set(sv_list))
        sv_list.sort()
        self.__generate_mcf(sv_list)
        self.__generate_tmcf()

def main(_):
    input_path = FLAGS.input_path
    if not os.path.exists(input_path):
        os.mkdir(input_path)
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]
    data_file_path = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "output"
    # Defining Output Files
    cleaned_csv_path = data_file_path + os.sep + \
        "EuroStat_Population_PhysicalActivity.csv"
    mcf_path = data_file_path + os.sep + \
        "EuroStat_Population_PhysicalActivity.mcf"
    tmcf_path = data_file_path + os.sep + \
        "EuroStat_Population_PhysicalActivity.tmcf"
    loader = EuroStatPhysicalActivity(ip_files, cleaned_csv_path, mcf_path,\
        tmcf_path)
    loader.process()

if __name__ == "__main__":
    app.run(main)
