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
Date: 08/24/2022
Name: protein_actions.py
Description: map protein names to Ensembl IDs in the actions.tsv
Run: python3 actions.py
'''
import pandas as pd
import numpy as np

from create_mapping_file import *
from protein_drug_interactions import *

def format_actions_file(PATH_PROTEIN_ACTION): 
    """
    Format the protein_actions file to have certain columns in Enum format
    and organize chemicals and proteins in two separate columns
    
    Parameters:
    ----------
    PATH_PROTEIN_ACTION: string
        path to csv that includes various protein-drug interactions
    
    Returns:
    --------
    Pandas dataframe 
    """
    df_protein_actions = pd.read_csv(PATH_PROTEIN_ACTION, sep = '\t')
    d = {'t': True, 'f': False}
    df_protein_actions['a_is_acting']=df_protein_actions[
        'a_is_acting'].map(d)
    df_protein_actions['mode'] = df_protein_actions['mode'].apply(
        lambda x: x.capitalize())
    df_protein_actions['mode'] = df_protein_actions['mode'].str.replace(
        "Pred_bind","PredictedToBind")
    # adding enum
    df_protein_actions['mode']= 'ChemicalInteractionMode' + df_protein_actions[
        'mode'] 
    df_protein_actions['action'] = df_protein_actions['action'].astype(str).str.replace(
        "activation","EnzymaticReactionEffectActivation")
    df_protein_actions['action'] = df_protein_actions['action'].astype(str).str.replace(
        "inhibition","EnzymaticReactionEffectInihibition")
    # identify incorrect rows
    m = df_protein_actions['item_id_a'].str.startswith('9606.')
    # swap
    df_protein_actions.loc[m, 'item_id_a'], df_protein_actions.loc[m, 'item_id_b'] =\
        df_protein_actions.loc[m, 'item_id_b'], df_protein_actions.loc[m, 'item_id_a']
    # flip boolean
    df_protein_actions.loc[m, 'a_is_acting'] = ~df_protein_actions.loc[m, 
        'a_is_acting']
    df_protein_actions.rename(columns={'item_id_a': 'chemical', 
        'item_id_b': 'protein', 'a_is_acting': 'chemical_is_acting'}, 
        inplace=True)
    df_protein_actions=df_protein_actions.replace('nan', np.NaN)
    return(df_protein_actions)

def map_protein_actions_name(actions_df, merged_protein_df):
    """
    Map the protein-drug interactions dataframe to the mapping file 
    using only archived ENSEMBLs
    
    Parameters:
    ----------
    df_protein_interactions: string
        path to csv that includes various protein-drug interactions
    merged_protein_df: pandas dataframe
        mapping file that has ENSEMBL IDs with their corresponding 
        protein name
    
    Returns:
    --------
    Pandas dataframe 
    """
    actions_df['Protein stable ID'] = actions_df["protein"]\
        .str.replace("9606.","")  
    df1 = merged_protein_df.merge(actions_df, on = 'Protein stable ID', 
        how = 'right')
    df2 = df1.loc[df1['STRING'].notna().groupby([df1['Protein stable ID'], 
        df1['chemical'], df1['chemical_is_acting']], sort = False).idxmax()]
    df2 = df2.reset_index(drop=True)
    return(df2)

def create_final_mapped_actions_df(PATH_PROTEIN_ACTION, merged_protein_df): 
    """
    Add protein names to the protein actions df

    Parameters:
    ----------
    df_protein_interactions: string
        path to csv that includes various protein-drug 
        interactions
    merged_protein_df: pandas dataframe
        mapping file that has ENSEMBL IDs with their 
        corresponding protein name
    
    Returns:
    --------
    Pandas dataframe 
    """
    actions_df = format_actions_file(PATH_PROTEIN_ACTION)
    current_df = map_protein_actions_name(actions_df, 
        merged_protein_df)
    mapped_df = check_other_ids(current_df, merged_protein_df)
    final_df = add_dcid(mapped_df)
    final_df.fillna('', inplace=True)
    return(final_df)

def main(): 
    PATH_PROTEIN_ACTION = sys.argv[1]
    PATH_MAPPING = sys.argv[2]
    mapping_df = pd.read_csv(PATH_MAPPING)
    final_df = create_final_mapped_actions_df(PATH_PROTEIN_ACTION, mapping_df)
    final_df.to_csv('protein_actions.csv', index=False)    
    
if __name__ == '__main__':
	main()