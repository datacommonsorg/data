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
Name: format_chemblBio_fasta.py
Description: Add dcids for all the proteins and format the fasta into a csv.
@file_input: input .fasta from chembl database
@file_output: csv output file with dcid column and other properly formatted columns
'''
import sys
import pandas as pd
import re
import csv
from Bio.SeqIO.FastaIO import SimpleFastaParser


def fasta_to_df(input_file):
    """
    Converts the fasta file to a dataframe
    Args:
        input file = input .fa file
    Returns:
        chembl dataframe with .fa file information
    """
    with open(input_file) as fasta_file:
        identifiers = []
        lengths = []
        for title, sequence in SimpleFastaParser(fasta_file):
            identifiers.append(title.split('None')[0])
            lengths.append(sequence)
    df = pd.DataFrame()
    df['Sequence'] = lengths
    df['Identifier'] = identifiers
    return df


def format_identifier(df):
    """
    Formats the identifier column of the input dataframe
    Args:
        df = input dataframe
    Returns:
        df with added chembl, uniprot and name columns 
    """
    list_chembl = []
    list_name = []
    for i in df.index:
        total_str = df['Identifier'][i]
        mod_str = re.sub(r"\([^()]*\)", "", total_str)
        mod_str_1 = mod_str.split(']')[0]
        mod_str_2 = mod_str.split(']')[1]
        list_chembl.append(mod_str_1.split(' ')[1])
        list_name.append(mod_str_2)
    df['chembl'] = list_chembl
    df['name'] = list_name
    return df


def format_cols(df):
    """
    Formats the columns of the input dataframe
    Args:
        df = input dataframe
    Returns:
        df with added dcid and formatted name column
    """
    df['dcid'] = "bio/" + df['chembl']
    df['name'] = df['name'].str.replace("(", "")
    df['name'] = df['name'].str.strip()
    df['name'] = df['name'].str.lower()
    df['name'] = df['name'].str.replace(",", "")
    df['name'] = df['name'].str.replace(" ", "_")
    df['name'] = df['name'].str.replace("[", "")
    df = df.drop(columns=['Identifier'])
    return df


def multiple_dcid(df):
    """
    Adds new row to entries with multiple dcids
    Args:
        df = input dataframe
    Returns:
        df with added rows
    """
    for i in df.index:
        if "," in df['chembl'][i]:
            old_str = df['chembl'][i]
            old_chembl = old_str.split(',')[0]
            new_chembl = old_str.split(',')[1]
            old_chembl = old_chembl.replace(",", "")
            new_chembl = new_chembl.replace(",", "")
            df['chembl'][i] = old_chembl
            df['dcid'][i] = "bio/" + old_chembl
            new_dcid = "bio/" + new_chembl
            df = df.append(
                {
                    'Sequence': df['Sequence'][i],
                    'chembl': new_chembl,
                    'uniprot': df['uniprot'][i],
                    'name': df['name'][i],
                    'dcid': new_dcid
                },
                ignore_index=True)
    return df


def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    df = fasta_to_df(file_input)
    df = format_identifier(df)
    df = format_cols(df)
    df.to_csv(
        file_output,
        index=None,
    )


if __name__ == '__main__':
    main()
