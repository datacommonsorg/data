# Copyright 2022 Google LLC
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
Date: 08/05/2022
Name: format_disease_ontology
Description: converts a .owl disease ontology file into
a csv format, creates dcids for each disease and links the dcids
of current MeSH and ICD10 codes to the corresponding properties in 
the dataset.
@file_input: input .owl from Human DO database
@file_output: formatted .csv with disease ontology
"""

from xml.etree import ElementTree
from collections import defaultdict
import pandas as pd
import re
import numpy as np
import sys
from absl import flags
from absl import app

FLAGS = flags.FLAGS
flags.DEFINE_string('HumanDO', 'scratch/HumanDO.owl',
                    'HumanDO.owl  file input  path.')
flags.DEFINE_string('HumanDO_out', 'scratch/HumanDO.csv',
                    'HumanDO.owl output file path.')



def format_tag(tag: str) -> str:
	"""Extract human-readable tag from xml tag
	Args:
		tag: tag of an element in xml file,
			 containg human-readable string after '}'
	Returns:
		tag_readable: human-readble string after '}'
	
	"""
	tag_readable = tag.split("}")[1]
	return tag_readable


def format_attrib(attrib: dict) -> str:
	"""Extract text from xml attributes dictionary
	Args:
		attrib: attribute of an xml element 
	Returns:
		text: extracted text from attribute values,
			either after '#' or after the final '/'
			if '#' does not exist
	"""
	attrib = list(attrib.values())[0]
	text = None
	if "#" in attrib:
		text = attrib.split("#")[-1]
	else:
		text = attrib.split("/")[-1]
	return text


def parse_do_info(info: list) -> dict:
	"""Parse owl class childrens 
	to human-readble dictionary
	Args:
		info: list of owl class children
	Returns:
		info_dict: human_readable dictionary 
		containing information of owl class children
	"""
	info_dict = defaultdict(list)
	for element in info:
		tag = format_tag(element.tag)
		if element.text == None:
			text = format_attrib(element.attrib)
			info_dict[tag].append(text)
		else:
			info_dict[tag].append(element.text)
	return info_dict


def format_cols(df):
	"""
	Converts all columns to string type and
	replaces all special characters
	Args:
		df = dataframe to change
	Returns:
		none
	"""
	for i, col in enumerate(df.columns):
		df[col] = df[col].astype(str)
		df[col] = df[col].map(lambda x: re.sub(r'[\([{})\]]', '', x))
		df.iloc[:, i] = df.iloc[:, i].str.replace("'", '')
		df[col] = df[col].replace('nan', np.nan)
	df['id'] = df['id'].str.replace(':', '_')
	#df['hasAlternativeId'] = df['hasAlternativeId'].str.replace(':', '_')
	
def replace_nan_func(x):
	"""
	Combines all NaN rows with same ID 
	Args:
		df = dataframe to change
	Returns:
		none
	"""
	x = x[~pd.isna(x)]
	if len(x) > 0:
		return x.iloc[0]
	else:
		return np.NaN


def col_explode(df):
	"""
	Splits the hasDbXref column into multiple columns
	based on the prefix identifying the database from which
	the ID originates
	Args:
		df = dataframe to change
	Returns
		df = modified dataframe
	"""
	df = df.assign(hasDbXref=df.hasDbXref.str.split(",")).explode('hasDbXref')
	df[['A', 'B']] = df['hasDbXref'].str.split(':', n=1, expand=True)
	df['A'] = df['A'].astype(str).map(lambda x: re.sub('[^A-Za-z0-9]+', '', x))
	col_add = list(df['A'].unique())
	for newcol in col_add:
		df[newcol] = np.nan
		df[newcol] = np.where(df['A'] == newcol, df['B'], np.nan)
		df[newcol] = df[newcol].astype(str).replace("nan", np.nan)
	#df['hasAlternativeId'] = df['hasAlternativeId'].str.split(',')
	#df = df.explode('hasAlternativeId')
	#df1 = df.groupby(by='id').agg(dict.fromkeys(df.columns[0:], replace_nan_func))
	return df


def shard(list_to_shard, shard_size):
	"""
	Breaks down a list into smaller 
	sublists, converts it into an array
	and appends the array to the master
	list
	Args:
		list_to_shard = original list
		shard_size = size of subist
	Returns:
		sharded_list = master list with
		smaller sublists 
	"""
	sharded_list = []
	for i in range(0, len(list_to_shard), shard_size):
		shard = list_to_shard[i:i + shard_size]
		arr = np.array(shard)
		sharded_list.append(arr)
	return sharded_list

def mesh_separator(df):
	"""
	Splits the mesh column into mesh descriptor and concept ID
	Args:
		df: pandas dataframe with mesh column 

	Returns:
		df: dataframe with split mesh column 
	"""
	
	df['meshDescriptor'] = np.where(df['MESH'].str[0] == 'D', df['MESH'], np.nan)
	df['meshDescriptor'] = "bio/" + df['meshDescriptor']
	df['meshConcept'] = np.where(df['MESH'].str[0] == 'C', df['MESH'], np.nan)
	df['meshConcept'] = "bio/" + df['meshConcept']
	df = df.drop(['MESH'], axis = 1)
	return df

def col_string(df):
	"""
	Adds string quotes to columns in a dataframe
	Args:
		df = dataframe whose columns are modified
	Returns:
		None
	"""
	col_names = ['hasExactSynonym', 'label', 'IAO_0000115']
	for col in col_names:
		df[col] = df[col].str.replace('"', "")
		df.update('"' + df[[col]].astype(str) + '"')
		df[col] = df[col].replace(["\"nan\""],np.nan)
	return df

def create_dcid(df):
	df['diseaseId'] = df['id']
	df['diseaseId'] = df['diseaseId'].str.replace("_", ":")
	df['subClassOf'] = df['subClassOf'].str.split(',')
	df['subClassOf'] = df['subClassOf'].str[0]
	col_names = ['id', 'subClassOf']
	for col in col_names:
		df[col] = "bio/" + df[col]
		df[col] = df[col].replace(["bio/nan"],np.nan)
	df['ICD10CM'] = "dcid:ICD10/" + df['ICD10CM'].astype(str)
	df['ICD10CM'] = df['ICD10CM'].replace("dcid:ICD10/nan", np.nan)
	df.update('"' + df[['diseaseId']].astype(str) + '"')
	return df

def check_for_illegal_charc(s):
	list_illegal = ["'", "#", "–", "*" ">", "<", "@", "]", "[", "|", ":", ";", " "]
	if any([x in s for x in list_illegal]):
		print('Error! dcid contains illegal characters!', s)

def check_for_dcid(row):
	check_for_illegal_charc(str(row['id']))
	check_for_illegal_charc(str(row['subClassOf']))
	return row


def wrapper_fun(file_input):
	# Read disease ontology .owl file
	tree = ElementTree.parse(file_input)
	# Get file root
	root = tree.getroot()
	# Find owl classes elements
	all_classes = root.findall('{http://www.w3.org/2002/07/owl#}Class')
	# Parse owl classes to human-readble dictionary format
	parsed_owl_classes = []
	for owl_class in all_classes:
		info = list(owl_class.iter())
		parsed_owl_classes.append(parse_do_info(info))
	# Convert to pandas Dataframe
	df_do = pd.DataFrame(parsed_owl_classes)
	format_cols(df_do)
	df_do = df_do.drop([
		'Class', 'exactMatch', 'deprecated', 'hasRelatedSynonym', 'comment',
		'OBI_9991118', 'narrowMatch', 'hasBroadSynonym', 'disjointWith',
		'hasNarrowSynonym', 'broadMatch', 'created_by', 'creation_date',
		'inSubset', 'hasOBONamespace'
	],
					   axis=1)
	df_do = col_explode(df_do)
	df_do = mesh_separator(df_do)
	df_do = col_string(df_do)
	df_do = df_do.drop(['A', 'B', 'nan', 'hasDbXref', 'KEGG'], axis=1)
	df_do = df_do.drop_duplicates(subset='id', keep="last")
	df_do = df_do.reset_index(drop=True)
	df_do = df_do.replace('"nan"', np.nan)
	df_do = create_dcid(df_do)
	df_do['IAO_0000115'] = df_do['IAO_0000115'].str.replace("_", " ")
	df_do = df_do.apply(lambda x: check_for_dcid(x),axis=1)
	return df_do

def main(argv):
	del argv 
	file_input = FLAGS.HumanDO
	file_output=FLAGS.HumanDO_out

	df = wrapper_fun(file_input)
	df.columns = ['diseaseDescription' if x=='IAO_0000115' else x for x in df.columns]
	df.to_csv(file_output, doublequote=False, escapechar='\\')


if __name__ == '__main__':
	app.run(main)