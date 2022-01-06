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
    df['Protein_Type'] = df['Protein_Type'].str.replace(' ', '_')
    df['Protein_Type'] = df['Protein_Type'].str.lower()
    return df


def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    df = pd.read_csv(file_input, sep='\t', header=None)
    df = format_names(df)
    df = format_cols(df)
    df.to_csv(file_output,
              index=None,
              quoting=csv.QUOTE_NONE,
              quotechar="",
              escapechar="\\")


if __name__ == '__main__':
    main()
