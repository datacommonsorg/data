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
from 2000-2010 on a State Level,
cleans it and create a cleaned csv
'''

import json
import pandas as pd

URLS_JSON_PATH = "State/state_2000_2010.json"
URLS_JSON = None
with open(URLS_JSON_PATH, encoding="UTF-8") as file:
    URLS_JSON = json.load(file)
url = URLS_JSON["url"]

# reading the csv input file
df = pd.read_csv(url, header=0)

# dropping unwanted columns
df.drop(columns=[
    "REGION", "DIVISION", "ESTIMATESBASE2000", "CENSUS2010POP",
    "POPESTIMATE2010"
],
        inplace=True)

# agegrp is only required as it gives total of all ages
df = df.query("AGEGRP == 0")

# state values are required
df = df.query("NAME not in ['United States']")

# origin not required
df = df.query("ORIGIN == 0")

# total population not required
df = df.query("SEX !=0")

# changing values of column as per the metadata
df['SEX'] = df['SEX'].astype(str).str.replace('1', 'Male')
df['SEX'] = df['SEX'].astype(str).str.replace('2', 'Female')

df['RACE'] = df['RACE'].astype(str).str.replace('0', 'All_Races_Combined')
df['RACE'] = df['RACE'].astype(str).str.replace('1', 'WhiteAlone')
df['RACE'] = df['RACE'].astype(str).str.replace('2',\
       'BlackOrAfricanAmericanAlone')
df['RACE'] = df['RACE'].astype(str).str.replace('3',\
       'AmericanIndianAndAlaskaNativeAlone')
df['RACE'] = df['RACE'].astype(str).str.replace('4', 'AsianAlone')
df['RACE'] = df['RACE'].astype(str).str.replace('5',\
       'NativeHawaiianAndOtherPacificIslanderAlone')
df['RACE'] = df['RACE'].astype(str).str.replace('6', 'TwoOrMoreRaces')

df['INFO'] = "Count_Person_" + df['SEX'] + '_' + df['RACE']
df['INFO'] = df['INFO'].astype(str).str.replace('_All_Races_Combined', '')
df.drop(columns=["ORIGIN", "AGEGRP", "RACE", "SEX", "NAME"], inplace=True)

# creating geoId and making them 2 digit as state
df['STATE'] = [f'{x:02}' for x in df['STATE']]
df = df.groupby(['STATE', 'INFO']).sum().transpose().stack(0).reset_index()

# to extract year from level_0 column which is the last 4 char
df['Year'] = df['level_0'].str[-4:]
df.drop(columns=["level_0"], inplace=True)
df = df.reindex(columns=[
    'Year', 'STATE', 'Count_Person_Female',
    'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone',
    'Count_Person_Female_AsianAlone',
    'Count_Person_Female_BlackOrAfricanAmericanAlone',
    'Count_Person_Female_NativeHawaiianAndOtherPacificIslanderAlone',
    'Count_Person_Female_TwoOrMoreRaces', 'Count_Person_Female_WhiteAlone',
    'Count_Person_Male', 'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone',
    'Count_Person_Male_AsianAlone',
    'Count_Person_Male_BlackOrAfricanAmericanAlone',
    'Count_Person_Male_NativeHawaiianAndOtherPacificIslanderAlone',
    'Count_Person_Male_TwoOrMoreRaces', 'Count_Person_Male_WhiteAlone'
])
df = df.rename(columns={"STATE": "geo_ID"})
df['geo_ID'] = 'geoId/' + df['geo_ID']

# writing the dataframe to output csv
df.to_csv("state_result_2000_2010.csv")
