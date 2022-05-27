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
for National Level Data
1960-1979
'''
import os
import pandas as pd


def national1960():
    '''
    This Python Script Loads csv datasets
    from 1960-1979 on a National Level,
    cleans it and create a cleaned csv
    '''
    final_df = pd.DataFrame()
    for i in range(60, 80):
        url = 'https://www2.census.gov/programs-surveys/popest/tables/'+\
            '1900-1980/national/asrh/pe-11-19'+str(i)+'.csv'

        # 0-All races total,1-All races male,2-All races female,3-White total,
        # 4-White male,5-White female,6-Black total,7-Black male,8-Black female,
        # 9-Other races total,10-Other races male,11-Other races female
        cols = [
            'Age', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'
        ]
        # reading the csv format input file and converting it to a dataframe
        # skipping unwanted rows from top and bottom
        df = pd.read_csv(url,names=cols,engine='python',skiprows=8,\
            skipfooter=15)
        df['Age'] = df['Age'].astype(str)
        df['Age'] = df['Age'].str.replace("85\\+", "85OrMore")
        df['Age'] = df['Age'] + 'Years'
        # dropping unwanted columns
        df.drop(columns=['0', '9', '10', '11'], inplace=True)
        # melt funtion used to change the Data frame format from wide to long
        df = df.melt(id_vars=['Age'], var_name='sv', value_name='observation')
        # providing proper column names
        _dict = {
            '1': 'Male',
            '2': 'Female',
            '3': 'WhiteAlone',
            '4': 'Male_WhiteAlone',
            '5': 'Female_WhiteAlone',
            '6': 'BlackOrAfricanAmericanAlone',
            '7': 'Male_BlackOrAfricanAmericanAlone',
            '8': 'Female_BlackOrAfricanAmericanAlone'
        }
        df = df.replace({'sv': _dict})
        df['SVs'] = 'Count_Person_' + df['Age'] + '_' + df['sv']
        # dropping unwanted columns
        df.drop(columns=['Age', 'sv'], inplace=True)
        # inserting Year,Location and Measurement_Method to the dataframe
        # extracting year values from url
        year = url[-8:-4]
        df.insert(loc=0, column='Year', value=year)
        df.insert(1, 'geo_ID', 'country/USA', True)
        df.insert(3, 'Measurement_Method', 'CensusPEPSurvey', True)
        # removing numeric thousand separator from the values
        df['observation'] = df['observation'].str.replace(",", "")
        # writting the data to final dataframe
        final_df = pd.concat([final_df, df])
    # writing the dataframe to output csv
    final_df.to_csv(os.path.dirname(os.path.abspath(__file__)) + os.sep \
        +'input_data/national_1960_1979.csv')
