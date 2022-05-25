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
This Python Script is for
for County Level Data
1970-1979
'''
import os
import json
import pandas as pd


def county1970():
    '''
   This Python Script Loads csv datasets
   from 1970-1979 on a County Level,
   cleans it and create a cleaned csv
   '''
    # Getting input URL from the JSON file
    _URLS_JSON_PATH = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "county.json"
    _URLS_JSON = None
    with open(_URLS_JSON_PATH, encoding="UTF-8") as file:
        _URLS_JSON = json.load(file)
    _url = _URLS_JSON["1970-79"]
    _cols=['Year','geo_ID','Race',0,1,2,3,4,5,6,7\
                      ,8,9,10,11,12,13,14,15,16,17]
    final_df = pd.DataFrame()
    df2 = pd.DataFrame()
    df = pd.read_csv(_url, names=_cols, low_memory=False, encoding='ISO-8859-1')
    df = (df.drop(_cols, axis=1).join(df[_cols]))
    df['geo_ID'] = df['geo_ID'].astype(int)
    df['geo_ID'] = [f'{x:05}' for x in df['geo_ID']]
    df['Race'] = df['Race'].astype(str)
    # Replacing the numbers with more understandable metadata headings
    _dict = {
        '1': 'Male_WhiteAlone',
        '2': 'Female_WhiteAlone',
        '3': 'Male_BlackOrAfricanAmericanAlone',
        '4': 'Female_BlackOrAfricanAmericanAlone',
        '5': 'Male_OtherRaces',
        '6': 'Female_OtherRaces'
    }
    df = df.replace({'Race': _dict})
    # Replacing the numbers with more understandable metadata headings
    _dict = {
        0: '0To4Years',
        1: '5To9Years',
        2: '10To14Years',
        3: '15To19Years',
        4: '20To24Years',
        5: '25To29Years',
        6: '30To34Years',
        7: '35To39Years',
        8: '40To44Years',
        9: '45To49Years',
        10: '50To54Years',
        11: '55To59Years',
        12: '60To64Years',
        13: '65To69Years',
        14: '70To74Years',
        15: '75To79Years',
        16: '80To84Years',
        17: '85OrMoreYears'
    }
    df.rename(columns=_dict, inplace=True)
    print(df)
    df = df.melt(id_vars=['Year','geo_ID' ,'Race'], var_name='sv' ,\
       value_name='observation')
    df['SVs'] = 'Count_Person_' + df['sv'] + '_' + df['Race']
    df.drop(columns=['Race', 'sv'], inplace=True)
    df['geo_ID'] = 'geoId/' + df['geo_ID']
    # Making copies of the current DF to be aggregated upon
    final_df = pd.concat([final_df, df])
    df2 = pd.concat([df2, df])
    final_df.insert(3, 'Measurement_Method', 'CensusPEPSurvey', True)
    df['SVs'] = df['SVs'].str.replace('_WhiteAlone', '')
    df['SVs'] = df['SVs'].str.replace('_BlackOrAfricanAmericanAlone', '')
    df['SVs'] = df['SVs'].str.replace('_OtherRaces', '')
    df = df.groupby(['Year', 'geo_ID', 'SVs']).sum().reset_index()
    df.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    df2['SVs'] = df2['SVs'].str.replace('_Male', '')
    df2['SVs'] = df2['SVs'].str.replace('_Female', '')
    df2 = df2.groupby(['Year', 'geo_ID', 'SVs']).sum().reset_index()
    df2.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    final_df = pd.concat([final_df, df2, df])
    final_df = final_df[~final_df.SVs.str.contains('OtherRaces')]
    final_df.to_csv(
        os.path.dirname(os.path.abspath(__file__)) + os.sep +
        'input_data/county_1970_1979.csv')
