# Copyright 2024 Google LLC
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
Date: 02/20/2023
Name: format_variants
Edited By: Samantha Piekos
Edit Date: 07/09/2024 
Description: converts a .tsv from PharmGKB into a clean csv format, 
where each columns contains linkages or references to only 
database only for the purpose of clarity and understanding
@file_input: input .tsv from PharmGKB
@file_output: formatted .csv with PharmGKB and other database annotations
"""
import pandas as pd 
import numpy as np
import sys
import re

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


def format_external_vocab(df):
    # ... (Column renaming and cleaning) ... 
	df = df.rename(columns={'PharmGKB Accession Id':'pharmGKBID','External Vocabulary':'externalVocab', 'Cross-references':'crossReferences'})
	df = df.replace('"', '', regex=True)
	df = df.assign(externalVocab=df.externalVocab.str.split(",")).explode('externalVocab')
	df[['A', 'B']] = df['externalVocab'].str.split(':', n=1, expand=True)
	df['A'] = df['A'].astype(str).map(lambda x: re.sub('[^A-Za-z0-9]+', '', x))

    # --- Dictionary Storage ---
	new_columns = {}  # Create a dictionary to store new columns
	for newcol in df['A'].unique():
		new_columns[newcol] = np.where(df['A'] == newcol, df['B'], np.nan)
	
	# --- Convert Dictionary to DataFrame and Concatenate ---
	df = df.reset_index(drop=True)
	new_df = pd.DataFrame(new_columns).reset_index(drop=True)  # Convert dictionary to DataFrame
	df = pd.concat([df, new_df], axis=1)  # Concatenate with original DataFrame

	# ... (Aggregation, dropping columns, and slicing)
	df = df.groupby(by='pharmGKBID').agg(dict.fromkeys(df.columns[0:], replace_nan_func))
	df = df.drop(['A', 'B', 'externalVocab'], axis =1)
	df = df.iloc[:,4:8]
	return df


def format_cols(df):
    """
    This function cleans and formats specific columns in a DataFrame and adds a new column 'MeSHDcid'.

    Args:
        df (pd.DataFrame): The DataFrame to modify.

    Returns:
        pd.DataFrame: The modified DataFrame with cleaned columns and the 'MeSHDcid' column added.
    """

    # Create a copy to work on explicitly
    df = df.loc[df['MeSH'].notna(), :].copy()  # Filter for non-NaN rows and create a copy

    # List of columns to process
    list_cols = ['MeSH', 'SnoMedCT', 'UMLS', 'NDFRT']

    # Clean and format specified columns using `.loc`
    for i in list_cols:
        df.loc[:, i] = df[i].str.replace(r"\([^()]*\)", "", regex=True)  # Remove parentheses
        df.loc[:, i] = df[i].str.split('(').str[0]                      # Remove after first parenthesis

    # Create a new column 'MeSHDcid'
    df.loc[:, 'MeSHDcid'] = 'bio/' + df['MeSH']

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
	# check that dcid does not contain any illegal characters
	check_for_illegal_charc(str(row['MeSHDcid']))
	return row


def main():
	file_input = sys.argv[1]
	file_output = sys.argv[2]
	df = pd.read_csv(file_input, sep = '\t')
	df = format_external_vocab(df)
	df = format_cols(df)
	df = df.apply(lambda x: check_for_dcid(x),axis=1)
	df.to_csv(file_output, doublequote=False, escapechar='\\', index=False)


if __name__ == '__main__':
	main()
	