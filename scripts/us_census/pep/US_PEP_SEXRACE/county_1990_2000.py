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
from 1990-2000 on a County Level,
cleans it and create a cleaned csv
'''

import pandas as pd

# reading the csv input file
final_df = pd.DataFrame()
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
        num_df = (df.drop(cols, axis=1).join(df[cols]\
            .apply(pd.to_numeric, errors='coerce')))
        df = num_df[num_df[cols].notnull().all(axis=1)]
        df[1:] = df[1:].apply(pd.to_numeric)
        df['geo_ID'] = df['geo_ID'].astype(int)

        # providing geoId to the dataframe and making the geoId of 5 digit as county
        df['geo_ID'] = [f'{x:05}' for x in df['geo_ID']]

        # columns after 11 where having origin
        df.drop(df[df['Race'] >= 11].index, inplace=True)
        df['Total']=df[0]+df[1]+df[2]+df[3]+df[4]+df[5]+df[6]+df[7]\
            +df[8]+df[9]+df[10]+df[11]+df[12]+df[13]+df[14]+df[15]+df[16]+df[17]
        df['Total'].astype(int)
        df.drop(columns=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14\
            ,15,16,17],inplace=True)

        # changing the column values as per metadata
        df['Race'] = df['Race'].astype(int).astype(str)
        df['Race'] = df['Race'].str.replace('10', 'APF')
        df['Race'] = df['Race'].str.replace('1', 'WM')
        df['Race'] = df['Race'].str.replace('2', 'WF')
        df['Race'] = df['Race'].str.replace('3', 'WM')
        df['Race'] = df['Race'].str.replace('4', 'WF')
        df['Race'] = df['Race'].str.replace('5', 'BM')
        df['Race'] = df['Race'].str.replace('6', 'BF')
        df['Race'] = df['Race'].str.replace('7', 'AIM')
        df['Race'] = df['Race'].str.replace('8', 'AIF')
        df['Race'] = df['Race'].str.replace('9', 'APM')

        df['Year'] = df['Year'].astype(str) + "-" + df['geo_ID'].astype(str)
        df.drop(columns=['geo_ID'], inplace=True)
        df = df.groupby(['Year','Race']).sum()\
            .transpose().stack(0).reset_index()

        # splitting column into geoId and Year
        df['geo_ID'] = df['Year'].str.split('-', expand=True)[1]
        df['Year'] = df['Year'].str.split('-', expand=True)[0]

        # dropping unwanted column
        df.drop(columns=['level_0'], inplace=True)

        # writing the dataframe to final dataframe
        final_df = pd.concat([final_df, df])

# creating geoId
final_df['geo_ID'] = 'geoId/' + final_df['geo_ID'].astype("str")

# providing proper name to cloumns
final_df.columns=['Year',
    'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone'+\
        'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone'+\
        'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Female_AsianOrPacificIslander',
    'Count_Person_Male_AsianOrPacificIslander',
    'Count_Person_Female_BlackOrAfricanAmericanAlone'+\
        'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Male_BlackOrAfricanAmericanAlone'+\
        'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Female_WhiteAlone'+\
        'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Male_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
    'geo_ID']

# aggregating columns to get Count_Person_Male
final_df["Count_Person_Male"] = final_df.loc[:,['Count_Person_Male_'+\
        'WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Male_BlackOrAfricanAmericanAlone'+\
        'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone'+\
        'OrInCombinationWithOneOrMoreOtherRaces',
        'Count_Person_Male_AsianOrPacificIslander']].sum(axis=1)

# aggregating columns to get Count_Person_Female
final_df["Count_Person_Female"] = final_df.loc[:,['Count_Person_Female_'+\
        'WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Female_BlackOrAfricanAmericanAlone'+\
        'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone'+\
            'OrInCombinationWithOneOrMoreOtherRaces',
    'Count_Person_Female_AsianOrPacificIslander']].sum(axis=1)

# writing to output csv
final_df.to_csv('county_result_1990_2000.csv')
