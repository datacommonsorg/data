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
df = pd.read_csv('REGION_DEMOGR_death_tl3.csv')
df = df[['TL', 'REG_ID', 'Region', 'VAR', 'SEX', 'Year', 'Value']]
# First remove geos with names that we don't have mappings to dcid for.
regid2dcid = dict(json.loads(open('../regid2dcid.json').read()))
nuts = dict(json.loads(open('../region_nuts_codes.json').read()))
df = df[df['REG_ID'].isin(nuts.keys()) | df['REG_ID'].isin(regid2dcid.keys())]
# Second, replace the names with dcids
df['Region'] = df.apply(lambda row: generate_geo_id(row, nuts, regid2dcid),
                        axis=1)
df['Year'] = '"' + df['Year'].astype(str) + '"'

temp = df[['REG_ID', 'Region', 'VAR', 'SEX', 'Year', 'Value']]
temp_multi_index = temp.pivot_table(values='Value',
                                    index=['REG_ID', 'Region', 'Year'],
                                    columns=['VAR', 'SEX'])
df_cleaned = multi_index_to_single_index(temp_multi_index)

VAR_to_statsvars = {
    'D_TT': 'Count_MortalityEvent',
    'D_Y0_4T': 'Count_MortalityEvent_Upto4Years',
    'D_Y5_9T': 'Count_MortalityEvent_5To9Years',
    'D_Y10_14T': 'Count_MortalityEvent_10To14Years',
    'D_Y15_19T': 'Count_MortalityEvent_15To19Years',
    'D_Y20_24T': 'Count_MortalityEvent_20To24Years',
    'D_Y25_29T': 'Count_MortalityEvent_25To29Years',
    'D_Y30_34T': 'Count_MortalityEvent_30To34Years',
    'D_Y35_39T': 'Count_MortalityEvent_35To39Years',
    'D_Y40_44T': 'Count_MortalityEvent_40To44Years',
    'D_Y45_49T': 'Count_MortalityEvent_45To49Years',
    'D_Y50_54T': 'Count_MortalityEvent_50To54Years',
    'D_Y55_59T': 'Count_MortalityEvent_55To59Years',
    'D_Y60_64T': 'Count_MortalityEvent_60To64Years',
    'D_Y65_69T': 'Count_MortalityEvent_65To69Years',
    'D_Y70_74T': 'Count_MortalityEvent_70To74Years',
    'D_Y75_79T': 'Count_MortalityEvent_75To79Years',
    'D_Y80_MAXT': 'Count_MortalityEvent_80OrMoreYears',
    'D_Y0_14T': 'Count_MortalityEvent_Upto14Years',
    'D_Y15_64T': 'Count_MortalityEvent_15To64Years',
    'D_Y65_MAXT': 'Count_MortalityEvent_65OrMoreYears',
    'D_TM': 'Count_MortalityEvent_Male',
    'D_Y0_4M': 'Count_MortalityEvent_Upto4Years_Male',
    'D_Y5_9M': 'Count_MortalityEvent_5To9Years_Male',
    'D_Y10_14M': 'Count_MortalityEvent_10To14Years_Male',
    'D_Y15_19M': 'Count_MortalityEvent_15To19Years_Male',
    'D_Y20_24M': 'Count_MortalityEvent_20To24Years_Male',
    'D_Y25_29M': 'Count_MortalityEvent_25To29Years_Male',
    'D_Y30_34M': 'Count_MortalityEvent_30To34Years_Male',
    'D_Y35_39M': 'Count_MortalityEvent_35To39Years_Male',
    'D_Y40_44M': 'Count_MortalityEvent_40To44Years_Male',
    'D_Y45_49M': 'Count_MortalityEvent_45To49Years_Male',
    'D_Y50_54M': 'Count_MortalityEvent_50To54Years_Male',
    'D_Y55_59M': 'Count_MortalityEvent_55To59Years_Male',
    'D_Y60_64M': 'Count_MortalityEvent_60To64Years_Male',
    'D_Y65_69M': 'Count_MortalityEvent_65To69Years_Male',
    'D_Y70_74M': 'Count_MortalityEvent_70To74Years_Male',
    'D_Y75_79M': 'Count_MortalityEvent_75To79Years_Male',
    'D_Y80_MAXM': 'Count_MortalityEvent_80OrMoreYears_Male',
    'D_Y0_14M': 'Count_MortalityEvent_Upto14Years_Male',
    'D_Y15_64M': 'Count_MortalityEvent_15To64Years_Male',
    'D_Y65_MAXM': 'Count_MortalityEvent_65OrMoreYears_Male',
    'D_TF': 'Count_MortalityEvent_Female',
    'D_Y0_4F': 'Count_MortalityEvent_Upto4Years_Female',
    'D_Y5_9F': 'Count_MortalityEvent_5To9Years_Female',
    'D_Y10_14F': 'Count_MortalityEvent_10To14Years_Female',
    'D_Y15_19F': 'Count_MortalityEvent_15To19Years_Female',
    'D_Y20_24F': 'Count_MortalityEvent_20To24Years_Female',
    'D_Y25_29F': 'Count_MortalityEvent_25To29Years_Female',
    'D_Y30_34F': 'Count_MortalityEvent_30To34Years_Female',
    'D_Y35_39F': 'Count_MortalityEvent_35To39Years_Female',
    'D_Y40_44F': 'Count_MortalityEvent_40To44Years_Female',
    'D_Y45_49F': 'Count_MortalityEvent_45To49Years_Female',
    'D_Y50_54F': 'Count_MortalityEvent_50To54Years_Female',
    'D_Y55_59F': 'Count_MortalityEvent_55To59Years_Female',
    'D_Y60_64F': 'Count_MortalityEvent_60To64Years_Female',
    'D_Y65_69F': 'Count_MortalityEvent_65To69Years_Female',
    'D_Y70_74F': 'Count_MortalityEvent_70To74Years_Female',
    'D_Y75_79F': 'Count_MortalityEvent_75To79Years_Female',
    'D_Y80_MAXF': 'Count_MortalityEvent_80OrMoreYears_Female',
    'D_Y0_14F': 'Count_MortalityEvent_Upto14Years_Female',
    'D_Y15_64F': 'Count_MortalityEvent_15To64Years_Female',
    'D_Y65_MAXF': 'Count_MortalityEvent_65OrMoreYears_Female',
}

df_cleaned.rename(columns=VAR_to_statsvars, inplace=True)
df_cleaned.to_csv('OECD_deaths_cleaned.csv',
                  index=False,
                  quoting=csv.QUOTE_NONE)

# Automate Template MCF generation since there are many Statistical Variables.
TEMPLATE_MCF_TEMPLATE = """
Node: E:OECD_deaths_cleaned->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
measurementMethod: dcs:OECDRegionalStatistics
observationAbout: C:OECD_deaths_cleaned->Region
observationDate: C:OECD_deaths_cleaned->Year
observationPeriod: "P1Y"
value: C:OECD_deaths_cleaned->{stat_var}
"""

stat_vars = df_cleaned.columns[3:]
with open('OECD_deaths.tmcf', 'w', newline='') as f_out:
    for i in range(len(stat_vars)):
        f_out.write(
            TEMPLATE_MCF_TEMPLATE.format_map({
                'index': i + 1,
                'stat_var': stat_vars[i]
            }))
