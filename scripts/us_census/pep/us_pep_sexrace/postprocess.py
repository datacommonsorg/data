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
and generate final csv, MCF, TMCF file
"""

import pandas as pd
import os

_CODEDIR = os.path.dirname(os.path.realpath(__file__))


def create_single_csv(output_files_names: list):
    """
    Function generate 3 csv
    1. preprocess.csv : for the files which are processed as is.
    2. preprocess_aggregate.csv : for the files which
        are having Count Person Male/Female aggregated.
    3. preprocess_aggregate_state_2010_2020.csv : for the files
        which are aggregated from different geo granularity.

    Args:
        output_files_names (List) : nested list of output file names generated.

    Return:
        column_name (List) : list of all the column names
    """
    # list of output files which are having no aggregation
    as_is_output_files = output_files_names[1]

    # list of output files which are having aggregation Count_Person_Male
    # and Count_Person_Female
    aggregate_output_files_before = output_files_names[2]

    # list of output files which are having aggregation Count_Person_Male
    # and Count_Person_Female
    aggregate_output_files_after = output_files_names[3]

    # aggregated State values 2010-2020 from County 2010-2020 data
    geo_aggregate_output_files = output_files_names[4]

    df1 = pd.DataFrame()
    df3 = pd.DataFrame()
    df5 = pd.DataFrame()
    df7 = pd.DataFrame()

    column_names = {}
    # aggregating the files which are processed as is
    # to final output csv
    if len(as_is_output_files) > 0:
        for i in as_is_output_files:
            df = pd.read_csv(_CODEDIR + "/output_files/intermediate/" + i,
                             header=0)
            for col in df.columns:
                df[col] = df[col].astype("str")
            df1 = pd.concat([df, df1], ignore_index=True)

        # coverting year values to int
        df1['Year'] = df1['Year'].astype(float).astype(int)

        # dropping unwanted column
        df1 = df1.drop(columns=['Unnamed: 0','Count_Person_Male',\
            'Count_Person_Female'])

        # making geoid uniform
        df1['geo_ID'] = df1['geo_ID'].str.strip()

        # sorting the values based on year and geoid
        df1.sort_values(by=['Year', 'geo_ID'], ascending=True, inplace=True)

        df1 = df1.replace('nan', '')
        # writing output to final csv
        df1.to_csv(_CODEDIR + "/output_files/final/" +
                   "national_before_2000.csv",
                   index=False)

        # collecting all the column headers
        columns_of_as_is_output_files = df1.columns.to_list()

        column_names[1] = columns_of_as_is_output_files

    # aggregating the files which are having
    # aggregation Count_Person_Male and Count_Person_Female
    # to final output csv
    if len(aggregate_output_files_before) > 0:
        for i in aggregate_output_files_before:
            df2 = pd.read_csv(_CODEDIR + "/output_files/intermediate/" + i,
                              header=0)
            for col in df2.columns:
                df2[col] = df2[col].astype("str")
            df3 = pd.concat([df2, df3], ignore_index=True)

        # coverting year values to int
        df3['Year'] = df3['Year'].astype(float).astype(int)

        # dropping unwanted column
        df3 = df3.drop(columns=['Count_Person_Male', 'Count_Person_Female'])

        # making geoid uniform
        df3['geo_ID'] = df3['geo_ID'].str.strip()

        # sorting the values based on year and geoid
        df3.sort_values(by=['Year', 'geo_ID'], ascending=True, inplace=True)

        # writing output to final csv
        df3 = df3[[
            'Year', 'geo_ID', 'Count_Person_Male_WhiteAlone',
            'Count_Person_Female_WhiteAlone',
            'Count_Person_Male_BlackOrAfricanAmericanAlone',
            'Count_Person_Female_BlackOrAfricanAmericanAlone',
            'Count_Person_Male_AmericanIndianAndAlaskaNativeAlone',
            'Count_Person_Female_AmericanIndianAndAlaskaNativeAlone',
            'Count_Person_Male_AsianOrPacificIslander',
            'Count_Person_Female_AsianOrPacificIslander'
        ]]

        df3 = df3.replace('nan', '')
        float_col = df3.select_dtypes(include=['float64'])
        for col in float_col.columns.values:
            df3[col] = df3[col].astype('int64')

        df3.to_csv(_CODEDIR + "/output_files/final/" +
                   "state_county_before_2000.csv",
                   index=False)

        # collecting all the column headers
        columns_of_aggregate_output_files_before = df3.columns.to_list()

        column_names[2] = columns_of_aggregate_output_files_before

    if len(aggregate_output_files_after) > 0:
        for i in aggregate_output_files_after:
            df6 = pd.read_csv(_CODEDIR + "/output_files/intermediate/" + i,
                              header=0)
            for col in df6.columns:
                df6[col] = df6[col].astype("str")
            df7 = pd.concat([df6, df7], ignore_index=True)

        # coverting year values to int
        df7['Year'] = df7['Year'].astype(float).astype(int)

        # dropping unwanted column
        df7 = df7.drop(columns=['Unnamed: 0','Count_Person_Male',\
            'Count_Person_Female'])

        # making geoid uniform
        df7['geo_ID'] = df7['geo_ID'].str.strip()

        # sorting the values based on year and geoid
        df7.sort_values(by=['Year', 'geo_ID'], ascending=True, inplace=True)

        df7 = df7.replace('nan', '')
        # writing output to final csv
        df7.to_csv(_CODEDIR + "/output_files/final/" +
                   "state_county_after_2000.csv",
                   index=False)

        # collecting all the column headers
        columns_of_as_is_output_files_after = df7.columns.to_list()

        column_names[3] = columns_of_as_is_output_files_after

    # aggregating the files which are aggregated
    # from different geo granularity
    # to final output csv
    if len(geo_aggregate_output_files) > 0:
        for i in geo_aggregate_output_files:
            df4 = pd.read_csv(_CODEDIR + "/output_files/intermediate/" + i,
                              header=0)
            for col in df4.columns:
                df4[col] = df4[col].astype("str")
            df5 = pd.concat([df4, df5], ignore_index=True)

        # coverting year values to int
        df5['Year'] = df5['Year'].astype(float).astype(int)

        # making geoid uniform
        df5['geo_ID'] = df5['geo_ID'].str.strip()

        # sorting the values based on year and geoid
        df5.sort_values(by=['Year', 'geo_ID'], ascending=True, inplace=True)

        # dropping unwanted column
        df5 = df5.drop(columns=['Unnamed: 0','Count_Person_Male',\
            'Count_Person_Female'])

        # writing output to final csv
        df5.to_csv(_CODEDIR + "/output_files/final/" +
                   "national_after_2000.csv",
                   index=False)

        # collecting all the column headers
        columns_of_geo_aggregate_output_files = df5.columns.to_list()

        column_names[4] = columns_of_geo_aggregate_output_files
    return column_names


def generate_mcf(statvar_names: list, flag: int) -> None:
    """
    This method generates 3 MCF file w.r.t
    dataframe headers and defined MCF template
    1. sex_race.mcf : for the files which are processed as is.
    2. sex_race_aggregate.mcf : for the files which
        are having Count Person Male/Female aggregated.
    3. sex_race_aggregate_state_2010_2020.mcf : for the files
        which are aggregated from different geo granularity.

    Args:
        sv_names (list) : List of DataFrame Columns
        flag (int) : flag value helps in generating
        output files. Possible values are 1,2 and 3.
        1 - generate mcf for files which are processed as is
        2 - generate mcf for files which are having
        Count_Person_Male and Count_Person_Female aggregated
        3 - generate mcf for files which are aggregated
        from different geo granulartiy.

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
    if flag == 1:
        with open(_CODEDIR + "/output_files/final/" +
                  "national_before_2000.mcf",
                  'w+',
                  encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
    elif flag == 2:
        with open(_CODEDIR + "/output_files/final/" +
                  "state_county_before_2000.mcf",
                  'w+',
                  encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
    elif flag == 3:
        with open(_CODEDIR + "/output_files/final/" +
                  "state_county_after_2000.mcf",
                  'w+',
                  encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
    else:
        with open(_CODEDIR + "/output_files/final/" + "national_after_2000.mcf",\
             'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))


def generate_tmcf(df_cols: list, flag: int) -> None:
    """
            This method generates 3 TMCF file w.r.t
    dataframe headers and defined TMCF template
    1. Sex_Rcae.tmcf : for the files which are processed as is.
    2. sex_race_aggregate.tmcf : for the files which
        are having Count Person Male/Female aggregated.
    3. sex_race_aggregate_state_2010_2020.tmcf : for the files
        which are aggregated from different geo granularity.

    Args:
        df_cols (list) : List of DataFrame Columns
        flag (int) : flag value helps in generating
        output files. Possible values are 1,2 and 3.
        1 - generate tmcf for files which are processed as is
        2 - generate tmcf for files which are having
        Count_Person_Male and Count_Person_Female aggregated
        3 - generate tmcf for files which are aggregated
        from different geo granulartiy.

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
    measure = ""
    tmcf = ""
    for cols in df_cols:
        if "Year" in cols:
            continue
        if "geo_ID" in cols:
            continue
        if flag == 1:
            if cols.lower().endswith('male'):
                measure = "dcAggregate/CensusPEPSurvey_PartialAggregate"
            elif cols.lower().endswith('nonwhite'):
                measure = "CensusPEPSurvey_RaceUpto1999"
            else:
                measure = "dcAggregate/CensusPEPSurvey_PartialAggregate_RaceUpto1999"
        elif flag == 2:
            if cols.lower().endswith('male'):
                measure = "dcAggregate/CensusPEPSurvey_PartialAggregate"
            else:
                measure = "CensusPEPSurvey_RaceUpto1999"
        elif flag == 3:
            if cols.lower().endswith('male'):
                measure = "dcAggregate/CensusPEPSurvey_PartialAggregate"
            else:
                measure = "CensusPEPSurvey_Race2000Onwards"
        else:
            if cols.lower().endswith('male'):
                measure = "dcAggregate/CensusPEPSurvey_PartialAggregate"
            else:
                measure = "dcAggregate/CensusPEPSurvey_PartialAggregate_Race2000Onwards"
        tmcf = tmcf + tmcf_template.format(j, cols, measure, cols) + "\n"
        j = j + 1
    # Writing Genereated TMCF to local path.
    if flag == 1:
        with open(_CODEDIR + "/output_files/final/" +
                  "national_before_2000.tmcf",
                  'w+',
                  encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))
    elif flag == 2:
        with open(_CODEDIR + "/output_files/final/" +
                  "state_county_before_2000.tmcf",
                  'w+',
                  encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))
    elif flag == 3:
        with open(_CODEDIR + "/output_files/final/" +
                  "state_county_after_2000.tmcf",
                  'w+',
                  encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))
    else:
        with open(_CODEDIR + "/output_files/final/" + "national_after_2000.tmcf"\
                , 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))
