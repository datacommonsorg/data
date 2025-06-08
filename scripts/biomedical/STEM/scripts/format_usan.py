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
Date: 01/10/2023
Edited By: Sanika Prasad.
Last Edited: 05/20/24
Name: format_usan
Description: converts a .csv file containing USAN (United States Adopted Names) approved stems into a formatted .csv with stems and substems differentiated and dcids created.  
@file_input: input .csv from USAN database
@file_output: formatted .csv with USAN approved stems and substems
"""

# import the required packages
import pandas as pd
import numpy as np
import sys
import csv
import os
from absl import flags
from pathlib import Path

#Disable false positive index chaining warnings
pd.options.mode.chained_assignment = None

_FLAGS = None


MODULE_DIR = str(Path(os.path.dirname(__file__)))

def check_for_illegal_charc(s):
    """Checks for illegal characters in a string and prints an error statement if any are present
    Args:
        s: target string that needs to be checked
    
    """
    list_illegal = ["'", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
    if any([x in s for x in list_illegal]):
        print('Error! dcid contains illegal characters!', s)

def remove_null_entries(df):
	"""Drop specific null entries from dataframe
	Args:
		df: dataframe with null entries 
	Returns:
		df: dataframe with null entries removed 
	
	"""
	df = df.dropna(how='all') ## drop all rows with all empty values
	df = df.iloc[:, [0, 1, 2, 3]] ## drop all columns with all empty values
	df = df.replace(r'\r+|\n+|\t+','', regex=True) ## remove endline and tab chars
	for index, row in df.iterrows():
		stem = row['Stem']
		col2 = row['Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)']
		col3 = row['Definition']
		if str(stem).startswith("subgroups") and str(col2) not in ["NaN", "nan"] and\
			  str(col3) not in ["NaN", "nan"]:
			df.loc[index,'Stem']="nan"
		if str(col2).startswith("subgroups"):
			df.drop(index,inplace=True)
	mask = ((df.drop("Stem",axis=1).isna().all(1)) & (df['Stem'].notna())) ## Drop rows where the column `stem` is not null but rest of the columns are null
	df = df[~mask]
	df["sameAs"] = " "
	return df

def format_stem_definitions(df):
	"""Formats the USAN stem and definitions
	Args:
		df: dataframe with USAN stem and definition columns
	Returns:
		df: dataframe with formatted USAN stem and definition columns
	
	"""
	df[['Stem', 'Definition']] = df[['Stem', 'Definition']].astype(str).replace(r"\(.*\)","", regex=True) ## removes text from paranthesis
	df['Definition'] = df['Definition'].replace('',np.nan,regex = True) ## replace empty string with np.nan
	for index, row in df.iterrows():
		if any(x in str(row['Stem']) for x in ['/','[',']',',','-']):
			stem_value=str(row['Stem']).replace(',','/').replace('[','/').replace(']','/')   			
			stem_value=stem_value.split('/')
			stem_value_new = []
			for s in stem_value:
				if len(str(s))>1:
					stem_value_new.append(s.strip())
			row['Stem'] = stem_value_new
			df.at[index, 'Stem'] = row['Stem']
			df.loc[index, 'sameAs'] = "|".join(stem_value_new)
			i = 1
			try:
				while df.loc[index+i, 'Stem'] in ["NaN", "nan"]:
					if len(df.loc[index+i, 'Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)']) > 1:
						df.at[index+i, 'Stem'] = stem_value_new
					i += 1
			except:
				pass
		
	df = df.explode('Stem')
	df['Stem'] = df['Stem'].str.replace('\W', '', regex=True) ## retain only text chars from stem columns
	return df


def map_word_stem_to_enum(values):
	"""Determines the word stem type for each of the rows
	Args:
		df: dataframe without word stem type
	Returns:
		df: dataframe with word stem type
	
	"""
	# based on where the dash is in the string, determine which word stem type it is
	# return appropriate WordStemEnum
	word_stems = []
	for val in values:
		val = str(val)
		if(val[0] == "-" and val[-1] == "-"): ## if the word starts and ends with a hyphen, it's an infix
			word_stems.append("dcs:WordStemInfix")
		elif(val[0] == "-"):
			word_stems.append("dcs:WordStemPrefix") ## else, if the word starts with a hyphen, it's a prefix
		else:
			word_stems.append("dcs:WordStemSuffix") ## if none of the above apply, it's a suffix
	return word_stems


def format_word_stem(df):
	"""Determines the word stem enum for each of the rows
	Args:
		df: dataframe without word stem categories
	Returns:
		df: dataframe with word stem categories
	
	"""
	df['WordStem'] = np.nan

	for index,row in df.iterrows():
		word_stems = []
		values = df.loc[index,'Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)']
		value_lst = []
		if isinstance(values, str) or isinstance(values, float):
			split_str = str(values).split(" ")
		if isinstance(values, pd.Series):
			split_str = values.tolist()
		try:	
			for s in split_str:
				if "-" in s:
					value_lst.append(s.replace(',',''))
		except:
			print(split_str, type(split_str), values, index, row)
			raise "error"
		word_stems = map_word_stem_to_enum(value_lst)
		word_stems = set(word_stems)
		if len(word_stems)>0:
			df.loc[index,'WordStem'] = (', ').join(word_stems)
	return df 


def format_usan_specialization(df):
	"""Determines the word specialization for each stem word
	Args:
		df: dataframe without word specialization
	Returns:
		df: dataframe with word specialization
	
	"""
	df['SpecializationOf'] = np.nan
	previous_stem = ''
	for index, row in df.iterrows():
		stem = row['Stem']
		stem_type = row['Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)']
		if str(stem_type) in ["NaN", "nan"]:
			continue
		if str(stem) in [
			"NaN",
			"nan",
		]: ## if word stem is absent, it implies specialization is needed
			df.loc[index,'SpecializationOf'] = previous_stem
			df.loc[index, 'Stem'] = stem_type.strip('-')
		else:
			previous_stem = str(stem)

	return df

def format_dcid(df):
	"""Formats dcid for each stem word
	Args:
		df: dataframe without dcid
	Returns:
		df: dataframe with acceptable dcid
	
	"""
	for index, row in df.iterrows():
		stem = row['Stem']
		if '- or -' in str(stem):
			df.loc[index, 'Stem'] = str(stem).replace('- or -', '_')
		if '- -' in str(stem):
			df.loc[index, 'Stem'] = str(stem).replace('- -', '_')

	df['dcid'] = 'chem/' +  df['Stem'].replace('\W', '', regex=True)
	df['SpecializationOf'] = "chem/" + df['SpecializationOf'].dropna().astype(
		str)     
	return df


def format_examples(df):
	"""Appending the example in empty line to the above example list
	Args:
		df: dataframe with example in empty line getting removed
	Returns:
		df: dataframe with example getting appended to correct example list
	
	"""
	for index, row in df.iterrows():
		col1 = row['Stem']
		col2 = row['Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)']
		col3 = row['Definition']
		col4 = row['Examples']
		# Check if all the column value are empty except example column
		if str(col1) in ["NaN", "nan"] and str(col2) in ["NaN", "nan"] and\
			  str(col3) in ["NaN", "nan"] and str(col4) not in ["NaN", "nan"]:
			i = 0
			while str(df.loc[index-i,'Stem']) in ["NaN", "nan"]:
				i+=1
			# appending the example to correct example list
			df.loc[index-i,
		  		'Examples'] = df.loc[index-i,
						   			'Examples'] + ", " + df.loc[index,
																'Examples']
	return df

def format_sameas(df):
	"""Adding sameAs property for stem with multiple Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)
	Args:
		df: dataframe without seperate sameAs property
	Returns:
		df: dataframe with eseperate sameAs property
	
	"""
	for index, row in df.iterrows():
		if row['sameAs'] != " ":
			sameas_format = []
			split_sameas = row['sameAs'].split('|')
			for s in split_sameas:
				s = s.replace(" ", "")
				if s != row['Stem']:
					sameas_format.append("chem/{}".format(s))
			if len(sameas_format)>0:
				df.loc[index, 'sameAs'] = ",".join(sameas_format)
	return df

def set_flags():
	global _FLAGS
	_FLAGS = flags.FLAGS
	flags.DEFINE_string('output_dir', 'scripts/CSVs/usan.csv',
					 	'Output directory for generated files.')
	flags.DEFINE_string('input_dir', 'scripts/input/usan.xlsx',
                    	'Input directory where .dmp files downloaded.')
	_FLAGS(sys.argv)

def driver_function(df):
	df = remove_null_entries(df)
	df = format_stem_definitions(df)
	df = format_word_stem(df)
	df = format_usan_specialization(df)
	df = format_dcid(df)
	df = format_examples(df)
	for index, row in df.iterrows():
		stem = row['Stem']
		stem_type = row['Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)']
		# dropping unwanted empty rows
		if str(stem_type) in ["NaN", "nan"] and str(stem) in ["NaN", "nan"]:
			df.drop(index,inplace=True)
		# dropping unwanted text rows
		if str(stem_type).startswith("*"):
			df.drop(index,inplace=True)
	df_final=df
	df_final.apply(check_for_illegal_charc)
	return df_final


def main(_FLAGS):
	file_input = _FLAGS.input_dir
	file_output = _FLAGS.output_dir
	df1 = pd.read_excel(file_input)
	# filtering the required columns
	df = df1[[
		'Stem','Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)','Definition',
		'Examples'
	]]
	df = driver_function(df)
	df = format_sameas(df)
	df_final = df[[
		"Stem","Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)","Definition",
		"Examples","WordStem","SpecializationOf","dcid", "sameAs"
	]]
	df_final.to_csv(file_output,
				 	doublequote=False,
				 	escapechar='\\',
				 	index=False)


if __name__ == '__main__':
	set_flags()
	main(_FLAGS)