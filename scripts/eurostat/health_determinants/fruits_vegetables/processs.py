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
 
 
def hlth_ehis_fv3e(df: pd.DataFrame) -> pd.DataFrame:
   """
   Cleans the file hlth_ehis_fv3e for concatenation in Final CSV.
   Arguments: df (pd.DataFrame), the raw df as the input
   Returns: df (pd.DataFrame), provides the cleaned df as output
   """
   cols = ['unit,n_portion,isced11,sex,age,geo', '2019', '2014']
   df.columns = cols
   col1 = "unit,n_portion,isced11,sex,age,geo"
   df = _split_column(df, col1)
   # Filtering out the wanted rows and columns.
   df = df[df['age'] == 'TOTAL']
   df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
   df = _replace_n_portion(df)
   df = _replace_sex(df)
   df = _replace_isced11(df)
   df['SV'] = 'Count_Person_' + 'HealthEnhancingConsumptionOfFruitsAnd'+\
       'Vegetables_' + df['isced11'] + '_' + df['n_portion'] + '_' +\
       df['sex'] + '_' + 'AsAFractionOf_Count_Person_' + df['isced11'] +\
       '_' + df['sex']
   df.drop(columns=['unit','age','isced11','n_portion','sex'], inplace=True)
   df = df.melt(id_vars=['SV','geo'], var_name='time'\
           ,value_name='observation')
   return df
 
def hlth_ehis_fv3i(df: pd.DataFrame) -> pd.DataFrame:
   """
   Cleans the file hlth_ehis_fv3i for concatenation in Final CSV.
   Arguments: df (pd.DataFrame), the raw df as the input
   Returns: df (pd.DataFrame), provides the cleaned df as output
   """
   cols = ['unit,n_portion,quant_inc,sex,age,geo', '2019', '2014']
   df.columns = cols
   col1 = "unit,n_portion,quant_inc,sex,age,geo"
   df = _split_column(df, col1)
   # Filtering out the wanted rows and columns.
   df = df[df['age'] == 'TOTAL']
   df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
   df = _replace_n_portion(df)
   df = _replace_sex(df)
   df = _replace_quant_inc(df)
   df['SV']='Count_Person_'+'HealthEnhancingConsumptionOfFruitsAnd'+\
       'Vegetables_'+df['n_portion'] + '_' + df['quant_inc'] + '_' +df['sex']+\
       '_' +'AsAFractionOf_Count_Person_' + df['quant_inc'] + '_' + df['sex']
   df.drop(columns=['unit','age','quant_inc','n_portion','sex'], inplace=True)
   df = df.melt(id_vars=['SV','geo'], var_name='time'\
           ,value_name='observation')
   return df
 
def hlth_ehis_fv3u(df: pd.DataFrame) -> pd.DataFrame:
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
   col1 = "n_portion,deg_urb,sex,age,unit,time"
   df = _split_column(df, col1)
   # Filtering out the wanted rows and columns.
   df = df[df['age'] == 'TOTAL']
   df = _replace_n_portion(df)
   df = _replace_sex(df)
   df = _replace_deg_urb(df)
   df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
   df['SV'] = 'Count_Person_' + df['deg_urb'] + '_' +\
   'HealthEnhancingEnhancingConsumptionOfFruitsAndVegetables' + df['sex']+'_'+\
   df['n_portion']+'_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['deg_urb']
   df.drop(columns=['unit','age','deg_urb','n_portion','sex'], inplace=True)
   df = df.melt(id_vars=['SV','time'], var_name='geo'\
       ,value_name='observation')
   return df
 
def hlth_ehis_fv1e(df: pd.DataFrame) -> pd.DataFrame:
   """
   Cleans the file hlth_ehis_fv1e for concatenation in Final CSV.
   Arguments: df (pd.DataFrame), the raw df as the input
   Returns: df (pd.DataFrame), provides the cleaned df as output
   """
   cols = ['unit,frequenc,coicop,isced11,sex,age,geo', '2019', '2014']
   df.columns = cols
   col1 = "unit,frequenc,coicop,isced11,sex,age,geo"
   df = _split_column(df, col1)
   # Filtering out the wanted rows and columns.
   df = df[df['age'] == 'TOTAL']
   df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
   df = _replace_coicop(df)
   df = _replace_sex(df)
   df = _replace_isced11(df)
   df = _replace_frequenc(df)
   df['SV'] = 'Count_Person_' + df['coicop'] + '_' + df['frequenc'] + '_' +\
   'HealthEnhancingConsumptionOfFruitsAndVegetables_' + df['isced11']+'_'+\
   df['sex']+'_'+ 'AsAFractionOf_Count_Person_' +df['isced11'] +'_' + df['sex']
   df.drop(columns=['unit','age','isced11','coicop','frequenc','sex'],\
        inplace=True)
   df = df.melt(id_vars=['SV','geo'], var_name='time'\
           ,value_name='observation')
   return df
 
def hlth_ehis_fv1u(df: pd.DataFrame) -> pd.DataFrame:
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
   col1 = "frequenc,coicop,deg_urb,sex,age,unit,time"
   df = _split_column(df, col1)
   # Filtering out the wanted rows and columns.
   df = df[df['age'] == 'TOTAL']
   df = _replace_coicop(df)
   df = _replace_frequenc(df)
   df = _replace_sex(df)
   df = _replace_deg_urb(df)
   df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
   df['SV'] = 'Count_Person_' + '_'+ df['coicop']+ '_' + df['frequenc'] +\
   '_'+df['deg_urb']+ '_' + 'HealthEnhancingEnhancingConsumptionOfFruitsAnd'+\
   'Vegetables' + df['sex']+'_' +'_AsAFractionOf_Count_Person_'+df['sex']+\
   '_'+df['deg_urb']
   df.drop(columns=['unit','age','deg_urb','coicop','frequenc','sex'],\
        inplace=True)
   df = df.melt(id_vars=['SV','time'], var_name='geo'\
       ,value_name='observation')
   return df
 
 
def hlth_ehis_fv3b(df: pd.DataFrame) -> pd.DataFrame:
  """
  Cleans the file hlth_ehis_fv3b for concatenation in Final CSV
  Input Taken: DF
  Output Provided: DF
  """
  cols = ['unit,n_portion,sex,age,c_birth,time','EU27_2020','EU28','BE','BG',
  'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
  'MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
  df.columns=cols
  col1 = "unit,n_portion,sex,age,c_birth,time"
  df = _split_column(df,col1)
  # Filtering out the wanted rows and columns  
  df = df[df['age'] == 'TOTAL']
 
  df = _replace_c_birth(df)
  df = _replace_sex(df)
  df = _replace_n_portion(df)
  df.drop(columns=['EU27_2020','EU28'],inplace=True)
  df['SV'] = 'Count_Person_'+df['n_portion']+'_'+ df['c_birth']+'_'+df['sex']+\
   '_'+'HealthEnhancingEnhancingConsumptionOfFruitsAndVegetables_'+\
   'AsAFractionOf_Count_Person_'+ df['n_portion']+'_'+df['sex']
  df.drop(columns=['unit','age','n_portion','c_birth','sex'],inplace=True)
  df = df.melt(id_vars=['SV','time'], var_name='geo'\
          ,value_name='observation')
  return df
def hlth_ehis_fv3c(df: pd.DataFrame) -> pd.DataFrame:
  """
  Cleans the file hlth_ehis_fv3c for concatenation in Final CSV
  Input Taken: DF
  Output Provided: DF
  """
  cols = ['unit,n_portion,sex,age,citizen,time', 'EU27_2020','EU28','BE','BG',
  'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
  'MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
  df.columns=cols
  col1 = "unit,n_portion,sex,age,citizen,time"
  df = _split_column(df,col1)
  # Filtering out the wanted rows and columns  
  df = df[df['age'] == 'TOTAL']
  df = _replace_citizen(df)
  df = _replace_sex(df)
  df = _replace_n_portion(df)
  df.drop(columns=['EU27_2020','EU28'],inplace=True)
  df['SV'] = 'Count_Person_'+df['n_portion']+'_'+ df['citizen']+'_'+df['sex']+\
      '_'+'HealthEnhancingEnhancingConsumptionOfFruitsAndVegetables_'+\
       'AsAFractionOf_Count_Person_'+df['n_portion']+'_'+df['sex']
  df.drop(columns=['unit','age','n_portion','citizen','sex'],inplace=True)
  df = df.melt(id_vars=['SV','time'], var_name='geo'\
          ,value_name='observation')
  return df
 
def hlth_ehis_fv3d(df: pd.DataFrame) -> pd.DataFrame:
  """
  Cleans the file hlth_ehis_fv3d for concatenation in Final CSV
  Input Taken: DF
  Output Provided: DF
  """
  cols = ['n_portion,lev_limit,sex,age,unit,time', 'EU27_2020','EU28','BE',
  'BG','CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU',
  'HU','MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
  df.columns=cols
  col1 = "n_portion,lev_limit,sex,age,unit,time"
  df = _split_column(df,col1)
  # Filtering out the wanted rows and columns  
  df = df[df['age'] == 'TOTAL']
  df = _replace_lev_limit(df)
  df = _replace_sex(df)
  df = _replace_n_portion(df)
  df.drop(columns=['EU27_2020','EU28'],inplace=True)
  df['SV'] = 'Count_Person_'+df['n_portion']+'_'+df['lev_limit']+'_'+\
      df['sex']+'_'+'HealthEnhancingEnhancingConsumptionOfFruitsAnd'+\
      'Vegetables_AsAFractionOf_Count_Person_'+ df['n_portion']+'_'+df['sex']
  df.drop(columns=['unit','age','n_portion','lev_limit','sex'],inplace=True)
  df = df.melt(id_vars=['SV','time'], var_name='geo'\
          ,value_name='observation')
  return df
 
def hlth_ehis_fv3m(df: pd.DataFrame) -> pd.DataFrame:
  """
  Cleans the file hlth_ehis_fv3m for concatenation in Final CSV
  Input Taken: DF
  Output Provided: DF
  """
  cols = ['unit,n_portion,sex,age,bmi,time', 'EU27_2020','BE','BG','CZ','DK',
  'DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU','MT','NL',
  'AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','RS','TR']
  df.columns=cols
  col1 = "unit,n_portion,sex,age,bmi,time"
  df = _split_column(df,col1)
  # Filtering out the wanted rows and columns  
  df = df[df['age'] == 'TOTAL']
  df = _replace_bmi(df)
  df = _replace_sex(df)
  df = _replace_n_portion(df)
  df.drop(columns=['EU27_2020'],inplace=True)
  df['SV'] = 'Count_Person_'+df['n_portion']+'_'+ df['bmi'] +'_'+df['sex']+\
      '_'+'HealthEnhancingEnhancingConsumptionOfFruitsAndVegetables_'+\
       'AsAFractionOf_Count_Person_'+ df['n_portion']+'_'+df['sex']
  df.drop(columns=['unit','age','n_portion','bmi','sex'],inplace=True)
  df = df.melt(id_vars=['SV','time'], var_name='geo'\
          ,value_name='observation')
  return df
 
def hlth_ehis_fv1b(df: pd.DataFrame) -> pd.DataFrame:
  """
  Cleans the file hlth_ehis_fv1b for concatenation in Final CSV
  Input Taken: DF
  Output Provided: DF
  """
  cols = ['unit,frequenc,coicop,c_birth,sex,age,time', 'EU27_2020','EU28','BE',
  'BG','CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU',
  'HU','MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
  df.columns=cols
  col1 = "unit,frequenc,coicop,c_birth,sex,age,time"
  df = _split_column(df,col1)
  # Filtering out the wanted rows and columns  
  df = df[df['age'] == 'TOTAL']
  df = _replace_coicop(df)
  df = _replace_sex(df)
  df = _replace_c_birth(df)
  df.drop(columns=['EU27_2020','EU28'],inplace=True)
  df['SV'] = 'Count_Person_'+df['c_birth']+'_'+ df['coicop'] +'_'+df['sex']+\
      '_'+'HealthEnhancingEnhancingConsumptionOfFruitsAndVegetables_'+\
       'AsAFractionOf_Count_Person_'+ df['c_birth']+'_'+df['sex']
  df.drop(columns=['unit','age','c_birth','coicop','sex'],inplace=True)
  df = df.melt(id_vars=['SV','time'], var_name='geo'\
          ,value_name='observation')
  return df
 
 
def hlth_ehis_fv1c(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_fv1c for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['unit,frequenc,coicop,sex,age,citizen,time','EU27_2020','EU28','BE',
 'BG','CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU',
 'HU','MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
 df.columns=cols
 col1 = "unit,frequenc,coicop,sex,age,citizen,time"
 df = _split_column(df,col1)
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_frequenc(df)
 df = _replace_coicop(df)
 df = _replace_sex(df)
 df = _replace_citizen(df)
 df.drop(columns=['EU27_2020','EU28'],inplace=True)
 df['SV'] = 'Count_Person_'+df['citizen']+'_'+df['coicop']+'_'+df['frequenc']+\
     '_'+df['sex']+'_'+'HealthEnhancingEnhancingConsumptionOfFruitsAnd'+\
     'Vegetables_AsAFractionOf_Count_Person_'+ df['citizen']+'_'+df['sex']
 df.drop(columns=['unit','age','citizen','coicop','frequenc','sex'],\
     inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
 
def hlth_ehis_fv1i(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_fv1i for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['unit,frequenc,coicop,sex,age,quant_inc,time','EU27_2020','BE','BG',
 'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
 'MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','RS','TR']
 df.columns=cols
 col1 = "unit,frequenc,coicop,sex,age,quant_inc,time"
 df = _split_column(df,col1)
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_frequenc(df)
 df = _replace_coicop(df)
 df = _replace_sex(df)
 df = _replace_quant_inc(df)
 df.drop(columns=['EU27_2020'],inplace=True)
 df['SV'] = 'Count_Person_'+df['quant_inc']+'_'+ df['coicop'] + '_' +\
   df['frequenc'] +'_'+df['sex']+'_'+'HealthEnhancingEnhancingConsumption'+\
   'OfFruitsAndVegetables_AsAFractionOf_Count_Person_'+df['quant_inc']+\
   '_'+df['sex']
 df.drop(columns=['unit','age','quant_inc','coicop','frequenc','sex'],\
     inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
 
def hlth_ehis_fv1m(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_fv1m for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['unit,frequenc,coicop,sex,age,bmi,time','EU27_2020','BE','BG','CZ',
 'DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU','MT',
 'NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','RS','TR']
 df.columns=cols
 col1 = "unit,frequenc,coicop,sex,age,bmi,time"
 df = _split_column(df,col1)
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_frequenc(df)
 df = _replace_coicop(df)
 df = _replace_sex(df)
 df = _replace_bmi(df)
 df.drop(columns=['EU27_2020'],inplace=True)
 df['SV'] = 'Count_Person_'+df['bmi']+'_'+ df['coicop']+'_'+df['frequenc'] +\
     '_'+df['sex']+'_'+'HealthEnhancingEnhancingConsumptionOfFruitsAnd'+\
     'Vegetables_AsAFractionOf_Count_Person_'+ df['bmi']+'_'+df['sex']
 df.drop(columns=['unit','age','bmi','coicop','frequenc','sex'],inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
 
def hlth_ehis_fv1d(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_fv1d for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['frequenc,coicop,lev_limit,sex,age,unit,time','EU27_2020','EU28','BE',
 'BG','CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU',
 'HU','MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
 df.columns=cols
 col1 = "frequenc,coicop,lev_limit,sex,age,unit,time"
 df = _split_column(df,col1)
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_frequenc(df)
 df = _replace_coicop(df)
 df = _replace_sex(df)
 df = _replace_lev_limit(df)
 df.drop(columns=['EU27_2020','EU28'],inplace=True)
 df['SV'] = 'Count_Person_'+df['lev_limit']+'_'+ df['coicop']+'_'+\
     df['frequenc'] +'_'+df['sex']+'_'+'HealthEnhancingEnhancingConsumption'+\
     'OfFruitsAndVegetables_AsAFractionOf_Count_Person_'+df['lev_limit']+\
     '_'+df['sex']
 df.drop(columns=['unit','age','lev_limit','coicop','frequenc','sex'],\
     inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
 
def hlth_ehis_fv7e(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_fv7e for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['unit,frequenc,sex,age,isced11,time','EU27_2020','BE','BG','CZ','DK',
 'DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU','MT','AT',
 'PL','PT','RO','SI','SK','FI','SE','IS','NO','RS','TR']
 df.columns=cols
 col1 = "unit,frequenc,sex,age,isced11,time"
 df = _split_column(df,col1)
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_frequenc(df)
 df = _replace_sex(df)
 df = _replace_isced11(df)
 df.drop(columns=['EU27_2020'],inplace=True)
 df['SV'] = 'Count_Person_'+df['isced11']+'_'+df['frequenc'] +'_'+df['sex']+\
     '_'+'HealthEnhancingEnhancingConsumptionOfFruitsAndVegetables_'+\
       'AsAFractionOf_Count_Person_'+df['isced11']+'_'+df['sex']
 df.drop(columns=['unit','age','isced11','frequenc','sex'],inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
 
def hlth_ehis_fv7m(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_fv7m for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['unit,frequenc,sex,age,bmi,time', 'EU27_2020','BE','BG','CZ','DK',
 'DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU','MT','AT',
 'PL','PT','RO','SI','SK','FI','SE','IS','NO','RS','TR']
 df.columns=cols
 col1 = "unit,frequenc,sex,age,bmi,time"
 df = _split_column(df,col1)
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_frequenc(df)
 df = _replace_sex(df)
 df = _replace_bmi(df)
 df.drop(columns=['EU27_2020'],inplace=True)
 df['SV'] = 'Count_Person_'+df['bmi']+'_'+df['frequenc'] +'_'+df['sex']+\
     '_'+'HealthEnhancingEnhancingConsumptionOfFruitsAndVegetables_'+\
       'AsAFractionOf_Count_Person_'+df['bmi']+'_'+df['sex']
 df.drop(columns=['unit','age','bmi','frequenc','sex'],inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
 
def hlth_ehis_fv7i(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_fv7i for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['unit,frequenc,sex,age,quant_inc,time','EU27_2020','BE','BG','CZ',
 'DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU','MT',
 'AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','RS','TR']
 df.columns=cols
 col1 = "unit,frequenc,sex,age,quant_inc,time"
 df = _split_column(df,col1)
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_frequenc(df)
 df = _replace_sex(df)
 df = _replace_quant_inc(df)
 df.drop(columns=['EU27_2020'],inplace=True)
 df['SV'] = 'Count_Person_'+ df['frequenc']+'_' + df['quant_inc']+ '_'+\
   df['sex']+'_'+'HealthEnhancingEnhancingConsumptionOfFruitsAndVegetables_'+\
   'AsAFractionOf_Count_Person_'+ df['quant_inc']+'_'+ df['sex']
 df.drop(columns=['unit','age','quant_inc','frequenc','sex'],inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
 
def hlth_ehis_de7(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_de7 for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['sex,age,frequenc,isced97,time','BE','BG','CZ','EE','EL','ES','FR',
 'CY','LV','HU','MT','PL','RO','SI','SK','TR']
 df.columns=cols
 col1 = "sex,age,frequenc,isced97,time"
 df = _split_column(df,col1)
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_frequenc(df)
 df = _replace_sex(df)
 df = _replace_isced97(df)
 df['SV'] = 'Count_Person_'+ df['frequenc']+'_' + df['isced97']+ '_'+\
   df['sex']+'_'+'HealthEnhancingEnhancingConsumptionOfFruitsAndVegetables_'+\
   'AsAFractionOf_Count_Person_'+ df['isced97']+'_'+ df['sex']
 df.drop(columns=['age','isced97','frequenc','sex'],inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
 
def hlth_ehis_de8(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_de8 for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['sex,age,frequenc,isced97,time','BE','BG','CZ','EE','EL','ES','FR',
 'CY','LV','HU','MT','PL','RO','SI','SK','TR']
 df.columns=cols
 col1 = "sex,age,frequenc,isced97,time"
 df = _split_column(df,col1)
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_frequenc(df)
 df = _replace_sex(df)
 df = _replace_isced97(df)
 df['SV'] = 'Count_Person_'+ df['frequenc']+'_' + df['isced97']+ '_'+\
   df['sex']+'_'+'HealthEnhancingEnhancingConsumptionOfFruitsAndVegetables_'+\
   'AsAFractionOf_Count_Person_'+ df['isced97']+'_'+ df['sex']
 df.drop(columns=['age','isced97','frequenc','sex'],inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
 
def _replace_bmi(df:pd.DataFrame) -> pd.DataFrame:
  """
  Replaces values of a single column into true values
  from metadata returns the DF
  """
  _dict = {
   'BMI_LT18P5' :  'Underweight',
   'BMI18P5-24' : 'Normal',
   'BMI_GE25' :    'Overweight',
   'BMI25-29' :    'Pre-obese',
   'BMI_GE30' :    'Obese'
      }
  df = df.replace({'bmi': _dict})
  return df
 
def _replace_lev_limit(df:pd.DataFrame) -> pd.DataFrame:
  """
  Replaces values of a single column into true values
  from metadata returns the DF
  """
  _dict = {
      'MOD': 'Moderate',
      'SEV': 'Severe',
      'SM_SEV': 'SomeOrSevere',
      'NONE': 'None'
      }
  df = df.replace({'lev_limit': _dict})
  return df
 
def _replace_citizen(df: pd.DataFrame) -> pd.DataFrame:
   """
   Replaces values of a single column into true values
   from metadata returns the DF.
   Arguments: df (pd.DataFrame)
   Returns: df (pd.DataFrame)
   """
   citizen = {
       'EU28_FOR': 'ForeignWithinEU28',
       'NEU28_FOR': 'ForeignOutsideEU28',
       'FOR': 'NotACitizen',
       'NAT': 'Citizen'
   }
   df = df.replace({'citizen': citizen})
   return df
 
 
def _replace_c_birth(df:pd.DataFrame) -> pd.DataFrame:
  """
  Replaces values of a single column into true values
  from metadata returns the DF
  """
  _dict = {
      'EU28_FOR': 'EU28CountriesExceptReportingCountry',
   'NEU28_FOR': 'Non-EU28CountriesNorReportingCountry',
   'FOR': 'ForeignCountry',
   'NAT': 'ReportingCountry'
      }
  df = df.replace({'c_birth': _dict})
  return df
def _replace_sex(df: pd.DataFrame) -> pd.DataFrame:
   """
   Replaces values of a single column into true values
   from metadata returns the DF.
   Arguments: df (pd.DataFrame)
   Returns: df (pd.DataFrame)
   """
   sex = {'F': 'Female', 'M': 'Male', 'T': 'Total'}
   df = df.replace({'sex': sex})
   return df
 
 
def _replace_n_portion(df: pd.DataFrame) -> pd.DataFrame:
   """
   Replaces values of a single column into true values
   from metadata returns the DF.
   Arguments: df (pd.DataFrame)
   Returns: df (pd.DataFrame)
   """
   n_portion = {
       '0': '0Portions',
       '1-4': 'From1To4Portions',
       'GE5': '5PortionsOrMore'
   }
   df = df.replace({'n_portion': n_portion})
   return df
 
 
def _replace_isced11(df: pd.DataFrame) -> pd.DataFrame:
   """
   Replaces values of a single column into true values
   from metadata returns the DF.
   Arguments: df (pd.DataFrame)
   Returns: df (pd.DataFrame)
   """
   isced11 = {
       'ED0-2': 'EducationalAttainment'+\
       'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
       'ED3_4': 'EducationalAttainment'+\
       'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
       'ED5-8': 'EducationalAttainmentTertiaryEducation',
       'TOTAL': 'Total'
       }
   df = df.replace({'isced11': isced11})
   return df
 
def _replace_isced97(df: pd.DataFrame) -> pd.DataFrame:
   """
   Replaces values of a single column into true values
   from metadata returns the DF.
   Arguments: df (pd.DataFrame)
   Returns: df (pd.DataFrame)
   """
   isced97 = {
       'ED0-2': 'EducationalAttainment'+\
       'PrePrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
       'ED3_4': 'EducationalAttainment'+\
       'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
       'ED5_6': 'EducationalAttainment'+\
       'FirstOrSecondStageOfTertiaryEducation',
       'TOTAL': 'Total'
       }
   df = df.replace({'isced97': isced97})
   return df
 
def _replace_quant_inc(df: pd.DataFrame) -> pd.DataFrame:
   """
   Replaces values of a single column into true values
   from metadata returns the DF.
   Arguments: df (pd.DataFrame)
   Returns: df (pd.DataFrame)
   """
 
   quant_inc = {
       'TOTAL': 'Total',
       'QU1': 'Percentile0To20',
       'QU2': 'Percentile20To40',
       'QU3': 'Percentile40To60',
       'QU4': 'Percentile60To80',
       'QU5': 'Percentile80To100'
   }
   df = df.replace({'quant_inc': quant_inc})
   return df
 
def _replace_deg_urb(df: pd.DataFrame) -> pd.DataFrame:
   """
   Replaces values of a single column into true values
   from metadata returns the DF.
   Arguments: df (pd.DataFrame)
   Returns: df (pd.DataFrame)
   """
   deg_urb = {
       'TOTAL': 'Total',
       'DEG1': 'Cities',
       'DEG2': 'TownsAndSuburbs',
       'DEG3': 'RuralAreas',
   }
   df = df.replace({'deg_urb': deg_urb})
   return df
 
def _replace_coicop(df: pd.DataFrame) -> pd.DataFrame:
   """
   Replaces values of a single column into true values
   from metadata returns the DF.
   Arguments: df (pd.DataFrame)
   Returns: df (pd.DataFrame)
   """
   coicop = {
       'CP0116': 'Fruit',
       'CP0117': 'Vegetables'
   }
   df = df.replace({'coicop': coicop})
   return df
 
def _replace_frequenc(df: pd.DataFrame) -> pd.DataFrame:
   """
   Replaces values of a single column into true values
   from metadata returns the DF.
   Arguments: df (pd.DataFrame)
   Returns: df (pd.DataFrame)
   """
   frequenc = {
       'GE1D': 'AtLeastOnceADay',
       '1-3W': 'From1To3TimesAWeek',
       '4-6W': 'From4To6TimesAWeek',
       'NVR_OCC': 'NeverOrOccasionally'
   }
   df = df.replace({'frequenc': frequenc})
   return df
 
def _split_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
   """
   Divides a single column into multiple columns and returns the DF.
   Arguments: df (pd.DataFrame)
   Returns: df (pd.DataFrame)
   """
   info = col.split(",")
   df[info] = df[col].str.split(',', expand=True)
   df.drop(columns=[col], inplace=True)
   return df
 
 
class EuroStatConsumptionOfFruitsAndVegetables:
   """
   This Class has requried methods to generate Cleaned CSV,
   MCF and TMCF Files.
   """
 
   def __init__(self, input_files: list, csv_file_path: str) -> None:
       self.input_files = input_files
       self.cleaned_csv_file_path = csv_file_path
 
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
               "hlth_ehis_fv3e": hlth_ehis_fv3e,
               "hlth_ehis_fv3i": hlth_ehis_fv3i,
               "hlth_ehis_fv3u": hlth_ehis_fv3u,
               "hlth_ehis_fv1e": hlth_ehis_fv1e,
               "hlth_ehis_fv1u": hlth_ehis_fv1u,
               "hlth_ehis_fv3b": hlth_ehis_fv3b,
               "hlth_ehis_fv3c": hlth_ehis_fv3c,
               "hlth_ehis_fv3d": hlth_ehis_fv3d,
               "hlth_ehis_fv3m": hlth_ehis_fv3m,
               "hlth_ehis_fv1b": hlth_ehis_fv1b,
               "hlth_ehis_fv1c": hlth_ehis_fv1c,
               "hlth_ehis_fv1i": hlth_ehis_fv1i,
               "hlth_ehis_fv1m": hlth_ehis_fv1m,
               "hlth_ehis_fv1d": hlth_ehis_fv1d,
               "hlth_ehis_fv7e": hlth_ehis_fv7e,
               "hlth_ehis_fv7m": hlth_ehis_fv7m,
               "hlth_ehis_fv7i": hlth_ehis_fv7i,
               "hlth_ehis_de7": hlth_ehis_de7,
               "hlth_ehis_de8": hlth_ehis_de8
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
 
def main(_):
   input_path = FLAGS.input_path
   if not os.path.exists(input_path):
       os.mkdir(input_path)
   ip_files = os.listdir(input_path)
   ip_files = [input_path + os.sep + file for file in ip_files]
   data_file_path = os.path.dirname(
       os.path.abspath(__file__)) + os.sep + "output"
   # Defining Output Files
   csv_name = "eurostat_population_consumptionoffruitsandvegetables.csv"
   cleaned_csv_path = data_file_path + os.sep + csv_name
   loader = EuroStatConsumptionOfFruitsAndVegetables(ip_files,cleaned_csv_path)
   loader.process()
 
 
if __name__ == "__main__":
   app.run(main)