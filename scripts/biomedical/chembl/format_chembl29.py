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
Author: Suhana Bedi
Date: 01/01/2022
Name: format_chembl29.py
Description: Add dcids for all the proteins and format the corresponding canonical_smiles and InchiKey IDs.
@file_input: input .txt from chembl database
@file_output: csv output file with dcid column and other properly formatted columns
'''

import sys
import csv
import pandas as pd
import numpy as np
import datacommons as dc
import math

def fetch_dcid(df):
    chunk_size = 450
    df_split = np.array_split(df, math.ceil(len(df) / chunk_size))
    df_query_results = pd.DataFrame(columns =['?dcid','?chembl'])
    for i in range(len(df_split)):
        arr_name = np.array((df_split[i])['chembl_id'])
        query_str = """
        SELECT DISTINCT ?dcid ?chembl
        WHERE {{
        ?a typeOf Drug .
        ?a dcid ?dcid .
        ?a chemblID {value} .
        ?a chemblID ?chembl .
        }}
        """.format(value=arr_name)
        result = dc.query(query_str)
        result = pd.DataFrame(result)
        df_query_results = pd.concat([df_query_results,result])
    df_query_results = df_query_results.reset_index(drop=True)
    df_cd = pd.merge(df, df_query_results, how='left', left_on = 'chembl_id', right_on = '?chembl')
    df_cd = df_cd.assign(dcid=np.where(df_cd['?dcid'].notnull(), df_cd['?dcid'], "chem/" + df_cd['chembl_id']))
    return df_cd

def format_col(df):
    """
    Format the columns of the input dataframe
    Args:
        df = chembl data
    Returns:
        chembl dataframe with formatted columns and added dcids
    """
    col_names = ['canonical_smiles', 'standard_inchi', 'standard_inchi_key']
    for col in col_names:
        df[col] = df[col].str.replace('"', "")
        df.update('"' + df[[col]].astype(str) + '"')
        df[col] = df[col].replace(["\"nan\""],np.nan)
    df = df.replace(r'\\n',"P", regex=True)
    return df

def check_for_illegal_charc(s):
    """Checks for illegal characters in a string and prints an error statement if any are present
    Args:
        s: target string that needs to be checked
    
    """
    list_illegal = ["'", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
    if any([x in s for x in list_illegal]):
        print('Error! dcid contains illegal characters!', s)

def check_for_dcid(row):
    check_for_illegal_charc(str(row['dcid']))
    return row


def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    df = pd.read_csv(file_input, sep='\t')
    df = fetch_dcid(df)
    df = format_col(df)
    df = df.apply(lambda x: check_for_dcid(x),axis=1)
    df.to_csv(file_output, doublequote=False, escapechar='\\')


if __name__ == '__main__':
    main()
