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
    2020 - 2029     Processed As Is
    
State
    1980 - 1990     Processed As Is
    1990 - 2000     Processed As Is
    2000 - 2010     Aggregated from County to state
                    (data matches with State Level files available)
    2010 - 2020     Aggregated from County to state
                    (data matches with State Level files available)
    2020 - 2029     Aggregated from County to state
                    (data matches with State Level files available)              

National
    1980 - 1990     Aggregted from State to National Level
    1990 - 2000     Aggregted from State to National Level
    2000 - 2010     Aggregted from State to National Level
    2010 - 2020     Aggregted from State to National Level
    2020 - 2029     Aggregted from State to National Level

Also SV aggregation are produced while processing above files.
E.g., Count_Person_White_HispanicOrLatino is calulated by addding
Count_Person_Male_WhiteHispanicOrLatino and
Count_Person_Female_WhiteHispanicOrLatino

input_url - essentially represents the URL of the file to be downloaded, which is extracted from the file_to_download dictionary
Also There is a function that automatically generate and add URLs for future years of data download.

Folder information
input_url - essentially represents the URL of the file to be downloaded, which is extracted from the file_to_download dictionary
input_files - downloaded files from the provided URLs (from US census website) are placed here
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

_FLAGS = flags.FLAGS

flags.DEFINE_string('mode', '', 'Options: download or process')

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = os.path.join(_MODULE_DIR, 'input_files')
output_path = '/output_files/'
_FILES_TO_DOWNLOAD = []

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_FLAGS = flags.FLAGS
flags.DEFINE_string(
    "data_directory", DOWNLOAD_DIR,
    "Folder consisting of all input files required for processing")

# Columns with single race(SR) or combination(SR CMBN) with one or more race
# These columns are not used as part of current import
# belwo are the Columns to be retained when SR COLUMNS is dropped
# Columns with single race(SR) or combination(SR CMBN) with one or more race
# These columns are not used as part of current import
# belwo are the Columns to be retained when SR COLUMNS is dropped
_SR_COLUMNS_DROPPED = [
    'YEAR', 'LOCATION', 'NH_MALE', 'NH_FEMALE', 'NHWA_MALE', 'NHWA_FEMALE',
    'NHBA_MALE', 'NHBA_FEMALE', 'NHIA_MALE', 'NHIA_FEMALE', 'NHAA_MALE',
    'NHAA_FEMALE', 'NHNA_MALE', 'NHNA_FEMALE', 'NHTOM_MALE', 'NHTOM_FEMALE',
    'H_MALE', 'H_FEMALE', 'HWA_MALE', 'HWA_FEMALE', 'HBA_MALE', 'HBA_FEMALE',
    'HIA_MALE', 'HIA_FEMALE', 'HAA_MALE', 'HAA_FEMALE', 'HNA_MALE',
    'HNA_FEMALE', 'HTOM_MALE', 'HTOM_FEMALE'
]

# belwo are the Columns to be retained when both SR COLUMNS and SR CMBN COLUMNS are dropped
_SR_CMBN_COLUMNS_DROPPED = [
    'YEAR', 'LOCATION', 'NH_MALE', 'NH_FEMALE', 'NHWA_MALE', 'NHWA_FEMALE',
    'NHBA_MALE', 'NHBA_FEMALE', 'NHIA_MALE', 'NHIA_FEMALE', 'NHAA_MALE',
    'NHAA_FEMALE', 'NHNA_MALE', 'NHNA_FEMALE', 'NHTOM_MALE', 'NHTOM_FEMALE',
    'NHWAC_MALE', 'NHWAC_FEMALE', 'NHBAC_MALE', 'NHBAC_FEMALE', 'NHIAC_MALE',
    'NHIAC_FEMALE', 'NHAAC_MALE', 'NHAAC_FEMALE', 'NHNAC_MALE', 'NHNAC_FEMALE',
    'H_MALE', 'H_FEMALE', 'HWA_MALE', 'HWA_FEMALE', 'HBA_MALE', 'HBA_FEMALE',
    'HIA_MALE', 'HIA_FEMALE', 'HAA_MALE', 'HAA_FEMALE', 'HNA_MALE',
    'HNA_FEMALE', 'HTOM_MALE', 'HTOM_FEMALE', 'HWAC_MALE', 'HWAC_FEMALE',
    'HBAC_MALE', 'HBAC_FEMALE', 'HIAC_MALE', 'HIAC_FEMALE', 'HAAC_MALE',
    'HAAC_FEMALE', 'HNAC_MALE', 'HNAC_FEMALE'
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
    2020 - 2029     Aggregated from County to state
                    (data matches with State Level files available)                

    National
    1980 - 1990     Aggregated from State to National Level
    1990 - 2000     Aggregated from State to National Level
    2000 - 2010     Aggregated from State to National Level
    2010 - 2020     Aggregated from State to National Level
    2020 - 2029     Aggregated from State to National Level
    """

    # Below dictionary holds list of years and geo details for which
    # data needs to be aggregated.
    # Dictionary key provides Geo and Year information for which data is
    # aggregated. Dictionary value is a list which provides details of input
    # folder name, input file name, output folder name, output file name and
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
        'state_2020_2029': [
            '2020_2029/county/', 'county_2020_2029.csv', '2020_2029/state/',
            'state_2020_2029.csv', 'state'
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
        'national_2020_2029': [
            '2020_2029/state/', 'state_2020_2029.csv', '2020_2029/national/',
            'national_2020_2029.csv', 'national'
        ]
    }

    try:
        # Loop through the files for aggregation based on geographical level
        for geo_agg_file, details in file_process_details.items():
            for measurement_method in ['as-is', 'aggregate']:
                if measurement_method == 'as-is':
                    input_file_path = _CODEDIR + PROCESS_AS_IS_DIR + details[0]
                    output_file_path = _CODEDIR + PROCESS_AS_IS_DIR + details[2]
                else:
                    input_file_path = _CODEDIR + PROCESS_AGG_DIR + details[0]
                    output_file_path = _CODEDIR + PROCESS_AGG_DIR + details[2]

                input_file_name = details[1]
                output_file_name = details[3]
                geo_level = details[4]

                # Check if the input file exists before attempting to process it
                if not os.path.exists(input_file_path + input_file_name):
                    logging.error(
                        f"Input file does not exist: {input_file_path + input_file_name}"
                    )
                    continue  # Skip to the next aggregation if input file doesn't exist

                # Check if the output directory exists; if not, create it
                if not os.path.exists(output_file_path):
                    os.makedirs(output_file_path)
                    logging.info(
                        f"Created output directory: {output_file_path}")

                # Process the geographical aggregation
                _process_geo_aggregation(input_file_path, input_file_name,
                                         output_file_path, output_file_name,
                                         geo_level)
                logging.info(
                    f"Geo-level aggregation successful for {geo_agg_file} ({measurement_method})"
                )

    except Exception as e:
        # If any exception occurs, log it and stop the function
        logging.fatal(f"Fatal error during geo-level aggregation: {e}")
        return


def _process_state_files_1980_1990(download_dir):
    """
    Process state files from year 1980 - 1990

    Source files (for 1980 - 1990) consist of age information in brackets 
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

    _NOT_HISPANIC_RACES = ['NH-W', 'NH-B', 'NH-AI', 'NH-API']
    _HISPANIC_RACES = ['H-W', 'H-B', 'H-AI', 'H-API']

    try:
        # List and sort files in the input directory
        files_list = os.listdir(input_file_path)
        files_list.sort()

        # Check if files exist in the input directory
        if not files_list:
            logging.fatal(
                f"No input files found in the directory: {input_file_path}")
            return

        # Track the number of files processed successfully
        files_processed = 0

        for file in files_list:
            try:
                # Read the fixed width files
                df = pd.read_fwf(input_file_path + file,
                                 names=column_names,
                                 colspecs=column_specification)

                # Aggregate age columns into 'ALL_AGE'
                df["ALL_AGE"] = 0
                for age in age_columns:
                    df["ALL_AGE"] += df[age]

                # Drop individual age columns
                df.drop(age_columns, axis=1, inplace=True)

                # Pivot the data by LOCATION and YEAR_TEMP, with multi-level columns
                df = df.pivot(index=['LOCATION', 'YEAR_TEMP'],
                              columns=['RACE_ORIGIN', 'SEX'],
                              values='ALL_AGE').reset_index()

                # Write the intermediate file
                df.to_csv(output_file_path + output_temp_file_name,
                          header=True,
                          index=False)

                # Load the temp file back, remove any NaNs and convert to int
                df = pd.read_csv(output_file_path + output_temp_file_name)
                df = df.dropna()

                # Convert float columns to int
                float_col = df.select_dtypes(include=['float64'])
                for col in float_col.columns.values:
                    df[col] = df[col].astype('int64')

                # Insert the correct 'YEAR' column and format LOCATION
                df.insert(0, 'YEAR', 1980 + df['YEAR_TEMP'], True)
                df['LOCATION'] = 'geoId/' + (
                    df['LOCATION'].map(str)).str.zfill(2)
                df.drop(["YEAR_TEMP"], axis=1, inplace=True)

                # Define column headers
                column_header = ['YEAR', 'LOCATION']
                for p in _NOT_HISPANIC_RACES:
                    column_header.append(p + '-M')
                    column_header.append(p + '-F')
                for p in _HISPANIC_RACES:
                    column_header.append(p + '-M')
                    column_header.append(p + '-F')

                # Map the old column names to the new column names
                column_mapping = {
                    old: new for old, new in zip(df.columns, column_header)
                }

                # Use df.rename() to rename columns
                df.rename(columns=column_mapping, inplace=True)

                # Write to the final output file, appending if necessary
                if file == files_list[0]:
                    df.to_csv(output_file_path + output_file_name, index=False)
                else:
                    df.to_csv(output_file_path + output_file_name,
                              index=False,
                              mode='a')

                # Remove the temporary file
                if os.path.exists(output_file_path + output_temp_file_name):
                    os.remove(output_file_path + output_temp_file_name)

                files_processed += 1

            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")
                continue  # Continue processing the next file

        # After processing all files, ensure all files were processed
        if files_processed != len(files_list):
            logging.fatal(
                f"File processing mismatch: Expected {len(files_list)} files, but processed {files_processed}. Output file generation aborted."
            )
            return

        # Section 2 - Writing Aggregated data
        output_file_path = _CODEDIR + PROCESS_AGG_DIR + '1980_1990/state/'

        # Aggregating data by race groups
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

        # Write the aggregated data
        df1.to_csv(output_file_path + output_file_name,
                   header=True,
                   index=False)
        logging.info("Aggregated data saved successfully to: %s",
                     output_file_path + output_file_name)

    except Exception as e:
        logging.fatal(f"Error during processing of 1980-1990 state files: {e}")
        return


def _process_state_files_1990_2000(download_dir):
    """
    Process state files from 1990 - 2000
    
    There are 10 files in total for each year (1990 - 1999).
    Each yearly file consists of Population Census for all states.

    All files are available in the same format.

    Args:
      download_dir: download directory - input files are saved here.
    """

    try:
        # Section 1 - Writing As Is Data
        input_file_path = _CODEDIR + download_dir + '1990_2000/state/'
        output_file_path = _CODEDIR + PROCESS_AS_IS_DIR + '1990_2000/state/'
        output_file_name = 'state_1990_2000.csv'
        output_temp_file_name = 'state_1990_2000_temp.csv'

        column_names = [
            "YEAR", "LOCATION", "AGE", "NH-W-M", "NH-W-F", "NH-B-M", "NH-B-F",
            "NH-AIAN-M", "NH-AIAN-F", "NH-API-M", "NH-API-F", "H-W-M", "H-W-F",
            "H-B-M", "H-B-F", "H-AIAN-M", "H-AIAN-F", "H-API-M", "H-API-F"
        ]

        # Column specification - Link to metadata file:
        # https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/1990-2000/sasrh_rl.txt
        column_specification = [(0, 4), (5, 7), (8, 11), (12, 19), (19, 26),
                                (27, 34), (34, 41), (42, 49), (49, 56),
                                (57, 64), (64, 71), (72, 79), (79, 86),
                                (87, 94), (94, 101), (102, 109), (109, 116),
                                (117, 124), (124, 131)]

        # Read all files and concatenate them into a temporary file before further processing
        files_list = os.listdir(input_file_path)
        files_list.sort()

        if not files_list:
            logging.fatal(
                f"No input files found in directory: {input_file_path}")
            return

        for file in files_list:
            try:
                temp_file_df = pd.read_fwf(input_file_path + file,
                                           encoding='latin-1',
                                           names=column_names,
                                           colspecs=column_specification,
                                           skiprows=16)

                if file == files_list[0]:
                    temp_file_df.to_csv(output_file_path +
                                        output_temp_file_name,
                                        header=True,
                                        index=False)
                else:
                    temp_file_df.to_csv(output_file_path +
                                        output_temp_file_name,
                                        header=False,
                                        index=False,
                                        mode='a')
            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")
                continue  # Proceed with the next file if this one fails

        # After processing all files, aggregate the data
        df = pd.read_csv(output_file_path + output_temp_file_name)
        df.drop(["AGE"], axis=1, inplace=True)
        df = df.groupby(['YEAR', 'LOCATION']).agg('sum').reset_index()
        df['LOCATION'] = 'geoId/' + df['LOCATION'].map(str).str.zfill(2)
        df.to_csv(output_file_path + output_file_name, index=False)

        # Delete the temporary concatenated file
        if os.path.exists(output_file_path + output_temp_file_name):
            os.remove(output_file_path + output_temp_file_name)

        # Section 2 - Writing Aggregated Data
        output_file_path = _CODEDIR + PROCESS_AGG_DIR + '1990_2000/state/'

        # Prepare aggregated data
        df1 = pd.DataFrame()
        df1['YEAR'] = df['YEAR'].copy()
        df1['LOCATION'] = df['LOCATION'].copy()

        _NOT_HISPANIC_RACES = ['NH-W', 'NH-B', 'NH-AIAN', 'NH-API']
        _HISPANIC_RACES = ['H-W', 'H-B', 'H-AIAN', 'H-API']

        df1['NH'] = df1['H'] = 0

        # Aggregate Non-Hispanic races
        for p in _NOT_HISPANIC_RACES:
            df1['NH'] += (df[p + '-M'] + df[p + '-F']).copy()
            df1[p] = (df[p + '-M'] + df[p + '-F']).copy()

        # Aggregate Hispanic races
        for p in _HISPANIC_RACES:
            df1['H'] += (df[p + '-M'] + df[p + '-F']).copy()
            df1[p] = (df[p + '-M'] + df[p + '-F']).copy()

        # Write aggregated data to output CSV
        df1.to_csv(output_file_path + output_file_name,
                   header=True,
                   index=False)
        logging.info(
            f"Aggregated data saved successfully to: {output_file_path + output_file_name}"
        )

    except Exception as e:
        logging.fatal(
            f"Fatal error during the processing of 1990-2000 state files: {e}")
        return


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
    Process County files 1990-2000.
    This method generates CSV files for as-is data (e.g., for SV such as 
    H-W) and aggregated data (e.g., NH = NH-W + NH-B + NH-AIAN + NH-API).

    Args:
      download_dir: download directory - input files are saved here.
    """

    try:
        # Section 1 - Writing As Is Data
        input_file_path = _CODEDIR + download_dir + '1990_2000/county/'
        output_file_path = _CODEDIR + PROCESS_AS_IS_DIR + '1990_2000/county/'
        output_file_name = 'county_1990_2000.csv'

        if not os.path.exists(input_file_path):
            logging.fatal(f"Input directory does not exist: {input_file_path}")
            return

        if not os.path.exists(output_file_path):
            logging.fatal(
                f"Output directory does not exist: {output_file_path}")
            return

        files_list = os.listdir(input_file_path)
        if not files_list:
            logging.fatal(f"No files found in the directory: {input_file_path}")
            return

        files_list.sort()

        column_names = [
            "YEAR", "LOCATION", "NH-W", "NH-B", "NH-AIAN", "NH-API", "H-W",
            "H-B", "H-AIAN", "H-API"
        ]

        # Column specification reference file:
        # https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/1990-2000/co-99-10-rl.txt
        column_specification = [(0, 4), (5, 10), (10, 19), (19, 28), (28, 37),
                                (37, 46), (46, 55), (55, 64), (64, 73),
                                (73, 82)]

        for file in files_list:
            try:
                df = pd.read_fwf(input_file_path + file,
                                 encoding='latin-1',
                                 names=column_names,
                                 colspecs=column_specification,
                                 header=None,
                                 skiprows=18)

                # Add geoId to LOCATION column
                df['LOCATION'] = 'geoId/' + (
                    df['LOCATION'].map(str)).str.zfill(5)

                # Write to CSV (append if not the first file)
                if file == files_list[0]:
                    df.to_csv(output_file_path + output_file_name, index=False)
                else:
                    df.to_csv(output_file_path + output_file_name,
                              index=False,
                              mode='a',
                              header=False)

                logging.info(f"Processed and saved file: {file}")

            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")
                continue  # Continue with the next file if this one fails

        # Section 2 - Writing Aggregated Data
        output_file_path = _CODEDIR + PROCESS_AGG_DIR + '1990_2000/county/'

        df1 = pd.DataFrame()
        df1['YEAR'] = df['YEAR'].copy()
        df1['LOCATION'] = df['LOCATION'].copy()
        df1['NH'] = (df['NH-W'] + df['NH-B'] + df['NH-AIAN'] +
                     df['NH-API']).copy()
        df1['H'] = (df['H-W'] + df['H-B'] + df['H-AIAN'] + df['H-API']).copy()

        df1.to_csv(output_file_path + output_file_name,
                   header=True,
                   index=False)
        logging.info(
            f"Aggregated data saved successfully to: {output_file_path + output_file_name}"
        )

    except Exception as e:
        logging.fatal(
            f"Fatal error during the processing of county files 1990-2000: {e}")
        return


def _process_county_files_2000_2010(download_dir):
    """
    Process County files 2000-2010.
    This method generates CSV files for as-is data (e.g., for SV such as NHWA, NHBA etc.)
    and aggregated data (e.g., NH = NH_MALE + NH_FEMALE).

    Args:
        download_dir: download directory - input files are saved here.
    """
    try:
        # Section 1 - Writing As Is data
        input_file_path = _CODEDIR + download_dir + '2000_2010/county/'
        output_file_path = _CODEDIR + PROCESS_AS_IS_DIR + '2000_2010/county/'
        output_file_name = 'county_2000_2010.csv'

        # List and sort the files in the input directory
        files_list = os.listdir(input_file_path)
        files_list.sort()

        # Expected number of files
        expected_files_count = len(files_list)

        # Check if the number of files in the directory matches the expected count
        if not files_list:
            logging.error(
                f"No input files found in the directory: {input_file_path}")
            return

        if len(files_list) != expected_files_count:
            logging.error(
                f"Mismatch in the number of input files. Expected {expected_files_count} files, but found {len(files_list)}."
            )
            return

        files_processed = 0  # Track the number of successfully processed files

        # Read and process each file
        for file in files_list:
            try:
                df = pd.read_csv(input_file_path + file, encoding='ISO-8859-1')

                # Apply filtering and transformation
                df = df.query('AGEGRP == 99 & YEAR not in [1, 12, 13]').copy()
                df['YEAR'] = 2000 - 2 + df['YEAR']
                df.insert(7, 'LOCATION', '', True)
                df['LOCATION'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(
                    2) + (df['COUNTY'].map(str)).str.zfill(3)

                # Dynamically select columns to keep
                columns_to_keep = ['YEAR', 'LOCATION'
                                  ]  # Retain YEAR and LOCATION columns

                # Population columns (male and female for various racial/ethnic groups)
                population_columns = [
                    'TOT_POP', 'TOT_MALE', 'TOT_FEMALE', 'WA_MALE', 'WA_FEMALE',
                    'BA_MALE', 'BA_FEMALE', 'IA_MALE', 'IA_FEMALE', 'AA_MALE',
                    'AA_FEMALE', 'NA_MALE', 'NA_FEMALE', 'TOM_MALE',
                    'TOM_FEMALE', 'NH_MALE', 'NH_FEMALE', 'NHWA_MALE',
                    'NHWA_FEMALE', 'NHBA_MALE', 'NHBA_FEMALE', 'NHIA_MALE',
                    'NHIA_FEMALE', 'NHAA_MALE', 'NHAA_FEMALE', 'NHNA_MALE',
                    'NHNA_FEMALE', 'NHTOM_MALE', 'NHTOM_FEMALE', 'H_MALE',
                    'H_FEMALE', 'HWA_MALE', 'HWA_FEMALE', 'HBA_MALE',
                    'HBA_FEMALE', 'HIA_MALE', 'HIA_FEMALE', 'HAA_MALE',
                    'HAA_FEMALE', 'HNA_MALE', 'HNA_FEMALE', 'HTOM_MALE',
                    'HTOM_FEMALE'
                ]

                # Add population columns to columns_to_keep
                columns_to_keep.extend(population_columns)

                # Retain only the necessary columns
                df = df[columns_to_keep]

                # Append data to the output CSV
                if file == files_list[0]:
                    df.to_csv(output_file_path + output_file_name,
                              header=True,
                              index=False)
                else:
                    df.to_csv(output_file_path + output_file_name,
                              header=False,
                              index=False,
                              mode='a')

                logging.info(f"Processed and saved file: {file}")

            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")
                continue  # Continue with the next file if this one fails

        # Section 2 - Writing Aggregated data
        df = pd.read_csv(output_file_path + output_file_name)
        output_file_path = _CODEDIR + PROCESS_AGG_DIR + '2000_2010/county/'

        df1 = pd.DataFrame()
        df1['YEAR'] = df['YEAR'].copy()
        df1['LOCATION'] = df['LOCATION'].copy()

        _NOT_HISPANIC_RACES = [
            'NH', 'NHWA', 'NHBA', 'NHIA', 'NHAA', 'NHNA', 'NHTOM'
        ]
        _HISPANIC_RACES = ['H', 'HWA', 'HBA', 'HIA', 'HAA', 'HNA', 'HTOM']

        # Process the non-Hispanic and Hispanic races
        for p in _NOT_HISPANIC_RACES:
            df1[p] = (df[p + '_MALE'] + df[p + '_FEMALE']).copy()

        for p in _HISPANIC_RACES:
            df1[p] = (df[p + '_MALE'] + df[p + '_FEMALE']).copy()

        # Save the aggregated data to CSV
        df1.to_csv(output_file_path + output_file_name,
                   header=True,
                   index=False)
        logging.info("Aggregated data saved successfully to: %s",
                     output_file_path + output_file_name)

    except Exception as e:
        logging.fatal(
            f"Fatal error during the processing of county files 2000-2010: {e}")
        return


def _process_county_files_2010_2020(download_dir):
    """
    Process County files 2010-2020.
    This method generates files for SV available as-is in source 
    file and aggregated SV by adding relevant stats 
    e.g., NH = NH_MALE + NH_FEMALE.

    Args:
      download_dir: download directory - input files are saved here.
    """

    try:
        # Section 1 - Writing As Is Data
        input_file_path = _CODEDIR + download_dir + '2010_2020/county/'
        output_file_path = _CODEDIR + PROCESS_AS_IS_DIR + '2010_2020/county/'
        output_file_name = 'county_2010_2020.csv'

        if not os.path.exists(input_file_path):
            logging.fatal(f"Input directory does not exist: {input_file_path}")
            return

        if not os.path.exists(output_file_path):
            logging.fatal(
                f"Output directory does not exist: {output_file_path}")
            return

        files_list = os.listdir(input_file_path)
        if not files_list:
            logging.fatal(f"No files found in the directory: {input_file_path}")
            return

        files_list.sort()

        for file in files_list:
            try:
                df = pd.read_csv(input_file_path + file,
                                 encoding='ISO-8859-1',
                                 low_memory=False)

                # Filter by AGEGRP = 0 (sum of all age groups added)
                # Filter out base estimates (YEAR 1, 2) and year 13 (already processed)
                df = df.query("AGEGRP == 0 & YEAR not in [1, 2, 13]").copy()

                # Convert year code to actual year
                df['YEAR'] = df['YEAR'] + 2010 - 3

                # Add fips code for location
                df.insert(6, 'LOCATION', 'geoId/', True)
                df['LOCATION'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(
                    2) + (df['COUNTY'].map(str)).str.zfill(3)

                # Dynamically select columns to keep
                columns_to_keep = ['YEAR', 'LOCATION'
                                  ]  # Retain YEAR and LOCATION columns

                # Population columns (male and female for various racial/ethnic groups)
                population_columns = [
                    'TOT_POP', 'TOT_MALE', 'TOT_FEMALE', 'WA_MALE', 'WA_FEMALE',
                    'BA_MALE', 'BA_FEMALE', 'IA_MALE', 'IA_FEMALE', 'AA_MALE',
                    'AA_FEMALE', 'NA_MALE', 'NA_FEMALE', 'TOM_MALE',
                    'TOM_FEMALE', 'WAC_MALE', 'WAC_FEMALE', 'BAC_MALE',
                    'BAC_FEMALE', 'IAC_MALE', 'IAC_FEMALE', 'AAC_MALE',
                    'AAC_FEMALE', 'NAC_MALE', 'NAC_FEMALE', 'NH_MALE',
                    'NH_FEMALE', 'NHWA_MALE', 'NHWA_FEMALE', 'NHBA_MALE',
                    'NHBA_FEMALE', 'NHIA_MALE', 'NHIA_FEMALE', 'NHAA_MALE',
                    'NHAA_FEMALE', 'NHNA_MALE', 'NHNA_FEMALE', 'NHTOM_MALE',
                    'NHTOM_FEMALE', 'NHWAC_MALE', 'NHWAC_FEMALE', 'NHBAC_MALE',
                    'NHBAC_FEMALE', 'NHIAC_MALE', 'NHIAC_FEMALE', 'NHAAC_MALE',
                    'NHAAC_FEMALE', 'NHNAC_MALE', 'NHNAC_FEMALE', 'H_MALE',
                    'H_FEMALE', 'HWA_MALE', 'HWA_FEMALE', 'HBA_MALE',
                    'HBA_FEMALE', 'HIA_MALE', 'HIA_FEMALE', 'HAA_MALE',
                    'HAA_FEMALE', 'HNA_MALE', 'HNA_FEMALE', 'HTOM_MALE',
                    'HTOM_FEMALE', 'HWAC_MALE', 'HWAC_FEMALE', 'HBAC_MALE',
                    'HBAC_FEMALE', 'HIAC_MALE', 'HIAC_FEMALE', 'HAAC_MALE',
                    'HAAC_FEMALE', 'HNAC_MALE', 'HNAC_FEMALE'
                ]

                # Add population columns to columns_to_keep
                columns_to_keep.extend(population_columns)

                # Retain only the necessary columns
                df = df[columns_to_keep]

                # Write processed data to the output file
                if file == files_list[0]:
                    df.to_csv(output_file_path + output_file_name, index=False)
                else:
                    df.to_csv(output_file_path + output_file_name,
                              index=False,
                              mode='a',
                              header=False)

                logging.info(f"Processed and saved file: {file}")

            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")
                continue  # Continue with the next file if this one fails

        # Section 2 - Writing Aggregated Data
        df = pd.read_csv(output_file_path + output_file_name)
        output_file_path = _CODEDIR + PROCESS_AGG_DIR + '2010_2020/county/'

        df1 = pd.DataFrame()
        df1['YEAR'] = df['YEAR'].copy()
        df1['LOCATION'] = df['LOCATION'].copy()

        _NOT_HISPANIC_RACES = [
            'NH', 'NHWA', 'NHBA', 'NHIA', 'NHAA', 'NHNA', 'NHTOM', 'NHWAC',
            'NHBAC', 'NHIAC', 'NHAAC', 'NHNAC'
        ]
        _HISPANIC_RACES = [
            'H', 'HWA', 'HBA', 'HIA', 'HAA', 'HNA', 'HTOM', 'HWAC', 'HBAC',
            'HIAC', 'HAAC', 'HNAC'
        ]

        # Dynamically aggregate male and female data for races
        for p in _NOT_HISPANIC_RACES:
            df1[p] = (df[p + '_MALE'] + df[p + '_FEMALE']).copy()

        for p in _HISPANIC_RACES:
            df1[p] = (df[p + '_MALE'] + df[p + '_FEMALE']).copy()

        df1.to_csv(output_file_path + output_file_name,
                   header=True,
                   index=False)
        logging.info(
            f"Aggregated data saved successfully to: {output_file_path + output_file_name}"
        )

    except Exception as e:
        logging.fatal(
            f"Fatal error during the processing of county files 2010-2020: {e}")
        return


def _process_county_files_2020_2029(download_dir):
    """
    Process County files 2020-2029.
    This method generates files for SV available as-is in source 
    file and aggregated SV by adding relevant stats 
    e.g., NH = NH_MALE + NH_FEMALE.

    Args:
      download_dir: download directory - input files are saved here.
    """

    try:
        # Section 1 - Writing As Is Data
        input_file_path = _CODEDIR + download_dir + '2020_2029/county/'
        output_file_path = _CODEDIR + PROCESS_AS_IS_DIR + '2020_2029/county/'
        output_file_name = 'county_2020_2029.csv'

        if not os.path.exists(input_file_path):
            logging.fatal(f"Input directory does not exist: {input_file_path}")
            return

        if not os.path.exists(output_file_path):
            logging.fatal(
                f"Output directory does not exist: {output_file_path}")
            return

        files_list = os.listdir(input_file_path)
        if not files_list:
            logging.fatal(f"No files found in the directory: {input_file_path}")
            return

        files_list.sort()

        for file in files_list:
            try:
                df = pd.read_csv(input_file_path + file,
                                 encoding='ISO-8859-1',
                                 low_memory=False)

                # Filter by AGEGRP = 0 (sum of all age groups added)
                # Filter years 1 - 5 (exclude years 1 as it is base estimates)
                df = df.query("AGEGRP == 0 & YEAR not in [1]").copy()

                # Convert year code to actual year
                # Year code starting from 1 for Year 2020
                df['YEAR'] = df['YEAR'] + 2020 - 2

                # Add fips code for location
                df.insert(6, 'LOCATION', 'geoId/', True)
                df['LOCATION'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(
                    2) + (df['COUNTY'].map(str)).str.zfill(3)

                # Dynamically select columns to retain
                columns_to_keep = ['YEAR', 'LOCATION'
                                  ]  # Retain YEAR and LOCATION columns

                # Include population columns (male and female)
                population_columns = [
                    'TOT_POP', 'TOT_MALE', 'TOT_FEMALE', 'WA_MALE', 'WA_FEMALE',
                    'BA_MALE', 'BA_FEMALE', 'IA_MALE', 'IA_FEMALE', 'AA_MALE',
                    'AA_FEMALE', 'NA_MALE', 'NA_FEMALE', 'TOM_MALE',
                    'TOM_FEMALE', 'WAC_MALE', 'WAC_FEMALE', 'BAC_MALE',
                    'BAC_FEMALE', 'IAC_MALE', 'IAC_FEMALE', 'AAC_MALE',
                    'AAC_FEMALE', 'NAC_MALE', 'NAC_FEMALE', 'NH_MALE',
                    'NH_FEMALE', 'NHWA_MALE', 'NHWA_FEMALE', 'NHBA_MALE',
                    'NHBA_FEMALE', 'NHIA_MALE', 'NHIA_FEMALE', 'NHAA_MALE',
                    'NHAA_FEMALE', 'NHNA_MALE', 'NHNA_FEMALE', 'NHTOM_MALE',
                    'NHTOM_FEMALE', 'NHWAC_MALE', 'NHWAC_FEMALE', 'NHBAC_MALE',
                    'NHBAC_FEMALE', 'NHIAC_MALE', 'NHIAC_FEMALE', 'NHAAC_MALE',
                    'NHAAC_FEMALE', 'NHNAC_MALE', 'NHNAC_FEMALE', 'H_MALE',
                    'H_FEMALE', 'HWA_MALE', 'HWA_FEMALE', 'HBA_MALE',
                    'HBA_FEMALE', 'HIA_MALE', 'HIA_FEMALE', 'HAA_MALE',
                    'HAA_FEMALE', 'HNA_MALE', 'HNA_FEMALE', 'HTOM_MALE',
                    'HTOM_FEMALE', 'HWAC_MALE', 'HWAC_FEMALE', 'HBAC_MALE',
                    'HBAC_FEMALE', 'HIAC_MALE', 'HIAC_FEMALE', 'HAAC_MALE',
                    'HAAC_FEMALE', 'HNAC_MALE', 'HNAC_FEMALE'
                ]

                # Add population columns to columns_to_keep
                columns_to_keep.extend(population_columns)

                # Retain only the necessary columns
                df = df[columns_to_keep]

                # Write processed data to the output file
                if file == files_list[0]:
                    df.to_csv(output_file_path + output_file_name, index=False)
                else:
                    df.to_csv(output_file_path + output_file_name,
                              index=False,
                              mode='a',
                              header=False)

                logging.info(f"Processed and saved file: {file}")

            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")
                continue  # Continue with the next file if this one fails

        # Section 2 - Writing Aggregated Data
        df = pd.read_csv(output_file_path + output_file_name)
        output_file_path = _CODEDIR + PROCESS_AGG_DIR + '2020_2029/county/'

        df1 = pd.DataFrame()
        df1['YEAR'] = df['YEAR'].copy()
        df1['LOCATION'] = df['LOCATION'].copy()

        _NOT_HISPANIC_RACES = [
            'NH', 'NHWA', 'NHBA', 'NHIA', 'NHAA', 'NHNA', 'NHTOM', 'NHWAC',
            'NHBAC', 'NHIAC', 'NHAAC', 'NHNAC'
        ]
        _HISPANIC_RACES = [
            'H', 'HWA', 'HBA', 'HIA', 'HAA', 'HNA', 'HTOM', 'HWAC', 'HBAC',
            'HIAC', 'HAAC', 'HNAC'
        ]

        # Dynamically aggregate male and female data for races
        for p in _NOT_HISPANIC_RACES:
            df1[p] = (df[p + '_MALE'] + df[p + '_FEMALE']).copy()

        for p in _HISPANIC_RACES:
            df1[p] = (df[p + '_MALE'] + df[p + '_FEMALE']).copy()

        df1.to_csv(output_file_path + output_file_name,
                   header=True,
                   index=False)
        logging.info(
            f"Aggregated data saved successfully to: {output_file_path + output_file_name}"
        )

    except Exception as e:
        logging.fatal(
            f"Fatal error during the processing of county files 2020-2029: {e}")
        return


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
    _process_county_files_2020_2029(download_dir)


def _consolidate_national_files():
    """
    Consolidate all national level files into single national level file.
    Only SV relevant for SRH processing are retained and all other stats are 
    dropped.

    This function consolidates both as-is and agg data into two separate files.
    """
    try:
        national_as_is_files = [
            _CODEDIR + PROCESS_AS_IS_DIR + yr + '/national/national_' + yr +
            '.csv' for yr in
            ['1980_1990', '1990_2000', '2000_2010', '2010_2020', '2020_2029']
        ]

        for file in national_as_is_files:
            try:
                df = pd.read_csv(file)

                # Drop S, SR columns 2000 - 2010 file
                if file == national_as_is_files[2]:
                    df = df[_SR_COLUMNS_DROPPED]

                # Drop S, SR, Race Combination columns 2010 - 2020 file
                if file == national_as_is_files[3]:
                    df = df[_SR_CMBN_COLUMNS_DROPPED]

                # Drop S, SR, Race Combination columns 2020 - 2029 file
                if file == national_as_is_files[4]:
                    df = df[_SR_CMBN_COLUMNS_DROPPED]

                df = df.melt(id_vars=['YEAR', 'LOCATION'],
                             var_name='SV',
                             value_name='OBSERVATION')
                df.replace({"SV": STAT_VAR_COL_MAPPING}, inplace=True)
                df["SV"] = 'dcid:' + df["SV"]
                df.insert(3, 'MEASUREMENT_METHOD',
                          'dcs:dcAggregate/CensusPEPSurvey', True)
                df["MEASUREMENT_METHOD"] = df.apply(
                    lambda r: _calculate_agg_measure_method(r.YEAR, r.SV),
                    axis=1)

                # Write to temp file (append)
                if file == national_as_is_files[0]:
                    df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR +
                              'national_consolidated_temp.csv',
                              header=True,
                              index=False)
                else:
                    df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR +
                              'national_consolidated_temp.csv',
                              header=False,
                              index=False,
                              mode='a')

            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")

        # Finalizing As-Is Data
        try:
            df = pd.read_csv(_CODEDIR + PROCESS_AS_IS_DIR +
                             'national_consolidated_temp.csv')
            df.sort_values(by=['LOCATION', 'SV', 'YEAR'], inplace=True)
            df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR +
                      'national_consolidated_as_is_final.csv',
                      header=True,
                      index=False)

            if os.path.exists(_CODEDIR + PROCESS_AS_IS_DIR +
                              'national_consolidated_temp.csv'):
                os.remove(_CODEDIR + PROCESS_AS_IS_DIR +
                          'national_consolidated_temp.csv')

            logging.info("Successfully consolidated as-is national data.")

        except Exception as e:
            logging.error(f"Error during finalizing As-Is national data: {e}")

        # Aggregate file processing
        national_agg_files = [
            _CODEDIR + PROCESS_AGG_DIR + yr + '/national/national_' + yr +
            '.csv' for yr in
            ['1980_1990', '1990_2000', '2000_2010', '2010_2020', '2020_2029']
        ]

        for file in national_agg_files:
            try:
                df = pd.read_csv(file)
                df = df.melt(id_vars=['YEAR', 'LOCATION'],
                             var_name='SV',
                             value_name='OBSERVATION')
                df.replace({"SV": STAT_VAR_COL_MAPPING}, inplace=True)
                df["SV"] = 'dcid:' + df["SV"]

                # Write to temp file (append)
                if file == national_agg_files[0]:
                    df.to_csv(_CODEDIR + PROCESS_AGG_DIR +
                              'national_consolidated_temp.csv',
                              header=True,
                              index=False)
                else:
                    df.to_csv(_CODEDIR + PROCESS_AGG_DIR +
                              'national_consolidated_temp.csv',
                              header=False,
                              index=False,
                              mode='a')

            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")

        # Finalizing Agg Data
        try:
            df = pd.read_csv(_CODEDIR + PROCESS_AGG_DIR +
                             'national_consolidated_temp.csv')
            df.sort_values(by=['LOCATION', 'SV', 'YEAR'], inplace=True)
            df.insert(3, 'MEASUREMENT_METHOD',
                      'dcs:dcAggregate/CensusPEPSurvey', True)
            df["MEASUREMENT_METHOD"] = df.apply(
                lambda r: _calculate_agg_measure_method(r.YEAR, r.SV), axis=1)
            df.to_csv(_CODEDIR + PROCESS_AGG_DIR +
                      'national_consolidated_agg_final.csv',
                      header=True,
                      index=False)

            if os.path.exists(_CODEDIR + PROCESS_AGG_DIR +
                              'national_consolidated_temp.csv'):
                os.remove(_CODEDIR + PROCESS_AGG_DIR +
                          'national_consolidated_temp.csv')

            logging.info("Successfully consolidated agg national data.")

        except Exception as e:
            logging.error(f"Error during finalizing Agg national data: {e}")

    except Exception as e:
        logging.fatal(
            f"Fatal error during the consolidation of national files: {e}")
        return


def _consolidate_state_files():
    """
    Consolidate all (4) state level files into single state level file.
    Only SV relevant for SRH processing are retained and all other stats are 
    dropped.

    This function consolidates both as-is and agg data into two separate files.
    """
    try:
        # List of state level files for as-is data
        state_as_is_files = [
            _CODEDIR + PROCESS_AS_IS_DIR + yr + '/state/state_' + yr + '.csv'
            for yr in
            ['1980_1990', '1990_2000', '2000_2010', '2010_2020', '2020_2029']
        ]

        # Processing As-Is Files
        for file in state_as_is_files:
            try:
                df = pd.read_csv(file)

                # Drop S, SR columns 2000 - 2010 file
                if file == state_as_is_files[2]:
                    df = df[_SR_COLUMNS_DROPPED]

                # Drop S, SR, Race Combination columns 2010 - 2020 file
                if file == state_as_is_files[3]:
                    df = df[_SR_CMBN_COLUMNS_DROPPED]

                # Drop S, SR, Race Combination columns 2020 - 2029 file
                if file == state_as_is_files[4]:
                    df = df[_SR_CMBN_COLUMNS_DROPPED]

                df = df.melt(id_vars=['YEAR', 'LOCATION'],
                             var_name='SV',
                             value_name='OBSERVATION')
                df.replace({"SV": STAT_VAR_COL_MAPPING}, inplace=True)
                df["SV"] = 'dcid:' + df["SV"]
                df.insert(3, 'MEASUREMENT_METHOD', 'dcs:CensusPEPSurvey', True)
                df["MEASUREMENT_METHOD"] = df.apply(
                    lambda r: _calculate_asis_measure_method(r.YEAR, r.SV),
                    axis=1)

                # Writing to temp file (appending)
                if file == state_as_is_files[0]:
                    df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR +
                              'state_consolidated_temp.csv',
                              header=True,
                              index=False)
                else:
                    df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR +
                              'state_consolidated_temp.csv',
                              header=False,
                              index=False,
                              mode='a')

            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")

        # Finalizing As-Is Data
        try:
            df = pd.read_csv(_CODEDIR + PROCESS_AS_IS_DIR +
                             'state_consolidated_temp.csv')
            df.sort_values(by=['LOCATION', 'SV', 'YEAR'], inplace=True)
            df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR +
                      'state_consolidated_as_is_final.csv',
                      header=True,
                      index=False)

            if os.path.exists(_CODEDIR + PROCESS_AS_IS_DIR +
                              'state_consolidated_temp.csv'):
                os.remove(_CODEDIR + PROCESS_AS_IS_DIR +
                          'state_consolidated_temp.csv')

            logging.info("Successfully consolidated as-is state data.")

        except Exception as e:
            logging.error(f"Error during finalizing As-Is state data: {e}")

        # Processing Agg Files
        state_agg_files = [
            _CODEDIR + PROCESS_AGG_DIR + yr + '/state/state_' + yr + '.csv'
            for yr in
            ['1980_1990', '1990_2000', '2000_2010', '2010_2020', '2020_2029']
        ]

        # Processing Agg Data Files
        for file in state_agg_files:
            try:
                df = pd.read_csv(file)
                df = df.melt(id_vars=['YEAR', 'LOCATION'],
                             var_name='SV',
                             value_name='OBSERVATION')
                df.replace({"SV": STAT_VAR_COL_MAPPING}, inplace=True)
                df["SV"] = 'dcid:' + df["SV"]

                # Writing to temp file (appending)
                if file == state_agg_files[0]:
                    df.to_csv(_CODEDIR + PROCESS_AGG_DIR +
                              'state_consolidated_temp.csv',
                              header=True,
                              index=False)
                else:
                    df.to_csv(_CODEDIR + PROCESS_AGG_DIR +
                              'state_consolidated_temp.csv',
                              header=False,
                              index=False,
                              mode='a')

            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")

        # Finalizing Agg Data
        try:
            df = pd.read_csv(_CODEDIR + PROCESS_AGG_DIR +
                             'state_consolidated_temp.csv')
            df.sort_values(by=['LOCATION', 'SV', 'YEAR'], inplace=True)
            df.insert(3, 'MEASUREMENT_METHOD',
                      'dcs:dcAggregate/CensusPEPSurvey', True)
            df["MEASUREMENT_METHOD"] = df.apply(
                lambda r: _calculate_agg_measure_method(r.YEAR, r.SV), axis=1)
            df.to_csv(_CODEDIR + PROCESS_AGG_DIR +
                      'state_consolidated_agg_final.csv',
                      header=True,
                      index=False)

            if os.path.exists(_CODEDIR + PROCESS_AGG_DIR +
                              'state_consolidated_temp.csv'):
                os.remove(_CODEDIR + PROCESS_AGG_DIR +
                          'state_consolidated_temp.csv')

            logging.info("Successfully consolidated agg state data.")

        except Exception as e:
            logging.error(f"Error during finalizing Agg state data: {e}")

    except Exception as e:
        logging.fatal(
            f"Fatal error during the consolidation of state files: {e}")
        return


def _consolidate_county_files():
    """
    Consolidate all (4) county-level files into a single county-level file.
    Only SV relevant for SRH processing are retained and all other stats are 
    dropped.

    This function consolidates both as-is and agg data into two separate files.
    """

    try:
        # List of county-level files for as-is data
        county_as_is_files = [
            _CODEDIR + PROCESS_AS_IS_DIR + yr + '/county/county_' + yr + '.csv'
            for yr in ['1990_2000', '2000_2010', '2010_2020', '2020_2029']
        ]

        # Processing As-Is Files
        for file in county_as_is_files:
            try:
                df = pd.read_csv(file)

                # Drop S, SR columns 2000 - 2010 file
                if file == county_as_is_files[1]:
                    df = df[_SR_COLUMNS_DROPPED]

                # Drop S, SR, Race Combination columns 2010 - 2020 file
                if file == county_as_is_files[2]:
                    df = df[_SR_CMBN_COLUMNS_DROPPED]

                # Drop S, SR, Race Combination columns 2020 - 2029 file
                if file == county_as_is_files[3]:
                    df = df[_SR_CMBN_COLUMNS_DROPPED]

                df = df.melt(id_vars=['YEAR', 'LOCATION'],
                             var_name='SV',
                             value_name='OBSERVATION')
                df.replace({"SV": STAT_VAR_COL_MAPPING}, inplace=True)
                df["SV"] = 'dcid:' + df["SV"]
                df.insert(3, 'MEASUREMENT_METHOD', 'dcs:CensusPEPSurvey', True)
                df["MEASUREMENT_METHOD"] = df.apply(
                    lambda r: _calculate_asis_measure_method(r.YEAR, r.SV),
                    axis=1)

                # Writing to temp file (appending)
                if file == county_as_is_files[0]:
                    df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR +
                              'county_consolidated_temp.csv',
                              header=True,
                              index=False)
                else:
                    df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR +
                              'county_consolidated_temp.csv',
                              header=False,
                              index=False,
                              mode='a')

            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")

        # Finalizing As-Is Data
        try:
            df = pd.read_csv(_CODEDIR + PROCESS_AS_IS_DIR +
                             'county_consolidated_temp.csv')
            df.sort_values(by=['LOCATION', 'SV', 'YEAR'], inplace=True)
            df.to_csv(_CODEDIR + PROCESS_AS_IS_DIR +
                      'county_consolidated_as_is_final.csv',
                      header=True,
                      index=False)

            if os.path.exists(_CODEDIR + PROCESS_AS_IS_DIR +
                              'county_consolidated_temp.csv'):
                os.remove(_CODEDIR + PROCESS_AS_IS_DIR +
                          'county_consolidated_temp.csv')

            logging.info("Successfully consolidated as-is county data.")

        except Exception as e:
            logging.error(f"Error during finalizing As-Is county data: {e}")

        # Processing Agg Files
        county_as_is_files = [
            _CODEDIR + PROCESS_AS_IS_DIR +
            '1990_2000/county/county_1990_2000.csv', _CODEDIR +
            PROCESS_AGG_DIR + '1990_2000/county/county_1990_2000.csv',
            _CODEDIR + PROCESS_AGG_DIR +
            '2000_2010/county/county_2000_2010.csv', _CODEDIR +
            PROCESS_AGG_DIR + '2010_2020/county/county_2010_2020.csv',
            _CODEDIR + PROCESS_AGG_DIR + '2020_2029/county/county_2020_2029.csv'
        ]

        for file in county_as_is_files:
            try:
                df = pd.read_csv(file)
                df = df.melt(id_vars=['YEAR', 'LOCATION'],
                             var_name='SV',
                             value_name='OBSERVATION')
                df.replace({"SV": STAT_VAR_COL_MAPPING}, inplace=True)
                df["SV"] = 'dcid:' + df["SV"]

                # Writing to temp file (appending)
                if file == county_as_is_files[0]:
                    df.to_csv(_CODEDIR + PROCESS_AGG_DIR +
                              'county_consolidated_temp.csv',
                              header=True,
                              index=False)
                else:
                    df.to_csv(_CODEDIR + PROCESS_AGG_DIR +
                              'county_consolidated_temp.csv',
                              header=False,
                              index=False,
                              mode='a')

            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")

        # Finalizing Agg Data
        try:
            df = pd.read_csv(_CODEDIR + PROCESS_AGG_DIR +
                             'county_consolidated_temp.csv')
            df.sort_values(by=['LOCATION', 'SV', 'YEAR'], inplace=True)
            df.insert(3, 'MEASUREMENT_METHOD',
                      'dcs:dcAggregate/CensusPEPSurvey', True)
            df["MEASUREMENT_METHOD"] = df.apply(
                lambda r: _calculate_agg_measure_method(r.YEAR, r.SV), axis=1)
            df.to_csv(_CODEDIR + PROCESS_AGG_DIR +
                      'county_consolidated_agg_final.csv',
                      header=True,
                      index=False)

            if os.path.exists(_CODEDIR + PROCESS_AGG_DIR +
                              'county_consolidated_temp.csv'):
                os.remove(_CODEDIR + PROCESS_AGG_DIR +
                          'county_consolidated_temp.csv')

            logging.info("Successfully consolidated agg county data.")

        except Exception as e:
            logging.error(f"Error during finalizing Agg county data: {e}")

    except Exception as e:
        logging.fatal(
            f"Fatal error during the consolidation of county files: {e}")
        return


def _consolidate_all_geo_files(output_path):
    """
    Consolidate National, State and County files into a single file.
    This function generates final csv files for both as-is and agg
    data processing which will be used for importing into DC.

    Output files are written to /output_files/ folder.
    """

    try:
        # Initialize empty DataFrames
        as_is_df = pd.DataFrame()
        agg_df = pd.DataFrame()

        # Process as-is files
        for file in [
                _CODEDIR + PROCESS_AS_IS_DIR + geo +
                '_consolidated_as_is_final.csv'
                for geo in ['national', 'state', 'county']
        ]:
            try:
                # Read the file and concatenate
                df = pd.read_csv(file)
                as_is_df = pd.concat([as_is_df, df])
            except Exception as e:
                logging.error(f"Error processing 'as-is' file {file}: {e}")

        # Save the consolidated as-is DataFrame
        try:
            as_is_df.to_csv(_CODEDIR + output_path +
                            'population_estimate_by_srh.csv',
                            header=True,
                            index=False)
            logging.info(
                "Successfully saved 'as-is' consolidated file to population_estimate_by_srh.csv"
            )
        except Exception as e:
            logging.error(f"Error saving 'as-is' consolidated file: {e}")

        # Process agg files
        for file in [
                _CODEDIR + PROCESS_AGG_DIR + geo + '_consolidated_agg_final.csv'
                for geo in ['national', 'state', 'county']
        ]:
            try:
                # Read the file and concatenate
                df = pd.read_csv(file)
                agg_df = pd.concat([agg_df, df])
            except Exception as e:
                logging.error(f"Error processing 'agg' file {file}: {e}")

        # Save the consolidated agg DataFrame
        try:
            agg_df.to_csv(_CODEDIR + output_path +
                          'population_estimate_by_srh_agg.csv',
                          header=True,
                          index=False)
            logging.info(
                "Successfully saved 'agg' consolidated file to population_estimate_by_srh_agg.csv"
            )
        except Exception as e:
            logging.error(f"Error saving 'agg' consolidated file: {e}")

    except Exception as e:
        logging.fatal(
            f"Fatal error during the consolidation of all geo files: {e}")
        return


def _consolidate_files(output_path):
    """
    Consolidate National, State and County files into single file.
    Two seperate files - consolidates-as-is and consolidated-agg files are 
    created
    """
    _consolidate_county_files()
    _consolidate_state_files()
    _consolidate_national_files()
    _consolidate_all_geo_files(output_path)


def add_future_year_urls():
    global _FILES_TO_DOWNLOAD
    with open(os.path.join(_MODULE_DIR, 'input_url.json'), 'r') as input_file:
        _FILES_TO_DOWNLOAD = json.load(input_file)

    urls_to_scan = [
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/counties/asrh/cc-est{YEAR}-alldata.csv"
    ]

    # This method will generate URLs for the years 2023 to 2029
    for url in urls_to_scan:
        for future_year in range(2030, 2022, -1):
            YEAR = future_year
            file_path = os.path.join(_MODULE_DIR,
                                     "input_files/2020_2029/county/"
                                    )  # Dynamic folder structure and file name
            url_to_check = url.format(YEAR=YEAR)
            logging.info(f"checking url: {url_to_check}")
            try:
                check_url = requests.head(url_to_check)
                if check_url.status_code == 200:
                    _FILES_TO_DOWNLOAD.append({
                        "download_path": url_to_check,
                        "file_path": file_path
                    })
                    logging.info(f"url added to download: {url_to_check}")
                    break
            except:
                logging.error(f"URL is not accessible: {url_to_check}")


def download_files():
    """Downloads files from the provided URLs.

  This function iterates through a list of files to download (`_FILES_TO_DOWNLOAD`)
  and attempts to download each file with retries in case of errors.

  Returns:
      bool: True if all files were downloaded successfully, False otherwise.
  """

    global _FILES_TO_DOWNLOAD
    session = requests.session()
    max_retry = 5

    for file_to_download in _FILES_TO_DOWNLOAD:
        file_name_to_save = None
        url = file_to_download['download_path']

        # Determine the filename to save the downloaded file
        if 'file_name' in file_to_download:
            file_name_to_save = file_to_download['file_name']
        else:
            file_name_to_save = url.split('/')[-1]

        # Include file path if specified
        if 'file_path' in file_to_download:
            file_name_to_save = os.path.join(file_to_download['file_path'],
                                             file_name_to_save)

        retry_number = 0
        is_file_downloaded = False

        while not is_file_downloaded:
            try:
                # Download the file with retries
                with session.get(url, stream=True) as response:
                    response.raise_for_status()

                    if response.status_code == 200:
                        # Create the download directory if it doesn't exist
                        os.makedirs(os.path.dirname(
                            os.path.join(_INPUT_FILE_PATH, file_name_to_save)),
                                    exist_ok=True)
                        with open(
                                os.path.join(_INPUT_FILE_PATH,
                                             file_name_to_save), 'wb') as f:
                            f.write(response.content)
                        file_to_download['is_downloaded'] = True
                        logging.info(f"Downloaded file: {url}")
                        is_file_downloaded = True
                    else:
                        logging.info(f"Retry file download: {url}")
                        time.sleep(5)
                        retry_number += 1

            except Exception as e:
                logging.fatal(f"Error downloading {url}: {e}")
                time.sleep(5)
                retry_number += 1

            if retry_number > max_retry:
                logging.fatal(
                    f"Error downloading {url} after {max_retry} retries")
                # Exit the function if download fails after retries
                return False

    return True  # All files downloaded successfully (or at least attempted)


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
    # _process_geo_level_aggregations will process state 2000 - 2020, 2020 - 2029 data
    # and national 1980 - 2020, 2020 - 2029 data
    # The national-level data is generated through aggregation because the aggregated data and the national files are similar in content
    # It simplifies the dataset for broader use, while maintaining consistency across national, state, and county levels.
    # Although the source has national files, they may be in a different format or require additional processing compared to the state and county data.
    _process_geo_level_aggregation()


def _create_output_n_process_folders():
    """
    Create directories for processing data and saving final output
    """
    for d in WORKING_DIRECTORIES:
        os.system("mkdir -p " + _CODEDIR + d)


def process(data_directory, output_path):
    """
    Produce As Is and Agg output files for National, State and County
    Produce MCF and tMCF files for both As-Is and Agg output files

    Args:
      download_dir: download directory - input files are saved here.
      output_path: output directory - output files from test data input are saved here.
    """
    input_files = []
    # Walk through the directory and its subdirectories
    for root, dirs, files in os.walk(_INPUT_FILE_PATH):
        for file in sorted(files):  # Sort the files alphabetically
            file_path = os.path.join(root, file)
            input_files.append(file_path)
    # Now `input_files` contains paths to all the files in `_INPUT_FILE_PATH` and its subdirectories

    total_files_to_process = len(input_files)
    logging.info(f"No of files to be processed {total_files_to_process}")

    _create_output_n_process_folders()
    _process_files(data_directory)
    _consolidate_files(output_path)
    generate_mcf(output_path)
    generate_tmcf(output_path)


def main(_):
    """
    Produce As Is and Agg output files for National, State and County
    Produce MCF and tMCF files for both As-Is and Agg output files
    """
    mode = _FLAGS.mode
    download_status = True
    if mode == "" or mode == "download":
        _create_output_n_process_folders()
        add_future_year_urls()
        download_status = download_files()
    if download_status and (mode == "" or mode == "process"):
        process(_FLAGS.data_directory, output_path)


if __name__ == '__main__':
    app.run(main)
