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
This Python Script is for County Level Data 2010-2020.
'''
import os
import numpy as np
import pandas as pd
from common_functions import input_url, replace_agegrp


def county2010(url_file: str, output_folder: str):
    '''
    This Python Script Loads csv datasets from 2010-2020 on a County Level,
    cleans it and create a cleaned csv.
    '''
    _url = input_url(url_file, "2010-20")
    df = pd.read_csv(_url, encoding='ISO-8859-1', low_memory=False)
    # Filter by agegrp = 0.
    df = df.query("YEAR not in [1, 2, 13]")
    df = df.query("AGEGRP != 0")
    # Filter years 3 - 14.
    df['YEAR'] = df['YEAR'].astype(str)
    df = df.replace({
        'YEAR': {
            '3': '2010',
            '4': '2011',
            '5': '2012',
            '6': '2013',
            '7': '2014',
            '8': '2015',
            '9': '2016',
            '10': '2017',
            '11': '2018',
            '12': '2019',
            '14': '2020'
        }
    })
    df.insert(6, 'geo_ID', 'geoId/', True)
    df['geo_ID'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(2) + \
        (df['COUNTY'].map(str)).str.zfill(3)
    df['AGEGRP'] = df['AGEGRP'].astype(str)
    # Replacing the numbers with more understandable metadata headings.
    # Code 0 is sent if AGEGRP starts from 0 and 1 if it starts from 0To4
    df = replace_agegrp(df, 1)
    # Drop unwanted columns.
    df.drop(columns=['SUMLEV', 'STATE', 'COUNTY', 'STNAME', 'CTYNAME'], \
        inplace=True)
    df = df.drop(columns=[
        'TOT_POP', 'NH_MALE', 'NH_FEMALE', 'NHWA_MALE', 'NHWA_FEMALE',
        'NHBA_MALE', 'NHBA_FEMALE', 'NHIA_MALE', 'NHIA_FEMALE', 'NHAA_MALE',
        'NHAA_FEMALE', 'NHNA_MALE', 'NHNA_FEMALE', 'NHTOM_MALE', 'NHTOM_FEMALE',
        'H_MALE', 'H_FEMALE', 'HWA_MALE', 'HWA_FEMALE', 'HBA_MALE',
        'HBA_FEMALE', 'HIA_MALE', 'HIA_FEMALE', 'HAA_MALE', 'HAA_FEMALE',
        'HNA_MALE', 'HNA_FEMALE', 'HTOM_MALE', 'HTOM_FEMALE'
    ])
    df['Year'] = df['YEAR']
    df.drop(columns=['YEAR'], inplace=True)
    df['WhiteAloneAgg'] = df['WA_MALE'].astype(int) + df['WA_FEMALE'].astype(
        int)
    df['BlackOrAfricanAmericanAlone'] = df['BA_MALE'].astype(int)\
        +df['BA_FEMALE'].astype(int)
    df['AmericanIndianAndAlaskaNativeAlone'] = df['IA_MALE'].astype(int)\
        +df['IA_FEMALE'].astype(int)
    df['AsianAloneAgg'] = df['AA_MALE'].astype(int) + df['AA_FEMALE'].astype(
        int)
    df['NativeHawaiianAndOtherPacificIslanderAloneAgg'] = df['NA_MALE']\
        .astype(int)+df['NA_FEMALE'].astype(int)
    df['TwoOrMoreRacesAgg'] = df['TOM_MALE'].astype(int)+\
        df['TOM_FEMALE'].astype(int)
    df = df.melt(id_vars=['Year','geo_ID' ,'AGEGRP'], var_name='sv' , \
        value_name='observation')
    # Changing Names to be more understandable.
    _sexrace_dict = {
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
    df = df.replace({"sv": _sexrace_dict})
    df['SVs'] = 'Count_Person_' + df['AGEGRP'] + '_' + df['sv']
    df = df.drop(columns=['AGEGRP', 'sv'])
    df['Measurement_Method'] = np.where(df['SVs'].str.contains('Agg')\
        , 'dcAggregate/CensusPEPSurvey', 'CensusPEPSurvey')
    df['SVs'] = df['SVs'].str.replace('Agg', '')
    # Write to final file.
    df.to_csv(
        os.path.join(os.path.dirname(
        os.path.abspath(__file__)), output_folder,'county_2010_2020.csv'),\
        index=False)
