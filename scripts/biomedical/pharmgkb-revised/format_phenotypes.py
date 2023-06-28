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
Date: 02/20/2023
Name: format_variants 
Description: converts a .tsv from PharmGKB into a clean csv format, 
where each columns contains linkages or references to only 
database only for the purpose of clarity and understanding
@file_input: input .tsv from PharmGKB
@file_output: formatted .csv with PharmGKB and other database annotations
"""
import pandas as pd 
import numpy as np
import sys
import re

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

def format_external_vocab(df):
	df = df.rename(columns={'PharmGKB Accession Id':'pharmGKBID','External Vocabulary':'externalVocab', 'Cross-references':'crossReferences'})
	df = df.replace('"', '', regex=True)
	df = df.assign(externalVocab=df.externalVocab.str.split(",")).explode('externalVocab')
	df[['A', 'B']] = df['externalVocab'].str.split(':', 1, expand=True)
	df['A'] = df['A'].astype(str).map(lambda x: re.sub('[^A-Za-z0-9]+', '', x))
	col_add = list(df['A'].unique())
	for newcol in col_add:
	    df[newcol] = np.nan
	    df[newcol] = np.where(df['A'] == newcol, df['B'], np.nan)
	    df[newcol] = df[newcol].astype(str).replace("nan", np.nan)
	df = df.groupby(by='pharmGKBID').agg(dict.fromkeys(df.columns[0:], replace_nan_func))
	df = df.drop(['A', 'B', 'externalVocab'], axis =1)
	df = df.iloc[:,4:8]
	return df 

def format_cols(df):
	df = df[df['MeSH'].notna()]
	list_cols = ['MeSH', 'SnoMedCT', 'UMLS', 'NDFRT']
	for i in list_cols:
	    df[i] = df[i].str.replace(r"\([^()]*\)", "", regex=True)
	    df[i] = df[i].str.split('(').str[0]
	df['MeSHDcid'] = 'bio/' + df['MeSH']
	return df 

def main():
	file_input = sys.argv[1]
	file_output = sys.argv[2]
	df = pd.read_csv(file_input, sep = '\t')
	df = format_external_vocab(df)
	df = format_cols(df)
	df.to_csv(file_output, doublequote=False, escapechar='\\')


if __name__ == '__main__':
	main()