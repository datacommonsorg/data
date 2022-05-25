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
for National Level Data
2010-2019
'''
import os
import json
import pandas as pd


def national2010():
    '''
    This Python Script Loads csv datasets
    from 2010-2019 on a National Level,
    cleans it and create a cleaned csv
    '''
    # Getting input URL from the JSON file
    _URLS_JSON_PATH = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "national.json"
    _URLS_JSON = None
    with open(_URLS_JSON_PATH, encoding="UTF-8") as file:
        _URLS_JSON = json.load(file)
    _urls = _URLS_JSON["2010-19"]
    _sheets = _URLS_JSON["2010-19sheets"]
    df_final = pd.DataFrame()
    for sheet in _sheets:
        df_sheet = pd.DataFrame()
        df = pd.read_excel(_urls, sheet, skiprows=4, header=0)
        # Dropping extra columns
        df = df.drop(['Census', 'Estimates Base'], axis=1)
        df = df.drop([0], axis=0)
        # Cleaning the data to
        df['Unnamed: 0'] = df['Unnamed: 0'].str.replace(".", "").str.replace\
            ("Under 5", "0 to 4").str.replace(" ", "").str.replace("to", "To")\
            .str.replace("years", "Years").str.replace("85Yearsandover", \
            "85OrMoreYears")
        # Filtering and reading the data
        if sheet != 'Total':
            df1 = df[0:18]
            df_sheet = pd.concat([df_sheet, df1])
        df1 = df[36:54]
        df1['Unnamed: 0'] = df1['Unnamed: 0'] + '_Male'
        df_sheet = pd.concat([df_sheet, df1])
        df1 = df[72:90]
        df1['Unnamed: 0'] = df1['Unnamed: 0'] + '_Female'
        df_sheet = pd.concat([df_sheet, df1])
        df_sheet['Unnamed: 0'] = df_sheet['Unnamed: 0'] + '_' + sheet + 'Alone'
        df_sheet = df_sheet.melt(id_vars=['Unnamed: 0'],
                                 var_name='Year',
                                 value_name='observation')
        df_sheet.columns = df_sheet.columns.str.replace('Unnamed: 0', 'SVs')
        df_final = pd.concat([df_final, df_sheet])
    df_final['SVs'] = df_final['SVs'].str.replace("_TotalAlone", "")\
        .str.replace("Black", "BlackOrAfricanAmerican").str.replace\
        ("AIAN", "AmericanIndianAndAlaskaNative").str.replace\
        ("NHPI", "NativeHawaiianAndOtherPacificIslander").str.replace\
        ("Two or More RacesAlone", "TwoOrMoreRaces")
    df_final['SVs'] = 'Count_Person_' + df_final['SVs']
    df_final['Measurement_Method'] = 'CensusPEPSurvey'
    df_final['geo_ID'] = 'country/USA'
    df_temp = pd.DataFrame()
    # Making copies of DF to be aggregated upon
    df_temp = pd.concat([df_temp, df_final])
    df_temp['SVs'] = df_temp['SVs'].str.replace('_Male', '')
    df_temp['SVs'] = df_temp['SVs'].str.replace('_Female', '')
    df_temp = df_temp.groupby(['Year', 'geo_ID', 'SVs']).sum().reset_index()
    df_temp.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    df_temp = df_temp[df_temp.SVs.str.contains('Years_')]
    df_final = pd.concat([df_temp, df_final])
    df_final.to_csv(
        os.path.dirname(os.path.abspath(__file__)) + os.sep +
        'input_data/national_2010_2019.csv')
