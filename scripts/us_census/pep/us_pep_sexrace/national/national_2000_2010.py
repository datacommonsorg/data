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
for national 2000-2009 and the file
is processed as is.
"""

import pandas as pd
import os

_CODEDIR = os.path.dirname(os.path.realpath(__file__))


def process_national_2000_2010(url: str) -> pd.DataFrame:
    """
    Function Loads input csv datasets
    from 2000-2009 on a National Level,
    cleans it and return cleaned dataframe.

    Args:
        url (str) : url of the dataset

    Returns:
        df.columns (pd.DataFrame) : Column names of cleaned dataframe
    """
    # reading the csv format input file and converting it to a dataframe
    # skipping unwanted rows from top and bottom
    # removing commas from the row values
    df = pd.read_csv(url, skiprows=3, skipfooter=8, header=0, thousands=',')

    df.rename(columns={
        'Unnamed: 0': 'SRH',
        'Unnamed: 13': '2010'
    },
              inplace=True)

    # dropping unwanted columns
    df.drop(['Unnamed: 1', 'Unnamed: 12'], axis=1, inplace=True)

    sex = ''
    race = ''
    hispanic = ''

    # providing column names
    for i in range(len(df)):
        if df.loc[i, 'SRH'].replace('.',
                                    '') in ['BOTH SEXES', 'MALE', 'FEMALE']:
            df.loc[i,'SRH'] = str(df.loc[i, 'SRH'])\
            .title().replace(' ','').replace('.','')
            sex = df.loc[i, 'SRH'].replace('.', '')
            race = ''
            hispanic = ''
        elif df.loc[i, 'SRH'].replace('.', '') in \
                ['One Race:', 'Race Alone or in Combination:1']:
            df.loc[i,'SRH'] = str(df.loc[i, 'SRH'])\
                .title().replace(' ','').replace('.','')
            race = df.loc[i, 'SRH'].replace('.', '')
        elif df.loc[i, 'SRH'].replace('.', '') in ['NOT HISPANIC', 'HISPANIC']:
            df.loc[i,'SRH'] = str(df.loc[i, 'SRH'])\
                .title().replace(' ','').replace('.','')
            hispanic = df.loc[i, 'SRH'].replace('.', '')
        else:
            df.loc[i,'SRH'] = (str(df.loc[i, 'SRH'])\
                .title().replace(' ','').replace('.','')
                + '_' + race.replace(':1','').replace(':', '')
                + '_' + hispanic
                + '_' + sex).replace('__','_')

    # renaming column to year
    df = df.rename(columns={"SRH": "Year"})

    df = df.transpose()
    new_header = df.iloc[0]
    df = df[1:]
    df.columns = new_header

    # inserting geoId to the dataframe
    df.insert(0, 'LOCATION', 'country/USA', True)

    # dropping unwanted columns
    df.drop(columns=[
        'LOCATION', 'OneRace__BothSexes', 'White__BothSexes',
        'Black__BothSexes', 'Aian__BothSexes', 'Asian__BothSexes',
        'Nhpi__BothSexes', 'TwoOrMoreRaces__BothSexes', 'NotHispanic',
        'OneRace_NotHispanic_BothSexes', 'White_NotHispanic_BothSexes',
        'Black_NotHispanic_BothSexes', 'Aian_NotHispanic_BothSexes',
        'Asian_NotHispanic_BothSexes', 'Nhpi_NotHispanic_BothSexes',
        'TwoOrMoreRaces_NotHispanic_BothSexes', 'Hispanic',
        'OneRace_Hispanic_BothSexes', 'White_Hispanic_BothSexes',
        'Black_Hispanic_BothSexes', 'Aian_Hispanic_BothSexes',
        'Asian_Hispanic_BothSexes', 'Nhpi_Hispanic_BothSexes',
        'TwoOrMoreRaces_Hispanic_BothSexes', 'OneRace__Male', 'NotHispanic',
        'OneRace_NotHispanic_Male', 'White_NotHispanic_Male',
        'Black_NotHispanic_Male', 'Aian_NotHispanic_Male',
        'Asian_NotHispanic_Male', 'Nhpi_NotHispanic_Male',
        'TwoOrMoreRaces_NotHispanic_Male', 'Hispanic', 'OneRace_Hispanic_Male',
        'White_Hispanic_Male', 'Black_Hispanic_Male', 'Aian_Hispanic_Male',
        'Asian_Hispanic_Male', 'Nhpi_Hispanic_Male',
        'TwoOrMoreRaces_Hispanic_Male', 'OneRace__Female', 'NotHispanic',
        'OneRace_NotHispanic_Female', 'White_NotHispanic_Female',
        'Black_NotHispanic_Female', 'Aian_NotHispanic_Female',
        'Asian_NotHispanic_Female', 'Nhpi_NotHispanic_Female',
        'TwoOrMoreRaces_NotHispanic_Female', 'Hispanic',
        'OneRace_Hispanic_Female', 'White_Hispanic_Female',
        'Black_Hispanic_Female', 'Aian_Hispanic_Female',
        'Asian_Hispanic_Female', 'Nhpi_Hispanic_Female',
        'TwoOrMoreRaces_Hispanic_Female'
    ],
            inplace=True)

    df['Year'] = df.index

    # giving proper column names
    df.columns = [
        "BothSexes", "Count_Person_Male", "Count_Person_Male_WhiteAlone",
        "Count_Person_Male_BlackOrAfricanAmericanAlone",
        "Count_Person_Male_AmericanIndianAndAlaskaNativeAlone",
        "Count_Person_Male_AsianAlone",
        "Count_Person_Male_NativeHawaiianAndOtherPacificIslanderAlone",
        "Count_Person_Male_TwoOrMoreRaces", "Count_Person_Female",
        "Count_Person_Female_WhiteAlone",
        "Count_Person_Female_BlackOrAfricanAmericanAlone",
        "Count_Person_Female_AmericanIndianAndAlaskaNativeAlone",
        "Count_Person_Female_AsianAlone",
        "Count_Person_Female_NativeHawaiianAndOtherPacificIslanderAlone",
        "Count_Person_Female_TwoOrMoreRaces", "Year"
    ]

    df.insert(0, 'geo_ID', 'country/USA', True)
    df = df.reset_index()

    # dropping unwanted columns
    df = df.drop(columns=['index', 'BothSexes'])

    df.drop(df[df['Year'] == "2010"].index, inplace=True)

    df.to_csv(_CODEDIR + "/../output_files/intermediate/" +
              "nationals_result_2000_2010.csv")
    return df.columns
