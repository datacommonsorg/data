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
# Author: Sanika Prasad
# Date: 21-Jul-2024
# Edited By: Samantha Piekos
# Last Edited: 22-Jul-2024
# Name: process
# Description: cleaning the NCBI Assembly summary reports data.
# @source data: Download assembly_summary_genbank.txt and assembly_summary_refseq.txt from NCBI Assembly FTP Download page
# @file_input: assembly_summary_genbank.txt and assembly_summary_refseq.txt
# @file_output: formatted ncbi_assembly_summary.csv

# import environment
from absl import flags
from pathlib import Path
from absl import logging
from google.cloud import storage
import absl
import csv
import numpy as np
import pandas as pd
import os
import sys
logging.set_verbosity(logging.INFO)

# Declare Universal Variables
TAX_ID_DCID_MAPPING = {}

MODULE_DIR = str(Path(os.path.dirname(__file__)))

TEXT_COLUMNS = [
    'breed', 'cultivar', 'ecotype', 'infraspecific_name', 'isolate', 'strain'
]


def generate_column(df):
    """Adding new columns with required terms from existing columns.
	Args:
		df: dataframe with existing columns from source.
	Returns:
		df: dataframe with new columns with required terms.
	
	"""
    df['dcid'] = 'bio/' + df['assembly_accession']
    df['genome_size_dcid'] = 'BasePairs' + df['genome_size'].astype(str)
    df['genome_size_name'] = 'BasePairs ' + df['genome_size'].astype(str)
    df['genome_size_ungapped_dcid'] = 'BasePairs' + df[
        'genome_size_ungapped'].astype(str)
    df['genome_size_ungapped_name'] = 'BasePairs ' + df[
        'genome_size_ungapped'].astype(str)
    df['gc_percent_dcid'] = 'Percent' + df['gc_percent'].astype(str)
    df['gc_percent_name'] = 'Percent ' + df['gc_percent'].astype(str)
    return df


def refseq_category(df):
    """Replacing columns values to required property value.
	Args:
		df: dataframe with existing columns values from source.
	Returns:
		df: dataframe with new columns values.
	
	"""
    conversion_to_refseq_category = {
        'representative genome': 'dcs:RefSeqCategoryRepresentativeGenome',
        'reference genome': 'dcs:RefSeqCategoryReferenceGenome',
    }
    df['refseq_category'] = df['refseq_category'].map(
        conversion_to_refseq_category).fillna(df['refseq_category'])
    return df


def tax_id(df):
    """Replacing taxid column value as required.
	Args:
		df: dataframe with existing taxid column values from source.
	Returns:
		df: dataframe with required taxid column values.
	
	"""
    df['taxid'] = df.apply(lambda row: '' if str(row['taxid']) == str(row[
        'species_taxid']) else TAX_ID_DCID_MAPPING.get(row['taxid'], ''),
                           axis=1)
    df['taxid'] = df['taxid'].astype(str).str.replace(
        'dcid:', '', regex=False)  # Remove dcid prefix
    # Set values that don't start with 'bio/' to ''
    df.loc[~df['taxid'].astype(str).str.startswith('bio/'), 'taxid'] = ''
    return df


def species_tax_id(df):
    """Replacing species_taxid column value with tax_id_dcid_mapping.txt.
	Args:
		df: dataframe with existing species_taxid column values from source.
	Returns:
		df: dataframe with updated species_taxid column values.
	
	"""
    df['species_taxid'] = df['species_taxid'].map(TAX_ID_DCID_MAPPING).fillna(
        df['species_taxid'])
    df['species_taxid'] = df['species_taxid'].astype(str).str.replace(
        'dcid:', '', regex=False)  # Remove dcid prefix
    # Set values that don't start with 'bio/' to ''
    df.loc[~df['species_taxid'].astype(str).str.startswith('bio/'),
           'species_taxid'] = ''
    return df


def clean_columns(df):
    """Replacing unwanted char from organism_name, asm_submitter, annotation_name, and annotation_provider columns.
    Args:
        df: dataframe with unwanted characters in specific columns.
    Returns:
        df: dataframe with removed unwanted characters from desired columns.
    
    """
    df['organism_name'] = df['organism_name'].str.replace('[', '').str.replace(
        ']', '')
    df['asm_submitter'] = df['asm_submitter'].str.replace('\"', '')
    df['annotation_name'] = df['annotation_name'].str.replace('\"', '')
    df['annotation_provider'] = df['annotation_provider'].str.replace('\"', '')
    return df


def split_infraspecific_subtype(df, col1, col2, str_start):
    """Splits a column containing infraspecific identifiers into two columns.

    This function takes a DataFrame and three column names as input. 
    It identifies infraspecific identifiers in the first column that start with a 
    specific string, extracts them to the second column, and removes them from the original.

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        col1 (str): The name of the column containing the original infraspecific identifiers.
        col2 (str): The name of the new column where the extracted substrings will be stored.
        str_start (str): The starting substring used to identify infraspecific identifiers.

    Returns:
        pd.DataFrame: The modified DataFrame with the split columns.
    """
    # Extract substrings starting with 'start' and create `col2`
    df[col2] = df[col1].apply(lambda x: x if x.startswith(str_start) else '')

    # Set values in `col1` to empty string where `col2` is not empty
    df.loc[df[col2] != '', col1] = ''

    # Strip 'start' from `col2` if it exists
    df[col2] = df[col2].astype(str).str.replace(str_start, '', regex=False)

    return df


def infraspecific_name(df):
    """
    Processes the 'infraspecific_name' column in a DataFrame to extract and categorize 
    specific subtypes based on pre-defined keywords.

    Args:
        df (pd.DataFrame): The DataFrame containing the data, 
                          expected to have a column named 'infraspecific_name'.

    Returns:
        pd.DataFrame: The modified DataFrame with new columns for each extracted subtype, 
                      and the original 'infraspecific_name' column potentially modified.
    """
    # Dictionary mapping subtype column names to the starting strings used to identify them.
    dict_strings = {
        'breed': 'breed=',
        'cultivar': 'cultivar=',
        'ecotype': 'ecotype=',
        'strain': 'strain='
    }

    # Iterate over the dictionary to process each subtype
    for col, str_start in dict_strings.items():
        df = split_infraspecific_subtype(df, 'infraspecific_name', col,
                                         str_start)

    return df


def format_correction(df):
    """Replacing unwanted char from infraspecific_name and isolate column value.
	Args:
		df: dataframe with unwanted char in infraspecific_name and isolate column values from source.
	Returns:
		df: dataframe with removed unwanted char.
	
	"""
    df['infraspecific_name'] = '\"' + df['infraspecific_name'] + '\"'
    df['isolate'] = '\"' + df['isolate'] + '\"'
    return df


def is_not_none(x):
    # check if value exists
    if pd.isna(x):
        return False
    return True


def format_text_strings(df, col_names):
    """
    Converts missing values to numpy nan value and adds outside quotes
    to strings (excluding np.nan). Applies change to columns specified in col_names.
    """

    for col in col_names:
        df[col] = df[col].str.rstrip()  # Remove trailing whitespace
        df[col] = df[col].replace([''],
                                  np.nan)  # replace missing values with np.nan

        # Quote only string values
        mask = df[col].apply(is_not_none)
        df.loc[mask, col] = '"' + df.loc[mask, col].astype(str) + '"'

    return df


def assembly_level(df):
    """Replacing columns values to required property value.
	Args:
		df: dataframe with existing columns values from source.
	Returns:
		df: dataframe with new columns values.
	
	"""
    conversion_to_assembly_level = {
        'Complete Genome': 'dcs:GenomeAssemblyLevelCompleteGenome',
        'Chromosome': 'dcs:GenomeAssemblyLevelChromosome',
        'Scaffold': 'dcs:GenomeAssemblyLevelScaffold',
        'Contig': 'dcs:GenomeAssemblyLevelContig',
    }
    df['assembly_level'] = df['assembly_level'].map(
        conversion_to_assembly_level).fillna(df['assembly_level'])
    return df


def release_type(df):
    """Replacing columns values to required property value.
	Args:
		df: dataframe with existing columns values from source.
	Returns:
		df: dataframe with new columns values.
	
	"""
    conversion_to_release_type = {
        'Major': 'dcs:GenomeAssemblyReleaseTypeMajor',
        'Minor': 'dcs:GenomeAssemblyReleaseTypeMinor',
        'Patch': 'dcs:GenomeAssemblyReleaseTypePatch',
    }
    df['release_type'] = df['release_type'].map(
        conversion_to_release_type).fillna(df['release_type'])
    return df


def genome_rep(df):
    """Replacing columns values to required property value.
	Args:
		df: dataframe with existing columns values from source.
	Returns:
		df: dataframe with new columns values.
	
	"""
    df['genome_rep'] = df['genome_rep'].apply(lambda x: 'True'
                                              if 'Full' in str(x) else 'False')
    return df


def formatdate(df):
    """Modifiying date format to correct format.
	Args:
		df: dataframe with incorrect date format.
	Returns:
		df: dataframe with correct date format.
	
	"""
    df['seq_rel_date'] = pd.to_datetime(df['seq_rel_date'])
    df['seq_rel_date'] = df['seq_rel_date'].dt.strftime('%Y-%m-%d')
    df['annotation_date'] = pd.to_datetime(df['annotation_date'])
    df['annotation_date'] = df['annotation_date'].dt.strftime('%Y-%m-%d')
    return df


def paired_asm_comp(df):
    """Replacing columns values to required property value.
	Args:
		df: dataframe with existing columns values from source.
	Returns:
		df: dataframe with new columns values.
	
	"""
    df['paired_asm_comp'] = df['paired_asm_comp'].apply(
        lambda x: 'True' if 'identical' in str(x) else 'False')
    return df


def relation_to_type_material(df):
    """Replacing columns values to required property value.
	Args:
		df: dataframe with existing columns values from source.
	Returns:
		df: dataframe with new columns values.
	
	"""
    conversion_to_type_material = {
        'ICTV additional isolate':
            'dcs:GenomeAssemblyDerivedFromIctvAdditionalIsolate',
        'ICTV species exemplar':
            'dcs:GenomeAssemblyDerivedFromIctvSpeciesExemplar',
        'assembly designated as clade exemplar':
            'dcs:GenomeAssemblyDerivedFromCladeExemplar',
        'assembly designated as neotype':
            'dcs:GenomeAssemblyDerivedFromNeotype',
        'assembly designated as reftype':
            'dcs:GenomeAssemblyDerivedFromReftype',
        'assembly from pathotype material':
            'dcs:GenomeAssemblyDerivedFromPathotypeMaterial',
        'assembly from synonym type material':
            'dcs:GenomeAssemblyDerivedFromSynonymTypeMaterial',
        'assembly from type material':
            'dcs:GenomeAssemblyDerivedFromTypeMaterial',
    }
    df['relation_to_type_material'] = df['relation_to_type_material'].map(
        conversion_to_type_material).fillna(df['relation_to_type_material'])
    return df


def assembly_type(df):
    """Replacing columns values to required property value.
	Args:
		df: dataframe with existing columns values from source.
	Returns:
		df: dataframe with new columns values.
	
	"""
    conversion_to_assembly_type = {
        'alternate-pseudohaplotype':
            'dcs:GenomeAssemblyTypeAlternatePseudohaplotype',
        'diploid':
            'dcs:GenomeAssemblyTypeDiploidAssembly',
        'haploid':
            'dcs:GenomeAssemblyTypeHaploidAssembly',
        'haploid-with-alt-loci':
            'dcs:GenomeAssemblyTypeHaploidWithAltLoci',
        'unresolved-diploid':
            'dcs:GenomeAssemblyTypeUnresolvedDiploid',
    }
    df['assembly_type'] = df['assembly_type'].map(
        conversion_to_assembly_type).fillna(df['assembly_type'])
    return df


def group(df):
    """Replacing columns values to required property value.
	Args:
		df: dataframe with existing columns values from source.
	Returns:
		df: dataframe with new columns values.
	
	"""
    conversion_to_group = {
        'archaea':
            'dcs:BiologicalTaxonomyGroupArchaea',
        'bacteria':
            'dcs:BiologicalTaxonomyGroupBacteria',
        'fungi':
            'dcs:BiologicalTaxonomyGroupFungi',
        'invertebrate':
            'dcs:BiologicalTaxonomyGroupInvertebrate',
        'metagenomes':
            'dcs:BiologicalTaxonomyGroupMetagenomes',
        'other':
            'dcs:BiologicalTaxonomyGroupOther',
        'plant':
            'dcs:BiologicalTaxonomyGroupPlant',
        'protozoa':
            'dcs:BiologicalTaxonomyGroupProtozoa',
        'vertebrate_mammalian':
            'dcs:BiologicalTaxonomyGroupVertebrateMammalian',
        'vertebrate_other':
            'dcs:BiologicalTaxonomyGroupVertebrateOther',
        'viral':
            'dcs:BiologicalTaxonomyGroupViral',
    }
    df['group'] = df['group'].map(conversion_to_group).fillna(df['group'])
    return df


def set_flags():
    global _FLAGS
    _FLAGS = flags.FLAGS
    flags.DEFINE_string('output_dir', 'scripts/output',
                        'Output directory for generated files.')
    flags.DEFINE_string('input_dir',
                        'scripts/input/assembly_summary_genbank.txt',
                        'Input directory where .txt files downloaded.')
    flags.DEFINE_string('input_dir1',
                        'scripts/input/assembly_summary_refseq.txt',
                        'Output directory for generated files.')
    flags.DEFINE_string(
        'tax_id_dcid_mapping',
        'gs://datcom-prod-imports/scripts/biomedical/NCBI_tax_id_dcid_mapping/tax_id_dcid_mapping.txt',
        'Input directory where .txt files downloaded.')


def preprocess_data(df):
    df = generate_column(df)
    df = refseq_category(df)
    df = tax_id(df)
    df = species_tax_id(df)
    df = clean_columns(df)
    df = infraspecific_name(df)
    # df = format_correction(df)
    df = format_text_strings(df, TEXT_COLUMNS)
    df = assembly_level(df)
    df = release_type(df)
    df = genome_rep(df)
    df = formatdate(df)
    df = paired_asm_comp(df)
    df = relation_to_type_material(df)
    df = assembly_type(df)
    df = group(df)
    df = df.fillna('')
    return df


def main(_FLAGS):
    global TAX_ID_DCID_MAPPING
    file_input = _FLAGS.input_dir
    file_input1 = _FLAGS.input_dir1
    tax_id_dcid_mapping = _FLAGS.tax_id_dcid_mapping
    file_output = _FLAGS.output_dir
    if not os.path.exists(file_output):
        logging.info(f"Output directory '{file_output}' does not exist. Creating it.")
        try:
            os.makedirs(file_output)
        except OSError as e:
            logging.fatal(f"Failed to create output directory '{file_output}': {e}")

    else:
        logging.info(f"Output directory '{file_output}' already exists.")

    df = pd.read_csv(file_input, skiprows=1, delimiter='\t')
    df = df.replace('na', '')
    df = df.drop(columns='asm_not_live_date')
    df = df.rename(columns={'#assembly_accession': 'assembly_accession'})

    df1 = pd.read_csv(file_input1, skiprows=1, delimiter='\t')
    ref_gbrs_paired_asm = df1['gbrs_paired_asm'].tolist()
    # Replace NaN values with a placeholder
    df['gbrs_paired_asm'] = df['gbrs_paired_asm'].fillna('')

    # Perform operations after replacing NaN
    df.loc[~df['gbrs_paired_asm'].str.startswith('GC') &
           df['assembly_accession'].isin(ref_gbrs_paired_asm),
           'gbrs_paired_asm'] = df['assembly_accession']

    # with open(tax_id_dcid_mapping, 'r') as file:
    #     csv_reader = csv.DictReader(file)
    #     for row in csv_reader:
    #         TAX_ID_DCID_MAPPING[int(row['tax_id'])] = row['dcid']
    storage_client = storage.Client()
    bucket_name = 'datcom-prod-imports'
    bucket = storage_client.bucket(bucket_name)
    path_parts = tax_id_dcid_mapping.split('/')
    blob_name = '/'.join(path_parts[3:])
    blob = bucket.blob(blob_name)

    # Download the file contents as a string.
    file_contents = blob.download_as_text()

    # Create a CSV reader from the string.
    csv_reader = csv.DictReader(file_contents.splitlines())

    for row in csv_reader:
        TAX_ID_DCID_MAPPING[int(row['tax_id'])] = row['dcid']

    df = preprocess_data(df)
    file_output = os.path.join(file_output, 'ncbi_assembly_summary.csv')
    df.to_csv(file_output, doublequote=False, escapechar='\\', index=False)


if __name__ == "__main__":
    try:
        set_flags()  # Parse the flags
        _FLAGS = flags.FLAGS  # Access the parsed flags
        main(_FLAGS)

    except absl.flags._exceptions.UnparsedFlagAccessError:
        # Retry parsing the flags if the UnparsedFlagAccessError occurs
        flags.FLAGS(sys.argv)
        _FLAGS = flags.FLAGS
        main(_FLAGS)
