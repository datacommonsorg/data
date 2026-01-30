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
Edit Date: 07/15/2024 
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


def get_databases_in_row(s, l):
	"""Extracts unique database names from a string containing comma-separated database-value pairs.

    Args:
        s (str): A string containing comma-separated entries like "database:value".
        l (list): A list to store the extracted database names.

    Returns:
        list: The updated list 'l' with unique database names.
    """
	for entry in s.split('),'):
		if ":" in entry:
			entry_list = entry.split(':')
			database = entry_list[0].strip().replace('"', '')
			l.append(database)
	return l


def get_unique_databases(df, col):
	"""Collects all unique database names found within a specific column of a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to analyze.
        col (str): The name of the column containing database-value pairs.

    Returns:
        list: A list of unique database names.
    """
	l = []
	for index, row in df.iterrows():
		s = row[col]
		if isinstance(s, str):
			all_databases = get_databases_in_row(s, l)
	l = list(set(l))
	return l


def create_empty_columns(df, column_names):
    """Creates empty columns in a DataFrame for each item in a list.

    Args:
        df: The DataFrame to modify.
        column_names: A list of column names to create.

    Returns:
        The modified DataFrame with new empty columns.
    """

    for col_name in column_names:
        df[col_name] = ""  # Assign an empty string to each new column

    return df


def identify_clean_id_values(df, index, s):
	"""Extracts and cleans ID values from a string of database-ID pairs for a specific row in a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to modify.
        index: The row index to update.
        s (str): A string containing comma-separated "database:ID(name)" pairs.

    Returns:
        pd.DataFrame: The modified DataFrame with extracted ID values in corresponding columns.
    """
	for entry in s.split('),'):
		if ":" in entry:
			entry_list = entry.split(':')
			database = entry_list[0].strip().replace('"', '')
			ID = (':').join(entry_list[1:])
			ID = ID.split ('(')[0]  # take ID only, remove name in ()
			df.loc[index, database] = ID
	return df


def parse_database_ID_pairs(df, col):
	"""Parses a column containing database-ID pairs and extracts the ID values into separate columns.

    Args:
        df (pd.DataFrame): The DataFrame to modify.
        col (str): The name of the column containing the database-ID pairs.

    Returns:
        pd.DataFrame: The modified DataFrame with extracted ID values in new columns, with duplicates removed.
    """
	for index, row in df.iterrows():
		s = row[col]
		if isinstance(s, str):
			df = identify_clean_id_values(df, index, s)
	return df.drop_duplicates()	


def write_ID_values_to_df(df, col):
	"""Extracts and writes ID values from a specific column into separate columns, then drops the original column.

    Args:
        df (pd.DataFrame): The DataFrame to modify.
        col (str): The name of the column containing database-ID pairs.

    Returns:
        pd.DataFrame: The modified DataFrame with ID values in separate columns and the original column removed.
    """
	all_databases = get_unique_databases(df, col)
	create_empty_columns(df, all_databases)
	df = parse_database_ID_pairs(df, col)
	df = df.drop(col, axis=1)
	return df


def check_for_illegal_charc(s):
	"""Checks for illegal characters in a string and prints an error statement if any are present
	Args:
		s: target string that needs to be checked
	
	"""
	list_illegal = ["'", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
	if any([x in s for x in list_illegal]):
		print('Error! dcid contains illegal characters!', s)
	return


def check_for_dcid(row):
	"""
    Checks if the 'dcid_mesh' column in a row contains any illegal characters.

    Args:
        row: A row from a pandas DataFrame.

    Returns:
        The row if 'dcid_mesh' is valid, otherwise raises an error (likely from `check_for_illegal_charc`).
    """
	# check that dcid does not contain any illegal characters
	check_for_illegal_charc(str(row['dcid_mesh']))
	return row


def filter_non_empty(df, col):
	"""
    Filters out rows where a specified column is empty.

    Args:
        df (pd.DataFrame): The DataFrame to filter.
        col (str): The name of the column to check for empty values.

    Returns:
        pd.DataFrame: The filtered DataFrame with non-empty rows for the specified column.
    """
	# Replace empty strings in `col1` with `np.nan`
	df[col] = df[col].replace('', np.nan)

	# Drop rows where the value in `col1` is `np.nan`
	df = df.dropna(subset=[col])

	return df


def add_dcid(df):
	"""
    Adds a 'dcid_mesh' column to the DataFrame based on the 'MeSH' column.

    Args:
        df (pd.DataFrame): The DataFrame to modify.

    Returns:
        pd.DataFrame: The modified DataFrame with the added 'dcid_mesh' column.
    """
	# filter for columns missing mesh ids
	df =  filter_non_empty(df.copy(), 'MeSH')

	# Create a new column 'dcid_mesh'
	df.loc[:, 'dcid_mesh'] = 'bio/' + df['MeSH']

	# check that generated dcid doesn't contain any illegal characters
	df = df.apply(lambda x: check_for_dcid(x),axis=1)

	return df


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


def format_columns(df):
	"""
    Performs column renaming, cleaning, and formatting operations on a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to process.

    Returns:
        pd.DataFrame: The modified DataFrame with formatted columns.
    """
    # Rename columns to match the desired format
	df = df.rename(columns={
		'PharmGKB Accession Id':'pharmGKBID',
		'Alternate Names': 'synonyms',
		'External Vocabulary':'externalVocab',
		'Cross-references':'crossReferences'
		})

	# Explode database:ID pairs from specified columns so that each database
	# is represented as its own column with the values being the IDs
	df = write_ID_values_to_df(df, 'crossReferences')
	df = write_ID_values_to_df(df, 'externalVocab')

	# Add the 'dcid_mesh' column and reorder the columns
	df = add_dcid(df)
	df = reorder_columns(df, 'synonyms')
	
	return df


def write_subset_to_csv(df, prefix, file_output):
	# filter for rows that have dcid of interest
	df = df[df['dcid_mesh'].astype(str).str.startswith(prefix)].copy()

	# write dataframe to csv file
	df.to_csv(file_output, doublequote=False, escapechar='\\', index=False)
	
	return


def write_csvs(df, file_output):
	"""Filter df for each MeSH entity type and write to a seperate CSV file.

    Args:
        df: The pandas DataFrame containing the data.
    """
	# filter df for each MeSH entity type and write to a seperate CSV file
	
	# MeSHDescriptor
	write_subset_to_csv(df, 'bio/D', file_output)

	# MeSHConcepts
	file_output_2 = file_output[:-4] + '_mesh_supplementary_concept_record.csv'
	write_subset_to_csv(df, 'bio/C', file_output_2)

	# MeSHQualifiers
	file_output_3 = file_output[:-4] + '_mesh_qualifier.csv'
	write_subset_to_csv(df, 'bio/Q', file_output_3)

	return


def main():
	file_input = sys.argv[1]
	file_output = sys.argv[2]
	df = pd.read_csv(file_input, sep = '\t')
	df = format_columns(df)
	write_csvs(df, file_output)
	df.to_csv(file_output, doublequote=False, escapechar='\\', index=False)


if __name__ == '__main__':
	main()
	