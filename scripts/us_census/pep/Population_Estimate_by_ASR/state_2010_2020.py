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
This Python Script is for State Level Data 2010-2020.
'''
import os
import pandas as pd
from common_functions import input_url, gender_based_grouping


def state2010(url_file: str, output_folder: str):
    '''
   This Python Script Loads csv datasets from 2010-2020 on a State Level,
   cleans it and create a cleaned csv.
   '''
    _url = input_url(url_file, "2010-20")
    df = pd.read_csv(_url, encoding='ISO-8859-1')

    # Filter years 3 - 13.
    df.insert(2, 'geo_ID', 'geoId/', True)
    df['geo_ID'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(2)
    # Filtering the data needed.
    df = df.query("geo_ID !=0")
    df = df.query("ORIGIN ==0")
    # Replacing the Sex Numbers as per the metadata.
    df['SEX'] = df['SEX'].astype(str)
    df = df.replace({"SEX": {'0': 'Total', '1': 'Male', '2': 'Female'}})
    df['RACE'] = df['RACE'].astype(str)
    # Replacing the Race Numbers as per the metadata.
    df = df.replace({
        "RACE": {
            '1': 'WhiteAlone',
            '2': 'BlackOrAfricanAmericanAlone',
            '3': 'AmericanIndianAndAlaskaNativeAlone',
            '4': 'AsianAlone',
            '5': 'NativeHawaiianAndOtherPacificIslanderAlone',
            '6': 'TwoOrMoreRaces'
        }
    })
    df['AGE'] = df['AGE'].astype(str)
    df['AGE'] = df['AGE'] + 'Years'
    df['AGE'] = df['AGE'].str.replace("85Years", "85OrMoreYears")
    # Drop unwanted columns.
    df.drop(columns=['SUMLEV','REGION','DIVISION', 'STATE', 'NAME', 'ORIGIN',\
       'ESTIMATESBASE2010','CENSUS2010POP','POPESTIMATE042020'], inplace=True)
    df = df.melt(id_vars=['geo_ID','AGE','SEX','RACE'], var_name='Year' , \
       value_name='observation')
    # Making the years more understandable.
    df = df.replace({
        "Year": {
            'POPESTIMATE2010': '2010',
            'POPESTIMATE2011': '2011',
            'POPESTIMATE2012': '2012',
            'POPESTIMATE2013': '2013',
            'POPESTIMATE2014': '2014',
            'POPESTIMATE2015': '2015',
            'POPESTIMATE2016': '2016',
            'POPESTIMATE2017': '2017',
            'POPESTIMATE2018': '2018',
            'POPESTIMATE2019': '2019',
            'POPESTIMATE2020': '2020'
        }
    })
    df['SVs'] = 'Count_Person_' + df['AGE'] + '_' + df['SEX'] + '_' + df['RACE']
    df = df.drop(columns=['AGE', 'RACE', 'SEX'])
    # df_as is used to get aggregated data of age/sex.
    df_as = pd.DataFrame()
    df_as = pd.concat([df_as, df])
    df.insert(3, 'Measurement_Method', 'CensusPEPSurvey', True)
    df_as = df_as[~df_as["SVs"].str.contains("Total")]
    # DF sent to an external function for aggregation based on gender.
    df_as = gender_based_grouping(df_as)
    df['SVs'] = df['SVs'].str.replace('_Total', '')
    df = pd.concat([df, df_as])
    df.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder,
                     'state_2010_2020.csv'))
