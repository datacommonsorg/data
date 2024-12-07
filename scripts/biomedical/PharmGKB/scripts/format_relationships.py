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
Name: format_relationships
Edited By: Samantha Piekos
Last Edited: 7/11/24
Description: converts a .tsv from PharmGKB into a clean csv format, 
where each columns contains linkages or references to only 
database only for the purpose of clarity and understanding
@file_input: input .tsv from PharmGKB
@file_output: formatted .csv with PharmGKB and other database annotations
"""
import pandas as pd
import numpy as np
import datacommons as dc
import re
import sys


ASSOCIATION_DICT = {
	'associated': 'dcs:RelationshipAssociationTypeAssociated',
	'not associated': 'dcs:RelationshipAssociationTypeNotAssociated',
	'ambiguous': 'dcs:RelationshipAssociationTypeAmbiguous'
}


MESH_MAPPING_DICT = {
	'Lymphoma Nonhodgkin': 'bio/D008228',
	'Anemia Sickle Cell': 'bio/D000755',
	'Covid19': 'bio/D000086382',
	'Diabetes Mellitus Type 1': 'bio/D003922',
	'Leukemia Myelogenous Chronic Bcrabl Positive': 'bio/D007951',
	'Lymphoma Tcell Cutaneous': 'bio/D016410',
	'Arthritis Rheumatoid': 'bio/D001172'
}


def check_for_illegal_charc(s):
	"""Checks for illegal characters in a string and prints an error statement if any are present
	Args:
		s: target string that needs to be checked
	
	"""
	list_illegal = ["'", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
	if any([x in s for x in list_illegal]):
		print('Error! dcid contains illegal characters!', s)
	return


def choose_data_subset(df):
	"""
    This function filters and cleans a DataFrame based on entity types and duplicate entries.

    Args:
        df (pd.DataFrame): The input DataFrame containing entity relationships.

    Returns:
        pd.DataFrame: The filtered DataFrame without duplicates or haplotype entities.
    """
	df['sorted'] = df.apply(lambda x: ''.join(sorted([x['Entity1_id'],x['Entity2_id']])),axis=1)
	df = df.drop_duplicates(subset='sorted').drop('sorted',axis=1)
	df = df[ (df['Entity1_type'] != 'Haplotype') & (df['Entity2_type'] != 'Haplotype')]
	return df


def format_multivalue_cols(df):
	"""
    Expands multi-value columns in the DataFrame, specifically 'Evidence' and 'PMIDs'.

    Args:
        df (pd.DataFrame): The input DataFrame with multi-value columns.

    Returns:
        pd.DataFrame: The transformed DataFrame with expanded columns.
    """
	df = df.assign(Evidence=df.Evidence.str.split(",")).explode('Evidence')
	df = df.assign(PMIDs=df.PMIDs.str.split(";")).explode('PMIDs')
	return df


def format_enums(df):
	"""
    Converts binary enum columns ('PK' and 'PD') from string values to boolean.

    Args:
        df (pd.DataFrame): The input DataFrame with enum columns.

    Returns:
        pd.DataFrame: The modified DataFrame with boolean enum columns.
    """
	df['PK'] = np.where(df['PK'] == 'PK', 'True', 'False')
	df['PD'] = np.where(df['PD'] == 'PD', 'True', 'False')
	return df


def col_swap(df):
	"""
    This function swaps the values of columns related to Entity1 and Entity2 within a DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame containing columns related to Entity1 and Entity2.

    Returns:
        pd.DataFrame: The modified DataFrame with swapped column values.
    """
	df.rename({"Entity1_id": "Entity2_id", 
		   "Entity2_id": "Entity1_id", 
		   "Entity1_name": "Entity2_name",
		   "Entity2_name": "Entity1_name",
		   "Entity1_dcid": "Entity2_dcid", 
		   "Entity2_dcid": "Entity1_dcid",
		   "Entity1_type": "Entity2_type", 
		   "Entity2_type": "Entity1_type",}, 
		  axis = "columns", inplace = True)
	return df


def check_if_mesh_mapping_missing(dict_mesh_terms, dict_mesh_mappings):
	"""
    This function checks if there are missing mappings between MeSH terms and MeSH descriptors.

    Args:
        dict_mesh_terms (dict): A dictionary containing MeSH terms and their corresponding values.
        dict_mesh_mappings (dict): A dictionary containing manual mappings between PharmGKBIds and MeSH descriptors.

    Returns:
        None: This function does not return a value, but it prints an error message if a missing mapping is found.
    """
	for k, v in dict_mesh_terms.items():
		# Skip terms starting with 'bio/' already have been mapped to a dcid
		if v.startswith('bio/'):
			continue
		
		# skip if manual mapping exists for diseases whose dcids were not retreived using the dc API
		if k in dict_mesh_mappings.keys():
			continue
		
		# If the term is not in the mappings dictionary, print an error message
		print('Error! Mapping to MeSH Descriptor is not detected by using datacommons API or manual mapping file for', v +'!')
		
		return


def query_mesh_terms(df, col_name, dict_mesh_terms, dict_mesh_mappings):
	"""
    This function queries MeSH terms from a DataFrame column and updates dictionaries for further processing.

    Args:
        df (pd.DataFrame): The input DataFrame containing a column with MeSH terms.
        col_name (str): The name of the column containing MeSH terms in the DataFrame.
        dict_mesh_terms (dict): A dictionary containing previously identified MeSH terms and their corresponding values.
        dict_mesh_mappings (dict): A dictionary containing mappings between MeSH terms and MeSH descriptors.

    Returns:
        dict: An updated dictionary containing MeSH terms and their corresponding values.
    """
    # get unique list of disease names to query for corresponding dcids
	df = df.copy()
	df[col_name] = df[col_name].str.title()
	list_names = list(df[col_name].unique())
	arr_name = np.array(list_names)
	
	# Construct a SPARQL query to fetch MeSH descriptors and their corresponding DCIDs
	query_str = """
	SELECT DISTINCT ?dcid ?name
	WHERE {{
	?a typeOf MeSHDescriptor .
	?a name {value} .
	?a dcid ?dcid .
	?a name ?name
	}}
	""".format(value=arr_name)
	
	result = dc.query(query_str)  # Execute the query using the datacommons library 
	result = pd.DataFrame(result)   # convert results to pandas df
	
	# Create a dictionary to map MeSH names to their DCIDs
	dict_terms = dict(zip(result['?name'], result['?dcid']))
	
	# Update the existing dictionary with the newly found terms
	dict_mesh_terms = dict_mesh_terms | dict_terms
	
	# Check if any of the newly found terms have missing mappings
	check_if_mesh_mapping_missing(dict_mesh_terms, dict_mesh_mappings)
	
	return dict_mesh_terms


def check_for_dcid(row):
	"""
    This function checks for illegal characters in DCIDs within a DataFrame row.

    Args:
        row (pd.Series): A row from a DataFrame containing DCID columns.

    Returns:
        pd.Series: The row after checking for illegal characters.
    """
	check_for_illegal_charc(str(row['dcid']))
	check_for_illegal_charc(str(row['Entity1_dcid']))
	check_for_illegal_charc(str(row['Entity2_dcid']))
	return row


def get_value_from_dict(d, k):
	"""
    This function retrieves a value from a dictionary based on a key, with error handling.

    Args:
        d (dict): The dictionary to search.
        k: The key to look for.

    Returns:
        The value associated with the key, or an empty string if not found.
    """
	if k in d.keys():
		return d[k]
	print('Error! The MeSH Descriptor dcid', k, 'is not detectable via matching on name using datacommons API or in the additional manual mapping file!')
	return ''


def update_missing_mesh_ids(df, col_id, col_dcid, dict_mesh):
	"""
    This function updates missing MeSH IDs in a DataFrame using a dictionary of mappings.

    Args:
        df (pd.DataFrame): The DataFrame containing MeSH IDs to update.
        col_id (str): The name of the column containing the IDs to match in the dictionary.
        col_dcid (str): The name of the column containing the DCIDs to update.
        dict_mesh (dict): A dictionary manually mapping PharmGKB IDs to MeSH DCIDs.

    Returns:
        pd.DataFrame: The updated DataFrame with missing MeSH IDs filled in.
    """
	for index, row in df.iterrows():
		dcid = row[col_dcid]
		pharmgkbId = row[col_id]
		if dcid.startswith('bio/D'):  # Skip rows where the mesh DCID already exists
			continue
		else:
			# Get the MeSH DCID from the dictionary
			mesh_dcid = get_value_from_dict(dict_mesh, pharmgkbId)
			df.loc[index, col_dcid] = mesh_dcid
	return df


def format_disease_variant_df1(df, dict_mesh):
	"""
    This function formats the first DataFrame containing disease-variant associations for Data Commons.

    Args:
        df (pd.DataFrame): The input DataFrame with disease-variant associations where disease is Entity1.
        dict_mesh (dict): A dictionary for mapping MeSH terms.

    Returns:
        pd.DataFrame: The formatted DataFrame.
    """
    # Filter for relevant associations and variant names
	df = df[ ((df['Entity1_type'] == 'Disease') & (df['Entity2_type'] == 'Variant'))].copy()
	
	# Filter for GeneticVariants whose names are rsIDs
	df = df[df['Entity2_name'].str.startswith(('rs'))]
	
	# Query and map Disease PharmGKB Ids to MeSH Descriptor dcids
	mesh_dict = query_mesh_terms(df, 'Entity1_name', MESH_MAPPING_DICT, dict_mesh)
	df['Entity1_dcid'] = df['Entity1_name'].map(mesh_dict)
	df = df[df['Entity1_dcid'].notna()]

	# Construct Variant dcids
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name']

	# Construct DiseaseGeneticVariantAssociation dcids
	df['dcid'] = 'bio/' + df['Entity1_dcid'].str[4:] + '_' + df['Entity2_dcid'].str[4:]
	
	# Create a 'name' column by removing the prefix from the 'dcid' column
	df['name'] = df['dcid'].str[4:]

	# Check that there are no illegal characters in the dcids
	df = df.apply(lambda x: check_for_dcid(x),axis=1)

	return df


def format_disease_variant_df2(df, dict_mesh):
	# Filter for relevant associations and variant names
	df = df[ ((df['Entity1_type'] == 'Variant') & (df['Entity2_type'] == 'Disease'))].copy()
	
	# Filter for GeneticVariants whose names are rsIDs
	df = df[df['Entity1_name'].str.startswith(('rs'))]
	
	# Query and map Disease PharmGKB Ids to MeSH Descriptor dcids
	mesh_dict = query_mesh_terms(df, 'Entity2_name', MESH_MAPPING_DICT, dict_mesh)
	df['Entity2_dcid'] = df['Entity2_name'].map(mesh_dict)
	df = df[df['Entity2_dcid'].notna()]

	# Construct Variant dcids
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name']

	# Construct DiseaseGeneticVariantAssociation dcids
	df['dcid'] = 'bio/' + df['Entity2_dcid'].str[4:] + '_' + df['Entity1_dcid'].str[4:]
	
	# Create a 'name' column by removing the prefix from the 'dcid' column
	df['name'] = df['dcid'].str[4:]
	
	# swap the column mappings so that the info corresponds to the disease as entity1 and variant as entity2
	df = col_swap(df)
	
	# Check that there are no illegal characters in the dcids
	df = df.apply(lambda x: check_for_dcid(x),axis=1)

	return df


def combined_disease_variant(df, dict_mesh):
	"""
    This function combines and formats disease-variant associations.

    Args:
        df (pd.DataFrame): The input DataFrame containing disease-variant associations.
        dict_mesh (dict): A dictionary for mapping MeSH terms.

    Returns:
        None: This function saves the combined and formatted DataFrame to a CSV file.
    """
    # Format disease-variant associations from two different formattings (disease entity1 and variant entity1)
	df_disease_var1 = format_disease_variant_df1(df, dict_mesh)
	df_disease_var2 = format_disease_variant_df2(df, dict_mesh)

	# Combine the two formatted DataFrames
	df = pd.concat([df_disease_var1, df_disease_var2], axis=0)

	# Prepend the Evidence and Association columns of type enum
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)

	# Save the combined and formatted DataFrame to a CSV file
	df = df.drop_duplicates()
	df.to_csv('CSVs/disease_var.csv', doublequote=False, escapechar='\\', index=False)

	return


def format_disease_gene_df1(df, dict_mesh):
	"""
    Formats the first DataFrame containing disease-gene associations for Data Commons (disease as Entity1).

    Args:
        df (pd.DataFrame): The input DataFrame with disease-gene associations.
        dict_mesh (dict): A dictionary for mapping MeSH terms.

    Returns:
        pd.DataFrame: The formatted DataFrame.
    """
    # Filter for rows where Entity1 is Disease and Entity2 is Gene
	df = df[ ((df['Entity1_type'] == 'Disease') & (df['Entity2_type'] == 'Gene'))].copy()
	
	# Query and map Disease PharmGKB Ids to MeSH Descriptor dcids
	mesh_dict = query_mesh_terms(df, 'Entity1_name', MESH_MAPPING_DICT, dict_mesh)
	df['Entity1_dcid'] = df['Entity1_name'].map(mesh_dict)
	df = df[df['Entity1_dcid'].notna()]
	
	# Construct Gene dcids
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name']

	# Construct DiseaseGeneAssociation dcids
	df['dcid'] = 'bio/' + df['Entity1_dcid'].str[4:] + '_' + df['Entity2_dcid'].str[4:]
	
	# Create a 'name' column by removing the prefix from the 'dcid' column
	df['name'] = df['dcid'].str[4:]
	
	# Check that there are no illegal characters in the dcids
	df = df.apply(lambda x: check_for_dcid(x),axis=1)

	return df


def format_disease_gene_df2(df, dict_mesh):
	"""
    Formats the second DataFrame containing disease-gene associations for Data Commons (gene as Entity1).

    Args:
        df (pd.DataFrame): The input DataFrame with disease-gene associations.
        dict_mesh (dict): A dictionary for mapping MeSH terms.

    Returns:
        pd.DataFrame: The formatted DataFrame.
    """
	# Filter for rows where Entity1 is Gene and Entity2 is Disease
	df = df[ ((df['Entity1_type'] == 'Gene') & (df['Entity2_type'] == 'Disease'))].copy()
	
	# Query and map Disease PharmGKB Ids to MeSH Descriptor dcids
	mesh_dict = query_mesh_terms(df, 'Entity2_name', MESH_MAPPING_DICT, dict_mesh)
	df['Entity2_dcid'] = df['Entity2_name'].map(mesh_dict)
	df = df[df['Entity2_dcid'].notna()]
	
	# Construct Gene dcids
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name']

	# Construct DiseaseGeneAssociation dcids
	df['dcid'] = 'bio/' + df['Entity2_dcid'].str[4:] + '_' + df['Entity1_dcid'].str[4:]
	
	# Create a 'name' column by removing the prefix from the 'dcid' column
	df['name'] = df['dcid'].str[4:]

	# swap the column mappings so that the info corresponds to the disease as entity1 and gene as entity2
	df = col_swap(df)
	
	# Check that there are no illegal characters in the dcids
	df = df.apply(lambda x: check_for_dcid(x),axis=1)

	return df


def combined_disease_gene(df, dict_mesh):
	"""
    This function combines and formats disease-gene associations from two DataFrames for Data Commons.

    Args:
        df (pd.DataFrame): The input DataFrame containing disease-gene associations.
        dict_mesh (dict): A dictionary containing manual mappings between PharmGKB Ids and Mesh Descriptor dcids.

    Returns:
        None: This function saves the combined and formatted DataFrame to a CSV file.
    """
    # Format disease-gene associations from two different formattings (disease entity1 and gene entity1)
	df_disease_gene1 = format_disease_gene_df1(df, dict_mesh)
	df_disease_gene2 = format_disease_gene_df2(df, dict_mesh)

	# Combine the two formatted DataFrames
	df = pd.concat([df_disease_gene1, df_disease_gene2], axis=0)
	# df = df[df['dcid'].notna()]  # drop rows missing dcid
	
	# Prepend the Evidence and Association columns of type enum
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)

	# Save the combined and formatted DataFrame to a CSV file
	df = df.drop_duplicates()
	df.to_csv('CSVs/disease_gene.csv', doublequote=False, escapechar='\\', index=False)
	
	return


def lookup_dcid(df, col, col_new, dict_lookup):
	"""
    This function looks up DCIDs in a dictionary based on values in a specific column of a DataFrame, 
    and adds a new column with the corresponding DCIDs.

    Args:
        df (pd.DataFrame): The input DataFrame containing the column to use for the lookup.
        col (str): The name of the column in the DataFrame containing the values to look up.
        col_new (str): The name of the new column to be added to the DataFrame, which will contain the looked-up DCIDs.
        dict_lookup (dict): A dictionary mapping values from the `col` column to their corresponding DCIDs.

    Returns:
        pd.DataFrame: The modified DataFrame with the new `col_new` column containing the looked-up DCIDs.
    """
	d = {col_new: []}  # initialize dictionary to store looked up values

    # Iterate over each row in the DataFrame
	for index, row in df.iterrows():
		item = row[col]  # Get the value from the specified column
		dcid = dict_lookup[item]  # Look up the DCID in the dictionary
		d[col_new].append(dcid)  # Add the DCID to the dictionary
    # Add the new column to the DataFrame using the looked-up DCIDs
	df[col_new] = d[col_new]

	return df


def format_chemical_gene_df1(df, df_dict):
	"""
        Formats the first DataFrame containing chemical compund-gene associations for Data Commons (chemical as Entity1).

    Args:
        df (pd.DataFrame): The input DataFrame containing chemical compound-gene associations.
        df_dict (dict): A dictionary containing mappings between PharmGKB Ids and ChemicalCompound dcids.

    Returns:
        d.DataFrame: The formatted DataFrame.
    """
	# Filter for rows where Entity1 is Chemical Compound and Entity2 is Gene
	df = df[ ((df['Entity1_type'] == 'Chemical') & (df['Entity2_type'] == 'Gene'))].copy()
	
	# Create a dictionary to map PharmGKBIDs to their corresponding DCIDs
	dict_lookup = dict(zip(df_dict['pharmGKBID'], df_dict['dcid']))
	
	# Look up DCIDs for Entity1 based on the mapping dictionary
	df = lookup_dcid(df, 'Entity1_id', 'Entity1_dcid', dict_lookup)
	
	# Construct Gene dcids
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name']
	
	# Construct ChemicalCompoundGeneAssociation dcids
	df['dcid'] = 'chem/' + df['Entity1_dcid'].str[5:] + '_' + df['Entity2_name']
	
	# Create a 'name' column by removing the prefix from the 'dcid' column
	df['name'] = df['dcid'].str[5:]

	# Check that there were no illegal characters in the dcids
	df = df.apply(lambda x: check_for_dcid(x),axis=1)
	return df


def format_chemical_gene_df2(df, df_dict):
	"""
        Formats the second DataFrame containing chemical compund-gene associations for Data Commons (gene as Entity1).

    Args:
        df (pd.DataFrame): The input DataFrame containing chemical compound-gene associations.
        df_dict (dict): A dictionary containing mappings between PharmGKB Ids and ChemicalCompound dcids.

    Returns:
        d.DataFrame: The formatted DataFrame.
    """
	# Filter for rows where Entity1 is Gene and Entity2 is Chemical Compound
	df = df[ ((df['Entity2_type'] == 'Chemical') & (df['Entity1_type'] == 'Gene'))].copy()
	
	# Create a dictionary to map PharmGKBIDs to their corresponding DCIDs
	dict_lookup = dict(zip(df_dict['pharmGKBID'], df_dict['dcid']))
	
	# Look up DCIDs for Entity2 based on the mapping dictionary
	df = lookup_dcid(df, 'Entity2_id', 'Entity2_dcid', dict_lookup)
	
	# Construct Gene dcids
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name']
	
	# Construct ChemicalCompoundGeneAssociation dcids
	df['dcid'] = 'chem/' + df['Entity2_dcid'].str[5:] + '_' + df['Entity1_name']
	
	# Create a 'name' column by removing the prefix from the 'dcid' column
	df['name'] = df['dcid'].str[9:]

	# Check that there were no illegal characters in the dcids
	df = df.apply(lambda x: check_for_dcid(x),axis=1)
	
	# swap the column mappings so that the info corresponds to the ChemicalCompound as entity1 and Gene as entity2
	df = col_swap(df)

	return df


def combined_chemical_gene(df, df_dict):
	"""
    This function combines and formats chemical compound-gene associations from two DataFrames for Data Commons.

    Args:
        df (pd.DataFrame): The input DataFrame containing chemical compound-gene associations.
        df_dict (dict): A dictionary containing mappings between PharmGKB Ids and ChemicalCompound dcids.

    Returns:
        None: This function saves the combined and formatted DataFrame to a CSV file.
    """
    # Format chemical compound-gene associations from two different formattings (chemical entity1 and gene entity1)
	df_chem_gene1 = format_chemical_gene_df1(df, df_dict)
	df_chem_gene2 = format_chemical_gene_df2(df, df_dict)
	
	# Combine two formatted dataframes
	df = pd.concat([df_chem_gene1, df_chem_gene2], axis=0)

	# Prepend the Evidence and Association columns of type enum
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)

	# Save the combined and formatted DataFrame to a CSV file
	df = df.drop_duplicates()
	df.to_csv('CSVs/chem_gene.csv', doublequote=False, escapechar='\\', index=False)

	return


def format_gene_variant_df1(df):
	"""
    Formats the first DataFrame containing gene-genetic variant associations for Data Commons (gene as Entity1).

    Args:
        df (pd.DataFrame): The input DataFrame containing chemical compound-gene associations.

    Returns:
        d.DataFrame: The formatted DataFrame.
    """
	# Filter for rows where Entity1 is Gene and Entity2 is GeneticVariant
	df = df[ ((df['Entity1_type'] == 'Variant') & (df['Entity2_type'] == 'Gene'))].copy()
	
	# Filter for GeneticVariants whose names are rsIDs
	df = df[df['Entity1_name'].str.startswith(('rs'))]
	
	# Construct the Gene and GeneticVariant dcids
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name']
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name']
	
	# Construct the GeneGeneticVariantAssociation dcids
	df['dcid'] = 'bio/' + df['Entity2_name'] + '_' + df['Entity1_name']
	
	# Create a 'name' column by removing the prefix from the 'dcid' column
	df['name'] = df['dcid'].str[4:]
	
	# Check that there are no illegal characters in the dcid
	df = df.apply(lambda x: check_for_dcid(x),axis=1)
	return df


def format_gene_variant_df2(df):
	"""
    Formats the second DataFrame containing gene-genetic variant associations for Data Commons (variant as Entity1).

    Args:
        df (pd.DataFrame): The input DataFrame containing chemical compound-gene associations.

    Returns:
        d.DataFrame: The formatted DataFrame.
    """
	# Filter for rows where Entity1 is GeneticVariant and Entity2 is Gene
	df = df[ ((df['Entity2_type'] == 'Variant') & (df['Entity1_type'] == 'Gene'))].copy()
	
	# Filter for GeneticVariants whose names are rsIDs
	df = df[df['Entity2_name'].str.startswith(('rs'))]
	
	# Construct the Gene and GeneticVariant dcids
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name']
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name']

	# Construct the GeneGeneticVariantAssociation dcids
	df['dcid'] = 'bio/' + df['Entity1_name'] + '_' + df['Entity2_name']
	
	# Create a 'name' column by removing the prefix from the 'dcid' column
	df['name'] = df['dcid'].str[4:]
	
	# Check that there are no illegal characters in the dcid
	df = df.apply(lambda x: check_for_dcid(x),axis=1)

	# swap the column mappings so that the info corresponds to the Gene as entity1 and GeneticVariant as entity2
	df = col_swap(df)
	return df


def combined_gene_variant(df):
	"""
    This function combines and formats gene-genetic variant associations from two DataFrames for Data Commons.

    Args:
        df (pd.DataFrame): The input DataFrame containing gene-genetic variant associations.

    Returns:
        None: This function saves the combined and formatted DataFrame to a CSV file.
    """
    # Format gene-genetic variant associations from two different formattings (gene entity1 and variant entity1)
	df_gene_var1 = format_gene_variant_df1(df)
	df_gene_var2 = format_gene_variant_df2(df)
	
	# Combine two formatted dataframes
	df = pd.concat([df_gene_var1, df_gene_var2], axis=0)

	# Prepend the Evidence and Association columns of type enum
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)
	
	# Save the combined and formatted DataFrame to a CSV file
	df = df.drop_duplicates()
	df.to_csv('CSVs/gene_var.csv', doublequote=False, escapechar='\\', index=False)

	return


def format_chemical_variant_df1(df, df_dict):
	"""
      Formats the first DataFrame containing chemical compund-genetic variant associations for Data Commons (gene as Entity1).

    Args:
        df (pd.DataFrame): The input DataFrame containing chemical compound-genetic variant associations.
        df_dict (dict): A dictionary containing mappings between PharmGKB Ids and ChemicalCompound dcids.

    Returns:
        d.DataFrame: The formatted DataFrame.
    """
	# Filter for rows where Entity1 is ChemicalCompound and Entity2 is GeneticVariant
	df = df[ ((df['Entity1_type'] == 'Chemical') & (df['Entity2_type'] == 'Variant'))].copy()
	
	# Filter for GeneticVariants whose names are rsIDs
	df = df[df['Entity2_name'].str.startswith(('rs'))]
	
	# Create a dictionary to map PharmGKBIDs to their corresponding DCIDs
	dict_lookup = dict(zip(df_dict['pharmGKBID'], df_dict['dcid']))
	
	# Look up DCIDs for Entity2 based on the mapping dictionary
	df = lookup_dcid(df, 'Entity1_id', 'Entity1_dcid', dict_lookup)

	# Construct GeneticVariant dcids
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name']

	# Construct the ChemicalCompoundGeneticVariantAssociation dcids
	df['dcid'] = 'chem/' + df['Entity1_dcid'].str[5:] + '_' + df['Entity2_name']
	
	# Create a 'name' column by removing the prefix from the 'dcid' column
	df['name'] = df['dcid'].str[5:]

	# Check that the dcids don't contain any illegal characters
	df = df.apply(lambda x: check_for_dcid(x),axis=1)

	return df


def format_chemical_variant_df2(df, df_dict):
	"""
       Formats the second DataFrame containing chemical compund-genetic variant associations for Data Commons (variant as Entity1).

    Args:
        df (pd.DataFrame): The input DataFrame containing chemical compound-genetic variant associations.
        df_dict (dict): A dictionary containing mappings between PharmGKB Ids and ChemicalCompound dcids.

    Returns:
        d.DataFrame: The formatted DataFrame.
    """
	# Filter for rows where Entity1 is Genetic Variant and Entity2 is Chemical Compound
	df = df[ ((df['Entity1_type'] == 'Variant') & (df['Entity2_type'] == 'Chemical'))].copy()
	
	# Filter for GeneticVariants whose names are rsIDs
	df = df[df['Entity1_name'].str.startswith(('rs'))]

	# Create a dictionary to map PharmGKBIDs to their corresponding DCIDs
	dict_lookup = dict(zip(df_dict['pharmGKBID'], df_dict['dcid']))
	
	# Look up DCIDs for Entity2 based on the mapping dictionary
	df = lookup_dcid(df, 'Entity2_id', 'Entity2_dcid', dict_lookup)

	# Construct GeneticVariant dcids
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name']
	
	# Construct the ChemicalCompoundGeneticVariantAssociation dcids
	df['dcid'] = 'chem/' + df['Entity2_dcid'].str[5:] + '_' + df['Entity1_name']
	
	# Create a 'name' column by removing the prefix from the 'dcid' column
	df['name'] = df['dcid'].str[5:]
	
	# Check that the dcids don't contain any illegal characters
	df = df.apply(lambda x: check_for_dcid(x),axis=1)
	
	# swap the column mappings so that the info corresponds to the Chemical Compound as entity1 and GeneticVariant as entity2
	df = col_swap(df)
	
	return df


def combined_chemical_variant(df, df_dict):
	"""
    This function combines and formats chemical compound-genetic variant associations from two DataFrames for Data Commons.

    Args:
        df (pd.DataFrame): The input DataFrame containing chemical compound-genetic variant associations.
        df_dict (dict): A dictionary containing mappings between PharmGKB Ids and ChemicalCompound dcids.

    Returns:
        None: This function saves the combined and formatted DataFrame to a CSV file.
    """
    # Format chemical compound-genetic variant associations from two different formattings (chemical entity1 and variant entity1)
	df_chem_var1 = format_chemical_variant_df1(df, df_dict)
	df_chem_var2 = format_chemical_variant_df2(df, df_dict)
	
	# Combine two formatted dataframes
	df = pd.concat([df_chem_var1, df_chem_var2], axis=0)
	
	# Prepend the Evidence and Association columns of type enum
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)
	
	# Save the combined and formatted DataFrame to a CSV file
	df = df.drop_duplicates()
	df.to_csv('CSVs/chem_var.csv', doublequote=False, escapechar='\\', index=False)

	return



def alphabetically_sort_two_items(item1, item2):
	"""
    This function sorts two items alphabetically.

    Args:
        item1 (str): The first item to be sorted.
        item2 (str): The second item to be sorted.

    Returns:
        tuple: A tuple containing the alphabetically sorted items.
    """
	sorted_items = sorted([item1, item2])
	i1 = sorted_items[0]
	i2 = sorted_items[1]
	return i1, i2


def determine_prefix(prefix_index):
	"""
    This function determines the prefix based on the integer representing a given prefix index.

    Args:
        prefix_index (int): The index of the prefix.

    Returns:
        str: The corresponding prefix.
    """
	if prefix_index == 4:
		return 'bio/'
	if prefix_index == 5:
		return 'chem/'
	print('Error! This prefix is not supported. There is no known prefix of', str(prefix_index), 'length')
	return


def format_same_association_dcid(df, prefix_index=4):
	"""
    This function formats DCIDs for associations based on the alphabetical order of entity DCIDs.

    Args:
        df (pd.DataFrame): The input DataFrame containing 'Entity1_dcid' and 'Entity2_dcid' columns.
        prefix_index (int, optional): The index where the prefix of entity DCIDs ends (default is 4).

    Returns:
        pd.DataFrame: The modified DataFrame with a new 'dcid' column containing formatted association DCIDs.
    """
	d = {'dcid': []}
	for index, row in df.iterrows():
	    # Extract DCIDs for each entity from the row and remove the prefix
		dcid1 = row['Entity1_dcid'][prefix_index:]
		dcid2 = row['Entity2_dcid'][prefix_index:]
		
		# Determine the correct dcid prefix based on the provided index
		prefix = determine_prefix(prefix_index)
		
		# Sort the DCIDs alphabetically
		part1, part2 = alphabetically_sort_two_items(dcid1, dcid2)
		
		# format dcid as prefix plus the alphabetically sorted entity dcids
		dcid_association = prefix + part1 + '_' + part2
		d['dcid'].append(dcid_association)  # Add the formatted DCID to the dictionary
	
	df['dcid'] = d['dcid'] # add dcid column to df
	df = df.apply(lambda x: check_for_dcid(x),axis=1)  # Check for invalid characters in DCIDs

	return df.drop_duplicates()


def format_chemical_chemical_df(df, df_dict):
    """
    This function formats a DataFrame containing chemical-chemical associations for Data Commons.

    Args:
        df (pd.DataFrame): The input DataFrame with chemical-chemical associations.
        df_dict (pd.DataFrame): A DataFrame for looking up DCIDs for chemical entities.

    Returns:
        None: This function saves the formatted DataFrame to a CSV file.
    """
    # Set the prefix index to 5 to indicate use of 'chem' prefix for dcids
    prefix_index = 5

	# Filter for rows where both entities are chemicals
    df = df[ (df['Entity1_type'] == 'Chemical') & (df['Entity2_type'] == 'Chemical')].copy()

	# Create a dictionary to map PharmGKBIDs to their corresponding DCIDs
    dict_lookup = dict(zip(df_dict['pharmGKBID'], df_dict['dcid']))

	# Look up DCIDs for Entity1 and Entity2 based on the mapping dictionary
    df = lookup_dcid(df, 'Entity1_id', 'Entity1_dcid', dict_lookup)
    df = lookup_dcid(df, 'Entity2_id', 'Entity2_dcid', dict_lookup)

	# Format association DCIDs based on alphabetical order
    df = format_same_association_dcid(df, prefix_index=prefix_index)

	# Create a 'name' column by removing the prefix from the 'dcid' column
    df['name'] = df['dcid'].str[5:]

	# Convert Evidence and Association columns to enums
    df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
    df['Association'] = df['Association'].map(ASSOCIATION_DICT)

	# Save the formatted DataFrame to a CSV file
    df = df.drop_duplicates()
    df.to_csv('CSVs/chem_chem.csv', doublequote=False, escapechar='\\', index=False)

    return


def format_disease_disease_df(df, dict_mesh):
	"""
    This function formats a DataFrame containing disease-disease associations for Data Commons.

    Args:
        df (pd.DataFrame): The input DataFrame with disease-disease associations.
        dict_mesh (dict): A dictionary of manual mapping between PharmGKB Ids and MeSH Descriptor DCIDs.

    Returns:
        pd.DataFrame: The formatted DataFrame ready for Data Commons ingestion.
    """
    # Filter for rows where both entities are diseases
	df = df[ (df['Entity1_type'] == 'Disease') & (df['Entity2_type'] == 'Disease')].copy()
	
	# Query and map PharmGKB Ids to MeSH Descriptor dcids for Entity1
	mesh_dict = query_mesh_terms(df, 'Entity1_name', MESH_MAPPING_DICT, dict_mesh)
	df['Entity1_dcid'] = df['Entity1_name'].map(mesh_dict).astype(str)
	df = update_missing_mesh_ids(df, 'Entity1_id', 'Entity1_dcid', dict_mesh)
	
	# Query and map PharmGKB Ids to MeSH Descriptor dcids for Entity2
	mesh_dict = query_mesh_terms(df, 'Entity2_name', MESH_MAPPING_DICT, dict_mesh)
	df['Entity2_dcid'] = df['Entity2_name'].map(mesh_dict).astype(str)
	df = update_missing_mesh_ids(df, 'Entity2_id', 'Entity2_dcid', dict_mesh)
	
	# Format association DCIDs based on alphabetical order
	df = format_same_association_dcid(df)
	# Create a 'name' column by removing the prefix from the 'dcid' column
	df['name'] = df['dcid'].str[4:]

	# Convert Evidence and Association columns to enums
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)

	# Save the formatted DataFrame to a CSV file
	df = df.drop_duplicates()
	df.to_csv('CSVs/disease_disease.csv', doublequote=False, escapechar='\\', index=False)

	return df


def format_gene_gene_df(df):
    """
    This function formats a DataFrame containing gene-gene associations for Data Commons.

    Args:
        df (pd.DataFrame): The input DataFrame with gene-gene associations.

    Returns:
        None: This function saves the formatted DataFrame to a CSV file.
    """
    # Filter for rows where both entities are genes
    df = df[(df['Entity1_type'] == 'Gene') & (df['Entity2_type'] == 'Gene')].copy()

    # Add the 'bio/' prefix to the gene names to create DCIDs
    df['Entity1_dcid'] = 'bio/' + df['Entity1_name'].astype(str)
    df['Entity2_dcid'] = 'bio/' + df['Entity2_name'].astype(str)
	
	# Format association DCIDs based on alphabetical order
    df = format_same_association_dcid(df)

	# Create a 'name' column by removing the 'bio/' prefix from the 'dcid' column
    df['name'] = df['dcid'].str[4:]

	# Convert 'Evidence' and 'Association' to Enums
    df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
    df['Association'] = df['Association'].map(ASSOCIATION_DICT)

	# Save the formatted DataFrame to a CSV file
    df = df.drop_duplicates()
    df.to_csv('CSVs/gene_gene.csv', doublequote=False, escapechar='\\', index=False)

    return


def format_var_var_df(df):
	"""
    This function formats a DataFrame containing variant-variant associations for Data Commons.

    Args:
        df (pd.DataFrame): The input DataFrame with variant-variant associations.

    Returns:
        None: This function saves the formatted DataFrame to a CSV file.
    """
	# Filter for rows where both entities are variants
	df = df[ ((df['Entity1_type'] == 'Variant') & (df['Entity2_type'] == 'Variant'))].copy()
	
	# # Filter for GeneticVariants whose names are rsIDs
	df = df[df['Entity1_name'].str.startswith(('rs'))]
	df = df[df['Entity2_name'].str.startswith(('rs'))]
	
	# Format association DCIDs based on alphabetical order
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name'].astype(str)
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name'].astype(str)
	
	# Add the 'bio/' prefix to the gene names to create DCIDs
	df = format_same_association_dcid(df)
	
	# Create a 'name' column by removing the 'bio/' prefix from the 'dcid' column
	df['name'] = df['dcid'].str[4:]
	
	# Convert 'Evidence' and 'Association' to Enums
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)

	# Save the formatted DataFrame to a CSV file
	df = df.drop_duplicates()
	df.to_csv('CSVs/var_var.csv', doublequote=False, escapechar='\\', index=False)

	return


def convert_csv_to_dict(df, k, v):
	"""
    Converts a DataFrame into a dictionary, mapping values from one column to another.

    Args:
        df (pd.DataFrame): The input DataFrame.
        k (str): The column name to use as keys in the dictionary.
        v (str): The column name to use as values in the dictionary.

    Returns:
        dict: A dictionary where keys are from `k` and values are from `v`.
    """
	d = {}
	for index, row in df.iterrows():
		d[row[k]] = row[v]
	return d


def wrapper_fun(df, df_chem, df_mesh):
    """
    This function acts as a wrapper to orchestrate the formatting and processing of different types of biomedical associations.

    Args:
        df (pd.DataFrame): The main input DataFrame containing association data.
        df_chem (pd.DataFrame): DataFrame containing chemical mapping data.
        df_mesh (pd.DataFrame): DataFrame containing MeSH term mappings.

    Returns:
        None: This function writes the formatted results to CSV files.
    """
    # Convert the MeSH mapping CSV into a dictionary
    dict_mesh = convert_csv_to_dict(df_mesh, 'PharmGkbID', 'mesh_dcid')

    # Filter and clean the main DataFrame
    df = choose_data_subset(df)
    df = format_multivalue_cols(df)
    df = format_enums(df)
    df = df.replace(r'[^0-9a-zA-Z ]', '', regex=True).replace("'", '')  # Remove special characters

    # Format and process various types of associations
    # Process associations of different entity types
    combined_chemical_gene(df, df_chem)       # Process chemical-gene associations
    combined_chemical_variant(df, df_chem)    # Process chemical-variant associations
    combined_disease_variant(df, dict_mesh)   # Process disease-variant associations
    combined_disease_gene(df, dict_mesh)      # Process disease-gene associations
    combined_gene_variant(df)        		  # Process gene-variant associations
    
    # process associations of the same entity type
    format_chemical_chemical_df(df, df_chem)  # Process chemical-chemical associations
    format_gene_gene_df(df)                   # Process gene-gene associations
    format_var_var_df(df)                     # Process variant-variant associations
    format_disease_disease_df(df, dict_mesh)  # Process disease-disease associations

    return



def main():
    """
    The main function to read input files, initialize data, and call the wrapper function.
    """
    # Get file paths from command line arguments
    file_input = sys.argv[1]
    file_chem_mapping = sys.argv[2]
    file_drug_mapping = sys.argv[3]
    file_mesh_mapping = sys.argv[4]

    # Read the main input file and chemical mapping files
    df = pd.read_csv(file_input, sep='\t')
    df_chem1 = pd.read_csv(file_chem_mapping)
    df_chem2 = pd.read_csv(file_drug_mapping)
    df_chem = df_chem1._append(df_chem2)  # Combine the two chemical mapping DataFrames

    # Read the MeSH mapping file
    df_mesh = pd.read_csv(file_mesh_mapping)

    # Call the wrapper function to process all the associations
    wrapper_fun(df, df_chem, df_mesh)


if __name__ == '__main__':
	main()
