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
This Python Script is for National Level Data 2000-2010.
'''
import os
import pandas as pd
from common_functions import input_url, race_based_grouping


def national2000(url_file: str, output_folder: str):
    '''
    This Python Script Loads csv datasets from 2000-2010 on a National Level,
    cleans it and create a cleaned csv.
    '''
    # Getting input URL from the JSON file.
    _url = input_url(url_file, "2000-10")
    # Reading the csv format input file and converting it to a dataframe.
    df = pd.read_csv(_url, encoding='ISO-8859-1', low_memory=False)
    # Removing the unwanted rows.
    # 4 removed as July month is being considered
    df = df.query("MONTH != 4")
    # 2010 is covered in another input function
    df = df.query("YEAR != 2010")
    # 999 denotes total age which is not being taken in ASR input
    df = df.query("AGE != 999")
    df['AGE'] = df['AGE'].astype(str)
    df['AGE'] = df['AGE'] + 'Years'
    df['AGE'] = df['AGE'].str.replace("85Years", "85OrMoreYears")
    # Dropping unwanted columns.
    df = df.drop(columns=[
        'TOT_POP', 'NH_MALE', 'NH_FEMALE', 'NHWA_MALE', 'MONTH', 'NHWA_FEMALE',
        'NHBA_MALE', 'NHBA_FEMALE', 'NHIA_MALE', 'NHIA_FEMALE', 'NHAA_MALE',
        'NHAA_FEMALE', 'NHNA_MALE', 'NHNA_FEMALE', 'NHTOM_MALE', 'NHTOM_FEMALE',
        'H_MALE', 'H_FEMALE', 'HWA_MALE', 'HWA_FEMALE', 'HBA_MALE',
        'HBA_FEMALE', 'HIA_MALE', 'HIA_FEMALE', 'HAA_MALE', 'HAA_FEMALE',
        'HNA_MALE', 'HNA_FEMALE', 'HTOM_MALE', 'HTOM_FEMALE'
    ])
    # Melt funtion used to change the Data frame format from wide to long.
    df['Year'] = df['YEAR']
    df.drop(columns=['YEAR'], inplace=True)
    df = df.melt(id_vars=['Year','AGE'], var_name='sv' ,\
        value_name='observation')
    # Providing proper columns names.
    df = df.replace({
        "sv": {
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
    })
    # Giving proper column names.
    df['SVs'] = 'Count_Person_' + df['AGE'] + '_' + df['sv']
    df = df.drop(columns=['AGE', 'sv'])
    # Inserting geoId to the dataframe.
    df.insert(1, 'geo_ID', 'country/USA', True)
    # Inserting measurement method to the dataframe.
    df.insert(3, 'Measurement_Method', 'CensusPEPSurvey', True)
    # Contains aggregated data for age and race.
    df_ar = pd.DataFrame()
    df_ar = pd.concat([df_ar, df])
    # DF sent to an external function for aggregation based on race.
    df_ar = race_based_grouping(df_ar)
    df_ar.insert(3, 'Measurement_Method', 'dcAggregate/CensusPEPSurvey', True)
    df_ar = df_ar[df_ar.SVs.str.contains('Years_')]
    df = pd.concat([df_ar, df])
    # Writing the dataframe to output csv.
    df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           output_folder, 'national_2000_2010.csv'),
              index=False)
