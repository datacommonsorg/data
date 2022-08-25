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
Script to read all
the generated csv for
National, State and County
and generate final CSV, MCF, TMCF file.
"""

import pandas as pd
import os
from common import Outputfiles, _OUTPUTFINAL, _OUTPUTINTERMEDIATE

_CODEDIR = os.path.dirname(os.path.realpath(__file__))


def write_to_tmcf(filename: str, tmcf: str):
    with open(os.path.join(_CODEDIR, _OUTPUTFINAL, filename + ".tmcf"),
              'w+',
              encoding='utf-8') as f_out:
        f_out.write(tmcf.rstrip('\n'))


def write_to_mcf(filename: str, final_mcf_template: str):
    with open(os.path.join(_CODEDIR, _OUTPUTFINAL, filename + ".mcf"),
              'w+',
              encoding='utf-8') as f_out:
        f_out.write(final_mcf_template.rstrip('\n'))


def process_national_before_2000(df: pd.DataFrame):
    # coverting year values to int
    df['Year'] = df['Year'].astype(float).astype(int)

    # dropping unwanted column
    df = df.drop(columns=['Unnamed: 0','Count_Person_Male',\
        'Count_Person_Female'])

    # making geoid uniform
    df['geo_ID'] = df['geo_ID'].str.strip()

    # sorting the values based on year and geoid
    df.sort_values(by=['Year', 'geo_ID'], ascending=True, inplace=True)

    df = df.replace('nan', '')
    # writing output to final csv
    df.to_csv(os.path.join(_CODEDIR, _OUTPUTFINAL, "national_before_2000.csv"),
              index=False)

    # collecting all the column headers
    columns_of_national_before_2000 = df.columns.to_list()
    return columns_of_national_before_2000


def process_state_county_before_2000(df: pd.DataFrame):
    # coverting year values to int
    df['Year'] = df['Year'].astype(float).astype(int)

    # dropping unwanted column
    df = df.drop(columns=['Count_Person_Male', 'Count_Person_Female'])

    # making geoid uniform
    df['geo_ID'] = df['geo_ID'].str.strip()

    # sorting the values based on year and geoid
    df.sort_values(by=['Year', 'geo_ID'], ascending=True, inplace=True)

    # writing output to final csv
    df = df[[
        'Year', 'geo_ID', 'Count_Person_Male_WhiteAlone',
        'Count_Person_Female_WhiteAlone',
        'Count_Person_Male_BlackOrAfricanAmericanAlone',
        'Count_Person_Female_BlackOrAfricanAmericanAlone',
        'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone',
        'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone',
        'Count_Person_Male_AsianOrPacificIslander',
        'Count_Person_Female_AsianOrPacificIslander'
    ]]

    df = df.replace('nan', '')
    float_col = df.select_dtypes(include=['float64'])
    for col in float_col.columns.values:
        df[col] = df[col].astype('int64')

    df.to_csv(os.path.join(_CODEDIR, _OUTPUTFINAL,
                           "state_county_before_2000.csv"),
              index=False)

    # collecting all the column headers
    columns_of_state_county_before_2000 = df.columns.to_list()
    return columns_of_state_county_before_2000


def process_state_county_after_2000(df: pd.DataFrame):
    # coverting year values to int
    df['Year'] = df['Year'].astype(float).astype(int)

    # dropping unwanted column
    df = df.drop(columns=['Unnamed: 0','Count_Person_Male',\
        'Count_Person_Female'])

    # making geoid uniform
    df['geo_ID'] = df['geo_ID'].str.strip()

    # sorting the values based on year and geoid
    df.sort_values(by=['Year', 'geo_ID'], ascending=True, inplace=True)

    df = df.replace('nan', '')
    # writing output to final csv
    df.to_csv(os.path.join(_CODEDIR, _OUTPUTFINAL,
                           "state_county_after_2000.csv"),
              index=False)

    # collecting all the column headers
    columns_of_state_county_after_2000 = df.columns.to_list()
    return columns_of_state_county_after_2000


def process_national_after_2000(df: pd.DataFrame):
    # coverting year values to int
    df['Year'] = df['Year'].astype(float).astype(int)

    # making geoid uniform
    df['geo_ID'] = df['geo_ID'].str.strip()

    # sorting the values based on year and geoid
    df.sort_values(by=['Year', 'geo_ID'], ascending=True, inplace=True)

    # dropping unwanted column
    df = df.drop(columns=['Unnamed: 0','Count_Person_Male',\
        'Count_Person_Female'])

    # writing output to final csv
    df.to_csv(os.path.join(_CODEDIR, _OUTPUTFINAL, "national_after_2000.csv"),
              index=False)

    # collecting all the column headers
    columns_of_national_after_2000 = df.columns.to_list()
    return columns_of_national_after_2000


def create_single_csv(output_files_names: list):
    """
    Function generate 4 CSV
    1. national_before_2000.csv : for the natioanl files before the year 2000.
    2. state_county_before_2000.csv : for the state and county files before
    the year 2000.
    3. state_county_after_2000.csv : for the state and county files after
    the year 2000.
    4. national_after_2000.csv : for the natioanl files after the year 2000.

    Args:
        output_files_names (List) : nested list of output file names generated.

    Return:
        column_name (List) : list of all the column names.
    """
    df1 = pd.DataFrame()
    df3 = pd.DataFrame()
    df5 = pd.DataFrame()
    df7 = pd.DataFrame()
    column_names = {}

    # list of output files for national before the year 2000
    national_before_2000 = output_files_names[
        Outputfiles.NationalBefore2000.value]
    # list of output files for state and county before the year 2000
    state_county_before_2000 = output_files_names[
        Outputfiles.StateCountyBefore2000.value]
    # list of output files for state and county after the year 2000
    state_county_after_2000 = output_files_names[
        Outputfiles.StateCountyAfter2000.value]
    # list of output files for national after the year 2000
    national_after_2000 = output_files_names[
        Outputfiles.NationalAfter2000.value]

    # aggregating the files which are having national data before the year 2000
    # to final output csv
    if len(national_before_2000) > 0:
        for i in national_before_2000:
            #os.path.join(_CODEDIR, _OUTPUTFINAL, "national_after_2000.csv")
            df = pd.read_csv(os.path.join(_CODEDIR, _OUTPUTINTERMEDIATE, i),
                             header=0)
            for col in df.columns:
                df[col] = df[col].astype("str")
            df1 = pd.concat([df, df1], ignore_index=True)
        column_names[1] = process_national_before_2000(df1)

    # aggregating the files which are having state and county data before the
    # year 2000 to final output csv
    if len(state_county_before_2000) > 0:
        for i in state_county_before_2000:
            df2 = pd.read_csv(os.path.join(_CODEDIR, _OUTPUTINTERMEDIATE, i),
                              header=0)
            for col in df2.columns:
                df2[col] = df2[col].astype("str")
            df3 = pd.concat([df2, df3], ignore_index=True)
        column_names[2] = process_state_county_before_2000(df3)

    # aggregating the files which are having state and county data after the
    # year 2000 to final output csv
    if len(state_county_after_2000) > 0:
        for i in state_county_after_2000:
            df6 = pd.read_csv(os.path.join(_CODEDIR, _OUTPUTINTERMEDIATE, i),
                              header=0)
            for col in df6.columns:
                df6[col] = df6[col].astype("str")
            df7 = pd.concat([df6, df7], ignore_index=True)
        column_names[3] = process_state_county_after_2000(df7)

    # aggregating the files which are having national data after the year 2000
    # to final output csv
    if len(national_after_2000) > 0:
        for i in national_after_2000:
            df4 = pd.read_csv(os.path.join(_CODEDIR, _OUTPUTINTERMEDIATE, i),
                              header=0)
            for col in df4.columns:
                df4[col] = df4[col].astype("str")
            df5 = pd.concat([df4, df5], ignore_index=True)
        column_names[4] = process_national_after_2000(df5)
    return column_names


def generate_mcf(statvar_names: list, mcfflag: Outputfiles) -> None:
    """
    Function generate 4 MCF
    1. national_before_2000.mcf : for the natioanl files before the year 2000.
    2. state_county_before_2000.mcf : for the state and county files before
    the year 2000.
    3. state_county_after_2000.mcf : for the state and county files after
    the year 2000.
    4. national_after_2000.mcf : for the natioanl files after the year 2000.

    Args:
        sv_names (list) : List of DataFrame Columns
        mcfflag (Enum) : flag value helps in generating output files.

    Returns:
        None
    """
    mcf_template = """Node: dcid:{}
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
{}{}
statType: dcs:measuredValue
measuredProperty: dcs:count
"""

    final_mcf_template = ""
    for sv in statvar_names:
        if "Total" in sv:
            continue
        if "Year" in sv:
            continue
        if "geo_ID" in sv:
            continue
        gender = ''
        race = ''
        sv_prop = sv.split("_")
        for prop in sv_prop:
            if prop in ["Count", "Person"]:
                continue
            if "Male" in prop or "Female" in prop:
                gender = "gender: dcs:" + prop
            else:
                race = "race: dcs:" + prop + "\n"
        final_mcf_template += mcf_template.format(sv, race, gender) + "\n"
    # Writing Genereated MCF to local path.
    if mcfflag == Outputfiles.NationalBefore2000.value:
        write_to_mcf("national_before_2000", final_mcf_template)
    elif mcfflag == Outputfiles.StateCountyBefore2000.value:
        write_to_mcf("state_county_before_2000", final_mcf_template)
    elif mcfflag == Outputfiles.StateCountyAfter2000.value:
        write_to_mcf("state_county_after_2000", final_mcf_template)
    else:
        write_to_mcf("national_after_2000", final_mcf_template)


def generate_tmcf(df_cols: list, tmcfflag: Outputfiles) -> None:
    """
    Function generate 4 TMCF
    1. national_before_2000.tmcf : for the natioanl files before the year 2000.
    2. state_county_before_2000.tmcf : for the state and county files before
    the year 2000.
    3. state_county_after_2000.tmcf : for the state and county files after
    the year 2000.
    4. national_after_2000.tmcf : for the natioanl files after the year 2000.

    Args:
        df_cols (list) : List of DataFrame Columns
        tmcfflag (Enum) : flag value helps in generating output files.

    Returns:
        None
    """

    tmcf_template = """Node: E:postprocess->E{}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{}
measurementMethod: dcs:{}
observationAbout: C:postprocess->geo_ID
observationDate: C:postprocess->Year
observationPeriod: "P1Y"
value: C:postprocess->{} 

"""
    j = 0
    mmethod = ""
    tmcf = ""
    for cols in df_cols:
        if "Year" in cols:
            continue
        if "geo_ID" in cols:
            continue
        if tmcfflag == Outputfiles.NationalBefore2000.value:
            if cols.lower().endswith('male'):
                mmethod = "dcAggregate/CensusPEPSurvey_PartialAggregate"
            elif cols.lower().endswith('nonwhite'):
                mmethod = "CensusPEPSurvey_RaceUpto1999"
            else:
                mmethod = "dcAggregate/CensusPEPSurvey_PartialAggregate_RaceUpto1999"
        elif tmcfflag == Outputfiles.StateCountyBefore2000.value:
            if cols.lower().endswith('male'):
                mmethod = "dcAggregate/CensusPEPSurvey_PartialAggregate"
            else:
                mmethod = "CensusPEPSurvey_RaceUpto1999"
        elif tmcfflag == Outputfiles.StateCountyAfter2000.value:
            if cols.lower().endswith('male'):
                mmethod = "dcAggregate/CensusPEPSurvey_PartialAggregate"
            else:
                mmethod = "CensusPEPSurvey_Race2000Onwards"
        else:
            if cols.lower().endswith('male'):
                mmethod = "dcAggregate/CensusPEPSurvey_PartialAggregate"
            else:
                mmethod = "dcAggregate/CensusPEPSurvey_PartialAggregate_Race2000Onwards"
        tmcf = tmcf + tmcf_template.format(j, cols, mmethod, cols) + "\n"
        j = j + 1
    # Writing Genereated TMCF to local path.
    if tmcfflag == Outputfiles.NationalBefore2000.value:
        write_to_tmcf("national_before_2000", tmcf)
    elif tmcfflag == Outputfiles.StateCountyBefore2000.value:
        write_to_tmcf("state_county_before_2000", tmcf)
    elif tmcfflag == Outputfiles.StateCountyAfter2000.value:
        write_to_tmcf("state_county_after_2000", tmcf)
    else:
        write_to_tmcf("national_after_2000", tmcf)
