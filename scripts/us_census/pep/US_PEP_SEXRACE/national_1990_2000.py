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
from 1990-2000 on a National Level,
cleans it and create a cleaned csv
'''

import json
import pandas as pd

# Load the url in a variable
URLS_JSON_PATH = "Nationals/national_1990_2000.json"
URLS_JSON = None
with open(URLS_JSON_PATH, encoding="UTF-8") as file:
    URLS_JSON = json.load(file)
url = URLS_JSON["url"]

cols = [
    'Series', 'Info', 'TP', 'TMP', 'TFP', 'WM', 'WF', 'BM', 'BF', 'AIM', 'AIF',
    'APM', 'APF'
]

# reading the txt format input file, delimitng the columns by whitespace
df = pd.read_table(url,
                   index_col=False,
                   delim_whitespace=True,
                   engine='python',
                   names=cols)

df['Info'] = df['Info'].astype(str)
mask = df['Info'].str.len() >= 6
df = df.loc[mask]

# to get only july month estitmates of every year
mask = df['Info'].str[0] == '7'
df = df.loc[mask]

# to only get the row having total value of all the ages
# which is present in "999" year in dataset
mask = df['Info'].str[-3:] == '999'
df = df.loc[mask]

# Extracting year from column value
df['Year'] = df['Info'].str[1:5]

# dropping the unwanted columns
df.drop(columns=['Series', 'Info', 'TP'], inplace=True)

# providing column names
df.columns=["Count_Person_Male","Count_Person_Female",
    "Count_Person_Male_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces",
    "Count_Person_Female_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces",
    "Count_Person_Male_BlackOrAfricanAmericanAlone"+\
    "OrInCombinationWithOneOrMoreOtherRaces",
    "Count_Person_Female_BlackOrAfricanAmericanAlone"+\
    "OrInCombinationWithOneOrMoreOtherRaces",
    "Count_Person_Male_AmericanIndianAndAlaskaNativeAlone"+\
    "OrInCombinationWithOneOrMoreOtherRaces",
    "Count_Person_Female_AmericanIndianAndAlaskaNativeAlone"+\
    "OrInCombinationWithOneOrMoreOtherRaces",
    "Count_Person_Male_AsianOrPacificIslander",
    "Count_Person_Female_AsianOrPacificIslander","Year"]

# inserting geoId to the dataframe
df.insert(1, 'geo_ID', 'country/USA', True)

# writing the dataframe to output csv
df.to_csv("nationals_result_1990_2000.csv")
