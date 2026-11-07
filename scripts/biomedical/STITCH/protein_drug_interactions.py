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
Name: protein_drug_interactions.py
Description: map protein names to Ensembl IDs in the protein_interactions.tsv
Run: python3 protein_drug_interactions.py
'''
import numpy as np
import pandas as pd
import sys
from create_mapping_file import *
    
def map_protein_name(PATH_PROTEIN_INTERACTIONS, merged_protein_df):
    """
    Map the protein-drug interactions dataframe to the mapping file 
    using only archived ENSEMBLS
    
    Parameters:
    ----------
    PATH_PROTEIN_INTERACTIONS: string
        path to csv that includes various protein-drug interactions
    merged_protein_df: pandas dataframe
        mapping file that has ENSEMBL IDs with their corresponding 
        protein name
    
    Returns:
    --------
    Pandas dataframe 
    """
    df_protein_interactions = pd.read_csv(PATH_PROTEIN_INTERACTIONS, 
        sep = '\t')
    df_protein_interactions['Protein stable ID'] = df_protein_interactions[
        "protein"].str.replace("9606.","")  
    df1 = merged_protein_df.merge(df_protein_interactions, on = 'Protein stable ID', 
        how = 'right')
    df2 = df1.loc[df1['STRING'].notna().groupby([df1['Protein stable ID'], 
        df1['chemical']], sort = False).idxmax()]
    df2 = df2.reset_index(drop=True)
    return(df2)

def check_other_ids(current_df, merged_protein_df):
    """
    Check updated EMSEMBL IDs if there is no match to the archived ENSEMBL ID

    Parameters:
    ----------
    current_df: pandas dataframe
        mapped drug-protein interactions file only according to 
        archived ENSEMBLS
    merged_protein_df: pandas dataframe
        mapping file that has ENSEMBL IDs with their corresponding 
        protein name
    
    Returns:
    --------
    Pandas dataframe 
    """
    bad_matches_df=current_df.loc[current_df['UniProtKB-ID'].isna()]\
        ['Protein stable ID'].drop_duplicates(keep='first')
    mapping_df=merged_protein_df
    mapping_df.Ensembl_PRO = mapping_df.Ensembl_PRO.astype(str).str.split(',')
    mapping_df = mapping_df.explode('Ensembl_PRO')
    mapping_df.Ensembl_PRO = mapping_df.Ensembl_PRO.astype(str).str.split('.')\
        .str[0].astype(str)
    mapping_df=mapping_df[['UniProtKB-ID', 'Ensembl_PRO']]
    extra=mapping_df.merge(bad_matches_df, left_on='Ensembl_PRO', 
        right_on='Protein stable ID', how='right')
    extra=extra.drop_duplicates(keep='first')
    current_df_final = extra.merge(current_df, on='Protein stable ID', 
        how='right')
    current_df_final['UniProtKB-ID_y']=current_df_final['UniProtKB-ID_y']\
        .fillna(current_df_final['UniProtKB-ID_x'])
    final_bad_matches=current_df_final.loc[current_df_final['UniProtKB-ID_y']
        .isna()]['protein'].drop_duplicates()
    current_df_final.drop(['UniProtKB-ID_x', 'Ensembl_PRO_x','Ensembl_PRO_y', 
        'Protein stable ID', 'STRING', 'protein'], axis=1, inplace=True)
    current_df_final.rename(columns={'UniProtKB-ID_y': 'protein'}, inplace=True)
    current_df_final = current_df_final.drop_duplicates(keep='first')
    
    print(final_bad_matches)
    return(current_df_final)

def add_dcid(mapped_df): 
    """
    Add PubChem DCIDs for the drug, protein and the drug-protein interaction. 
    
    Parameters:
    ----------
    mapped_df: pandas dataframe
        mapped drug-protein interactions file that includes protein names

    Returns:
    --------
    Pandas dataframe 
    """
    mapped_df.chemical=mapped_df.chemical.replace(r'CID[a-z]?0*',
        'chem/CID',regex=True)
    mapped_df['dcid']= mapped_df['chemical'] + "_" + mapped_df['protein']
    mapped_df['protein'] = 'bio/' + mapped_df['protein']
    mapped_df['name_interaction'] = mapped_df['dcid'].str.replace("chem/","")
    mapped_df.fillna('', inplace=True)
    return(mapped_df)

def create_final_mapped_df(PATH_PROTEIN_INTERACTIONS, merged_protein_df): 
    """
    Add protein names to the drug-protein interaction df

    Parameters:
    ----------
    PATH_PROTEIN_INTERACTIONS: string
        path to csv that includes various protein-drug 
        interactions
    merged_protein_df: pandas dataframe
        mapping file that has ENSEMBL IDs with their 
        corresponding protein name
    
    Returns:
    --------
    Pandas dataframe 
    """
    current_df = map_protein_name(PATH_PROTEIN_INTERACTIONS, 
        merged_protein_df)
    mapped_df = check_other_ids(current_df, merged_protein_df)
    final_df = add_dcid(mapped_df)
    return(final_df)

def main(): 
    PATH_PROTEIN_INTERACTIONS = sys.argv[1]
    PATH_MAPPING = sys.argv[2]
    mapping_df = pd.read_csv(PATH_MAPPING)
    final_df = create_final_mapped_df(PATH_PROTEIN_INTERACTIONS, 
        mapping_df)
    final_df.to_csv('protein_drug_interactions.csv', index = False)    
    
if __name__ == '__main__':
    main()