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
'''
Author: Mariam Benazouz
Date: 07/27/2022
Name: compile_stitch.py
Description: combines drug data spread across three files
@PATH_SOURCES   file path for sources.tsv file (contains 
                various source codes for drugs)
@PATH_INCHIKEYS   file path for inchikeys.tsv file (contains 
                  InChIKeys for drugs)
@PATH_CHEMICALS   file path for chemicals.tsv file (contains 
                  drug names and SMILES string)
'''
# Import Data Commons
import datacommons as dc

# Import other required libraries
from functools import reduce
from pandas.core.common import SettingWithCopyWarning

import gc
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os
import pandas as pd
import requests
import sys 
import time
import warnings

DELAY_TIME = 5
TRIAL_LIMIT = 5
    
def reorder_df(merged_df): 
    """
    Orders df by ascending stereo CID

    Parameters:
    ----------
    merged_df: pandas dataframe
        merged df that includes data from chemicals.tsv, 
        sources.tsv, and inchikeys.tsv
    
    Returns:
    --------
    Pandas dataframe 
    
    TEST:
    df_reordered = reorder_df(PATH_CHEMICALS)
    assert(type(df_reordered) == pd.core.frame.dataframe)
    """
    merged_df['CIDs'] = merged_df["stereo_chemical_id"]\
        .str.replace("CIDs","") 
    merged_df = merged_df.sort_values(by = ['CIDs']) 
    merged_df = merged_df.reset_index(drop = True) 
    merged_df = merged_df.drop(columns = ['CIDs'])
    return(merged_df)

def chemicals_reformat(file_name): 
    """
    Reformat the 'chemicals.v5.0.tsv' such that 
    complementary stereo and flat chemical IDs are on 
    the same row, but separate columns 
    
    Parameters:
    ----------
    file_name: str
        'chemicals.v5.0.tsv'

    Returns:
    --------
    Pandas dataframe that has the corresponding stereo and flat 
    chemical IDs on the same row as well as other information 
    including chemical name, molecular weight, and SMILES string. 
    
    TEST:
    df_chemicals_reformatted = chemicals_reformat(PATH_CHEMICALS)
    assert(type(df_chemicals_reformatted) == pd.core.frame.dataframe)
    """
    df_drug_chemicals= pd.read_table(file_name, header=None,
            names = ['chemical_id', 'name', 'molecular_weight', 
            'SMILES_string']) 
    df_drug_chemicals_cid_s = df_drug_chemicals[
            df_drug_chemicals['chemical_id'].str.contains('s')]
    df_drug_chemicals_cid_m = df_drug_chemicals[
            df_drug_chemicals['chemical_id'].str.contains('m')]
    df_drug_chemicals_cid_s = df_drug_chemicals_cid_s.rename(
                columns = {'chemical_id': 'stereo_chemical_id'})
    df_drug_chemicals_cid_m = df_drug_chemicals_cid_m.rename(
                columns = {'chemical_id': 'flat_chemical_id'})
    chemicals_reformatted = pd.concat([df_drug_chemicals_cid_s,      
        df_drug_chemicals_cid_m], axis = 0).groupby('name').agg({
        'flat_chemical_id': 'first', 'stereo_chemical_id': 
        'first', 'molecular_weight':'first', 
        'SMILES_string': 'first'}).reset_index() 
    chemicals_reformatted = reorder_df(chemicals_reformatted)
    return(chemicals_reformatted)

def clean_inchikey_sources(new_df):
    """
    Organize different source rows into their own columns
    
    Parameters:
    ----------
    new_df: pandas dataframe
        merged df that includes data from 
        sources.tsv and inchikeys.tsv
    
    Returns:
    --------
    Pandas dataframe 
    
    TEST:
    df = clean_inchikey_sources(PATH_SOURCES)

    assert(type(df) == pd.core.frame.dataframe)
    """

    new_df['CIDs'] = new_df["stereo_chemical_id"].str.replace("CIDs","")     
    new_df['CIDs'] = [ele.lstrip('0') for ele in new_df['CIDs']]
    new_df['CIDs'] = new_df['CIDs'].astype(float).astype('Int64')

    new_df = new_df.loc[new_df.CIDs == new_df.source_cid]
    new_df = new_df.drop(columns = ['CIDs'])

    new_df['code'] = new_df['code'].astype(str)

    new_df_formatted = new_df.assign(source=new_df[\
        'source'].str.split(' ')).explode('source').groupby([\
        'flat_chemical_id', 'stereo_chemical_id', 'source_cid', 'inchikey', 'source'])['code']\
        .agg(lambda x: f'''{', '.join(x)}''')\
        .unstack(fill_value = '').reset_index()

    new_df_formatted = new_df_formatted.rename(columns =
        {'ATC': 'ATC_code', 'BindingDB':'BindingDB_code', 
         'ChEBI':'ChEBI_code', 'ChEMBL':'ChEMBL_code', 
         'KEGG': 'KEGG_code','PC':'PC_code','PS': 'PS_code'})
    
    return(new_df_formatted)

def fix_PC_column(merged_df):
    """
    Remove values in the PC column that match source_cid
    
    Parameters:
    ----------
    merged_df: pandas dataframe
        merged df that includes data from chemicals.tsv, 
        sources.tsv, and inchikeys.tsv

    Returns:
    --------
    Pandas dataframe 
    
    TEST:
    merged_df = merge_dfs(PATH_SOURCES, PATH_INCHIKEYS, PATH_CHEMICALS)  
    merged_df = fix_PC_column(merged_df)
    assert(type(merged_df) == pd.core.frame.dataframe)
    """
    merged_df1 = merged_df.assign(PC_code=merged_df[
        'PC_code'].str.split(',')).explode('PC_code')
    merged_df1['source_cid'] = merged_df1[
        'source_cid'].astype(float).astype('Int64')
    merged_df1['PC_code'] = merged_df1['PC_code'].astype(
        float).astype('Int64')
    merged_df1=merged_df1.loc[~(merged_df1[
        'PC_code'] == merged_df1['source_cid'])]
    merged_df1['source_cid'] = merged_df1['source_cid'].astype(str)
    merged_df1['PC_code'] = merged_df1['PC_code'].astype(str)
    PC_codes=merged_df1.groupby('source_cid')[
        'PC_code'].apply(', '.join).reset_index()
    PC_codes['source_cid'] = PC_codes[
        'source_cid'].astype(float)
    PC_codes = PC_codes.sort_values(by = ['source_cid']) 
    merge_df3=pd.merge(merged_df, PC_codes, 
        on='source_cid', how='outer')
    merge_df3 = merge_df3.drop(columns = ['PC_code_x', 
        'flat_chemical_id_y'])
    merge_df3 = merge_df3.rename(columns = {'PC_code_y': 
        'PC_code', 'flat_chemical_id_x': 'flat_chemical_id'})
    merge_df3.fillna("",inplace=True) 
    return(merge_df3)

def recursive_query(query_str, trial_num):
  """
  Queries Data Commons with the given query string.

  If the query results in an error, then this function 
  will be recursively called after a delay of DELAY_TIME seconds 
  until the query is resolved or the TRIAL_LIMIT has been exceeded.

  Args:
      query_str: The query to be passed to Data Commons.
      trial_num: The number of times the query has been attempted.
  
  Returns:
    The result of the query from Data Commons which is an array of dictionaries.
  
  Raises:
    If the TRIAL_LIMIT is exceeded, then the error thrown by Data Commons is
    raised.
  """
  try:
    return dc.query(query_str) # this is the actual query to Data Commons
  except:
    time.sleep(DELAY_TIME)
    if trial_num < TRIAL_LIMIT:
        return recursive_query(query_str, trial_num+1)
    print('exceeded trial limit: ' + query_str)
    raise

def conduct_query(query_template, query_arr):
  """
  Generates query strings and intiates queries user helper function.
  
  Chunks the given array into smaller sizes and uses the given template to
  create queries of manageable size for the Data Commons server. Each generated
  query string is passed to the helper function recursive_query.

  Args:
      query_template: The template of the query which needs to be filled in with
          the given array. The template should have only one missing value
          denoted with {0}.
      querry_arr: The array to fill in the given template.
  
  Returns:
      The results of the smaller queries from Data Commons concatonated into one
      result array.
  """
  result = []
  i = 0
  chunk_size = 400

  while (i+chunk_size < len(query_arr)):
    query_str = query_template.format('" "'.join(query_arr[i:i+chunk_size]))
    result.extend(recursive_query(query_str, 0))
    i+= chunk_size

  query_str = query_template.format('" "'.join(query_arr[i:]))
  result.extend(recursive_query(query_str, 0))
  return result


def find_mesh_dcid(merged_df):
    """
    Adds corresponding MeSHDescriptor DCID and Chemical 
    Compound DCID for a given drug name as a column in df 

    Parameters:
    ----------
    merged_df: pandas dataframe
        merged df that includes data from chemicals.tsv, 
        sources.tsv, and inchikeys.tsv

    Returns:
    --------
    Pandas dataframe 
    
    TEST:
    merged_df = merge_dfs(PATH_SOURCES, PATH_INCHIKEYS, PATH_CHEMICALS)  
    merged_df = fix_PC_column(merged_df)
    merged_df = find_mesh_dcid(merged_df)
    merged_df = find_inchikey(merged_df)
    assert(type(merged_df) == pd.core.frame.dataframe)
    """
    query_str_mesh = ''' 
        SELECT ?dcid
        WHERE {{
        ?dcid typeOf MeSHDescriptor .
        ?dcid descriptorName "{0}" .
        }}
        '''  
    merged_df['name']=[x.capitalize() for x in merged_df['name']]
    name_list = merged_df['name']
    results_mesh=conduct_query(query_str_mesh, name_list)
    res = [i for n, i in enumerate(results_mesh) if i not in results_mesh[:n]]
    #no duplicates
    cga_list = [row['?dcid'] for row in res]
    cga_to_candidate = dc.get_property_values(cga_list, 'descriptorName')
    dcid_mesh_map = {}  #invert dict
    for k,v in cga_to_candidate.items():
        for x in v:
            dcid_mesh_map.setdefault(x,[]).append(k)

    merged_df['mesh_dcid'] = merged_df['name'].map(dcid_mesh_map) 
    merged_df['mesh_dcid'] = merged_df['mesh_dcid'].str[0]
    
    merged_df['chembl_dcid'] = (merged_df.ChEMBL_code.str.strip('"') 
        .str.split(', ').apply(lambda x: ['bio/' + i for i in x if i]
            if isinstance(x, list) 
            else x).str.join(', ')) 
    return(merged_df)


def merge_dfs(PATH_SOURCES, PATH_INCHIKEYS, PATH_CHEMICALS): 
    """
    merges dfs that include data from chemicals.tsv, 
    sources.tsv, and inchikeys.tsv into one pandas df 

    Parameters:
    ----------
    sources_df: pandas dataframe
    inchikeys_df: pandas dataframe
    chemicals_df: pandas dataframe
    
    Returns:
    --------
    Pandas dataframe 
    
    TEST:
    merged_df = merge_dfs(PATH_SOURCES, PATH_INCHIKEYS, PATH_CHEMICALS)  
    assert(type(merged_df) == pd.core.frame.dataframe)
    """
    # load in and prep files 
    df_sources = pd.read_csv(PATH_SOURCES, sep = '\t', names =  
        ['flat_chemical_id', 'stereo_chemical_id', 'source', 'code']) 
    df_inchikeys = pd.read_csv(PATH_INCHIKEYS, sep = '\t', names = 
        ['flat_chemical_id', 'stereo_chemical_id', 'source_cid', 'inchikey']) 
    df_chemicals = chemicals_reformat(PATH_CHEMICALS)  
    # merge sources and inchikeys 
    sources_inchikeys = reduce(lambda x,y: pd.merge(x, y, 
        on = ['flat_chemical_id', 'stereo_chemical_id'], how = 'outer'), 
        [df_sources, df_inchikeys])
    # clean up sources and inchikeys 
    sources_inchikeys = clean_inchikey_sources(sources_inchikeys)
    # merge sources, inchikeys, and chemicals
    merged_df = reduce(lambda x,y: pd.merge(x, y, 
        on = ['stereo_chemical_id'], how = 'outer'), 
        [sources_inchikeys, df_chemicals])
    return (merged_df)

def find_inchikey(merged_df):  
    """
    Conducts query to check if the InChIKey string is an exact match
    to Data Commons

    Parameters:
    ----------
    merged_df: pandas dataframe
        merged df that includes data from chemicals.tsv, 
        sources.tsv, and inchikeys.tsv

    Returns:
    --------
    Pandas dataframe 
    
    TEST:
    merged_df = merge_dfs(PATH_SOURCES, PATH_INCHIKEYS, PATH_CHEMICALS)  
    merged_df = mesh_dcid_find(merged_df)
    merged_df = format_df(merged_df)
    final_df = find_string(merged_df)

    assert(type(final_df) == pd.core.frame.dataframe)
    """
    query_str = '''
        SELECT ?dcid
        WHERE {{
        ?dcid inChIKey "{0}" .
            }}
        '''
    string_values = merged_df['inchikey']
    results_dcid=conduct_query(query_str, string_values)
    if len(results_dcid)==0:
        merged_df["same_as"] = ""
        
    else:
        results_dcid = [row['?dcid'] for row in results_dcid]

        string_match = dc.get_property_values(results_dcid, 'inChIKey')

        string_map = {}  #invert dict
        for k,v in string_match.items():
            for x in v:
                string_map.setdefault(x,[]).append(k)

        merged_df['same_as'] = merged_df['inchikey'].map(string_map) 
        merged_df['same_as'] = merged_df['same_as'].str[0]
    return(merged_df)

def pubchem_id(merged_df): 
    """
    Create PubChem ID column and its corresponding DCID
    
    Parameters:
    ----------
    merged_df: pandas dataframe
        merged df that includes data from chemicals.tsv, 
        sources.tsv, and inchikeys.tsv

    Returns:
    --------
    Pandas dataframe 
    
    TEST:
    merged_df = merge_dfs(PATH_SOURCES, PATH_INCHIKEYS, PATH_CHEMICALS)  
    merged_df = fix_PC_column(merged_df)
    final_df1 = find_mesh_dcid(merged_df)
    final_df1 = find_inchikey(final_df1)
    final_df1 = pubchem_id(final_df1)
    assert(type(final_df1) == pd.core.frame.dataframe)
    """
    merged_df['pubchem_ID'] = merged_df["stereo_chemical_id"].str.replace("CIDs","")
    merged_df['pubchem_ID'] = [ele.lstrip('0') for ele in merged_df['pubchem_ID']]
    merged_df['pubchem_ID']= 'CID' + merged_df['pubchem_ID']
    merged_df['pubchem_dcid']='chem/'+merged_df['pubchem_ID']
    return(merged_df)

def find_IDs(merged_df):
    """
    Find the corresponding PubChem IDs, InChiKeys, DCIDs, as well as
    PubChem IDs of similar compounds for the corresponding CID pairs
    
    Parameters:
    ----------
    merged_df: pandas dataframe
        merged df that includes data from chemicals.tsv, 
        sources.tsv, and inchikeys.tsv

    Returns:
    --------
    Pandas dataframe 
    
    TEST:
    merged_df = merge_dfs(PATH_SOURCES, PATH_INCHIKEYS, PATH_CHEMICALS)  
    merged_df = find_IDs(merged_df)
    assert(type(merged_df) == pd.core.frame.dataframe)
    """  
    final_df = fix_PC_column(merged_df)
    final_df = find_mesh_dcid(final_df)
    final_df = find_inchikey(final_df)
    final_df = pubchem_id(final_df)
    return(final_df)

def format_text_cols(merged_df):
    """
    Reformat the merged df such that the text columns 
    have quotes

    Parameters:
    ----------
    merged_df: pandas dataframe
        merged df that includes data from chemicals.tsv, 
        sources.tsv, and inchikeys.tsv

    Returns:
    --------
    Pandas dataframe 
    
    TEST:
    df_formatted = format_text_cols(PATH_CHEMICALS)

    assert(type(df_formatted) == pd.core.frame.dataframe)
    """
    merged_df['name']='"\\"' + merged_df['name'] + '\\""'
    merged_df['inchikey']='"' + merged_df['inchikey'] + '"'
    merged_df['SMILES_string']='"' + merged_df['SMILES_string'] + '"'
    merged_df['chembl_dcid']='"' + merged_df['chembl_dcid'] + '"'
    merged_df['ATC_code']='"' + merged_df['ATC_code'] + '"'
    merged_df['ChEBI_code']='"' + merged_df['ChEBI_code'] + '"'
    merged_df['DrugBank']='"' + merged_df['DrugBank'] + '"'
    merged_df['KEGG_code']='"' + merged_df['KEGG_code'] + '"'
    #remove empty double quotes
    replacer = lambda x: x.replace('""','')
    merged_df = merged_df.apply(replacer)
    #remove empty single quotes
    replacer = lambda x: x.replace("''","")
    merged_df = merged_df.apply(replacer)
    replacer = lambda x: x.replace('"\\"\\""','')
    merged_df = merged_df.apply(replacer)
    return(merged_df)

def format_df(merged_df): 
    """
    Reformat the merged df such that the text columns 
    have quotes and the df is ordered by ascending stereo CID

    Parameters:
    ----------
    merged_df: pandas dataframe
        merged df that includes data from chemicals.tsv, 
        sources.tsv, and inchikeys.tsv

    Returns:
    --------
    Pandas dataframe 
    
    TEST:
    merged_df = merge_dfs(PATH_SOURCES, PATH_INCHIKEYS, PATH_CHEMICALS)  
    final_df = find_IDs(merged_df)
    final_df_formatted = format_df(final_df)
    assert(type(final_df_formatted) == pd.core.frame.dataframe)
    """
    merged_df = format_text_cols(merged_df)
    final_df = reorder_df(merged_df)
    final_df = final_df.replace(np.nan,'',regex=True)
    final_df = final_df.drop(columns = ['ChEMBL_code'])  
    final_df['stereo_chemical_id'].replace('', np.nan, inplace=True)
    final_df.dropna(subset=['stereo_chemical_id'], inplace=True)
    final_df['source_cid'] = final_df['source_cid'].astype(float).astype('Int64')
    return(final_df)

def main():
    PATH_SOURCES = sys.argv[1]
    PATH_INCHIKEYS = sys.argv[2]
    PATH_CHEMICALS = sys.argv[3]
    merged_df = merge_dfs(PATH_SOURCES, PATH_INCHIKEYS, PATH_CHEMICALS)  
    final_df = find_IDs(merged_df)
    final_df_formatted = format_df(final_df)
    final_df_formatted.to_csv('drugs.csv')  
    
if __name__ == '__main__':
    main()