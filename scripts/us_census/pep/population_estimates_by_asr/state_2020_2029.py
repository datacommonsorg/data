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
This Python Script is for State Level Data 2020-2029.
'''
import os
import pandas as pd
from common_functions import input_url, gender_based_grouping, extract_year


def state2029(url_file: str, output_folder: str):
    '''
   This Python Script Loads csv datasets from 2020-2029 on a State Level,
   cleans it and create a cleaned csv.
   '''
    df = pd.read_csv(url_file, encoding='ISO-8859-1')
    #Writing raw data to csv
    df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "raw_data", 'raw_data_state_2020_2029.csv'),
              index=False)
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

    pop_estimate_cols = [
        col for col in df.columns if col.startswith('POPESTIMATE')
    ]
    df = df.drop(
        columns=df.columns.difference(['geo_ID', 'AGE', 'SEX', 'RACE'] +
                                      pop_estimate_cols))
    df = df.melt(id_vars=['geo_ID','AGE','SEX','RACE'], var_name='Year' , \
       value_name='observation')
    # Making the years more understandable.
    df['Year'] = df['Year'].apply(extract_year)
    df['SVs'] = 'Count_Person_' + df['AGE'] + '_' + df['SEX'] + '_' + df['RACE']

    # df_as is used to get aggregated data of age/sex.
    df.insert(3, 'Measurement_Method', 'CensusPEPSurvey', True)
    df = df.drop(columns=['AGE', 'SEX', 'RACE'])
    df_as = pd.DataFrame()
    df_as = pd.concat([df_as, df])
    df_as = df_as[~df_as["SVs"].str.contains("Total")]

    # DF sent to an external function for aggregation based on gender.
    df_as = gender_based_grouping(df_as)
    df['SVs'] = df['SVs'].str.replace('_Total', '')
    df = pd.concat([df, df_as])
    df.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder,
                     'state_2020_2029.csv'))
