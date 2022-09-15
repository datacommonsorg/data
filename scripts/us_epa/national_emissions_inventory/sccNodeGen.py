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

import pandas as pd
import numpy as np

_SCHEMA_TEMPLATE = ("Node: dcid:EPA_SCC/{pv1}\n"
                    "typeOf: dcs:EpaSccCodeEnum\n{pv2}"
                    "name: \"{pv3}\"\n"
)

def make_schema(df,level):
    df = df.drop_duplicates()
    df = df.rename(columns={df.columns[0]:"code", df.columns[1]:"name", df.columns[2]:"specialization"})
    final_schema = ''
    for ind in df.index:
        e1 = df['code'][ind]
        e3 = df['name'][ind]
        if df['specialization'][ind] == '':
            e2 = ''
        else:
            e2 = "specializationOf: dcid:" + df['specialization'][ind] + "\n"
        final_schema += _SCHEMA_TEMPLATE.format(
                pv1=e1, pv2=e2, pv3=e3) + "\n"
    with open("scripts/us_epa/national_emissions_inventory/output/scc"+level+".mcf", 'w+', encoding='utf-8') as f_out:
        f_out.write(final_schema.rstrip('\n'))


df = pd.read_excel("scripts/us_epa/national_emissions_inventory/scc_list/SCCDownload.xlsx")
# df = df.drop(df[df.status != 'Active'].index)
# df = df.drop(columns=['status'])
df['SCC'] = df['SCC'].astype(str)
df['SCC_L1'] = np.where(df['SCC'].str.len() == 8, df['SCC'].str[:1],df['SCC'].str[:2])
df['SCC_L2'] = np.where(df['SCC'].str.len() == 8, df['SCC'].str[:3],df['SCC'].str[:4])
df['SCC_L3'] = np.where(df['SCC'].str.len() == 8, df['SCC'].str[:6],df['SCC'].str[:7])
# Remove if specialization needed at L1
df['data category'] = ''
#
df_temp = df[['SCC_L1','scc level one','data category']]
make_schema(df_temp,"L1")
df['SCC_L1'] = 'EPA_SCC/' + df['SCC_L1']
df_temp = df[['SCC_L2','scc level two','SCC_L1']]
make_schema(df_temp,"L2")
df['SCC_L2'] = 'EPA_SCC/' + df['SCC_L2']
df_temp = df[['SCC_L3','scc level three','SCC_L2']]
make_schema(df_temp,"L3")
df['SCC_L3'] = 'EPA_SCC/' + df['SCC_L3']
df_temp = df[['SCC','scc level four','SCC_L3']]
make_schema(df_temp,"L4")
