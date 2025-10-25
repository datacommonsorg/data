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
Date: 03/05/2022
Name: format_drugs
Edited By: Samantha Piekos
Last Edited: 07/17/24
Description: converts a .tsv from PharmGKB into a clean csv format, 
where each columns contains linkages or references to only 
database only for the purpose of clarity and understanding
@file_input: input .tsv from PharmGKB
@file_output: formatted .csv with PharmGKB and other database annotations
"""
# set up environment
import sys
import pandas as pd
import numpy as np
import re


# declare universal variables
DRUG_TYPE_DICT = {
    "Drug": "dcs:DrugTypeUnknown",
    "Drug Class": "dcs:DrugTypeUnknown",
    "Prodrug": "dcs:DrugTypeProdrug",
    "Biological Intermediate": "dcs:DrugTypeBiologicalIntermediate",
    "Metabolite": "dcs:DrugTypeMetabolite",
    "Ion": "dcs:DrugTypeIon",
    "Small Molecule": "dcs:DrugTypeSmallMolecule"
}


CLINICAL_ANNOTATION_LEVEL = {
    "1A": "dcs:PharmGkbClinicalLevelOneA",
    "1B": "dcs:PharmGkbClinicalLevelOneB",
    "2A": "dcs:PharmGkbClinicalLevelTwoA",
    "2B": "dcs:PharmGkbClinicalLevelTwoB",
    "3": "dcs:PharmGkbClinicalLevelThree",
    "4": "dcs:PharmGkbClinicalLevelFour"
}


DROP_COLUMNS = [
    'crossReferences',
    'externalVocab',
    'Dosing Guideline',
    'Dosing Guideline Sources',
    'Top FDA Label Testing Level',
    'Top Any Drug Label Testing Level',
    'Label Has Dosing Info',
    'Top CPIC Pairs Level',
    'FDA Label has Prescribing Info',
    'Has Rx Annotation',
    'In FDA PGx Association Sections',
    'PharmGKB Tags'
    ''
]


TEXT_COLUMNS = [
    "pharmGKBID",
    "Name",
    "genericName",
    "tradeName",
    "brandMixture",
    "SMILES",
    "InChI",
    "rxNormID",
    "pubChemCID",
    'drugBankMetabolite',
    'BindingDB',
    "CAS",
    "ChEBI",
    "URL",
    "ClinicalTrials.gov",
    "HMDB",
    "ChEMBL",
    "DrugBank",
    "pubChemSubstance",
    "NDF-RT",
    "RxNorm",
    "MedDRA",
]


TEXT_COLUMNS_SUBSET = [
    "SMILES",
    "genericName"
]


# declare functions
def get_unique_new_cols(df, col):
    """
    Extracts unique identifiers from a specified column in a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to process.
        col (str): The name of the column containing comma-separated identifier pairs.

    Returns:
        list: A list of unique identifiers extracted from the column.
    """
    # Explode the comma-separated values into separate rows
    df = df.assign(col=df[col].str.split(", ")).explode(col)
    
    # Split the identifier pairs into separate columns A and B
    df[['A', 'B']] = df[col].str.split(':', n=1, expand=True)  
    
    # Return a list of unique values from column A (the identifiers)
    list_unique_columns = list(set(df['A']))  
    return list_unique_columns


def create_mapping_dict(df, col):
    """
    Creates a dictionary to store mappings from 'pharmGKBID' to unique identifiers.

    Args:
        df (pd.DataFrame): The DataFrame containing the mapping information.
        col (str): The name of the column with the comma-separated identifier pairs.

    Returns:
        dict: A dictionary where keys are unique identifiers and values are initially empty lists.
    """
    list_unique_columns = get_unique_new_cols(df, col)  # Get unique identifiers
    
    # Initialize the dictionary with 'pharmGKBID' and empty lists for other identifiers
    d = {'pharmGKBID': []}  
    
    # Add keys to the dictionary for each unique identifier not already a column in the DataFrame
    for item in list_unique_columns:
        if item not in list(df.columns):  
            d[item] = []
    return d


def add_value_to_dict(d, k, v):
    """
    Adds a value to a list in a dictionary, creating the list if necessary.

    Args:
        d (dict): The dictionary to modify.
        k (str): The key (identifier) for which the value is being added.
        v (str): The value to be added.

    Returns:
        dict: The modified dictionary.
    """
    # Append v to the list of d[k] if k exists in d; else create a new list
    if k in d.keys(): 
        d[k].append(v)
    else:
        d[k] = [v]
    return d


def write_row_to_dict(d, d_row):
    """
    Writes mapping values for a row to the main dictionary.

    Args:
        d (dict): The main dictionary to update.
        d_row (dict): The dictionary containing mappings for the current row.

    Returns:
        dict: The updated main dictionary.
    """

    for k, v in d.items():  # Iterate over items in the main dictionary
        if k == 'pharmGKBID':  # Skip the 'pharmGKBID' key
            continue
        
        # If the identifier (k) is in the row dictionary, join its values into a comma-separated string
        # Otherwise, add an empty string to the corresponding list in the main dictionary
        if k in d_row.keys():  
            new_value = (', ').join(d_row[k])
            d[k].append(new_value)
        else:
            d[k].append('')
    return d


def determine_value(id_pairs):
    """
    Determines the correct value for an identifier pair.

    Args:
        id_pairs (list): A list containing the database and ID (e.g., ['db1', 'id1']).

    Returns:
        str: The ID value, potentially concatenated with a colon if there are multiple parts.
    """

    if len(id_pairs) == 2:  
        v = id_pairs[1]
    else:
        v = (':').join(id_pairs[1:])  # Join multiple parts with a colon
    return v


def extend_id_entry(df, index, k, v):
    """
    Extends an existing comma-separated entry in a DataFrame with a new value.

    Args:
        df (pd.DataFrame): The DataFrame to modify.
        index (int): The row index to update.
        k (str): The column name.
        v (str): The value to add to the existing entry.

    Returns:
        pd.DataFrame: The modified DataFrame.
    """
    list_values = df.loc[index, k].split(',')  # Get existing values
    list_values.append(v)  # Add the new value
    df.loc[index, k] = (', ').join(list_values)  # Update the DataFrame
    return df


def handle_database_id_pairs(identifiers, d, df, index):
    """
    Processes database identifier pairs (e.g., "db1:id1") and adds them to a dictionary or extends existing entries in a DataFrame.

    Args:
        identifiers (list): A list of strings, each representing a database ID pair.
        d (dict): The dictionary to store or update the mappings.
        df (pd.DataFrame): The DataFrame to potentially extend with new columns.
        index (int): The row index of the current mapping being processed.

    Returns:
        dict: The updated dictionary containing the processed mappings.
    """

    d_row = {}  # Initialize a dictionary to store mappings for the current row

    for identifier in identifiers:
        if len(identifier) == 0:    # Skip empty identifiers
            continue

        id_pairs = identifier.split(':')  # Split the identifier into [database, ID]
        k = id_pairs[0]                  # Get the database name (e.g., 'db1')
        v = determine_value(id_pairs)    # Get the ID value (e.g., 'id1')
                                         # (Assumes 'determine_value' function is defined elsewhere)

        if k in list(df.columns):   # If the database name is already a column in the DataFrame
            df = extend_id_entry(df, index, k, v)  # Extend the existing entry in that column
                                                   # (Assumes 'extend_id_entry' function is defined elsewhere)
        else:
            d_row = add_value_to_dict(d_row, k, v)  # Otherwise, add the mapping to the row dictionary
                                                   # (Assumes 'add_value_to_dict' function is defined elsewhere)

    # Update the main dictionary with the row's mappings. 
    d = write_row_to_dict(d, d_row)  # (Assumes 'write_row_to_dict' function is defined elsewhere)
    return d  # Return the updated main dictionary


def create_unique_mapping_columns(df, col):
    """
    Creates unique columns for each database ID mapping found in the specified column.

    Args:
        df (pd.DataFrame): The DataFrame to process.
        col (str): The name of the column containing comma-separated mapping values.

    Returns:
        pd.DataFrame: The DataFrame with new columns for each unique mapping.
    """
    df[col] = df[col].astype(str)  # declare type string
    d = create_mapping_dict(df, col)  # initiate mapping dictionary
    for index, row in df.iterrows():
        d['pharmGKBID'].append(row['pharmGKBID'])  # add pharmGKB value to dict
        identifiers = row[col].split(', ')   # split specified column on the ','
        # Process the list of identifiers for this row and update the dictionary
        d = handle_database_id_pairs(identifiers, d, df, index)
    df_new_cols = pd.DataFrame.from_dict(d)  # initiate new df with identifier dict
    # add identifier df to the main df
    df_final = df.merge(df_new_cols, on='pharmGKBID', how='left').fillna('')
    return df_final


def replace_empty_with_second_column(df, column_to_replace, replacement_column):
    """Replaces empty string values in one column with values from another column.

    Args:
        df: The pandas DataFrame.
        column_to_replace: The name of the column where empty strings will be replaced.
        replacement_column: The name of the column whose values will be used for replacement.

    Returns:
        The modified DataFrame with the replacements made and the replacement column dropped.
    """

    # check to make sure both columns of interest are in the df
    if column_to_replace not in df.columns or replacement_column not in df.columns:
        print("Error: One or both columns not found in the DataFrame.")
        return df
    
    # where missing values in one column with values of a second column
    df[column_to_replace] = df[column_to_replace].replace('',np.nan)
    df[column_to_replace] = df[column_to_replace].fillna(df[replacement_column])
    df[column_to_replace] = df[column_to_replace].replace(np.nan, '')
    
    # Drop the replacement column
    df = df.drop(replacement_column, axis=1)

    return df


def format_mappings(df):
    """
    This function formats and cleans a DataFrame containing mappings between chemicals and database identifiers.

    Args:
        df (pandas.DataFrame): The input DataFrame to be formatted.

    Returns:
        pandas.DataFrame: The formatted DataFrame.
    """
    # Dictionary to rename columns for consistency and clarity
    dict_rename_col = {
        'ATC Identifiers': 'atcCodes',
        'Brand Mixtures':'brandMixture',
        'Clinical Annotation Count': 'clinicalAnnotationCount',
        'Cross-references':'crossReferences',
        'External Vocabulary':'externalVocab',
        'Generic Names':'genericName',
        'Pathway Count': 'pathwayCount',
        'PharmGKB Accession Id':'pharmGKBID',
        'PubChem Compound Identifiers': 'pubChemCID',
        'RxNorm Identifiers': 'rxNormID',
        'Top Clinical Annotation Level': 'topClinicalAnnotationLevel',
        'Trade Names':'tradeName',
        'Variant Annotation Count': 'variantAnnotationCount',
        'VIP Count': 'vipCount'
        }
    
    # clean up mappings of chemicals to other database ids
    df = df.replace('"', '', regex=True)
    df = df.rename(columns=dict_rename_col)
    
    # create unique column for each database id
    df = create_unique_mapping_columns(df, 'crossReferences')
    df = create_unique_mapping_columns(df, 'externalVocab')
    df = df.rename(columns={
        'DrugBank Metabolite': 'drugBankMetabolite',
        'PubChem Substance': 'pubChemSubstance',
        })
    df = df.drop(DROP_COLUMNS , axis=1)
    
    # filter for valid links in URL column
    df['URL'] = np.where(df['URL'].str.startswith('http'), df['URL'], np.nan)
    
    # remove trailing '.0'
    df['pubChemCID'] = df['pubChemCID'].astype(str).apply(lambda x: x.split('.')[0])
    df['rxNormID'] = df['rxNormID'].astype(str).apply(lambda x: x.split('.')[0])
    
    # combine instances of ATC and PubChem Identifers into one column
    df = replace_empty_with_second_column(df, 'atcCodes', 'ATC')
    df = replace_empty_with_second_column(df, 'pubChemCID', 'PubChem Compound')   

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


def format_col_dcids(df, col, prefix):
    """
    Formats values in a specific column by adding a prefix and handling empty values.

    Args:
        df (pd.DataFrame): The DataFrame to modify.
        col (str): The name of the column to process.
        prefix (str): The prefix to add to each value.

    Returns:
        pd.DataFrame: The modified DataFrame with formatted values.
    """
    
    for index, row in df.iterrows(): # Iterate through rows of the dataframe
        value = row[col] 
        
        if len(value) == 0:  # Skip empty values
            continue

        list_values = value.split(', ') # Split the comma-separated values into a list
        list_formatted = [] # Initialize an empty list to store formatted values

        for item in list_values: 
            check_for_illegal_charc(item) # Validate the item (function assumed to be defined elsewhere)
            item = item.strip()  # remove whitespace
            list_formatted.append(prefix + item)  # Add the prefix to the item and store in the list

        # Join the formatted items back into a comma-separated string and update the DataFrame
        df.loc[index, col] = (', ').join(list_formatted)  

    return df


def remove_whitespace(text):
    # remove whitespace from text value column
    if pd.notna(text):   
        return "".join(text.split())
    else:
        return text


def convert_to_pascal_case(text):
  """
  Converts a given string to PascalCase format.

  Args:
      text: The string to be converted.

  Returns:
      The converted string in PascalCase.
  """
  # Split the string into words based on various delimiters
  words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", text)

  # Capitalize the first letter of each word
  pascal_case_words = [word.capitalize() for word in words]

  # Join the capitalized words back into a string
  pascal_case_string = "".join(pascal_case_words)

  return pascal_case_string


def generate_dcid(row):
    # if exists use CID to generate CID
    # else use the name of the compound converted to pascalcase
    pubchem_id = row['pubChemCID']
    if pd.isna(pubchem_id) or pubchem_id == "":  # Check for both NaN and empty strings
        dcid = convert_to_pascal_case(row['Name'])
        return dcid
    else:
        return 'CID' + str(pubchem_id)


def explode_column(col, df):
    # expand column whose value is a comma seperated list
    # so that one entry exists per row
    df[col] = df[col].str.split(',')
    df = df.explode(col)
    df[col] = df[col].astype(str).str.strip()
    return df


def classify_mesh_string(s):
    """Classifies strings as belonging to one prefix or another. Prints out strings that don't match either prefix.

    Args:
        s: The string to classify.
        original_column: The name of the column to split.

    Returns:
        strings that match each prefix or ""
    """
    if isinstance(s, str): 
        if s.startswith("bio/D"):
            return s, ""
        elif s.startswith("bio/C"):
            return "", s
        elif len(s) > 0: 
            print(f"Found string not matching prefix: '{s}'") 

    return "", ""


def split_descriptors_and_concepts(df):
    """Splits MeSH column in a DataFrame based on prefixes and replaces the original column.

    Args:
        df: The pandas DataFrame containing the data.

    Returns:
        The modified DataFrame with new columns and the original column removed.
    """
    # Split and create new columns
    new_columns = pd.DataFrame(df['MeSH'].apply(classify_mesh_string)
        .tolist(), columns=["dcid_MeSHDescriptor", "dcid_MeSHConcept"])

    # Add new columns to the DataFrame and remove the original
    df['dcid_MeSHDescriptor'] = new_columns['dcid_MeSHDescriptor']
    df['dcid_MeSHConcept'] = new_columns['dcid_MeSHConcept']
    df = df.drop('MeSH', axis=1)

    return df


def format_dcid(df):
    # format dcid using the CID plus the prefix 'chem/'
    # in absence of this existing use the prefix 'chem/' plus the name in pascal case
    # format dcids: add prefixes, ensure one per row, check for illegal characters
    # split MeSHDescriptors and MeSHConcepts into two seperate columns
    df['dcid'] = df.apply(generate_dcid, axis=1)
    df['dcid']= df['dcid'].replace(r'[^0-9a-zA-Z.-_\s]', '', regex=True).replace("'", '')
    df = format_col_dcids(df, 'atcCodes', 'chem/')
    df['atcCodes'] = df['atcCodes'].apply(remove_whitespace)
    df = explode_column('atcCodes', df)
    df = format_col_dcids(df, 'MeSH', 'bio/')
    df = explode_column('MeSH', df)
    df = split_descriptors_and_concepts(df)
    df = format_col_dcids(df, 'dcid', 'chem/')
    return df


def format_enum_cols(df):
    # Use universally declared dictionary to replace text values with appropriate enums
    df['Type'] = df['Type'].str.replace('"', '')
    df = df.assign(Type=df.Type.str.split(",")).explode('Type')
    df["Type"] = df["Type"].map(DRUG_TYPE_DICT)
    df['topClinicalAnnotationLevel'] = df['topClinicalAnnotationLevel'].astype(str).map(CLINICAL_ANNOTATION_LEVEL)
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
        df = unformatted dataframć
    Returns:
        df = formatted dataframe
    """
    df = format_mappings(df)
    df = format_dcid(df)
    df = format_enum_cols(df)
    df = format_text_strings(df, TEXT_COLUMNS, TEXT_COLUMNS_SUBSET)
    df = reorder_columns(df, 'genericName')
    return df.drop_duplicates()


def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    file_output_dict = sys.argv[3]
    df = pd.read_csv(file_input, sep = '\t').fillna('')
    df = wrapper_fun(df)
    df.to_csv(file_output, doublequote=False, escapechar='\\', index=False)
    df_limited = df[['pharmGKBID', 'dcid']]
    df_limited.to_csv(file_output_dict, doublequote=False, escapechar='\\', index=False)


if __name__ == '__main__':
    main()
    