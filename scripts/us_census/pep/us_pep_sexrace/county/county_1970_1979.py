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
for county 1970-1979 and Count_Person_Male
and Count_person_Female are aggregated for this file.
"""

import pandas as pd
import os

_CODEDIR = os.path.dirname(os.path.realpath(__file__))


def process_county_1970_1979(url: str) -> pd.DataFrame:
    """
    Function Loads input csv datasets
    from 1970-1979 on a County Level,
    cleans it and return cleaned dataframe.

    Args:
        url (str) : url of the dataset

    Returns:
        df.columns (pd.dataframe) : Column names of cleaned dataframe
    """
    # reading the csv input file
    df = pd.read_csv(url, header=None)

    # listing the columns to be dropped as age gaps are not required
    COLUMNS_TO_SUM = [
        '0-4 year olds', '5 to 9 years', '10 to 14 years', '15 to 19 years',
        '20 to 24 years', '25 to 29 years', '30 to 34 years', '35 to 39 years',
        '40 to 44 years', '45 to 49 years', '50 to 54 years', '55 to 59 years',
        '60 to 64 years', '65 to 69 years', '70 to 74 years', '75 to 79 years',
        '80 to 84 years', '85 years and over'
    ]

    # providing column headers
    df.columns = ["Year", "geo_ID", "Race/Sex code"] + COLUMNS_TO_SUM

    # summing all the ages value as age is not required as
    # the dataset deals with sex and race
    df['Total'] = df[COLUMNS_TO_SUM].sum(axis=1)

    # providing geoId to the dataframe and making the geoId of 5 digit as county
    df['geo_ID'] = [f'{x:05}' for x in df['geo_ID']]
    df['Year'] = df['Year'].astype(str) + "-" + df['geo_ID'].astype(str)
    df.drop(columns=['geo_ID'], inplace=True)

    # dropping the unwanted columns
    df = df.drop(columns=COLUMNS_TO_SUM)

    # changing the column values as per metadata
    df = df.replace({
        'Race/Sex code': {
            1: 'Count_Person_Male_WhiteAlone',
            2: 'Count_Person_Female_WhiteAlone',
            3: 'Count_Person_Male_BlackOrAfricanAmericanAlone',
            4: 'Count_Person_Female_BlackOrAfricanAmericanAlone',
            5: 'Count_Person_Male_OtherRaces',
            6: 'Count_Person_Female_OtherRaces'
        }
    })

    # grouping the df as per columns provided
    # performs the provided functions on the data
    df = df.groupby(['Year','Race/Sex code'])\
        .sum().transpose().stack(0).reset_index()

    # dropping unwanted column
    df.drop(columns='level_0', inplace=True)

    # splitting column into geoId and Year
    df['geo_ID'] = df['Year'].str.split('-', expand=True)[1]
    df['Year'] = df['Year'].str.split('-', expand=True)[0]

    df = df.reindex(columns=[
        'Year', 'geo_ID', 'Count_Person_Male_WhiteAlone',
        'Count_Person_Female_WhiteAlone',
        'Count_Person_Male_BlackOrAfricanAmericanAlone',
        'Count_Person_Female_BlackOrAfricanAmericanAlone',
        'Count_Person_Male_OtherRaces', 'Count_Person_Female_OtherRaces'
    ])

    # aggregating columns to get Count_Person_Male
    df["Count_Person_Male"] = df[[
        'Count_Person_Male_WhiteAlone',
        "Count_Person_Male_BlackOrAfricanAmericanAlone",
        'Count_Person_Male_OtherRaces'
    ]].sum(axis=1)

    # aggregating columns to get Count_Person_Female
    df["Count_Person_Female"] = df[[
        'Count_Person_Female_WhiteAlone',
        "Count_Person_Female_BlackOrAfricanAmericanAlone",
        'Count_Person_Female_OtherRaces'
    ]].sum(axis=1)

    # dropping unwanted columns
    df = df.drop(columns=[
        'Count_Person_Male_OtherRaces', 'Count_Person_Female_OtherRaces'
    ])

    # creating geoId
    df['geo_ID'] = 'geoId/' + df['geo_ID']

    df.to_csv(_CODEDIR + "/../output_files/intermediate/" +
              "county_result_1970_1979.csv")
    return df.columns
