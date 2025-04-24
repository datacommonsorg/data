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
This Python Script is for National Level Data 2020-2029.
'''
import os
import pandas as pd
import requests
from common_functions import input_url, extract_year


def national2029(url_file: str, output_folder: str):
    '''
    This Python Script Loads csv datasets from 2020-2029 on a National Level,
    cleans it and create a cleaned csv.
    '''
    # Getting input URL from the JSON file.
    print("url_file", url_file)
    filename = 'raw_data_national_2020_2029.csv'
    raw_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "raw_data")
    file_path = os.path.join(raw_data_dir, filename)
    os.makedirs(raw_data_dir, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url_file, headers=headers)
    if response.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(response.content)
        df = pd.read_csv(file_path,
                         engine='python',
                         header=0,
                         encoding='ISO-8859-1')
        #Writing raw data to csv
        df.to_csv(file_path, index=False)
    df.drop(df[(df['SEX'] == 0) | (df['AGE'] == 999)].index, inplace=True)
    df = df.replace({'SEX': {2: 'Female', 1: 'Male'}})
    pop_estimate_cols = [
        col for col in df.columns if col.startswith('POPESTIMATE')
    ]
    df = df.drop(
        columns=df.columns.difference(['geo_ID', 'AGE', 'SEX', 'RACE'] +
                                      pop_estimate_cols))
    df['SVs'] = "Count_Person_" + df['AGE'].astype(str) + "Years_" + df['SEX']
    df.drop(columns=['AGE', 'SEX'], inplace=True)
    df = df.melt(id_vars=['SVs'], var_name='Year', value_name='observation')
    df['Year'] = df['Year'].apply(extract_year)
    df['Measurement_Method'] = 'CensusPEPSurvey'
    df['geo_ID'] = 'country/USA'

    df.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder,
                     'national_2020_2029.csv'))
