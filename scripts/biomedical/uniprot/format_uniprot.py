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
"""
Author: Suhana Bedi
Date: 08/22/2023
Name: format_uniprot
Description: converts a .fasta from UniprotKB into a clean csv format, 
where each columns contains protein sequences, ids, gene ids, and
organisms names
@file_input: input .fasta from Uniprot
@file_output: formatted .csv with Uniprot annotations
"""

import sys
import pandas as pd
import numpy as np
import re
import csv
from Bio.SeqIO.FastaIO import SimpleFastaParser

DICT_PROTEIN_EXISTENCE = {
	'1':'ProteinExistenceEvidenceExperimentalEvidenceAtProteinLevel',
	'2':'ProteinExistenceEvidenceExperimentalEvidenceAtTranscriptLevel',
	'3':'ProteinExistenceEvidenceProteinInferredFromHomology',
	'4':'ProteinExistenceEvidenceProteinPredicted',
	'5':'ProteinExistenceEvidenceProteinUncertain'
}

def check_for_illegal_charc(s):
	"""Checks for illegal characters in a string and prints an error statement if any are present
	Args:
		s: target string that needs to be checked
	
	"""
	list_illegal = ["'", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
	if any([x in s for x in list_illegal]):
		print('Error! dcid contains illegal characters!', s)

def check_for_dcid(row):
	check_for_illegal_charc(str(row['EntryName']))
	return row 

def fasta_to_df(input_file):
	"""
	Converts the fasta file into a pandas dataframe
	Args:
		input_file = input fasta file
	Returns:
		df = output pandas dataframe
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

def format_protein_existence_enum(df):
	"""
	Formats the enumeration column for a dataframe
	Args:
		df = unformatted dataframe
	Returns:
		df = formatted dataframe with enums 
	"""
	df['ProteinExistence'] = df['Identifier'].str.split('PE=').str[1] 
	df['ProteinExistence'] = df['ProteinExistence'].str.split('SV=').str[0] 
	df['ProteinExistence'] = df['ProteinExistence'].str.strip()
	df['ProteinExistence'] = df['ProteinExistence'].map(DICT_PROTEIN_EXISTENCE)
	return df

def format_organism_cols(df):
	"""
	Formats the organism columns for a dataframe
	Args:
		df = unformatted dataframe
	Returns:
		df = formatted dataframe with organism columns
	"""
	df['OrganismName'] = df['Identifier'].str.split('OS=').str[1] 
	df['OrganismIdentifier'] = df['OrganismName'].str.split('OX=').str[1] 
	df['OrganismIdentifier'] = df['OrganismIdentifier'].str.split('GN=').str[0] 
	df['OrganismName'] = df['OrganismName'].str.split('OX=').str[0] 
	return df 

def format_identifier_cols(df):
	"""
	Formats the identifier columns for a dataframe
	Args:
		df = unformatted dataframe
	Returns:
		df = formatted dataframe with identifier columns
	"""
	df['uniprotID'] = df['Identifier'].str.split('|').str[1]
	df['Identifier'] = df['Identifier'].str.split('|').str[2]
	df['EntryName'] = df['Identifier'].str.split(' ').str[0]
	df['ProteinName'] = df['Identifier'].str.split('OS=').str[0] 
	df['ProteinName'] = df['ProteinName'].str.partition(' ')[2]
	return df 

def format_gene_cols(df):
	"""
	Formats the gene columns for a dataframe
	Args:
		df = unformatted dataframe
	Returns:
		df = formatted dataframe with gene columns
	"""
	df['GeneName'] = df['Identifier'].str.split('GN=').str[1] 
	df['GeneName'] = df['GeneName'].str.split('PE=').str[0]
	df.replace({'\'': ''}, regex=True, inplace=True)
	df['GeneDcid'] = df['GeneName']
	df['GeneDcid'] = df['GeneDcid'].str.replace(":", '_')
	df["GeneDcid"] = df["GeneDcid"].str.replace("[^a-zA-Z0-9\\s._]", "", regex=True)
	df['GeneDcid'] = df['GeneDcid'].replace(r'[()]',"", regex=True)
	df['GeneDcid'] = df['GeneDcid'].replace(r"[\[\]]","", regex=True)
	df['GeneDcid'] = 'bio/' + df['GeneDcid']
	return df 

def format_dcid(df):
	"""
	Formats the dcid for a dataframe
	Args:
		df = unformatted dataframe
	Returns:
		df = formatted dataframe with dcid
	"""
	df = df.apply(lambda x: check_for_dcid(x),axis=1)
	df['dcid'] = 'bio/'  + df['EntryName'].astype(str)
	return df 

def format_columns(df):
	"""
	Formats the columns for a dataframe
	Args:
		df = unformatted dataframe
	Returns:
		df = dataframe with formatted columns
	"""
	df = format_identifier_cols(df)
	df = format_organism_cols(df)
	df = format_protein_existence_enum(df)
	df = format_gene_cols(df)
	df = format_dcid(df)
	df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
	df.update('"' +
			  df[['Sequence', 'ProteinName', 'OrganismName', 'GeneName', 'dcid', 'GeneDcid']].astype(str) + '"')
	df.replace("\"nan\"", np.nan, inplace=True)
	return df


def main():
	file_input = sys.argv[1]
	file_output = sys.argv[2]
	df = fasta_to_df(file_input)
	df = format_columns(df)
	df.to_csv(file_output, doublequote=False, escapechar='\\')


if __name__ == '__main__':
	main()
