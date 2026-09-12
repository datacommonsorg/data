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
Date: 09/30/2022
Name: format_chembl_pubchem_mapping.py
Description: maps puchem compound IDs to chembl, chebi, schembl and other synonyms for the compound of interest.
Run: python3 format_chembl_pubchem_mapping.py CID-Synonym-filtered.csv
'''
import sys
import pandas as pd

def extract_compound_id(x):
    """
    Extracts the chembl, chebi and schembl IDs from synonyms
    Args:
        x = dataframe with synonyms
    Returns:
        dataframe with chembl, chebi and schembl separated out
    """
    compound_list = x['Name']
    for element in compound_list:
        if element.startswith("\"CHEMBL"):
            x['Chembl'] = element
            compound_list.remove(element)
        elif element.startswith("\"SCHEMBL"):
            x['SChembl'] = element
            compound_list.remove(element)
        elif element.startswith("\"CHEBI"):
            x['Chebi'] = element
            compound_list.remove(element)
    return x

def split_synonyms(df):
    """
    splits the chembl, chebi and schembl IDs and groups synonyms
    Args:
        x = dataframe with synonyms
    Returns:
        dataframe with split columns
    """
    df.columns = ['Id', 'Name']
    df['Name'] = '"' + df['Name'].astype(str) + '"'
    df = df.groupby(["Id"])['Name'].apply(list)
    print("Groupby done!")
    df = df.to_frame()
    df = df.apply(extract_compound_id,axis=1)
    print("Compound ID extracted!")
    return df

def main():
    file_input = sys.argv[1]
    df = pd.read_csv(file_input, sep = '\t', header=None, chunksize = 10000)
    count = 0
    df_final = pd.DataFrame()
    for data in df:
        if (count == 1):
            df_data.loc[17597, 'Name'] = df_data.loc[17597, 'Name'].replace('"', '')
        df_data = split_synonyms(data)
        df_data['Name'] = df_data['Name'].apply(', '.join)
        df_data['Id'] = df_data.index
        df_data['Id'] = "chem/CID" + df_data['Id'].astype(str)
        df_final = pd.concat([df_final, df_data])
        count = count + 1
    df_final.to_csv('Synonym-mapping-1.csv')
    #df_final.to_csv('Synonym-mapping-1.csv', doublequote=False, escapechar='\\')

    
if __name__ == '__main__':
    main()