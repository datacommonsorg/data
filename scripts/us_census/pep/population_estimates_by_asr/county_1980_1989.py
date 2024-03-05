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
This Python Script is for County and State Level Data 1980-1989.
'''
import os
import pandas as pd
from common_functions import (input_url, replace_age, race_based_grouping,
                              gender_based_grouping)


def county1980(url_file: str, output_folder: str):
    '''
    This Python Script Loads csv datasets from 1980-1989 on a County and State 
    Level, cleans it and create a cleaned csv for both County and State.
    '''
    # Getting input URL from the JSON file.
    _url = input_url(url_file, "1980-89")
    # Contains the final data which has been taken directly and aggregated.
    final_df = pd.DataFrame()
    # Contains aggregated data for age and sex.
    df_as = pd.DataFrame()
    # Contains aggregated data for age and race.
    df_ar = pd.DataFrame()
    cols=['Year','geo_ID','Race',0,1,2,3,4,5,6,7\
                    ,8,9,10,11,12,13,14,15,16,17]
    df = pd.read_csv(_url,skiprows=7,names=cols,low_memory=False,\
        encoding='ISO-8859-1')

    df = (df.drop(cols, axis=1).join(df[cols]))
    df['geo_ID'] = df['geo_ID'].astype(int)
    df['geo_ID'] = [f'{x:05}' for x in df['geo_ID']]
    df['Race'] = df['Race'].astype(str)
    # Replacing the names with more understandable SV headings.
    df = df.replace({
        'Race': {
            'White male': 'Male_WhiteAlone',
            'White female': 'Female_WhiteAlone',
            'Black male': 'Male_BlackOrAfricanAmericanAlone',
            'Black female': 'Female_BlackOrAfricanAmericanAlone',
            'Other races male': 'Male_OtherRaces',
            'Other races female': 'Female_OtherRaces'
        }
    })
    # Replacing the numbers with more understandable metadata headings.
    df = replace_age(df)
    df = df.melt(id_vars=['Year','geo_ID' ,'Race'], var_name='sv' ,\
        value_name='observation')
    df['SVs'] = 'Count_Person_' + df['sv'] + '_' + df['Race']
    df.drop(columns=['Race', 'sv'], inplace=True)
    # Generating Aggregated Data by using Group by on rows.
    df_as = pd.concat([df_as, df])
    df_ar = pd.concat([df_ar, df])
    df.insert(3, 'Measurement_Method', 'CensusPEPSurvey', True)
    # DF sent to an external function for aggregation based on gender.
    df_as = gender_based_grouping(df_as)
    df_as.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    # DF sent to an external function for aggregation based on race.
    df_ar = race_based_grouping(df_ar)
    df_ar.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    df = pd.concat([df_as, df_ar, df])
    df['geo_ID'] = 'geoId/' + df['geo_ID'].astype(str)
    final_df = df[~df.SVs.str.contains('OtherRaces')]
    final_df.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder,
                     'county_1980_1989.csv'))
    # Aggregating the County Data on geo_ID to make State Data.
    final_df['geo_ID'] = final_df['geo_ID'].str[:-3]
    final_df = final_df.groupby(['Year','geo_ID','SVs']).sum()\
    .stack(0).reset_index()
    final_df['observation'] = final_df[0]
    final_df.drop(columns=['level_3', 0], inplace=True)
    final_df['Measurement_Method'] = 'dcAggregate/CensusPEPSurvey'
    final_df.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder,
                     'state_1980_1989.csv'))
