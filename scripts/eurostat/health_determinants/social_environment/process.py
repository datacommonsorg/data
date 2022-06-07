 
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
# from alpha2_to_dcid import COUNTRY_MAP
from absl import app
from absl import flags
# pd.set_option("display.max_columns", None)
# pd.set_option("display.max_rows", None)
FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
  os.path.abspath(__file__)) + os.sep + "input_file"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")
def hlth_ehis_ss1e(df: pd.DataFrame) -> pd.DataFrame:
  """
  Cleans the file hlth_ehis_pe9e for concatenation in Final CSV
  Input Taken: DF
  Output Provided: DF
  """
  cols = ['unit,lev_perc,isced11,sex,age,geo', '2019', '2014']
  df.columns=cols
  col1 = "unit,lev_perc,isced11,sex,age,geo"
  df = _split_column(df,col1)
  # Filtering out the wanted rows and columns  
  df = df[df['age'] == 'TOTAL']
  df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
  df = _replace_lev_perc(df)
  df = _replace_sex(df)
  df = _replace_isced11(df)
  df['SV'] = 'Count_Person_'+df['isced11']+'_'+ df['lev_perc'] +'_'+df['sex']+\
      '_'+'HealthEnhancingSocialEnvironment_AsAFractionOf_Count_Person_'+\
      df['isced11']+'_'+df['sex']
  df.drop(columns=['unit','age','isced11','lev_perc','sex'],inplace=True)
  df = df.melt(id_vars=['SV','geo'], var_name='time'\
          ,value_name='observation')
  return df
 
def hlth_ehis_ss1u(df: pd.DataFrame) -> pd.DataFrame:
   """
   Cleans the file hlth_ehis_pe1u for concatenation in Final CSV
   Input Taken: DF
   Output Provided: DF
   """
   cols = ['lev_perc,deg_urb,sex,age,unit,time','EU27_2020','EU28','BE','BG',
   'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU',
   'HU','MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
   df.columns=cols
   col1 = "lev_perc,deg_urb,sex,age,unit,time"
   df = _split_column(df,col1)
   # Filtering out the wanted rows and columns
   df = df[df['age'] == 'TOTAL']
   df = _replace_deg_urb(df)
   df = _replace_sex(df)
   df = _replace_lev_perc(df)
   df.drop(columns=['EU27_2020','EU28','unit','age'],inplace=True)
   df['SV'] = 'Count_Person_' + df['deg_urb'] + '_' + df['lev_perc']+ '_' +\
   df['sex'] + '_' + 'WorkRelatedSocialEnvoronment' +\
   '_AsAFractionOf_Count_Person_' + df['deg_urb'] +'_' + df['sex']
   df.drop(columns=['lev_perc','deg_urb','sex'],inplace=True)
   df = df.melt(id_vars=['SV','time'], var_name='geo'\
       ,value_name='observation')
   return df
 
def hlth_ehis_ic1e(df: pd.DataFrame) -> pd.DataFrame:
  """
  Cleans the file hlth_ehis_pe9e for concatenation in Final CSV
  Input Taken: DF
  Output Provided: DF
  """
  cols = ['unit,assist,isced11,sex,age,geo', '2019', '2014']
  df.columns=cols
  col1 = "unit,assist,isced11,sex,age,geo"
  df = _split_column(df,col1)
  # Filtering out the wanted rows and columns  
  df = df[df['age'] == 'TOTAL']
  df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
  df = _replace_assist(df)
  df = _replace_sex(df)
  df = _replace_isced11(df)
  df['SV'] = 'Count_Person_' + df['assist'] + '_' + df['isced11'] + '_' +\
   df['sex'] + '_' + 'HealthEnhancingSocialEnvironment_AsAFractionOf_'+\
   'Count_Person_' + df['isced11'] + '_' + df['sex']
  df.drop(columns=['unit','age','isced11','assist','sex'],inplace=True)
  df = df.melt(id_vars=['SV','geo'], var_name='time'\
          ,value_name='observation')
  return df
 
def hlth_ehis_ic1u(df: pd.DataFrame) -> pd.DataFrame:
  """
  Cleans the file hlth_ehis_pe9e for concatenation in Final CSV
  Input Taken: DF
  Output Provided: DF
  """
  cols = ['assist,deg_urb,sex,age,unit,time','EU27_2020','EU28','BE','BG','CZ',
  'DK','DE','EE','IE','EL','ES','HR','IT','CY','LV','LT','LU','HU','MT',
  'NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
  df.columns=cols
  col1 = "assist,deg_urb,sex,age,unit,time"
  df = _split_column(df,col1)
  # Filtering out the wanted rows and columns  
  df = df[df['age'] == 'TOTAL']
  df = _replace_deg_urb(df)
  df = _replace_sex(df)
  df = _replace_assist(df)
  df.drop(columns=['EU27_2020','EU28'],inplace=True)
  df['SV'] = 'Count_Person_'+df['assist']+'_'+ df['deg_urb'] +'_'+df['sex']+\
   '_'+'HealthEnhancingSocialEnvironment_AsAFractionOf_Count_Person_'+\
   df['deg_urb']+'_' + df['sex']
  df.drop(columns=['unit','age','assist','deg_urb','sex'],inplace=True)
  df = df.melt(id_vars=['SV','time'], var_name='geo'\
          ,value_name='observation')
  return df
 
def hlth_ehis_ss1b(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_pe9e for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['unit,lev_perc,sex,age,c_birth,time','EU27_2020','EU28','BE','BG',
   'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
   'MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR ']
 df.columns=cols
 col1 = "unit,lev_perc,sex,age,c_birth,time"
 df = _split_column(df,col1)
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_lev_perc(df)
 df = _replace_sex(df)
 df = _replace_c_birth(df)
 df.drop(columns=['EU27_2020','EU28'],inplace=True)
 df['SV'] = 'Count_Person_'+df['c_birth']+'_'+ df['lev_perc'] +'_'+df['sex']+\
     '_'+'HealthEnhancingSocialEnvironment_AsAFractionOf_Count_Person_'+\
     df['c_birth']+'_'+df['sex']
 df.drop(columns=['unit','age','c_birth','lev_perc','sex'],inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
 
def hlth_ehis_ss1c(df: pd.DataFrame) -> pd.DataFrame:
 """
 Cleans the file hlth_ehis_pe9e for concatenation in Final CSV
 Input Taken: DF
 Output Provided: DF
 """
 cols = ['unit,lev_perc,sex,age,citizen,time','EU27_2020','EU28','BE','BG',
   'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
   'MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR ']
 df.columns=cols
 col1 = "unit,lev_perc,sex,age,citizen,time"
 df = _split_column(df,col1)
 # Filtering out the wanted rows and columns 
 df = df[df['age'] == 'TOTAL']
 df = _replace_lev_perc(df)
 df = _replace_sex(df)
 df = _replace_citizen(df)
 df.drop(columns=['EU27_2020','EU28'],inplace=True)
 df['SV'] = 'Count_Person_'+ df['citizen'] + '_' + df['lev_perc'] + '_'\
   + df['sex'] + '_' + 'HealthEnhancingSocialEnvironment_AsAFractionOf_'+\
   'Count_Person_' + df['citizen'] + '_' + df['sex']
 df.drop(columns=['unit','age','citizen','lev_perc','sex'],inplace=True)
 df = df.melt(id_vars=['SV','time'], var_name='geo'\
         ,value_name='observation')
 return df
 
def hlth_ehis_ss1d(df: pd.DataFrame) -> pd.DataFrame:
  """
  Cleans the file hlth_ehis_pe9e for concatenation in Final CSV
  Input Taken: DF
  Output Provided: DF
  """
  cols = ['unit,lev_perc,sex,age,lev_limit,time', 'EU27_2020','EU28','BE','BG',
   'CZ','DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU',
   'MT','NL','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR ']
  df.columns=cols
  col1 = "unit,lev_perc,sex,age,lev_limit,time"
  df = _split_column(df,col1)
  # Filtering out the wanted rows and columns  
  df = df[df['age'] == 'TOTAL']
  df = _replace_lev_perc(df)
  df = _replace_sex(df)
  df = _replace_lev_limit(df)
  df['SV'] = 'Count_Person_' + df['lev_limit'] + '_' + df['lev_perc'] + '_' +\
   df['sex'] + '_' + 'HealthEnhancingSocialEnvironment_AsAFractionOf_'+\
   'Count_Person_' + df['lev_limit']+'_'+df['sex']
  df.drop(columns=['unit','age','lev_limit','lev_perc','sex'],inplace=True)
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
def _replace_lev_perc(df:pd.DataFrame) -> pd.DataFrame:
  """
  Replaces values of a single column into true values
  from metadata returns the DF
  """
  _dict = {
      'STR' : 'Strong',
      'INT' : 'Intermediate',
      'POOR' : 'Poor'
      }
  df = df.replace({'lev_perc': _dict})
  return df
def _replace_isced11(df:pd.DataFrame) -> pd.DataFrame:
  """
  Replaces values of a single column into true values
  from metadata returns the DF
  """
  _dict = {
      'ED0-2': 'EducationalAttainment'+\
      'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
      'ED3_4': 'EducationalAttainment'+\
          'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
      'ED5-8': 'EducationalAttainmentTertiaryEducation',
      'TOTAL': 'Total'
      }
  df = df.replace({'isced11': _dict})
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
 
def _replace_assist(df:pd.DataFrame) -> pd.DataFrame:
  """
  Replaces values of a single column into true values
  from metadata returns the DF
  """
  _dict = {
      'PROV' : 'AssistanceProvided',
      'PROV_R' : 'AssistanceProvidedMainlyToRelatives',
      'PROV_NR' : 'AssistanceProvidedMainlyToNonRelatives',
      'NPROV'   : 'NoAssistanceProvided'
      }
  df = df.replace({'assist': _dict})
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
 
def _replace_citizen(df:pd.DataFrame) -> pd.DataFrame:
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
 df = df.replace({'citizen': _dict})
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
 
def _split_column(df: pd.DataFrame,col: str) -> pd.DataFrame:
  """
  Divides a single column into multiple columns and returns the DF
  """
  info = col.split(",")
  df[info] = df[col].str.split(',', expand=True)
  df.drop(columns=[col],inplace=True)
  return df
class EuroStatSocialEnvironment:
  """
  This Class has requried methods to generate Cleaned CSV,
  MCF and TMCF Files
  """
  def __init__(self, input_files: list, csv_file_path: str) -> None:
      self.input_files = input_files
      self.cleaned_csv_file_path = csv_file_path
      self.df = None
      self.file_name = None
      self.scaling_factor = 1
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
          if 'hlth_ehis_ss1e' in file_path:
              df = hlth_ehis_ss1e(df)
          elif 'hlth_ehis_ss1u' in file_path:
              df = hlth_ehis_ss1u(df)
          elif 'hlth_ehis_ic1e' in file_path:
              df = hlth_ehis_ic1e(df)
          elif 'hlth_ehis_ic1u' in file_path:
              df = hlth_ehis_ic1u(df)
          elif 'hlth_ehis_ss1b' in file_path:
              df = hlth_ehis_ss1b(df)
          elif 'hlth_ehis_ss1c' in file_path:
              df = hlth_ehis_ss1c(df)
          elif 'hlth_ehis_ss1d' in file_path:
              df = hlth_ehis_ss1d(df)
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
      # final_df = final_df.replace({'geo': COUNTRY_MAP})
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
  cleaned_csv_path = data_file_path + os.sep + \
      "EuroStat_Population_SocialEnvironment.csv"
  loader = EuroStatSocialEnvironment(ip_files, cleaned_csv_path)
  loader.process()
if __name__ == "__main__":
  app.run(main)