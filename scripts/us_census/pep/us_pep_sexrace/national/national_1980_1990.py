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
"""
This script generate output CSV
for national 1980-1990 and it is aggregated
from state 1980-1990 file.
"""

import pandas as pd
import os

_CODEDIR = os.path.dirname(os.path.realpath(__file__))


def process_national_1980_1990(url: str) -> pd.DataFrame:
    """
    Function Loads input txt datasets
    from 1980-1990 on a National Level,
    cleans it and return cleaned dataframe.

    Args:
        url (str) : url of the dataset

    Returns:
        df.columns (pd.DataFrame) : Coulumn names of cleaned dataframe
    """
    # 0 = Ages 0-4, 1 = Ages 5-9, 2 = Ages 10-14, 3 = Ages 15-19
    # 4 = Ages 20-24, 5 = Ages 25-29, 6 = Ages 30-34, 7 = Ages 35-39
    # 8 = Ages 40-44, 9 = Ages 45-49, 10 = Ages 50-54, 11 = Ages 55-59
    # 12 = Ages 60-64, 13 = Ages 65-69, 14 = Ages 70-74, 15 = Ages 75-79
    # 16 = Ages 80-84, 17 = Ages 85+

    COLUMNS_TO_SUM = list(range(18))
    _cols = ['Info']
    _cols.extend(COLUMNS_TO_SUM)

    # reading the csv input file
    df = pd.read_table(url,
                       index_col=False,
                       delim_whitespace=True,
                       engine='python',
                       names=_cols)

    df['Total'] = df[COLUMNS_TO_SUM].sum(axis=1)

    # extracting year and geoid from Info column
    df['Info'] = [f'{x:05}' for x in df['Info']]
    df['Info'] = df['Info'].astype(str)
    df['Year'] = df['Info'].str[0:2] + "-198" + df['Info'].str[2]

    # extracting sex and race from the Info column
    df['Race'] = df['Info'].str[3]
    df['Sex'] = df['Info'].str[4]
    df = df.replace({'Sex': {'1': 'Male', '2': 'Female'}})
    df = df.replace({
        'Race': {
            '1': 'W',
            '2': 'B',
            '3': 'AI',
            '4': 'AP',
            '5': 'W',
            '6': 'B',
            '7': 'AI',
            '8': 'AP'
        }
    })
    df['SR'] = df['Sex'] + ' ' + df['Race']

    # dropping unwanted columns
    df.drop(columns=COLUMNS_TO_SUM, inplace=True)
    df.drop(columns=['Info', 'Sex', 'Race'], inplace=True)

    # group the df as per columns provided
    df = df.groupby(['Year', 'SR']).sum().transpose().stack(0).reset_index()

    # splitting year and geoId
    df['geo_ID'] = df['Year'].str.split('-', expand=True)[0]
    df['geo_ID'] = 'geoId/' + df['geo_ID']
    df['Year'] = df['Year'].str.split('-', expand=True)[1]

    # dropping unwanted column
    df.drop(columns=['level_0'], inplace=True)

    # providing proper column names
    female_columns = [
        'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone',
        'Count_Person_Female_AsianOrPacificIslander',
        'Count_Person_Female_BlackOrAfricanAmericanAlone',
        'Count_Person_Female_WhiteAlone'
    ]

    male_columns = [
        'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone',
        'Count_Person_Male_AsianOrPacificIslander',
        'Count_Person_Male_BlackOrAfricanAmericanAlone',
        'Count_Person_Male_WhiteAlone'
    ]

    df.columns = ['Year'] + female_columns + male_columns + ['geo_ID']

    # aggregating columns to get Count_Person_Male
    df["Count_Person_Male"] = df[male_columns].sum(axis=1)

    # aggregating columns to get Count_Person_Female
    df["Count_Person_Female"] = df[female_columns].sum(axis=1)

    df.drop(columns=['geo_ID'], inplace=True)

    df = df.groupby(['Year']).sum().reset_index()

    # inserting geoid in columns
    df.insert(0, 'geo_ID', 'country/USA', True)

    df.to_csv(_CODEDIR + "/../output_files/intermediate/" +
              "nationals_result_1980_1990.csv")
    return df.columns
