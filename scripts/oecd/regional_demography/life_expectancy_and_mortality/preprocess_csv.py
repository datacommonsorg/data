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

import sys
sys.path.append('../')
from utils import multi_index_to_single_index, generate_geo_id
import csv
import json
import pandas as pd


# Read csv from source csv
df = pd.read_csv('REGION_DEMOGR_life_expectancy_and_mortality.csv')
df = df[['TL', 'REG_ID', 'Region', 'VAR', 'SEX', 'Year', 'Value']]
# First remove geos with names that we don't have mappings to dcid for.
name2dcid = dict(json.loads(open('../name2dcid.json').read()))
nuts = dict(json.loads(open('../region_nuts_codes.json').read()))
df = df[df['REG_ID'].isin(nuts.keys()) | df['Region'].isin(name2dcid.keys())]
# Second, replace the names with dcids
df['Region'] = df.apply(lambda row: generate_geo_id(row, nuts, name2dcid), axis=1)

# process the source data
df = df[['REG_ID', 'Region', 'VAR', 'SEX', 'Year', 'Value']]
df_clear = df.drop(df[(df['VAR']=='INF_SEXDIF') | (df['VAR']=='LIFE_SEXDIF')].index)
df_clear['Year'] = '"' + df_clear['Year'].astype(str) + '"'

df_cleaned = df_clear.pivot_table(values='Value',
                                  index=['REG_ID', 'Region', 'Year'],
                                  columns=['VAR', 'SEX'])
df_cleaned['DEATH_RA'] = df_cleaned['DEATH_RA'] / 1000
df_cleaned['INF_MORT'] = df_cleaned['INF_MORT'] / 1000
df_cleaned['STD_MORT'] = df_cleaned['STD_MORT'] / 1000
df_cleaned['YOU_DEATH_RA'] = df_cleaned['YOU_DEATH_RA'] / 1000
df_cleaned = multi_index_to_single_index(df_cleaned)

VAR_to_statsvars = {
    'DEATH_RAT':
        'Count_MortalityEvent_Count_Person',
    'DEATH_RAM':
        'Count_MortalityEvent_Male_Count_Person_Male',
    'DEATH_RAF':
        'Count_MortalityEvent_Female_Count_Person_Female',
    'STD_MORTT':
        'Count_MortalityEvent_Count_Person_AgeAdjusted',
    'STD_MORTM':
        'Count_MortalityEvent_Male_Count_Person_Male_AgeAdjusted',
    'STD_MORTF':
        'Count_MortalityEvent_Female_Count_Person_Female_AgeAdjusted',
    'YOU_DEATH_RAT':
        'Count_MortalityEvent_Upto14Years_Count_Person_Upto14Years',
    'YOU_DEATH_RAM':
        'Count_MortalityEvent_Upto14Years_Male_Count_Person_Upto14Years_Male',
    'YOU_DEATH_RAF':
        'Count_MortalityEvent_Upto14Years_Female_Count_Person_Upto14Years_Female',
    'INF_MORTT':
        'Count_MortalityEvent_LessThan1Year_Count_BirthEvent',
    'INF_MORTM':
        'Count_MortalityEvent_LessThan1Year_Male_Count_BirthEvent_Male',
    'INF_MORTF':
        'Count_MortalityEvent_LessThan1Year_Female_Count_BirthEvent_Female',
    'LIFE_EXPT':
        'LifeExpectancy_Person',
    'LIFE_EXPF':
        'LifeExpectancy_Person_Female',
    'LIFE_EXPM':
        'LifeExpectancy_Person_Male',
}

df_cleaned.rename(columns=VAR_to_statsvars, inplace=True)
df_cleaned.to_csv('OECD_life_expectancy_and_mortality_cleaned.csv',
                  index=False,
                  quoting=csv.QUOTE_NONE)

TEMPLATE_MCF_TEMPLATE = """
Node: E:OECD_life_expectancy_and_mortality_cleaned->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
measurementMethod: dcs:OECDRegionalStatistics
observationAbout: C:OECD_life_expectancy_and_mortality_cleaned->Region
observationDate: C:OECD_life_expectancy_and_mortality_cleaned->Year
observationPeriod: "P1Y"
value: C:OECD_life_expectancy_and_mortality_cleaned->{stat_var}
"""

TEMPLATE_MCF_TEMPLATE_YEAR = """
Node: E:OECD_life_expectancy_and_mortality_cleaned->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
measurementMethod: dcs:OECDRegionalStatistics
observationAbout: C:OECD_life_expectancy_and_mortality_cleaned->Region
observationDate: C:OECD_life_expectancy_and_mortality_cleaned->Year
observationPeriod: "P1Y"
value: C:OECD_life_expectancy_and_mortality_cleaned->{stat_var}
unit: dcs:Year
"""

stat_vars = df_cleaned.columns[3:]
with open('OECD_life_expectancy_and_mortality.tmcf', 'w', newline='') as f_out:
    for i in range(len(stat_vars)):
        if stat_vars[i].startswith("LifeExpectancy"):
            f_out.write(
                TEMPLATE_MCF_TEMPLATE_YEAR.format_map({
                    'index': i + 1,
                    'stat_var': stat_vars[i]
                }))
        else:
            f_out.write(
                TEMPLATE_MCF_TEMPLATE.format_map({
                    'index': i + 1,
                    'stat_var': stat_vars[i]
                }))
