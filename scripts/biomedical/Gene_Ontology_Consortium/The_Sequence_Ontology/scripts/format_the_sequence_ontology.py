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
'''
Author: Samantha Piekos
Date: 05/13/2024
Last Edited: 07/02/2024
Name: format_the_sequence_ontology.py
Description: converts nested .json to .csv and seperates out cross 
references for the sequence ontology and corresponding definitions into
distinct properties.
@file_input: input json file downloaded from The-Sequence-Ontology GitHub
@file_output: formatted csv files ready for import into data commons kg 
              with corresponding tmcf file 
'''

# import environment
import json
import numpy as np
import pandas as pd
import sys


# declare universal variables
DICT_SUBSETS = {
	'http://purl.obolibrary.org/obo/so#DBVAR': 'dcs:SequenceOntologySubsetDbVar',
	'http://purl.obolibrary.org/obo/so#biosapiens': 'dcs:SequenceOntologySubsetBiosapiens',
	'http://purl.obolibrary.org/obo/so#SOFA': 'dcs:SequenceOntologySubsetSofa',
	'http://purl.obolibrary.org/obo/so#Alliance_of_Genome_Resources': 'dcs:SequenceOntologySubsetAllianceOfGenomeResources'
}

DICT_SYNONYM_TYPE = {
	'hasRelatedSynonym': 'dcs:SynonymTypeRelated',
	'hasNarrowSynonym': 'dcs:SynonymTypeNarrow',
	'hasBroadSynonym': 'dcs:SynonymTypeBroad',
	'hasExactSynonym': 'dcs:SynonymTypeExact'
}

LIST_META_KEYS = [
	'basicPropertyValues',   # [{'pred': '', 'val': ''},
				 			 # {'pred': '', 'val': ''}]
	'comments',  # list
	'definition', # dictionary {'val': '', 'xrefs': []}
	'deprecated',  # boolean
	'subsets',  # list
	'synonyms',  # [{'pred': '', 'val': '',  'xrefs': []},
				 # {'pred': '', 'val': '',  'xrefs': []}]
	'xrefs'  # [{'val': ''}]
]

LIST_DROP_MIN_USED_SOURCES = [
	'BACTERIAL_REGULATION_WORKING_GROUP',
	'BBOP',
	'BCS',
	'CLINGEN',
	'EBIBS',
	'GREEKC',
	'GENCC',
	'GMOD',
	'GO',
	'HGNC',
	'INDIANA',
	'INVITROGEN',
	'JAX',
	'LAMHDI',
	'MGD',
	'MGI',
	'MODENCODE',
	'OBO',
	'PHIGO',
	'POMBE',
	'RFAM',
	'RSC',
	'SANGER',
	'SBOL',
	'SGD',
	'UNIPROT',
	'WB',
	'XENBASE',
	'ZFIN'
]


LIST_DROP_UNKNOWN_SOURCES =[
'EBI',
'FB',
'GOC',
'NCBI',
'SO'
]


# define functions
def pascalcase(s):
	# convert string to pascal case
    list_words = s.split()
    converted = "".join(
        word[0].upper() + word[1:].lower() for word in list_words)
    return converted


def check_for_illegal_charc(s):
	# check that dcid does not contain any illegal characters
	# print error message if it does
    list_illegal = ["'", "–", "*", ','
                    ">", "<", "@", "]", "[", "|", ":", ";"
                    " "]
    if any([x in s for x in list_illegal]):
        print('Error! dcid contains illegal characters!', s)


def check_if_new_meta_variables(df):
	# evaluate if any new properties are added to meta data
	# print out error message if one is detected
	l = []
	for index, row in df.iterrows():
		# identify keys in meta column dictionary
		for item in row['meta'].keys():
			l.append(item)
	l = list(set(l))  # remove duplicates
	for item in l:
		# check if any new keys added to meta dictionary
		# print any new keys
		if item not in LIST_META_KEYS:
			print('Error! New key in meta dictionary! Update code to incorporate:', item)
	return


def initiate_empty_meta_key_columns(df):
	# initate new column of empty strings for every meta dictionary key
	for key in LIST_META_KEYS:
		df[key] = ''
	return df


def expand_meta(df):
	# expand the meta data into one line per entry in the dataframe
	check_if_new_meta_variables(df)
	df = initiate_empty_meta_key_columns(df)
	for index, row in df.iterrows():
		for key in row['meta'].keys():
			df.at[index, key] = row['meta'][key]
	df = df.drop(['meta'], axis=1)
	return df


def format_reference_list(l):
	# return first item in list if one exists
	if len(l) > 0:
		return l[0]
	return ''


def expand_properties(df, col):
	# expand dataframe so that each property with multiple values is represented on it's own line
	new_rows = []
	for index, row in df.iterrows():
		c = row[col]
		if isinstance(c, list):  # Check if property is a list
			for item in c: # Iterate over each property list
				new_row = row.copy()  # Deep copy to avoid modifying original
				pred, value = item.get('pred'), item.get('val')
				if '#' in pred:
					pred = pred.split('#')[1]
					new_row[pred] = value
					new_rows.append(new_row)
				else:
					new_rows.append(row)  # Unchanged row if 'property' is not a list
		else:
			new_rows.append(row)  # Unchanged row if 'property' is not a list
             
	return pd.DataFrame(new_rows).drop([col], axis=1).fillna('')


def format_synonym_value(value):
	# take the text value after ':'
	if ':' in value:
		value = value.split(':')[1]
	return value


def expand_synonyms(df, col):
	# expand dataframe so that each synonym is represented on it's own line
	new_rows = []
	for index, row in df.iterrows():
		c = row[col]
		if isinstance(c, list):  # Check if synonyms is a list
			for item in c: # Iterate over each synonym dictionary
				new_row = row.copy()  # Deep copy to avoid modifying original
				new_row[col + '_pred'] = DICT_SYNONYM_TYPE[item.get('pred')]
				new_row[col + '_value'] = format_synonym_value(item.get('val'))
				new_row[col + '_source'] = format_reference_list(item.get('xrefs'))
				new_rows.append(new_row)
		else:
			new_rows.append(row)  # Unchanged row if 'synonyms' is not a list

	# replace '_' with ' '
	df_final = pd.DataFrame(new_rows).drop([col], axis=1).fillna('')
	df_final[col + '_value'] = df_final[col + '_value'].str.replace('_', ' ')

	return df_final


def replace_illegal_dcid_characters(s):
	# replace illegal characters with legal characters for dcid
	s = s.replace('-', ' ')\
		.replace("'", ' ')\
		.replace(",", ' ')\
		.replace('(', '')\
		.replace(')', '')\
		.replace('*', '')\
		.replace('  ', ' ')
	return s


def handle_placeholder_synonym_cases(df, index, row):
	# delete info for synonym entry if a placeholder name was not updated with actual entry
	if row['synonyms_value'] == '<new synonym>':
		# if missing synonym value make sure all values related to synonym are blank
		df.loc[index, 'synonyms_dcid'] = ''
		df.loc[index, 'synonyms_value'] = ''
		df.loc[index, 'synonyms_pred'] = ''
		df.loc[index, 'synonyms_source'] = ''
	return df


def format_synonym_dcid(df):
	# format dcid for synonyms that have multiple pieces of info attached
	# that will be stored in SequenceOntologyTermSynonym nodes
	df['synonyms_dcid'] = df['synonyms_value'].copy()
	# Deep copy to avoid modifying original
	for index, row in df.iterrows():
		if len(row['synonyms_dcid']) > 0:
			synonym = row['synonyms_dcid']
			synonym = replace_illegal_dcid_characters(synonym)
			synonym = pascalcase(synonym)
			synonym_dcid = row['dcid'] + '_' + synonym
			df.loc[index, 'synonyms_dcid'] = synonym_dcid
			df = handle_placeholder_synonym_cases(df, index, row)
			check_for_illegal_charc(df.loc[index, 'synonyms_dcid'])
	# format string values with commas appropriately
	return df


def format_dcid_and_id(df):
	# generate dcid, indicate id value, and format node names
	df['url'] = df['id']
	df['dcid'] = 'bio/SO_' + df['id'].str.split('/SO_').str[1]
	df['identifier'] = 'SO:' + df['id'].str.split('/SO_').str[1]
	df['name'] = df['lbl'].str.replace('_', ' ')
	df = format_synonym_dcid(df)
	return df.drop(['id'], axis=1)


def is_not_none(x):
	# check if value exists
    if pd.isna(x):
    	return False
    return True


def convert_list_to_string(df, col):
	# convert a property that has a list to an appropriately formatted string value
 	for index, row in df.iterrows():
 		v = row[col]
 		if isinstance(v, list):
 			v = ','.join(v)
 			df.loc[index, col] = v
 	return df


def format_list_as_text_strings(df, col_names):
    """
    Converts missing values to numpy nan value and adds outside quotes
    to strings (excluding np.nan). Applies change to columns specified in col_names.
    """
    for col in col_names:
    	df = convert_list_to_string(df, col)
    	df[col] = df[col].str.rstrip()  # Remove trailing whitespace
    	df[col] = df[col].replace([''],np.nan)  # replace missing values with np.nan

    	# Quote only string values
    	mask = df[col].apply(is_not_none)
    	df.loc[mask, col] = '"' + df.loc[mask, col].astype(str) + '"'

    return df


def format_text_strings(df, col_names):
    """
    Converts missing values to numpy nan value and adds outside quotes
    to strings (excluding np.nan). Applies change to columns specified in col_names.
    """

    for col in col_names:
        df[col] = df[col].str.rstrip()  # Remove trailing whitespace
        df[col] = df[col].replace([''],np.nan)  # replace missing values with np.nan

        # Quote only string values
        mask = df[col].apply(is_not_none)
        #df.loc[mask, col] = '"' + df.loc[mask, col].astype(str) + '"'
        df.loc[mask, col] = df.loc[mask, col].apply(lambda x: f'"{x}"')

    return df


def check_if_url(list_id):
	# if the id contains the start of a website url
	# return identifier before the source as the id
	# return source as 'HTTP'
	# else return the identifir as is and the source
	# as indicated before the first ':'
	if list_id[0].startswith('http'):
		identifier = (':').join(list_id)
		source = 'HTTP'
	elif list_id[1].startswith('www.'):
		identifier = (':').join(list_id[1:])
		source = 'HTTP'
	elif list_id[1].startswith('http'):
		identifier = (':').join(list_id[1:])
		source = 'HTTP'
	else:
		identifier = (':').join(list_id[0:])
		source = list_id[0].upper()
	return identifier, source


def extract_source_id(item):
	# identify if value is a link, if it is format it appropriately
	l = []
	list_id = item.split(':')
	if len(list_id) > 2:
		for i in list_id[1:]:
			identifier, source = check_if_url(list_id)
			l.append(identifier)
	else:
		identifier, source = check_if_url(list_id)
		l.append(identifier)
	return l, source


def check_if_col(df, col):
	# check if a column is a column in the df
	# if not, initiate a new column full of empty strings
	if col in df.columns:
		return df
	df[col] = ''
	return df


def seperate_xrefs_cols(value, index, col, df):
	# initiate new column for all cross reference sources
	df = check_if_col(df, col)
	df.loc[index, col] = value
	return df


def determine_source(value):
	# identify source as the string prior to the ':'
	if value.startswith('http'):
		return 'HTTP'
	source = value.split(':')[0]
	source = source.upper()
	return source


def expand_xrefs(df, col):
	# for each database that provides a cross reference
	# write the identifier values to their own columns
	for index, row in df.iterrows():
		l = row[col]
		for d in l:
			value = d['val']
			source = 'xrefs_' + determine_source(value)
			df = seperate_xrefs_cols(value, index, source, df)
	df = df.drop(['xrefs'], axis=1)
	return df


def format_edges(data):
	# get edges from the json file
	# format them as links between parent and child nodes
	edges = data['graphs'][0]['edges']
	df = pd.DataFrame(edges)
	df['dcid'] = 'bio/SO_' + df['sub'].str.split('/SO_').str[1]
	df['parent'] = 'bio/SO_' + df['obj'].str.split('/SO_').str[1]
	df = df.drop(['sub', 'pred', 'obj'], axis=1)
	return df


def expand_definition(df, col):
	# dictionary {'val': '', 'xrefs': []}
	for index, row in df.iterrows():
		if len(row[col]) == 0:
			continue
		l = row[col]['xrefs']
		for item in l:
			list_items, source = extract_source_id(item)
			df = check_if_col(df, source)
			df.loc[index, source] = (',').join(list_items)
		df.loc[index, col] = row[col]['val'].strip('"')
	df[col] = df[col].str.replace('\n', ' ')  # remove new line characters
	return df


def expand_columns(df):
	# Expand nested 'meta' dictionary into individual columns
	#df = pd.concat([df.drop(['meta'], axis=1), pd.json_normalize(df['meta'])], axis=1)
	df = expand_meta(df)
	# expand other columns
	df = expand_definition(df, 'definition')
	df = expand_properties(df, 'basicPropertyValues')
	df = expand_synonyms(df, 'synonyms')
	df = expand_xrefs(df, 'xrefs')
	# drop uninformative xrefs
	df = df.drop(LIST_DROP_MIN_USED_SOURCES, axis=1)
	df = df.drop(LIST_DROP_UNKNOWN_SOURCES, axis=1)
	# reset indices
	df = df.reset_index()
	return df


def format_subsets(df, col):
	# convert subset properties to SequenceOntologySubset enums
	for index, row in df.iterrows():
		l = []
		for i in row[col]:
			subset = DICT_SUBSETS[i]
			l.append(subset)
		subset_value = (',').join(l)
		df.loc[index, col] = subset_value
	return df


def format_columns(df):
	# format dcid, id, and name
	df = format_dcid_and_id(df)
	# format date column:
	df['creation_date'] = df['creation_date'].str[:10]
	# format subsets column
	df = format_subsets(df, 'subsets')
	# set Sequence Ontology ID as name if no name is provided
	df.loc[df['name'] == '', 'name'] = df['identifier']
	# drop unnecessary columns
	df.drop(['type', 'lbl', 'hasOBONamespace'], axis=1, inplace=True)
	# convert list columns to string values
	col_names = ['comments']
	df = format_list_as_text_strings(df, col_names)
	df['comments'] = df['comments'].str.replace('\n', ' ')  # remove new line characters
	# put quotes around string values
	col_names = ['name', 'definition',  'PMID', 'HTTP', 'DOI',
	'ISBN', 'POMBASE', 'ISSN', 'CHEBI', 'PMC', 'created_by',
	'hasAlternativeId', 'consider', 'synonyms_value','synonyms_source',
	'xrefs_HTTP', 'xrefs_LOINC', 'xrefs_MOD', 'xrefs_RNAMOD',
	'xrefs_DOI', 'xrefs_WIKIPEDIA','xrefs_PMID', 'url', 'identifier']
	format_text_strings(df, col_names)
	return df


def format_nodes(data):
	# format information about each SequenceOntologyTerm node
	# by parsing the json file
	nodes = data['graphs'][0]['nodes']
	df = pd.DataFrame(nodes)  # create pandas df
	df = df[df['type'] == 'CLASS']  # limit to class values
	# expand each feature into individual columns
	df = expand_columns(df)
	# data clean and format columns
	df = format_columns(df)
	return df
			

def read_json_to_df(file_input):
	# convert the json to csv with each property represented
	# in it's own seperate column
	with open(file_input, 'r') as file:  # load json
		data = json.load(file)
	# extract edges
	df_edges = format_edges(data)
	# extract nodes
	df_nodes = format_nodes(data)
	# merge nodes and edges dfs together
	df = pd.merge(df_nodes, df_edges, on='dcid', how='outer')
	# drop duplicates and replace missing values
	df.drop_duplicates(inplace=True)
	df = df.fillna('')
	# drop index
	df = df.drop(['index'], axis=1)
	return df


def main():
	file_input = sys.argv[1]  # read in file
	file_output = sys.argv[2]
	df = read_json_to_df(file_input)  # convert json to pandas df
	df.to_csv(file_output, doublequote=False, escapechar='\\', index=False)


if __name__ == "__main__":
    main()
