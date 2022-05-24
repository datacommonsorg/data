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
This Python Script is for
for National Level Data
2000-2010
'''
import json
import os
import pandas as pd


def national2000():
    '''
    This Python Script Loads csv datasets
    from 2000-2010 on a National Level,
    cleans it and create a cleaned csv
    '''
    _URLS_JSON_PATH = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + 'National.json'
    _URLS_JSON = None
    with open(_URLS_JSON_PATH, encoding="UTF-8") as file:
        _URLS_JSON = json.load(file)
    _url = _URLS_JSON["2000-10"]
    # reading the csv format input file and converting it to a dataframe
    df = pd.read_csv(_url, encoding='ISO-8859-1', low_memory=False)
    # removing the unwanted rows
    df = df.query("MONTH != 4")
    df = df.query("YEAR != 2010")
    df = df.query("AGE != 999")
    df['AGE'] = df['AGE'].astype(str)
    df['AGE'] = df['AGE'] + 'Years'
    df['AGE'] = df['AGE'].str.replace("85Years", "85OrMoreYears")
    # dropping unwanted columns
    df = df.drop(columns=[
        'TOT_POP', 'NH_MALE', 'NH_FEMALE', 'NHWA_MALE', 'MONTH', 'NHWA_FEMALE',
        'NHBA_MALE', 'NHBA_FEMALE', 'NHIA_MALE', 'NHIA_FEMALE', 'NHAA_MALE',
        'NHAA_FEMALE', 'NHNA_MALE', 'NHNA_FEMALE', 'NHTOM_MALE', 'NHTOM_FEMALE',
        'H_MALE', 'H_FEMALE', 'HWA_MALE', 'HWA_FEMALE', 'HBA_MALE',
        'HBA_FEMALE', 'HIA_MALE', 'HIA_FEMALE', 'HAA_MALE', 'HAA_FEMALE',
        'HNA_MALE', 'HNA_FEMALE', 'HTOM_MALE', 'HTOM_FEMALE'
    ])
    # melt funtion used to change the Data frame format from wide to long
    df['Year'] = df['YEAR']
    df.drop(columns=['YEAR'], inplace=True)
    df = df.melt(id_vars=['Year','AGE'], var_name='sv' ,\
        value_name='observation')
    # Providing proper columns names
    _dict = {
        'TOT_MALE': 'Male',
        'TOT_FEMALE': 'Female',
        'WA_MALE': 'Male_WhiteAlone',
        'WA_FEMALE': 'Female_WhiteAlone',
        'BA_MALE': 'Male_BlackOrAfricanAmericanAlone',
        'BA_FEMALE': 'Female_BlackOrAfricanAmericanAlone',
        'IA_MALE': 'Male_AmericanIndianAndAlaskaNativeAlone',
        'IA_FEMALE': 'Female_AmericanIndianAndAlaskaNativeAlone',
        'AA_MALE': 'Male_AsianAlone',
        'AA_FEMALE': 'Female_AsianAlone',
        'NA_MALE': 'Male_NativeHawaiianAndOtherPacificIslanderAlone',
        'NA_FEMALE': 'Female_NativeHawaiianAndOtherPacificIslanderAlone',
        'TOM_MALE': 'Male_TwoOrMoreRaces',
        'TOM_FEMALE': 'Female_TwoOrMoreRaces'
    }
    df = df.replace({"sv": _dict})
    # giving proper column names
    df['SVs'] = 'Count_Person_' + df['AGE'] + '_' + df['sv']
    df = df.drop(columns=['AGE', 'sv'])
    # inserting geoId to the dataframe
    df.insert(1, 'geo_ID', 'country/USA', True)
    # inserting measurement method to the dataframe
    df.insert(3, 'Measurement_Method', 'CensusPEPSurvey', True)
    df_temp = pd.DataFrame()
    df_temp = pd.concat([df_temp, df])
    df_temp['SVs'] = df_temp['SVs'].str.replace('_Male', '')
    df_temp['SVs'] = df_temp['SVs'].str.replace('_Female', '')
    df_temp = df_temp.groupby(['Year', 'geo_ID', 'SVs']).sum().reset_index()
    df_temp.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    df_temp = df_temp[df_temp.SVs.str.contains('Years_')]
    df = pd.concat([df_temp, df])
    # writing the dataframe to output csv
    df.to_csv(os.path.dirname(
        os.path.abspath(__file__)) + os.sep +\
        'input_data/national_2000_2010.csv',index=False)
