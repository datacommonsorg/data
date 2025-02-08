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
Date: 08/12/2023
Edited By: Samantha Piekos
Last Edited: 2/7/25
Name: format_disease_jensen_lab
Description: converts a three input .txt files from Diseases at
Jensen Lab into output .csv files with formatted dcids, 
NonCoding RNA types, and gene ensemblIDs.
@file_input: input .txt files from Diseases at Jensen Lab 
@file_output: formatted .csv files for Diseases at Jensen Lab
"""

# load environment
import sys
import numpy as np
import pandas as pd
import time


# declare universal variables
HGNC_DICT = {'HGNC:9982':'RFX1', 'HGNC:9979':'RFPL2'}
LIST_ILLEGAL_CHARACTERS = ["'", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
DICT_COL_NAMES = {'experiments': 
	[
	'Id',
	'Gene',
	'Disease',
	'Disease_Name',
	'score-db',
	'source-score',
	'confidence'
	],
	'knowledge':
	[
	'Id',
	'Gene',
	'Disease',
	'Disease_Name',
	'score-db',
	'evidence',
	'confidence'
	],
	'textmining':
	[
	'Id',
	'Gene',
	'Disease',
	'Disease_Name',
	'z-score',
	'confidence',
	'url'
	]
}



def filter_for_lowest_ICD10_level(df):
    """Filters for the most specific ICD10 code for each gene."""

    indices_to_drop = []
    previous_ICD10 = ''
    previous_gene = ''
    previous_index = -1

    for index, row in df.iterrows():
        current_ICD10 = row['ICD10']
        current_gene = row['Gene']

        # Check if current ICD10 is more specific than previous for the same gene
        if current_gene == previous_gene and current_ICD10.startswith(previous_ICD10):
            indices_to_drop.append(previous_index)

        # Update tracking variables
        previous_ICD10 = current_ICD10
        previous_gene = current_gene
        previous_index = index

    # drop rows with less specific ICD10 codes for a given gene
    df.drop(indices_to_drop, axis=0, inplace=True)
    
    return df


def fix_ICD10_formatting(df, col):
	"""
	Adds a missing decimal in proper position to more specific ICD10 codes 
	that are missing them. If string in specified column is 10 characters or longer, 
	add '.' in the 10th position.
	"""
	mask = df[col].str.len() >= 10
	df.loc[mask, col] = df.loc[mask, col].str[:9] + '.' + df.loc[mask, col].str[9:]
	return df


def format_icd10_code_dcids(df):
	"""Formats ICD10 code DCIDs, filtering for the most specific codes."""
	df_doid = df.dropna(subset=['DOID'])    # Create a separate DataFrame for rows with DOID

	# Filter out invalid ICD-10 codes (e.g., root, short codes like C1 or C2)
	df['count'] = np.where(df['ICD10'] == df['ICD10'],df['ICD10'].str.split(':'),np.nan)
	df['count'] = np.where(df['count'] == df['count'],df['count'].str[1],np.nan)
	df = df[df['count']!='root']  # Remove "root" codes
	df.loc[:, 'count'] = df['count'].str.len()
	df = df[df['count'] > 2]  # Keep codes longer than 2 characters

	df = filter_for_lowest_ICD10_level(df)   # Keep only the most specific ICD10 codes
	
	# fix ill formatted ICD10 codes
	df = fix_ICD10_formatting(df, 'Disease')
	df = fix_ICD10_formatting(df, 'Disease_Name')
	df = fix_ICD10_formatting(df, 'ICD10')
	
	df_final = pd.concat([df, df_doid]).sort_index() # Recombine with DOID rows
	return df_final


def format_doid_icd(df):
	"""Formats DOID and ICD10 columns, and extracts Ensembl IDs."""
	df['DOID'] = np.where(df['Disease'].str.contains('DOID'),df['Disease'],np.nan)
	df['ICD10'] = np.where(df['Disease'].str.contains('ICD10'),df['Disease'],np.nan)
	## identify ensemblIDs and set as new column
	df['ensemblID'] = np.where(df['Id'].str.contains('ENSP00000'),df['Id'],np.nan)
	## format icd10 dcids filtering for the most specific ICD10 code
	df = format_icd10_code_dcids(df)
	return df


def check_for_illegal_char(s):
    """Checks for illegal characters in a string and raises a ValueError if any are present.

    Args:
        s: The target string that needs to be checked.

    Raises:
        ValueError: If the string contains any illegal characters.
    """
    for char in LIST_ILLEGAL_CHARACTERS:
    	if char in s:
    		raise ValueError(f"Illegal character '{char}' found in string: {s}")


def check_for_dcid(row):
	"""Checks dcid columns for illegal characters."""
	for cell in [row['dcid'], row['DOID_dcid'], row['ICD10_dcid'], row['Gene_dcid']]:
		check_for_illegal_char(str(cell))
	return row


def format_disease_gene_cols(df, data_type):
	"""
	 Formats disease/gene columns, generating DCIDs and names - 
	 handling formatting for import into a data commons knowledge graph.
	 """
	# handle exceptions in Gene names
	df['Gene'] = df['Gene'].map(HGNC_DICT).fillna(df['Gene'])
	df['Gene'] = df['Gene'].str.replace('@', '_Cluster')

    # generate gene dcid
	df['Gene_dcid'] = 'bio/' + df['Gene'].astype(str)

    # generate mappings to existing Disease or ICD10 nodes
	df['DOID_dcid'] = 'bio/' + df['DOID'].str.replace(':', '_')
	df['DOID_dcid'] = df['DOID_dcid'].replace('bio/nan', np.nan)
	df['ICD10_dcid'] = df['ICD10'].str.replace(':', '/')

    # use Disease nodes as default diseaseID mapping
    # use ICD10 nodes as diseaseID mapping in cases where Disease mapping does not exist
	df['Disease_dcid'] = df['DOID_dcid']
	df['Disease_dcid'] = df['Disease_dcid'].fillna(df['ICD10_dcid'])
	df['Disease_dcid'] = 'dcid:' + df['Disease_dcid']

    # generate dcid for DiseaseGeneAssociation nodes
	df['dcid'] = 'bio/' + df['Disease'].astype(str).str.replace(':', '_', regex=False) + '_' + df['Gene'].astype(str) + '_association'

    # format name for DiseaseGeneAssociation nodes
	df['name'] = df['Disease_Name'].astype(str) + ' and ' + df['Gene'].astype(str) + ' association'

    # drop columns not used in import
	df = df.drop(['Disease'], axis=1)
	return df


def format_RNA_type(df_non_coding):
    """
    Categorizes non-coding RNAs based on their gene names and assigns corresponding RNA types.

    This function adds an 'RNA_type' column to the input DataFrame, classifying 
    non-coding RNAs into specific categories based on keywords found in the 'Gene' column.  
    It uses a hierarchical approach, checking for specific RNA types first before 
    assigning a more general type.

    Args:
        df_non_coding: The input DataFrame containing non-coding RNA data, 
                       expected to have a 'Gene' column.

    Returns:
        The modified DataFrame with the added 'RNA_type' column.
    """

    gene_list = ['orf', 'ZNF']  # Keywords for protein-coding genes (treated as "Gene")
    sno_rna_list = ['sno', 'SNOR', 'SCAR']  # Keywords for small nucleolar RNAs
    linc_rna_list = ['LINC', 'linc', 'MIR']  # Keywords for long intergenic non-coding RNAs

    # Default RNA type (Long Non-Coding RNA)
    df_non_coding['RNA_type'] = 'dcs:NonCodingRNATypeLongNonCodingRNA'

    # Assign more specific RNA types based on gene name keywords
    df_non_coding['RNA_type'] = np.where(
        df_non_coding["Gene"].str.contains('|'.join(gene_list)),
        'Gene',  # Protein-coding genes
        df_non_coding['RNA_type']
    )
    df_non_coding['RNA_type'] = np.where(
        df_non_coding["Gene"].str.contains('rRNA'),
        'dcs:NonCodingRNATypeRibosomalRNA',  # Ribosomal RNA
        df_non_coding['RNA_type']
    )
    df_non_coding['RNA_type'] = np.where(
        df_non_coding["Gene"].str.contains('|'.join(linc_rna_list)),
        'dcs:NonCodingRNATypeLongIntergenicNonCodingRNA',  # Long intergenic non-coding RNA
        df_non_coding['RNA_type']
    )
    df_non_coding['RNA_type'] = np.where(
        df_non_coding["Gene"].str.contains('|'.join(sno_rna_list)),
        'dcs:NonCodingRNATypeSmallNucleolarRNA',  # Small nucleolar RNA
        df_non_coding['RNA_type']
    )
    df_non_coding['RNA_type'] = np.where(
        df_non_coding["Gene"].str.contains('miR'),
        'dcs:NonCodingRNATypeMicroRNA',  # MicroRNA
        df_non_coding['RNA_type']
    )
    df_non_coding['RNA_type'] = np.where(
        df_non_coding["Gene"].str.contains('circ'),
        'dcs:NonCodingRNATypeCircularRNA',  # Circular RNA
        df_non_coding['RNA_type']
    )
    df_non_coding['RNA_type'] = np.where(
        df_non_coding["Gene"].str.contains('pRNA'),
        'dcs:NonCodingRNATypePromoterAssociatedRNA',  # Promoter-associated RNA
        df_non_coding['RNA_type']
    )

    return df_non_coding


def format_dcids(df, data_type):
    """Formats DCIDs by calling helper functions and checking for illegal characters."""
    df = format_doid_icd(df)  # Format DOID and ICD10 columns
    df = format_disease_gene_cols(df, data_type)  # Format disease and gene columns
    df = df.apply(lambda x: check_for_dcid(x), axis=1)  # Check DCID-related columns for illegal characters
    return df

def format_data_type_specific_info(df, data_type):
    """Adds data type-specific information (e.g., association type)."""
    if data_type == 'experiments':
        df['associationType'] = 'dcs:AssociationSourceExperiment'
        df['source-score'] = df['source-score'].str.split('=')  # Split source score string
        df['source-score'] = np.where(df['source-score'] == df['source-score'], df['source-score'].str, np.nan) # Extract the score value
        df.update('"' + df[['Disease_Name', 'score-db']].astype(str) + '"')  # Add quotes around specific columns
    if data_type == 'knowledge':
        df['associationType'] = 'dcs:AssociationSourceKnowledge'
        df.update('"' + df[['Disease_Name', 'score-db']].astype(str) + '"')  # Add quotes
    if data_type == 'textmining':
        df['associationType'] = 'dcs:AssociationSourceTextMining'
        df.update('"' + df[['Disease_Name', 'url']].astype(str) + '"')  # Add quotes
    return df


def clean_data(df, data_type):
	"""
    Cleans and separates a DataFrame into coding and non-coding RNA data.

    Args:
        df: The input DataFrame containing RNA data.
        data_type: The type of data being processed (used by formatting functions).

    Returns:
        A tuple containing two DataFrames:
            - df: DataFrame with coding RNA data (and some gene data from non-coding).
            - df_non_coding: DataFrame with only non-coding RNA data.
    """
	df_non_coding = df  # Create a copy to hold non-coding RNA data
	searchfor = ['ENSP00', 'LINC', 'linc'] # list of stings to identify non-coding RNAs
	
	# Filter df to keep only coding RNAs (containing "ENSP00" and not in searchfor)
	df = df[df['Id'].str.contains("ENSP00")]
	df = df[~df.Gene.str.contains('|'.join(searchfor))]

	# Filter df_non_coding to keep only non-coding RNAs (not present in the filtered df)
	df_non_coding = df_non_coding[~df_non_coding.isin(df)].dropna() ## df with only non coding RNAs
	
	# Further filter non-coding RNAs to remove unwanted entries (containing "chr" or "ENSP00")
	df_non_coding = df_non_coding[~df_non_coding['Gene'].str.contains("chr")]
	df_non_coding = df_non_coding[~df_non_coding['Gene'].str.contains("ENSP00")]
	
	# Format DCIDs (Data Center IDs) for both DataFrames
	df = format_dcids(df, data_type)
	df_non_coding = format_dcids(df_non_coding, data_type)
	
	# Format RNA types for the non-coding DataFrame
	df_non_coding = format_RNA_type(df_non_coding)
	
	# Extract gene data from the non-coding DataFrame
	df_gene = df_non_coding.loc[df_non_coding['RNA_type']=='Gene']
	
	# Remove gene entries from the non-coding DataFrame
	df_non_coding = df_non_coding[~df_non_coding['RNA_type'].str.contains("Gene")]
	
	# Drop the 'RNA_type' column from the gene DataFrame
	df_gene.drop(['RNA_type'],axis=1,inplace=True)
	
	# Drop columns with all NA values from both DataFrames
	df = df.dropna(axis=1, how='all')
	df_gene = df_gene.dropna(axis=1, how='all') 

	# Concatenate the coding RNA DataFrame with the gene data from non-coding RNAs
	df = pd.concat([df, df_gene], ignore_index=True)

    # Apply data type-specific formatting
	df = format_data_type_specific_info(df, data_type)
	df_non_coding = format_data_type_specific_info(df_non_coding, data_type)
	
	return df, df_non_coding


def write_df_to_csv(df, data_type, coding=True):
    """Writes a DataFrame to a CSV file."""
    if df.shape == 0:  # Check for empty DataFrame
        return

    # Construct file path
    if coding:
        filepath = 'CSVs/codingGenes-' + data_type + '.csv'
    else:
        filepath = 'CSVs/nonCodingGenes-' + data_type + '.csv'

    df.to_csv(filepath, doublequote=False, escapechar='\\')  # Write to CSV
    return


def format_csv(data_type):
    """Formats a TSV file, cleans the data, and writes to separate CSV files."""
    start_time = time.time()
    filepath = 'input/human_disease_' + data_type + '_full.tsv'
    col_names = DICT_COL_NAMES[data_type]  # Get column names
    df = pd.read_csv(filepath, sep='\t', header=None)  # Read TSV
    df.columns = col_names  # Set column names

    df_coding_genes, df_non_coding_genes = clean_data(df, data_type)  # Clean and split data

    write_df_to_csv(df_coding_genes, data_type)  # Write coding gene data to CSV
    
    if len(df_non_coding_genes) >= 2: # Write non-coding gene data to CSV if it's not empty
    	write_df_to_csv(df_non_coding_genes, data_type, coding=False)  # Write non-coding gene data to CSV

    processing_time = "%s seconds" % round((time.time() - start_time), 2)
    print('Finished processing ' + data_type + ' data in ' + processing_time + '!')


def main():
	format_csv('experiments')
	format_csv('knowledge')
	format_csv('textmining')


if __name__ == '__main__':
    main() 
    
