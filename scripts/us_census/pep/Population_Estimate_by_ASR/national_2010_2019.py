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


def national2010(url_file: str, output_folder: str):
    '''
    This Python Script Loads csv datasets from 2010-2019 on a National Level,
    cleans it and create a cleaned csv.
    '''
    # Getting input URL from the JSON file.
    _urls = input_url(url_file, "2010-19")
    _sheets = input_url(url_file, "2010-19sheets")
    # Used to collect data after every loop for every file's df.
    df_final = pd.DataFrame()
    for sheet in _sheets:
        df_sheet = pd.DataFrame()
        df = pd.read_excel(_urls, sheet, skiprows=4, header=0)
        # Dropping extra columns
        df = df.drop(['Census', 'Estimates Base'], axis=1)
        # Deleting the row with garbage information , 0 denotes the row
        df = df.drop([0], axis=0)
        # Cleaning the data to
        df['Unnamed: 0'] = df['Unnamed: 0'].str.replace(".", "").str.replace\
            ("Under 5", "0 to 4").str.replace(" ", "").str.replace("to", "To")\
            .str.replace("years", "Years").str.replace("85Yearsandover", \
            "85OrMoreYears")
        # Due to data being in a different format for male/female, and also
        # required some extra processing. So, it has been put into other dfs
        # df_sex(has data to be processed by gender),
        # df_sheet(has data of a single sheet in excel) so it can be processed
        # seperately before being put into our main df.
        # 0 to 18 are the total values to be picked.
        # 36 to 54 are the male values to be picked.
        # 72 to 90 are the female values to be picked.
        if sheet != 'Total':
            df_sex = df[0:18]
            df_sheet = pd.concat([df_sheet, df_sex])
        df_sex = df[36:54]
        df_sex['Unnamed: 0'] = df_sex['Unnamed: 0'] + '_Male'
        df_sheet = pd.concat([df_sheet, df_sex])
        df_sex = df[72:90]
        df_sex['Unnamed: 0'] = df_sex['Unnamed: 0'] + '_Female'
        df_sheet = pd.concat([df_sheet, df_sex])
        df_sheet['Unnamed: 0'] = df_sheet['Unnamed: 0'] + '_' + sheet + 'Alone'
        df_sheet = df_sheet.melt(id_vars=['Unnamed: 0'],
                                 var_name='Year',
                                 value_name='observation')
        df_sheet.columns = df_sheet.columns.str.replace('Unnamed: 0', 'SVs')
        df_final = pd.concat([df_final, df_sheet])
    df_final['SVs'] = (df_final['SVs'].str.replace(
        "_TotalAlone",
        "").str.replace("Black", "BlackOrAfricanAmerican").str.replace(
            "AIAN", "AmericanIndianAndAlaskaNative").str.replace(
                "NHPI", "NativeHawaiianAndOtherPacificIslander").str.replace(
                    "Two or More RacesAlone", "TwoOrMoreRaces"))
    df_final['SVs'] = 'Count_Person_' + df_final['SVs']
    df_final['Measurement_Method'] = 'CensusPEPSurvey'
    df_final['geo_ID'] = 'country/USA'
    df_final.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder,
                     'national_2010_2019.csv'))
