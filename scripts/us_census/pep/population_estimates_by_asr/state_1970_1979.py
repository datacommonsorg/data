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
This Python Script is for State Level Data 1970-1979.
'''
import os
import pandas as pd
from common_functions import (input_url, gender_based_grouping,
                              race_based_grouping)


def state1970(url_file: str, output_folder: str):
    '''
      This Python Script Loads csv datasets from 1970-1979 on a State Level,
      cleans it and create a cleaned csv.
      '''

    _url = input_url(url_file, "1970-79")
    df = pd.read_csv(_url, skiprows=5, encoding='ISO-8859-1')
    df.insert(1, 'geo_ID', 'geoId/', True)
    df['geo_ID'] = 'geoId/' + (df['FIPS State Code'].map(str)).str.zfill(2)
    # Dropping the old unwanted columns.
    df.drop(columns=['State Name', 'FIPS State Code'], inplace=True)
    df.rename(columns=\
       {'Year of Estimate': 'Year','Race/Sex Indicator': 'Race/Sex'},\
          inplace=True)

    df['Race/Sex'] = df['Race/Sex'].astype(str)
    df = df.replace({
        "Race/Sex": {
            'White male': 'Male_WhiteAlone',
            'White female': 'Female_WhiteAlone',
            'Black male': 'Male_BlackOrAfricanAmericanAlone',
            'Black female': 'Female_BlackOrAfricanAmericanAlone',
            'Other races male': 'Male_OtherRaces',
            'Other races female': 'Female_OtherRaces'
        }
    })
    df = df.melt(id_vars=['Year','geo_ID' ,'Race/Sex'], var_name='Age' ,\
       value_name='observation')
    df['Age'] = df['Age'].astype(str)
    # Making Age groups as per SV Naming Convention.

    df = df.replace({
        "Age": {
            'Under 5 years': '0To4Years',
            '5 to 9 years': '5To9Years',
            '10 to 14 years': '10To14Years',
            '15 to 19 years': '15To19Years',
            '20 to 24 years': '20To24Years',
            '25 to 29 years': '25To29Years',
            '30 to 34 years': '30To34Years',
            '35 to 39 years': '35To39Years',
            '40 to 44 years': '40To44Years',
            '45 to 49 years': '45To49Years',
            '50 to 54 years': '50To54Years',
            '55 to 59 years': '55To59Years',
            '60 to 64 years': '60To64Years',
            '65 to 69 years': '65To69Years',
            '70 to 74 years': '70To74Years',
            '75 to 79 years': '75To79Years',
            '80 to 84 years': '80To84Years',
            '85 years and over': '85OrMoreYears'
        }
    })
    df['SVs'] = 'Count_Person_' + df['Age'] + '_' + df['Race/Sex']
    df = df.drop(columns=['Age', 'Race/Sex'])
    df['observation'] = df['observation'].str.replace(",", "").astype(int)
    # Making Copies of current DF and using Group by on them
    # to get Aggregated Values
    # final_df for displaying final concatinated output
    # and df_ar for aggregated age/race output.
    final_df = pd.DataFrame()
    df_ar = pd.DataFrame()
    final_df = pd.concat([final_df, df])
    df_ar = pd.concat([df_ar, df])
    final_df.insert(3, 'Measurement_Method', 'CensusPEPSurvey', True)
    # DF sent to an external function for aggregation based on gender.
    df = gender_based_grouping(df)
    df.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    # DF sent to an external function for aggregation based on race.
    df_ar = race_based_grouping(df_ar)
    df_ar.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    final_df = pd.concat([final_df, df_ar, df])
    final_df = final_df[~final_df.SVs.str.contains('OtherRaces')]
    final_df.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder,
                     'state_1970_1979.csv'))
