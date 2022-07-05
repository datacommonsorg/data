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
                                          _replace_isced97, _replace_n_portion,
                                          _replace_deg_urb, _replace_quant_inc,
                                          _replace_bmi, _replace_c_birth,
                                          _replace_citizen, _replace_coicop,
                                          _replace_frequenc, _replace_lev_limit,
                                          _split_column)                                    
# # For import util.alpha2_to_dcid
_COMMON_PATH = os.path.abspath(
   os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(1, _COMMON_PATH)
from util.alpha2_to_dcid import COUNTRY_MAP
# pylint: enable=import-error
# pylint: enable=wrong-import-position
FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")
 
_MCF_TEMPLATE = ("Node: dcid:{pv1}\n"
                "{pv2}\n"
                "typeOf: dcs:StatisticalVariable\n"
                "populationType: dcs:Person{pv3}{pv4}{pv5}"
                "{pv6}{pv7}{pv8}{pv9}{pv10}{pv11}{pv12}{pv13}\n"
                "statType: dcs:measuredValue\n"
                "measuredProperty: dcs:count\n")
 
_TMCF_TEMPLATE = (
   "Node: E:eurostat_population_consumptionoffruitsandvegetables->E0\n"
   "typeOf: dcs:StatVarObservation\n"
   "variableMeasured: C:eurostat_population_consumptionoffruitsandvegetables->"
   "SV\n"
   "measurementMethod: C:eurostat_population_consumptionoffruitsandvegetables->"
   "Measurement_Method\n"
   "observationAbout: C:eurostat_population_consumptionoffruitsandvegetables->"
   "geo\n"
   "observationDate: C:eurostat_population_consumptionoffruitsandvegetables->"
   "time\n"
   "scalingFactor: 100\n"
   "value: C:eurostat_population_consumptionoffruitsandvegetables->"
   "observation\n")
 
 
def _consumption_fruit_vegetables_edu(df: pd.DataFrame) -> pd.DataFrame:
  """
  Cleans the file hlth_ehis_fv3e for concatenation in Final CSV.
  Arguments: df (pd.DataFrame), the raw df as the input
  Returns: df (pd.DataFrame), provides the cleaned df as output
  """
  cols = ['unit,n_portion,isced11,sex,age,geo', '2019', '2014']
  df.columns = cols
  df = _split_column(df, cols[0])
  # Filtering out the wanted rows and columns.
  df = df[df['age'] == 'TOTAL']
  df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
  df = _replace_n_portion(df)
  df = _replace_sex(df)
  df = _replace_isced11(df)
  df['SV'] = 'Percent_' + 'Daily_'+df['n_portion']+'_'+'ConsumptionOfFruitsOr'+\
             'ConsumptionOfVegetables_'+'In_Count_Person_' + df['isced11']+\
             '_' + df['sex']
  df.drop(columns=['unit','age','isced11','n_portion','sex'], inplace=True)
  df = df.melt(id_vars=['SV','geo'], var_name='time'\
          ,value_name='observation')
  return df
def _consumption_fruit_vegetables_inc(df: pd.DataFrame) -> pd.DataFrame:
  """
  Cleans the file hlth_ehis_fv3i for concatenation in Final CSV.
  Arguments: df (pd.DataFrame), the raw df as the input
  Returns: df (pd.DataFrame), provides the cleaned df as output
  """
  cols = ['unit,n_portion,quant_inc,sex,age,geo', '2019', '2014']
  df.columns = cols
  df = _split_column(df, cols[0])
  # Filtering out the wanted rows and columns.
  df = df[df['age'] == 'TOTAL']
  df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
  df = _replace_n_portion(df)
  df = _replace_sex(df)
  df = _replace_quant_inc(df)
  df['SV']= 'Percent_'+'Daily_'+df['n_portion']+'_'+'ConsumptionOfFruitsOr'+\
            'ConsumptionOfVegetables_'+'In_Count_Person_' + df['sex']+\
            '_'+ df['quant_inc'] 
  df.drop(columns=['unit','age','quant_inc','n_portion','sex'], inplace=True)
  df = df.melt(id_vars=['SV','geo'], var_name='time' ,value_name='observation')
  return df
def _consumption_fruit_vegetables_urb(df: pd.DataFrame) -> pd.DataFrame:
  """
  Cleans the file hlth_ehis_fv3u for concatenation in Final CSV.
  Arguments: df (pd.DataFrame), the raw df as the input
  Returns: df (pd.DataFrame), provides the cleaned df as output
  """
  cols = [
      'n_portion,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28','BE', 'BG',
      'CZ','DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
      'LT','LU', 'HU', 'MT','NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
      'SE', 'IS','NO', 'UK', 'TR'
  ]
  df.columns = cols
  df = _split_column(df, cols[0])
  # Filtering out the wanted rows and columns.
  df = df[df['age'] == 'TOTAL']
  df = _replace_n_portion(df)
  df = _replace_sex(df)
  df = _replace_deg_urb(df)
  df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
  df['SV'] = 'Percent_'  +\
  'Daily_'+df['n_portion']+'_'+'ConsumptionOfFruitsOrConsumptionOfVegetables_'+\
  'In_Count_Person_'+df['deg_urb']+'_'+df['sex']
  df.drop(columns=['unit','age','deg_urb','n_portion','sex'], inplace=True)
  df = df.melt(id_vars=['SV','time'], var_name='geo'\
      ,value_name='observation')
  return df
def _frequency_fruit_vegetables_edu(df: pd.DataFrame) -> pd.DataFrame:
  """
  Cleans the file hlth_ehis_fv1e for concatenation in Final CSV.
  Arguments: df (pd.DataFrame), the raw df as the input
  Returns: df (pd.DataFrame), provides the cleaned df as output
  """
  cols = ['unit,frequenc,coicop,isced11,sex,age,geo', '2019', '2014']
  df.columns = cols
  df = _split_column(df, cols[0])
  # Filtering out the wanted rows and columns.
  df = df[df['age'] == 'TOTAL']
  df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
  df = _replace_coicop(df)
  df = _replace_sex(df)
  df = _replace_isced11(df)
  df = _replace_frequenc(df)
  df['SV'] = 'Percent_'  + df['frequenc'] + '_' +df['coicop'] + '_'+\
    'In_Count_Person_' +df['isced11'] +'_' + df['sex']
  df.drop(columns=['unit','age','isced11','coicop','frequenc','sex'],\
       inplace=True)
  df = df.melt(id_vars=['SV','geo'], var_name='time'\
          ,value_name='observation')
  return df
def _frequency_fruit_vegetables_urb(df: pd.DataFrame) -> pd.DataFrame:
  """
  Cleans the file hlth_ehis_fv1u for concatenation in Final CSV.
  Arguments: df (pd.DataFrame), the raw df as the input
  Returns: df (pd.DataFrame), provides the cleaned df as output
  """
  cols = [
      'frequenc,coicop,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28','BE',
      'BG', 'CZ','DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY',
      'LV','LT','LU', 'HU', 'MT','NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK',
      'FI', 'SE', 'IS','NO', 'UK', 'TR'
  ]
  df.columns = cols
  df = _split_column(df, cols[0])
  # Filtering out the wanted rows and columns.
  df = df[df['age'] == 'TOTAL']
  df = _replace_coicop(df)
  df = _replace_frequenc(df)
  df = _replace_sex(df)
  df = _replace_deg_urb(df)
  df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
  df['SV'] = 'Percent_' + df['frequenc'] +\
  '_'+df['coicop'] +'_In_Count_Person_'+df['deg_urb']+'_'+df['sex']
  df.drop(columns=['unit','age','deg_urb','coicop','frequenc','sex'],\
       inplace=True)
  df = df.melt(id_vars=['SV','time'], var_name='geo'\
      ,value_name='observation')
  return df
def _consumption_fruit_vegetables_cob(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_fv3b for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['unit,n_portion,sex,age,c_birth,time','EU27_2020','EU28','BE','BG',
 'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
 'MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
 df.columns=cols
 df = _split_column(df,cols[0])
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_c_birth(df)
 df = _replace_sex(df)
 df = _replace_n_portion(df)
 df.drop(columns=['EU27_2020','EU28'],inplace=True)
 df['SV'] = 'Percent_'+ 'Daily_'+df['n_portion']+'_'+'ConsumptionOfFruitsOr'+\
     'ConsumptionOfVegetables_'+'In_Count_Person_' +df['sex']+'_'+df['c_birth']
 df.drop(columns=['unit','age','n_portion','c_birth','sex'],inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
def _consumption_fruit_vegetables_coc(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_fv3c for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['unit,n_portion,sex,age,citizen,time', 'EU27_2020','EU28','BE','BG',
 'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
 'MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
 df.columns=cols
 df = _split_column(df,cols[0])
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_citizen(df)
 df = _replace_sex(df)
 df = _replace_n_portion(df)
 df.drop(columns=['EU27_2020','EU28'],inplace=True)
 df['SV'] = 'Percent_'+ 'Daily_'+df['n_portion']+'_'+\
     'ConsumptionOfFruitsOrConsumptionOfVegetables_'+\
      'In_Count_Person_'+df['citizen']+'_'+df['sex']
 df.drop(columns=['unit','age','n_portion','citizen','sex'],inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
def _consumption_fruit_vegetables_lev(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_fv3d for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['n_portion,lev_limit,sex,age,unit,time', 'EU27_2020','EU28','BE',
 'BG','CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU',
 'HU','MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
 df.columns=cols
 df = _split_column(df,cols[0])
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_lev_limit(df)
 df = _replace_sex(df)
 df = _replace_n_portion(df)
 df.drop(columns=['EU27_2020','EU28'],inplace=True)
 df['SV'] = 'Percent_'+'Daily_'+df['n_portion']+'_'+\
     'ConsumptionOfFruitsOrConsumptionOfVegetables_In_Count_Person_'+\
          df['sex']+'_'+df['lev_limit']
 df.drop(columns=['unit','age','n_portion','lev_limit','sex'],inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
def _consumption_fruit_vegetables_bmi(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_fv3m for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['unit,n_portion,sex,age,bmi,time', 'EU27_2020','BE','BG','CZ','DK',
 'DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU','MT','NL',
 'AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','RS','TR']
 df.columns=cols
 df = _split_column(df,cols[0])
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_bmi(df)
 df = _replace_sex(df)
 df = _replace_n_portion(df)
 df.drop(columns=['EU27_2020'],inplace=True)
 df['SV'] = 'Percent_'+ 'Daily_'+ df['n_portion']+'_'+\
     'ConsumptionOfFruitsOrConsumptionOfVegetables_'+\
      'In_Count_Person_'+df['sex']+'_'+df['bmi']
 df.drop(columns=['unit','age','n_portion','bmi','sex'],inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
def _frequency_fruit_vegetables_cob(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_fv1b for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['unit,frequenc,coicop,c_birth,sex,age,time', 'EU27_2020','EU28','BE',
 'BG','CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU',
 'HU','MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
 df.columns=cols
 df = _split_column(df,cols[0])
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_coicop(df)
 df = _replace_sex(df)
 df = _replace_c_birth(df)
 df = _replace_frequenc(df)
 df.drop(columns=['EU27_2020','EU28'],inplace=True)
 df['SV'] = 'Percent_'+ df['frequenc']+'_'+df['coicop'] +'_'+\
      'In_Count_Person_'+df['sex']+'_'+df['c_birth']
 df.drop(columns=['unit','age','c_birth','coicop','sex'],inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
def _frequency_fruit_vegetables_coc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_fv1c for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,frequenc,coicop,sex,age,citizen,time','EU27_2020','EU28','BE',
    'BG','CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU',
    'HU','MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=cols
    df = _split_column(df,cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = _replace_frequenc(df)
    df = _replace_coicop(df)
    df = _replace_sex(df)
    df = _replace_citizen(df)
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df['SV'] = 'Percent_'+df['frequenc']+ '_'+df['coicop']+\
        '_'+'In_Count_Person_'+ df['citizen']+'_'+df['sex']
    df.drop(columns=['unit','age','citizen','coicop','frequenc','sex'],\
        inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df
def _frequency_fruit_vegetables_inc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_fv1i for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,frequenc,coicop,sex,age,quant_inc,time','EU27_2020','BE','BG',
    'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
    'MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','RS','TR']
    df.columns=cols
    df = _split_column(df,cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = _replace_frequenc(df)
    df = _replace_coicop(df)
    df = _replace_sex(df)
    df = _replace_quant_inc(df)
    df.drop(columns=['EU27_2020'],inplace=True)
    df['SV'] = 'Percent_'+df['frequenc'] +'_'+ df['coicop'] +\
     '_'+'In_Count_Person_'+df['sex']+'_'+df['quant_inc']
    df.drop(columns=['unit','age','quant_inc','coicop','frequenc','sex'],\
        inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df
def _frequency_fruit_vegetables_bmi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_fv1m for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,frequenc,coicop,sex,age,bmi,time','EU27_2020','BE','BG','CZ',
    'DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU','MT',
    'NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','RS','TR']
    df.columns=cols
    df = _split_column(df,cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = _replace_frequenc(df)
    df = _replace_coicop(df)
    df = _replace_sex(df)
    df = _replace_bmi(df)
    df.drop(columns=['EU27_2020'],inplace=True)
    df['SV'] = 'Percent_'+df['frequenc']+'_'+ df['coicop']+\
        '_'+'In_Count_Person_'+ df['sex']+'_'+df['bmi']
    df.drop(columns=['unit','age','bmi','coicop','frequenc','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df
def _frequency_fruit_vegetables_lev(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_fv1d for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['frequenc,coicop,lev_limit,sex,age,unit,time','EU27_2020','EU28',
     'BE','BG','CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV',
     'LT','LU','HU','MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS',
     'NO','UK','TR']
    df.columns=cols
    df = _split_column(df,cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = _replace_frequenc(df)
    df = _replace_coicop(df)
    df = _replace_sex(df)
    df = _replace_lev_limit(df)
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df['SV'] = 'Percent_'+df['frequenc']+'_'+df['coicop']+'_'+\
        'In_Count_Person_'+df['sex']+'_'+df['lev_limit']
    df.drop(columns=['unit','age','lev_limit','coicop','frequenc','sex'],\
        inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df
def _drinking_sugar_sweetened_edu(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_fv7e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,frequenc,sex,age,isced11,time','EU27_2020','BE','BG','CZ',
    'DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU','MT',
    'AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','RS','TR']
    df.columns=cols
    df = _split_column(df,cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    df.drop(columns=['EU27_2020'],inplace=True)
    df['SV'] = 'Percent_'+df['frequenc'] +\
        '_'+'ConsumptionOfSugarSweetenedSoftDrinks_'+\
        'In_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['unit','age','isced11','frequenc','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df
def _drinking_sugar_sweetened_bmi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_fv7m for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,frequenc,sex,age,bmi,time', 'EU27_2020','BE','BG','CZ','DK',
    'DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU','MT','AT',
    'PL','PT','RO','SI','SK','FI','SE','IS','NO','RS','TR']
    df.columns=cols
    df = _split_column(df,cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_bmi(df)
    df.drop(columns=['EU27_2020'],inplace=True)
    df['SV'] = 'Percent_'+df['frequenc'] +'_'+\
        'ConsumptionOfSugarSweetenedSoftDrinks_'+\
        'In_Count_Person_'+df['sex']+'_'+df['bmi']
    df.drop(columns=['unit','age','bmi','frequenc','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df
def _drinking_sugar_sweeetened_inc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_fv7i for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,frequenc,sex,age,quant_inc,time','EU27_2020','BE','BG','CZ',
    'DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU','MT',
    'AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','RS','TR']
    df.columns=cols
    df = _split_column(df,cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_quant_inc(df)
    df.drop(columns=['EU27_2020'],inplace=True)
    df['SV'] = 'Percent_'+ df['frequenc']+'_' +\
    'ConsumptionOfSugarSweetenedSoftDrinks_'+\
    'In_Count_Person_'+ df['sex']+'_'+ df['quant_inc']
    df.drop(columns=['unit','age','quant_inc','frequenc','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df
def _frequency_drinking_pure_juice_edu(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_fv5e for concatenation in Final CSV.
    Arguments: df (pd.DataFrame), the raw df as the input
    Returns: df (pd.DataFrame), provides the cleaned df as output
    """
    cols = ['unit,sex,age,frequenc,isced11,time','EU27_2020','BE','BG','CZ',
    'DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU','MT',
    'AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','RS','TR']
    df.columns = cols
    df = _split_column(df, cols[0])
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df = df[(df['time'] != 'EU27_2020')]
    df = _replace_sex(df)
    df = _replace_isced11(df)
    df = _replace_frequenc(df)
    df['SV'] = 'Percent_'+ df['frequenc'] + '_' +'ConsumptionOfPure'+\
    'FruitOrVegetableJuice_'+'In_Count_Person_' +df['isced11'] +'_' + df['sex']
    df.drop(columns=['unit','age','isced11','frequenc','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo',value_name='observation')
    return df

def _consumption_fruits_edu(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_de7 for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['sex,age,frequenc,isced97,time','BE','BG','CZ','EE','EL','ES','FR',
    'CY','LV','HU','MT','PL','RO','SI','SK','TR']
    df.columns=cols
    df = _split_column(df,cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_isced97(df)
    df['SV'] = 'Percent_'+ df['frequenc']+ '_'+\
    'ConsumptionOfFruits_'+\
    'In_Count_Person_'+ df['isced97']+'_'+ df['sex']
    df.drop(columns=['age','isced97','frequenc','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df
def _consumption_vegetables_edu(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_de8 for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['sex,age,frequenc,isced97,time','BE','BG','CZ','EE','EL','ES','FR',
    'CY','LV','HU','MT','PL','RO','SI','SK','TR']
    df.columns=cols
    df = _split_column(df,cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_isced97(df)
    print(df)
    df['SV'] = 'Percent_'+ df['frequenc']+'_' +\
    'ConsumptionOfVegetables_'+\
    'In_Count_Person_'+ df['isced97']+'_'+ df['sex']
    df.drop(columns=['age','isced97','frequenc','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df

class EuroStatConsumptionOfFruitsandVegetables:
   """
 This Class has requried methods to generate Cleaned CSV,
 MCF and TMCF Files
 """
 
   def __init__(self, input_files: list, csv_file_path: str,
                mcf_file_path: str, tmcf_file_path: str) -> None:
       self._input_files = input_files
       self._cleaned_csv_file_path = csv_file_path
       self._mcf_file_path = mcf_file_path
       self._tmcf_file_path = tmcf_file_path
 
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
       final_mcf_template = ""
       for sv in sv_list:
           if "Total" in sv:
               continue
           gender = education  = portion = frequency = residence = ''
           countryofbirth = citizenship = lev_limit = sv_name = incomequin =''
           coicop = ''
 
           sv_temp = sv.split("_In_")
           denominator = "\nmeasurementDenominator: dcs:" + sv_temp[1]
           sv_property = sv.split("_")
           for prop in sv_property:
               if prop == "Percent":
                   sv_name = sv_name + "Percentage "
               elif "Portions" in prop:
 #                   sv_name = sv_name + prop + ", "
                    if "PortionsOrMore" in prop:
                        portion = "\nconsumptionQuantity: [" + prop.replace\
                            ("PortionsOrMore","") + " - Portions]"
                    elif "To" in prop:
                        portion = "\nconsumptionQuantity: [" + prop.replace\
                            ("Portions", "").replace("To", " ").replace\
                                ("From","") + " Portions]"
                    else:
                        portion = "\nconsumptionQuantity: [Portions " +\
                            prop.replace("Portions","") + "]"    
                    sv_name = sv_name + prop + ", "
               elif prop == "In":
                   sv_name = sv_name + "Among "
               elif prop == "Count":
                   continue
               elif prop == "Person":
                   continue
               if "Male" in prop or "Female" in prop:
                   gender = "\ngender: dcs:" + prop
                   sv_name = sv_name + prop + ", "
               elif "ConsumptionOfPureFruitOrVegetableJuice" in prop:
                   coicop="\nhealthBehavior: dcs:" + prop
                   sv_name = sv_name + prop + ", "
               elif "ConsumptionOfFruits" in prop or "ConsumptionOfVegetables" in prop or \
                   "SugarSweetenedSoftDrinks" in prop :
                   coicop = "\nhealthBehavior: dcs:" + prop.replace("Or","__") 
                   sv_name = sv_name + prop + ", "
               elif "UnderWeight" in prop or "Normal" in prop or "OverWeight"\
                    in prop or "PreObese" in prop or "Obesity" in prop:
                   sv_name = sv_name + prop + ", "
                   coicop =  coicop+"__"+prop
               elif "Education" in prop:
                   education = "\neducationalAttainment: dcs:" + \
                       prop.replace("EducationalAttainment","")\
                       .replace("Or","__")
                   sv_name = sv_name + prop + ", "
               elif "Urban" in prop or "Rural" in prop or "SemiUrban" in prop:
                   residence = "\nplaceOfResidenceClassification: dcs:" + prop
                   sv_name = sv_name + prop + ", "
               elif "Limitation" in prop:
                   lev_limit = "\nglobalActivityLimitationindicator: dcs:"\
                       + prop
                   sv_name = sv_name + prop + ", "
               elif "ForeignBorn" in prop or "Native" in prop:
                   countryofbirth = "\nnativity: dcs:" + \
                       prop.replace("CountryOfBirth","")
                   sv_name = sv_name + prop + ", "
               elif "Citizen" in prop:
                   citizenship = "\ncitizenship: dcs:" + \
                       prop.replace("Citizenship","")
                   sv_name = sv_name + prop + ", "
               elif "Percentile" in prop:
                   incomequin = "\nincome: ["+prop.replace("IncomeOf","")\
                       .replace("To"," ").replace("Percentile"," Percentile")\
                       +"]"
                   sv_name = sv_name + prop.replace("Of","Of ")\
                       .replace("To"," To ") + ", "
               elif "OnceADay" in prop or "AtLeastOnceADay" in prop or\
                    "AtleastTwiceADay" in prop or "LessThanOnceAWeek" \
                   in prop or "From1To3TimesAWeek" in prop or \
                    "From4To6TimesAWeek" in prop or "Never" \
                    in prop or "NeverOrOccasionally" in prop or "Daily" in prop:
                   frequency = "\nactivityFrequency: dcs:" + prop\
                        .replace("Or","__")
                   sv_name = sv_name + prop + ", "
           # Making the changes to the SV Name,
           # Removing any extra commas, with keyword and
           # adding Population in the end
           sv_name = sv_name.replace(", Among", " Among")
           sv_name = sv_name.rstrip(', ')
           sv_name = sv_name.rstrip('with')
           # Adding spaces before every capital letter,
           # to make SV look more like a name.
           sv_name = re.sub(r"(\w)([A-Z])", r"\1 \2", sv_name)
           sv_name = "name: \"" + sv_name + " Population\""
           sv_name = sv_name.replace('AWeek', 'A Week')
           sv_name = sv_name.replace('From1','From 1')
           sv_name = sv_name.replace('To4','To 4')
           sv_name = sv_name.replace('To3','To 3')
           sv_name = sv_name.replace('ADay','A Day')
           sv_name = sv_name.replace('From4','From 4')
           sv_name = sv_name.replace('To6','To 6')
           sv_name = sv_name.replace('ACitizen','A Citizen')
           sv_name = sv_name.replace('Weig ','Weight ')
 
           final_mcf_template += _MCF_TEMPLATE.format(pv1=sv,
                                                      pv2=sv_name,
                                                      pv3=denominator,
                                                      pv4=education,
                                                      pv5=residence,
                                                      pv6=portion,
                                                      pv7=gender,
                                                      pv8=countryofbirth,
                                                      pv9=citizenship,
                                                      pv10=lev_limit,
                                                      pv11=coicop,
                                                      pv12=frequency,
                                                      pv13=incomequin) + "\n"
 
       # Writing Genereated MCF to local path.
       with open(self._mcf_file_path, 'w+', encoding='utf-8') as f_out:
           f_out.write(final_mcf_template.rstrip('\n'))
       # pylint: enable=R0914
       # pylint: enable=R0912
       # pylint: enable=R0915
 
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
 
   def process(self):
       """
     This Method calls the required methods to generate
     cleaned CSV, MCF, and TMCF file
     """
       final_df = pd.DataFrame(columns=['time','geo','SV','observation',\
           'Measurement_Method'])
       # Creating Output Directory
       output_path = os.path.dirname(self._cleaned_csv_file_path)
       if not os.path.exists(output_path):
           os.mkdir(output_path)
       sv_list = []
       for file_path in self._input_files:
           print(file_path)
           df = pd.read_csv(file_path, sep='\t',header=0)
           file_name = file_path.split("/")[-1][:-4]
           function_dict = {
               "hlth_ehis_fv3e": _consumption_fruit_vegetables_edu,
               "hlth_ehis_fv3i": _consumption_fruit_vegetables_inc,
               "hlth_ehis_fv3u": _consumption_fruit_vegetables_urb,
               "hlth_ehis_fv1e": _frequency_fruit_vegetables_edu,
               "hlth_ehis_fv1u": _frequency_fruit_vegetables_urb,
               "hlth_ehis_fv3b": _consumption_fruit_vegetables_cob,
               "hlth_ehis_fv3c": _consumption_fruit_vegetables_coc,
               "hlth_ehis_fv3d": _consumption_fruit_vegetables_lev,
               "hlth_ehis_fv3m": _consumption_fruit_vegetables_bmi,
               "hlth_ehis_fv1b": _frequency_fruit_vegetables_cob,
               "hlth_ehis_fv1c": _frequency_fruit_vegetables_coc,
               "hlth_ehis_fv1i": _frequency_fruit_vegetables_inc,
               "hlth_ehis_fv1m": _frequency_fruit_vegetables_bmi,
               "hlth_ehis_fv1d": _frequency_fruit_vegetables_lev,
               "hlth_ehis_fv7e": _drinking_sugar_sweetened_edu,
               "hlth_ehis_fv7m": _drinking_sugar_sweetened_bmi,
               "hlth_ehis_fv7i": _drinking_sugar_sweeetened_inc,
               "hlth_ehis_de7": _consumption_fruits_edu,
               "hlth_ehis_de8": _consumption_vegetables_edu,
               "hlth_ehis_fv5e": _frequency_drinking_pure_juice_edu
           }
           df = function_dict[file_name](df)
           df['SV'] = df['SV'].str.replace('_Total', '')
           final_df = pd.concat([final_df, df])
           sv_list += df["SV"].to_list()
           sv_temp = df["SV"].to_list()
           print(set(sv_temp))
           print(file_name)
           print("**********************************************************")
 
       final_df = final_df.sort_values(by=['time', 'geo', 'SV', 'observation'])
       final_df = final_df.drop_duplicates(subset=['time','geo','SV'],\
           keep='first')
       final_df['observation'] = final_df['observation'].astype(str)\
           .str.strip()
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
       #   country/AUT
       #   Percent_AerobicSports_NonWorkRelatedPhysicalActivity_In_Count_Person
       #   77.3 u,
       # so measurement method for both 2014 and 2019 years shall be made
       # low reliability.
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
       final_df.to_csv(self._cleaned_csv_file_path, index=False)
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
   data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "output")
   # Defining Output Files
   csv_name = "eurostat_population_consumptionoffruitsandvegetables.csv"
   mcf_name = "eurostat_population_consumptionoffruitsndvegetables.mcf"
   tmcf_name = "eurostat_population_consumptionoffruitsandvegetables.tmcf"
   cleaned_csv_path = os.path.join(data_file_path, csv_name)
   mcf_path = os.path.join(data_file_path, mcf_name)
   tmcf_path = os.path.join(data_file_path, tmcf_name)
   loader = EuroStatConsumptionOfFruitsandVegetables(ip_files, cleaned_csv_path,
        mcf_path,tmcf_path)
   loader.process()
 
 
if __name__ == "__main__":
   app.run(main)

