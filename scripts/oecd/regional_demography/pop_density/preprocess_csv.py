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


df = pd.read_csv('REGION_DEMOGR_pop_density.csv')
# First remove geos with names that we don't have mappings to dcid for.
name2dcid = dict(json.loads(open('../name2dcid.json').read()))
df = df[df['Region'].isin(name2dcid.keys())]
# Second, replace the names with dcids
df.replace({'Region': name2dcid}, inplace=True)

df['Year'] = '"' + df['Year'].astype(str) + '"'
temp = df[['REG_ID', 'Region', 'VAR', 'Year', 'Value']]
temp_multi_index = temp.pivot_table(values='Value', index=['REG_ID', 'Region', 'Year'],
                                    columns=['VAR'])
df_cleaned = multi_index_to_single_index(temp_multi_index)[['REG_ID', 'Region', 'Year', 'POP_DEN', 'SURF']]

VAR_to_statsvars = {
    'POP_DEN': 'Count_Person_PerArea',
    'SURF': 'Area',
}

df_cleaned.rename(columns=VAR_to_statsvars, inplace=True)
df_cleaned.to_csv('OECD_pop_density_cleaned.csv', index=False, quoting=csv.QUOTE_NONE)
