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
This Python Script Loads every year csv datasets
from 1990-2000 on a State Level,
cleans it and create a cleaned csv
'''

import json
import pandas as pd

URLS_JSON_PATH = "State/state_1990_2000.json"
URLS_JSON = None
with open(URLS_JSON_PATH, encoding="UTF-8") as file:
    URLS_JSON = json.load(file)
urls = URLS_JSON["urls"]

final_df = pd.DataFrame()
for url in urls:
    # reading the csv input file
    df = pd.read_table(url,
                       skiprows=15,
                       header=None,
                       delim_whitespace=True,
                       index_col=False,
                       engine='python')
    df.columns = [
        'Year', 'geo_ID', 'Age', 'NHWM', 'NHWF', 'NHBM', 'NHBF', 'NHAIANM',
        'NHAIANF', 'NHAPIM', 'NHAPIF', 'HWM', 'HWF', 'HBM', 'HBF', 'HAIANM',
        'HAIANF', 'HAPIM', 'HAPIF'
    ]

    # adding columns to get proper values
    df['Count_Person_Male_WhiteAloneOrInCombination'+\
        'WithOneOrMoreOtherRaces']=df["NHWM"]+df["HWM"]
    df['Count_Person_Female_WhiteAloneOrInCombination'+\
        'WithOneOrMoreOtherRaces']=df["NHWF"]+df["HWF"]
    df['Count_Person_Male_BlackOrAfricanAmericanAloneOrInCombination'+\
        'WithOneOrMoreOtherRaces']=df["NHBM"]+df["HBM"]
    df['Count_Person_Female_BlackOrAfricanAmericanAloneOrInCombination'+\
        'WithOneOrMoreOtherRaces']=df["NHBF"]+df["HBF"]
    df['Count_Person_Male_AmericanIndianAndAlaskaNativeAloneOrInCombination'+\
        'WithOneOrMoreOtherRaces']=df["NHAIANM"]+df["HAIANM"]
    df['Count_Person_Female_AmericanIndianAndAlaskaNativeAlone'+\
        'OrInCombinationWithOneOrMoreOtherRaces']=df["NHAIANF"]+df["HAIANF"]
    df['Count_Person_Male_AsianOrPacificIslander'] = df["NHAPIM"] + df["HAPIM"]
    df['Count_Person_Female_AsianOrPacificIslander']\
         = df["NHAPIF"] + df["HAPIF"]

    # dropping unwanted columns
    df.drop(columns=[
        'Age', 'NHWM', 'NHWF', 'NHBM', 'NHBF', 'NHAIANM', 'NHAIANF', 'NHAPIM',
        'NHAPIF', 'HWM', 'HWF', 'HBM', 'HBF', 'HAIANM', 'HAIANF', 'HAPIM',
        'HAPIF'
    ],
            inplace=True)

    # providing geoId to the dataframe and making the geoId of 2 digit as state
    df['geo_ID'] = [f'{x:02}' for x in df['geo_ID']]
    df['geo_ID'] = 'geoId/' + df['geo_ID']
    df = df.groupby(['Year', 'geo_ID']).agg('sum').reset_index()
    final_df = pd.concat([final_df, df])

# aggregating columns to get Count_Person_Male
final_df["Count_Person_Male"] = final_df.loc[:,['Count_Person_Male_WhiteAlone'+\
        'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Male_BlackOrAfricanAmericanAlone'+\
        'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone'+\
        'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Male_AsianOrPacificIslander']].sum(axis=1)

# aggregating columns to get Count_Person_Female
final_df["Count_Person_Female"] = final_df.loc[:,
    ['Count_Person_Female_WhiteAlone'+\
        'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Female_BlackOrAfricanAmericanAlone'+\
        'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone'+\
            'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Female_AsianOrPacificIslander']].sum(axis=1)

# writing the dataframe to output csv
final_df.to_csv("state_result_1990_2000.csv")
