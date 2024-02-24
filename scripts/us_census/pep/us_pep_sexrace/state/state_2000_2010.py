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
for State 2000-2010 and the file
is processed as is.
"""

import pandas as pd
import os

_CODEDIR = os.path.dirname(os.path.realpath(__file__))


def process_state_2000_2010(url: str) -> pd.DataFrame:
    """
    Function Loads input csv datasets
    from 2000-2010 on a State Level,
    cleans it and return cleaned dataframe.

    Args:
        url (str) : url of the dataset

    Returns:
        df.columns (pd.DataFrame) : Column names of cleaned dataframe
    """
    # reading the csv input file
    df = pd.read_csv(url, header=0)

    # dropping unwanted columns
    df.drop(columns=[
        "REGION", "DIVISION", "ESTIMATESBASE2000", "CENSUS2010POP",
        "POPESTIMATE2010"
    ],
            inplace=True)

    # agegrp = 0 is only required as it gives total of all ages
    df = df.query("AGEGRP == 0")

    # national values are required
    df = df.query("NAME not in ['United States']")

    # origin is not required
    # origin = 0 is values without origin
    df = df.query("ORIGIN == 0")

    # total population is not required
    # sex = 0 is total
    df = df.query("SEX != 0")

    # changing values of column as per the metadata
    df = df.replace({'SEX': {1: 'Male', 2: 'Female'}})
    df = df.replace({
        'RACE': {
            0: 'All_Races_Combined',
            1: 'WhiteAlone',
            2: 'BlackOrAfricanAmericanAlone',
            3: 'AmericanIndianAndAlaskaNativeAlone',
            4: 'AsianAlone',
            5: 'NativeHawaiianAndOtherPacificIslanderAlone',
            6: 'TwoOrMoreRaces'
        }
    })

    df['INFO'] = "Count_Person_" + df['SEX'] + '_' + df['RACE']
    df['INFO'] = df['INFO'].astype(str).str.replace('_All_Races_Combined', '')
    df.drop(columns=["ORIGIN", "AGEGRP", "RACE", "SEX", "NAME"], inplace=True)

    # creating geoId and making them 2 digit as state
    df['STATE'] = [f'{x:02}' for x in df['STATE']]

    # it groups the df as per columns provided
    # performs the provided functions on the data
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
        'Count_Person_Male', 'Count_Person_Male_AmericanIndian'+\
            'AndAlaskaNativeAlone', 'Count_Person_Male_AsianAlone',
        'Count_Person_Male_BlackOrAfricanAmericanAlone',
        'Count_Person_Male_NativeHawaiianAndOtherPacificIslanderAlone',
        'Count_Person_Male_TwoOrMoreRaces', 'Count_Person_Male_WhiteAlone'])

    # providing proper name to geoid column
    df = df.rename(columns={"STATE": "geo_ID"})
    df['geo_ID'] = 'geoId/' + df['geo_ID']

    df.to_csv(_CODEDIR + "/../output_files/intermediate/" +
              "state_result_2000_2010.csv")
    return df.columns
