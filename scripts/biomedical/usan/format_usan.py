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

import pandas as pd
import numpy as np
import sys
import csv 

def remove_null_entries(df):
	df = df.dropna(how='all') ## drop all rows with all empty values
	df = df.iloc[:, [0, 1, 2, 3]] ## drop all columns with all empty values
	mask = df.drop("Stem",axis=1).isna().all(1) & df['Stem'].notna() ## Drop rows where stem is not null but rest of the columns are null
	df = df[~mask]
	return df

def isNaN(num):
	return num != num

def format_stem_definitions(df):
	df['Stem'] = df['Stem'].str.replace(r"\(.*\)","") ## removes text in parantheses
	df['Definition'] = df['Definition'].str.replace(r"\(.*\)","")
	df['Definition'] = df['Definition'].replace('',np.nan,regex = True)
	df = df.assign(Stem=df.Stem.str.split(",")).explode('Stem')
	df = df.assign(Stem=df.Stem.str.split("/")).explode('Stem')
	df = df.replace(r'\r+|\n+|\t+','', regex=True) ## remove endline and tab chars
	df['Stem'] = df['Stem'].str.replace('\W', '')
	return df

def format_empty_rows(df):
	df = df.reset_index(drop=True)
	for index,row in df.iterrows():
		val = df.loc[index,'Definition']
		val1 = df.loc[index,'Stem']
		if(isNaN(val) & isNaN(val1)):
			df.loc[index,'Definition'] = df.loc[index-1,'Definition']
			df.loc[index,'Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)'] = df.loc[index-1,'Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)']
			df.loc[index,'Stem'] = df.loc[index-1,'Stem']
	return df

def format_word_stem(df):
	df['WordStem'] = np.nan
	for index,row in df.iterrows():
		val = df.loc[index,'Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)']
		if(~isNaN(val)):
			val = str(val)
			if((val[0] == "-") & (val[-1] == "-")):
				df.loc[index,'WordStem'] = "WordStemInfix"
			elif(val[0] == "-"):
				df.loc[index,'WordStem'] = "WordStemPrefix"
			else:
				df.loc[index,'WordStem'] = "WordStemSuffix"
	return df 

def format_usan_specialization(df):
	df['SpecializationOf'] = np.nan
	for index,row in df.iterrows():
		val = df.loc[index,'Stem']
		if(isNaN(val)):
			if(isNaN(df.loc[index-1,'SpecializationOf'])):
				df.loc[index,'SpecializationOf'] = df.loc[index-1,'Stem']
			else:
				df.loc[index,'SpecializationOf'] = df.loc[index-1,'SpecializationOf']
	return df

def format_dcid(df):
	df['dcid'] = df['Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)'].str.split(' ').str[0]
	df['dcid'] = df['dcid'].str.split().str[0]
	df['dcid'] = df['dcid'].str.replace('\W', '')
	df = df.dropna(subset=['dcid'])
	df['name'] = df['dcid']
	df['dcid'] = 'chem/' +  df['dcid']
	df['SpecializationOf'] = "chem/" + df['SpecializationOf'].dropna().astype(str)	       
	return df

def format_chembl(df_chembl):
	df_chembl = df_chembl.iloc[:, [5,6]]
	df_chembl.rename(columns={'USAN Stem': 'dcid', 'USAN Year':'year'}, inplace=True)
	df_chembl = df_chembl.assign(dcid=df_chembl.dcid.str.split(";")).explode('dcid')
	df_chembl['dcid'] = df_chembl['dcid'].str.replace('\W', '')
	df_chembl = df_chembl.dropna()
	df_chembl['dcid'] = "chem/" + df_chembl['dcid']
	return df_chembl

def format_year(df, df_chembl):
	df1 = pd.merge(df, df_chembl, on=['dcid'], how='left')
	df1.rename(columns={'Prefix (xxx-), Infix (-xxx-), or Suffix (-xxx)': 'StemType'}, inplace=True)
	df1['year'] = df1['year'].astype(str).apply(lambda x: x.replace('.0',''))
	df1.replace("nan", np.nan, inplace=True)
	df1 = df1.drop_duplicates()
	df1.update('"' +
				  df1[['Stem', 'StemType', 'Definition', 'Examples', 'WordStem', 'SpecializationOf', 'dcid', 'name'
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
	return df_final

def main():
	file_input = sys.argv[1]
	file_chembl = sys.argv[2]
	file_output = sys.argv[3]
	df = pd.read_csv(file_input, low_memory=False)
	df_chembl = pd.read_csv(file_chembl, sep = "\t")
	df_final = driver_function(df, df_chembl)
	df_final.to_csv('usan_output.csv', doublequote=False, escapechar='\\')
	

if __name__ == '__main__':
	main()