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
'''
This Python Script is for State Level Data 1990-2000.
'''
import os
import pandas as pd
from common_functions import input_url


def state1990(url_file: str, output_folder: str):
    '''
    This Python Script Loads csv datasets from 1990-2000 on a State Level,
    cleans it and create a cleaned csv.
    '''
    _urls = input_url(url_file, "1990-00")
    # Used to collect data after every loop for every file's df.
    final_df = pd.DataFrame()
    for url in _urls:
        df = pd.read_table(url, skiprows=15, delim_whitespace=True, header=None)
        df.columns=['Year','geo_ID','Age','NHWM','NHWF','NHBM','NHBF','NHAIANM'\
        ,'NHAIANF','NHAPIM','NHAPIF','HWM','HWF','HBM','HBF','HAIANM','HAIANF',\
        'HAPIM','HAPIF']
        # Defining New Columns as Aggregation is required in all.
        df['Male']=df["NHWM"]+df["HWM"]+df["NHBM"]+df["HBM"]+df["NHAIANM"]+\
            df["HAIANM"]+df["NHAPIM"]+df["HAPIM"]
        df['Female']=df["NHWF"]+df["HWF"]+df["NHBF"]+df["HBF"]+df["NHAIANF"]+\
            df["HAIANF"]+df["NHAPIF"]+df["HAPIF"]
        df['WhiteAlone']=\
            df["NHWM"]+df["HWM"]+df["NHWF"]+df["HWF"]
        df['BlackOrAfricanAmericanAlone']=\
            df["NHBM"]+df["HBM"]+df["NHBF"]+df["HBF"]
        df['AmericanIndianAndAlaskaNativeAlone']\
            =df["NHAIANM"]+df["HAIANM"]+df["NHAIANF"]+df["HAIANF"]
        df['AsianOrPacificIslander']=df["NHAPIM"]+df["HAPIM"]+df["NHAPIF"]\
            +df["HAPIF"]
        df['Male_WhiteAlone'] = df["NHWM"] + df["HWM"]
        df['Female_WhiteAlone'] = df["NHWF"] + df["HWF"]
        df['Male_BlackOrAfricanAmericanAlone'] = df["NHBM"] + df["HBM"]
        df['Female_BlackOrAfricanAmericanAlone'] = df["NHBF"] + df["HBF"]
        df['Male_AmericanIndianAndAlaskaNativeAlone'] = df["NHAIANM"] + df[
            "HAIANM"]
        df['Female_AmericanIndianAndAlaskaNativeAlone']=\
            df["NHAIANF"]+df["HAIANF"]
        df['Male_AsianOrPacificIslander'] = df["NHAPIM"] + df["HAPIM"]
        df['Female_AsianOrPacificIslander'] = df["NHAPIF"] + df["HAPIF"]
        # Dropping the old unwanted columns.
        df.drop(columns=['NHWM','NHWF','NHBM','NHBF','NHAIANM','NHAIANF',\
            'NHAPIM','NHAPIF','HWM','HWF','HBM','HBF','HAIANM','HAIANF','HAPIM'\
            ,'HAPIF'],inplace=True)
        df['geo_ID'] = [f'{x:02}' for x in df['geo_ID']]
        df['geo_ID'] = 'geoId/' + df['geo_ID']
        df['Age'] = df['Age'].astype(str)
        df['Age'] = df['Age'] + 'Years'
        df['Age'] = df['Age'].str.replace("85Years", "85OrMoreYears")
        df = df.melt(id_vars=['Year','geo_ID','Age'], var_name='sv' , \
            value_name='observation')
        df['SVs'] = 'Count_Person_' + df['Age'] + '_' + df['sv']
        df.drop(columns=['Age', 'sv'], inplace=True)
        df.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
        final_df = pd.concat([final_df, df])

    final_df.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder,
                     'state_1990_2000.csv'))
    final_df['geo_ID'] = 'country/USA'
    final_df = final_df.groupby(['geo_ID','Year','Measurement_Method','SVs'])\
        .sum()
    final_df.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder,
                     'national_1990_2000.csv'))
