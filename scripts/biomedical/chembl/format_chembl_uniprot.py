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
Date: 01/01/2021
Name: format_chembl_uniprot.py
Description: Add dcids for all the proteins and format uniprot IDs and protein type
@file_input: .txt input file with chembl-uniprot mapping
@file_output: csv output file with dcid column and other properly formatted columns
'''

import sys
import pandas as pd
import numpy as np
import re
import csv

DICT_PROTEIN_TYPE = {'SINGLE PROTEIN':'dcs:ProteinTargetTypeSingleProtein', 
 'PROTEIN FAMILY':'dcs:ProteinTargetTypeProteinFamily', 
 'PROTEIN-PROTEIN INTERACTION':'dcs:ProteinTargetTypeProteinProteinInteraction',
 'PROTEIN COMPLEX':'dcs:ProteinTargetTypeProteinComplex',
 'PROTEIN COMPLEX GROUP':'dcs:ProteinTargetTypeProteinComplexGroup',
 'NUCLEIC-ACID':'dcs:ProteinTargetTypeNucleicAcid',
 'SELECTIVITY GROUP':'dcs:ProteinTargetTypeSelectivityGroup',
 'CHIMERIC PROTEIN':'dcs:ProteinTargetTypeChimericProtein',
 'PROTEIN NUCLEIC-ACID COMPLEX':'dcs:ProteinTargetTypeProteinNucleicAcidComplex'}

def format_names(df):
    """
    Format the name column of the input dataframe
    Args:
        df = chembl-uniprot data
    Returns:
        chembl-uniprot dataframe with formatted name column
    """
    df.columns = ['uniprotID', 'ChemBL', 'Name', 'Protein_Type']
    df['Name'] = df['Name'].apply(lambda x: x.replace('[', '').replace(']', ''))
    df['Name'] = df['Name'].apply(lambda x: x.replace('(', '').replace(')', ''))
    df['Name'] = df['Name'].str.replace(',', '')
    df['Name'] = df['Name'].str.replace(' ', '_')
    df['Name'] = df['Name'].str.lower()
    return df


def format_cols(df):
    """
    Format the columns of the input dataframe
    Args:
        df = chembl-uniprot data
    Returns:
        chembl-uniprot dataframe with formatted columns
    """
    df['dcid'] = "bio/" + df['ChemBL'].astype(str)
    df['Protein_Type'] = df['Protein_Type'].map(DICT_PROTEIN_TYPE)
    col_names = ['Name', 'Protein_Type', 'uniprotID', 'ChemBL']
    for col in col_names:
        df[col] = df[col].str.replace('"', "")
        df.update('"' + df[[col]].astype(str) + '"')
        df[col] = df[col].replace(["\"nan\""],np.nan)
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
    df = pd.read_csv(file_input, sep='\t', header=None)
    df = format_names(df)
    df = format_cols(df)
    df = df.apply(lambda x: check_for_dcid(x),axis=1)
    df.to_csv(file_output, doublequote=False, escapechar='\\')


if __name__ == '__main__':
    main()
