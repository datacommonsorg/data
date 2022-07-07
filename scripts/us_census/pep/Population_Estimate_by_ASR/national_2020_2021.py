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
This Python Script is for National Level Data 2010-2019.
'''
import os
import pandas as pd
from common_functions import input_url


def national2020(url_file: str, output_folder: str):
    '''
    This Python Script Loads csv datasets from 2010-2019 on a National Level,
    cleans it and create a cleaned csv.
    '''
    # Getting input URL from the JSON file.
    _url = input_url(url_file, "2020-21")
    df = pd.read_csv(_url, header=0)
    df.drop(df[(df['SEX'] == 0) | (df['AGE'] == 999)].index, inplace=True)
    df = df.replace({'SEX': {2: 'Female', 1: 'Male'}})
    df.rename(columns={
        'POPESTIMATE2020': '2020',
        'POPESTIMATE2021': '2021'
    },
              inplace=True)
    df['SVs'] = "Count_Person_" + df['AGE'].astype(str) + "Years_" + df['SEX']
    df.drop(columns=['SEX', 'AGE', 'ESTIMATESBASE2020'], inplace=True)
    df = df.melt(id_vars=['SVs'], var_name='Year', value_name='observation')
    df['Measurement_Method'] = 'CensusPEPSurvey'
    df['geo_ID'] = 'country/USA'
    df.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder,
                     'national_2020_2021.csv'))
