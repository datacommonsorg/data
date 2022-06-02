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
This Python Script is
for County Level Data
2000-2010.
'''

import os
import pandas as pd
import numpy as np


def county2000():
    """
    This Python Script Loads csv datasets
    from 2000-2010 on a County Level,
    cleans it and create a cleaned csv.
    """
    # Used to collect data after every loop for every file's df.
    final_df = pd.DataFrame()
    for i in range(1, 57):
        if i not in [3, 7, 14, 43, 52]:
            j = f'{i:02}'
            url = 'https://www2.census.gov/programs-surveys/popest/datasets/2'+\
                '000-2010/intercensal/county/co-est00int-alldata-'+str(j)+'.csv'
            df = pd.read_csv(url, encoding='ISO-8859-1')
            # Filter years 1 - 12.
            df['Year'] = df['YEAR']
            df.drop(columns=['YEAR'], inplace=True)
            df = df.query("Year not in [1,12,13]")
            # Filter by agegrp = 99.
            df = df.query("AGEGRP != 99")
            df['Year'] = df['Year'].astype(str)
            # Replacing the numbers with more understandable metadata headings.
            _dict = {
                '2': '2000',
                '3': '2001',
                '4': '2002',
                '5': '2003',
                '6': '2004',
                '7': '2005',
                '8': '2006',
                '9': '2007',
                '10': '2008',
                '11': '2009'
            }
            df = df.replace({'Year': _dict})
            df.insert(6, 'geo_ID', 'geoId/', True)
            df['geo_ID'] = 'geoId/' + (df['STATE'].map(str)).str.zfill(2) + \
                (df['COUNTY'].map(str)).str.zfill(3)
            df['AGEGRP'] = df['AGEGRP'].astype(str)
            # Replacing the numbers with more understandable metadata headings.
            _dict = {
                '0': '0Years',
                '1': '1To4Years',
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
            df = df.replace({"AGEGRP": _dict})

            # Drop unwanted columns.
            df.drop(columns=['SUMLEV', 'STATE', 'COUNTY', 'STNAME', 'CTYNAME'],\
                inplace=True)
            df = df.drop(columns=[
                'TOT_POP', 'NH_MALE', 'NH_FEMALE', 'NHWA_MALE', 'NHWA_FEMALE',
                'NHBA_MALE', 'NHBA_FEMALE', 'NHIA_MALE', 'NHIA_FEMALE',
                'NHAA_MALE', 'NHAA_FEMALE', 'NHNA_MALE', 'NHNA_FEMALE',
                'NHTOM_MALE', 'NHTOM_FEMALE', 'H_MALE', 'H_FEMALE', 'HWA_MALE',
                'HWA_FEMALE', 'HBA_MALE', 'HBA_FEMALE', 'HIA_MALE',
                'HIA_FEMALE', 'HAA_MALE', 'HAA_FEMALE', 'HNA_MALE',
                'HNA_FEMALE', 'HTOM_MALE', 'HTOM_FEMALE'
            ])
            df['WhiteAloneAgg'] = df['WA_MALE'].astype(int)+\
                df['WA_FEMALE'].astype(int)
            df['BlackOrAfricanAmericanAlone'] = df['BA_MALE'].astype(int)+\
                df['BA_FEMALE'].astype(int)
            df['AmericanIndianAndAlaskaNativeAlone'] = df['IA_MALE']\
                .astype(int)+df['IA_FEMALE'].astype(int)
            df['AsianAloneAgg'] = df['AA_MALE'].astype(int)+\
                df['AA_FEMALE'].astype(int)
            df['NativeHawaiianAndOtherPacificIslanderAloneAgg'] = \
                df['NA_MALE'].astype(int)+df['NA_FEMALE'].astype(int)
            df['TwoOrMoreRacesAgg'] = df['TOM_MALE'].astype(int)+\
                df['TOM_FEMALE'].astype(int)
            df = df.melt(id_vars=['Year','geo_ID' ,'AGEGRP'], var_name='sv' , \
                value_name='observation')
            # Changing Names to be more understandable.
            _dict = {
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
                    'Female_TwoOrMoreRaces'
            }
            df = df.replace({"sv": _dict})
            df['SVs'] = 'Count_Person_' + df['AGEGRP'] + '_' + df['sv']
            df = df.drop(columns=['AGEGRP', 'sv'])
            df['Measurement_Method'] = np.where(df['SVs'].str.contains('Agg')\
            , 'dcAggregate/CensusPEPSurvey', 'CensusPEPSurvey')
            df['SVs'] = df['SVs'].str.replace('Agg', '')
            final_df = pd.concat([final_df, df])

    # Write to final file.
    final_df.to_csv(os.path.dirname(
    os.path.abspath(__file__)) + os.sep +'input_data/county_2000_2010.csv', \
        index=False)
