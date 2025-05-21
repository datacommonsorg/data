# Copyright 2024 Google LLC
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
""" A Script to process USA Census PEP monthly population data
    from the datasets in provided local path.
    Typical usage:
    1. python3 preprocess.py
       "only download" run the below command:
    2. python3 preprocess.py --mode=download
       "only process", run the below command:
    3. python3 preprocess.py --mode=process

"""

import os
import re
import sys
import requests
import time
import json
from datetime import datetime as dt
from absl import logging
from io import StringIO
# To import util.alpha2_to_dcid
_COMMON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(1, _COMMON_PATH)
import warnings

warnings.filterwarnings('ignore')

import pandas as pd
from absl import app
from absl import flags
from util.alpha2_to_dcid import USSTATE_MAP
from states_to_shortform import get_states

#pd.options.mode.copy_on_write = True

_FLAGS = flags.FLAGS
flags.DEFINE_string('mode', '', 'Options: download or process')
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = os.path.join(_MODULE_DIR, 'input_files')

default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_files"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")
_FILES_TO_DOWNLOAD = None


# Generating geoID by taking Geographical area as input
def _add_geo_id(df: pd.DataFrame) -> pd.DataFrame:
    short_forms = get_states()
    df['Short_Form'] = df['Geographic Area'].str.title()
    df['Short_Form'] = df['Short_Form'].str.replace(" ", "").replace(",", "").\
        apply(lambda row: short_forms.get(row, row))
    USSTATE_MAP.update({'US': 'country/USA'})
    df['geo_ID'] = df['Short_Form'].apply(
        lambda rec: USSTATE_MAP.get(rec, pd.NA))
    df = df.dropna(subset=['Geographic Area'])
    return df


def _clean_xls_file(df: pd.DataFrame, file: str) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a xls file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of xls dataset
        file: str : String of Dataset File Path
    Returns:
        df (DataFrame) : Transformed DataFrame for xls dataset.
     According to dataset, origin=0, sex=0
     considered as they hold the total value.
    """
    if "2020" in file:
        # "2020" refers to the file name: "CC-EST2020" which carries a different
        # format hence, extra rows/columns needed to be dropped from the file.
        df.drop(df[df['ORIGIN'] != 0].index, inplace=True)
        df.drop(df[df['SEX'] != 0].index, inplace=True)
        df = df.drop(['STATE','DIVISION','SUMLEV','SEX','ORIGIN'\
            ,'AGE','REGION','ESTIMATESBASE2010','CENSUS2010POP'\
            ,'POPESTIMATE042020'],axis=1)
    else:
        df = df.drop(['STATE','DIVISION','REGION','ESTIMATESBASE2000',\
            'CENSUS2010POP','POPESTIMATE2010'],axis=1)
    df = df.groupby(['NAME', 'RACE']).sum().transpose().stack(0).reset_index()
    if "2020" in file:
        df[0] = df[1] + df[2] + df[3] + df[4] + df[5] + df[6]
    df['Total'] = df[0]
    df['White Alone'] = df[1]
    df['Black or African American Alone'] = df[2]
    df['American Indian or Alaska Native Alone'] = df[3]
    df['Asian Alone'] = df[4]
    df['Native Hawaiian and Other Pacific Islander Alone'] = df[5]
    df['Two or more Races'] = df[6]
    df['Year'] = df['level_0'].str[-4:]
    df = df.drop(['level_0', 0, 1, 2, 3, 4, 5, 6], axis=1)
    df.columns = df.columns.str.replace('NAME', 'Geographic Area')
    return df


def _clean_xlsx_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a xls file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of xls dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for xls dataset.
    """
    df = df.drop(['Census', 'Estimates Base'], axis=1)
    df = df.drop([1], axis=0)
    df.drop(df.index[7:], inplace=True)
    df['Unnamed: 0'] = df['Unnamed: 0'].str.replace(".", "")
    df['Geographic Area'] = 'United States'

    # it groups the df as per columns provided
    # performs the provided functions on the data
    df = df.groupby(['Geographic Area','Unnamed: 0']).sum()\
        .transpose().stack(0).reset_index()
    df.columns = df.columns.str.replace('level_0', 'Year')
    df.columns = df.columns.str.replace('White', 'White Alone')
    df.columns = df.columns.str.replace('TOTAL POPULATION', 'Total')
    df.columns = df.columns.str.replace('Black or African American', \
        'Black or African American Alone')
    df.columns = df.columns.str.replace(
        'Native Hawaiian and Other Pacific Islander'\
        , 'Native Hawaiian and Other Pacific Islander Alone')
    df.columns = df.columns.str.replace(
        'American Indian and Alaska Native'\
        , 'American Indian or Alaska Native Alone')
    df.columns = df.columns.str.replace('Asian', 'Asian Alone')

    df['Total'] = pd.to_numeric(df['Total'])
    return df


def _clean_county_70_xls_file(df: pd.DataFrame, file_path: str) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a xls file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of xls dataset
        file_path (str) : File path of csv dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for xls dataset.
    """
    try:
        df['Total People'] = 0
        for i in range(1, 19):
            df['Total People'] = df['Total People'] + df[i]
        df['FIPS'] = [f'{x:05}' for x in df['FIPS']]
        df['Info'] = df['Year'].astype(str) + '-' + df['FIPS'].astype(str)
        df.drop(columns=['Year','FIPS',1,2,3,4,5,6,7,8,9,10,11,12,\
            13,14,15,16,17,18],inplace=True)
        df = df.groupby(['Info','Race/Sex']).sum().transpose().\
            stack(0).reset_index()
        df['Year'] = df['Info'].str.split('-', expand=True)[0]
        df['geo_ID'] = "geoId/" + df['Info'].str.split('-', expand=True)[1]
        df['Total'] = df[1] + df[2] + df[3] + df[4] + df[5] + df[6]
        df['White Alone'] = df[1] + df[2]
        df['Black or African American Alone'] = df[3] + df[4]
        df.drop(columns=['Info', 'level_0', 1, 2, 3, 4, 5, 6], inplace=True)
    except Exception as e:
        logging.fatal(
            f"error in the method clean_county_70_xls_file,{file_path} -{e}")
    return df


def _clean_county_80_xls_file(df: pd.DataFrame, file_path: str) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a xls file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of xls dataset
        file_path: str : This file path location
    Returns:
        df (DataFrame) : Transformed DataFrame for xls dataset.
    """
    # All the Column values are summed up to derive Total Population Value
    # {"1":"0-4 year olds", "2":"5-9 year olds", "3":"10-14 year olds",
    # "4":"15-19 year olds","5":"20-24 year olds","6":"25-29 year olds",
    # "7":"30-34 year olds","8":"35-39 year olds","9":"40-44 year olds",
    # "10":"45-49 year olds","11":"50-54 year olds","12":"55-59 year olds",
    # "13":"60-64 year olds","14":"65-69 year olds","15":"0-74 year olds",
    # "16":"75-79 year olds","17":"80-84 year olds","18":"85 years old and older"}
    try:
        df['Total People']=df[1]+df[2]+df[3]+df[4]+df[5]+df[6]+df[7]+\
            df[8]+df[9]+df[10]+df[11]+df[12]+df[13]+df[14]+df[15]+\
            df[16]+df[17]+df[18]
        df['FIPS'] = [f'{x:05}' for x in df['FIPS']]
        df['Info'] = df['Year'].astype(str) + '-' + df['FIPS'].astype(str)
        df.drop(columns=['Year','FIPS',1,2,3,4,5,6,7,8,9,10,11,12,13,14\
            ,15,16,17,18],inplace=True)
        df = df.groupby(['Info','Race/Sex']).sum().transpose().\
            stack(0).reset_index()
        df['Year'] = df['Info'].str.split('-', expand=True)[0]
        df['geo_ID'] = "geoId/" + df['Info'].str.split('-', expand=True)[1]
        # Deriving the total values as per the requires SV's
        df['Total']=df['White male']+df['White female']+df['Black male']\
            +df['Black female']+df['Other races male']+df['Other races female']
        df['White Alone'] = df['White male'] + df['White female']
        df['Black or African American Alone'] = df['Black male'] + \
            df['Black female']
        df.drop(columns=['Info','level_0','White male','White female','Black male'\
            ,'Black female','Other races male','Other races female'],inplace=True)
        final_df = pd.DataFrame()
        final_df = pd.concat([final_df, df])
        df['geo_ID'] = df['geo_ID'].str[:-3]
        df = df.groupby(['Year','geo_ID']).sum().\
            reset_index()
        df.drop(columns=['Total'], inplace=True)
        df_temp = pd.DataFrame()
        df_temp = pd.concat([df, df_temp])
        df_temp['geo_ID'] = "country/USA"
        df_temp = df_temp.groupby(['Year','geo_ID']).sum().\
            reset_index()
        final_df = pd.concat([final_df, df, df_temp])
        final_df = final_df.drop_duplicates()

    except Exception as e:

        logging.fatal(
            f"error in the method clean_county_80_xls_file,{file_path} -{e}")
    return final_df


def _clean_xls2_file(df: pd.DataFrame, file_path: str) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a xls file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of xls dataset
        file_path:str: File path to be processed

    Returns:
        df (DataFrame) : Transformed DataFrame for xls dataset.
    """
    try:
        df['Race'] = (df['Race/Sex Indicator'].str.replace(" female", ""))
        df['Race'] = (df['Race'].str.replace(" male", ""))
        df = df.drop(['Race/Sex Indicator'], axis=1)
        for col in df.columns:
            df[col] = df[col].astype(str)
            df[col] = df[col].str.replace(",", "")
        extras = ['Year of Estimate', 'FIPS State Code', 'State Name', 'Race']
        cols = df.columns.drop(extras)
        df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
        # All the age groups are being added up to get total value.
        age_list = [
            'Under 5 years', '5 to 9 years', '10 to 14 years', '15 to 19 years',
            '20 to 24 years', '25 to 29 years', '30 to 34 years',
            '35 to 39 years', '40 to 44 years', '45 to 49 years',
            '50 to 54 years', '55 to 59 years', '60 to 64 years',
            '65 to 69 years', '70 to 74 years', '75 to 79 years',
            '80 to 84 years', '85 years and over'
        ]

        df['count'] = 0
        for i in age_list:
            df['count'] = df['count'] + df[i]
        df = df.drop(age_list, axis=1)
        df['locationyear'] = df['Year of Estimate'] + "-" + df['State Name']
        df = df.drop(['Year of Estimate', 'State Name'], axis=1)
        # it groups the df as per columns provided
        # performs the provided functions on the data
        # The rows and columns have been transposed as per requirements
        df = df.groupby(['locationyear','Race']).sum().transpose().\
            stack(0).reset_index()
        df['Year'] = df['locationyear'].str.split('-', expand=True)[0]
        df['Geographic Area'] = df['locationyear'].str.split('-',
                                                             expand=True)[1]
        df['Total'] = df["White"] + df["Black"] + df['Other races']
        df = df.drop(['locationyear', 'level_0', 'Other races'], axis=1)
        df.columns = df.columns.str.replace('White', 'White Alone')
        df.columns = df.columns.str.replace('Black',
                                            'Black or African American Alone')

    except Exception as e:
        logging.fatal(f"error in the method clean_xls2_file,{file_path} -{e}")

    return df


def _clean_csv_file(df: pd.DataFrame, file_path: str) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a csv file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of csv dataset
        file_path:str: File path to be processed
    Returns:
        df (DataFrame) : Transformed DataFrame for csv dataset.
    The values are comma seperated.
    Created columns as per the name and dropped the
    remaining columns.
    """
    try:
        for col in df.columns:
            df[col] = df[col].astype(str)
            df[col] = df[col].str.replace(",", "")
        df['Total'] = pd.to_numeric(df['1'])
        df['White Alone'] = pd.to_numeric(df['4'])
        col = df.columns
        if len(col) >= 15:
            df['Black or African American Alone'] = pd.to_numeric(df['7'])
            df = df.drop(["10", "11", "12"], axis=1)
        else:
            df['Non White'] = df['7']
        df = df.drop(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], axis=1)
    except Exception as e:
        logging.fatal(f"error in the method clean_csv_file,{file_path} -{e}")
    return df


def _clean_county_20_csv_file(file_path: str) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a csv file format.
    Also, Performs transformations on the data.

    Arguments:
        file_path (str) : File path of csv dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for csv dataset.
    
    The function _clean_county_29_csv_file cleans 56 county files 
    for the year range 2000-2010.
    """
    try:
        df = pd.read_csv(file_path, encoding="ISO-8859-1")
        final_cols = ["Year", "geo_ID", "Total","White Alone",\
            "Black or African American Alone",\
            "American Indian or Alaska Native Alone","Asian Alone",\
            "Native Hawaiian and Other Pacific Islander Alone",\
            "Two or more Races"]

        cols_dict = {
            "geo_ID": ["STATE", "COUNTY"],
            "Total": ["TOT_POP"],
            "White Alone": ["WA_MALE", "WA_FEMALE"],
            "Black or African American Alone": ["BA_MALE", "BA_FEMALE"],
            "American Indian or Alaska Native Alone": ["IA_MALE", "IA_FEMALE"],
            "Asian Alone": ["AA_MALE", "AA_FEMALE"],
            "Native Hawaiian and Other Pacific Islander Alone"\
            : ["NA_MALE", "NA_FEMALE"],
            "Two or more Races": ["TOM_MALE", "TOM_FEMALE"]
        }
        start_yr, skip_yr1, skip_yr2, age_grp, initial_yr = 2, 12, 13, 99, 1998
        df = df[(df["YEAR"] >= start_yr) & (df["YEAR"] != skip_yr1) & (df["YEAR"] \
            != skip_yr2) & (df["AGEGRP"] == age_grp) ].reset_index().\
            drop(columns=["index"])
        df["YEAR"] = df["YEAR"].replace(skip_yr1 + 1, skip_yr1)
        df["STATE"] = df["STATE"].astype('str').str.pad\
            (width=2, side="left", fillchar="0")
        df["COUNTY"] = df["COUNTY"].astype('str').str.pad\
            (width=3, side="left", fillchar="0")
        final_df = pd.DataFrame()
        for col in final_cols:
            if col == "Year":
                final_df[col] = initial_yr + df["YEAR"]
            elif col == "geo_ID":
                final_df[col] = "geoId/" + df["STATE"] + df["COUNTY"]
            else:
                final_df[col] = df.loc[:,
                                       cols_dict[col]].sum(axis=1).astype('int')
    except Exception as e:
        logging.fatal(
            f"error in the method clean_county_20_csv_file,{file_path} -{e}")
    return final_df


def _clean_county_2010_csv_file(df: pd.DataFrame,
                                file_path: str) -> pd.DataFrame:
    '''
    This Python Script Loads csv datasets
    from 2010-2020 on a County Level,
    cleans it and create a cleaned csv

    Arguments:
        df (DataFrame) : DataFrame of csv dataset
        file_path:str: File path to be processed
    Returns:
        df (DataFrame) : Transformed DataFrame for csv dataset.
    '''
    try:
        # filter by agegrp = 0
        df = df.query("YEAR not in [1, 2]")
        df = df.query("AGEGRP == 0")
        # filter years 3 - 14
        df['YEAR'] = df['YEAR'].astype(str)
        conversion_of_year_to_value = {
            '3': '2010',
            '4': '2011',
            '5': '2012',
            '6': '2013',
            '7': '2014',
            '8': '2015',
            '9': '2016',
            '10': '2017',
            '11': '2018',
            '12': '2019'
            #'13': '2020' - commented this line because 2020 data is avaliable in 2023 file
        }
        df = df.replace({'YEAR': conversion_of_year_to_value})
        df = df[df['YEAR'] != '13']
        df.insert(6, 'geo_ID', 'geoId/', True)
        df['geo_ID'] = 'geoId/' +(df['STATE'].map(str)).str.zfill(2) + \
            (df['COUNTY'].map(str)).str.zfill(3)
        df['AGEGRP'] = df['AGEGRP'].astype(str)
        # Replacing the numbers with more understandable metadata headings
        conversion_of_agebracket_to_value = {
            '1': '0To4Years',
            '2': '5To9Years',
            '3': '10To14Years',
            '4': '15To19Years',
            '5': '20To24Years',
            '6': '25To29Years',
            '7': '30To34Years',
            '8': '35To39Years',
            '9': '40To44Years',
            '10': '45To49Years',
            '11': '50To54Years',
            '12': '55To59Years',
            '13': '60To64Years',
            '14': '65To69Years',
            '15': '70To74Years',
            '16': '75To79Years',
            '17': '80To84Years',
            '18': '85OrMoreYears'
        }
        df = df.replace({"AGEGRP": conversion_of_agebracket_to_value})
        # drop unwanted columns
        df.drop(columns=['SUMLEV', 'STATE', 'COUNTY', 'STNAME', 'CTYNAME'], \
            inplace=True)
        df = df.loc[:, :'NAC_FEMALE']
        df['Year'] = df['YEAR']
        df.drop(columns=['YEAR'], inplace=True)
        df['WhiteAlone'] = df['WA_MALE'].astype(int) + df['WA_FEMALE'].astype(
            int)
        df['BlackOrAfricanAmericanAlone'] = df['BA_MALE'].astype(int)\
            +df['BA_FEMALE'].astype(int)
        df['AmericanIndianAndAlaskaNativeAlone'] = df['IA_MALE'].astype(int)\
            +df['IA_FEMALE'].astype(int)
        df['AsianAlone'] = df['AA_MALE'].astype(int) + df['AA_FEMALE'].astype(
            int)
        df['NativeHawaiianAndOtherPacificIslanderAlone'] = df['NA_MALE']\
            .astype(int)+df['NA_FEMALE'].astype(int)
        df['TwoOrMoreRaces'] = df['TOM_MALE'].astype(int)+\
            df['TOM_FEMALE'].astype(int)
        df['WhiteAloneOrInCombinationWithOneOrMoreOtherRaces'] = df['WAC_MALE']\
            .astype(int)+ df['WAC_FEMALE'].astype(int)
        df['BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces']\
            = df['BAC_MALE'].astype(int)+df['BAC_FEMALE'].astype(int)
        df['AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMore'+\
            'OtherRaces']= df['IAC_MALE'].astype(int)+df['IAC_FEMALE'].astype(int)
        df['AsianAloneOrInCombinationWithOneOrMoreOtherRaces'] = df[
            'AAC_MALE'].astype(int) + df['AAC_FEMALE'].astype(int)
        df['NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOr'+\
            'MoreOtherRaces']= df['NAC_MALE']\
                .astype(int)+df['NAC_FEMALE'].astype(int)
        df.drop(columns=[
            'AGEGRP', 'TOT_POP', 'TOT_MALE', 'TOT_FEMALE', 'WA_MALE',
            'WA_FEMALE', 'BA_MALE', 'BA_FEMALE', 'IA_MALE', 'IA_FEMALE',
            'AA_MALE', 'AA_FEMALE', 'NA_MALE', 'NA_FEMALE', 'TOM_MALE',
            'TOM_FEMALE', 'WAC_MALE', 'WAC_FEMALE', 'BAC_MALE', 'BAC_FEMALE',
            'IAC_MALE', 'IAC_FEMALE', 'AAC_MALE', 'AAC_FEMALE', 'NAC_MALE',
            'NAC_FEMALE'
        ],
                inplace=True)
    except Exception as e:
        logging.fatal(
            f"error in the method clean_county_2010_csv_file,{file_path} -{e}")
    return df


def _clean_county_2022_csv_file(df: pd.DataFrame,
                                file_path: str) -> pd.DataFrame:
    '''
    This Python Script Loads csv datasets
    from 2010-2020 on a County Level,
    cleans it and create a cleaned csv

    Arguments:
        df (DataFrame) : DataFrame of csv dataset
        file_path:str: File path to be processed

    Returns:
        df (DataFrame) : Transformed DataFrame for csv dataset.
    '''
    try:
        # filter by agegrp = 0
        df = df.query("YEAR not in [1]")
        df = df.query("AGEGRP == 0")
        # filter years 3 - 14
        df['YEAR'] = df['YEAR'].astype(str)
        conversion_of_year_to_value = {
            '2': '2020',
            '3': '2021',
            '4': '2022',
            '5': '2023'
        }
        df = df.replace({'YEAR': conversion_of_year_to_value})
        df.insert(6, 'geo_ID', 'geoId/', True)
        df['geo_ID'] = 'geoId/' +(df['STATE'].map(str)).str.zfill(2) + \
            (df['COUNTY'].map(str)).str.zfill(3)
        df['AGEGRP'] = df['AGEGRP'].astype(str)
        # Replacing the numbers with more understandable metadata headings
        conversion_of_agebracket_to_value = {
            '1': '0To4Years',
            '2': '5To9Years',
            '3': '10To14Years',
            '4': '15To19Years',
            '5': '20To24Years',
            '6': '25To29Years',
            '7': '30To34Years',
            '8': '35To39Years',
            '9': '40To44Years',
            '10': '45To49Years',
            '11': '50To54Years',
            '12': '55To59Years',
            '13': '60To64Years',
            '14': '65To69Years',
            '15': '70To74Years',
            '16': '75To79Years',
            '17': '80To84Years',
            '18': '85OrMoreYears'
        }
        df = df.replace({"AGEGRP": conversion_of_agebracket_to_value})
        # drop unwanted columns
        df.drop(columns=['SUMLEV', 'STATE', 'COUNTY', 'STNAME', 'CTYNAME'], \
            inplace=True)
        df = df.loc[:, :'NAC_FEMALE']
        df['Year'] = df['YEAR']
        df.drop(columns=['YEAR'], inplace=True)
        df['WhiteAlone'] = df['WA_MALE'].astype(int) + df['WA_FEMALE'].astype(
            int)
        df['BlackOrAfricanAmericanAlone'] = df['BA_MALE'].astype(int)\
            +df['BA_FEMALE'].astype(int)
        df['AmericanIndianAndAlaskaNativeAlone'] = df['IA_MALE'].astype(int)\
            +df['IA_FEMALE'].astype(int)
        df['AsianAlone'] = df['AA_MALE'].astype(int) + df['AA_FEMALE'].astype(
            int)
        df['NativeHawaiianAndOtherPacificIslanderAlone'] = df['NA_MALE']\
            .astype(int)+df['NA_FEMALE'].astype(int)
        df['TwoOrMoreRaces'] = df['TOM_MALE'].astype(int)+\
            df['TOM_FEMALE'].astype(int)
        df['WhiteAloneOrInCombinationWithOneOrMoreOtherRaces'] = df['WAC_MALE']\
            .astype(int)+ df['WAC_FEMALE'].astype(int)
        df['BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces']\
            = df['BAC_MALE'].astype(int)+df['BAC_FEMALE'].astype(int)
        df['AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMore'+\
            'OtherRaces']= df['IAC_MALE'].astype(int)+df['IAC_FEMALE'].astype(int)
        df['AsianAloneOrInCombinationWithOneOrMoreOtherRaces'] = df[
            'AAC_MALE'].astype(int) + df['AAC_FEMALE'].astype(int)
        df['NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOr'+\
            'MoreOtherRaces']= df['NAC_MALE']\
                .astype(int)+df['NAC_FEMALE'].astype(int)
        df.drop(columns=[
            'AGEGRP', 'TOT_POP', 'TOT_MALE', 'TOT_FEMALE', 'WA_MALE',
            'WA_FEMALE', 'BA_MALE', 'BA_FEMALE', 'IA_MALE', 'IA_FEMALE',
            'AA_MALE', 'AA_FEMALE', 'NA_MALE', 'NA_FEMALE', 'TOM_MALE',
            'TOM_FEMALE', 'WAC_MALE', 'WAC_FEMALE', 'BAC_MALE', 'BAC_FEMALE',
            'IAC_MALE', 'IAC_FEMALE', 'AAC_MALE', 'AAC_FEMALE', 'NAC_MALE',
            'NAC_FEMALE'
        ],
                inplace=True)
    except Exception as e:
        logging.fatal(
            f"error in the method clean_county_2022_csv_file,{file_path} -{e}")
    return df


def _clean_csv2_file(df: pd.DataFrame, file_path: str) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a csv file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of csv dataset
        file_path:str: File path to be processed

    Returns:
        df (DataFrame) : Transformed DataFrame for csv dataset.
    """
    try:
        # dropping unwanted rows after the data
        df.drop(df.index[65:], inplace=True)
        # dropping the first 14 unwanted rows
        df.drop(df.index[1:14], inplace=True)
        modify = [0, 30, 31, 32, 33, 34, 35, 40, 41, 42, 49]
        for j in modify:
            df.iloc[j]["Area"] = df.iloc[j]["Area"] + " " + df.iloc[j][1]
            for i in range(2, 10):
                df.iloc[j][i - 1] = df.iloc[j][i]
        df.iloc[9]["Area"] = df.iloc[9]["Area"] + " " + df.iloc[9][
            1] + " " + df.iloc[9][2]
        for i in range(3, 11):
            df.iloc[9][i - 2] = df.iloc[9][i]
        df.drop(columns=["3", "4", "8", "9", "10"], inplace=True)
        # Replacing the reuired columns.
        df.columns = df.columns.str.replace('Area', 'Geographic Area')
        df.columns = df.columns.str.replace('1', 'Total')
        df.columns = df.columns.str.replace('2', 'Total White')
        df.columns = df.columns.str.replace('5', 'Total Black')
        df.columns = df.columns.str.replace('6', \
            'Total American Indian & Alaska Native')
        df.columns = df.columns.str.replace('7',
                                            'Total Asian & Pacific Islander')

        df["Geographic Area"] = [x.title() for x in df["Geographic Area"]]
    except Exception as e:
        logging.fatal(f"error in the method clean_csv2_file,{file_path} -{e}")
    return df


def _clean_txt2_file(df: pd.DataFrame, file_path: str) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a txt file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of txt dataset
        file_path:str: File path to be processed

    Returns:
        df (DataFrame) : Transformed DataFrame for txt dataset.
    """
    try:
        df['1'] = df['1'].astype(str)
        # Length more than 6 has been taken to avoid individual ages
        mask = df['1'].str.len() >= 6
        df = df.loc[mask]
        # This has been taken to consider the month of july
        mask = df['1'].str[0] == '7'
        df = df.loc[mask]
        df = df[df['1'].str.contains("999")]
        df['Geographic Area'] = "United States"
        df['Year'] = df['1'].str[1:5]
        df['Total'] = df['2']
        # Adding individual columns to derive the required column
        df['Total White'] = df['5'] + df['6']
        df['Total Black'] = df['7'] + df['8']
        df['Total American Indian & Alaska Native'] = df['9'] + df['10']
        df['Total Asian & Pacific Islander'] = df['11'] + df['12']
        df = df.drop([
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
            "13", "14", "15", "16", "17", "18", "19", "20", "21", "22"
        ],
                     axis=1)
    except Exception as e:
        logging.fatal(f"error in the method clean_txt2_file,{file_path} -{e}")
    return df


def _clean_county_90_txt_file(file: str) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a txt file format.
    Also, Performs transformations on the data.

    Arguments:
        file (str) : Address of the file in system.

    Returns:
        df (DataFrame) : Transformed DataFrame for txt dataset.
    """
    # Naming the required columns
    df=pd.DataFrame(columns=["FIPS","Total","Total White",1,2,"Total Black",\
        "Total American Indian & Alaska Native",\
        "Total Asian & Pacific Islander",3])
    with open(file, encoding="ISO-8859-1") as inp:
        filter_list = ["1", "2", "3", "4", "5", "0"]
        for line in inp.readlines():
            if line.strip().startswith(tuple(filter_list)):
                list2 = (" ".join(line.strip('\n').split()).split())
                list1 = []
                for x in list2:
                    if x.isnumeric():
                        list1.append(x)
                df.loc[len(df.index)] = list1
    df["geo_ID"] = "geoId/" + df["FIPS"]
    df.drop(columns=["FIPS", 1, 2, 3], inplace=True)
    df["Year"] = "19" + file[-6:-4]
    df = df.drop(df[(df['geo_ID'].str.endswith('000'))].index)
    return df


def _transform_df(df: pd.DataFrame, file_path: str) -> pd.DataFrame:
    """
    This method transforms Dataframe into cleaned DF.
    Also, It Creates new columns, remove duplicates,
    Standaradize headers to SV's, Mulitply with
    scaling factor.

    Arguments:
        df (DataFrame) : DataFrame
        file_path:str: File path to be processed

    Returns:
        df (DataFrame) : DataFrame.
    """
    try:
        # Deriving new SV Count_Person_NonWhite as
        # subtracting White Alone from
        # Total

        if 'Geographic Area' in df.columns:
            final_cols = [
                col for col in df.columns if 'year' not in col.lower() and
                'geographic area' not in col.lower()
            ]
            missing_cols = ['Geographic Area', 'Year']
        else:
            final_cols = [
                col for col in df.columns
                if 'year' not in col.lower() and 'geo_id' not in col.lower()
            ]
            missing_cols = ['geo_ID', 'Year']

        df = df[missing_cols + final_cols]

        # Renaming DF Headers with ref to SV's Naming Standards.
        final_cols_list = ["Count_Person_" + col\
                        .replace("Asian Alone", "AsianAlone")\
                        .replace("White Alone", "WhiteAlone")\
                        .replace("Non White", "NonWhite")\
                        .replace\
                            ("Native Hawaiian and Other Pacific Islander Alone"\
                            ,"NativeHawaiianAndOtherPacificIslanderAlone")\
                        .replace("Black or African American Alone",\
                            "BlackOrAfricanAmericanAlone")\
                        .replace("Two or more Races",\
                                "TwoOrMoreRaces")\
                        .replace("American Indian or Alaska Native Alone",\
                            "AmericanIndianAndAlaskaNativeAlone")
                        .replace("Asian and Pacific Islander",\
                            "AsianAndPacificIslander")\
                        .replace("Total White",\
                            "WhiteAlone")\
                        .replace("Total Black",\
                            "BlackOrAfricanAmericanAlone")\
                        .replace("Total American Indian & Alaska Native",\
                            "AmericanIndianAndAlaskaNativeAlone")\
                        .replace("Total Asian & Pacific Islander",\
                            "AsianOrPacificIslander")\
                        .strip()\
                        .replace(" ", "_")\
                        for col in final_cols]

        final_cols_list = missing_cols + final_cols_list
        df.columns = final_cols_list
    except Exception as e:
        logging.fatal(f"error in the method transform_df,{file_path} -{e}")
    return df


def _mcf_process(col: str):
    """
    This method returns race statvar to make the MCF file.
        
    
    Arguments:
      col:  column name as str from the dataFrame returns race SV

    Returns: race SV
    """
    try:
        if re.findall('WhiteAlone', col) and \
            re.findall('OrInCombination', col):
            race = "WhiteAloneOrInCombinationWithOneOrMoreOtherRaces"
        elif re.findall('White', col) and re.findall('Non', col):
            race = "NonWhite"
        elif re.findall('WhiteAlone', col):
            race = "WhiteAlone"
        if re.findall('Black', col) and \
            re.findall('OrInCombination', col):
            race = "BlackOrAfricanAmericanAloneOrInCombination"+\
                "WithOneOrMoreOtherRaces"
        elif re.findall('Black', col):
            race = "BlackOrAfricanAmericanAlone"
        if re.findall('AmericanIndian', col) and re.findall(
                'OrInCombination', col):
            race = "AmericanIndianAndAlaskaNativeAloneOrIn"+\
                "CombinationWithOneOrMoreOtherRaces"
        elif re.findall('AmericanIndian', col):
            race = "AmericanIndianAndAlaskaNativeAlone"
        if re.findall('Asian', col):
            if re.findall('OrInCombination', col):
                race = "AsianAloneOrIn"+\
                    "CombinationWithOneOrMoreOtherRaces"
            else:
                race = "AsianAlone"
        if re.findall('NativeHawaiianAndOtherPacificIslander', col):
            if re.findall('OrInCombination', col):
                race = "NativeHawaiianAndOtherPacificIslanderAloneOrIn"+\
                    "CombinationWithOneOrMoreOtherRaces"
            else:
                race = "NativeHawaiianAndOtherPacificIslanderAlone"
        if re.findall('TwoOrMoreRaces', col):
            race = "TwoOrMoreRaces"
        if re.findall('AsianOrPacificIslander', col):
            race = "AsianOrPacificIslander"
    except Exception as e:
        logging.fatal(f"error in the method transform_df -{e}")
    return race


class CensusUSAPopulationByRace:
    """
    CensusUSAPopulationByRace class provides methods
    to load the data into dataframes, process, cleans
    dataframes and finally creates single cleaned csv
    file.
    Also provides methods to generate MCF and TMCF
    Files using pre-defined templates.
    """

    def __init__(self, input_path: str, csv_file_path: str, mcf_file_path: str,
                 tmcf_file_path: str) -> None:
        self.input_path = input_path
        self.cleaned_csv_file_path = csv_file_path
        self.mcf_file_path = mcf_file_path
        self.tmcf_file_path = tmcf_file_path
        self.df = None
        self.df_national = None
        self.file_name = None

    def _load_data(self, file: str) -> pd.DataFrame:
        """
        This Methods loads the data into pandas Dataframe
        using the provided file path and Returns the Dataframe.

        Arguments:
            file (str) : String of Dataset File Path
            self: refer to the instance of a class
        Returns:
            df (DataFrame) : DataFrame with loaded dataset
        """
        df = None
        self.file_name = os.path.basename(file)
        if ".xls" in file:
            if "pe-19" in file:
                df = pd.read_excel(file)
                df = _clean_xls2_file(df, file)
            elif "nc-est" in file:
                df = pd.read_excel(file)
                df = _clean_xlsx_file(df)
            elif "co-asr-7079" in file:
                df = pd.read_excel(file)
                df = _clean_county_70_xls_file(df, file)
            elif "pe-02" in file:
                df = pd.read_excel(file)
                df = _clean_county_80_xls_file(df, self.cleaned_csv_file_path)
            else:
                df = pd.read_excel(file)
                df = _clean_xls_file(df, file)
        elif ".csv" in file:
            if "srh" in file:
                df = pd.read_csv(file)
                df["Year"] = "19" + file[-6:-4]
                df = _clean_csv2_file(df, file)
            elif "co-est00" in file:
                df = _clean_county_20_csv_file(file)
                float_col = df.select_dtypes(include=['float64'])
                for col in float_col.columns.values:
                    df[col] = df[col].astype('int64')
            elif "CC-EST2020" in file:
                df = pd.read_csv(file, encoding='ISO-8859-1', low_memory=False)
                df = _clean_county_2010_csv_file(df, file)
                # aggregating County data to obtain National data for 2010-2020
                df_national = df.copy()
                df_national['geo_ID'] = "country/USA"
                df_national = df_national.groupby(['Year','geo_ID']).sum().\
                    reset_index()
                # aggregating County data to obtain State data for 2010-2020
                df_state = df.copy()
                df_state['geo_ID'] = (
                    df['geo_ID'].map(str)).str[:len('geoId/NN')]
                df_state = df_state.groupby(['Year', 'geo_ID']).sum().\
                    reset_index()
                df = pd.concat([df, df_state, df_national], ignore_index=True)
                float_col = df.select_dtypes(include=['float64'])
                for col in float_col.columns.values:
                    df[col] = df[col].astype('int64')

            #This change as be done to make sure to process all future files
            elif "cc-est202" in file:
                df = pd.read_csv(file, encoding='ISO-8859-1', low_memory=False)
                df = _clean_county_2022_csv_file(df, file)
                # aggregating County data to obtain National data for 2020-2022
                df_national = df.copy()
                df_national['geo_ID'] = "country/USA"
                df_national = df_national.groupby(['Year','geo_ID']).sum().\
                    reset_index()
                # aggregating County data to obtain State data for 2020-2022
                df_state = df.copy()
                df_state['geo_ID'] = (
                    df['geo_ID'].map(str)).str[:len('geoId/NN')]
                df_state = df_state.groupby(['Year', 'geo_ID']).sum().\
                    reset_index()
                df = pd.concat([df, df_state, df_national], ignore_index=True)
                float_col = df.select_dtypes(include=['float64'])
                for col in float_col.columns.values:
                    df[col] = df[col].astype('int64')
            else:
                df = pd.read_csv(file)
                df = _clean_csv_file(df, file)
        elif ".TXT" in file or ".txt" in file:
            if "USCounty" in file:
                df = _clean_county_90_txt_file(file)
            else:
                cols = ["0", "1", "2", "3", "4", "5", "6", "7",\
                    "8", "9", "10", "11","12", "13", "14", "15",\
                    "16", "17", "18", "19", "20", "21", "22"]
                df = pd.read_table(file,
                                   index_col=False,
                                   delim_whitespace=True,
                                   engine='python',
                                   names=cols)
                if "for" in file:
                    df = _clean_txt2_file(df, file)
        return df

    def _transform_data(self, df: pd.DataFrame, file_path: str) -> None:
        """
        This method calls the required functions to transform
        the dataframe and saves the final cleaned data in
        CSV file format.

        Arguments:
            self: refer to the instance of a class
            df (DataFrame) : DataFrame
            file (str) : String of Dataset File Path

        Returns:
            None
        """
        try:
            # Finding the Dir Path
            file_dir = self.cleaned_csv_file_path
            if not os.path.exists(file_dir):
                os.mkdir(file_dir)
            df = _transform_df(df, file_path)
            if 'geo_ID' not in df.columns:
                df = _add_geo_id(df)
            if self.df is None:
                self.df = pd.DataFrame(columns=["Year","geo_ID",\
                    "Count_Person_USAllRaces","Count_Person_WhiteAlone",\
                    "Count_Person_BlackOrAfricanAmericanAlone",\
                    "Count_Person_AmericanIndianAndAlaskaNativeAlone",\
                    "Count_Person_AsianAlone"\
                    ,"Count_Person_NativeHawaiianAndOtherPacificIslanderAlone",
                    "Count_Person_WhiteAloneOrInCombination"+\
                        "WithOneOrMoreOtherRaces",\
                    "Count_Person_BlackOrAfricanAmericanAlone"+\
                        "OrInCombinationWithOneOrMoreOtherRaces",\
                    "Count_Person_AmericanIndianAndAlaskaNativeAlone"+\
                        "OrInCombinationWithOneOrMoreOtherRaces",\
                    "Count_Person_AsianAloneOr"+\
                        "InCombinationWithOneOrMoreOtherRaces",\
                    "Count_Person_NativeHawaiianAndOtherPacificIslanderAloneOr"+\
                    "InCombinationWithOneOrMoreOtherRaces",\
                    "Count_Person_AsianOrPacificIslander",\
                    "Count_Person_TwoOrMoreRaces","Count_Person_NonWhite"])
                self.df = pd.concat([self.df, df], ignore_index=True)

            else:
                self.df = pd.concat([self.df, df], ignore_index=True)
            self.df['Year'] = pd.to_numeric(self.df['Year'])
            self.df.sort_values(by=['Year', 'geo_ID'],
                                ascending=True,
                                inplace=True)
            self.df = self.df[["Year","geo_ID",
                "Count_Person_WhiteAlone",\
                "Count_Person_BlackOrAfricanAmericanAlone",\
                "Count_Person_AmericanIndianAndAlaskaNativeAlone",\
                "Count_Person_AsianAlone",\
                "Count_Person_NativeHawaiianAndOtherPacificIslanderAlone",\
                "Count_Person_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces",\
                "Count_Person_BlackOrAfricanAmericanAlone"+\
                    "OrInCombinationWithOneOrMoreOtherRaces",\
                "Count_Person_AmericanIndianAndAlaskaNativeAloneOr"+\
                "InCombinationWithOneOrMoreOtherRaces",\
                "Count_Person_AsianAloneOrInCombinationWithOneOrMoreOtherRaces",\
                "Count_Person_NativeHawaiianAndOtherPacificIslanderAloneOr"+\
                "InCombinationWithOneOrMoreOtherRaces",\
                "Count_Person_AsianOrPacificIslander",\
                "Count_Person_TwoOrMoreRaces","Count_Person_NonWhite"]]
            df_before_2000 = self.df[self.df["Year"] < 2000]
            df_county_after_2000 = self.df[(self.df["Year"] >= 2000) &
                                           (self.df["geo_ID"] != "country/USA")
                                           & (self.df["geo_ID"].str.len() > 9)]
            df_national_state_2000 = self.df[(self.df["Year"] >= 2000) & (
                (self.df["geo_ID"].str.len() <= 9) |
                (self.df["geo_ID"] == "country/USA"))]
            df_before_2000.to_csv(os.path.join(
                self.cleaned_csv_file_path,
                "USA_Population_Count_by_Race_before_2000.csv"),
                                  index=False)
            df_county_after_2000.to_csv(os.path.join(
                self.cleaned_csv_file_path,
                "USA_Population_Count_by_Race_county_after_2000.csv"),
                                        index=False)
            df_national_state_2000.to_csv(os.path.join(
                self.cleaned_csv_file_path,
                "USA_Population_Count_by_Race_National_state_2000.csv"),
                                          index=False)
        except Exception as e:
            logging.error(f"error processing file -{e}")
            return False
        return True

    def process(self):
        """
        This is main method to iterate on each file,
        calls defined methods to clean, generate final
        cleaned CSV file, MCF file and TMCF file.
        """
        #input_path = _FLAGS.input_path
        ip_files = os.listdir(self.input_path)
        self.input_files = [
            self.input_path + os.sep + file for file in ip_files
        ]
        processed_count = 0
        total_files_to_process = len(self.input_files)
        logging.info(f"No of files to be processed {len(self.input_files)}")

        for file in self.input_files:
            logging.info(f"Processing the file: {file}")
            if 'USCountywv90.txt' in file:
                pass
            df = self._load_data(file)
            result = self._transform_data(df, file)
            if result:
                processed_count += 1
            else:
                logging.fatal(f'Failed to process {file}')
        logging.info(f"No of files processed {processed_count}")
        if processed_count == total_files_to_process & total_files_to_process > 0:

            name = "USA_Population_Count_by_Race_before_2000"
            generator_df=pd.read_csv\
                (os.path.join(self.cleaned_csv_file_path,
                    "USA_Population_Count_by_Race_before_2000.csv"))
            generator_df = generator_df[generator_df['geo_ID'].str.len() > 1]
            #Duplicate geo_ID instances were detected within the 1970-1979 data subset. To ensure data integrity, the older entries were eliminated, leaving only the most recent updates.
            generator_df = generator_df.drop_duplicates(
                subset=['geo_ID', 'Year'], keep='last')
            generator_df.to_csv(os.path.join(
                self.cleaned_csv_file_path,
                "USA_Population_Count_by_Race_before_2000.csv"),
                                index=False)
            self._generate_mcf(generator_df.columns, name)
            self._generate_tmcf(generator_df.columns, name)

            name = "USA_Population_Count_by_Race_county_after_2000"
            generator_df=pd.read_csv\
                (os.path.join(self.cleaned_csv_file_path,
                "USA_Population_Count_by_Race_county_after_2000.csv"))
            self._generate_mcf(generator_df.columns, name)
            self._generate_tmcf(generator_df.columns, name)

            name = "USA_Population_Count_by_Race_National_state_2000"
            generator_df=pd.read_csv\
                (os.path.join(self.cleaned_csv_file_path,
                "USA_Population_Count_by_Race_National_state_2000.csv"))

            self._generate_mcf(generator_df.columns, name)
            self._generate_tmcf(generator_df.columns, name)
        else:
            logging.fatal(
                "Aborting output files as no of files to process not matching processed files"
            )

    # Generating MCF files
    def _generate_mcf(self, df_cols: list, name: str) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Arguments:
            df_cols (list) : List of DataFrame Columns
            name (str): name of the file from which
            the mcf is generated
            self: refer to the instance of a class

        Returns:
            None
        """
        mcf_template = ("Node: dcid:{}\n"
                        "typeOf: dcs:StatisticalVariable\n"
                        "populationType: dcs:Person\n"
                        "statType: dcs:measuredValue\n"
                        "measuredProperty: dcs:count\n"
                        "race: dcs:{}\n")
        mcf = ""
        for col in df_cols:
            race = ""
            if col.lower() in [
                    "geographic area", "year", "short_form", "geo_id"
            ]:
                continue
            race = _mcf_process(col)
            mcf = mcf + mcf_template.format(col, race) + "\n"

        # Writing Genereated MCF to local path.
        suffix = name + ".mcf"
        with open(os.path.join(self.mcf_file_path,suffix),\
            'w+', encoding='utf-8') as f_out:
            f_out.write(mcf.rstrip('\n'))

    # Generating TMCF file.
    def _generate_tmcf(self, df_cols: list, name: str) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template

        Arguments:
            df_cols (list) : List of DataFrame Columns
            name (str) : name of the file from which
            the tmcf is being generated.

        Returns:
            None
        """
        tmcf_template = (
            "Node: E:USA_Population_Count_by_Race->E{}\n"
            "typeOf: dcs:StatVarObservation\n"
            "variableMeasured: dcs:{}\n"
            "measurementMethod: dcs:{}\n"
            "observationAbout: C:USA_Population_Count_by_Race->geo_ID\n"
            "observationDate: C:USA_Population_Count_by_Race->Year\n"
            "observationPeriod: \"P1Y\"\n"
            "value: C:USA_Population_Count_by_Race->{}\n")
        i = 0
        measure = ""
        tmcf = ""
        for col in df_cols:
            if col.lower() in [
                    "geographic area", "year", "short_form", "geo_id"
            ]:
                continue
            # Giving a different measurementMethod for the statistical Variables which are being.
            if name == "USA_Population_Count_by_Race_before_2000":
                if col in [
                        "Count_Person_WhiteAlone",
                        "Count_Person_BlackOrAfricanAmericanAlone"
                ]:
                    measure = "dcAggregate/CensusPEPSurvey_PartialAggregate_RaceUpto1999"
                else:
                    measure = "CensusPEPSurvey_RaceUpto1999"
            elif name == "USA_Population_Count_by_Race_county_after_2000":
                measure = "CensusPEPSurvey_Race2000Onwards"
            elif name == "USA_Population_Count_by_Race_National_state_2000":
                measure = "dcAggregate/CensusPEPSurvey_PartialAggregate_Race2000Onwards"
            tmcf = tmcf + tmcf_template.format(i, col, measure, col) + "\n"
            i = i + 1

        # Writing Genereated TMCF to local path.
        suffix = name + ".tmcf"
        with open(os.path.join(self.tmcf_file_path,suffix),\
            'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))


# The outputs are loaded into


def _resolve_pe_11(file_name: str, url: str) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a csv file format.

    Arguments:
        file_name (str) : File name of csv dataset
        url: str : Refers to file URL


    Returns:
        df (DataFrame) : Transformed DataFrame for csv dataset.
    """
    try:
        year = file_name[-8:-4]
        if int(year) < 1960:
            cols = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()  # will raise for 403/404/etc.
            df = pd.read_csv(StringIO(response.text), names=cols)
            df = df[df["0"].str.contains("All ages", na=False)]
            df['Year'] = year
            df['Geographic Area'] = "United States"
        else:
            cols = [
                "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11",
                "12"
            ]
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()  # will raise for 403/404/etc.
            df = pd.read_csv(StringIO(response.text), names=cols, skiprows=2)
            df = df[df["0"].str.contains("All ages", na=False)]
            df['Year'] = year
            df['Geographic Area'] = "United States"
        return df
    except Exception as e:
        logging.fatal(f"Error Downloading the file:", e)


def add_future_yearurls():
    """
    This method scans the download URLs for future years.

    """
    global _FILES_TO_DOWNLOAD
    with open(os.path.join(_MODULE_DIR, 'input_url.json'), 'r') as inpit_file:
        _FILES_TO_DOWNLOAD = json.load(inpit_file)
    urls_to_scan = [
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/counties/asrh/cc-est{YEAR}-alldata.csv"
    ]
    # This method will generate URLs for the years 2024 to 2029
    for future_year in range(2024, 2030):
        if dt.now().year > future_year:
            YEAR = future_year
            for url in urls_to_scan:
                url_to_check = url.format(YEAR=YEAR)
                try:
                    checkurl = requests.head(url_to_check)
                    if checkurl.status_code == 200:
                        _FILES_TO_DOWNLOAD.append(
                            {"download_path": url_to_check})

                except:
                    logging.error(f"URL is not accessable {url_to_check}")


def download_files():
    """
    This method allows to download the input files.

    """

    global _FILES_TO_DOWNLOAD
    session = requests.session()
    max_retry = 5
    for file_to_dowload in _FILES_TO_DOWNLOAD:
        file_name = None
        download_local_path = _INPUT_FILE_PATH
        url = file_to_dowload['download_path']
        if 'file_name' in file_to_dowload and len(
                file_to_dowload['file_name'] > 5):
            file_name = file_to_dowload['file_name']
        else:
            file_name = url.split('/')[-1]
        retry_number = 0

        is_file_downloaded = False
        # headers = {'User-Agent': 'Mozilla/5.0'}
        # response = requests.get(url, headers=headers)
        while is_file_downloaded == False:
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers, timeout=60)
                response.raise_for_status()
                if ".csv" in url:
                    if "st-est" in url or 'SC-EST' in url:
                        file_name = file_name.replace(".csv", ".xlsx")
                        df = pd.read_csv(StringIO(response.text),
                                         on_bad_lines='skip',
                                         header=0)
                        df.to_excel(download_local_path + os.sep + file_name\
                            ,index=False,engine='xlsxwriter')
                    elif "pe-11" in url:
                        df = _resolve_pe_11(file_name, url)
                        df.to_csv(download_local_path + os.sep + file_name,
                                  index=False)
                    elif "pe-19" in url:
                        file_name = file_name.replace(".csv", ".xlsx")
                        df = pd.read_csv(StringIO(response.text),
                                         skiprows=5,
                                         on_bad_lines='skip',
                                         header=0)
                        df.to_excel(download_local_path + os.sep + file_name\
                            ,index=False,engine='xlsxwriter')
                    elif "co-asr-7079" in url or "pe-02" in url:
                        file_name = file_name.replace(".csv", ".xlsx")
                        cols=['Year','FIPS','Race/Sex',1,2,3,4,5,6,7,8,9,10,11,12,\
                            13,14,15,16,17,18]
                        if "pe-02" in url:
                            df = pd.read_csv(StringIO(response.text), skiprows=7, on_bad_lines='skip', \
                                names=cols)
                        else:
                            df = pd.read_csv(StringIO(response.text),
                                             on_bad_lines='skip',
                                             names=cols)
                        df.to_excel(download_local_path + os.sep + file_name,\
                            index=False,engine='xlsxwriter')
                    elif "co-est00int-alldata" in url or "CC-EST2020-ALLDATA" in url or "cc-est2022-all" in url or "cc-est20" in url:
                        df = pd.read_csv(StringIO(response.text),
                                         on_bad_lines='skip',
                                         encoding='ISO-8859-1',
                                         low_memory=False)
                        df.to_csv(download_local_path + os.sep + file_name,
                                  index=False)
                    else:
                        logging.fatal(f'Unknown csv file: {url}')

                elif ".txt" in url and "srh" in url:
                    if "crh" in url:
                        file_name = file_name.replace("crh", "USCounty")
                        df = pd.read_table(StringIO(response.text),
                                           index_col=False,
                                           engine='python')
                        df.to_csv(download_local_path + os.sep + file_name,
                                  index=False)
                    else:
                        cols = ['Area', 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                        df = pd.read_table(StringIO(response.text),index_col=False,delim_whitespace=True\
                            ,engine='python',skiprows=14,names=cols)
                        file_name = file_name.replace(".txt", ".csv")
                        df.to_csv(download_local_path + os.sep + file_name,
                                  index=False)

                elif "xlsx" in url:
                    df = pd.read_excel(StringIO(response.text),
                                       skiprows=2,
                                       header=0)
                    df.to_excel(download_local_path + os.sep + file_name\
                        ,index=False,header=False,engine='xlsxwriter')
                else:
                    logging.fatal(f'Unknown file - {url}')

                logging.info(f"Downloaded file : {url}")
                is_file_downloaded = True

            except Exception as e:
                logging.error(f"Retry file download {url} - {e}")
                time.sleep(5)
                retry_number += 1
                if retry_number > max_retry:
                    logging.fatal(f"Error downloading URL- {url} -{e}")

    return True


def main(_):
    mode = _FLAGS.mode
    # Defining Output file names
    output_path = os.path.join(_MODULE_DIR, "output")
    input_path = os.path.join(_MODULE_DIR, "input_files")
    if not os.path.exists(input_path):
        os.mkdir(input_path)
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    cleaned_csv_path = output_path
    mcf_path = output_path
    tmcf_path = output_path
    input_path = _FLAGS.input_path

    if mode == "" or mode == "download":
        # download & process
        add_future_yearurls()
        download_files()
    if mode == "" or mode == "process":
        loader = CensusUSAPopulationByRace(input_path, output_path, mcf_path,
                                           tmcf_path)
        loader.process()

    logging.info("Processing completed")


if __name__ == "__main__":
    app.run(main)
