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
This Python Script is for County Level Data 2020-2029.
'''
import os
import numpy as np
import pandas as pd
from common_functions import input_url, replace_agegrp


def county2029(url_file: str, output_folder: str):
    '''
    This Python Script Loads csv datasets from 2020-2029 on a County Level,
    cleans it and create a cleaned csv.
    '''
    df = pd.read_csv(url_file, encoding='ISO-8859-1', low_memory=False)
    #Writing raw data to csv
    df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "raw_data", 'raw_data_county_2020_2029.csv'),
              index=False)
    # Filter by agegrp = 0.
    df = df.query("YEAR not in [1]")
    df = df.query("AGEGRP != 0")
    # Filter years 3 - 14.
    df['YEAR'] = df['YEAR'].astype(str)
    base_year = 2020
    df['YEAR'] = df['YEAR'].astype(int) + base_year - 2
    df.insert(6, 'geo_ID', 'geoId/', True)
    df['geo_ID'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(2) + \
        (df['COUNTY'].map(str)).str.zfill(3)
    df['AGEGRP'] = df['AGEGRP'].astype(str)
    # Replacing the numbers with more understandable metadata headings.
    # Code 0 is sent if AGEGRP starts from 0 and 1 if it starts from 0To4
    df = replace_agegrp(df, 1)
    # Drop unwanted columns.
    df.drop(columns=['SUMLEV', 'STATE', 'COUNTY', 'STNAME', 'CTYNAME'], \
        inplace=True)
    df = df.drop(columns=[
        'TOT_POP', 'NH_MALE', 'NH_FEMALE', 'NHWA_MALE', 'NHWA_FEMALE',
        'NHBA_MALE', 'NHBA_FEMALE', 'NHIA_MALE', 'NHIA_FEMALE', 'NHAA_MALE',
        'NHAA_FEMALE', 'NHNA_MALE', 'NHNA_FEMALE', 'NHTOM_MALE', 'NHTOM_FEMALE',
        'H_MALE', 'H_FEMALE', 'HWA_MALE', 'HWA_FEMALE', 'HBA_MALE',
        'HBA_FEMALE', 'HIA_MALE', 'HIA_FEMALE', 'HAA_MALE', 'HAA_FEMALE',
        'HNA_MALE', 'HNA_FEMALE', 'HTOM_MALE', 'HTOM_FEMALE'
    ])

    columns = [
        'Year', 'geo_ID', 'AGEGRP', 'TOT_MALE', 'TOT_FEMALE', 'WA_MALE',
        'WA_FEMALE', 'BA_MALE', 'BA_FEMALE', 'IA_MALE', 'IA_FEMALE', 'AA_MALE',
        'AA_FEMALE', 'NA_MALE', 'NA_FEMALE', 'TOM_MALE', 'TOM_FEMALE',
        'WAC_MALE', 'WAC_FEMALE', 'BAC_MALE', 'BAC_FEMALE', 'IAC_MALE',
        'IAC_FEMALE', 'AAC_MALE', 'AAC_FEMALE', 'NAC_MALE', 'NAC_FEMALE',
        'NHWAC_MALE', 'NHWAC_FEMALE', 'NHBAC_MALE', 'NHBAC_FEMALE',
        'NHIAC_MALE', 'NHIAC_FEMALE', 'NHAAC_MALE', 'NHAAC_FEMALE',
        'NHNAC_MALE', 'NHNAC_FEMALE', 'HWAC_MALE', 'HWAC_FEMALE', 'HBAC_MALE',
        'HBAC_FEMALE', 'HIAC_MALE', 'HIAC_FEMALE', 'HAAC_MALE', 'HAAC_FEMALE',
        'HNAC_MALE', 'HNAC_FEMALE'
    ]

    df['Year'] = df['YEAR']
    df.drop(columns=['YEAR'], inplace=True)
    df['WhiteAloneAgg'] = df['WA_MALE'].astype(int) + df['WA_FEMALE'].astype(
        int)
    df['BlackOrAfricanAmericanAlone'] = df['BA_MALE'].astype(int)\
        +df['BA_FEMALE'].astype(int)
    df['AmericanIndianAndAlaskaNativeAlone'] = df['IA_MALE'].astype(int)\
        +df['IA_FEMALE'].astype(int)
    df['AsianAloneAgg'] = df['AA_MALE'].astype(int) + df['AA_FEMALE'].astype(
        int)
    df['NativeHawaiianAndOtherPacificIslanderAloneAgg'] = df['NA_MALE']\
        .astype(int)+df['NA_FEMALE'].astype(int)
    df['TwoOrMoreRacesAgg'] = df['TOM_MALE'].astype(int)+\
        df['TOM_FEMALE'].astype(int)
    df = df.melt(id_vars=['Year','geo_ID' ,'AGEGRP'], var_name='sv' , \
        value_name='observation')
    # Changing Names to be more understandable.
    _sexrace_dict = {
        'TOT_MALE':
            'Male',
        'TOT_FEMALE':
            'Female',
        'WA_MALE':
            'Male_WhiteAlone',
        'WA_FEMALE':
            'Female_WhiteAlone',
        'BA_MALE':
            'Male_BlackOrAfricanAmericanAlone',
        'BA_FEMALE':
            'Female_BlackOrAfricanAmericanAlone',
        'IA_MALE':
            'Male_AmericanIndianAndAlaskaNativeAlone',
        'IA_FEMALE':
            'Female_AmericanIndianAndAlaskaNativeAlone',
        'AA_MALE':
            'Male_AsianAlone',
        'AA_FEMALE':
            'Female_AsianAlone',
        'NA_MALE':
            'Male_NativeHawaiianAndOtherPacificIslanderAlone',
        'NA_FEMALE':
            'Female_NativeHawaiianAndOtherPacificIslanderAlone',
        'TOM_MALE':
            'Male_TwoOrMoreRaces',
        'TOM_FEMALE':
            'Female_TwoOrMoreRaces',
        'WAC_MALE':
            "Male_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces",
        'WAC_FEMALE':
            "Female_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces",
        'BAC_MALE':
            "Male_BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces",
        'BAC_FEMALE':
            "Female_BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces",
        'IAC_MALE':
            "Male_AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces",
        'IAC_FEMALE':
            "Female_AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces",
        'AAC_MALE':
            "Male_AsianAloneOrInCombinationWithOneOrMoreOtherRaces",
        'AAC_FEMALE':
            "Female_AsianAloneOrInCombinationWithOneOrMoreOtherRaces",
        'NAC_MALE':
            "Male_NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces",
        'NAC_FEMALE':
            "Female_NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces",
        'NHWAC_MALE':
            "Male_NotHispanicOrLatino_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces",
        'NHWAC_FEMALE':
            "Female_NotHispanicOrLatino_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces",
        'NHBAC_MALE':
            "Male_NotHispanicOrLatino_BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces",
        'NHBAC_FEMALE':
            "Female_NotHispanicOrLatino_BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces",
        'NHIAC_MALE':
            "Male_NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces",
        'NHIAC_FEMALE':
            "Female_NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces",
        'NHAAC_MALE':
            "Male_NotHispanicOrLatino_AsianAloneOrInCombinationWithOneOrMoreOtherRaces",
        'NHAAC_FEMALE':
            "Female_NotHispanicOrLatino_AsianAloneOrInCombinationWithOneOrMoreOtherRaces",
        'NHNAC_MALE':
            "Male_NotHispanicOrLatino_NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces",
        'NHNAC_FEMALE':
            "Female_NotHispanicOrLatino_NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces",
        'NHWAC_MALE':
            "Male_NotHispanicOrLatino_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces",
        'NHWAC_FEMALE':
            "Female_NotHispanicOrLatino_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces",
        'HBAC_MALE':
            "Male_HispanicOrLatino_BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces",
        'HBAC_FEMALE':
            "Female_HispanicOrLatino_BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces",
        'HIAC_MALE':
            "Male_HispanicOrLatino_AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces",
        'HIAC_FEMALE':
            "Female_HispanicOrLatino_AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces",
        'HAAC_MALE':
            "Male_HispanicOrLatino_AsianAloneOrInCombinationWithOneOrMoreOtherRaces",
        'HAAC_FEMALE':
            "Female_HispanicOrLatino_AsianAloneOrInCombinationWithOneOrMoreOtherRaces",
        'HNAC_MALE':
            "Male_HispanicOrLatino_NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces",
        'HNAC_FEMALE':
            "Female_HispanicOrLatino_NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces",
        'HWAC_MALE':
            "Male_HispanicOrLatino_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces",
        'HWAC_FEMALE':
            "Female_HispanicOrLatino_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces"
    }
    df = df.replace({"sv": _sexrace_dict})
    df['SVs'] = 'Count_Person_' + df['AGEGRP'] + '_' + df['sv']
    df = df.drop(columns=['AGEGRP', 'sv'])
    df['Measurement_Method'] = np.where(df['SVs'].str.contains('Agg')\
        , 'dcAggregate/CensusPEPSurvey', 'CensusPEPSurvey')
    df['SVs'] = df['SVs'].str.replace('Agg', '')

    # Write to final file.
    df.to_csv(
        os.path.join(os.path.dirname(
        os.path.abspath(__file__)), output_folder,'county_2020_2029.csv'),\
        index=False)
