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
from 1980-1990 on a State Level,
cleans it and create a cleaned csv
'''

import json
import pandas as pd

URLS_JSON_PATH = "State/state_1980_1990.json"
URLS_JSON = None
with open(URLS_JSON_PATH, encoding="UTF-8") as file:
    URLS_JSON = json.load(file)
url = URLS_JSON["url"]

cols = ['Info', 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]

# reading the csv input file
df = pd.read_table(url,
                   index_col=False,
                   delim_whitespace=True,
                   engine='python',
                   names=cols)
df['Total']=df[0]+df[1]+df[2]+df[3]+df[4]+df[5]+df[6]\
    +df[7]+df[8]+df[9]+df[10]+df[11]+df[12]+df[13]+df[14]\
    +df[15]+df[16]+df[17]

# dropping unwanted columns
df.drop(columns=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
        inplace=True)

df['Info'] = [f'{x:05}' for x in df['Info']]
df['Info'] = df['Info'].astype(str)
df['Year'] = df['Info'].str[0:2] + "-198" + df['Info'].str[2]
df['Race'] = df['Info'].str[3]
df['Sex'] = df['Info'].str[4]
df['Sex'] = df['Sex'].str.replace('1', 'Male')
df['Sex'] = df['Sex'].str.replace('2', 'Female')
df['Race'] = df['Race'].str.replace('1', 'W')
df['Race'] = df['Race'].str.replace('2', 'B')
df['Race'] = df['Race'].str.replace('3', 'AI')
df['Race'] = df['Race'].str.replace('4', 'AP')
df['Race'] = df['Race'].str.replace('5', 'W')
df['Race'] = df['Race'].str.replace('6', 'B')
df['Race'] = df['Race'].str.replace('7', 'AI')
df['Race'] = df['Race'].str.replace('8', 'AP')
df['SR'] = df['Sex'] + ' ' + df['Race']
df.drop(columns=['Info', 'Sex', 'Race'], inplace=True)
df = df.groupby(['Year','SR']).sum()\
    .transpose().stack(0).reset_index()

# splitting year and geoId
df['geo_ID'] = df['Year'].str.split('-', expand=True)[0]
df['geo_ID'] = 'geoId/' + df['geo_ID']
df['Year'] = df['Year'].str.split('-', expand=True)[1]

# dropping unwanted column
df.drop(columns=['level_0'], inplace=True)

# providing proper column names
df.columns=['Year',
    'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone'+\
    'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Female_AsianOrPacificIslander',
    'Count_Person_Female_BlackOrAfricanAmericanAlone'+\
    'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Female_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone'+\
    'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Male_AsianOrPacificIslander',
    'Count_Person_Male_BlackOrAfricanAmericanAlone'+\
    'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Male_WhiteAlone'+\
    'OrInCombinationWithOneOrMoreOtherRaces','geo_ID']

# aggregating columns to get Count_Person_Male
df["Count_Person_Male"] = df.loc[:,['Count_Person_Male_'+\
    'AmericanIndianAndAlaskaNativeAlone'
    'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Male_AsianOrPacificIslander',
    'Count_Person_Male_BlackOrAfricanAmericanAlone'+\
    'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Male_WhiteAloneOrInCombination'+\
    'WithOneOrMoreOtherRaces']].sum(axis=1)

# aggregating columns to get Count_Person_Female
df["Count_Person_Female"] = df.loc[:,['Count_Person_Female_'+\
    'AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Female_AsianOrPacificIslander',
    'Count_Person_Female_BlackOrAfricanAmericanAlone'+\
    'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Female_WhiteAlone'+\
    'OrInCombinationWithOneOrMoreOtherRaces']].sum(axis=1)

# writing the dataframe to output csv
df.to_csv("state_result_1980_1990.csv")
