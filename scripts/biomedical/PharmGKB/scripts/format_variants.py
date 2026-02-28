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
Edit Date: 07/17/2024 
Description: converts a .tsv from PharmGKB into a clean csv format, 
where each columns contains linkages or references to only 
database only for the purpose of clarity and understanding
@file_input: input .tsv from PharmGKB
@file_output: formatted .csv with PharmGKB and other database annotations
"""
import pandas as pd 
import numpy as np
import sys


def is_not_none(x):
    # check if value exists
    if pd.isna(x):
        return False
    return True


def format_text_strings(df, col):
    """
    Adds outside quotes to a specified text column that's problematic.
    """
    mask = df[col].apply(is_not_none)
    df.loc[mask, col] = '"' + df.loc[mask, col].astype(str) + '"'
    return df


def reorder_columns(df, column_to_move):
    """
    Reorders the columns of a DataFrame, moving the specified column to the last position.
    Add outside quotes to the column being move to the end.

    Args:
        df (pd.DataFrame): The DataFrame to reorder.
        column_to_move (str): The name of the column to move.

    Returns:
        pd.DataFrame: The DataFrame with reordered columns.
    """
    # move specified column to last column position within the df
    new_columns = [col for col in df.columns if col != column_to_move] + [column_to_move]
    df = df[new_columns]
    df = format_text_strings(df, column_to_move)
    return df


def format_cols(df):
	"""
	Formats the variants dataframe and generates dcid
	Args:
		df = unformatted dataframe
	Returns:
		df = formatted dataframe
	"""
	# Explode the dataframe on Gene Symbols so that there is one per row
	df['geneSymbols'] = df['Gene Symbols'].str.split(',')
	df = df.explode('geneSymbols')
	df = df.drop('Gene Symbols', axis=1)
	
	# generate dcids
	df = df.assign(dcid='bio/' + df['Variant Name'].astype(str))
	df = df.assign(dcid_gene='bio/' + df['geneSymbols'].astype(str))
	
	# reorder columns so problamatic string column is at the end
	df = reorder_columns(df, 'Synonyms')

	# rename columns
	df = df.rename(columns={
		'Clinical Annotation count': 'clinicalAnnotationCount',
		'Gene IDs': 'geneID',
		'Guideline Annotation count': 'guidelineAnnotationCount',
		'Label Annotation count': 'labelAnnotationCount',
		'Level 1/2 Clinical Annotation count': 'clinicalAnnotationCountLevel1_2',
		'Variant Annotation count': 'variantAnnotationCount',
		'Variant ID': 'pharmGKBID',
		'Variant Name': 'rsID'
		})

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
    check_for_illegal_charc(str(row['dcid']))
    return row


def main():
	file_input = sys.argv[1]
	file_output = sys.argv[2]
	df = pd.read_csv(file_input, sep = '\t')
	df = format_cols(df)
	df = df.apply(lambda x: check_for_dcid(x),axis=1)
	df.to_csv(file_output, doublequote=False, escapechar='\\', index=False)


if __name__ == '__main__':
	main()
	