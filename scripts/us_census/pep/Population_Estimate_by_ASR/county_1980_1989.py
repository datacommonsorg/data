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
This Python Script is
for County and State Level Data
1980-1989.
'''
import os
import pandas as pd
from common_functions import _input_url, _replace_age


def county1980():
    '''
    This Python Script Loads csv datasets
    from 1980-1989 on a County and State Level,
    cleans it and create a cleaned csv
    for both County and State.
    '''
    # Getting input URL from the JSON file.
    _url = _input_url("county.json", "1980-89")
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
    _dict = {
        'White male': 'Male_WhiteAlone',
        'White female': 'Female_WhiteAlone',
        'Black male': 'Male_BlackOrAfricanAmericanAlone',
        'Black female': 'Female_BlackOrAfricanAmericanAlone',
        'Other races male': 'Male_OtherRaces',
        'Other races female': 'Female_OtherRaces'
    }
    df = df.replace({'Race': _dict})
    # Replacing the numbers with more understandable metadata headings.
    df = _replace_age(df)
    df = df.melt(id_vars=['Year','geo_ID' ,'Race'], var_name='sv' ,\
        value_name='observation')
    df['SVs'] = 'Count_Person_' + df['sv'] + '_' + df['Race']
    df.drop(columns=['Race', 'sv'], inplace=True)
    # Generating Aggregated Data by using Group by on rows.
    df_as = pd.concat([df_as, df])
    df_ar = pd.concat([df_ar, df])
    df_as.insert(3, 'Measurement_Method', 'CensusPEPSurvey', True)
    df['SVs'] = df['SVs'].str.replace('_WhiteAlone', '')
    df['SVs'] = df['SVs'].str.replace('_BlackOrAfricanAmericanAlone', '')
    df['SVs'] = df['SVs'].str.replace('_OtherRaces', '')
    df = df.groupby(['Year', 'geo_ID', 'SVs']).sum().reset_index()
    df.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    df_ar['SVs'] = df_ar['SVs'].str.replace('_Male', '')
    df_ar['SVs'] = df_ar['SVs'].str.replace('_Female', '')
    df_ar = df_ar.groupby(['Year', 'geo_ID', 'SVs']).sum().reset_index()
    df_ar.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    df_as = pd.concat([df_as, df_ar, df])
    df_as['geo_ID'] = 'geoId/' + df_as['geo_ID'].astype(str)
    final_df = df_as[~df_as.SVs.str.contains('OtherRaces')]
    final_df.to_csv(
        os.path.dirname(os.path.abspath(__file__)) + os.sep +
        'input_data/county_1980_1989.csv')
    # Aggregating the County Data on geo_ID to make State Data.
    final_df['geo_ID'] = final_df['geo_ID'].str[:-3]
    final_df = final_df.groupby(['Year','geo_ID','SVs']).sum()\
    .stack(0).reset_index()
    print(final_df)
    final_df['observation'] = final_df[0]
    final_df.drop(columns=['level_3', 0], inplace=True)
    final_df['Measurement_Method'] = 'dcAggregate/CensusPEPSurvey'
    final_df.to_csv(
        os.path.dirname(os.path.abspath(__file__)) + os.sep +
        'input_data/state_1980_1989.csv')
