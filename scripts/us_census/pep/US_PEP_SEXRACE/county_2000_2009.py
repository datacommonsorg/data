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
from 2000-2009 on a County Level,
cleans it and create a cleaned csv
'''

import json
import pandas as pd

URLS_JSON_PATH = "County/county_2000_2009.json"
URLS_JSON = None
with open(URLS_JSON_PATH, encoding="UTF-8") as file:
    URLS_JSON = json.load(file)
url = URLS_JSON["url"]

# reading the csv input file
df = pd.read_csv(url)

# years having 1 and 2 value are not requried as estimate is for April Month
df = df.query("YEAR not in [1, 2]")

# agegrp is only required as it gives total of all ages
df = df.query("AGEGRP == 0")

# providing geoId to the dataframe
df.insert(1, 'geo_ID', 'geoId/', True)
df['geo_ID'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(2)\
     + (df['COUNTY'].map(str)).str.zfill(3)

# year value starting from 3-12 so need to convet it to 2000-2009
df['YEAR'] = df['YEAR'] + 2000 - 3

# dropping unwanted column
df = df.drop(columns=[
    'SUMLEV', 'STNAME', 'CTYNAME', 'AGEGRP', 'COUNTY', 'TOT_POP', 'STATE',
    'NH_MALE', 'NH_FEMALE', 'NHWA_MALE', 'NHWA_FEMALE', 'NHBA_MALE',
    'NHBA_FEMALE', 'NHIA_MALE', 'NHIA_FEMALE', 'NHAA_MALE', 'NHAA_FEMALE',
    'NHNA_MALE', 'NHNA_FEMALE', 'NHTOM_MALE', 'NHTOM_FEMALE', 'NHWAC_MALE',
    'NHWAC_FEMALE', 'NHBAC_MALE', 'NHBAC_FEMALE', 'NHIAC_MALE', 'NHIAC_FEMALE',
    'NHAAC_MALE', 'NHAAC_FEMALE', 'NHNAC_MALE', 'NHNAC_FEMALE', 'H_MALE',
    'H_FEMALE', 'HWA_MALE', 'HWA_FEMALE', 'HBA_MALE', 'HBA_FEMALE', 'HIA_MALE',
    'HIA_FEMALE', 'HAA_MALE', 'HAA_FEMALE', 'HNA_MALE', 'HNA_FEMALE',
    'HTOM_MALE', 'HTOM_FEMALE', 'HWAC_MALE', 'HWAC_FEMALE', 'HBAC_MALE',
    'HBAC_FEMALE', 'HIAC_MALE', 'HIAC_FEMALE', 'HAAC_MALE', 'HAAC_FEMALE',
    'HNAC_MALE', 'HNAC_FEMALE'
])

# providing proper column name
df.columns=['geo_ID','Year','Count_Person_Male','Count_Person_Female',
    'Count_Person_Male_WhiteAlone','Count_Person_Female_WhiteAlone',
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

# writing the dataframe to output csv
df.to_csv("county_result_2000_2009.csv")
