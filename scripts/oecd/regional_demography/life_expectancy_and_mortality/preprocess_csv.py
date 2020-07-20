# Copyright 2020 Google LLC
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

import csv
import json
import pandas as pd


def multi_index_to_single_index(df):
    columns = []
    for column in df.columns:
        column = list(column)
        column[1] = str(column[1])
        columns.append(''.join(column))

    df.columns = columns
    return df.reset_index()


# Read csv from source csv
df = pd.read_csv('REGION_DEMOGR_life_expectancy_and_mortality.csv')
# First remove geos with names that we don't have mappings to dcid for.
name2dcid = dict(json.loads(open('../name2dcid.json').read()))
df = df[df['Region'].isin(name2dcid.keys())]
# Second, replace the names with dcids
df.replace({'Region': name2dcid}, inplace=True)


# process the source data
df = df[['REG_ID', 'Region', 'VAR', 'SEX', 'Year', 'Value']]
df_clear = df.drop(df[(df['VAR']=='INF_SEXDIF') | (df['VAR']=='LIFE_SEXDIF')].index)
df_clear['Year'] = '"' + df_clear['Year'].astype(str) + '"'

df_cleaned = df_clear.pivot_table(values='Value', index=['REG_ID', 'Region', 'Year'],
                    columns=['VAR', 'SEX'])
df_cleaned['DEATH_RA'] = df_cleaned['DEATH_RA'] / 1000
df_cleaned['INF_MORT'] = df_cleaned['INF_MORT'] / 1000
df_cleaned['STD_MORT'] = df_cleaned['STD_MORT'] / 1000
df_cleaned['YOU_DEATH_RA'] = df_cleaned['YOU_DEATH_RA'] / 1000
df_cleaned = multi_index_to_single_index(df_cleaned)

VAR_to_statsvars = {
    'DEATH_RAT': 'Count_MortalityEvent_Count_Person',
    'DEATH_RAM': 'Count_MortalityEvent_Male_Count_Person',
    'DEATH_RAF': 'Count_MortalityEvent_Female_Count_Person',

    'STD_MORTT': 'Count_MortalityEvent_Count_Person_AgeAdjusted',
    'STD_MORTM': 'Count_MortalityEvent_Male_Count_Person_AgeAdjusted',
    'STD_MORTF': 'Count_MortalityEvent_Female_Count_Person_AgeAdjusted',

    'YOU_DEATH_RAT': 'Count_MortalityEvent_15To64Years_Count_Person',
    'YOU_DEATH_RAM': 'Count_MortalityEvent_15To64Years_Male_Count_Person',
    'YOU_DEATH_RAF': 'Count_MortalityEvent_15To64Years_Female_Count_Person',

    'INF_MORTT': 'Count_MortalityEvent_LessThan1Year_Count_BirthEvent_LiveBirth',
    'INF_MORTM': 'Count_MortalityEvent_LessThan1Year_Male_Count_BirthEvent_LiveBirth',
    'INF_MORTF': 'Count_MortalityEvent_LessThan1Year_Female_Count_BirthEvent_LiveBirth',

    'LIFE_EXPT': 'LifeExpectancy_Person',
    'LIFE_EXPF': 'LifeExpectancy_Person_Female',
    'LIFE_EXPM': 'LifeExpectancy_Person_Male',
}

df_cleaned.rename(columns=VAR_to_statsvars, inplace=True)
df_cleaned.to_csv('OECD_life_expectancy_and_mortality_cleaned.csv', index=False, quoting=csv.QUOTE_NONE)

TEMPLATE_MCF_TEMPLATE = """
Node: E:OECD_life_expectancy_and_mortality_cleaned->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
measurementMethod: dcs:OECDRegionalStatistics
observationAbout: C:OECD_life_expectancy_and_mortality_cleaned->E0
observationDate: C:OECD_life_expectancy_and_mortality_cleaned->Year
observationPeriod: "P1Y"
value: C:OECD_life_expectancy_and_mortality_cleaned->{stat_var}
"""

stat_vars = df_cleaned.columns[3:]
with open('OECD_life_expectancy_and_mortality.tmcf', 'w', newline='') as f_out:
    for i in range(len(stat_vars)):
        f_out.write(TEMPLATE_MCF_TEMPLATE.format_map({'index': i + 1, 'stat_var': stat_vars[i]}))