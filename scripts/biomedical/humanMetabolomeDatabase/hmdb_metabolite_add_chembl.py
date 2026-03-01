# Copyright 2021 Google LLC
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
Authors: Suhana Bedi & Khoa Hoang
Date: 07/23/2021
Name: hmdb_metabolite_add_chembl.py
Description: Adds a ChEMBL id column for hmdb data, using 
bioservices, virtual metabolic human data, and human1 data 
@file_input: hmdb_metabolites.csv, metabolites_vmh.csv (from VMH),
metaboliles.tsv (from Human1)
@file_output: csv output file with ChEMBL ids added to hmdb data 
'''
import re
import sys
import os
import pandas as pd
import numpy as np
from bioservices import UniChem


def format_df_human1(df_human1):
    """format human1 data """
    # remove all special characters in fullName column, and lower case.
    df_human1["name"] = df_human1["name"].map(\
        lambda x: re.sub('[^A-Za-z0-9]+', '', x)).str.lower()
    # Remove chebi with wrong format (not starting with CHEBI)
    condition = df_human1['chebi'].str.\
                findall("CHE").explode() == np.array("CHE")
    df_human1["chebi"] =\
                 np.where(condition, df_human1["chebi"], np.nan)
    # format chebiID to float type (to match virtual df)
    df_human1["chebi"] = df_human1["chebi"].str[6:].astype(float)
    return df_human1


def format_df_virtual(df_virtual):
    """format virtual data """
    # remove all special characters in fullName column and lower case.
    df_virtual["fullName"] = df_virtual["fullName"].map(\
        lambda x: re.sub('[^A-Za-z0-9]+', '', x)).str.lower()
    df_virtual["cheBlId"] = df_virtual["cheBlId"].str[6:].astype(float)
    return df_virtual


def format_df_hmdb(df_hmdb):
    """format hmdb data """
    df_hmdb["name"] = df_hmdb["name"].map(\
    lambda x: re.sub('[^A-Za-z0-9]+', '', x))\
    .str.lower().str[1:].str.strip("''")
    df_hmdb["bigg"] = df_hmdb["bigg"].astype(object)
    return df_hmdb


def find_overlapped_id(df1, df2, df1_column, df2_column, id_return_column):
    """find overlapped id between 2 columns from 2 dataframes
    Args:
        df1: pd.DataFrame 1
        df2: pd.DataFrame 2
        df1_column: name of column in df1 that needs to be matched
        df2_column: name of column in df2 that needs to be matched
        id_return_column: column used to return matched id
    Returns:
        panda.Series with matched ids
    """
    matched_id = df1[~df1[df1_column].isna()].merge(\
    df2[~df2[df2_column].isna()], left_on=df1_column,\
                                       right_on=df2_column)[id_return_column]
    matched_id = matched_id.drop_duplicates()
    return matched_id


def name_map(df_virtual, df_hmdb):
    """
    Map the hmdb and VMH metabolite data, based on common names and
    add the ChEMBL id to hmdb for perfect matches.
    """
    df_virtual['fullName'] = df_virtual['fullName'].map(
        lambda x: re.sub(r'\W+', '', x))
    df_virtual['fullName'] = df_virtual['fullName'].str.lower()
    df_hmdb['name'] = df_hmdb['name'].map(lambda x: re.sub(r'\W+', '', x))
    df_hmdb['name'] = df_hmdb['name'].str.lower()
    df_hmdb['name'] = df_hmdb['name'].str[2:]
    df_hmdb['name'] = df_hmdb['name'].str[:-1]
    overlapped_name = find_overlapped_id(df_virtual, df_hmdb, "fullName",
                                         "name", "name")
    name_chembl_dict = df_virtual[df_virtual["fullName"].\
    isin(overlapped_name)][["fullName","ChEMBL"]].set_index("fullName").to_dict()["ChEMBL"]
    df_hmdb["chembl"] = df_hmdb["chembl"].fillna(
        df_hmdb["name"].map(name_chembl_dict))
    return df_hmdb


def kegg_map(df_virtual, df_hmdb):
    """
    Map the hmdb and VMH metabolite data, based on KEGG ids and
    add the ChEMBL id to hmdb for perfect matches.
    """
    overlapped_kegg = find_overlapped_id(df_virtual, df_hmdb, "keggId", "kegg",
                                         "kegg")
    kegg_chembl_dict = df_virtual[df_virtual["keggId"].\
    isin(overlapped_kegg)][["keggId","ChEMBL"]].set_index("keggId").to_dict()["ChEMBL"]
    df_hmdb["chembl"] = df_hmdb["chembl"].fillna(
        df_hmdb["kegg"].map(kegg_chembl_dict))
    return df_hmdb


def chebi_map(df_virtual, df_hmdb):
    """
    Map the hmdb and VMH metabolite data, based on CHEBI ids and
    add the ChEMBL id to hmdb for perfect matches.
    """
    overlapped_chebi = find_overlapped_id(df_virtual, df_hmdb, "cheBlId",
                                          "chebi_id", "chebi_id")
    chebi_chembl_dict = df_virtual[df_virtual["cheBlId"].\
    isin(overlapped_chebi)][["cheBlId","ChEMBL"]].set_index("cheBlId").to_dict()["ChEMBL"]
    df_hmdb["chembl"] = df_hmdb["chembl"].fillna(
        df_hmdb["chebi_id"].map(chebi_chembl_dict))
    return df_hmdb


def convert_kegg_to_chembl(df):
    """
    Convert KEGG id to ChEMBL id using the bioservices
    package.
    """
    uni = UniChem()
    from_, to_ = "kegg", "chembl"
    from_list = list(df[df[to_].isna()][from_].unique())
    if np.nan in from_list:
        from_list.remove(np.nan)
    mapping = uni.get_mapping("kegg_ligand", "chembl")
    for val in from_list:
        try:
            df.loc[df[from_] == val, "chembl"] = mapping[val]
        except KeyError:
            pass
    return df


def convert_chebi_to_chembl(df):
    """
    Convert CHEBI id to ChEMBL id using the bioservices
    package.
    """
    uni = UniChem()
    from_, to_ = "chebi_id", "chembl"
    df['chebi_id'] = "CHEBI:" + df['chebi_id'].astype(str)
    from_list = list(df[df[to_].isna()][from_].unique())
    if np.nan in from_list:
        from_list.remove(np.nan)
    mapping = uni.get_mapping("chebi", "chembl")
    for val in from_list:
        try:
            df.loc[df[from_] == val, "chembl"] = mapping[val]
        except KeyError:
            pass
    return df

def add_chembl_vhm_hmdb(df_hmdb, df_virtual):
    """
    Adds chembl matches from VHM data to HMDB
    Args:
        df_hmdb = HMDB data
        df_virtual = VMH data
    Returns:
        df_hmdb = HMDB data with chembl added
    """
    df_hmdb = name_map(df_virtual, df_hmdb)
    df_hmdb = kegg_map(df_virtual, df_hmdb)
    df_hmdb = chebi_map(df_virtual, df_hmdb)
    df_hmdb['chembl'] = df_hmdb['chembl'].replace({'0': np.nan, 0: np.nan})
    df_hmdb = convert_kegg_to_chembl(df_hmdb)
    df_hmdb = convert_chebi_to_chembl(df_hmdb)
    return df_hmdb




def main():
    # get argument from input
    human1_tsv, virtual_tsv, hmdb_csv =\
                 sys.argv[1], sys.argv[2], sys.argv[3]

    # read 3 input files to dataframe format
    df_human1 = pd.read_csv(human1_tsv, sep="\t")
    df_virtual = pd.read_csv(virtual_tsv)
    df_hmdb = pd.read_csv(hmdb_csv)
    # Format 3 dataframes so that columns can be matched
    df_human1 = format_df_human1(df_human1)
    df_virtual = format_df_virtual(df_virtual)
    df_hmdb = format_df_hmdb(df_hmdb)
    human1_matching_column = ["name", "kegg.compound", "metanetx.chemical",\
                              "pubchem.compound", "chebi", "bigg.metabolite"]
    virtual_matching_column = ["fullName", "keggId", "metanetx",\
                              "pubChemId", "cheBlId", "biggId"]
    overlapped_column_values = []
    # find matched ID in all possible columns
    for names in tuple(zip(human1_matching_column, virtual_matching_column)):
        overlapped_val = find_overlapped_id(df_human1, \
                df_virtual, names[0], names[1], names[1])
        overlapped_column_values.append(overlapped_val)
    virtual_columns = ["abbreviation", "keggId",\
     "pubChemId", "cheBlId", "hmdb", "chemspider", \
     "biggId", "drugbank", "metanetx", "metlin",\
         "casRegistry", "inchiKey", "smile"]
    human1_virtual_columns = list(np.char.add(\
        np.array(virtual_columns), "_virtual"))
    # insert columns in virtual df to human1 df
    for col in human1_virtual_columns:
        df_human1[col] = np.nan
    #fill values to inserted columns (virtual df) based on
    # mapping between coreesponding columns in 2 dataframes
    for overlap_column in list(zip(overlapped_column_values,\
         human1_matching_column, virtual_matching_column)):
        map_dict = df_virtual[df_virtual[overlap_column[2]].\
            isin(overlap_column[0])].\
            set_index(overlap_column[2]).to_dict()
        for key in map_dict.keys():
            if key + "_virtual" in df_human1.columns:
                df_human1[key + "_virtual"] = df_human1[key + "_virtual"].\
                    fillna(df_human1[overlap_column[1]].map(map_dict[key]))
    human1_matching_column_2 = ['name', 'bigg.metabolite',\
           'chebi', 'kegg.compound', 'pubchem.compound',\
            'keggId_virtual', 'pubChemId_virtual', 'cheBlId_virtual',\
           'chemspider_virtual', 'biggId_virtual', 'drugbank_virtual',\
            'metlin_virtual', 'casRegistry_virtual',\
           'inchiKey_virtual', 'smile_virtual']
    hmdb_matching_column = ['name', 'bigg',\
                            'chebi_id', 'kegg', 'pubchem', 'kegg',\
                            'pubchem', 'chebi_id', 'chemspider', \
                            'bigg', 'drugbank', 'metlin_id',
                            'cas_registry_number', 'InChIKey', 'smiles']
    overlapped_column_values_2 = []
    # find match ID in all possible columns between the
    # appended human1 dataframe and hmdb dataframe
    for names in tuple(zip(human1_matching_column_2, hmdb_matching_column)):
        overlapped_val = find_overlapped_id(df_human1, \
                df_hmdb, names[0], names[1], names[1])
        overlapped_column_values_2.append(overlapped_val)
    # insert a column for hmdb_id
    df_human1["master_hmdb"] = np.nan
    # fill new master_hmdb column with values
    for overlap_column in list(zip(overlapped_column_values_2, \
        human1_matching_column_2, hmdb_matching_column)):
        map_dict = df_hmdb[df_hmdb[overlap_column[2]].isin(\
            overlap_column[0])].set_index(overlap_column[2]).to_dict()
        df_human1["master_hmdb"] = df_human1["master_hmdb"].\
            fillna(df_human1[overlap_column[1]].map(map_dict["accession"]))
    # fill missing values of human 1 with
    #  hmdb exsiting in human1 and virtual df
    df_human1["master_hmdb"] = df_human1["master_hmdb"].\
        fillna(df_human1["hmdb"])
    df_human1["master_hmdb"] = df_human1["master_hmdb"].\
        fillna(df_human1["hmdb_virtual"])
    # save output file
    output_path = os.path.join(os.getcwd(), "CHEMBL_HMDB_map.csv")
    hmdb_chembl_dict = df_human1[["chembl","master_hmdb"]].dropna().\
                   drop_duplicates().set_index("master_hmdb").\
                   to_dict()["chembl"]
    df_hmdb["chembl"] = df_hmdb["accession"].map(hmdb_chembl_dict)
 
    df_hmdb = add_chembl_vhm_hmdb(df_hmdb, df_virtual)
    df_hmdb.to_csv(output_path, index=None)


if __name__ == "__main__":
    main()
