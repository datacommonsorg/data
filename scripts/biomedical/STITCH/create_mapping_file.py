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
Name: create_mapping_file.py
Description: creates file that maps Ensembl IDs to protein names
Run: python3 create_mapping_file.py 
'''
import numpy as np
import pandas as pd
import sys

def reformat_data(df_ensembls, df_uniprot): 
    """
    Reformat the two dataframes containing Ensembl and UniProt IDs
    
    Parameters:
    ----------
    df_ensembls: pandas dataframe
        includes Ensembl Protein IDs 
    df_uniprot: pandas dataframe
        includes updated UniProt accession IDs and their protein entry names 
    Returns:
    --------
    2 pandas dataframes 
    """
    df_ensembls=df_ensembls.dropna(subset=['UniProtKB/Swiss-Prot ID', 
        'UniProtKB/TrEMBL ID'], how='all')
    df_ensembls = df_ensembls.fillna('')
    df_ensembls['ID'] = df_ensembls['UniProtKB/Swiss-Prot ID'] + ", "+ \
        df_ensembls['UniProtKB/TrEMBL ID']
    df_ensembls=df_ensembls[['ID', 'Protein stable ID_old']]
    df_ensembls=df_ensembls.replace(r'^\s*$', np.nan, regex=True)
    df_ensembls['ID'].fillna(df_ensembls['Protein stable ID_old'], 
        inplace=True)
    df_ensembls.drop_duplicates()
    df_uniprot = df_uniprot.pivot_table(index='UniProtKB/Swiss-Prot ID', 
        columns='identifier_type', values='value', aggfunc=','.join, 
        fill_value='')
    df_uniprot=df_uniprot[['Ensembl_PRO', 'STRING', 'UniProtKB-ID']]
    df_uniprot=df_uniprot.replace(r'^\s*$', np.nan, regex=True)
    df_uniprot = df_uniprot.reset_index(level=0)

    return(df_ensembls, df_uniprot) 

def add_old_accessions(df_secondary_accession_ids, df_uniprot):
    """
    Take the Uniprot ID df and add the corresponding archived accession 
    numbers for each protein  

    Parameters:
    ----------
    df_secondary_accession_ids: pandas dataframe
        includes archived UniProt accession IDs with their updated IDs
    df_uniprot: pandas dataframe
        includes updated UniProt accession IDs and their protein entry names 
    
    Returns:
    --------
    Pandas dataframe 
    """
    df_secondary_accession_ids['ID'] = df_secondary_accession_ids['old_id'] + "," + \
        df_secondary_accession_ids['new_id']
    df_ids_combined=df_secondary_accession_ids.melt('ID', 
        value_name = 'UniProtKB/Swiss-Prot ID')
    df_ids_combined=df_ids_combined[['ID', 'UniProtKB/Swiss-Prot ID']]
    uniprot_with_old_accessions=df_uniprot.merge(df_ids_combined, 
        on='UniProtKB/Swiss-Prot ID', how='outer')
    uniprot_with_old_accessions['ID'].fillna(uniprot_with_old_accessions[
        'UniProtKB/Swiss-Prot ID'], inplace=True)
    return(uniprot_with_old_accessions)

def combine_dfs(df_ensembls, uniprot_with_old_accessions):
    """
    Create a dataframe that has archived and updated ENSEMBL IDs, 
    archived and updated UniProt accession IDs along their corresponding 
    protein name

    Parameters:
    ----------
    df_ensembls: pandas dataframe
        includes Ensembl Protein IDs 
    uniprot_with_old_accessions: pandas dataframe
        includes archived and updated Uniprot accession IDs and their 
        protein entry names 
    
    Returns:
    --------
    Pandas dataframe 
    """
    uniprot_with_old_accessions.ID = uniprot_with_old_accessions.ID.str.split(',')
    uniprot_with_old_accessions = uniprot_with_old_accessions.explode('ID')
    df_ensembls.ID = df_ensembls.ID.str.split(', ')
    df_ensembls = df_ensembls.explode('ID')
    merged_protein_df = pd.merge(uniprot_with_old_accessions, df_ensembls, 
        how='right',  on = 'ID')
    merged_protein_df.fillna('', inplace=True)
    # Merge on ID
    merged_protein_df = (uniprot_with_old_accessions.merge(df_ensembls, 'left')
        .groupby('UniProtKB-ID').agg(set).applymap(lambda x: ', '
        .join(i for i in x if isinstance(i, str))).reset_index())
    merged_protein_df['Protein stable ID']=merged_protein_df['STRING']+ ", " + \
        merged_protein_df['Protein stable ID_old']
    merged_protein_df = merged_protein_df.replace(r'^\s*$', np.nan, regex = True)
    merged_protein_df['Protein stable ID'] = merged_protein_df["Protein stable ID"]\
        .str.replace("9606.ENSP","ENSP")  
    merged_protein_df['Protein stable ID'] = merged_protein_df[
        'Protein stable ID'].str.split(', ')
    merged_protein_df = merged_protein_df.explode('Protein stable ID')
    merged_protein_df.drop_duplicates(keep = 'first')
    merged_protein_df = merged_protein_df.reset_index(drop = True)
    mapping_df = merged_protein_df[['UniProtKB-ID', 'Ensembl_PRO', 'STRING', 
        'Protein stable ID']]
    mapping_df = mapping_df.drop_duplicates(keep = 'first')
    return(mapping_df)

def create_mapping_df(PATH_ARCHIVED_ENSEMBLS, PATH_ARCHIVED_ACCESSIONS, PATH_UNIPROT_MAPPING): 
    """
    Create a mapping dataframe that has ENSEMBL IDs with their corresponding 
    protein name by combining three datasets 

    Parameters:
    ----------
    PATH_ARCHIVED_ENSEMBLS: string
        path to csv that includes archived ENSEMBL IDs with their 
        UniProt accession IDs
    PATH_ARCHIVED_ACCESSIONS: string
        path to csv that includes archived UniProt accession IDs 
        with their updated IDs
    PATH_UNIPROT_MAPPING: string
        path to csv that includes Uniprot accession IDs and their 
        protein entry names 
    
    Returns:
    --------
    Pandas dataframe 
    """
    df_ensembls = pd.read_csv(PATH_ARCHIVED_ENSEMBLS, skiprows=1,  
        names=['Protein stable ID_old', 'UniProtKB/Swiss-Prot ID', 
        'UniProtKB/TrEMBL ID'])
    df_secondary_accession_ids = pd.read_csv(PATH_ARCHIVED_ACCESSIONS, 
        usecols=[0,24], names=['old_id', 'new_id'], sep = ' ', header=None, 
        skiprows = 31)
    df_uniprot = pd.read_csv(PATH_UNIPROT_MAPPING,  sep ='\t', names = 
        ['UniProtKB/Swiss-Prot ID', 'identifier_type', 'value'])
    df_ensembls, df_uniprot = reformat_data(
        df_ensembls, df_uniprot)
    uniprot_with_old_accessions = add_old_accessions(
        df_secondary_accession_ids, df_uniprot)
    mapping_df = combine_dfs(df_ensembls, 
        uniprot_with_old_accessions)
    mapping_df = mapping_df[['UniProtKB-ID', 'Ensembl_PRO', 'STRING', 
        'Protein stable ID']]
    mapping_df = mapping_df.drop_duplicates(keep = 'first')
    mapping_df['dcid']='bio/' + mapping_df['UniProtKB-ID']
    return(mapping_df)

def main(): 
    PATH_ARCHIVED_ENSEMBLS = sys.argv[1]
    PATH_ARCHIVED_ACCESSIONS = sys.argv[2]
    PATH_UNIPROT_MAPPING = sys.argv[3]
    mapping_df = create_mapping_df(PATH_ARCHIVED_ENSEMBLS, 
        PATH_ARCHIVED_ACCESSIONS, PATH_UNIPROT_MAPPING)
    mapping_df.to_csv('mapping_protein_names.csv', index=False)    

if __name__ == '__main__':
	main()