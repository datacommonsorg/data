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
This Python Script is for National Level Data 1980-1989.
'''
import os
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
import pandas as pd
import numpy as np
from common_functions import input_url


def column_naming(df: pd.DataFrame):
    '''
    Provides appropriate names to df columns.
    '''
    df['Year'] = "19" + df['1'].str[1:3]
    df['Age'] = df['2'].astype(float).astype(int)
    df['Male'] = df['4']
    df['Female'] = df['5']
    df['WhiteAggrAll'] = df['6'] + df['7']
    df['Male_WhiteAll'] = df['6']
    df['Female_WhiteAll'] = df['7']
    df['BlackOrAfricanAmericanAggrAll'] = df['8'] + df['9']
    df['Male_BlackOrAfricanAmericanAll'] = df['8']
    df['Female_BlackOrAfricanAmericanAll'] = df['9']
    df['AmericanIndianAndAlaskaNativeAggrAll'] = df['10'] + df['11']
    df['Male_AmericanIndianAndAlaskaNativeAll'] = df['10']
    df['Female_AmericanIndianAndAlaskaNativeAll'] = df['11']
    df['AsianOrPacificIslanderAggr'] = df['12'] + df['13']
    df['Male_AsianOrPacificIslander'] = df['12']
    df['Female_AsianOrPacificIslander'] = df['13']
    df = df.drop([
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
        "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23"
    ],
                 axis=1)
    return df


def national1980(url_file: str, output_folder: str):
    '''
    This Python Script Loads csv datasets from 1980-1989 on a National Level,
    cleans it and create a cleaned csv.
    '''
    # Getting list of URLs from JSON file.
    _ZIP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'Zip1980-90')
    _urls = input_url(url_file, "1980-90")

    # Creation of a folder if it does not exist.
    if not os.path.exists(_ZIP_DIR):
        os.mkdir(_ZIP_DIR)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(_ZIP_DIR)

    # Extraction of ZIP files.
    for url in _urls:
        with urlopen(url) as resp:
            # unzipping the dataset
            with ZipFile(BytesIO(resp.read()), 'r') as zipfile:
                zipfile.extractall()
    _urls = _urls = input_url(url_file, "1980-90files")

    cols = ["0", "1", "2", "3", "4", "5", "6", "7",\
                        "8", "9", "10", "11","12", "13", "14", "15",\
                        "16", "17", "18", "19", "20", "21", "22"]
    # Used to collect data after every loop for every file's df.
    final_df = pd.DataFrame()

    for file in _urls:

        # Reading the txt format input file converting it to a dataframe.
        # Delimitng the columns by whitespace.
        df = pd.read_table(file,
                           index_col=False,
                           delim_whitespace=True,
                           engine='python',
                           names=cols)
        df = df.loc[df['0'].isin(['2I', '9P'])]
        df['1'] = df['1'].astype(str)
        # Divinding rows with 100 and others to make the format similar
        # rows with 100 have a different format.
        df1 = df[df['1'].str.contains("100")]
        # Removing rows with 999 as they denote total age,
        # which is not needed in ASR
        df = df[~df['1'].str.contains("999")]
        df = df[~df['1'].str.contains("100")]
        # Making the columns shift one place left for df1 which has 100 year,
        # different format data
        for i in range(22, 1, -1):
            j = i + 1
            i = str(i)
            j = str(j)
            df1[j] = df1[i]
            i = int(i)
        # Dividing the 1 column into multiple parts as the basic information
        # and year is combined for age 100 and need to be sepreated
        df1['2'] = df1['1'].str[-5:]
        df1['1'] = df1['1'].str[:-5]
        df = pd.concat([df, df1])
        # Using data from July, hence number 7
        df = df.loc[df['1'].str[0] == '7']
        df = column_naming(df)
        # Writing all the output to a final dataframe.
        df.columns = df.columns.str.replace('All', \
            'Alone')
        df = df.melt(id_vars=['Year', 'Age'],
                     var_name='SVs',
                     value_name='observation')
        df['Age'] = df['Age'].astype(str)
        df['Age'] = df['Age'] + 'Years'
        df['SVs'] = 'Count_Person_' + df['Age'] + '_' + df['SVs']
        df.drop(columns=['Age'], inplace=True)
        df['Measurement_Method'] = np.where(df['SVs'].str.contains("Aggr"), \
            'dcAggregate/CensusPEPSurvey', 'CensusPEPSurvey')
        df['SVs'] = df['SVs'].str.replace('Aggr', '')
        final_df = pd.concat([final_df, df])

    final_df['geo_ID'] = 'country/USA'
    final_df.to_csv(
        os.path.join(current_dir, output_folder, 'national_1980_1990.csv'))
