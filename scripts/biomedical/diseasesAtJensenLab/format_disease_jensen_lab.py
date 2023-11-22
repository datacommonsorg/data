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
Date: 08/12/2023
Name: format_disease_jensen_lab
Description: converts a three input .txt files from Diseases at
Jensen Lab into output .csv files with formatted dcids, 
NonCoding RNA types, and gene synonyms.
@file_input: input .txt files from Diseases at Jensen Lab 
@file_output: formatted .csv files for Diseases at Jensen Lab
"""

import sys
import numpy as np
import pandas as pd

HGNC_DICT = {'HGNC:9982':'RFX1', 'HGNC:9979':'RFPL2'}

def format_doid_icd(df):
    df['DOID'] = np.where(df['Identifier'].str.contains('DOID'),df['Identifier'],np.nan)
    df['ICD10'] = np.where(df['Identifier'].str.contains('ICD10'),df['Identifier'],np.nan)
    ## filter out synonyms
    df['synonym'] = np.where(df['Id'].str.contains('ENSP00000'),df['Id'],np.nan)
    ## filter out ICD-10 codes based on true existence - remove codes like C1, C2 and root
    df['count'] = np.where(df['ICD10'] == df['ICD10'],df['ICD10'].str.split(':'),np.nan)
    df['count'] = np.where(df['count'] == df['count'],df['count'].str[1],np.nan)
    df = df[df['count']!='root']
    df['count'] = df['count'].str.len()
    df = df[df['count'] !=2]
    df = df[df['count'] !=1]
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
    check_for_illegal_charc(str(row['GeneDcid']))
    check_for_illegal_charc(str(row['ICD10']))
    return row

def format_disease_gene_cols(df):
    df['Gene'] = df['Gene'].map(HGNC_DICT).fillna(df['Gene'])
    df['Gene'] = df['Gene'].str.replace('@', '')
    df['GeneDcid'] = 'bio/' + df['Gene'].astype(str)
    df['GeneDcid'] = df['GeneDcid'].str.replace('-', '_')
    df['DOID'] = 'dcid:bio/' + df['DOID'].str.replace(':', '_')
    df['DOID'] = df['DOID'].replace('dcid:bio/nan', np.nan)
    df['ICD10'] = df['ICD10'].str.replace(':', '/')
    df['DiseaseDcid'] = df['DOID'].fillna('dcid:'+df['ICD10'])
    df['dcid'] = 'bio/DGA_' + df['Identifier'] + '_' + df['Gene'] + '_text_mining'
    df['dcid'] = df['dcid'].str.replace(':', '_')
    return df

def format_RNA_type(df_tm):
	gene_list = ['orf', 'ZNF']
	sno_rna_list = ['sno', 'SNOR', 'SCAR']
	linc_rna_list = ['LINC', 'linc', 'MIR']
	df_tm['RNA_type'] = 'NonCodingRNATypeLongNonCodingRNA'
	df_tm['RNA_type'] = np.where(df_tm["Gene"].str.contains('|'.join(gene_list)),'Gene', df_tm['RNA_type'])
	df_tm['RNA_type'] = np.where(df_tm["Gene"].str.contains('rRNA'),'NonCodingRNATypeRibosomalRNA', df_tm['RNA_type'])
	df_tm['RNA_type'] = np.where(df_tm["Gene"].str.contains('|'.join(linc_rna_list)),'NonCodingRNATypeLongIntergenicNonCodingRNA', df_tm['RNA_type'])
	df_tm['RNA_type'] = np.where(df_tm["Gene"].str.contains('|'.join(sno_rna_list)),'NonCodingRNATypeSmallNucleolarRNA', df_tm['RNA_type'])
	df_tm['RNA_type'] = np.where(df_tm["Gene"].str.contains('miR'),'NonCodingRNATypeMicroRNA', df_tm['RNA_type'])
	df_tm['RNA_type'] = np.where(df_tm["Gene"].str.contains('circ'),'NonCodingRNATypeCircularRNA', df_tm['RNA_type'])
	df_tm['RNA_type'] = np.where(df_tm["Gene"].str.contains('pRNA'),'NonCodingRNATypePromoterAssociatedRNA', df_tm['RNA_type'])
	return df_tm

def format_genes(df):
	df = format_doid_icd(df)
	df = format_disease_gene_cols(df)
	df = df.apply(lambda x: check_for_dcid(x),axis=1)
	return df 

def format_df(df, num):
	if num ==1:
		df['associationType'] = 'bio/AssociationTypeTextMining'
		df.update('"' +
				  df[['Name', 'url', 'associationType']].astype(str) + '"')
		df.replace("\"nan\"", np.nan, inplace=True)
	elif num==2:
		df['dcid'] = df['dcid'].str.replace('text_mining', 'manual_curation')
		df['associationType'] = 'bio/AssociationTypeManualCuration'
		df.update('"' +
				  df[['Name', 'score-db', 'associationType']].astype(str) + '"')
		df.replace("\"nan\"", np.nan, inplace=True)
	else:
		df['dcid'] = df['dcid'].str.replace('text_mining', 'experiment')
		df['associationType'] = 'bio/AssociationTypeExperiment'
		df['source-score'] = df['source-score'].str.split('=')
		df['source-score'] = np.where(df['source-score'] == df['source-score'],df['source-score'].str[1],np.nan)
		df.update('"' +
				  df[['Name', 'score-db', 'associationType']].astype(str) + '"')
		df.replace("\"nan\"", np.nan, inplace=True)
	return df

def format_genes_textmining(df):
	df.columns = ['Id', 'Gene', 'Identifier', 'Name', 'z-score', 'confidence', 'url']
	df_tm = df
	searchfor = ['ENSP00', 'LINC', 'linc'] ### filter out non coding RNAs
	df = df[df['Id'].str.contains("ENSP00")]
	df = df[~df.Gene.str.contains('|'.join(searchfor))]
	df_tm = df_tm[~df_tm.isin(df)].dropna() ## df with only non coding RNAs
	df_tm = df_tm[~df_tm['Gene'].str.contains("chr")]
	df_tm = df_tm[~df_tm['Gene'].str.contains("ENSP00")]
	df = format_genes(df)
	df_tm = format_genes(df_tm)
	df_tm = format_RNA_type(df_tm) ## filter out genes from df with non coding RNA
	df_gene = df_tm.loc[df_tm['RNA_type']=='Gene'] ## filter out genes from df with non coding RNA
	df_tm = df_tm[~df_tm['RNA_type'].str.contains("Gene")]
	df_gene.drop(['RNA_type'],axis=1,inplace=True)
	df = df._append(df_gene).reset_index(drop=True)
	df = format_df(df, 1)
	df_tm = format_df(df_tm, 1)
	return df, df_tm

def format_genes_knowledge(df):
	df.columns = ['Id', 'Gene', 'Identifier', 'Name', 'score-db', 'evidence', 'confidence']
	df_tm = df
	searchfor = ['ENSP00', 'LINC', 'linc'] ### filter out non coding RNAs
	df = df[df['Id'].str.contains("ENSP00")]
	df = df[~df.Gene.str.contains('|'.join(searchfor))]
	df_tm = df_tm[~df_tm.isin(df)].dropna() ## df with only non coding RNAs
	df_tm = df_tm[~df_tm['Gene'].str.contains("chr")]
	df_tm = df_tm[~df_tm['Gene'].str.contains("ENSP00")]
	df = format_genes(df)
	df_tm = format_genes(df_tm)
	df_tm = format_RNA_type(df_tm) ## filter out genes from df with non coding RNA
	df_gene = df_tm.loc[df_tm['RNA_type']=='Gene'] ## filter out genes from df with non coding RNA
	df_tm = df_tm[~df_tm['RNA_type'].str.contains("Gene")]
	df_gene.drop(['RNA_type'],axis=1,inplace=True)
	df = df._append(df_gene).reset_index(drop=True)
	df = format_df(df,2)
	df_tm = format_df(df_tm,2)
	return df, df_tm

def format_genes_experiment(df):
	df.columns = ['Id', 'Gene', 'Identifier', 'Name', 'score-db', 'source-score', 'confidence']
	df['Identifier'] = df['Identifier'].str.replace('DOID:3394', 'DOID:3393')
	df_tm = df
	searchfor = ['ENSP00', 'LINC', 'linc'] ### filter out non coding RNAs
	df = df[df['Id'].str.contains("ENSP00")]
	df = df[~df.Gene.str.contains('|'.join(searchfor))]
	df_tm = df_tm[~df_tm.isin(df)].dropna() ## df with only non coding RNAs
	df_tm = df_tm[~df_tm['Gene'].str.contains("chr")]
	df_tm = df_tm[~df_tm['Gene'].str.contains("ENSP00")]
	df = format_genes(df)
	df_tm = format_genes(df_tm)
	df_tm = format_RNA_type(df_tm) ## filter out genes from df with non coding RNA
	df_gene = df_tm.loc[df_tm['RNA_type']=='Gene'] ## filter out genes from df with non coding RNA
	df_tm = df_tm[~df_tm['RNA_type'].str.contains("Gene")]
	df_gene.drop(['RNA_type'],axis=1,inplace=True)
	df = df._append(df_gene).reset_index(drop=True)
	df = format_df(df,3)
	df_tm = format_df(df_tm,3)
	return df, df_tm

def wrapper_function(df_textmining, df_manual, df_experiment):
	df_txt, df_txt_rna = format_genes_textmining(df_textmining)
	df_txt1, df_txt_rna1 = format_genes_knowledge(df_manual)
	df_txt2, df_txt_rna2 = format_genes_experiment(df_experiment)
	df_txt[0:4003718].to_csv('codingGenes-textmining-1.csv', doublequote=False, escapechar='\\')
	df_txt[4003719:].to_csv('codingGenes-textmining-2.csv', doublequote=False, escapechar='\\')
	df_txt_rna.to_csv('nonCodingGenes-textmining.csv', doublequote=False, escapechar='\\')
	df_txt1.to_csv('codingGenes-manual.csv', doublequote=False, escapechar='\\')
	df_txt_rna1.to_csv('nonCodingGenes-manual.csv', doublequote=False, escapechar='\\')
	df_txt2.to_csv('experiment.csv', doublequote=False, escapechar='\\')

def main():
	df_textmining = pd.read_csv('human_disease_textmining_full.tsv', sep = '\t', header=None)
	df_manual = pd.read_csv('human_disease_knowledge_full.tsv', sep = '\t', header=None)
	df_experiment = pd.read_csv('human_disease_experiments_full.tsv', sep = '\t', header=None)
	wrapper_function(df_textmining, df_manual, df_experiment)



if __name__ == '__main__':
    main() 
