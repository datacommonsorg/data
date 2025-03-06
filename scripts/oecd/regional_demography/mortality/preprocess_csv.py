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
from utils import multi_index_to_single_index
import csv
import json
import pandas as pd
from columns import *

sys.path.append('../../')
from download import download_data_to_file_and_df
# Read csv from source csv
url = "https://sdmx.oecd.org/public/rest/data/OECD.CFE.EDS,DSD_REG_DEMO@DF_LIFE_EXP,2.0/all?dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
filename = "REGION_DEMOGR_life_expectancy.csv"

df = download_data_to_file_and_df(url, filename)
# df = pd.read_csv('REGION_DEMOGR_life_expectancy.csv',
#                  low_memory=False)
# Renaming new column names back to old column names for process
column_rename = {
    'TERRITORIAL_LEVEL': 'TL',
    'REF_AREA': 'REG_ID',
    'Reference area': 'Region',
    'MEASURE': 'VAR',
    'TIME_PERIOD': 'Year',
    'OBS_VALUE': 'Value'
}
df = df.rename(columns=column_rename)
df = df[['TL', 'REG_ID', 'Region', 'VAR', 'SEX', 'Year', 'Value']]
# First remove geos with names that we don't have mappings to dcid for.
regid2dcid = dict(json.loads(open('../regid2dcid.json').read()))
df = df[df['REG_ID'].isin(regid2dcid.keys())]
# Second, replace the names with dcids
df['Region'] = df.apply(lambda row: regid2dcid[row['REG_ID']], axis=1)

# process the source data
df = df[['REG_ID', 'Region', 'VAR', 'SEX', 'Year', 'Value']]
df_clear = df.drop(df[(df['VAR'] == 'INF_SEXDIF') |
                      (df['VAR'] == 'LIFE_SEXDIF')].index)
df_clear['Year'] = '"' + df_clear['Year'].astype(str) + '"'

df_cleaned = df_clear.pivot_table(values='Value',
                                  index=['REG_ID', 'Region', 'Year'],
                                  columns=['VAR', 'SEX'])
# df_cleaned['DEATH_RA'] = df_cleaned['DEATH_RA'] / 1000
# df_cleaned['INF_MORT'] = df_cleaned['INF_MORT'] / 1000
# df_cleaned['STD_MORT'] = df_cleaned['STD_MORT'] / 1000
# df_cleaned['YOU_DEATH_RA'] = df_cleaned['YOU_DEATH_RA'] / 1000
df_cleaned = multi_index_to_single_index(df_cleaned)

df_cleaned.rename(columns=VAR_to_statsvars, inplace=True)
df_cleaned_reset = df_cleaned.reindex(columns=reindex_column)
# df_cleaned.drop(columns=["REG_ID"], inplace=True)

df_cleaned_reset.to_csv('OECD_mortality_cleaned.csv',
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
