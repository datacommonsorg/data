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
This Python Script is for National Level Data 1960-1979.
'''
import os
import pandas as pd


def national1960(output_folder: str):
    '''
    This Python Script Loads csv datasets from 1960-1979 on a National Level,
    cleans it and create a cleaned csv.
    '''
    # Used to collect data after every loop for every file's df.
    final_df = pd.DataFrame()
    # The numbers 60 to 80 signify the available files as per year numbers
    for i in range(60, 80):
        url = 'https://www2.census.gov/programs-surveys/popest/tables/'+\
            '1900-1980/national/asrh/pe-11-19'+str(i)+'.csv'

        # 0-All races total,1-All races male,2-All races female,3-White total,
        # 4-White male,5-White female,6-Black total,7-Black male,8-Black female,
        # 9-Other races total,10-Other races male,11-Other races female.
        cols = [
            'Age', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'
        ]
        # Reading the csv format input file and converting it to a dataframe.
        # Skipping unwanted rows from top and bottom.
        df = pd.read_csv(url,names=cols,engine='python',skiprows=8,\
            skipfooter=15)
        df['Age'] = df['Age'].astype(str)
        df['Age'] = df['Age'].str.replace("85\\+", "85OrMore")
        df['Age'] = df['Age'] + 'Years'
        # Dropping unwanted columns Total (0) and Other Races (9-11)
        df.drop(columns=['0', '9', '10', '11'], inplace=True)
        # Melt funtion used to change the Data frame format from wide to long.
        df = df.melt(id_vars=['Age'], var_name='sv', value_name='observation')
        # Providing proper column names.
        df = df.replace({
            'sv': {
                '1': 'Male',
                '2': 'Female',
                '3': 'WhiteAlone',
                '4': 'Male_WhiteAlone',
                '5': 'Female_WhiteAlone',
                '6': 'BlackOrAfricanAmericanAlone',
                '7': 'Male_BlackOrAfricanAmericanAlone',
                '8': 'Female_BlackOrAfricanAmericanAlone'
            }
        })
        df['SVs'] = 'Count_Person_' + df['Age'] + '_' + df['sv']
        # Dropping unwanted columns.
        df.drop(columns=['Age', 'sv'], inplace=True)
        # Inserting Year,Location and Measurement_Method to the dataframe.
        # Extracting year values from url.
        year = url[-8:-4]
        df.insert(loc=0, column='Year', value=year)
        df.insert(1, 'geo_ID', 'country/USA', True)
        df.insert(3, 'Measurement_Method', 'CensusPEPSurvey', True)
        # Removing numeric thousand separator from the values.
        df['observation'] = df['observation'].str.replace(",", "")
        # Writting the data to final dataframe
        final_df = pd.concat([final_df, df])
    # Writing the dataframe to output csv.
    final_df.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder,
                     'national_1960_1979.csv'))
