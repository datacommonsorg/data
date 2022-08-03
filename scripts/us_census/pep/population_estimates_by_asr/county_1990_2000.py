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
This Python Script is for County Level Data 1990-2000.
'''
import os
import numpy as np
import pandas as pd
from common_functions import (replace_age, gender_based_grouping,
                              race_based_grouping)


def county1990(output_folder: str):
    '''
    This Python Script Loads csv datasets from 1990-2000 on a County Level,
    cleans it and create a cleaned csv.
    '''
    # Contains the final data which has been taken directly and aggregated.
    final_df = pd.DataFrame()
    # Contains aggregated data for age and sex.
    df_as = pd.DataFrame()
    # Contains aggregated data for age and race.
    df_ar = pd.DataFrame()
    # Reading the csv input file.
    # The numbers 1 to 57 signify the available files as per state numbers
    # The [3, 7, 14, 43, 52] signify the state numbers absent
    for i in range(1, 57):
        if i not in [3, 7, 14, 43, 52]:
            j = f'{i:02}'
            url = 'https://www2.census.gov/programs-surveys'+\
                '/popest/tables/1990-2000/counties/asrh/casrh'+str(j)+'.txt'

            cols=['Year','geo_ID','Race',0,1,2,3,4,5,6,7\
                ,8,9,10,11,12,13,14,15,16,17]
            df = pd.read_table(url,index_col=False,delim_whitespace=True\
                ,skiprows=16,skipfooter=14,engine='python',names=cols,\
                    encoding='ISO-8859-1')
            # Removing the lines that have false symbols.
            num_df = (df.drop(cols, axis=1).join(df[cols]\
                .apply(pd.to_numeric, errors='coerce')))
            df = num_df[num_df[cols].notnull().all(axis=1)]
            df[1:] = df[1:].apply(pd.to_numeric)
            df['geo_ID'] = df['geo_ID'].astype(int)

            # Providing geoId to the dataframe.
            df['geo_ID'] = [f'{x:05}' for x in df['geo_ID']]
            # Replacing the numbers with more understandable metadata headings.
            df = replace_age(df)

            # Columns after 11 where having origin.
            df.drop(df[df['Race'] >= 11].index, inplace=True)
            # Changing the column values as per metadata.
            df['Race'] = df['Race'].astype(int).astype(str)
            df = df.replace({
                'Race': {
                    '10': 'Female_AsianOrPacificIslander',
                    '1': 'Male_WhiteAlone',
                    '2': 'Female_WhiteAlone',
                    '3': 'Male_WhiteAlone',
                    '4': 'Female_WhiteAlone',
                    '5': 'Male_BlackOrAfricanAmericanAlone',
                    '6': 'Female_BlackOrAfricanAmericanAlone',
                    '7': 'Male_AmericanIndianAndAlaskaNativeAlone',
                    '8': 'Female_AmericanIndianAndAlaskaNativeAlone',
                    '9': 'Male_AsianOrPacificIslander'
                }
            })
            df = df.melt(id_vars=['Year','geo_ID' ,'Race'], var_name='Age' , \
                value_name='observation')
            df['SVs'] = 'Count_Person_' + df['Age'] + '_' + df['Race']
            df.drop(columns=['Race', 'Age'], inplace=True)
            # writing the dataframe to final dataframe
            final_df = pd.concat([final_df, df])

    # Creating geoId.
    final_df['geo_ID'] = 'geoId/' + final_df['geo_ID'].astype("str")
    final_df = final_df.groupby(['Year', 'geo_ID', 'SVs']).sum().reset_index()
    # Adding measurement method.
    final_df['Measurement_Method'] = np.where(final_df['SVs'].str.contains\
        ('White'), 'dcAggregate/CensusPEPSurvey', 'CensusPEPSurvey')
    # Making copies and using group by to get Aggregated Values.
    df_as = pd.concat([final_df, df_as])
    df_ar = pd.concat([df_ar, final_df])
    # DF sent to an external function for aggregation based on gender.
    df_as = gender_based_grouping(df_as)
    df_as.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    # DF sent to an external function for aggregation based on race.
    df_ar = race_based_grouping(df_ar)
    df_ar.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    final_df = pd.concat([final_df, df_ar, df_as])

    # Writing to output csv.
    final_df.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder,
                     'county_1990_2000.csv'))
