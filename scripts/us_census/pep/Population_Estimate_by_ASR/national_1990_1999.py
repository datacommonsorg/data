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
1990-1999
'''
import os
import json
import pandas as pd
import numpy as np


def national1990():
    '''
    This Python Script Loads csv datasets
    from 1990-1999 on a National Level,
    cleans it and create a cleaned csv
    '''
    # Load the url in a variable
    _URLS_JSON_PATH = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "national.json"
    _URLS_JSON = None
    with open(_URLS_JSON_PATH, encoding="UTF-8") as file:
        _URLS_JSON = json.load(file)
    _url = _URLS_JSON["1990-99"]
    # Defining dummy column names for importing the data
    cols = ["0", "1", "2", "3", "4", "5", "6", "7",\
            "8", "9", "10", "11","12", "13", "14", "15",\
            "16", "17", "18", "19", "20", "21", "22", "23"]
    df = pd.read_table(_url,
                       index_col=False,
                       delim_whitespace=True,
                       engine='python',
                       names=cols)
    # Filtering the data required
    df = df.loc[df['0'].isin(['2I', '9P'])]
    df['1'] = df['1'].astype(str)
    df1 = df[df['1'].str.contains("100")]
    df = df[df['1'].str.len() <= 5]
    for i in range(22, 1, -1):
        j = i + 1
        i = str(i)
        j = str(j)
        df1[j] = df1[i]
        i = int(i)
    df1['2'] = df1['1'].str[-3:]
    df1['1'] = df1['1'].str[:-3]
    df = pd.concat([df, df1])
    mask = df['1'].str[0] == '7'
    df = df.loc[mask]
    # Defining Columns based on the Dummy Column Names
    df['Year'] = df['1'].str[1:5]
    df['Age'] = df['2'].astype(float).astype(int)
    df['Male'] = df['4']
    df['Female'] = df['5']
    df['WhiteAggrAll'] = df['6'] + df['7']
    df['Male_WhiteAll'] = df['6']
    df['Female_WhiteAll'] = df['7']
    df['BlackOrAfricanAmericanAggrAll'] = df['8'] + df['9']
    df['Male_BlackOrAfricanAmericanAll'] = df['8']
    df['Female_BlackOrAfricanAmericanAll'] = df['9']
    df['AmericanIndianAndAlaskaNativeAggrAll'] = df['10'] + df['11']
    df['Male_AmericanIndianAndAlaskaNativeAll'] = df['10']
    df['Female_AmericanIndianAndAlaskaNativeAll'] = df['11']
    df['AsianOrPacificIslanderAggr'] = df['12'] + df['13']
    df['Male_AsianOrPacificIslander'] = df['12']
    df['Female_AsianOrPacificIslander'] = df['13']
    df = df.drop([
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
        "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23"
    ],
                 axis=1)
    df.columns = df.columns.str.replace('All', \
        'Alone')
    df = df.melt(id_vars=['Year', 'Age'],
                 var_name='SVs',
                 value_name='observation')
    df['Age'] = df['Age'].astype(str)
    df['Age'] = df['Age'] + 'Years'
    df['SVs'] = 'Count_Person_' + df['Age'] + '_' + df['SVs']
    df.drop(columns=['Age'], inplace=True)
    # Adding the column Measurement method based on a condition
    df['Measurement_Method'] = np.where(df['SVs'].str.contains("Aggr"), \
        'dcAggregate/CensusPEPSurvey', 'CensusPEPSurvey')
    df['SVs'] = df['SVs'].str.replace('Aggr', '')
    df['geo_ID'] = 'country/USA'
    df.to_csv(os.path.dirname(os.path.abspath(__file__)) + os.sep +\
        'input_data/national_1990_1999.csv')
