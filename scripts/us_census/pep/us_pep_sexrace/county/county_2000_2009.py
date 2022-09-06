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
for county 2000-2009 and the file
is processed as is.
"""

import pandas as pd
import os

_CODEDIR = os.path.dirname(os.path.realpath(__file__))


def process_county_2000_2009(url: str) -> pd.DataFrame:
    """
    Function Loads input csv datasets
    from 2000-2009 on a County Level,
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
            _url = url + str(j) + '.csv'

            # reading the input csv as dataframe
            df = pd.read_csv(_url, encoding='ISO-8859-1', low_memory=False)

            # years having 1 and 12 and 13 value are not requried
            # as estimate is for April Month and 2010
            df = df.query("YEAR not in [1, 12, 13]")

            # agegrp = 99 is only required as it gives total of all ages
            df = df.query("AGEGRP == 99")

            # converting year value from 3-11 to 2000-2009 as per metadata
            df = df.replace({
                'YEAR': {
                    2: '2000',
                    3: '2001',
                    4: '2002',
                    5: '2003',
                    6: '2004',
                    7: '2005',
                    8: '2006',
                    9: '2007',
                    10: '2008',
                    11: '2009'
                }
            })

            # dropping unwanted columns
            df = df.drop(columns=[
                'SUMLEV', 'STNAME', 'CTYNAME', 'AGEGRP', 'TOT_POP', 'NH_MALE',
                'NH_FEMALE', 'NHWA_MALE', 'NHWA_FEMALE', 'NHBA_MALE',
                'NHBA_FEMALE', 'NHIA_MALE', 'NHIA_FEMALE', 'NHAA_MALE',
                'NHAA_FEMALE', 'NHNA_MALE', 'NHNA_FEMALE', 'NHTOM_MALE',
                'NHTOM_FEMALE', 'H_MALE', 'H_FEMALE', 'HWA_MALE', 'HWA_FEMALE',
                'HBA_MALE', 'HBA_FEMALE', 'HIA_MALE', 'HIA_FEMALE', 'HAA_MALE',
                'HAA_FEMALE', 'HNA_MALE', 'HNA_FEMALE', 'HTOM_MALE',
                'HTOM_FEMALE'
            ])

            # providing geoId to the dataframe
            df.insert(1, 'geo_ID', 'geoId/', True)

            # extracting geoid from state and county column
            df['geo_ID'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(2)\
                + (df['COUNTY'].map(str)).str.zfill(3)

            df.drop(columns=['STATE', 'COUNTY'], inplace=True)

            # writing dataframe to final dataframe
            final_df = pd.concat([final_df, df], ignore_index=True)

    final_df.columns = [
        'geo_ID', 'Year', 'Count_Person_Male', 'Count_Person_Female',
        'Count_Person_Male_WhiteAlone', 'Count_Person_Female_WhiteAlone',
        'Count_Person_Male_BlackOrAfricanAmericanAlone',
        'Count_Person_Female_BlackOrAfricanAmericanAlone',
        'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone',
        'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone',
        'Count_Person_Male_AsianAlone', 'Count_Person_Female_AsianAlone',
        'Count_Person_Male_NativeHawaiianAndOtherPacificIslanderAlone',
        'Count_Person_Female_NativeHawaiianAndOtherPacificIslanderAlone',
        'Count_Person_Male_TwoOrMoreRaces', 'Count_Person_Female_TwoOrMoreRaces'
    ]

    final_df.to_csv(_CODEDIR + "/../output_files/intermediate/" +
                    "county_result_2000_2009.csv")
    return final_df.columns
