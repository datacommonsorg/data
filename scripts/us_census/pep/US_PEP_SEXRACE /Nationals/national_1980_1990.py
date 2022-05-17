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
This Python Script Loads each year csv datasets
from 1980-1990 on a National Level,
cleans it and create a cleaned csv
'''
import json
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
import pandas as pd

URLS_JSON_PATH = "Nationals/national_1980_1990.json"
URLS_JSON = None
with open(URLS_JSON_PATH, encoding="UTF-8") as file:
    URLS_JSON = json.load(file)
urls = URLS_JSON["urls"]

for url in urls:
    with urlopen(url) as resp:
        # unzipping the dataset
        with ZipFile(BytesIO(resp.read()), 'r') as zipfile:
            zipfile.extractall()

files = URLS_JSON["files"]

cols = ["0", "1", "2", "3", "4", "5", "6", "7",\
                    "8", "9", "10", "11","12", "13", "14", "15",\
                    "16", "17", "18", "19", "20", "21", "22"]

final_df = pd.DataFrame()

for file in files:

    # reading the txt format input file converting it to a dataframe
    # delimitng the columns by whitespace
    df = pd.read_table(file,
                       index_col=False,
                       delim_whitespace=True,
                       engine='python',
                       names=cols)
    df['1'] = df['1'].astype(str)

    # to only get the row having total value of all the ages
    # which is present in "999" year in dataset
    df = df[df['1'].str.contains("999")]

    # to get only july month estitmates of every year
    mask = df['1'].str[0] == '7'
    df = df.loc[mask]

    # creating proper year value
    df['Year'] = "19" + df['1'].str[1:3]

    df['Total'] = df['2']
    df['Male White'] = df['5']
    df['Female White'] = df['6']
    df['Male Black'] = df['7']
    df['Female Black'] = df['8']
    df['Male American Indian & Alaska Native'] = df['9']
    df['Female American Indian & Alaska Native'] = df['10']
    df['Male Asian & Pacific Islander'] = df['11']
    df['Female Asian & Pacific Islander'] = df['12']

    # dropping unwanted columns
    df = df.drop([
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
        "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", 'Total'
    ],
                 axis=1)

    # writing all the output to a final dataframe
    final_df = pd.concat([final_df, df])

# giving proper column names
final_df.columns=["Year",
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
    "Count_Person_Female_AsianOrPacificIslander"]

# aggregating columns to get Count_Person_Male
final_df["Count_Person_Male"] = final_df.loc[:,["Count_Person_Male_"+\
    "WhiteAloneOrInCombinationWithOneOrMoreOtherRaces",
    "Count_Person_Male_BlackOrAfricanAmericanAlone"+\
    "OrInCombinationWithOneOrMoreOtherRaces",
    "Count_Person_Male_AmericanIndianAndAlaskaNativeAlone"+\
    "OrInCombinationWithOneOrMoreOtherRaces",
    "Count_Person_Male_AsianOrPacificIslander"]].sum(axis=1)

# aggregating columns to get Count_Person_Female
final_df["Count_Person_Female"] = final_df.loc[:,['Count_Person_'+\
    'Female_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
    "Count_Person_Female_BlackOrAfricanAmericanAlone"+\
    "OrInCombinationWithOneOrMoreOtherRaces",
    "Count_Person_Female_AmericanIndianAndAlaskaNativeAlone"+\
    "OrInCombinationWithOneOrMoreOtherRaces",
    "Count_Person_Female_AsianOrPacificIslander"]].sum(axis=1)

# inserting geoId to the final dataframe
final_df.insert(1, 'geo_ID', 'country/USA', True)

# writing the final dataframe to output csv
final_df.to_csv('nationals_result_1980_1990.csv')
