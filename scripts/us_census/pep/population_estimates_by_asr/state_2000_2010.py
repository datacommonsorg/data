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
This Python Script is for State Level Data 2000-2010
'''
import os
import pandas as pd
from common_functions import input_url, replace_agegrp


def state2000(url_file: str, output_folder: str):
    '''
    This Python Script Loads csv datasets from 2000-2010 on a State Level,
    cleans it and create a cleaned csv
    '''
    _url = input_url(url_file, "2000-10")
    df = pd.read_csv(_url, encoding='ISO-8859-1')
    # Filtering the data needed.
    df.drop(df[(df['RACE'] == 0) & (df['SEX'] == 0)].index, inplace=True)
    df = df.query("STATE != 0")
    df = df.query("AGEGRP != 0")
    df = df.query("ORIGIN == 0")
    df.insert(7, 'geo_ID', 'geoId/', True)
    df['geo_ID'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(2)
    # Replacing the Sex Numbers as per the metadata.
    df['SEX'] = df['SEX'].astype(str)
    df = df.replace({"SEX": {'0': 'Total', '1': 'Male', '2': 'Female'}})
    # Replacing the Race Numbers as per the metadata.
    df['RACE'] = df['RACE'].astype(str)

    df = df.replace({
        "RACE": {
            '0': 'Total',
            '1': 'WhiteAlone',
            '2': 'BlackOrAfricanAmericanAlone',
            '3': 'AmericanIndianAndAlaskaNativeAlone',
            '4': 'AsianAlone',
            '5': 'NativeHawaiianAndOtherPacificIslanderAlone',
            '6': 'TwoOrMoreRaces'
        }
    })
    # Replacing the Age group Numbers as per the metadata.
    df['AGEGRP'] = df['AGEGRP'].astype(str)
    # Code 0 is sent if AGEGRP starts from 0 and 1 if it starts from 0To4
    df = replace_agegrp(df, 1)
    # Dropping unwanted columns.
    df.drop(columns=['REGION','DIVISION', 'STATE', 'NAME', 'ORIGIN',\
            'ESTIMATESBASE2000','CENSUS2010POP','POPESTIMATE2010'],\
            inplace=True)
    df = df.melt(id_vars=['geo_ID','AGEGRP','SEX','RACE'], var_name='Year'\
            ,value_name='observation')
    # Making the years more understandable.
    df = df.replace({
        "Year": {
            'POPESTIMATE2000': '2000',
            'POPESTIMATE2001': '2001',
            'POPESTIMATE2002': '2002',
            'POPESTIMATE2003': '2003',
            'POPESTIMATE2004': '2004',
            'POPESTIMATE2005': '2005',
            'POPESTIMATE2006': '2006',
            'POPESTIMATE2007': '2007',
            'POPESTIMATE2008': '2008',
            'POPESTIMATE2009': '2009'
        }
    })
    df['SVs'] = 'Count_Person_' + df['AGEGRP'] + '_' + df['SEX'] + '_' + \
            df['RACE']
    df = df.drop(columns=['AGEGRP', 'RACE', 'SEX'])
    df.insert(3, 'Measurement_Method', 'CensusPEPSurvey', True)
    df['SVs'] = df['SVs'].str.replace('_Total', '')
    df.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder,
                     'state_2000_2010.csv'))
