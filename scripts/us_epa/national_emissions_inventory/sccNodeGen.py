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
import os

_SCHEMA_TEMPLATE = ("Node: dcid:EPA_SCC/{pv1}\n"
                    "typeOf: dcs:EpaSccCodeEnum\n{pv2}"
                    "name: \"{pv3}\"\n"
)

def make_schema(df,level):
    """
    Generates MCF file for the schema of SCCs according 
    to the DF provided.

    Args:
        df (pd.DataFrame): df as the input, to generate SCC schema.
        level (str): A string indicating what level of SCCs are provided.
    Returns:
        None
    """
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
    output_file_name = "scc" + level + ".mcf"
    output_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),"output",output_file_name)
    with open(output_file_path, 'w+', encoding='utf-8') as f_out:
        f_out.write(final_schema.rstrip('\n'))

if __name__ == "__main__":
    input_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),"scc_list")
    input_file_name = "SCCDownload.xlsx"

    df = pd.read_excel(os.path.join(input_file_path,input_file_name))

    # Seperate SCC Levels based on Length of String
    # Length = 8 :  L1 - 1 digit
    #               L2 - L1 + 2 digits
    #               L3 - L2 + 3 digits
    #               L4 - L3 + 2 digits
    # Length = 10 : L1 - 2 digits
    #               L2 - L1 + 2 digits
    #               L3 - L2 + 3 digits
    #               L4 - L3 + 3 digits
    df['SCC'] = df['SCC'].astype(str)
    df['SCC_L1'] = np.where(df['SCC'].str.len() == 8, df['SCC'].str[:1],df['SCC'].str[:2])
    df['SCC_L2'] = np.where(df['SCC'].str.len() == 8, df['SCC'].str[:3],df['SCC'].str[:4])
    df['SCC_L3'] = np.where(df['SCC'].str.len() == 8, df['SCC'].str[:6],df['SCC'].str[:7])

    # Remove if specialization needed at L1
    df['data category'] = ''
    #
    # Calls to the above Function for different Levels of Schema
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
