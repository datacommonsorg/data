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
Date: 02/15/2022
EditedBy: Samantha Piekos
Last Edited: 07/17/24
Name: format_genes
Description: converts a .tsv from PharmGKB into a clean csv format, 
where each columns contains linkages or references to only 
database only for the purpose of clarity and understanding
@file_input: input .tsv from PharmGKB
@file_output: formatted .csv with PharmGKB and other database annotations
"""
# import environment
import pandas as pd
import numpy as np
import re
import sys


# declare universal variables
TEXT_COLUMNS = [
    "pharmGKBID",
    "Name",
    "ncbiGeneID",
    "hgncID",
    "ensemblID",
    "Symbol",
    "synonyms",
    "alternateSymbols",
    "Chromosome",
    "Ensembl",
    "ncbiGeneID",
    "ncbiGene",
    "comparativeToxicogenomicsDatabase",
    "GeneCard",
    "GenAtlas",
    "HGNC",
    "genomeCoordName37",
    "genomeCoordName38",
    "GenomeAssembly37",
    "GenomeAssembly38"
]


TEXT_COLUMNS_SUBSET = [
    "synonyms"
]


# declare functions
def get_unique_new_cols(df, col):
    """
    Extracts unique keys from a column containing colon-separated key-value pairs.

    Args:
        df (pd.DataFrame): The DataFrame to process.
        col (str): The name of the column containing key-value pairs.

    Returns:
        list: A list of unique keys found in the specified column.
    """
    df = df.assign(col=df[col].str.split(", ")).explode(col)  # Split on ", " and explode into rows
    df[['A', 'B']] = df[col].str.split(':', n=1, expand=True)  # Split each row into key ('A') and value ('B')
    list_unique_columns = list(set(df['A']))  # Get unique keys
    return list_unique_columns


def create_mapping_dict(df, col):
    """
    Creates a dictionary for storing extracted key-value pairs.

    Args:
        df (pd.DataFrame): The DataFrame to process.
        col (str): The name of the column containing key-value pairs.

    Returns:
        dict: A dictionary with unique keys as keys and empty lists as values.
    """
    list_unique_columns = get_unique_new_cols(df, col)  # Get unique keys
    d = {'pharmGKBID': []}  # Initialize dictionary with 'pharmGKBID' as a key
    for item in list_unique_columns:
        if item not in list(df.columns):  # Add keys not already in the DataFrame as columns
            d[item] = []
    return d


def add_value_to_dict(d, k, v):
    """
    Adds a value to a list in a dictionary for a given key.

    Args:
        d (dict): The dictionary to modify.
        k: The key to which the value should be added.
        v: The value to add.

    Returns:
        dict: The modified dictionary.
    """
    if k in d.keys():  # If the key exists, append the value
        d[k].append(v)
    else:  # If not, create a new list with the value
        d[k] = [v]
    return d


def write_row_to_dict(d, d_row):
    """
    Writes a row of data to a dictionary, filling in missing values with empty strings.

    Args:
        d (dict): The main dictionary where data is being collected.
        d_row (dict): A dictionary representing a single row of data.

    Returns:
        dict: The updated main dictionary.
    """
    for k, v in d.items():  # Iterate over keys in the main dictionary
        if k == 'pharmGKBID':  # Skip the 'pharmGKBID' key
            continue
        if k in d_row.keys():  # If the key exists in the row, add the value
            new_value = (', ').join(d_row[k])  # Join multiple values with comma and space
            d[k].append(new_value)
        else:  # If the key is missing, add an empty string
            d[k].append('')
    return d


def determine_value(id_pairs):
    """
    Determines the value part from a list of ID pairs.

    Args:
        id_pairs (list): A list containing the key and value(s) of an ID pair.

    Returns:
        str: The formatted value part.
    """
    if len(id_pairs) == 2:  # Simple key:value pair
        v = id_pairs[1]  # The value is the second element
    else:  # Complex case: key:value1:value2:...
        v = (':').join(id_pairs[1:])  # Join all values after the first with ":"
    return v


def extend_id_entry(df, index, k, v):
    """
    Adds a new value to an existing comma-separated list in a DataFrame cell.

    Args:
        df (pd.DataFrame): The DataFrame to modify.
        index: The row index to update.
        k: The column name (key).
        v: The new value to append.

    Returns:
        pd.DataFrame: The modified DataFrame with the updated cell.
    """

    list_values = df.loc[index, k].split(',')  # Get the existing values as a list
    list_values.append(v)  # Add the new value
    df.loc[index, k] = (', ').join(list_values)  # Join the list back into a comma-separated string

    return df


def handle_database_id_pairs(identifiers, d, df, index):
    """Processes pairs of identifiers (like "key:value") to update two data structures:

    * d: A dictionary for new key-value pairs
    * df: A DataFrame for existing keys in columns

    Args:
        identifiers: List of strings, each potentially a "key:value" pair or "key:value1:value2..." 
        d: Existing dictionary to be updated.
        df: Existing DataFrame to be updated.
        index: The row index of the DataFrame to update if a key exists in columns.

    Returns:
        The updated dictionary (d).
    """

    d_row = {}  # Temporary dict for new key-value pairs in the current row

    for identifier in identifiers:
        # Skip empty identifiers or those with only a colon (e.g., ":" or "::")
        if not identifier or identifier.count(":") == 0: 
            continue

        id_pairs = identifier.split(':')  # Split into key and value parts
        
        # The first part is the key
        k = id_pairs[0]           
        # Get the value(s) (could be a single value or multiple values joined by ':')
        v = determine_value(id_pairs)  

        if k in list(df.columns):  # Check if the key is already a column in the DataFrame
            df = extend_id_entry(df, index, k, v)  # Add the value to the existing entry
        else:
            # Store the key-value pair in the temp dict for later addition to the main dict
            d_row = add_value_to_dict(d_row, k, v)  

    # Add the collected key-value pairs from the temp dict to the main dictionary
    d = write_row_to_dict(d, d_row)  

    return d  # Return the updated main dictionary


def create_unique_mapping_columns(df, col):
    """Creates new columns in the DataFrame based on unique identifiers found within a specified column.

    Args:
        df: The DataFrame to process.
        col: The column containing comma-separated identifiers to split and extract key-value pairs from.

    Returns:
        The modified DataFrame with new columns for each unique identifier (key) found in the specified column.
    """

    # Ensure values in the target column are strings for consistent processing
    df[col] = df[col].astype(str)  

    # Initialize a dictionary to store the mapping between identifiers (keys) and their values
    d = create_mapping_dict(df, col) 

    # Iterate over each row and extract identifiers to update the mapping dictionary and DataFrame
    for index, row in df.iterrows():
        d['pharmGKBID'].append(row['pharmGKBID'])  # Collect 'pharmGKBID' for the mapping
        
        # Split the identifiers in the current row into a list 
        identifiers = row[col].split(', ')         

        # Process the key-value pairs extracted from the identifiers
        d = handle_database_id_pairs(identifiers, d, df, index)  

    # Create a new DataFrame from the mapping dictionary
    df_new_cols = pd.DataFrame.from_dict(d) 

    # Merge the new DataFrame back into the original one based on the 'pharmGKBID' column
    # Using 'left' join to keep all rows from the original df
    df_final = df.merge(df_new_cols, on='pharmGKBID', how='left').fillna('') 

    return df_final


def replace_at_symbol(df, column_name):
  """Replaces all instances of '@' with '_Cluster' in a DataFrame column.

  Args:
      df (pandas.DataFrame): The DataFrame containing the column.
      column_name (str): The name of the column to modify.

  Returns:
      pandas.DataFrame: The DataFrame with the modified column.
  """

  return df.assign(**{column_name: df[column_name].str.replace('@', '_Cluster')})


def check_for_illegal_charc(s):
    """Checks for illegal characters in a string and prints an error statement if any are present
    Args:
        s: target string that needs to be checked
    
    """
    list_illegal = ["'", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
    if any([x in s for x in list_illegal]):
        print('Error! dcid contains illegal characters!', s)


def eval_dcids_for_illegal_charc(l):
    """
    Iterates over a list of dcid values and checks each one for illegal characters.

    Args:
        l (list): A list of DCID values.

    Returns:
        None. This function raises an error if an illegal character is found.
    """
    for item in l:  # Iterate through each dcid value in the list
        check_for_illegal_charc(item)  # Call a function to check for illegal characters in the dcid


def format_dcids(df):
    """
    Formats the DCID column in a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to modify.

    Returns:
        pd.DataFrame: The modified DataFrame with formatted DCID values.
    """
    df['dcid'] = "bio/" + df['Symbol']  # Create a new 'dcid' column by adding "bio/" to the 'Symbol' column
    df = replace_at_symbol(df, 'dcid')  # Call a function to replace invalid characters in the 'dcid' column
    eval_dcids_for_illegal_charc(df['dcid'])  # Check if any invalid characters remain in the 'dcid' column
    return df


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
    dict_mapping = {
    'Alternate Names':'synonyms',
    'Alternate Symbols': 'alternateSymbols',
    'Cross-references':'crossReferences',
    'Ensembl Id':'ensemblID',
    'Has CPIC Dosing Guideline': 'hasCpicDosingGuideline',
    'Has Variant Annotation': 'hasVariantAnnotation',
    'HGNC ID':'hgncID',
    'Is VIP': 'isVIP',
    'NCBI Gene ID':'ncbiGeneID',
    'PharmGKB Accession Id':'pharmGKBID'
    }
    
    # get rid of superfulous quotes
    df = df.replace('"', '', regex=True)

    # rename a subset of columns
    df = df.rename(columns=dict_mapping)

    # create unique column for each database id
    df = create_unique_mapping_columns(df, 'crossReferences')
    df = df.rename(columns={
        'Comparative Toxicogenomics Database': 'comparativeToxicogenomicsDatabase',
        'NCBI Gene': 'ncbiGene'
        })
    df = df.drop(['crossReferences'], axis=1)

    # format dcids from gene symbol
    df = format_dcids(df)
	
    return df


def strip_decimal_from_coordinates(df, assembly):
    """
    This function removes trailing decimal points from the start and stop genomic coordinates columns for a specific genome assembly.

    Args:
        df (pd.DataFrame): The DataFrame containing the genomic coordinates.
        assembly (str): The genome assembly version (e.g., "37" or "38").

    Returns:
        pd.DataFrame: The modified DataFrame with the decimal points removed.
    """

    # Format column names based on the provided assembly
    start_col = 'Chromosomal Start - GRCh' + assembly
    stop_col = 'Chromosomal Stop - GRCh' + assembly

    # Ensure columns are treated as strings for splitting
    df[start_col] = df[start_col].astype(str)
    df[stop_col] = df[stop_col].astype(str)

    # Remove decimal points from the start column
    df[start_col] = df[start_col].apply(lambda x: x.split('.')[0])

    # Remove decimal points from the stop column
    df[stop_col] = df[stop_col].apply(lambda x: x.split('.')[0])

    return df


def format_genomic_coordinates(df):
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
        # format GenomicCoordinates properties
        df['GenomeAssembly' + i] = 'GRCh' + i
        df['genomeCoordName' + i] = 'GRCh' + i + "_" + df['Symbol'] + '_coordinates'
        df['genomeCoordDcid' + i] = "bio/" + df['genomeCoordName' + i]

        # remove trailing .0 from genomic coordinate start stop
        df = strip_decimal_from_coordinates(df, i)

        # replace @ within dcids with _Cluster
        df = replace_at_symbol(df, 'genomeCoordDcid' + i)

        # double check that dcids don't contain illegal characters
        eval_dcids_for_illegal_charc(df['genomeCoordDcid' + i])

    # rename genomic coordinate columns
    df = df.rename(columns={
        'Chromosomal Start - GRCh37': 'grCh37Start',
        'Chromosomal Stop - GRCh37': 'grCh37Stop',
        'Chromosomal Start - GRCh38': 'grCh38Start',
        'Chromosomal Stop - GRCh38': 'grCh38Stop'
        })

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
	list_bool_cols = ['isVIP', 'hasVariantAnnotation', 'hasCpicDosingGuideline']
	for i in list_bool_cols:
		df[i] = np.where(df[i] == "Yes", "True", "False")
	return df


def is_not_none(x):
    # check if value exists
    if pd.isna(x):
        return False
    return True


def format_text_strings(df, col_names, col_names_subset):
    """
    Converts missing values to numpy nan value and adds outside quotes
    to strings (excluding np.nan) to a subset. Applies change to columns specified in col_names.
    """

    for col in col_names:
        df[col] = df[col].str.rstrip()  # Remove trailing whitespace
        df[col] = df[col].replace([''],np.nan)  # replace missing values with np.nan

        if col in col_names_subset:
            # Quote only string values
            mask = df[col].apply(is_not_none)
            df.loc[mask, col] = '"' + df.loc[mask, col].astype(str) + '"'

    return df


def reorder_columns(df, column_to_move):
    # move specified column to last column position within the df
    new_columns = [col for col in df.columns if col != column_to_move] + [column_to_move]
    df = df[new_columns]
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
    df = format_genomic_coordinates(df)
    df = format_boolean_cols(df).fillna('')
    df = format_text_strings(df, TEXT_COLUMNS, TEXT_COLUMNS_SUBSET)
    df = reorder_columns(df, 'synonyms')
    return df


def main():
	file_input = sys.argv[1]
	file_output = sys.argv[2]
	df = pd.read_csv(file_input, sep = '\t').fillna('')
	df = wrapper_fun(df)
	df.to_csv(file_output, doublequote=False, escapechar='\\', index=False)


if __name__ == '__main__':
	main()
