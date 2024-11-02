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
Last Edited: 10/31/24
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


def filter_for_lowest_ICD10_level(df):
	# initiate values
	indices_to_drop = []
	previous_ICD10 = ''
	previous_gene = ''
	previous_index = -1
	# check if ICD10 code is more specific than previous row for the same gene
	# if it is add the previous ICD10 code index to the list of indices to drop
	for index, row in df.iterrows():
		current_ICD10 = row['ICD10']
		current_gene = row['Gene']
		if current_gene == previous_gene and current_ICD10.startswith(previous_ICD10):
			indices_to_drop.append(previous_index)
		# update reference values
		previous_ICD10 = current_ICD10
		previous_gene = current_gene
		previous_index = index
	# drop rows with less specific ICD10 codes for a given gene
	df.drop(indices_to_drop, axis=0, inplace=True)
	return df


def fix_ICD10_formatting(df, col):
	# if string in specified column is 10 characters or longer
	# add '.' in the 10th position
    mask = df[col].str.len() >= 10
    df.loc[mask, col] = df.loc[mask, col].str[:9] + '.' + df.loc[mask, col].str[9:]
    return df


def format_icd10_code_dcids(df):
	df_doid = df.dropna(subset=['DOID'])  # make a doid specific table
	## filter out ICD-10 codes based on true existence - remove codes like C1, C2 and root
	df['count'] = np.where(df['ICD10'] == df['ICD10'],df['ICD10'].str.split(':'),np.nan)
	df['count'] = np.where(df['count'] == df['count'],df['count'].str[1],np.nan)
	# remove non-existing ICD-10 codes
	df = df[df['count']!='root']
	df.loc[:, 'count'] = df['count'].str.len()
	df = df[df['count'] > 2]
	df = filter_for_lowest_ICD10_level(df)
	# fix ill formatted ICD10 codes
	df = fix_ICD10_formatting(df, 'Disease')
	df = fix_ICD10_formatting(df, 'Disease_Name')
	df = fix_ICD10_formatting(df, 'ICD10')
	# join back with the doid rows
	df_final = pd.concat([df, df_doid]).sort_index()
	return df_final


def format_doid_icd(df):
	df['DOID'] = np.where(df['Disease'].str.contains('DOID'),df['Disease'],np.nan)
	df['ICD10'] = np.where(df['Disease'].str.contains('ICD10'),df['Disease'],np.nan)
	## identify ensemblIDs and set as new column
	df['ensemblID'] = np.where(df['Id'].str.contains('ENSP00000'),df['Id'],np.nan)
	## format icd10 dcids filtering for the most specific ICD10 code
	df = format_icd10_code_dcids(df)
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
    check_for_illegal_charc(str(row['dcid']))
    check_for_illegal_charc(str(row['DOID_dcid']))
    check_for_illegal_charc(str(row['ICD10_dcid']))
    check_for_illegal_charc(str(row['Gene_dcid']))
    return row


def format_disease_gene_cols(df, data_type):
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


def format_RNA_type(df_tm):
	gene_list = ['orf', 'ZNF']
	sno_rna_list = ['sno', 'SNOR', 'SCAR']
	linc_rna_list = ['LINC', 'linc', 'MIR']
	df_tm['RNA_type'] = 'dcs:NonCodingRNATypeLongNonCodingRNA'
	df_tm['RNA_type'] = np.where(df_tm["Gene"].str.contains('|'.join(gene_list)),'Gene', df_tm['RNA_type'])
	df_tm['RNA_type'] = np.where(df_tm["Gene"].str.contains('rRNA'),'dcs:NonCodingRNATypeRibosomalRNA', df_tm['RNA_type'])
	df_tm['RNA_type'] = np.where(df_tm["Gene"].str.contains('|'.join(linc_rna_list)),'dcs:NonCodingRNATypeLongIntergenicNonCodingRNA', df_tm['RNA_type'])
	df_tm['RNA_type'] = np.where(df_tm["Gene"].str.contains('|'.join(sno_rna_list)),'dcs:NonCodingRNATypeSmallNucleolarRNA', df_tm['RNA_type'])
	df_tm['RNA_type'] = np.where(df_tm["Gene"].str.contains('miR'),'dcs:NonCodingRNATypeMicroRNA', df_tm['RNA_type'])
	df_tm['RNA_type'] = np.where(df_tm["Gene"].str.contains('circ'),'dcs:NonCodingRNATypeCircularRNA', df_tm['RNA_type'])
	df_tm['RNA_type'] = np.where(df_tm["Gene"].str.contains('pRNA'),'dcs:NonCodingRNATypePromoterAssociatedRNA', df_tm['RNA_type'])
	return df_tm


def format_dcids(df, data_type):
	df = format_doid_icd(df)
	df = format_disease_gene_cols(df, data_type)
	df = df.apply(lambda x: check_for_dcid(x),axis=1)
	return df 


def format_data_type_specific_info(df, data_type):
	if data_type == 'experiments':
		df['associationType'] = 'dcs:AssociationSourceExperiment'
		df['source-score'] = df['source-score'].str.split('=')
		df['source-score'] = np.where(df['source-score'] == df['source-score'],df['source-score'].str[1],np.nan)
		df.update('"' +
				  df[['Disease_Name', 'score-db']].astype(str) + '"')
	if data_type=='knowledge':
		df['associationType'] = 'dcs:AssociationSourceKnowledge'
		df.update('"' +
				  df[['Disease_Name', 'score-db']].astype(str) + '"')
	if data_type =='textmining':
		df['associationType'] = 'dcs:AssociationSourceTextMining'
		df.update('"' +
				  df[['Disease_Name', 'url']].astype(str) + '"')
	return df


def clean_data(df, data_type):
	df_tm = df
	searchfor = ['ENSP00', 'LINC', 'linc'] ## filter out non coding RNAs
	df = df[df['Id'].str.contains("ENSP00")]
	df = df[~df.Gene.str.contains('|'.join(searchfor))]
	df_tm = df_tm[~df_tm.isin(df)].dropna() ## df with only non coding RNAs
	df_tm = df_tm[~df_tm['Gene'].str.contains("chr")]
	df_tm = df_tm[~df_tm['Gene'].str.contains("ENSP00")]
	df = format_dcids(df, data_type)
	df_tm = format_dcids(df_tm, data_type)
	df_tm = format_RNA_type(df_tm) ## filter out genes from df with non coding RNA
	df_gene = df_tm.loc[df_tm['RNA_type']=='Gene'] ## filter out genes from df with non coding RNA
	df_tm = df_tm[~df_tm['RNA_type'].str.contains("Gene")]
	df_gene.drop(['RNA_type'],axis=1,inplace=True)
	df = df.dropna(axis=1, how='all')  # Drop columns with all NA values from df
	df_gene = df_gene.dropna(axis=1, how='all')  # Drop columns with all NA values from df_gene
	df = pd.concat([df, df_gene], ignore_index=True)
	df = pd.concat([df, df_gene], ignore_index=True)
	df = format_data_type_specific_info(df, data_type)
	df_tm = format_data_type_specific_info(df_tm, data_type)
	return df, df_tm


def generate_column_names(data_type):
	# return column names corresponding to the data type of the file
	col_names = []
	if data_type == 'experiments':
		col_names= ['Id', 'Gene', 'Disease', 'Disease_Name', 'score-db', 'source-score', 'confidence']
	if data_type == 'knowledge':
		col_names =  ['Id', 'Gene', 'Disease', 'Disease_Name', 'score-db', 'evidence', 'confidence']
	if data_type == 'textmining':
		col_names = ['Id', 'Gene', 'Disease', 'Disease_Name', 'z-score', 'confidence', 'url']
	return col_names


def write_df_to_csv(df, data_type, coding=True):
	# check if df is empty
	if df.shape[0] == 0:
		return
	# write filepath for output file
	if coding:
		filepath = 'CSVs/codingGenes-' + data_type + '.csv'
	else:
		filepath = 'CSVs/nonCodingGenes-' + data_type + '.csv'
	# write df to csv file
	df.to_csv(filepath, doublequote=False, escapechar='\\')
	return


def format_csv(data_type):
	start_time = time.time()
	filepath = 'input/human_disease_'+data_type+'_full.tsv'
	col_names = generate_column_names(data_type)
	df = pd.read_csv(filepath, sep = '\t', header=None)
	df.columns = col_names
	df_coding_genes, df_non_coding_genes = clean_data(df, data_type)
	write_df_to_csv(df_coding_genes, data_type)
	write_df_to_csv(df_non_coding_genes, data_type, coding=False)
	processing_time = "%s seconds" % round((time.time() - start_time), 2)
	print('Finished processing ' + data_type + ' data in ' + processing_time + '!')


def main():
	format_csv('experiments')
	format_csv('knowledge')
	format_csv('textmining')


if __name__ == '__main__':
    main() 
    
