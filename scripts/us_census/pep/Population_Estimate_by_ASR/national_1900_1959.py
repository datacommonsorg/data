# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''
This Python Script is for National Level Data 1900-1959
'''
import os
import pandas as pd


def national1900(output_folder: str):
    '''
    This Python Script Loads csv datasets from 1900-1959 on a National Level,
    cleans it and create a cleaned csv
    '''
    # Used to collect data after every loop for every file's df
    final_df = pd.DataFrame()
    # The numbers 00 to 60 signify the available files as per year numbers
    for i in range(00, 60):
        j = f'{i:02}'
        url = 'https://www2.census.gov/programs-surveys/popest/tables/'+\
            '1900-1980/national/asrh/pe-11-19'+str(j)+'.csv'
        # 0=Total_AllRaces
        # 1=Male_AllRaces
        # 2=Female_AllRaces
        # 3=Total_WhiteAlone
        # 4=Male_WhiteAlone
        # 5=Female_WhiteAlone
        # 6=Total_NonWhiteAlone
        # 7=Male_NonWhiteAlone
        # 8=Female_NonWhiteAlone
        cols = ['Age', '0', '1', '2', '3', '4', '5', '6', '7', '8']
        # reading the csv format input file and converting it to a dataframe
        # skipping unwanted rows from top and bottom
        df = pd.read_csv(url,names=cols,engine='python',skiprows=9,\
            skipfooter=15,encoding='ISO-8859-1')
        df['Age'] = df['Age'].astype(str)
        df['Age'] = df['Age'].str.replace("75\\+", "75OrMore")
        df['Age'] = df['Age'].str.replace("85\\+", "85OrMore")
        df['Age'] = df['Age'] + 'Years'
        # dropping unwanted columns
        df.drop(columns=['0'], inplace=True)
        # melt function is used to change the dataframe format from wide to long
        df = df.melt(id_vars=['Age'], var_name='sv', value_name='observation')
        # giving proper column names
        df = df.replace({
            'sv': {
                '1': 'Male',
                '2': 'Female',
                '3': 'WhiteAlone',
                '4': 'Male_WhiteAlone',
                '5': 'Female_WhiteAlone',
                '6': 'NonWhite',
                '7': 'Male_NonWhite',
                '8': 'Female_NonWhite'
            }
        })
        df['SVs'] = 'Count_Person_' + df['Age'] + '_' + df['sv']
        df.drop(columns=['Age', 'sv'], inplace=True)
        #to swap the columns
        year = url[-8:-4]
        # inserting location,year column and measurement_method to the dataframe
        df.insert(loc=0, column='Year', value=year)
        df.insert(1, 'geo_ID', 'country/USA', True)
        df.insert(3, 'Measurement_Method', 'CensusPEPSurvey', True)
        # removing commas from the row values
        df['observation'] = df['observation'].str.replace(",", "")
        final_df = pd.concat([final_df, df])
    final_df.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder,
                     'national_1900_1959.csv'))
