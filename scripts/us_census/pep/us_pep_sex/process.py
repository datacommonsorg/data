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
This Python Script Load the datasets, cleans it
and generates cleaned CSV, MCF, TMCF file.
"""

import os
import sys
import pandas as pd
import numpy as np
from absl import app, flags
import requests
import shutil
import time
import json
from datetime import datetime as dt
from absl import logging
from absl import flags

_FLAGS = flags.FLAGS

flags.DEFINE_string('mode', '', 'Options: download or process')

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = os.path.join(_MODULE_DIR, 'input_files')
_FILES_TO_DOWNLOAD = None

sys.path.insert(1, os.path.join(_MODULE_DIR, '../../../../'))
# pylint: disable=wrong-import-position
import util.alpha2_to_dcid as alpha2todcid
import util.name_to_alpha2 as statetoshortform

USSTATE_MAP = alpha2todcid.USSTATE_MAP
_USSTATE_SHORT_FORM = statetoshortform.USSTATE_MAP
# pylint: enable=wrong-import-position

_FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

_MCF_TEMPLATE = ("Node: dcid:{pv1}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Person{pv2}\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:count\n")

_TMCF_TEMPLATE = (
    "Node: E:population_estimate_sex->E0\n"
    "typeOf: dcs:StatVarObservation\n"
    "variableMeasured: C:population_estimate_sex->SV\n"
    "measurementMethod: C:population_estimate_sex->Measurement_Method\n"
    "observationAbout: C:population_estimate_sex->geo_ID\n"
    "observationDate: C:population_estimate_sex->Year\n"
    "observationPeriod: \"P1Y\"\n"
    "value: C:population_estimate_sex->Observation\n")

_COLUMNS_TO_SUM = [
    'Under 5 years', '5 to 9 years', '10 to 14 years', '15 to 19 years',
    '20 to 24 years', '25 to 29 years', '30 to 34 years', '35 to 39 years',
    '40 to 44 years', '45 to 49 years', '50 to 54 years', '55 to 59 years',
    '60 to 64 years', '65 to 69 years', '70 to 74 years', '75 to 79 years',
    '80 to 84 years', '85 years and over'
]


def _states_full_to_short_form(data_df: pd.DataFrame,
                               data_col: str,
                               new_col: str,
                               replace_key: str = " ") -> pd.DataFrame:
    short_forms = _USSTATE_SHORT_FORM
    data_df[new_col] = data_df[data_col].str.replace(
        replace_key, "",
        regex=False).apply(lambda row: short_forms.get(row, row))
    return data_df


def _add_geo_id(data_df: pd.DataFrame, data_col: str,
                new_col: str) -> pd.DataFrame:
    data_df[new_col] = data_df[data_col].apply(
        lambda rec: USSTATE_MAP.get(rec, rec))
    return data_df


def _national_1900_1979(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for national 1900 to 1979.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        # extracting year from file path.
        year = file_path[-8:-4]
        # schema is changing after 1960
        if int(year) < 1960:
            # schema is changing after 1940
            if int(year) < 1940:
                df = pd.read_csv(file_path,
                                 thousands=',',
                                 engine='python',
                                 skiprows=7,
                                 skipfooter=92,
                                 header=None)
            else:
                df = pd.read_csv(file_path,
                                 thousands=',',
                                 engine='python',
                                 skiprows=7,
                                 skipfooter=102,
                                 header=None)
            """
            The columns order has been fixed. Two headers combines to form the column name.
            Even if we want to use rename method we still have to assume rolws and col position
            Incase of change in order of the columns in the future has been handled by try catch block.
            The logic applies to the other methods below
            """

            df.columns = [
                'Age', 'Total', 'Count_Person_Male', 'Count_Person_Female',
                'White Total', 'White Male', 'White Female', 'NonWhite Total',
                'NonWhite Male', 'NonWhite Female'
            ]
            df = df.drop(columns=df.columns.difference(
                ['Count_Person_Male', 'Count_Person_Female']))

        else:
            df = pd.read_csv(file_path,
                             thousands=',',
                             engine='python',
                             skiprows=6,
                             skipfooter=102,
                             header=None)
            df.columns = [
                'Age', 'Total', 'Count_Person_Male', 'Count_Person_Female',
                'White Total', 'White Male', 'White Female', 'Black Total',
                'Black Male', 'Black Female', 'OtherRace Total',
                'OtherRace Male', 'OtherRace Female'
            ]

            # dropping unwanted columns
            df = df.drop(columns=df.columns.difference(
                ['Count_Person_Male', 'Count_Person_Female']))

        # adding geoid, year and measurement method
        df['Year'] = year
        df.insert(0, 'geo_ID', 'country/USA', True)
        df['Measurement_Method'] = 'dcAggregate/CensusPEPSurvey_PartialAggregate'
        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


def _national_1990_2000(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for national 1990 to 2000.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        df = pd.read_csv(file_path, thousands=',', skiprows=1, header=None)
        df.columns = [
            'Year', 'Age', 'Total', 'Count_Person_Male', 'Count_Person_Female'
        ]
        # total age is required as we are bring age in a seperate import
        df = df[(df["Age"] == "All Age") &
                (df["Year"].str.startswith("July"))].reset_index(drop=True)
        df["Year"] = df["Year"].str.replace("July 1, ", "")
        # dropping unwanted columns
        df = df.drop(columns=df.columns.difference(
            ['Year', 'Total', 'Count_Person_Male', 'Count_Person_Female']))

        df.insert(0, 'geo_ID', 'country/USA', True)
        float_col = df.select_dtypes(include=['float64'])
        for col in float_col.columns.values:
            df[col] = df[col].astype('int64')
        df['Measurement_Method'] = 'dcAggregate/CensusPEPSurvey_PartialAggregate'
        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


def _national_2000_2010(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for national 2000 to 2010.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        df = pd.read_csv(file_path, thousands=',', skiprows=4, header=None)
        df.columns = [
            'SEX', 'April2000', '2000', '2001', '2002', '2003', '2004', '2005',
            '2006', '2007', '2008', '2009', 'April2010', '2010'
        ]
        df = df.query('SEX=="MALE" or SEX=="FEMALE"')
        # dropping unwanted columns
        df = df.drop(columns=df.columns.difference([
            'SEX', '2000', '2001', '2002', '2003', '2004', '2005', '2006',
            '2007', '2008', '2009'
        ]))

        df = df.replace({
            'SEX': {
                'MALE': 'Count_Person_Male',
                'FEMALE': 'Count_Person_Female'
            }
        })
        # replacing rows with columns
        # making the first row as column name
        # to get all dataframe in one formate
        df = df.transpose().reset_index()
        df.columns = df.iloc[0]
        df = df[1:]
        df.insert(0, 'geo_ID', 'country/USA', True)
        df = df.fillna(-1)
        float_col = df.select_dtypes(include=['float64'])
        for col in float_col.columns.values:
            df[col] = df[col].astype('int64')
            df[col] = df[col].astype("str").str.replace("-1", "")
        df.rename(columns={'SEX': 'Year'}, inplace=True)
        df['Measurement_Method'] = 'dcAggregate/CensusPEPSurvey_PartialAggregate'
        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


def _national_2010_2020(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for national 2010 to 2020.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        df = pd.read_csv(file_path)
        # to get total age present at age = 999
        df = df.query("AGE == 999")
        # total is not required in gender
        df = df.query("SEX != 0")
        # dropping unwanted column
        df = df.drop(columns=df.columns.difference([
            'SEX', 'POPESTIMATE2010', 'POPESTIMATE2011', 'POPESTIMATE2012',
            'POPESTIMATE2013', 'POPESTIMATE2014', 'POPESTIMATE2015',
            'POPESTIMATE2016', 'POPESTIMATE2017', 'POPESTIMATE2018',
            'POPESTIMATE2019', 'POPESTIMATE2020'
        ]))

        df = df.replace(
            {'SEX': {
                1: 'Count_Person_Male',
                2: 'Count_Person_Female'
            }})
        df.rename(columns={
            'POPESTIMATE2010': '2010',
            'POPESTIMATE2011': '2011',
            'POPESTIMATE2012': '2012',
            'POPESTIMATE2013': '2013',
            'POPESTIMATE2014': '2014',
            'POPESTIMATE2015': '2015',
            'POPESTIMATE2016': '2016',
            'POPESTIMATE2017': '2017',
            'POPESTIMATE2018': '2018',
            'POPESTIMATE2019': '2019',
            'POPESTIMATE2020': '2020',
            'SEX': 'Year'
        },
                  inplace=True)
        # replacing rows with columns
        # making the first row as column name
        # to get all dataframe in one formate
        df = df.transpose().reset_index()
        df.columns = df.iloc[0]
        df = df[1:]
        df.insert(0, 'geo_ID', 'country/USA', True)
        df['Measurement_Method'] = 'dcAggregate/CensusPEPSurvey_PartialAggregate'
        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


def _national_latest(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for national 2023.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        df = pd.read_csv(file_path)
        # total is not required in gender
        df = df.query("SEX !=0")
        # to get total age present at age = 999
        df = df.query("AGE == 999")
        df = df.replace(
            {'SEX': {
                1: 'Count_Person_Male',
                2: 'Count_Person_Female'
            }})
        column_list = []
        for year in range(2021, 2030):
            column_name = f'POPESTIMATE{year}'
            if column_name in df.columns:
                df.rename(columns={column_name: str(year)}, inplace=True)
                column_list.append(str(year))

        # Ensure columns are renamed correctly before dropping unnecessary ones
        if 'SEX' in df.columns:
            df.rename(columns={'SEX': 'Year'}, inplace=True)

        column_list.insert(0, "Year")
        df = df.drop(columns=df.columns.difference(column_list))
        # replacing rows with columns
        # making the first row as column name
        # to get all dataframe in one formate
        df = df.transpose().reset_index()
        df.columns = df.iloc[0]
        df = df[1:]
        df.insert(0, 'geo_ID', 'country/USA', True)
        df['Measurement_Method'] = 'dcAggregate/CensusPEPSurvey_PartialAggregate'
        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


def _state_1970_1980(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for state 1970 to 1980.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        df = pd.read_csv(file_path, skiprows=5, thousands=',')
        df['Total'] = df[_COLUMNS_TO_SUM].sum(axis=1)
        df = df.drop(columns=_COLUMNS_TO_SUM)
        df = df.replace({
            'Race/Sex Indicator': {
                'White male': 'Count_Person_Male',
                'Black male': 'Count_Person_Male',
                'Other races male': 'Count_Person_Male',
                'White female': 'Count_Person_Female',
                'Black female': 'Count_Person_Female',
                'Other races female': 'Count_Person_Female'
            }
        })
        df = df.rename(columns={
            'Year of Estimate': 'Year',
            'FIPS State Code': 'geo_ID'
        })
        df['geo_ID'] = 'geoId/' + (df['geo_ID'].map(str)).str.zfill(2)
        df['geo_ID'] = df['geo_ID'] + '-' + df['Year'].astype(str)
        df = df.drop(columns=df.columns.difference(
            ['geo_ID', 'Race/Sex Indicator', 'Total']))

        # replacing rows with columns
        # to get all dataframe in one formate
        df = df.groupby(['geo_ID','Race/Sex Indicator']).sum().transpose()\
            .stack(0).reset_index()
        df[['geo_ID', 'Year']] = df['geo_ID'].str.split('-', expand=True)
        df = df.drop(columns=['level_0'])
        df['Measurement_Method'] = 'dcAggregate/CensusPEPSurvey_PartialAggregate'
        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


def _state_1980_1990(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for state 1980 to 1990 and also aggregate
    state values to get national 1980 to 1990.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        # extracting year from file path
        year = file_path[-6:-4]
        year = 1900 + int(year)
        if year == 1983:
            pass
        column_names = [
            'geo_ID', 'CountyCode', 'Age', 'Total', 'Count_Person_Male',
            'Count_Person_Female'
        ]
        if year == 1987:
            df = pd.read_table(file_path,
                               skiprows=29,
                               delim_whitespace=True,
                               names=column_names)
        else:
            df = pd.read_table(file_path,
                               skiprows=28,
                               delim_whitespace=True,
                               names=column_names)
        df['geo_ID'] = 'geoId/' + (df['geo_ID'].map(str)).str.zfill(2)
        df['Year'] = year
        df = df.drop(columns=['CountyCode', 'Age', 'Total'])
        df = df.groupby(['Year', 'geo_ID']).sum().reset_index()
        # aggregating state data to get national data
        df_national = df.copy()
        df_national['geo_ID'] = "country/USA"
        df_national = df_national.groupby(['Year',
                                           'geo_ID']).sum().reset_index()
        df = pd.concat([df_national, df], ignore_index=True)
        df['Measurement_Method'] = 'dcAggregate/CensusPEPSurvey_PartialAggregate'
        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


def _state_2000_2010(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for state 2000 to 2010.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        # extract geoid from the file path
        geoid = file_path[-6:-4]
        column_name = [
            'AgeSex', 'April2000', '2000', '2001', '2002', '2003', '2004',
            '2005', '2006', '2007', '2008', '2009', 'April2010', '2010'
        ]
        df = pd.read_csv(file_path, skiprows=4, thousands=',')
        df.columns = column_name
        df = df.query('AgeSex == "MALE" or AgeSex == "FEMALE"')
        df = df.replace({
            'AgeSex': {
                "MALE": 'Count_Person_Male',
                "FEMALE": 'Count_Person_Female'
            }
        })
        df = df.drop(columns=df.columns.difference([
            'AgeSex', '2000', '2001', '2002', '2003', '2004', '2005', '2006',
            '2007', '2008', '2009'
        ]))

        # replacing rows with columns
        # making the first row as column name
        # to get all dataframe in one formate
        df = df.transpose().reset_index()
        df.columns = df.iloc[0]
        df = df[1:]
        df = df.rename(columns={'AgeSex': 'Year'})
        df.insert(1, 'geo_ID', 'geoId/' + geoid)
        df = df.fillna(-1)
        float_col = df.select_dtypes(include=['float64'])
        for col in float_col.columns.values:
            df[col] = df[col].astype('int64')
            df[col] = df[col].astype("str").str.replace("-1", "")
        df['Measurement_Method'] = 'dcAggregate/CensusPEPSurvey_PartialAggregate'
        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


def _state_2010_2020(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for state 2010 to 2020.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        df = pd.read_csv(file_path, thousands=',')
        df['geo_ID'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(2)
        df = df.replace({
            'YEAR': {
                1: 'April2010Census',
                2: 'April2010Estimate',
                3: '2010',
                4: '2011',
                5: '2012',
                6: '2013',
                7: '2014',
                8: '2015',
                9: '2016',
                10: '2017',
                11: '2018',
                12: '2019',
                13: 'April2020',
                14: '2020'
            }
        })
        df = df.rename(
            columns={
                'POPEST_MALE': 'Count_Person_Male',
                'POPEST_FEM': 'Count_Person_Female',
                'YEAR': 'Year'
            })
        df = df.drop(columns=df.columns.difference(
            ['Year', 'Count_Person_Male', 'Count_Person_Female', 'geo_ID']))

        df = df[(df['Year'] != 'April2010Census') &
                (df['Year'] != 'April2010Estimate') &
                (df['Year'] != 'April2020') & (df['Year'] != '2020')]
        df['Measurement_Method'] = 'dcAggregate/CensusPEPSurvey_PartialAggregate'
        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


def _state_latest(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for state 2023, dynamically supporting years from 2021 to 2029.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """

    # Base column names that are common for all years
    base_columns = [
        'Age',
        'April2020Total',
        'April2020Male',
        'April2020Female',
        'July2020Total',
        'July2020Male',
        'July2020Female',
    ]
    # Adding year-specific columns dynamically till latest year
    df = pd.read_excel(file_path, engine='openpyxl')

    fourth_row_list = df.iloc[2].tolist()
    max_year = np.nanmax(fourth_row_list) if any(
        not pd.isna(i) for i in fourth_row_list) else np.nan

    df = pd.read_excel(file_path, skiprows=5, skipfooter=7, header=None)
    current_year = int(max_year) + 1
    for year in range(2021, current_year):
        if current_year < 2030:
            base_columns.append(f'July{year}Total')
            base_columns.append(f'July{year}Male')
            base_columns.append(f'July{year}Female')

    # Assign dynamic column names
    df.columns = base_columns

    # extract geoid from file path
    geoid = file_path[-7:-5]
    if geoid == "0.":
        geoid = "01"
    df = df.query('Age == "Total"')
    df.insert(1, 'geo_ID', 'geoId/' + geoid)
    processed_dfs = []  # List to hold yearly DataFrames

    for year in range(2020, 2030):
        # Generate column names dynamically
        male_col = f'July{year}Male'
        female_col = f'July{year}Female'

        if male_col in df.columns and female_col in df.columns:  # Ensure columns exist
            yearly_df = df[['Age', 'geo_ID', male_col, female_col]].copy()
            yearly_df = yearly_df.rename(columns={
                male_col: 'Count_Person_Male',
                female_col: 'Count_Person_Female'
            })
            yearly_df['Year'] = str(year)
            yearly_df[
                'Measurement_Method'] = 'dcAggregate/CensusPEPSurvey_PartialAggregate'
            processed_dfs.append(yearly_df)

    # Concatenate all the processed DataFrames
    final_df = pd.concat(processed_dfs, ignore_index=True)
    return final_df


def _county_1970_1980(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for county 1970 to 1980.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        df = pd.read_excel(file_path, skiprows=5)
        df = df.dropna()
        float_col = df.select_dtypes(include=['float64'])
        for col in float_col.columns.values:
            df[col] = df[col].astype('int64')
        # adding age groups to get total value
        df['Total'] = df[_COLUMNS_TO_SUM].sum(axis=1)
        df = df.drop(columns=_COLUMNS_TO_SUM)
        df = df.replace({
            'Race/Sex Indicator': {
                'White male': 'Count_Person_Male',
                'Black male': 'Count_Person_Male',
                'Other races male': 'Count_Person_Male',
                'White female': 'Count_Person_Female',
                'Black female': 'Count_Person_Female',
                'Other races female': 'Count_Person_Female'
            }
        })
        df = df.rename(columns={
            'Year of Estimate': 'Year',
            'FIPS State and County Codes': 'geo_ID'
        })
        df['geo_ID'] = 'geoId/' + (df['geo_ID'].map(str)).str.zfill(5)
        df['geo_ID'] = df['geo_ID'] + '-' + df['Year'].astype(str)
        df = df.drop(columns=['Year'])
        # replacing rows with columns
        # to get all dataframe in one formate
        df = df.groupby(['geo_ID','Race/Sex Indicator']).sum().transpose()\
            .stack(0).reset_index()
        df[['geo_ID', 'Year']] = df['geo_ID'].str.split('-', expand=True)
        df = df.drop(columns=['level_0'])
        df['Measurement_Method'] = 'CensusPEPSurvey'
        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


def _county_1980_1990(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for county 1980 to 1990.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        df = pd.read_csv(file_path, skiprows=5)
        # adding age groups to get total value
        df['Total'] = df[_COLUMNS_TO_SUM].sum(axis=1)
        df = df.drop(columns=_COLUMNS_TO_SUM)
        df = df.replace({
            'Race/Sex Indicator': {
                'White male': 'Count_Person_Male',
                'Black male': 'Count_Person_Male',
                'Other races male': 'Count_Person_Male',
                'White female': 'Count_Person_Female',
                'Black female': 'Count_Person_Female',
                'Other races female': 'Count_Person_Female'
            }
        })
        df = df.rename(columns={
            'Year of Estimate': 'Year',
            'FIPS State and County Codes': 'geo_ID'
        })
        df['geo_ID'] = 'geoId/' + (df['geo_ID'].map(str)).str.zfill(5)
        df['geo_ID'] = df['geo_ID'] + '-' + df['Year'].astype(str)
        df = df.drop(columns=['Year'])
        # replacing rows with columns
        # to get all dataframe in one formate
        df = df.groupby(['geo_ID','Race/Sex Indicator']).sum().transpose()\
            .stack(0).reset_index()
        df[['geo_ID', 'Year']] = df['geo_ID'].str.split('-', expand=True)
        df = df.drop(columns=['level_0'])
        df['Measurement_Method'] = 'CensusPEPSurvey'
        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


def _county_1990_2000(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for county 1990 to 2000 and also aggregate
    county values to get state 1990 to 2000.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        column_names = ['Year', 'geo_ID', 'Age', 'Race-Sex', 'Ethnic', 'Value']
        df = pd.read_table(file_path, delim_whitespace=True, header=None)
        df.columns = column_names
        df['Year'] = '19' + df['Year'].astype(str)
        df['geo_ID'] = 'geoId/' + (df['geo_ID'].map(str)).str.zfill(5)
        df = df.drop(columns=['Age', 'Ethnic'])
        df = df.replace({
            'Race-Sex': {
                1: 'Count_Person_Male',
                2: 'Count_Person_Female',
                3: 'Count_Person_Male',
                4: 'Count_Person_Female',
                5: 'Count_Person_Male',
                6: 'Count_Person_Female',
                7: 'Count_Person_Male',
                8: 'Count_Person_Female'
            }
        })
        df['geo_ID'] = df['geo_ID'] + '-' + df['Year'].astype(str)
        df = df.drop(columns=['Year'])
        # replacing rows with columns
        # to get all dataframe in one formate
        df = df.groupby(['geo_ID','Race-Sex']).sum().transpose()\
            .stack(0).reset_index()
        df[['geo_ID', 'Year']] = df['geo_ID'].str.split('-', expand=True)
        df = df.drop(columns=['level_0'])
        # aggregating county data to get state data
        df_state = df.copy()
        df_state['geo_ID'] = (df['geo_ID'].map(str)).str[:len('geoId/NN')]
        df_state = df_state.groupby(['Year', 'geo_ID']).sum().reset_index()
        df = pd.concat([df_state, df], ignore_index=True)
        df['Measurement_Method'] = np.where(
            df['geo_ID'].str.len() > 10, 'CensusPEPSurvey',
            'dcAggregate/CensusPEPSurvey_PartialAggregate')
        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


def _county_2000_2010(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for county 2000 to 2010.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        df = pd.read_csv(file_path, encoding='ISO-8859-1')
        df['geo_ID'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(2) +\
            (df['COUNTY'].map(str)).str.zfill(3)
        df = df.query('AGEGRP == 0')
        df = df.query('SEX != 0')
        df = df.replace(
            {'SEX': {
                1: 'Count_Person_Male',
                2: 'Count_Person_Female'
            }})
        df = df.drop(columns=df.columns.difference([
            'SEX', 'POPESTIMATE2000', 'POPESTIMATE2001', 'POPESTIMATE2002',
            'POPESTIMATE2003', 'POPESTIMATE2004', 'POPESTIMATE2005',
            'POPESTIMATE2006', 'POPESTIMATE2007', 'POPESTIMATE2008',
            'POPESTIMATE2009', 'geo_ID'
        ]))

        df.rename(columns={
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
        },
                  inplace=True)
        # replacing rows with columns
        # to get all dataframe in one formate
        df = df.groupby(['geo_ID',
                         'SEX']).sum().transpose().stack(0).reset_index()
        df = df.rename(columns={'level_0': 'Year'})
        float_col = df.select_dtypes(include=['float64'])
        for col in float_col.columns.values:
            df[col] = df[col].astype('int64')
            df[col] = df[col].astype("str").str.replace("-1", "")
        df['Measurement_Method'] = 'CensusPEPSurvey'
        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


def _county_2010_2020(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for county 2010 to 2020.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        df = pd.read_csv(file_path, encoding='ISO-8859-1', low_memory=False)
        df['geo_ID'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(2) +\
            (df['COUNTY'].map(str)).str.zfill(3)
        df = df.replace({
            'YEAR': {
                1: 'April2010Census',
                2: 'April2010Estimate',
                3: '2010',
                4: '2011',
                5: '2012',
                6: '2013',
                7: '2014',
                8: '2015',
                9: '2016',
                10: '2017',
                11: '2018',
                12: '2019',
                13: 'April2020',
                14: '2020'
            }
        })
        df = df.rename(
            columns={
                'POPEST_MALE': 'Count_Person_Male',
                'POPEST_FEM': 'Count_Person_Female',
                'YEAR': 'Year'
            })
        df = df.drop(columns=df.columns.difference(
            ['Year', 'Count_Person_Male', 'Count_Person_Female', 'geo_ID']))

        df = df[(df['Year'] != 'April2010Census') &
                (df['Year'] != 'April2010Estimate') &
                (df['Year'] != 'April2020')]
        df['Measurement_Method'] = 'CensusPEPSurvey'
        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


def _county_latest(file_path: str) -> pd.DataFrame:
    """
    Process and cleans the file for county 2023.

    Args:
        file_path (str) : input file path.

    Returns:
        df (pd.DataFrame) : cleaned dataframe.
    """
    try:
        df = pd.read_csv(file_path, encoding='ISO-8859-1', low_memory=False)
        df['geo_ID'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(2)+\
            (df['COUNTY'].map(str)).str.zfill(3)
        df = df.replace({
            'YEAR': {
                1: 'April2020Estimate',
                2: 'July2020',
                3: '2021',
                4: '2022',
                5: '2023',
                6: '2024',
                7: '2025',
                8: '2026',
                9: '2027',
                10: '2028',
                11: '2029'
            }
        })

        df = df.rename(
            columns={
                'POPEST_MALE': 'Count_Person_Male',
                'POPEST_FEM': 'Count_Person_Female',
                'YEAR': 'Year'
            })
        df = df.drop(columns=df.columns.difference(
            ['Year', 'Count_Person_Male', 'Count_Person_Female', 'geo_ID']))

        df = df[(df['Year'] != 'April2020Estimate') &
                (df['Year'] != 'July2020')]
        df['Measurement_Method'] = 'CensusPEPSurvey'

        return df
    except Exception as e:
        logging.fatal(f"Error processing the file {file_path}: {e}")


class PopulationEstimateBySex:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    def __init__(self, input_path: str, csv_file_path: str, mcf_file_path: str,
                 tmcf_file_path: str) -> None:
        self._input_path = input_path
        self._cleaned_csv_file_path = csv_file_path
        self._mcf_file_path = mcf_file_path
        self._tmcf_file_path = tmcf_file_path

    def _generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.

        Args:
            None

        Returns:
            None
        """
        # Writing Genereated TMCF to local path.
        with open(self._tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(_TMCF_TEMPLATE.rstrip('\n'))

    def _generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Args:
            sv_list (list) : List of DataFrame Columns

        Returns:
            None
        """
        final_mcf_template = ""
        for sv in sv_list:
            gender = ''
            sv_temp = sv.split("_")
            for prop in sv_temp:
                if prop in ["Count", "Person"]:
                    continue
                if "Male" in prop or "Female" in prop:
                    gender = "\ngender: dcs:" + prop
            final_mcf_template += _MCF_TEMPLATE.format(
                pv1=sv,
                pv2=gender,
            ) + "\n"
        # Writing Genereated MCF to local path.
        with open(self._mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))

    def process(self):
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.

        Args:
            None

        Returns:
            None
        """
        ip_files = os.listdir(self._input_path)
        ip_files = [self._input_path + os.sep + file for file in ip_files]

        # Creating Output Directory
        output_path = os.path.dirname(self._cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_list = []
        final_df = pd.DataFrame()
        processed_count = 0
        total_files_to_process = len(ip_files)
        logging.info(f"No of files to be processed {len(ip_files)}")
        for file_path in ip_files:
            logging.info(f"Processing the file:{file_path}")
            if 'pe-02-1983.csv' in file_path or 'pe-02-1982.csv' in file_path:
                pass
            # Taking the File name out of the complete file address
            # Used -1 to pickup the last part which is file name
            # Read till -4 inorder to remove the .tsv extension

            file_name = file_path.split("/")[-1][:-7]

            # Define the base mappings for fixed years (e.g., 2023)
            file_to_function_mapping = {
                "pe-11-1": _national_1900_1979,
                "us-est90int": _national_1990_2000,
                "us-est90int-": _national_1990_2000,
                "us-est00int": _national_2000_2010,
                "us-est00int-": _national_2000_2010,
                "nc-est2020-agesex-": _national_2010_2020,
                "nc-est2020-agesex-r": _national_2010_2020,
                "pe": _state_1970_1980,
                "stiag": _state_1980_1990,
                "st-est00int-02-": _state_2000_2010,
                "st-est00int-02": _state_2000_2010,
                "SC-EST2020-AGESEX": _state_2010_2020,
                "SC-EST2020-AGESEX-": _state_2010_2020,
                "co-asr-1": _county_1970_1980,
                "pe-02-1": _county_1980_1990,
                "stch-icen1": _county_1990_2000,
                "co-est00int-agesex-": _county_2000_2010,
                "co-est00int-agesex-5": _county_2000_2010,
                "CC-EST2020-AGESEX-": _county_2010_2020,
                "CC-EST2020-AGESEX-A": _county_2010_2020
            }

            # Iterate from 2023 to 2029 and add mappings for years dynamically
            for file_year in range(2023, 2030):
                # For the 'national', 'state', and 'county' entries, use the same method for years 2023 to 2029
                if file_year < dt.now().year:
                    file_to_function_mapping[
                        f"nc-est{file_year}-agesex-"] = _national_latest
                    file_to_function_mapping[
                        f"nc-est{file_year}-agesex-r"] = _national_latest

                    file_to_function_mapping[
                        f"sc-est{file_year}-syasex-2"] = _state_latest
                    file_to_function_mapping[
                        f"sc-est{file_year}-syasex-3"] = _state_latest
                    file_to_function_mapping[
                        f"sc-est{file_year}-syasex-4"] = _state_latest
                    file_to_function_mapping[
                        f"sc-est{file_year}-syasex-5"] = _state_latest
                    file_to_function_mapping[
                        f"sc-est{file_year}-syasex-0"] = _state_latest
                    file_to_function_mapping[
                        f"sc-est{file_year}-syasex-1"] = _state_latest
                    file_to_function_mapping[
                        f"sc-est{file_year}-syasex-"] = _state_latest
                    file_to_function_mapping[
                        f"sc-est{file_year}-agesex-"] = _state_latest

                    file_to_function_mapping[
                        f"cc-est{file_year}-agesex-"] = _county_latest
                    file_to_function_mapping[
                        f"cc-est{file_year}-agesex-a"] = _county_latest

            df = file_to_function_mapping[file_name](file_path)

            if not df.empty:
                processed_count += 1
                final_df = pd.concat([final_df, df])
                final_df = final_df.sort_values(by=['Year', 'geo_ID'])
            else:
                logging.fatal(f"Failed to process {file_path}")

        logging.info(f"No of files processed {processed_count}")
        # Log the resulting dictionary
        logging.info(f"File-to-Function mappings: {file_to_function_mapping}")
        if processed_count == total_files_to_process & total_files_to_process > 0:
            final_df = _states_full_to_short_form(final_df, 'geo_ID', "geo_ID")
            final_df = _add_geo_id(final_df, "geo_ID", "geo_ID")
            final_df = pd.melt(
                final_df,
                id_vars=["Year", "geo_ID", "Measurement_Method"],
                value_vars=['Count_Person_Male', 'Count_Person_Female'],
                var_name="SV",
                value_name="Observation")

            final_df.to_csv(self._cleaned_csv_file_path, index=False)
            sv_list = ['Count_Person_Female', 'Count_Person_Male']
            self._generate_mcf(sv_list)
            self._generate_tmcf()
        else:
            logging.fatal(
                "Aborting output files as no of files to process not matching processed files"
            )


def add_future_year_urls():
    """
    This method adds the future year urls that has to be downloaded
    Args: None
    Return: None

    """
    global _FILES_TO_DOWNLOAD
    # Initialize the list to store files to download
    _FILES_TO_DOWNLOAD = []
    with open(os.path.join(_MODULE_DIR, 'input_url.json'), 'r') as inpit_file:
        _FILES_TO_DOWNLOAD = json.load(inpit_file)

    # List of URLs with placeholders for {YEAR} and {i}
    urls_to_scan = [
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/national/asrh/nc-est{YEAR}-agesex-res.csv",  # No {i}
        "https://www2.census.gov/programs-surveys/popest/tables/2020-{YEAR}/state/asrh/sc-est{YEAR}-syasex-{i}.xlsx",  # Contains {i}
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/counties/asrh/cc-est{YEAR}-agesex-all.csv",  # No {i}
        "https://www2.census.gov/programs-surveys/popest/tables/2020-{YEAR}/state/detail/sc-est{YEAR}-agesex-{i}.xlsx"  # Contains {i}
    ]

    # A set to track downloaded URLs for unique {YEAR} and URLs without {i}
    downloaded_year_urls = set()

    # Loop through years in reverse order from 2030 to 2023
    for future_year in range(2030, 2022, -1):  # From 2030 to 2023

        YEAR = future_year
        # Loop through URLs
        for url in urls_to_scan:
            if "{i}" in url:  # This URL contains the {i} variable, so we loop through i from 01 to 56
                for i in range(1, 57):  # Loop i from 01 to 56
                    formatted_i = f"{i:02}"  # Ensure i is always 2 digits (01, 02, ..., 56)
                    url_to_check = url.format(YEAR=YEAR, i=formatted_i)
                    logging.info(f"checking url: {url_to_check}")

                    try:
                        check_url = requests.head(url_to_check,
                                                  allow_redirects=True)
                        if check_url.status_code == 200:
                            _FILES_TO_DOWNLOAD.append(
                                {"download_path": url_to_check})

                    except requests.exceptions.RequestException as e:
                        logging.error(
                            f"URL is not accessible {url_to_check} due to {e}")

            else:  # This URL does not contain {i}, so we only need to process it once per year
                url_to_check = url.format(YEAR=YEAR)
                logging.info(f"checking url: {url_to_check}")
                # If the URL has already been processed for this year, skip it
                if url_to_check in downloaded_year_urls:
                    continue  # Skip this URL if it's already processed

                try:
                    check_url = requests.head(url_to_check,
                                              allow_redirects=True)
                    if check_url.status_code == 200:
                        _FILES_TO_DOWNLOAD.append(
                            {"download_path": url_to_check})
                        downloaded_year_urls.add(
                            url_to_check)  # Mark this URL as processed

                    else:
                        logging.error(
                            f"URL returned status code {check_url.status_code}: {url_to_check}"
                        )

                except requests.exceptions.RequestException as e:
                    logging.error(
                        f"URL is not accessible {url_to_check} due to {e}")


def download_files():
    """
    This method download the files and if there any file/files is not downloaded throws an exception
    Args : None
    Return : None

    """
    global _FILES_TO_DOWNLOAD
    session = requests.session()
    max_retry = 5
    for file_to_dowload in _FILES_TO_DOWNLOAD:
        file_name_to_save = None
        url = file_to_dowload['download_path']
        if 'file_name' in file_to_dowload and len(
                file_to_dowload['file_name'] > 5):
            file_name_to_save = file_to_dowload['file_name']
        else:
            file_name_to_save = url.split('/')[-1]
        retry_number = 0

        is_file_downloaded = False
        while is_file_downloaded == False:
            try:
                with session.get(url, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    if response.status_code == 200:
                        with open(
                                os.path.join(_INPUT_FILE_PATH,
                                             file_name_to_save), 'wb') as f:
                            f.write(response.content)
                            file_to_dowload['is_downloaded'] = True
                            logging.info(f"Downloaded file : {url}")
                            is_file_downloaded = True
                    else:
                        logging.error(f"Retry file download {{url}}")
                        time.sleep(5)
                        retry_number += 1
                        if retry_number > max_retry:
                            logging.fatal(f"Error downloading {url}")

            except Exception as e:
                logging.fatal(f"Retry file download {url}")
                time.sleep(5)
                retry_number += 1
                if retry_number > max_retry:
                    logging.fatal(f"Error downloading {url}")

    return True


def main(_):
    """
    Main function that produces the output files and place them in the output folder
    It also includes the modes to run the scripts.
    Arg : None
    Return : None

    """
    mode = _FLAGS.mode
    # Defining Output Files
    csv_name = "population_estimate_sex.csv"
    mcf_name = "population_estimate_sex.mcf"
    tmcf_name = "population_estimate_sex.tmcf"
    data_file_path = os.path.join(_MODULE_DIR, "output")
    if not (os.path.exists(data_file_path)):
        os.mkdir(data_file_path)
    if not (os.path.exists(_INPUT_FILE_PATH)):
        os.mkdir(_INPUT_FILE_PATH)
    cleaned_csv_path = data_file_path + os.sep + csv_name
    mcf_path = data_file_path + os.sep + mcf_name
    tmcf_path = data_file_path + os.sep + tmcf_name

    download_status = True
    if mode == "" or mode == "download":
        # download & process
        add_future_year_urls()
        download_status = download_files()
    if download_status and (mode == "" or mode == "process"):
        loader = PopulationEstimateBySex(_INPUT_FILE_PATH, cleaned_csv_path,
                                         mcf_path, tmcf_path)
        loader.process()


if __name__ == "__main__":
    app.run(main)
