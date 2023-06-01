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
Name: format_usan
Description: converts a .csv file containing USAN (United States Adopted Names) approved stems into a formatted .csv with stems and substems differentiated and dcids created.  
@file_input: input .csv from USAN database
@file_output: formatted .csv with USAN approved stems and substems
"""

# import the required packages
import pandas as pd
import numpy as np
import sys

#Disable false positive index chaining warnings
pd.options.mode.chained_assignment = None

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
	mask = df.drop("Stem",axis=1).isna().all(1) & df['Stem'].notna() ## Drop rows where the column `stem` is not null but rest of the columns are null
	df = df[~mask]
	df = df.replace(r'\r+|\n+|\t+','', regex=True) ## remove endline and tab chars
	return df

def isNaN(var):
	"""Determines whether a variable is null or not 
	Args:
		num: string value
	Returns:
		boolean whether the variable is null (True) or not (False)
	
	"""
	return var != var

def format_stem_definitions(df):
	"""Formats the USAN stem and definitions
	Args:
		df: dataframe with USAN stem and definition columns
	Returns:
		df: dataframe with formatted USAN stem and definition columns
	
	"""
	df[['Stem', 'Definition']] = df[['Stem', 'Definition']].astype(str).replace(r"\(.*\)","", regex=True) ## removes text from paranthesis
	df['Definition'] = df['Definition'].replace('',np.nan,regex = True) ## replace empty string with np.nan
	df = df.assign(Stem=df.Stem.str.split("[,/]")).explode('Stem') ## Explode Stem column based on comma and forward slash
	df['Stem'] = df['Stem'].str.replace('\W', '', regex=True) ## retain only text chars from stem columns
	return df

def format_empty_rows(df):
	"""Fills empty rows with important data once certain conditions are met
	Args:
		df: dataframe with empty row values
	Returns:
		df: dataframe with populated row values
	
	"""
	df = df.reset_index(drop=True) ## reindexes the dataframe
	df = df.astype(object).replace('nan', np.nan) ## replace 'nan strings with np.nan'
	for index,row in df.iterrows():
		val = df.loc[index,'Definition']
		val1 = df.loc[index,'Stem']
		if(isNaN(val) & isNaN(val1)): ## if both definition and stem values are empty for a row
			cols = ['Definition', 'Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)', 'Stem']
			for i in cols:
				df.loc[index,i] = df.loc[index-1,i] ## fetches the definition, prefix and stem from the previous row
	return df

def format_word_stem(df):
	"""Determines the word stem enum for each of the rows
	Args:
		df: dataframe without word stem categories
	Returns:
		df: dataframe with word stem categories
	
	"""
	df['WordElementType'] = np.nan
	for index,row in df.iterrows():
		val = df.loc[index,'Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)']
		if(~isNaN(val)): ## evaluate word stem based on non-empty value
			val = str(val)
			if((val[0] == "-") & (val[-1] == "-")): ## if the word starts and ends with a hyphen, it's an infix
				df.loc[index,'WordElementType'] = "WordElementTypeInfix"
			elif(val[0] == "-"):
				df.loc[index,'WordElementType'] = "WordElementTypePrefix" ## else, if the word starts with a hyphen, it's a prefix
			else:
				df.loc[index,'WordElementType'] = "WordElementTypeSuffix" ## if none of the above apply, it's a suffix
	return df 

def format_usan_specialization(df):
	"""Determines the word specialization for each stem word
	Args:
		df: dataframe without word specialization
	Returns:
		df: dataframe with word specialization
	
	"""
	df['SpecializationOf'] = np.nan
	for index,row in df.iterrows():
		val = df.loc[index,'Stem']
		if(isNaN(val)): ## if word stem is absent, it implies specialization is needed
			if(isNaN(df.loc[index-1,'SpecializationOf'])): ## if there's no specialization for the previous row, the previous stem is a specialization of the current one
				df.loc[index,'SpecializationOf'] = df.loc[index-1,'Stem']
			else:
				df.loc[index,'SpecializationOf'] = df.loc[index-1,'SpecializationOf'] ## else specializations are same for the previous and current rows
	return df

def format_dcid(df):
	"""Formats dcid for each stem word
	Args:
		df: dataframe without dcid
	Returns:
		df: dataframe with dcid
	
	"""
	df['dcid'] = df['Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)'].str.split(' ').str[0]
	df['dcid'] = df['dcid'].str.split().str[0] ## performs a split to retain only first substring
	df['dcid'] = df['dcid'].str.replace('\W', '', regex=True) ## retains only characters 
	df = df.dropna(subset=['dcid']) ## drops rows with empty dcids
	df['name'] = df['dcid']
	df['dcid'] = 'chem/' +  df['dcid']
	df['SpecializationOf'] = "chem/" + df['SpecializationOf'].dropna().astype(str)	       
	return df

def format_chembl(df_chembl):
	"""Fetches USAN stem and year from chembl dataframe
	Args:
		df: chembl dataframe
	Returns:
		df: chembl dataframe with only USAN years and stems
	
	"""
	df_chembl = df_chembl.iloc[:, [5,6]] ## only selects stem and year columns
	df_chembl.rename(columns={'USAN Stem': 'dcid', 'USAN Year':'year'}, inplace=True) ## renames the columns
	df_chembl = df_chembl.assign(dcid=df_chembl.dcid.str.split(";")).explode('dcid') ## explodes column on semi-colon
	df_chembl['dcid'] = df_chembl['dcid'].str.replace('\W', '', regex=True) ## retains only characters
	df_chembl = df_chembl.dropna()
	df_chembl['dcid'] = "chem/" + df_chembl['dcid'] ## creates dcid
	return df_chembl

def format_year(df, df_chembl):
	"""Formats the USAN year from df_chembl and joins with df on column year
	Args:
		df: chembl dataframe
	Returns:
		df: chembl dataframe with only USAN years and stems
	
	"""
	df1 = pd.merge(df, df_chembl, on=['dcid'], how='left')
	df1.rename(columns={'Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)': 'StemType'}, inplace=True)
	df1['year'] = df1['year'].astype(str).apply(lambda x: x.replace('.0',''))
	df1.replace("nan", np.nan, inplace=True)
	df1 = df1.drop_duplicates()
	df1.update('"' +
				  df1[['Stem', 'StemType', 'Definition', 'Examples', 'WordElementType', 'SpecializationOf', 'dcid', 'name'
					 ]].astype(str) + '"')
	df1.replace("\"nan\"", np.nan, inplace=True)
	return df1

def driver_function(df, df_chembl):
	df = remove_null_entries(df)
	df = format_stem_definitions(df)
	df = format_empty_rows(df)
	df = format_word_stem(df)
	df = format_usan_specialization(df)
	df = format_dcid(df)
	df_chembl = format_chembl(df_chembl)
	df_final = format_year(df, df_chembl)
	df_final.apply(check_for_illegal_charc)
	return df_final

def main():
	file_input = sys.argv[1]
	file_chembl = sys.argv[2]
	file_output = sys.argv[3]
	df = pd.read_csv(file_input, low_memory=False)
	df_chembl = pd.read_csv(file_chembl, sep = "\t")
	df_final = driver_function(df, df_chembl)
	df_final.to_csv(file_output, doublequote=False, escapechar='\\')
	

if __name__ == '__main__':
	main()
