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
for county 1990-2000 and Count_Person_Male
and Count_person_Female are aggregated for this file.
"""

from typing import final
import pandas as pd
import os

_CODEDIR = os.path.dirname(os.path.realpath(__file__))


def process_county_1990_2000(url: str) -> pd.DataFrame:
    """
    Function Loads input csv datasets
    from 1990-2000 on a County Level,
    cleans it and return cleaned dataframe.

    Args:
        url (str) : url of the dataset

    Returns:
        df.columns (pd.DataFrame) : Column names of cleaned dataframe
    """
    final_df = pd.DataFrame()
    # 1 to 57 as state goes till 56
    for i in range(1, 57):

        # states not available for these values
        if i not in [3, 7, 14, 43, 52]:
            j = f'{i:02}'
            _url = url + str(j) + '.txt'

            # 0 = Ages 0-4, 1 = Ages 5-9, 2 = Ages 10-14, 3 = Ages 15-19
            # 4 = Ages 20-24, 5 = Ages 25-29, 6 = Ages 30-34, 7 = Ages 35-39
            # 8 = Ages 40-44, 9 = Ages 45-49, 10 = Ages 50-54, 11 = Ages 55-59
            # 12 = Ages 60-64, 13 = Ages 65-69, 14 = Ages 70-74, 15 = Ages 75-79
            # 16 = Ages 80-84, 17 = Ages 85+
            COLUMNS_TO_SUM = list(range(18))
            _cols = ['Year', 'geo_ID', 'Race']
            _cols.extend(COLUMNS_TO_SUM)

            # reading the input file and converting to dataframe
            df = pd.read_table(_url,
                               index_col=False,
                               delim_whitespace=True,
                               skiprows=16,
                               skipfooter=14,
                               engine='python',
                               names=_cols,
                               encoding='ISO-8859-1')

            # dropping the rows which are having broken values
            num_df = (df.drop(_cols,
                              axis=1).join(df[_cols].apply(pd.to_numeric,
                                                           errors='coerce')))
            df = num_df[num_df[_cols].notnull().all(axis=1)]
            df.loc[:, 1:] = df.loc[:, 1:].apply(pd.to_numeric)
            df.loc[:, 'geo_ID'] = df.loc[:, 'geo_ID'].astype(int)

            # providing geoId to the dataframe
            # and making the geoId of 5 digit as county
            df.loc[:, 'geo_ID'] = [f'{x:05}' for x in df.loc[:, 'geo_ID']]

            # columns after 11 where having origin hence not required
            df.drop(df[df['Race'] >= 11].index, inplace=True)

            # summing all the ages value as age is not required
            df.loc[:, 'Total'] = df.loc[:, COLUMNS_TO_SUM].sum(axis=1)
            df['Total'].astype(int)

            # dropping unwanted age columns
            df.drop(columns=COLUMNS_TO_SUM, inplace=True)

            # changing the column values as per metadata
            df = df.replace({
                'Race': {
                    1: 'Count_Person_Male_WhiteAlone',
                    2: 'Count_Person_Female_WhiteAlone',
                    3: 'Count_Person_Male_WhiteAlone',
                    4: 'Count_Person_Female_WhiteAlone',
                    5: 'Count_Person_Male_BlackOrAfricanAmericanAlone',
                    6: 'Count_Person_Female_BlackOrAfricanAmericanAlone',
                    7: 'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone',
                    8: 'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone',
                    9: 'Count_Person_Male_AsianOrPacificIslander',
                    10: 'Count_Person_Female_AsianOrPacificIslander'
                }
            })

            # extracting year
            df['Year'] = df['Year'].astype(str) + "-" + df['geo_ID'].astype(str)
            df.drop(columns=['geo_ID'], inplace=True)

            # it groups the df as per columns provided
            # performs the provided functions on the data
            df = df.groupby(['Year','Race'])\
                .sum().transpose().stack(0).reset_index()

            # splitting column into geoId and Year
            df['geo_ID'] = df['Year'].str.split('-', expand=True)[1]
            df['Year'] = df['Year'].str.split('-', expand=True)[0]

            # dropping unwanted column
            df.drop(columns=['level_0'], inplace=True)

            # writing the dataframe to final dataframe
            final_df = pd.concat([final_df, df])

    # creating proper geoId
    final_df['geo_ID'] = 'geoId/' + final_df['geo_ID'].astype("str")

    # aggregating required columns to get Count_Person_Male
    final_df["Count_Person_Male"] = final_df.loc[:, [
        'Count_Person_Male_WhiteAlone',
        'Count_Person_Male_BlackOrAfricanAmericanAlone',
        'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone',
        'Count_Person_Male_AsianOrPacificIslander'
    ]].sum(axis=1)

    # aggregating required columns to get Count_Person_Female
    final_df["Count_Person_Female"] = final_df.loc[:, [
        'Count_Person_Female_WhiteAlone',
        'Count_Person_Female_BlackOrAfricanAmericanAlone',
        'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone',
        'Count_Person_Female_AsianOrPacificIslander'
    ]].sum(axis=1)
    final_df = final_df.fillna(-1)
    float_col = final_df.select_dtypes(include=['float64'])
    for col in float_col.columns.values:
        final_df[col] = final_df[col].astype('int64')
        final_df[col] = final_df[col].astype("str").str.replace("-1", "")

    final_df.to_csv(_CODEDIR + "/../output_files/intermediate/" +
                    'county_result_1990_2000.csv')
    return final_df.columns
