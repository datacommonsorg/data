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
Date: 02/15/2022
Name: format_genes
Description: converts a .tsv from PharmGKB into a clean csv format, 
where each columns contains linkages or references to only 
database only for the purpose of clarity and understanding
@file_input: input .tsv from PharmGKB
@file_output: formatted .csv with PharmGKB and other database annotations
"""
import pandas as pd
import numpy as np
import re
import sys

def replace_nan_func(x):
	"""
	Combines all NaN rows with same ID 
	Args:
		df = dataframe to change
	Returns:
		none
	"""
	x = x[~pd.isna(x)]
	if len(x) > 0:
		return x.iloc[0]
	else:
		return np.NaN

def format_cols(df):
	"""
	Formats the columns in a dataframe
	and inserts/deletes specific 
	characters
	Args:
		df = dataframe to change
	Returns:
		df = formatted dataframe
	"""
	df = df.replace('"', '', regex=True)
	df = df.rename(columns={'PharmGKB Accession Id':'pharmGKBID', 'NCBI Gene ID':'ncbiGeneID', 'HGNC ID':'hgncID', 'Ensembl Id':'ensemblID', 'Alternate Names':'synonyms', 'Cross-references':'crossReferences' })
	df['crossReferences'] = df['crossReferences'].str.replace('"','')
	df['hgncID'] = df['hgncID'].str.split(":", 1).str[1]
	df = df.assign(crossReferences=df.crossReferences.str.split(",")).explode('crossReferences')
	df[['A', 'B']] = df['crossReferences'].str.split(':', 1, expand=True)
	df= df.replace(r'[^0-9a-zA-Z ]', '', regex=True).replace("'", '')
	df['dcid'] = "bio/" + df['Symbol']
	return df

def fetch_annotations(df):
	"""
	Fetches the annotations of
	genes from other databases
	Args:
		df = dataframe to change
	Returns:
		df = formatted dataframe
	"""
	df['A'] = df['A'].astype(str).map(lambda x: re.sub('[^A-Za-z0-9]+', '', x))
	col_add = list(df['A'].unique())
	for newcol in col_add:
		df[newcol] = np.nan
		df[newcol] = np.where(df['A'] == newcol, df['B'], np.nan)
		df[newcol] = df[newcol].astype(str).replace("nan", np.nan)
	df = df.groupby(by='pharmGKBID').agg(dict.fromkeys(df.columns[0:], replace_nan_func))
	df = df.drop(['A', 'B', 'HGNC', 'Ensembl', 'URL'], axis =1)
	return df

def format_genome_assembly(df):
	"""
	Formats the columns with genome
	assemblies
	Args:
		df = dataframe to change
	Returns:
		df = formatted dataframe
	"""
	list_cols = ['37', '38']
	for i in list_cols:
		df['GenomeAssembly' + i] = 'GRCh' + i
		df['genomeCoordName' + i] = 'GRCh' + i + "_" + df['Symbol'] + '_coordinates'
		df['genomeCoordDcid' + i] = "bio/" + df['genomeCoordName' + i]
	return df

def format_boolean_cols(df):
	"""
	Formats boolean columns replacing
	true and false values with the 
	words True and False respectively
	Args:
		df = dataframe to format
	Returns:
		df = formatted dataframe
	"""
	list_bool_cols = ['Is VIP', 'Has Variant Annotation', 'Has CPIC Dosing Guideline']
	for i in list_bool_cols:
		df[i] = np.where(df[i] == "Yes", "True", "False")
	return df 

def wrapper_fun(df):
	"""
	Runs the intermediate functions to 
	format the dataset
	Args:
		df = unformatted dataframe
	Returns:
		df = formatted dataframe
	"""
	df = format_cols(df)
	df = fetch_annotations(df)
	df = format_genome_assembly(df)
	df = format_boolean_cols(df)
	#cols = [col for col in df.columns if col not in ['dcid', 'genomeCoordDcid38', 'genomeCoordDcid37']]
	#df[cols] = df[cols].replace(r'[^0-9a-zA-Z ]', '', regex=True).replace("'", '')
	df.update('"' +
			  df[['Name', 'Symbol', 'synonyms', 'Alternate Symbols', 'dcid', 'genomeCoordDcid38', 'genomeCoordDcid37']].astype(str) + '"')
	df.replace("\"nan\"", np.nan, inplace=True)
	df = df.drop('pharmGKBID', axis=1)
	return df
		

def main():
	file_input = sys.argv[1]
	file_output = sys.argv[2]
	df = pd.read_csv(file_input, sep = '\t')
	df = wrapper_fun(df)
	df.to_csv(file_output, doublequote=False, escapechar='\\')


if __name__ == '__main__':
	main()