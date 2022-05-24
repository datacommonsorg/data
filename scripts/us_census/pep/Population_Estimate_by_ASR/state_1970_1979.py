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
for State Level Data
1970-1979
'''
import os
import json
import pandas as pd


def state1970():
    '''
      This Python Script Loads csv datasets
      from 1970-1979 on a State Level,
      cleans it and create a cleaned csv
      '''
    _URLS_JSON_PATH = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "state.json"
    _URLS_JSON = None
    with open(_URLS_JSON_PATH, encoding="UTF-8") as file:
        _URLS_JSON = json.load(file)
    _url = _URLS_JSON["1970-79"]
    df = pd.read_csv(_url, skiprows=5, encoding='ISO-8859-1')
    df.insert(1, 'geo_ID', 'geoId/', True)
    df['geo_ID'] = 'geoId/' + (df['FIPS State Code'].map(str)).str.zfill(2)
    # Dropping the old unwanted columns
    df.drop(columns=['State Name', 'FIPS State Code'], inplace=True)
    df.rename(columns=\
       {'Year of Estimate': 'Year','Race/Sex Indicator': 'Race/Sex'},\
          inplace=True)

    df['Race/Sex'] = df['Race/Sex'].astype(str)
    _dict = {
        'White male': 'Male_WhiteAlone',
        'White female': 'Female_WhiteAlone',
        'Black male': 'Male_BlackOrAfricanAmericanAlone',
        'Black female': 'Female_BlackOrAfricanAmericanAlone',
        'Other races male': 'Male_OtherRaces',
        'Other races female': 'Female_OtherRaces'
    }
    df = df.replace({"Race/Sex": _dict})
    df = df.melt(id_vars=['Year','geo_ID' ,'Race/Sex'], var_name='Age' ,\
       value_name='observation')
    df['Age'] = df['Age'].astype(str)
    # Making Age groups as per SV Naming Convention
    _dict = {
        'Under 5 years': '0To4Years',
        '5 to 9 years': '5To9Years',
        '10 to 14 years': '10To14Years',
        '15 to 19 years': '15To19Years',
        '20 to 24 years': '20To24Years',
        '25 to 29 years': '25To29Years',
        '30 to 34 years': '30To34Years',
        '35 to 39 years': '35To39Years',
        '40 to 44 years': '40To44Years',
        '45 to 49 years': '45To49Years',
        '50 to 54 years': '50To54Years',
        '55 to 59 years': '55To59Years',
        '60 to 64 years': '60To64Years',
        '65 to 69 years': '65To69Years',
        '70 to 74 years': '70To74Years',
        '75 to 79 years': '75To79Years',
        '80 to 84 years': '80To84Years',
        '85 years and over': '85OrMoreYears'
    }
    df = df.replace({"Age": _dict})
    df['SVs'] = 'Count_Person_' + df['Age'] + '_' + df['Race/Sex']
    df = df.drop(columns=['Age', 'Race/Sex'])
    df['observation'] = df['observation'].str.replace(",", "").astype(int)
    # Making Copies of current DF and using Group by on them
    # to get Aggregated Values
    final_df = pd.DataFrame()
    df2 = pd.DataFrame()
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
        'input_data/state_1970_1979.csv')
