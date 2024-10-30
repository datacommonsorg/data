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
"""
This module creates CSV files used for importing data into DC.

Below are list of files processed -
County
    1990 - 2000     Processed As Is
    2000 - 2010     Processed As Is
    2010 - 2020     Processed As Is
    2020 - 2023     Processed As Is
    
State
    1980 - 1990     Processed As Is
    1990 - 2000     Processed As Is
    2000 - 2010     Aggregated from County to state
                    (data matches with State Level files available)
    2010 - 2020     Aggregated from County to state
                    (data matches with State Level files available)
    2020 - 2023     Aggregated from County to state
                    (data matches with State Level files available)              

National
    1980 - 1990     Aggregted from State to National Level
    1990 - 2000     Aggregted from State to National Level
    2000 - 2010     Aggregted from State to National Level
    2010 - 2020     Aggregted from State to National Level
    2020 - 2023     Aggregted from State to National Level

Also SV aggregation are produced while processing above files.
E.g., Count_Person_White_HispanicOrLatino is calulated by addding
Count_Person_Male_WhiteHispanicOrLatino and
Count_Person_Female_WhiteHispanicOrLatino

Before running this module, run download.sh script, it downloads required
input files, creates necessary folders for processing.

Folder information
input_files - downloaded files (from US census website) are placed here
process_files - intermediate processed files are placed in this folder.
output_files - output files (mcf, tmcf and csv are written here)
"""

import os
import pandas as pd
import requests
import shutil
import json
import time
from datetime import datetime as dt
from absl import logging

from absl import app
from absl import flags

from constants import DOWNLOAD_DIR, PROCESS_AS_IS_DIR, PROCESS_AGG_DIR, RACE
from constants import OUTPUT_DIR, STAT_VAR_COL_MAPPING, WORKING_DIRECTORIES
from mcf_generator import generate_mcf
from tmcf_generator import generate_tmcf

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = os.path.join(_MODULE_DIR, 'input_files')

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_FLAGS = flags.FLAGS
flags.DEFINE_string(
    "data_directory", DOWNLOAD_DIR,
    "Folder consisting of all input files required for processing. Run download.sh before running this python module"
)

# SR Columns with single race or combination with one or more race
# These columns are not used as part of current import
_SR_COLUMNS = [
    'TOT_POP', 'TOT_MALE', 'TOT_FEMALE', 'WA_MALE', 'WA_FEMALE', 'BA_MALE',
    'BA_FEMALE', 'IA_MALE', 'IA_FEMALE', 'AA_MALE', 'AA_FEMALE', 'NA_MALE',
    'NA_FEMALE', 'TOM_MALE', 'TOM_FEMALE'
]

_SR_CMBN_COLUMNS = [
    'WAC_MALE', 'WAC_FEMALE', 'BAC_MALE', 'BAC_FEMALE', 'IAC_MALE',
    'IAC_FEMALE', 'AAC_MALE', 'AAC_FEMALE', 'NAC_MALE', 'NAC_FEMALE'
]


def _calculate_agg_measure_method(year, sv):
    """
    This method calculates measurement method of SV's.
    US Census introduced additional Races and option to select more than one
    Race in census survey from year 2000 onwards. 
    This method will return measurement method as CensusPEPSurvey_RaceUpto1999
    for data prior to 2000 and CensusPEPSurvey_Race2000Onwards for data from
    2000 onwards. This is caluclated on those SV's only which has Race as one
    of their property
    
    Args:
      year: Year
      SV: Statistical Variable
    
    Returns:
      Measurement Method
    """
    for r in RACE:
        # if r in sv:
        if sv.endswith(r) or sv in [
                'dcid:Count_Person_WhiteAloneNotHispanicOrLatino',
                'dcid:Count_Person_Male_WhiteAloneNotHispanicOrLatino',
                'dcid:Count_Person_Female_WhiteAloneNotHispanicOrLatino'
        ]:
            if year < 2000:
                return 'dcs:dcAggregate/CensusPEPSurvey_RaceUpto1999'
            elif year >= 2000:
                return 'dcs:dcAggregate/CensusPEPSurvey_Race2000Onwards'
    return 'dcs:dcAggregate/CensusPEPSurvey'


def _calculate_asis_measure_method(year, sv):
    """
    This method calculates measurement method of SV's.
    US Census introduced additional Races and option to select more than one
    Race in census survey from year 2000 onwards. 
    This method will return measurement method as CensusPEPSurvey_RaceUpto1999
    for data prior to 2000 and CensusPEPSurvey_Race2000Onwards for data from
    2000 onwards. This is caluclated on those SV's only which has Race as one
    of their property
    
    Args:
      year: Year
      SV: Statistical Variable
    
    Returns:
      Measurement Method
    """
    for r in RACE:
        # if r in sv:
        if sv.endswith(r) or sv in [
                'dcid:Count_Person_WhiteAloneNotHispanicOrLatino',
                'dcid:Count_Person_Male_WhiteAloneNotHispanicOrLatino',
                'dcid:Count_Person_Female_WhiteAloneNotHispanicOrLatino'
        ]:
            if year < 2000:
                return 'dcs:CensusPEPSurvey_RaceUpto1999'
            elif year >= 2000:
                return 'dcs:CensusPEPSurvey_Race2000Onwards'
    return 'dcs:CensusPEPSurvey'


def _process_geo_aggregation(input_file_path, input_file_name, output_file_path,
                             output_file_name, geo_aggregation_level):
    """
    This method aggregates data from lower geo to higher geo level.
    E.g., from county level to state level; state level to national level.
    Aggregated files are written to output file path.
    
    Args:
      input_file_path: input file path - usually more granular level data
      input_file_name: name of the input file to read data from
      output_file_path: output path where file needs to be written
      output_file_name: output file name
      geo_aggregation_level: geo level to which data needs to be aggregated.
        currently accepts 'state' and 'national' level as input argument
    """

    df = pd.read_csv(input_file_path + input_file_name)
    if geo_aggregation_level == 'national':
        df['LOCATION'] = 'country/USA'
    elif geo_aggregation_level == 'state':
        df['LOCATION'] = (df['LOCATION'].map(str)).str[:len('geoId/NN')]
    df = df.groupby(['YEAR', 'LOCATION']).agg('sum').reset_index()
    df.to_csv(output_file_path + output_file_name, index=False)


def _process_geo_level_aggregation():
    """
    This method aggregates county and state level data to upper geography level.
    
    Below files are generated.
    State
    2000 - 2010     Aggregated from County to state
                    (data matches with State Level files available)
    2010 - 2020     Aggregated from County to state
                    (data matches with State Level files available)
    2020 - 2023     Aggregated from County to state
                    (data matches with State Level files available)                

    National
    1980 - 1990     Aggregted from State to National Level
    1990 - 2000     Aggregted from State to National Level
    2000 - 2010     Aggregted from State to National Level
    2010 - 2020     Aggregted from State to National Level
    2020 - 2023     Aggregted from State to National Level
    """

    # Below dictionary holds list of years and geo details for which
    # data needs to be aggregated.
    # Dictionay key provides Geo and Year information for which data is
    # aggregated. Dictionary value is a list which provides details of input
    # folder name, input file name, output folder namem output file name and
    # geo level aggregation we are carrying.

    file_process_details = {
        'state_2000_2010': [
            '2000_2010/county/', 'county_2000_2010.csv', '2000_2010/state/',
            'state_2000_2010.csv', 'state'
        ],
        'state_2010_2020': [
            '2010_2020/county/', 'county_2010_2020.csv', '2010_2020/state/',
            'state_2010_2020.csv', 'state'
        ],
        'state_2020_2023': [
            '2020_2023/county/', 'county_2020_2023.csv', '2020_2023/state/',
            'state_2020_2023.csv', 'state'
        ],
        'national_1980_1990': [
            '1980_1990/state/', 'state_1980_1990.csv', '1980_1990/national/',
            'national_1980_1990.csv', 'national'
        ],
        'national_1990_2000': [
            '1990_2000/state/', 'state_1990_2000.csv', '1990_2000/national/',
            'national_1990_2000.csv', 'national'
        ],
        'national_2000_2010': [
            '2000_2010/state/', 'state_2000_2010.csv', '2000_2010/national/',
            'national_2000_2010.csv', 'national'
        ],
        'national_2010_2020': [
            '2010_2020/state/', 'state_2010_2020.csv', '2010_2020/national/',
            'national_2010_2020.csv', 'national'
        ],
        'national_2020_2023': [
            '2020_2023/state/', 'state_2020_2023.csv', '2020_2023/national/',
            'national_2020_2023.csv', 'national'
        ]
    }

    for geo_agg_file in file_process_details:
        for measurement_method in 'as-is', 'aggregate':
            if measurement_method == 'as-is':
                input_file_path = _CODEDIR + PROCESS_AS_IS_DIR + file_process_details[
                    geo_agg_file][0]
                output_file_path = _CODEDIR + PROCESS_AS_IS_DIR + file_process_details[
                    geo_agg_file][2]
            else:
                input_file_path = _CODEDIR + PROCESS_AGG_DIR + file_process_details[
                    geo_agg_file][0]
                output_file_path = _CODEDIR + PROCESS_AGG_DIR + file_process_details[
                    geo_agg_file][2]
            input_file_name = file_process_details[geo_agg_file][1]
            output_file_name = file_process_details[geo_agg_file][3]
            _process_geo_aggregation(input_file_path, input_file_name,
                                     output_file_path, output_file_name,
                                     file_process_details[geo_agg_file][4])


def _process_state_files_1980_1990(download_dir):
    """
    Process state files from year 1980 - 1990
    Source files (for 1980 - 1990) consists of age information in bracket 
    of 5 years. These age brackets are aggregated during processing 
    along with SRH properties.

    Args:
      download_dir: download directory - input files are saved here.
    """
    # Section 1 - Writing As Is data
    input_file_path = _CODEDIR + download_dir + '1980_1990/state/'
    output_file_path = _CODEDIR + PROCESS_AS_IS_DIR + '1980_1990/state/'
    output_file_name = 'state_1980_1990.csv'
    output_temp_file_name = 'state_1980_1990_temp.csv'
    files_list = os.listdir(input_file_path)
    files_list.sort()

    column_names = ["LOCATION", "YEAR_TEMP", "RACE_ORIGIN", "SEX"]
    age_columns = [f'A{x:02d}' for x in range(1, 19)]
    column_names.extend(age_columns)

    # Metadata reference file for column specification
    # https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/1980-1990/st_int_asrh_doc.txt
    column_specification = [(0, 2), (2, 3), (3, 4), (4, 5), (5, 12), (12, 19),
                            (19, 26), (26, 33), (33, 40), (40, 47), (47, 54),
                            (54, 61), (61, 68), (68, 75), (75, 82), (82, 89),
                            (89, 96), (96, 103), (103, 110), (110, 117),
                            (117, 124), (124, 131)]

    for file in files_list:
        df = pd.read_fwf(input_file_path + files_list[0],
                         names=column_names,
                         colspecs=column_specification)

        df["ALL_AGE"] = 0
        for age in age_columns:
            df["ALL_AGE"] += df[age]

        df.drop(age_columns, axis=1, inplace=True)

        df = df.pivot(index=['LOCATION', 'YEAR_TEMP'],
                      columns=['RACE_ORIGIN', 'SEX'],
                      values='ALL_AGE').reset_index()

        df.to_csv(output_file_path + output_temp_file_name,
                  header=True,
                  index=False)

        df = pd.read_csv(output_file_path + output_temp_file_name)
        # On pivoting one new row is introduced with NaN - hence dropping
        df = df.dropna()
        # Some of the columns are read as Float, hence converting them to Int
        float_col = df.select_dtypes(include=['float64'])
        for col in float_col.columns.values:
            df[col] = df[col].astype('int64')

        df.insert(0, 'YEAR', 1980 + df['YEAR_TEMP'], True)
        df['LOCATION'] = 'geoId/' + (df['LOCATION'].map(str)).str.zfill(2)
        df.drop(["YEAR_TEMP"], axis=1, inplace=True)

        _NOT_HISPANIC_RACES = ['NH-W', 'NH-B', 'NH-AI', 'NH-API']
        _HISPANIC_RACES = ['H-W', 'H-B', 'H-AI', 'H-API']

        column_header = ['YEAR', 'LOCATION']
        for p in _NOT_HISPANIC_RACES:
            column_header.append(p + '-M')
            column_header.append(p + '-F')
        for p in _HISPANIC_RACES:
            column_header.append(p + '-M')
            column_header.append(p + '-F')
        df.columns = column_header

        if file == files_list[0]:
            df.to_csv(output_file_path + output_file_name, index=False)
        else:
            df.to_csv(output_file_path + output_file_name,
                      index=False,
                      mode='a')

        if os.path.exists(output_file_path + output_temp_file_name):
            os.remove(output_file_path + output_temp_file_name)

    # Section 2 - Writing Agg data
    output_file_path = _CODEDIR + PROCESS_AGG_DIR + '1980_1990/state/'

    df1 = pd.DataFrame()
    df1['YEAR'] = df['YEAR'].copy()
    df1['LOCATION'] = df['LOCATION'].copy()

    df1['NH'] = df1['H'] = 0
    for p in _NOT_HISPANIC_RACES:
        df1['NH'] += (df[p + '-M'] + df[p + '-F']).copy()
        df1[p] = (df[p + '-M'] + df[p + '-F']).copy()

    for p in _HISPANIC_RACES:
        df1['H'] += (df[p + '-M'] + df[p + '-F']).copy()
        df1[p] = (df[p + '-M'] + df[p + '-F']).copy()

    df1.to_csv(output_file_path + output_file_name, header=True, index=False)


def _process_state_files_1990_2000(download_dir):
    """
    Process state files from 1990 - 2000
    
    There are 10 files in total for each year i.e., from 1990 - 1999.
    Each yearly file consists of Population Census for all states.

    All files are available in same format.

    Args:
      download_dir: download directory - input files are saved here.
    """
    # Section 1 - Writing As Is data
    input_file_path = _CODEDIR + download_dir + '1990_2000/state/'
    output_file_path = _CODEDIR + PROCESS_AS_IS_DIR + '1990_2000/state/'
    output_file_name = 'state_1990_2000.csv'
    output_temp_file_name = 'state_1990_2000_temp.csv'
    files_list = os.listdir(input_file_path)
    files_list.sort()

    column_names = [
        "YEAR", "LOCATION", "AGE", "NH-W-M", "NH-W-F", "NH-B-M", "NH-B-F",
        "NH-AIAN-M", "NH-AIAN-F", "NH-API-M", "NH-API-F", "H-W-M", "H-W-F",
        "H-B-M", "H-B-F", "H-AIAN-M", "H-AIAN-F", "H-API-M", "H-API-F"
    ]

    # Column specification - Link to metadata file:
    # https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/1990-2000/sasrh_rl.txt
    column_specification = [(0, 4), (5, 7), (8, 11), (12, 19), (19, 26),
                            (27, 34), (34, 41), (42, 49), (49, 56), (57, 64),
                            (64, 71), (72, 79), (79, 86), (87, 94), (94, 101),
                            (102, 109), (109, 116), (117, 124), (124, 131)]

    # Read all files (10) and write to single temp file before further
    # processing.
    for file in files_list:
        temp_file_df = pd.read_fwf(input_file_path + file,
                                   encoding='latin-1',
                                   names=column_names,
                                   colspecs=column_specification,
                                   skiprows=16)
        if file == files_list[0]:
            temp_file_df.to_csv(output_file_path + output_temp_file_name,
                                header=True,
                                index=False)
        else:
            temp_file_df.to_csv(output_file_path + output_temp_file_name,
                                header=False,
                                index=False,
                                mode='a')

    df = pd.read_csv(output_file_path + output_temp_file_name)
    df.drop(["AGE"], axis=1, inplace=True)
    df = df.groupby(['YEAR', 'LOCATION']).agg('sum').reset_index()
    df['LOCATION'] = 'geoId/' + (df['LOCATION'].map(str)).str.zfill(2)
    df.to_csv(output_file_path + output_file_name, index=False)

    # Deleteing temp (concatenated file)
    if os.path.exists(output_file_path + output_temp_file_name):
        os.remove(output_file_path + output_temp_file_name)

    output_file_path = _CODEDIR + PROCESS_AGG_DIR + '1990_2000/state/'

    # Section 2 - Writing Agg data
    df1 = pd.DataFrame()
    df1['YEAR'] = df['YEAR'].copy()
    df1['LOCATION'] = df['LOCATION'].copy()

    _NOT_HISPANIC_RACES = ['NH-W', 'NH-B', 'NH-AIAN', 'NH-API']
    _HISPANIC_RACES = ['H-W', 'H-B', 'H-AIAN', 'H-API']

    df1['NH'] = df1['H'] = 0
    for p in _NOT_HISPANIC_RACES:
        df1['NH'] += (df[p + '-M'] + df[p + '-F']).copy()
        df1[p] = (df[p + '-M'] + df[p + '-F']).copy()

    for p in _HISPANIC_RACES:
        df1['H'] += (df[p + '-M'] + df[p + '-F']).copy()
        df1[p] = (df[p + '-M'] + df[p + '-F']).copy()

    df1.to_csv(output_file_path + output_file_name, header=True, index=False)


def _process_state_files(download_dir):
    """
    A helper function to invoke state level file processing from one place.
    Process state files from 1980 - 2020

    Args:
      download_dir: download directory - input files are saved here.
    """
    _process_state_files_1980_1990(download_dir)
    _process_state_files_1990_2000(download_dir)


def _process_county_files_1990_2000(download_dir):
    """
    Process County files 1990 2000.
    This method generated CSV files for as-is data (e.g., for SV such as 
    H-W) and aggregated data (e.g., NH = NH-W + NH-B + NH-AIAN + NH-API)

    Args:
      download_dir: download directory - input files are saved here.
    """
    # Section 1 - Writing As Is data
    input_file_path = _CODEDIR + download_dir + '1990_2000/county/'
    output_file_path = _CODEDIR + PROCESS_AS_IS_DIR + '1990_2000/county/'
    output_file_name = 'county_1990_2000.csv'
    files_list = os.listdir(input_file_path)
    files_list.sort()

    column_names = [
        "YEAR",
        "LOCATION",
        "NH-W",
        "NH-B",
        "NH-AIAN",
        "NH-API",
        "H-W",
        "H-B",
        "H-AIAN",
        "H-API",
    ]

    # Column specification reference file:
    # https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/1990-2000/co-99-10-rl.txt
    column_specification = [(0, 4), (5, 10), (10, 19), (19, 28), (28, 37),
                            (37, 46), (46, 55), (55, 64), (64, 73), (73, 82)]

    for file in files_list:
        df = pd.read_fwf(input_file_path + file,
                         encoding='latin-1',
                         names=column_names,
                         colspecs=column_specification,
                         header=None,
                         skiprows=18)

        df['LOCATION'] = 'geoId/' + (df['LOCATION'].map(str)).str.zfill(5)

        if file == files_list[0]:
            df.to_csv(output_file_path + output_file_name, index=False)
        else:
            df.to_csv(output_file_path + output_file_name,
                      index=False,
                      mode='a')

    # Section 2 - Writing Agg data
    output_file_path = _CODEDIR + PROCESS_AGG_DIR + '1990_2000/county/'

    df1 = pd.DataFrame()
    df1['YEAR'] = df['YEAR'].copy()
    df1['LOCATION'] = df['LOCATION'].copy()
    df1['NH'] = (df['NH-W'] + df['NH-B'] + df['NH-AIAN'] + df['NH-API']).copy()
    df1['H'] = (df['H-W'] + df['H-B'] + df['H-AIAN'] + df['H-API']).copy()

    df1.to_csv(output_file_path + output_file_name, header=True, index=False)


def _process_county_files_2000_2010(download_dir):
    """
    Process County files 2000 2010
    This method generated CSV files for as-is data (e.g., for SV such as 
    NHWA, NHBA etc.) and aggregated data (e.g., NH = NH_MALE + NH_FEMALE).

    Args:
      download_dir: download directory - input files are saved here.
    """
    # Section 1 - Writing As Is data
    input_file_path = _CODEDIR + download_dir + '2000_2010/county/'
    output_file_path = _CODEDIR + PROCESS_AS_IS_DIR + '2000_2010/county/'
    output_file_name = 'county_2000_2010.csv'
    files_list = os.listdir(input_file_path)
    files_list.sort()

    for file in files_list:
        df = pd.read_csv(input_file_path + file, encoding='ISO-8859-1')
        df = df.query('AGEGRP == 99  & YEAR not in [1, 12, 13]').copy()
        df['YEAR'] = 2000 - 2 + df['YEAR']
        df.insert(7, 'LOCATION', '', True)
        df['LOCATION'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(2) + (
            df['COUNTY'].map(str)).str.zfill(3)
        df.drop(['SUMLEV', 'STATE', 'COUNTY', 'STNAME', 'CTYNAME', 'AGEGRP'],
                axis=1,
                inplace=True)

        if file == files_list[0]:
            df.to_csv(output_file_path + output_file_name,
                      header=True,
                      index=False)
        else:
            df.to_csv(output_file_path + output_file_name,
                      header=False,
                      index=False,
                      mode='a')

    df = pd.read_csv(output_file_path + output_file_name)

    # Section 2 - Writing Agg data
    output_file_path = _CODEDIR + PROCESS_AGG_DIR + '2000_2010/county/'
    df1 = pd.DataFrame()
    df1['YEAR'] = df['YEAR'].copy()
    df1['LOCATION'] = df['LOCATION'].copy()

    _NOT_HISPANIC_RACES = [
        'NH', 'NHWA', 'NHBA', 'NHIA', 'NHAA', 'NHNA', 'NHTOM'
    ]
    _HISPANIC_RACES = ['H', 'HWA', 'HBA', 'HIA', 'HAA', 'HNA', 'HTOM']

    # df1['NH'] = df1['H'] = 0
    for p in _NOT_HISPANIC_RACES:
        df1[p] = (df[p + '_MALE'] + df[p + '_FEMALE']).copy()

    for p in _HISPANIC_RACES:
        df1[p] = (df[p + '_MALE'] + df[p + '_FEMALE']).copy()

    df1.to_csv(output_file_path + output_file_name, header=True, index=False)


def _process_county_files_2010_2020(download_dir):
    """
    Process County files 2010 2020.
    This method generates files for SV available as-is in source 
    file and aggregated SV by adding relevant stats 
    e.g., NH = NH_MALE + NH_FEMALE.

    Args:
      download_dir: download directory - input files are saved here.
    """
    input_file_path = _CODEDIR + download_dir + '2010_2020/county/'
    output_file_path = _CODEDIR + PROCESS_AS_IS_DIR + '2010_2020/county/'
    output_file_name = 'county_2010_2020.csv'
    files_list = os.listdir(input_file_path)
    files_list.sort()

    for file in files_list:
        df = pd.read_csv(input_file_path + file,
                         encoding='ISO-8859-1',
                         low_memory=False)
        # filter by agegrp = 0 (0 = sum of all age group added)
        # filter years 3 - 13 (1, 2 - is base estimate and not for month July)
        df = df.query("AGEGRP == 0 & YEAR not in [1, 2]").copy()

        # convert year code to year
        # Year code starting from 3 for Year 2010
        df['YEAR'] = df['YEAR'] + 2010 - 3

        # add fips code for location
        df.insert(6, 'LOCATION', 'geoId/', True)
        df['LOCATION'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(2) + (
            df['COUNTY'].map(str)).str.zfill(3)

        # drop not reuqire columns
        df.drop(['SUMLEV', 'STATE', 'COUNTY', 'STNAME', 'CTYNAME', 'AGEGRP'],
                axis=1,
                inplace=True)

        if file == files_list[0]:
            df.to_csv(output_file_path + output_file_name, index=False)
        else:
            df.to_csv(output_file_path + output_file_name,
                      index=False,
                      mode='a')

    # Section 2 - Writing Agg data
    df = pd.read_csv(output_file_path + output_file_name)
    output_file_path = _CODEDIR + PROCESS_AGG_DIR + '2010_2020/county/'
    df1 = pd.DataFrame()
    df1['YEAR'] = df['YEAR'].copy()
    df1['LOCATION'] = df['LOCATION'].copy()

    _NOT_HISPANIC_RACES = [
        'NH', 'NHWA', 'NHBA', 'NHIA', 'NHAA', 'NHNA', 'NHTOM', 'NHWAC', 'NHBAC',
        'NHIAC', 'NHAAC', 'NHNAC'
    ]
    _HISPANIC_RACES = [
        'H', 'HWA', 'HBA', 'HIA', 'HAA', 'HNA', 'HTOM', 'HWAC', 'HBAC', 'HIAC',
        'HAAC', 'HNAC'
    ]

    # df1['NH'] = df1['H'] = 0
    for p in _NOT_HISPANIC_RACES:
        df1[p] = (df[p + '_MALE'] + df[p + '_FEMALE']).copy()

    for p in _HISPANIC_RACES:
        df1[p] = (df[p + '_MALE'] + df[p + '_FEMALE']).copy()

    df1.to_csv(output_file_path + output_file_name, header=True, index=False)


def _process_county_files_2020_2023(download_dir):
    """
    Process County files 2020 2022.
    This method generates files for SV available as-is in source 
    file and aggregated SV by adding relevant stats 
    e.g., NH = NH_MALE + NH_FEMALE.

    Args:
      download_dir: download directory - input files are saved here.
    """
    input_file_path = _CODEDIR + download_dir + '2020_2023/county/'
    output_file_path = _CODEDIR + PROCESS_AS_IS_DIR + '2020_2023/county/'
    output_file_name = 'county_2020_2023.csv'
    files_list = os.listdir(input_file_path)
    files_list.sort()

    for file in files_list:
        df = pd.read_csv(input_file_path + file,
                         encoding='ISO-8859-1',
                         low_memory=False)
        # filter by agegrp = 0 (0 = sum of all age group added)
        # filter years 3 - 13 (1, 2 - is base estimate and not for month July)
        df = df.query("AGEGRP == 0 & YEAR not in [1]").copy()

        # convert year code to year
        # Year code starting from 3 for Year 2010
        df['YEAR'] = df['YEAR'] + 2020 - 2

        # add fips code for location
        df.insert(6, 'LOCATION', 'geoId/', True)
        df['LOCATION'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(2) + (
            df['COUNTY'].map(str)).str.zfill(3)

        # drop not reuqire columns
        df.drop(['SUMLEV', 'STATE', 'COUNTY', 'STNAME', 'CTYNAME', 'AGEGRP'],
                axis=1,
                inplace=True)

        if file == files_list[0]:
            df.to_csv(output_file_path + output_file_name, index=False)
        else:
            df.to_csv(output_file_path + output_file_name,
                      index=False,
                      mode='a')

    # Section 2 - Writing Agg data
    df = pd.read_csv(output_file_path + output_file_name)
    output_file_path = _CODEDIR + PROCESS_AGG_DIR + '2020_2023/county/'
    df1 = pd.DataFrame()
    df1['YEAR'] = df['YEAR'].copy()
    df1['LOCATION'] = df['LOCATION'].copy()

    _NOT_HISPANIC_RACES = [
        'NH', 'NHWA', 'NHBA', 'NHIA', 'NHAA', 'NHNA', 'NHTOM', 'NHWAC', 'NHBAC',
        'NHIAC', 'NHAAC', 'NHNAC'
    ]
    _HISPANIC_RACES = [
        'H', 'HWA', 'HBA', 'HIA', 'HAA', 'HNA', 'HTOM', 'HWAC', 'HBAC', 'HIAC',
        'HAAC', 'HNAC'
    ]

    # df1['NH'] = df1['H'] = 0
    for p in _NOT_HISPANIC_RACES:
        df1[p] = (df[p + '_MALE'] + df[p + '_FEMALE']).copy()

    for p in _HISPANIC_RACES:
        df1[p] = (df[p + '_MALE'] + df[p + '_FEMALE']).copy()

    df1.to_csv(output_file_path + output_file_name, header=True, index=False)


def _process_county_files(download_dir):
    """
    Process county files from 1990 - 2020
    Helper function - invokes county_process_file methods for individual decades.

    Args:
      download_dir: download directory - input files are saved here.
    """
    _process_county_files_1990_2000(download_dir)
    _process_county_files_2000_2010(download_dir)
    _process_county_files_2010_2020(download_dir)
    _process_county_files_2020_2023(download_dir)


def _consolidate_national_files():
    """
    Consolidate all national level files into single national level file.
    Only SV relevant for SRH processing are retained and all other stats are 
    dropped.

    This funtion consolidates both as-is and agg data into two seperate files.
    """
    national_as_is_files = [
        _CODEDIR + PROCESS_AS_IS_DIR + yr + '/national/national_' + yr + '.csv'
        for yr in ['1980_1990', '1990_2000', '2000_2010', '2010_2020', '2020_2023']
    ]

    for file in national_as_is_files:
        df = pd.read_csv(file)

        # Drop S, SR columns 2000 - 2010 file
        if file == national_as_is_files[2]:
            df.drop(_SR_COLUMNS, axis=1, inplace=True)

        # Drop S, SR, Race Combination columns 2010 - 2020 file
        if file == national_as_is_files[3]:
            df.drop(_SR_COLUMNS + _SR_CMBN_COLUMNS, axis=1, inplace=True)

        if file == national_as_is_files[4]:
            df.drop(_SR_COLUMNS + _SR_CMBN_COLUMNS, axis=1, inplace=True)

        df = df.melt(id_vars=['YEAR', 'LOCATION'], var_name='SV', value_name='OBSERVATION')
        df.replace({"SV": STAT_VAR_COL_MAPPING}, inplace=True)
        df["SV"] = 'dcid:' + df["SV"]

        df.insert(3, 'MEASUREMENT_METHOD', 'dcs:dcAggregate/CensusPEPSurvey', True)

        df["MEASUREMENT_METHOD"] = df.apply(lambda r: _calculate_agg_measure_method(r.YEAR, r.SV),
                                            axis=1)

        if file == national_as_is_files[0]:
            df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR + 'national_consolidated_temp.csv',
                      header=True,
                      index=False)
        else:
            df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR + 'national_consolidated_temp.csv',
                      header=False,
                      index=False,
                      mode='a')

    df = pd.read_csv(_CODEDIR + PROCESS_AS_IS_DIR + 'national_consolidated_temp.csv')

    df.sort_values(by=['LOCATION', 'SV', 'YEAR'], inplace=True)
    df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR + 'national_consolidated_as_is_final.csv',
              header=True,
              index=False)

    if os.path.exists(_CODEDIR + PROCESS_AS_IS_DIR \
        + 'national_consolidated_temp.csv'):
        os.remove(_CODEDIR + PROCESS_AS_IS_DIR + 'national_consolidated_temp.csv')

    # Aggregate file processing
    national_agg_files = [
        _CODEDIR + PROCESS_AGG_DIR + yr + '/national/national_' + yr + '.csv'
        for yr in ['1980_1990', '1990_2000', '2000_2010', '2010_2020', '2020_2023']
    ]

    for file in national_agg_files:
        df = pd.read_csv(file)
        df = df.melt(id_vars=['YEAR', 'LOCATION'], var_name='SV', value_name='OBSERVATION')
        df.replace({"SV": STAT_VAR_COL_MAPPING}, inplace=True)
        df["SV"] = 'dcid:' + df["SV"]

        if file == national_agg_files[0]:
            df.to_csv(_CODEDIR + PROCESS_AGG_DIR + 'national_consolidated_temp.csv',
                      header=True,
                      index=False)
        else:
            df.to_csv(_CODEDIR + PROCESS_AGG_DIR + 'national_consolidated_temp.csv',
                      header=False,
                      index=False,
                      mode='a')

    df = pd.read_csv(_CODEDIR + PROCESS_AGG_DIR + 'national_consolidated_temp.csv',)
    df.sort_values(by=['LOCATION', 'SV', 'YEAR'], inplace=True)
    df.insert(3, 'MEASUREMENT_METHOD', 'dcs:dcAggregate/CensusPEPSurvey', True)
    df["MEASUREMENT_METHOD"] = df.apply(lambda r: _calculate_agg_measure_method(r.YEAR, r.SV),
                                        axis=1)
    df.to_csv(_CODEDIR + PROCESS_AGG_DIR + 'national_consolidated_agg_final.csv',
              header=True,
              index=False)

    if os.path.exists(_CODEDIR + PROCESS_AGG_DIR \
        + 'national_consolidated_temp.csv'):
        os.remove(_CODEDIR + PROCESS_AGG_DIR + 'national_consolidated_temp.csv')


def _consolidate_state_files():
    """
    Consolidate all (4) state level files into single state level file.
    Only SV relevant for SRH processing are retained and all other stats are 
    dropped.

    This funtion consolidates both as-is and agg data into two seperate files.
    """
    state_as_is_files = [
        _CODEDIR + PROCESS_AS_IS_DIR + yr + '/state/state_' + yr + '.csv'
        for yr in ['1980_1990', '1990_2000', '2000_2010', '2010_2020', '2020_2023']
    ]

    for file in state_as_is_files:
        df = pd.read_csv(file)
        df.drop(_SR_COLUMNS + _SR_CMBN_COLUMNS, axis=1, inplace=True, errors='ignore')
        df = df.melt(id_vars=['YEAR', 'LOCATION'], var_name='SV', value_name='OBSERVATION')
        df.replace({"SV": STAT_VAR_COL_MAPPING}, inplace=True)
        df["SV"] = 'dcid:' + df["SV"]
        df.insert(3, 'MEASUREMENT_METHOD', 'dcs:CensusPEPSurvey', True)
        df["MEASUREMENT_METHOD"] = df.apply(lambda r: _calculate_asis_measure_method(r.YEAR, r.SV),
                                            axis=1)
        if file == state_as_is_files[0]:
            df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR + 'state_consolidated_temp.csv',
                      header=True,
                      index=False)
        else:
            df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR + 'state_consolidated_temp.csv',
                      header=False,
                      index=False,
                      mode='a')

    df = pd.read_csv(_CODEDIR + PROCESS_AS_IS_DIR + 'state_consolidated_temp.csv')
    df.sort_values(by=['LOCATION', 'SV', 'YEAR'], inplace=True)
    df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR + 'state_consolidated_as_is_final.csv',
              header=True,
              index=False)

    if os.path.exists(_CODEDIR + PROCESS_AS_IS_DIR \
        + 'state_consolidated_temp.csv'):
        os.remove(_CODEDIR + PROCESS_AS_IS_DIR + 'state_consolidated_temp.csv')

    # Agg file processing
    state_agg_files = [
        _CODEDIR + PROCESS_AGG_DIR + yr + '/state/state_' + yr + '.csv'
        for yr in ['1980_1990', '1990_2000', '2000_2010', '2010_2020', '2020_2023']
    ]

    for file in state_agg_files:
        df = pd.read_csv(file)
        df = df.melt(id_vars=['YEAR', 'LOCATION'], var_name='SV', value_name='OBSERVATION')
        df.replace({"SV": STAT_VAR_COL_MAPPING}, inplace=True)
        df["SV"] = 'dcid:' + df["SV"]

        if file == state_agg_files[0]:
            df.to_csv(_CODEDIR + PROCESS_AGG_DIR + 'state_consolidated_temp.csv',
                      header=True,
                      index=False)
        else:
            df.to_csv(_CODEDIR + PROCESS_AGG_DIR + 'state_consolidated_temp.csv',
                      header=False,
                      index=False,
                      mode='a')

    df = pd.read_csv(_CODEDIR + PROCESS_AGG_DIR + 'state_consolidated_temp.csv')
    df.sort_values(by=['LOCATION', 'SV', 'YEAR'], inplace=True)
    df.insert(3, 'MEASUREMENT_METHOD', 'dcs:dcAggregate/CensusPEPSurvey', True)
    df["MEASUREMENT_METHOD"] = df.apply(lambda r: _calculate_agg_measure_method(r.YEAR, r.SV),
                                        axis=1)
    df.to_csv(_CODEDIR + PROCESS_AGG_DIR + 'state_consolidated_agg_final.csv',
              header=True,
              index=False)

    if os.path.exists(_CODEDIR + PROCESS_AGG_DIR \
    + 'state_consolidated_temp.csv'):
        os.remove(_CODEDIR + PROCESS_AGG_DIR + 'state_consolidated_temp.csv')

def _consolidate_county_files():
    """
    Consolidate all (4) county level files into single county level file.
    Only SV relevant for SRH processing are retained and all other stats are 
    dropped.

    This funtion consolidates both as-is and agg data into two seperate files.
    """

    county_file = [
        _CODEDIR + PROCESS_AS_IS_DIR + '1990_2000/county/county_1990_2000.csv',
        _CODEDIR + PROCESS_AS_IS_DIR + '2000_2010/county/county_2000_2010.csv',
        _CODEDIR + PROCESS_AS_IS_DIR + '2010_2020/county/county_2010_2020.csv',
        _CODEDIR + PROCESS_AS_IS_DIR + '2020_2023/county/county_2020_2023.csv'
    ]

    for file in county_file:
        df = pd.read_csv(file)
        df.drop(_SR_COLUMNS + _SR_CMBN_COLUMNS, axis=1, inplace=True, errors='ignore')
        df = df.melt(id_vars=['YEAR', 'LOCATION'], var_name='SV', value_name='OBSERVATION')
        df.replace({"SV": STAT_VAR_COL_MAPPING}, inplace=True)
        df["SV"] = 'dcid:' + df["SV"]
        df.insert(3, 'MEASUREMENT_METHOD', 'dcs:CensusPEPSurvey', True)
        df["MEASUREMENT_METHOD"] = df.apply(lambda r: _calculate_asis_measure_method(r.YEAR, r.SV),
                                            axis=1)

        if file == county_file[0]:
            #added by Shamim to keep last values
            df = df.drop_duplicates(subset=['YEAR', 'LOCATION', 'SV', 'MEASUREMENT_METHOD'],
                                    keep='last')
            df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR + 'county_consolidated_temp.csv',
                      header=True,
                      index=False)
        else:
            #added by Shamim to keep last values
            df = df.drop_duplicates(subset=['YEAR', 'LOCATION', 'SV', 'MEASUREMENT_METHOD'],
                                    keep='last')
            df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR + 'county_consolidated_temp.csv',
                      header=False,
                      index=False,
                      mode='a')

    df = pd.read_csv(_CODEDIR + PROCESS_AS_IS_DIR + 'county_consolidated_temp.csv')
    df.sort_values(by=['LOCATION', 'SV', 'YEAR'], inplace=True)
    #added by Shamim to keep last values
    df = df.drop_duplicates(subset=['YEAR', 'LOCATION', 'SV', 'MEASUREMENT_METHOD'], keep='last')
    df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR + 'county_consolidated_as_is_final.csv',
              header=True,
              index=False)

    if os.path.exists(_CODEDIR + PROCESS_AS_IS_DIR \
        + 'county_consolidated_temp.csv'):
        os.remove(_CODEDIR + PROCESS_AS_IS_DIR + 'county_consolidated_temp.csv')

    # Agg file processing
    county_file = [
        _CODEDIR + PROCESS_AS_IS_DIR + '1990_2000/county/county_1990_2000.csv',
        _CODEDIR + PROCESS_AGG_DIR + '1990_2000/county/county_1990_2000.csv',
        _CODEDIR + PROCESS_AGG_DIR + '2000_2010/county/county_2000_2010.csv',
        _CODEDIR + PROCESS_AGG_DIR + '2010_2020/county/county_2010_2020.csv',
        _CODEDIR + PROCESS_AGG_DIR + '2020_2023/county/county_2020_2023.csv'
    ]

    for file in county_file:
        df = pd.read_csv(file)
        df = df.melt(id_vars=['YEAR', 'LOCATION'], var_name='SV', value_name='OBSERVATION')
        df.replace({"SV": STAT_VAR_COL_MAPPING}, inplace=True)
        df["SV"] = 'dcid:' + df["SV"]

        if file == county_file[0]:
            df.to_csv(_CODEDIR + PROCESS_AGG_DIR + 'county_consolidated_temp.csv',
                      header=True,
                      index=False)
        else:
            df.to_csv(_CODEDIR + PROCESS_AGG_DIR + 'county_consolidated_temp.csv',
                      header=False,
                      index=False,
                      mode='a')

    df = pd.read_csv(_CODEDIR + PROCESS_AGG_DIR + 'county_consolidated_temp.csv')
    df.sort_values(by=['LOCATION', 'SV', 'YEAR'], inplace=True)
    df.insert(3, 'MEASUREMENT_METHOD', 'dcs:dcAggregate/CensusPEPSurvey', True)
    df["MEASUREMENT_METHOD"] = df.apply(lambda r: _calculate_agg_measure_method(r.YEAR, r.SV),
                                        axis=1)
    df.to_csv(_CODEDIR + PROCESS_AGG_DIR + 'county_consolidated_agg_final.csv',
              header=True,
              index=False)

    if os.path.exists(_CODEDIR + PROCESS_AGG_DIR \
        + 'county_consolidated_temp.csv'):
        os.remove(_CODEDIR + PROCESS_AGG_DIR + 'county_consolidated_temp.csv')



def _consolidate_all_geo_files():
    """
    Consolidate National, State and County files into single file
    This function generates final csv file for both as-is and agg
    data processing which will be used for importing into DC.

    Output files are written to /output_files/ folder
    """
    as_is_df = pd.DataFrame()
    for file in [
            _CODEDIR + PROCESS_AS_IS_DIR + geo + '_consolidated_as_is_final.csv'
            for geo in ['national', 'state', 'county']
    ]:
        as_is_df = pd.concat([as_is_df, pd.read_csv(file)])
    #added by Shamim to keep last values
    as_is_df = as_is_df.drop_duplicates(
        subset=['YEAR', 'LOCATION', 'SV', 'MEASUREMENT_METHOD'], keep='last')
    as_is_df.to_csv(_CODEDIR + OUTPUT_DIR + 'population_estimate_by_srh.csv',
                    header=True,
                    index=False)

    agg_df = pd.DataFrame()
    for file in [
            _CODEDIR + PROCESS_AGG_DIR + geo + '_consolidated_agg_final.csv'
            for geo in ['national', 'state', 'county']
    ]:
        agg_df = pd.concat([agg_df, pd.read_csv(file)])
        #Added by shamim
        agg_df = agg_df.drop_duplicates(
            subset=['YEAR', 'LOCATION', 'MEASUREMENT_METHOD', 'SV'],
            keep='last')
        agg_df.to_csv(_CODEDIR + OUTPUT_DIR +
                      'population_estimate_by_srh_agg.csv',
                      header=True,
                      index=False)


def _consolidate_files():
    """
    Consolidate National, State and County files into single file.
    Two seperate files - consolidates-as-is and consolidated-agg files are 
    created
    """
    _consolidate_county_files()
    _consolidate_state_files()
    _consolidate_national_files()
    _consolidate_all_geo_files()

def add_future_year_urls():
    global _FILES_TO_DOWNLOAD
    with open(os.path.join(_MODULE_DIR, 'input_url.json'), 'r') as input_file:
        _FILES_TO_DOWNLOAD = json.load(input_file)
    urls_to_scan = [
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/counties/asrh/cc-est{YEAR}-alldata.csv",
        "https://www2.census.gov/programs-surveys/popest/tables/2020-{YEAR}/state/asrh/sasrh90.txt",
        "https://www2.census.gov/programs-surveys/popest/tables/2020-{YEAR}/state/asrh/sasrh91.txt",
        "https://www2.census.gov/programs-surveys/popest/tables/2020-{YEAR}/state/asrh/sasrh92.txt",
        "https://www2.census.gov/programs-surveys/popest/tables/2020-{YEAR}/state/asrh/sasrh93.txt",
        "https://www2.census.gov/programs-surveys/popest/tables/2020-{YEAR}/state/asrh/sasrh94.txt",
        "https://www2.census.gov/programs-surveys/popest/tables/2020-{YEAR}/state/asrh/sasrh95.txt",
        "https://www2.census.gov/programs-surveys/popest/tables/2020-{YEAR}/state/asrh/sasrh96.txt",
        "https://www2.census.gov/programs-surveys/popest/tables/2020-{YEAR}/state/asrh/sasrh97.txt",
        "https://www2.census.gov/programs-surveys/popest/tables/2020-{YEAR}/state/asrh/sasrh98.txt",
        "https://www2.census.gov/programs-surveys/popest/tables/2020-{YEAR}/state/asrh/sasrh99.txt"
        
    ]
    if dt.now().year < 2023:
        YEAR = dt.now().year
        for url in urls_to_scan:
            url_to_check = url.format(YEAR=YEAR)
            try:
                check_url = requests.head(url_to_check)
                if check_url.status_code == 200:
                    _FILES_TO_DOWNLOAD.append({"download_path": url_to_check})

            except:
                logging.error(f"URL is not accessable {url_to_check}")



def download_files():
    global _FILES_TO_DOWNLOAD
    session = requests.session()
    max_retry = 5
    for file_to_dowload in _FILES_TO_DOWNLOAD:
        file_name_to_save = None
        url = file_to_dowload['download_path']
        if 'file_name' in file_to_dowload and len(file_to_dowload['file_name'] > 5):
            file_name_to_save = file_to_dowload['file_name']
        else:
            file_name_to_save = url.split('/')[-1]
        if 'file_path' in file_to_dowload:
            file_name_to_save = file_to_dowload['file_path'] + file_name_to_save
        retry_number = 0

        is_file_downloaded = False
        while is_file_downloaded == False:
            try:
                with session.get(url, stream=True) as response:
                    response.raise_for_status()
                    if response.status_code == 200:
                        with open(os.path.join(_INPUT_FILE_PATH, file_name_to_save), 'wb') as f:
                            #shutil.copyfileobj(response.raw, f)
                            f.write(response.content)
                            file_to_dowload['is_downloaded'] = True
                            logging.info(f"Downloaded file : {url}")
                            is_file_downloaded = True
                    else:
                        logging.info(f"Retry file download {{url}}")
                        time.sleep(5)
                        retry_number += 1
                        if retry_number > max_retry:
                            logging.error(f"Error downloading {url}")
                            logging.error("Exit from script")
                            sys.exit(0)

            except Exception as e:
                logging.error(f"Retry file download {url}")
                time.sleep(5)
                retry_number += 1
                if retry_number > max_retry:
                    logging.error(f"Error downloading {url}")
                    logging.error("Exit from script")
                    sys.exit(0)
    return True

def _process_files(download_dir):
    """
    Process county, state and national files.
    This is helper method which will give call to geo level file processing 
    methods

    Args:
      download_dir: download directory - input files are saved here.
    """
    _process_county_files(download_dir)
    _process_state_files(download_dir)
    # _process_geo_level_aggregations will process state 2000 - 2020 data
    # and national 1980 - 2020 data
    _process_geo_level_aggregation()


def _create_output_n_process_folders():
    """
    Create directories for processing data and saving final output
    """
    for d in WORKING_DIRECTORIES:
        os.system("mkdir -p " + _CODEDIR + d)


def process(data_directory):
    """
    Produce As Is and Agg output files for National, State and County
    Produce MCF and tMCF files for both As-Is and Agg output files

    Args:
      download_dir: download directory - input files are saved here.
    """
    _create_output_n_process_folders()
    _process_files(data_directory)
    _consolidate_files()
    generate_mcf()
    generate_tmcf()


def main(_):
    """
    Produce As Is and Agg output files for National, State and County
    Produce MCF and tMCF files for both As-Is and Agg output files
    """
    _create_output_n_process_folders()
    add_future_year_urls()
    download_status = download_files()
    if download_status:
        process(_FLAGS.data_directory)



if __name__ == '__main__':
    app.run(main)