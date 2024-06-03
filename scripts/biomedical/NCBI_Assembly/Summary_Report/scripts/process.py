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
Author: Sanika Prasad
Date: 2024/05/31
@file_input: 2 input .txt from 	NCBI ASSEMBLY SUMMARY REPORTS database
@file_output: formatted .csv
"""

# import the required packages
import pandas as pd
import numpy as np
import sys
import csv
import os
from absl import flags
from pathlib import Path

TAX_ID_DCID_MAPPING = {}

#Disable false positive index chaining warnings
pd.options.mode.chained_assignment = None

_FLAGS = None

MODULE_DIR = str(Path(os.path.dirname(__file__)))


def generate_column(df):
	df['dcid'] = 'bio/' + df['#assembly_accession']
	df['genome_size_dcid'] = 'BasePairs' + df['genome_size'].astype(str)
	df['genome_size_name'] = 'BasePairs ' + df['genome_size'].astype(str)
	df['genome_size_ungapped_dcid'] = 'BasePairs' + df['genome_size_ungapped'].astype(str)
	df['genome_size_ungapped_name'] = 'BasePairs ' + df['genome_size_ungapped'].astype(str)
	df['gc_percent_dcid'] = 'Percent' + df['gc_percent'].astype(str)
	df['gc_percent_name'] = 'Percent ' + df['gc_percent'].astype(str)
	return df


def refseq_category(df):
	conversion_to_refseq_category = {
        'representative genome': 'dcs:RefSeqCategoryRepresentativeGenome',
        'reference genome': 'dcs:RefSeqCategoryReferenceGenome',
	}
	df = df.replace({'refseq_category': conversion_to_refseq_category})
	return df


def tax_id(df):
	for index, row in df.iterrows():
		if str(row['taxid']) == str(row['species_taxid']):
			df.loc[index,'taxid'] = ""			
		else:
			try:
				df.loc[index,'taxid'] = TAX_ID_DCID_MAPPING[row['taxid']]
			except:
				df.drop(index,inplace=True)
	return df


def species_tax_id(df):
	for index, row in df.iterrows():
		try:
			df.loc[index,'species_taxid'] = TAX_ID_DCID_MAPPING[row['species_taxid']]
		except:
				df.drop(index,inplace=True)
	return df


def infraspecific_name(df):
	for index, row in df.iterrows():
		if "/" in str(row['infraspecific_name']):
			df.loc[index,'infraspecific_name'] = str(df.loc[index,'infraspecific_name']).replace('/', ', ')
		if "[" or ']' in str(row['organism_name']):
			df.loc[index,'organism_name'] = str(df.loc[index,'organism_name']).replace('[','').replace(']','')
	return df


def format_correction(df):
	df['infraspecific_name'] = '\"' + df['infraspecific_name'] + '\"'
	df['isolate'] = '\"' + df['isolate'] + '\"'
	return df


def assembly_level(df):
	conversion_to_assembly_level = {
        'Complete Genome': 'dcs:GenomeAssemblyLevelCompleteGenome',
        'Chromosome': 'dcs:GenomeAssemblyLevelChromosome',
		'Scaffold': 'dcs:GenomeAssemblyLevelScaffold',
		'Contig': 'dcs:GenomeAssemblyLevelContig',
	}
	df = df.replace({'assembly_level': conversion_to_assembly_level})
	return df


def release_type(df):
	conversion_to_release_type = {
        'Major': 'dcs:GenomeAssemblyReleaseTypeMajor',
		'Minor': 'dcs:GenomeAssemblyReleaseTypeMinor',
		'Patch': 'dcs:GenomeAssemblyReleaseTypePatch',
	}
	df = df.replace({'release_type': conversion_to_release_type})
	return df


def genome_rep(df):
	for index, row in df.iterrows():
		if "Full" in str(row['genome_rep']):
			df.loc[index,'genome_rep'] = "True"
		else:
			df.loc[index,'genome_rep'] = "False"
	return df


def formatdate(df):
	df['seq_rel_date'] = pd.to_datetime(df['seq_rel_date'])
	df['seq_rel_date'] = df['seq_rel_date'].dt.strftime('%Y-%m-%d')
	df['annotation_date'] = pd.to_datetime(df['annotation_date'])
	df['annotation_date'] = df['annotation_date'].dt.strftime('%Y-%m-%d')
	return df


def paired_asm_comp(df):
	for index, row in df.iterrows():
		if "identical" in str(row['paired_asm_comp']):
			df.loc[index,'paired_asm_comp'] = "True"
		else:
			df.loc[index,'paired_asm_comp'] = "False"
	return df


def relation_to_type_material(df):
	conversion_to_type_material = {
        'ICTV additional isolate': 'dcs:GenomeAssemblyDerivedFromIctvAdditionalIsolate',
		'ICTV species exemplar': 'dcs:GenomeAssemblyDerivedFromIctvSpeciesExemplar',
		'assembly designated as clade exemplar': 'dcs:GenomeAssemblyDerivedFromCladeExemplar',
		'assembly designated as neotype': 'dcs:GenomeAssemblyDerivedFromNeotype',
		'assembly designated as reftype': 'dcs:GenomeAssemblyDerivedFromReftype',
		'assembly from pathotype material': 'dcs:GenomeAssemblyDerivedFromPathotypeMaterial',
		'assembly from synonym type material': 'dcs:GenomeAssemblyDerivedFromSynonymTypeMaterial',
		'assembly from type material': 'dcs:GenomeAssemblyDerivedFromTypeMaterial',
	}
	df = df.replace({'relation_to_type_material': conversion_to_type_material})
	return df


def assembly_type(df):
	conversion_to_assembly_type = {
        'alternate-pseudohaplotype': 'dcs:GenomeAssemblyTypeAlternatePseudohaplotype',
		'diploid': 'dcs:GenomeAssemblyTypeDiploidAssembly',
		'haploid': 'dcs:GenomeAssemblyTypeHaploidAssembly',
		'haploid-with-alt-loci': 'dcs:GenomeAssemblyTypeHaploidWithAltLoci',
		'unresolved-diploid': 'dcs:GenomeAssemblyTypeUnresolvedDiploid',
	}
	df = df.replace({'assembly_type': conversion_to_assembly_type})
	return df


def group(df):
	conversion_to_group = {
        'archaea': 'dcs:BiologicalTaxonomyGroupArchaea',
		'bacteria': 'dcs:BiologicalTaxonomyGroupBacteria',
		'fungi': 'dcs:BiologicalTaxonomyGroupFungi',
		'invertebrate': 'dcs:BiologicalTaxonomyGroupInvertebrate',
		'metagenomes': 'dcs:BiologicalTaxonomyGroupMetagenomes',
		'other': 'dcs:BiologicalTaxonomyGroupOther',
		'plant': 'dcs:BiologicalTaxonomyGroupPlant',
		'protozoa': 'dcs:BiologicalTaxonomyGroupProtozoa',
		'vertebrate_mammalian': 'dcs:BiologicalTaxonomyGroupVertebrateMammalian',
		'vertebrate_other': 'dcs:BiologicalTaxonomyGroupVertebrateOther',
		'viral': 'dcs:BiologicalTaxonomyGroupViral',
	}
	df = df.replace({'group': conversion_to_group})
	return df

def set_flags():
	global _FLAGS
	_FLAGS = flags.FLAGS
	flags.DEFINE_string('output_dir', 'scripts/output_file/ncbi_assembly_summary.csv',
                    'Output directory for generated files.')
	flags.DEFINE_string('input_dir', 'scripts/input/assembly_summary_genbank.txt',
                    'Input directory where .txt files downloaded.')	
	flags.DEFINE_string('input_dir1', 'scripts/input/assembly_summary_refseq.txt',
                    'Output directory for generated files.')
	flags.DEFINE_string('tax_id_dcid_mapping', 'scripts/input/tax_id_dcid_mapping.txt',
                    'Input directory where .txt files downloaded.')
	_FLAGS(sys.argv)


def driver_function(df):
	df = generate_column(df)
	df = refseq_category(df)
	df = tax_id(df)
	df = species_tax_id(df)
	df = infraspecific_name(df)
	df = format_correction(df)
	df = assembly_level(df)
	df = release_type(df)
	df = genome_rep(df)
	df = formatdate(df)
	df = paired_asm_comp(df)
	df = relation_to_type_material(df)
	df = assembly_type(df)
	df = group(df)
	return df

def main(_FLAGS):
	global TAX_ID_DCID_MAPPING
	file_input = _FLAGS.input_dir
	file_input1 = _FLAGS.input_dir1
	tax_id_dcid_mapping = _FLAGS.tax_id_dcid_mapping
	file_output = _FLAGS.output_dir
	df = pd.read_csv(file_input,skiprows=1,delimiter='\t')
	df = df.replace('na', '')
	df = df.drop(columns='asm_not_live_date')
	
	df1 = pd.read_csv(file_input1,skiprows=1,delimiter='\t')
	ref_gbrs_paired_asm = df1['gbrs_paired_asm'].tolist()
	
	with open(tax_id_dcid_mapping, 'r') as file:
		csv_reader = csv.DictReader(file)
		for row in csv_reader:
			TAX_ID_DCID_MAPPING[int(row['tax_id'])] = row['dcid']

	for index, row in df.iterrows():
		if str(row['gbrs_paired_asm']).startswith('GC'):
			continue
		else:
			if df.loc[index,'#assembly_accession'] in ref_gbrs_paired_asm:
				df.loc[index,'gbrs_paired_asm'] = df.loc[index,'#assembly_accession']

	df_final = driver_function(df)

	df_final.to_csv(file_output,index=False)

if __name__ == '__main__':
	set_flags()
	main(_FLAGS)