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
Name: format_relationships
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

def choose_data_subset(df):
	df['sorted'] = df.apply(lambda x: ''.join(sorted([x['Entity1_id'],x['Entity2_id']])),axis=1)
	df = df.drop_duplicates(subset='sorted').drop('sorted',axis=1)
	df = df[ (df['Entity1_type'] != 'Haplotype') & (df['Entity2_type'] != 'Haplotype')]
	return df

def format_multivalue_cols(df):
	df = df.assign(Evidence=df.Evidence.str.split(",")).explode('Evidence')
	df = df.assign(PMIDs=df.PMIDs.str.split(";")).explode('PMIDs')
	return df

def format_enums(df):
	df['PK'] = np.where(df['PK'] == 'PK', 'True', 'False')
	df['PD'] = np.where(df['PD'] == 'PD', 'True', 'False')
	return df

def col_swap(df):
	df.rename({"Entity1_id": "Entity2_id", 
		   "Entity2_id": "Entity1_id", 
		   "Entity1_name": "Entity2_name",
		   "Entity2_name": "Entity1_name",
		   "Entity1_dcid": "Entity2_dcid", 
		   "Entity2_dcid": "Entity1_dcid",}, 
		  axis = "columns", inplace = True)
	return df

def query_mesh_terms(df, col_name, dict_mesh_terms):
    df[col_name] = df[col_name].str.title()
    list_names = list(df[col_name].unique())
    arr_name = np.array(list_names)
    query_str = """
    SELECT DISTINCT ?dcid ?name
    WHERE {{
    ?a typeOf MeSHDescriptor .
    ?a name {value} .
    ?a dcid ?dcid .
    ?a name ?name
    }}
    """.format(value=arr_name)
    result = dc.query(query_str)
    result = pd.DataFrame(result)
    dict_terms = dict(zip(result['?name'], result['?dcid']))
    dict_mesh_terms = dict_mesh_terms | dict_terms
    return dict_mesh_terms

def format_disease_disease_df(df):
	df = df[ (df['Entity1_type'] == 'Disease') & (df['Entity2_type'] == 'Disease')]
	mesh_dict = query_mesh_terms(df, 'Entity1_name', MESH_MAPPING_DICT)
	df['Entity1_dcid'] = df['Entity1_name'].map(mesh_dict)
	mesh_dict = query_mesh_terms(df, 'Entity2_name', MESH_MAPPING_DICT)
	df['Entity2_dcid'] = df['Entity2_name'].map(mesh_dict)
	df['dcid'] = 'bio/DDA_' + df['Entity1_dcid'].str[4:] + '_' + df['Entity2_dcid'].str[4:]
	df['name'] = df['dcid'].str[8:]
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)
	df.to_csv('disease_disease_assoc.csv', doublequote=False, escapechar='\\')
	return df

def format_disease_variant_df1(df):
	df = df[ ((df['Entity1_type'] == 'Disease') & (df['Entity2_type'] == 'Variant'))]
	df = df[df['Entity2_name'].str.startswith(('rs'))]
	mesh_dict = query_mesh_terms(df, 'Entity1_name', MESH_MAPPING_DICT)
	df['Entity1_dcid'] = df['Entity1_name'].map(mesh_dict)
	df = df[df['Entity1_dcid'].notna()]
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name']
	df['dcid'] = 'bio/DGVA_' + df['Entity1_dcid'].str[4:] + '_' + df['Entity2_dcid'].str[4:]
	df['name'] = df['dcid'].str[9:]
	return df

def format_disease_variant_df2(df):
	df = df[ ((df['Entity1_type'] == 'Variant') & (df['Entity2_type'] == 'Disease'))]
	df = df[df['Entity1_name'].str.startswith(('rs'))]
	mesh_dict = query_mesh_terms(df, 'Entity2_name', MESH_MAPPING_DICT)
	df['Entity2_dcid'] = df['Entity2_name'].map(mesh_dict)
	df = df[df['Entity2_dcid'].notna()]
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name']
	df['dcid'] = 'bio/DGVA_' + df['Entity2_dcid'].str[4:] + '_' + df['Entity1_dcid'].str[4:]
	df['name'] = df['dcid'].str[9:]
	df = col_swap(df)
	return df

def combined_disease_variant(df):
	df_disease_var1 = format_disease_variant_df1(df)
	df_disease_var2 = format_disease_variant_df2(df)
	df = pd.concat([df_disease_var1, df_disease_var2], axis=0)
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)
	df.to_csv('disease_var_assoc.csv', doublequote=False, escapechar='\\')

def format_disease_gene_df1(df):
	df = df[ ((df['Entity1_type'] == 'Disease') & (df['Entity2_type'] == 'Gene'))]
	mesh_dict = query_mesh_terms(df, 'Entity1_name', MESH_MAPPING_DICT)
	df['Entity1_dcid'] = df['Entity1_name'].map(mesh_dict)
	df = df[df['Entity1_dcid'].notna()]
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name']
	df['dcid'] = 'bio/DGA_' + df['Entity1_dcid'].str[4:] + '_' + df['Entity2_dcid'].str[4:]
	df['name'] = df['dcid'].str[8:]
	return df

def format_disease_gene_df2(df):
	df = df[ ((df['Entity1_type'] == 'Gene') & (df['Entity2_type'] == 'Disease'))]
	mesh_dict = query_mesh_terms(df, 'Entity2_name', MESH_MAPPING_DICT)
	df['Entity2_dcid'] = df['Entity2_name'].map(mesh_dict)
	df = df[df['Entity2_dcid'].notna()]
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name']
	df['dcid'] = 'bio/DGA_' + df['Entity2_dcid'].str[4:] + '_' + df['Entity1_dcid'].str[4:]
	df['name'] = df['dcid'].str[8:]
	df = col_swap(df)
	return df

def combined_disease_gene(df):
	df_disease_gene1 = format_disease_gene_df1(df)
	df_disease_gene2 = format_disease_gene_df2(df)
	df = pd.concat([df_disease_gene1, df_disease_gene2], axis=0)
	df = df[df['dcid'].notna()]
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)
	df.to_csv('disease_gene_assoc.csv', doublequote=False, escapechar='\\')

def format_chemical_names(row):
	entity_1 = row['Entity1_dcid'][5:]
	entity_2 = row['Entity2_dcid'][5:]
	if (('CID' in entity_1) & ('CID' in entity_2)):
		check_num1 = entity_1[3]
		check_num2 = entity_2[3]
		if (check_num1 < check_num2):
			row['dcid'] = 'chem/CCA_' + (row['Entity1_dcid'])[5:] + '_' + (row['Entity2_dcid'])[5:]
			return row
		elif (check_num1 > check_num2):
			row['dcid'] = 'chem/CCA_' + (row['Entity2_dcid'])[5:] + '_' + (row['Entity1_dcid'])[5:]
			return row
	else:
		row['dcid'] = 'chem/CCA_' + min((row['Entity1_dcid'])[5:], (row['Entity2_dcid'])[5:]) + '_' + max((row['Entity1_dcid'])[5:], (row['Entity2_dcid'])[5:])
		return row

def format_variant_names(row):
	entity_1 = (row['Entity1_dcid'])[5:] 
	entity_2 = (row['Entity2_dcid'])[5:]
	counter = 0
	check_flag = False
	while (check_flag == False):
		if (entity_1[counter] < entity_2[counter]):
			row['dcid'] = 'bio/GVGVA_' + (row['Entity1_dcid'])[4:] + '_' + (row['Entity2_dcid'])[4:]
			return row
		if (entity_1[counter] > entity_2[counter]):
			row['dcid'] = 'bio/GVGVA_' + (row['Entity2_dcid'])[4:] + '_' + (row['Entity1_dcid'])[4:]
			return row
		counter = counter + 1


def format_chemical_chemical_df(df, df_dict):
	df1 = pd.read_csv('drugs_pkgb_dict.csv')
	df2 = pd.read_csv('chemicals_pkgb_dict.csv')
	df_dict = df1.append(df2)
	df = df[ (df['Entity1_type'] == 'Chemical') & (df['Entity2_type'] == 'Chemical')]
	key_list_1 = list(df['Entity1_id'])
	key_list_2 = list(df['Entity2_id'])
	dict_lookup = dict(zip(df_dict['pharmGKBID'], df_dict['dcid']))
	df['Entity1_dcid'] = [dict_lookup[item] for item in key_list_1]
	df['Entity2_dcid'] = [dict_lookup[item] for item in key_list_2]
	df = df.apply(lambda x: format_chemical_names(x),axis=1)
	df = df.dropna()
	df = df.drop_duplicates()
	df['name'] = df['dcid'].str[9:]
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)
	df.to_csv('chemical_chemical_assoc.csv', doublequote=False, escapechar='\\')

def format_chemical_gene_df1(df, df_dict):
	df = df[ ((df['Entity1_type'] == 'Chemical') & (df['Entity2_type'] == 'Gene'))]
	dict_lookup = dict(zip(df_dict['pharmGKBID'], df_dict['dcid']))
	df['Entity1_dcid'] = df['Entity1_id'].map(dict_lookup)
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name']
	df['dcid'] = 'chem/CGA_' + df['Entity1_dcid'].str[5:] + '_' + df['Entity2_dcid'].str[4:]
	df['name'] = df['dcid'].str[9:]
	return df

def format_chemical_gene_df2(df, df_dict):
	df = df[ ((df['Entity2_type'] == 'Chemical') & (df['Entity1_type'] == 'Gene'))]
	dict_lookup = dict(zip(df_dict['pharmGKBID'], df_dict['dcid']))
	df['Entity2_dcid'] = df['Entity2_id'].map(dict_lookup)
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name']
	df['dcid'] = 'chem/CGA_' + df['Entity2_dcid'].str[5:] + '_' + df['Entity1_dcid'].str[4:]
	df['name'] = df['dcid'].str[9:]
	df = col_swap(df)
	return df

def format_gene_variant_df1(df):
	df = df[ ((df['Entity1_type'] == 'Variant') & (df['Entity2_type'] == 'Gene'))]
	df = df[df['Entity1_name'].str.startswith(('rs'))]
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name']
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name']
	df['dcid'] = 'bio/GGVA_' + df['Entity2_name'] + '_' + df['Entity1_name']
	df['name'] = df['dcid'].str[9:]
	return df

def format_gene_variant_df2(df):
	df = df[ ((df['Entity2_type'] == 'Variant') & (df['Entity1_type'] == 'Gene'))]
	df = df[df['Entity2_name'].str.startswith(('rs'))]
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name']
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name']
	df['dcid'] = 'bio/GGVA_' + df['Entity1_name'] + '_' + df['Entity2_name']
	df['name'] = df['dcid'].str[9:]
	df = col_swap(df)
	return df

def format_chemical_variant_df1(df, df_dict):
	df = df[ ((df['Entity1_type'] == 'Variant') & (df['Entity2_type'] == 'Chemical'))]
	df = df[df['Entity1_name'].str.startswith(('rs'))]
	dict_lookup = dict(zip(df_dict['pharmGKBID'], df_dict['dcid']))
	df['Entity1_name'] = df['Entity1_name'].str.replace(' ', '_')
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name']
	df['Entity2_dcid'] = df['Entity2_id'].astype(str).map(dict_lookup)
	df['dcid'] = 'chem/CGVA_' + df['Entity2_dcid'].str[5:] + '_' + df['Entity1_name']
	df['name'] = df['dcid'].str[10:]
	return df

def format_chemical_variant_df2(df, df_dict):
	df = df[ ((df['Entity2_type'] == 'Variant') & (df['Entity1_type'] == 'Chemical'))]
	df = df[df['Entity2_name'].str.startswith(('rs'))]
	dict_lookup = dict(zip(df_dict['pharmGKBID'], df_dict['dcid']))
	df['Entity2_name'] = df['Entity2_name'].str.replace(' ', '_')
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name']
	df['Entity1_dcid'] = df['Entity1_id'].astype(str).map(dict_lookup)
	df['dcid'] = 'chem/CGVA_' + df['Entity1_dcid'].str[5:] + '_' + df['Entity2_name']
	df['name'] = df['dcid'].str[10:]
	df = col_swap(df)
	return df

def format_gene_gene_df(df):
	df = df[ ((df['Entity1_type'] == 'Gene') & (df['Entity2_type'] == 'Gene'))]
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name']
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name']
	df['dcid'] = 'bio/GGA_' + df['Entity1_name']+ '_' + df['Entity2_name']
	df['name'] = df['dcid'].str[8:]
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)
	df.to_csv('gene_gene_assoc.csv', doublequote=False, escapechar='\\')

def format_var_var_df(df):
	df = df[ ((df['Entity1_type'] == 'Variant') & (df['Entity2_type'] == 'Variant'))]
	df = df[df['Entity1_name'].str.startswith(('rs'))]
	df = df[df['Entity2_name'].str.startswith(('rs'))]
	df['Entity1_dcid'] = 'bio/' + df['Entity1_name']
	df['Entity2_dcid'] = 'bio/' + df['Entity2_name']
	df = df.apply(lambda x: format_variant_names(x),axis=1)
	df = df.dropna()
	df = df.drop_duplicates()
	df['name'] = df['dcid'].str[10:]
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)
	df.to_csv('var_var_assoc.csv', doublequote=False, escapechar='\\')

def combined_chemical_gene(df, df_dict):
	df_chem_gene1 = format_chemical_gene_df1(df, df_dict)
	df_chem_gene2 = format_chemical_gene_df2(df, df_dict)
	df = pd.concat([df_chem_gene1, df_chem_gene2], axis=0)
	df = df[df['dcid'].notna()]
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)
	df.to_csv('chemical_gene_assoc.csv', doublequote=False, escapechar='\\')

def combined_chemical_variant(df, df_dict):
	df_chem_var1 = format_chemical_variant_df1(df, df_dict)
	df_chem_var2 = format_chemical_variant_df2(df, df_dict)
	df = pd.concat([df_chem_var1, df_chem_var2], axis=0)
	df = df[df['dcid'].notna()]
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)
	df.to_csv('chemical_variant_assoc.csv', doublequote=False, escapechar='\\')

def combined_gene_variant(df, df_dict):
	df_gene_var1 = format_gene_variant_df1(df)
	df_gene_var2 = format_gene_variant_df2(df)
	df = pd.concat([df_gene_var1, df_gene_var2], axis=0)
	df = df[df['dcid'].notna()]
	df['Evidence'] = 'dcs:RelationshipEvidenceType' + df['Evidence']
	df['Association'] = df['Association'].map(ASSOCIATION_DICT)
	df.to_csv('gene_variant_assoc.csv', doublequote=False, escapechar='\\')

def wrapper_fun(df, df_dict):
	df = choose_data_subset(df)
	df = format_multivalue_cols(df)
	df = format_enums(df)
	df = df.replace(r'[^0-9a-zA-Z ]', '', regex=True).replace("'", '')
	format_chemical_chemical_df(df, df_dict)
	combined_chemical_gene(df, df_dict)
	combined_gene_variant(df, df_dict)
	combined_chemical_variant(df, df_dict)
	combined_disease_variant(df)
	combined_disease_gene(df)
	format_gene_gene_df(df)
	format_var_var_df(df)
	format_disease_disease_df(df)

def main():
	file_input = sys.argv[1]
	file_dict_drug = sys.argv[2]
	file_dict_chem = sys.argv[3]
	df = pd.read_csv(file_input, sep = '\t')
	df_dict1 = pd.read_csv(file_dict_drug)
	df_dict2 = pd.read_csv(file_dict_chem)
	df_dict = df_dict1.append(df_dict2)
	wrapper_fun(df, df_dict)


if __name__ == '__main__':
	main()
