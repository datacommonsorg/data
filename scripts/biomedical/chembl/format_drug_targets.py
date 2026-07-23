# Copyright 2023 Google LLC
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
Date: 01/31/2023
Name: format_drug_targets.py
Description: Add dcids for all the proteins and formats uniprot IDs and protein terminal structure types
@file_input: .tsv input file with chembl-uniprot mapping
@file_output: .csv output file with dcid column and other properly formatted columns
'''

import pandas as pd
import numpy as np
import sys

def check_for_illegal_charc(s):
    """Checks for illegal characters in a string and prints an error statement if any are present
    Args:
        s: target string that needs to be checked
    
    """
    list_illegal = ["'", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
    if any([x in s for x in list_illegal]):
        print('Error! dcid contains illegal characters!', s)

def format_cols(df):
	df.rename(columns={'UniProt Accessions': 'UniProtID', 'Type': 'TerminalStructure', 'Species Group Flag':'isSpeciesGroup'}, inplace=True)
	df = df.assign(UniProtID=df.UniProtID.str.split("|")).explode('UniProtID')
	df['dcid'] = 'bio/' + df['ChEMBL ID']
	return df

def format_str_cols(df):
	df['TerminalStructure'] = df['TerminalStructure'].apply(str.title)
	df['TerminalStructure'] = df['TerminalStructure'].replace(" ", "", regex=True)
	df['TerminalStructure'] = 'dcs:ProteinTerminalStructure' + df['TerminalStructure']
	df.update('"' +
			  df[['ChEMBL ID', 'Name', 'UniProtID', 'TerminalStructure', 'Organism']].astype(str) + '"')
	df.replace("\"nan\"", np.nan, inplace=True)
	return df

def format_numerical_cols(df):
	list_num_cols = ['Compounds', 'Activities', 'Tax ID']
	for i in list_num_cols:
		df[i] = df[i].astype(str).apply(lambda x: x.replace('.0',''))
		df[i] = df[i].replace('nan', np.nan)
	return df

def check_for_dcid(row):
	check_for_illegal_charc(str(row['dcid']))
	return row

def main():
	file_input = sys.argv[1]
	file_output = sys.argv[2]
	df = pd.read_csv(file_input, sep='\t')
	df = format_cols(df)
	df = format_str_cols(df)
	df = format_numerical_cols(df)
	df = df.apply(lambda x: check_for_dcid(x),axis=1)
	df.to_csv(file_output, doublequote=False, escapechar='\\')
	


if __name__ == '__main__':
	main()