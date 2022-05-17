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
This Python Script Loads csv datasets
from 2010-2020 on a National Level,
cleans it and create a cleaned csv
'''
import json
import pandas as pd

URLS_JSON_PATH = "Nationals/national_2010_2020.json"
URLS_JSON = None
with open(URLS_JSON_PATH, encoding="UTF-8") as file:
    URLS_JSON = json.load(file)
url = URLS_JSON["url"]

# reading the csv format input file and converting it to a dataframe
# skipping unwanted rows from top
df = pd.read_excel(url, skiprows=3, header=0)

# dropping the unwanted rows and column
df = df.drop(['Census', 'Estimates Base', 2010], axis=1)
df = df.drop([1], axis=0)
df['Unnamed: 0'] = df['Unnamed: 0'].str.replace(".", "")
df1 = df[0:6]
df2 = df[8:13]
df2['Unnamed: 0'] = df2['Unnamed: 0'] + ' Alone Or In Combination'
df_final = pd.concat([df1, df2])
df1 = df[41:48]
df1['Unnamed: 0'] = 'Male ' + df1['Unnamed: 0']
df2 = df[50:55]
df2['Unnamed: 0'] = 'Male ' + df2['Unnamed: 0'] + ' Alone Or In Combination'
df_final = pd.concat([df_final, df1, df2])
df1 = df[83:90]
df1['Unnamed: 0'] = 'Female ' + df1['Unnamed: 0']
df2 = df[92:97]
df2['Unnamed: 0'] = 'Female ' + df2['Unnamed: 0'] + ' Alone Or In Combination'
df_final = pd.concat([df_final, df1, df2])
df = df_final.transpose()
df.columns = df.iloc[0]

df = df[1:]

# dropping unwanted columns
df.drop(columns=[
    'TOTAL POPULATION', 'White', 'Black or African American',
    'American Indian and Alaska Native', 'Asian',
    'Native Hawaiian and Other Pacific Islander',
    'White Alone Or In Combination',
    'Black or African American Alone Or In Combination',
    'American Indian and Alaska Native Alone Or In Combination',
    'Asian Alone Or In Combination',
    'Native Hawaiian and Other Pacific Islander Alone Or In Combination',
    'Female One Race:', 'Male One Race:'
],
        inplace=True)
df['Year'] = df.index

# giving proper name to the columns
df.columns=['Count_Person_Male','Count_Person_Male_WhiteAlone',
       'Count_Person_Male_BlackOrAfricanAmericanAlone',
       'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone',
       'Count_Person_Male_AsianAlone',
       'Count_Person_Male_NativeHawaiianAndOtherPacificIslanderAlone',
       'Count_Person_Male_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
       'Count_Person_Male_BlackOrAfricanAmericanAlone'+\
       'OrInCombinationWithOneOrMoreOtherRaces',
       'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone'+\
       'OrInCombinationWithOneOrMoreOtherRaces',
       'Count_Person_Male_AsianAlone'+\
       'OrInCombinationWithOneOrMoreOtherRaces',
       'Count_Person_Male_NativeHawaiianAndOtherPacificIslanderAlone'+\
       'OrInCombinationWithOneOrMoreOtherRaces',
       'Count_Person_Female','Count_Person_Female_WhiteAlone',
       'Count_Person_Female_BlackOrAfricanAmericanAlone',
       'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone',
       'Count_Person_Female_AsianAlone',
       'Count_Person_Female_NativeHawaiianAndOtherPacificIslanderAlone',
       'Count_Person_Female_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
       'Count_Person_Female_BlackOrAfricanAmericanAlone'+\
       'OrInCombinationWithOneOrMoreOtherRaces',
       'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone'+\
       'OrInCombinationWithOneOrMoreOtherRaces',
       'Count_Person_Female_AsianAloneOrInCombinationWithOneOrMoreOtherRaces',
       'Count_Person_Female_NativeHawaiianAndOtherPacificIslanderAlone'+\
       'OrInCombinationWithOneOrMoreOtherRaces','Year']

df = df.reset_index()
df = df.drop(columns=['index'])
df.insert(0, 'geo_ID', 'country/USA', True)

# writing the dataframe to output csv
df.to_csv("nationals_result_2010_2020.csv")
