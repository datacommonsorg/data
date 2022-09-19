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
    compound_list = x['Name']
    for element in compound_list:
        if element.startswith("CHEMBL"):
            x['Chembl'] = element
            compound_list.remove(element)
        elif element.startswith("SCHEMBL"):
            x['SChembl'] = element
            compound_list.remove(element)
        elif element.startswith("CHEBI"):
            x['Chebi'] = element
            compound_list.remove(element)
    return x

def split_synonyms(df):
    df.columns = ['Id', 'Name']
    df = df.groupby(["Id"])['Name'].apply(list)
    df = df.to_frame()
    df = df.apply(extract_compound_id,axis=1)
    return df

def format_columns(df):
    df['Name'] = [[f'"{j}"' for j in i] for i in df['Name']]
    df['Name'] =  df['Name'].apply(lambda x: x.replace('[','').replace(']','')) 
    df['Id'] = "chem/CID" + df['Id'].astype(str)
    return df

def main():
    file_input = sys.argv[1]
    df = pd.read_csv(file_input, sep = '\t', header=None)
    df = split_synonyms(df)
    df = format_columns(df)
    df.to_csv('Synonym-mapping.csv', doublequote=False, escapechar='\\')
    
    
if __name__ == '__main__':
    main()