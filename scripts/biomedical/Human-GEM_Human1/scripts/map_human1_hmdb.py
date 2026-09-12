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
Author: Khoa Hoang
Date: 08/11/2021
Name: format_reactions.py
Description: This script find all mapping
betweenhumanGEMID and HMDB id using 3 dataset:
human1 metabolites, virtual metabolites,
and hmdb metabolites
@file_input: metabolites.tsv from human1 dataset,
recon-store-metabolites-1.tsv from virtual metabolites dataset,
and hmdb.csv from HMDB dataset
@file_output: humanGEM_HMDB_map.csv showing
the mapping between humanGEMID and HMDB_ID
'''

import re
import sys
import os
import pandas as pd
import numpy as np

# matching columns between human1
# and virtual metabolites dataframe
HUMAN1_COLUMNS_MATCH_VIRTUAL = ["name", "kegg.compound", "metanetx.chemical",\
                            "pubchem.compound", "chebi", "bigg.metabolite"]
VIRTUAL_COLUMNS_MATCH_HUMAN1 = ["fullName", "keggId", "metanetx",\
                            "pubChemId", "cheBlId", "biggId"]
HUMAN1_COLUMNS_MATCH_HMDB = ['name', 'bigg.metabolite',\
        'chebi', 'kegg.compound', 'pubchem.compound',\
        'keggId_virtual', 'pubChemId_virtual', 'cheBlId_virtual',\
        'chemspider_virtual', 'biggId_virtual', 'drugbank_virtual',\
        'metlin_virtual', 'casRegistry_virtual',\
        'inchiKey_virtual', 'smile_virtual']
HMDB_COLUMNS_MATCH_HUMAN1 = ['name', 'bigg',\
                             'chebi_id', 'kegg', 'pubchem', 'kegg',\
                             'pubchem', 'chebi_id', 'chemspider', \
                             'bigg', 'drugbank', 'metlin_id',
                             'cas_registry_number', 'InChIKey', 'smiles']
VIRTUAL_COLUMNS_APPEND_HUMAN1 = ["abbreviation", "keggId",\
     "pubChemId", "cheBlId", "hmdb", "chemspider", \
     "biggId", "drugbank", "metanetx", "metlin",\
         "casRegistry", "inchiKey", "smile"]

def format_df_human1(df_human1):
    """format human1 data columns to match
    between virtual_df, human1_df, and hmdb_df
    Args:
        df_human1: human1 dataframe
    Returns:
        df_human1: formatted human1 dataframe
    """
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
    """format virtual data columns to match
    between virtual_df, human1_df, and hmdb_df
    Args:
        df_virtual: virtual dataframe
    Returns:
        df_virtual: formatted virtual dataframe
    """
    # remove all special characters in fullName column and lower case.
    df_virtual["fullName"] = df_virtual["fullName"].map(\
        lambda x: re.sub('[^A-Za-z0-9]+', '', x)).str.lower()
    return df_virtual

def format_df_hmdb(df_hmdb):
    """format hmdb data columns to match
    between virtual_df, human1_df, and hmdb_df
    Args:
        df_hmdb: hmdb dataframe
    Returns:
        df_hmdb: formatted hmdb dataframe
    """
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

def append_human1_columns(df_human1, df_virtual):
    """Append human1 with columns from virtual dataframe
    by matching existing columns between 2 dataframes
    Args:
        df_human1: human1 metabolite dataframe
        df_virtual: virtual metabolite dataframe
    Returns:
        df_human1: human1 dataframe appended with
        virtual columns
    """
    overlapped_column_values = []
    # find matched ID in all possible columns
    for names in tuple(zip(HUMAN1_COLUMNS_MATCH_VIRTUAL, \
                            VIRTUAL_COLUMNS_MATCH_HUMAN1)):
        overlapped_val = find_overlapped_id(df_human1, \
                df_virtual, names[0], names[1], names[1])
        overlapped_column_values.append(overlapped_val)
    human1_virtual_columns = list(np.char.add(\
        np.array(VIRTUAL_COLUMNS_APPEND_HUMAN1), "_virtual"))
    # insert columns in virtual df to human1 df
    for col in human1_virtual_columns:
        df_human1[col] = np.nan
    #fill values to inserted columns (virtual df) based on
    # mapping between coreesponding columns in 2 dataframes
    for overlap_column in list(zip(overlapped_column_values,\
                                 HUMAN1_COLUMNS_MATCH_VIRTUAL,\
                                 VIRTUAL_COLUMNS_MATCH_HUMAN1)):
        map_dict = df_virtual[df_virtual[overlap_column[2]].\
            isin(overlap_column[0])].\
            set_index(overlap_column[2]).to_dict()
        for key in map_dict.keys():
            if key + "_virtual" in df_human1.columns:
                df_human1[key + "_virtual"] = df_human1[key + "_virtual"].\
                    fillna(df_human1[overlap_column[1]].map(map_dict[key]))
    return df_human1

def read_and_format_files(human1_tsv, virtual_tsv, hmdb_csv):
    """Read and format human1_tsv, virtual_tsv, hmdb_csv
    Args:
        human1_tsv: human1 metabolites file path
        virtual_tsv: virtual metabolites file path
        hmdb_csv: hmdb metabolite file path
    Returns:
        df_human1: formatted human1_metabolites dataframe
        df_virtual: formatted virtual_metabolites dataframe
        df_hmdb: formatted hmdb_metabolites dataframe
    """
    # read 3 input files to dataframe format
    df_human1 = pd.read_csv(human1_tsv, sep="\t")
    df_virtual = pd.read_csv(virtual_tsv, sep="\t")
    df_hmdb = pd.read_csv(hmdb_csv)
    # Format 3 dataframes so that columns can be matched
    df_human1 = format_df_human1(df_human1)
    df_virtual = format_df_virtual(df_virtual)
    df_hmdb = format_df_hmdb(df_hmdb)

    return df_human1, df_virtual, df_hmdb

def map_human1_hmdb(df_human1, df_hmdb):
    """Generate mapping between hummanGEMID and HMDB_ID
    Args:
        df_human1: human1_metabolites dataframe
                   appended with hmdb columns
        df_hmdb: hmdb metabolite dataframe
    Returns:
        write mapping to csv
    """

    overlapped_column_values_2 = []
    # find match ID in all possible columns between the
    # appended human1 dataframe and hmdb dataframe
    for names in tuple(zip(HUMAN1_COLUMNS_MATCH_HMDB,\
                             HMDB_COLUMNS_MATCH_HUMAN1)):
        overlapped_val = find_overlapped_id(df_human1, \
                df_hmdb, names[0], names[1], names[1])
        overlapped_column_values_2.append(overlapped_val)
    # insert a column for hmdb_id
    df_human1["master_hmdb"] = np.nan
    # fill new master_hmdb column with values
    for overlap_column in list(zip(overlapped_column_values_2, \
        HUMAN1_COLUMNS_MATCH_HMDB, HMDB_COLUMNS_MATCH_HUMAN1)):
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
    output_path = os.path.join(os.getcwd(), "humanGEM_HMDB_map.csv")
    df_human1[["id", "master_hmdb"]].to_csv(output_path, index=None)


def main():
    # get argument from input
    human1_tsv, virtual_tsv, hmdb_csv =\
                 sys.argv[1], sys.argv[2], sys.argv[3]
    df_human1, df_virtual, df_hmdb = \
        read_and_format_files(human1_tsv, virtual_tsv, hmdb_csv)
    df_human1 = append_human1_columns(df_human1, df_virtual)
    map_human1_hmdb(df_human1, df_hmdb)


if __name__ == "__main__":
    main()
