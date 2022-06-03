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
Script to read all
the generated csv for
National, State and County
and generate final csv, MCF, TMCF file
'''

import pandas as pd


def _create_single_csv(sv_dict):
    """
    Function generate 3 csv
    1. preprocess.csv : for the files which are processed as is.
    2. preprocess_aggregate.csv : for the files which
        are having Count Person Male/Female aggregated.
    3. preprocess_aggregate_state_2010_2020.csv : for the files
        which are aggregated from different geo granularity.
    """
    # list of output files which are having no aggregation
    CSVLIST = sv_dict[1]

    # list of output files which are having aggregation Count_Person_Male
    # and Count_Person_Female
    CSVLIST1 = sv_dict[2]

    # aggregated State values 2010-2020 from County 2010-2020 data
    CSVLIST2 = sv_dict[3]

    df1 = pd.DataFrame()
    df3 = pd.DataFrame()
    df5 = pd.DataFrame()

    # aggregating the files which are processed as is
    # to final output csv
    if len(CSVLIST) > 0:
        for i in CSVLIST:
            df = pd.read_csv(i, header=0)
            for col in df.columns:
                df[col] = df[col].astype("str")
            df1 = pd.concat([df, df1], ignore_index=True)

        # coverting year values to int
        df1['Year'] = df1['Year'].astype(float).astype(int)

        # dropping unwanted column
        df1.drop(columns=['Unnamed: 0'], inplace=True)

        # making geoid uniform
        df1['geo_ID'] = df1['geo_ID'].str.strip()

        # sorting the values based on year and geoid
        df1.sort_values(by=['Year', 'geo_ID'], ascending=True, inplace=True)

        df1 = df1.replace('nan', '')
        # writing output to final csv
        df1.to_csv("postprocess.csv", index=False)

        # collecting all the column headers
        sv_list1 = df1.columns.to_list()

        sv_dict[1] = sv_list1

    # aggregating the files which are having
    # aggregation Count_Person_Male and Count_Person_Female
    # to final output csv
    if len(CSVLIST1) > 0:
        for i in CSVLIST1:
            df2 = pd.read_csv(i, header=0)
            for col in df2.columns:
                df2[col] = df2[col].astype("str")
            df3 = pd.concat([df2, df3], ignore_index=True)

        # coverting year values to int
        df3['Year'] = df3['Year'].astype(float).astype(int)

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
            'Count_Person_Female_AsianOrPacificIslander', 'Count_Person_Male',
            'Count_Person_Female'
        ]]

        df3 = df3.replace('nan', '')
        df3.to_csv("postprocess_aggregate.csv", index=False)

        # collecting all the column headers
        sv_list2 = df3.columns.to_list()

        sv_dict[2] = sv_list2

    # aggregating the files which are aggregated
    # from different geo granularity
    # to final output csv
    if len(CSVLIST2) > 0:
        for i in CSVLIST2:
            df4 = pd.read_csv(i, header=0)
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
        df5.drop(columns=['Unnamed: 0'], inplace=True)

        # writing output to final csv
        df5.to_csv("postprocess_aggregate_state_2010_2020.csv", index=False)

        # collecting all the column headers
        sv_list3 = df5.columns.to_list()

        sv_dict[3] = sv_list3

    return sv_dict


def _generate_mcf(sv_list: list, flag1: int) -> None:
    """
    This method generates 3 MCF file w.r.t
    dataframe headers and defined MCF template
    1. sex_race.mcf : for the files which are processed as is.
    2. sex_race_aggregate.mcf : for the files which
        are having Count Person Male/Female aggregated.
    3. sex_race_aggregate_state_2010_2020.mcf : for the files
        which are aggregated from different geo granularity.
    Arguments:
        sv_list (list) : List of DataFrame Columns
        flag1 (int)
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
    for sv in sv_list:
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
    if flag1 == 1:
        with open("sex_race.mcf", 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
    elif flag1 == 2:
        with open("sex_race_aggregate.mcf", 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
    else:
        with open("sex_race_aggregate_state_2010_2020.mcf",\
             'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))


def _generate_tmcf(df_cols: list, flag2: int) -> None:
    """
            This method generates 3 TMCF file w.r.t
    dataframe headers and defined TMCF template
    1. Sex_Rcae.tmcf : for the files which are processed as is.
    2. sex_race_aggregate.tmcf : for the files which
        are having Count Person Male/Female aggregated.
    3. sex_race_aggregate_state_2010_2020.tmcf : for the files
        which are aggregated from different geo granularity.
    Arguments:
        df_cols (list) : List of DataFrame Columns
        flag2 (int)
    Returns:
        None
    """

    tmcf_template = """Node: E:postprocess->E{}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{}
measurementMethod: dcs:{}
observationAbout: C:postprocess->geo_ID
observationDate: C:postprocess->Year
observationPeriod: \"P1Y\"
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
        if flag2 == 1:
            measure = "CensusPEPSurvey"
        elif flag2 == 2:
            if cols == "Count_Person_Male":
                measure = "dcAggregate/CensusPEPSurvey"
            elif cols == "Count_Person_Female":
                measure = "dcAggregate/CensusPEPSurvey"
            else:
                measure = "CensusPEPSurvey"
        else:
            measure = "dcAggregate/CensusPEPSurvey"
        tmcf = tmcf + tmcf_template.format(j, cols, measure, cols) + "\n"
        j = j + 1
    # Writing Genereated TMCF to local path.
    if flag2 == 1:
        with open("sex_race.tmcf", 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))
    elif flag2 == 2:
        with open("sex_race_aggregate.tmcf", 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))
    else:
        with open("sex_race_aggregate_state_2010_2020.tmcf"\
                , 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))
