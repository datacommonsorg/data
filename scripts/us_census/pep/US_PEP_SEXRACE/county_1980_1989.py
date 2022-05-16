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
from 1980-1989 on a County Level,
cleans it and create a cleaned csv
'''

import json
import pandas as pd

URLS_JSON_PATH = "County/county_1980_1989.json"
URLS_JSON = None
with open(URLS_JSON_PATH, encoding="UTF-8") as file:
    URLS_JSON = json.load(file)
url = URLS_JSON["url"]

# reading the csv input file
df = pd.read_csv(url, skiprows=5)
df = df.drop(index=[0])
df.rename(columns={
    'Year of Estimate': 'Year',
    'Race/Sex Indicator': 'Sex',
    "FIPS State and County Codes": "geo_ID"
},
          inplace=True)
column_names = [
    'Under 5 years', '5 to 9 years', '10 to 14 years', '15 to 19 years',
    '20 to 24 years', '25 to 29 years', '30 to 34 years', '35 to 39 years',
    '40 to 44 years', '45 to 49 years', '50 to 54 years', '55 to 59 years',
    '60 to 64 years', '65 to 69 years', '70 to 74 years', '75 to 79 years',
    '80 to 84 years', '85 years and over'
]
df['Total'] = df[column_names].sum(axis=1)

# providing geoId to the dataframe and making the geoId of 5 digit as county
df['geo_ID'] = df['geo_ID'].astype(int)
df['geo_ID'] = [f'{x:05}' for x in df['geo_ID']]
df['Year'] = df['Year'].astype(str) + "-" + df['geo_ID'].astype(str)
df.drop(columns=['geo_ID'], inplace=True)

# dropping unwanted columns
df = df.drop(columns=[
    'Under 5 years', '5 to 9 years', '10 to 14 years', '15 to 19 years',
    '20 to 24 years', '25 to 29 years', '30 to 34 years', '35 to 39 years',
    '40 to 44 years', '45 to 49 years', '50 to 54 years', '55 to 59 years',
    '60 to 64 years', '65 to 69 years', '70 to 74 years', '75 to 79 years',
    '80 to 84 years', '85 years and over'
])

df = df.groupby(['Year', 'Sex']).sum().transpose().stack(0).reset_index()
df.drop(columns='level_0', inplace=True)

# splitting column into geoId and Year
df['geo_ID'] = df['Year'].str.split('-', expand=True)[1]
df['Year'] = df['Year'].str.split('-', expand=True)[0]

# providing proper column names
df = df.rename(
    columns={
        'White male': 'Count_Person_Male_WhiteAlone',
        'White female': 'Count_Person_Female_WhiteAlone',
        'Black male': 'Count_Person_Male_BlackOrAfricanAmericanAlone',
        'Black female': 'Count_Person_Female_BlackOrAfricanAmericanAlone',
        'Other races male': 'Count_Person_Male_OtherRaces',
        'Other races female': 'Count_Person_Female_OtherRaces'
    })

# aggregating columns to get Count_Person_Male
df["Count_Person_Male"] = df.loc[:, [
    'Count_Person_Male_WhiteAlone',
    "Count_Person_Male_BlackOrAfricanAmericanAlone"
]].sum(axis=1)

# aggregating columns to get Count_Person_Female
df["Count_Person_Female"] = df.loc[:, [
    'Count_Person_Female_WhiteAlone',
    "Count_Person_Female_BlackOrAfricanAmericanAlone"
]].sum(axis=1)

# dropping unwanted columns
df = df.drop(
    columns=['Count_Person_Male_OtherRaces', 'Count_Person_Female_OtherRaces'])
df['geo_ID'] = 'geoId/' + df['geo_ID']

# writing the dataframe to output csv
df.to_csv("county_Result_1980_1989.csv")
