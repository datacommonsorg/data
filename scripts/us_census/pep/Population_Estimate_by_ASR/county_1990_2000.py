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
This Python Script is for
for County Level Data
1990-2000
'''
import os
import numpy as np
import pandas as pd


def county1990():
    '''
    This Python Script Loads csv datasets
    from 1990-2000 on a County Level,
    cleans it and create a cleaned csv
    '''
    final_df = pd.DataFrame()
    df1 = pd.DataFrame()
    df2 = pd.DataFrame()
    # reading the csv input file
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
            # removing the lines that have false symbols
            num_df = (df.drop(cols, axis=1).join(df[cols]\
                .apply(pd.to_numeric, errors='coerce')))
            df = num_df[num_df[cols].notnull().all(axis=1)]
            df[1:] = df[1:].apply(pd.to_numeric)
            df['geo_ID'] = df['geo_ID'].astype(int)

            # providing geoId to the dataframe
            df['geo_ID'] = [f'{x:05}' for x in df['geo_ID']]
            # Replacing the numbers with more understandable metadata headings
            _dict = {
                0: '0To4Years',
                1: '5To9Years',
                2: '10To14Years',
                3: '15To19Years',
                4: '20To24Years',
                5: '25To29Years',
                6: '30To34Years',
                7: '35To39Years',
                8: '40To44Years',
                9: '45To49Years',
                10: '50To54Years',
                11: '55To59Years',
                12: '60To64Years',
                13: '65To69Years',
                14: '70To74Years',
                15: '75To79Years',
                16: '80To84Years',
                17: '85OrMoreYears'
            }
            df.rename(_dict, axis=1, inplace=True)

            # columns after 11 where having origin
            df.drop(df[df['Race'] >= 11].index, inplace=True)
            # changing the column values as per metadata
            df['Race'] = df['Race'].astype(int).astype(str)
            df['Race'] = df['Race'].str.replace('10',\
                'Female_AsianOrPacificIslander')
            df['Race'] = df['Race'].str.replace('1',\
                'Male_WhiteAlone')
            df['Race'] = df['Race'].str.replace('2',\
                'Female_WhiteAlone')
            df['Race'] = df['Race'].str.replace('3',\
                'Male_WhiteAlone')
            df['Race'] = df['Race'].str.replace('4',\
                'Female_WhiteAlone')
            df['Race'] = df['Race'].str.replace('5','Male_BlackOrAfrican'+\
                'AmericanAlone')
            df['Race'] = df['Race'].str.replace('6', 'Female_BlackOrAfrican'+\
                'AmericanAlone')
            df['Race'] = df['Race'].str.replace('7', 'Male_AmericanIndianAnd'+\
                'AlaskaNativeAlone')
            df['Race'] = df['Race'].str.replace('8', 'Female_AmericanIndianAnd'\
                +'AlaskaNativeAlone')
            df['Race'] = df['Race'].str.replace('9', \
                'Male_AsianOrPacificIslander')

            df = df.melt(id_vars=['Year','geo_ID' ,'Race'], var_name='Age' , \
                value_name='observation')
            df['SVs'] = 'Count_Person_' + df['Age'] + '_' + df['Race']
            df.drop(columns=['Race', 'Age'], inplace=True)
            # writing the dataframe to final dataframe
            final_df = pd.concat([final_df, df])

    # creating geoId
    final_df['geo_ID'] = 'geoId/' + final_df['geo_ID'].astype("str")
    final_df = final_df.groupby(['Year', 'geo_ID', 'SVs']).sum().reset_index()
    # adding measurement method
    final_df['Measurement_Method'] = np.where(final_df['SVs'].str.contains\
        ('White'), 'dcAggregate/CensusPEPSurvey', 'CensusPEPSurvey')
    # Making copies and using group by to get Aggregated Values
    df1 = pd.concat([final_df, df1])
    df2 = pd.concat([df2, final_df])
    df1['SVs'] = df1['SVs'].str.replace('_AmericanIndianAndAlaskaNativeAlone'\
        ,'')
    df1['SVs'] = df1['SVs'].str.replace('_AsianOrPacificIslander', '')
    df1['SVs'] = df1['SVs'].str.replace('_BlackOrAfricanAmericanAlone','')
    df1['SVs'] = df1['SVs'].str.replace('_WhiteAlone','')
    df1 = df1.groupby(['Year', 'geo_ID', 'SVs']).sum().reset_index()
    df1.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    df2['SVs'] = df2['SVs'].str.replace('_Male', '')
    df2['SVs'] = df2['SVs'].str.replace('_Female', '')
    df2 = df2.groupby(['Year', 'geo_ID', 'SVs']).sum().reset_index()
    df2.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    final_df = pd.concat([final_df, df2, df1])

    # writing to output csv
    final_df.to_csv(
        os.path.dirname(os.path.abspath(__file__)) + os.sep +
        'input_data/county_1990_2000.csv')
