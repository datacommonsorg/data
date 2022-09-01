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
for State 2010-2020 and the file
is processed as is.
"""

import pandas as pd
import os

_CODEDIR = os.path.dirname(os.path.realpath(__file__))


def process_state_2010_2020(url: str) -> pd.DataFrame:
    """
    Function Loads input csv datasets
    from 2010-2020 on a State Level,
    cleans it and return cleaned dataframe.

    Args:
        url (str) : url of the dataset

    Returns:
        df.columns (pd.DataFrame) : Coulumn names of cleaned dataframe
    """
    # reading input file to dataframe
    df = pd.read_csv(url, encoding='ISO-8859-1', low_memory=False)

    # years having 1 and 2 value are not requried as estimate is for April Month
    # agegrp is only required as it gives total of all ages
    df = df.query("YEAR not in [1, 2]")
    df = df.query("AGEGRP == 0")

    # year starting from 3 so need to convert it to 2010s
    # df['YEAR'] = df['YEAR'] + 2010 - 3
    df.loc[:, 'YEAR'] = df.loc[:, 'YEAR'] + 2010 - 3

    # add fips code for location
    df.loc[:,
           'geo_ID'] = 'geoId/' + (df.loc[:, 'STATE'].map(str)).str.zfill(2) + (
               df.loc[:, 'COUNTY'].map(str)).str.zfill(3)

    # drop unwanted columns
    df.drop(['SUMLEV', 'STATE', 'COUNTY', 'STNAME', 'CTYNAME', 'AGEGRP'],
            axis=1,
            inplace=True)

    # dropping unwanted columns
    df = df.drop(columns=[
        'TOT_POP', 'NH_MALE', 'NH_FEMALE', 'NHWA_MALE', 'NHWA_FEMALE',
        'NHBA_MALE', 'NHBA_FEMALE', 'NHIA_MALE', 'NHIA_FEMALE', 'NHAA_MALE',
        'NHAA_FEMALE', 'NHNA_MALE', 'NHNA_FEMALE', 'NHTOM_MALE', 'NHTOM_FEMALE',
        'NHWAC_MALE', 'NHWAC_FEMALE', 'NHBAC_MALE', 'NHBAC_FEMALE',
        'NHIAC_MALE', 'NHIAC_FEMALE', 'NHAAC_MALE', 'NHAAC_FEMALE',
        'NHNAC_MALE', 'NHNAC_FEMALE', 'H_MALE', 'H_FEMALE', 'HWA_MALE',
        'HWA_FEMALE', 'HBA_MALE', 'HBA_FEMALE', 'HIA_MALE', 'HIA_FEMALE',
        'HAA_MALE', 'HAA_FEMALE', 'HNA_MALE', 'HNA_FEMALE', 'HTOM_MALE',
        'HTOM_FEMALE', 'HWAC_MALE', 'HWAC_FEMALE', 'HBAC_MALE', 'HBAC_FEMALE',
        'HIAC_MALE', 'HIAC_FEMALE', 'HAAC_MALE', 'HAAC_FEMALE', 'HNAC_MALE',
        'HNAC_FEMALE'
    ])

    # to remove numeric thousand seperator
    for sv in [
            'YEAR', 'TOT_MALE', 'TOT_FEMALE', 'WA_MALE', 'WA_FEMALE', 'BA_MALE',
            'BA_FEMALE', 'IA_MALE', 'IA_FEMALE', 'AA_MALE', 'AA_FEMALE',
            'NA_MALE', 'NA_FEMALE', 'TOM_MALE', 'TOM_FEMALE', 'WAC_MALE',
            'WAC_FEMALE', 'BAC_MALE', 'BAC_FEMALE', 'IAC_MALE', 'IAC_FEMALE',
            'AAC_MALE', 'AAC_FEMALE', 'NAC_MALE', 'NAC_FEMALE'
    ]:
        df[sv] = df[sv].astype(int)

    # extracting geoid
    df['geo_ID'] = (df['geo_ID'].map(str)).str[:8]

    # it groups the df as per columns provided
    # performs the provided functions on the data
    df = df.groupby(['YEAR', 'geo_ID']).sum().reset_index()

    # providing proper column names
    df.columns=['Year','geo_ID','Count_Person_Male',
        'Count_Person_Female','Count_Person_Male_WhiteAlone',
        'Count_Person_Female_WhiteAlone',
        'Count_Person_Male_BlackOrAfricanAmericanAlone',
        'Count_Person_Female_BlackOrAfricanAmericanAlone',
        'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone',
        'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone',
        'Count_Person_Male_AsianAlone','Count_Person_Female_AsianAlone',
        'Count_Person_Male_NativeHawaiianAndOtherPacificIslanderAlone',
        'Count_Person_Female_NativeHawaiianAndOtherPacificIslanderAlone',
        'Count_Person_Male_TwoOrMoreRaces','Count_Person_Female_TwoOrMoreRaces',
        'Count_Person_Male_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
        'Count_Person_Female_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
        'Count_Person_Male_BlackOrAfricanAmericanAlone'+\
            'OrInCombinationWithOneOrMoreOtherRaces',
        'Count_Person_Female_BlackOrAfricanAmericanAlone'+\
            'OrInCombinationWithOneOrMoreOtherRaces',
        'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone'+\
            'OrInCombinationWithOneOrMoreOtherRaces',
        'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone'+\
            'OrInCombinationWithOneOrMoreOtherRaces',
        'Count_Person_Male_AsianAloneOrInCombinationWithOneOrMoreOtherRaces',
        'Count_Person_Female_AsianAloneOrInCombinationWithOneOrMoreOtherRaces',
        'Count_Person_Male_NativeHawaiianAndOtherPacificIslanderAlone'+\
            'OrInCombinationWithOneOrMoreOtherRaces',
        'Count_Person_Female_NativeHawaiianAndOtherPacificIslanderAlone'+\
            'OrInCombinationWithOneOrMoreOtherRaces']

    df.to_csv(_CODEDIR + "/../output_files/intermediate/" +
              'state_result_2010_2020.csv',
              index=False)
    return df.columns
