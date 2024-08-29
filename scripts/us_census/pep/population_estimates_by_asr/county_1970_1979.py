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
This Python Script is for County Level Data 1970-1979
'''
import os
import pandas as pd
from common_functions import (input_url, replace_age, gender_based_grouping,
                              race_based_grouping)


def county1970(url_file: str, output_folder: str):
    '''
   This Python Script Loads csv datasets from 1970-1979 on a County Level,
   cleans it and create a cleaned csv
   '''
    # Getting input URL from the JSON file.
    _url = input_url(url_file, "1970-79")
    _cols=['Year','geo_ID','Race',0,1,2,3,4,5,6,7\
                      ,8,9,10,11,12,13,14,15,16,17]
    # Contains the final data which has been taken directly and aggregated.
    final_df = pd.DataFrame()
    # Contains aggregated data for age and race.
    df_ar = pd.DataFrame()
    df = pd.read_csv(_url, names=_cols, low_memory=False, encoding='ISO-8859-1')
    df = (df.drop(_cols, axis=1).join(df[_cols]))
    df['geo_ID'] = df['geo_ID'].astype(int)
    df['geo_ID'] = [f'{x:05}' for x in df['geo_ID']]
    df['Race'] = df['Race'].astype(str)
    # Replacing the numbers with more understandable metadata headings.
    df = df.replace({
        'Race': {
            '1': 'Male_WhiteAlone',
            '2': 'Female_WhiteAlone',
            '3': 'Male_BlackOrAfricanAmericanAlone',
            '4': 'Female_BlackOrAfricanAmericanAlone',
            '5': 'Male_OtherRaces',
            '6': 'Female_OtherRaces'
        }
    })
    # Replacing the numbers with more understandable metadata headings.
    df = replace_age(df)
    df = df.melt(id_vars=['Year','geo_ID' ,'Race'], var_name='sv' ,\
       value_name='observation')
    df['SVs'] = 'Count_Person_' + df['sv'] + '_' + df['Race']
    df.drop(columns=['Race', 'sv'], inplace=True)
    df['geo_ID'] = 'geoId/' + df['geo_ID']
    # Making copies of the current DF to be aggregated upon.
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
                     'county_1970_1979.csv'))
