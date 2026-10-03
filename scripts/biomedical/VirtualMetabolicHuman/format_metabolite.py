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
Author: Suhana Bedi
Date: 07/10/2021
Name: format_metabolite.py
Description: Add dcids for all the metabolites in the VMH database.
Extract Chembl ids from kegg and chebi matches, and query datacommons
to check for pre-existing nodes for the same metabolite. In addition,
extract hmdb ids from the Human Metabolome database and use it as a
dcid when chembl is absent.
@file_input: input .tsv from VMH with metabolite list, and .csv from hmdb
@file_output: csv output file with addition chembl and dcid columns
'''

import sys
import pandas as pd
import numpy as np
import datacommons as dc
from bioservices import UniChem
import re


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


def name_map(dfm, dfh):
    """
    Finds the rows with the same name in the HMDB
    and VMH dataset.
    Args:
        dfm = VMH data, dfh = HMDB data
    Returns:
        VMH data with added HMDB ids
    """
    dfm['fullName'] = dfm['fullName'].map(
        lambda x: re.sub(r'\W+', '', x)).str.lower()
    dfh['name'] = dfh['name'].map(lambda x: re.sub(r'\W+', '', x)).str.lower()
    dfh['name'] = dfh['name'].str[2:]
    dfh['name'] = dfh['name'].str[:-1]
    overlapped_name = find_overlapped_id(dfm, dfh, "fullName", "name",
                                         "fullName")
    name_hmdb_dict = dfh[dfh["name"].\
    isin(overlapped_name)][["name","accession"]].set_index("name").to_dict()["accession"]
    dfm["hmdb"] = dfm["hmdb"].fillna(dfm["fullName"].map(name_hmdb_dict))
    return dfm


def kegg_map(dfm, dfh):
    """
    Finds the rows with the same KEGG id in the HMDB
    and VMH dataset.
    Args:
        dfm = VMH data, dfh = HMDB data
    Returns:
        VMH data with added HMDB ids
    """
    overlapped_kegg = find_overlapped_id(dfm, dfh, "keggId", "kegg", "keggId")
    kegg_hmdb_dict = dfh[dfh["kegg"].\
    isin(overlapped_kegg)][["kegg","accession"]].set_index("kegg").to_dict()["accession"]
    dfm["hmdb"] = dfm["hmdb"].fillna(dfm["keggId"].map(kegg_hmdb_dict))
    return dfm


def chebi_map(dfm, dfh):
    """
    Finds the rows with the same CHEBI id in the HMDB
    and VMH dataset.
    Args:
        dfm = VMH data, dfh = HMDB data
    Returns:
        VMH data with added HMDB ids
    """
    overlapped_chebi = find_overlapped_id(dfm, dfh, "cheBlId", "chebi_id",
                                          "cheBlId")
    chebi_hmdb_dict = dfh[dfh["chebi_id"].\
    isin(overlapped_chebi)][["chebi_id","accession"]].set_index("chebi_id").to_dict()["accession"]
    dfm["hmdb"] = dfm["hmdb"].fillna(dfm["cheBlId"].map(chebi_hmdb_dict))
    return dfm


def isNaN(num):
    """
    Checks null values
    """
    return num != num


def clean_result(result):
    """
    Converts a list of dicts obtained from dc
    query into a cleaned and easier to read list
    Arg:
        list of dictionaries
    Returns:
        list
    """
    ind_count = 0
    dcid_inch = []
    for index in range(len(result)):
        for key in result[index]:
            dcid_inch.insert(ind_count, result[index][key])
            ind_count += 1
    return dcid_inch


def add_query_result(df, col, dcid):
    """
    Checks if the df row matches with the dc
    query and if so, adds the dcid to the Id
    column of df.
    Args:
        df = dataframe to which ids are added
        col = col of df to match the query with
        dcid = list with dc query results

    """
    count_query = 0
    for i in df.index:
        for j in range(1, len(dcid)):
            if df.loc[i, col] == dcid[j]:
                count_query += 1
                df.loc[i, 'Id'] = dcid[j - 1]
                j += 2
    return df


def property_query(property_name, arr_name):
    """
    Queries dc using the python api, to find
    if the elements of the input list, have a 
    pre-existing matching the user input
    property on dc
    Args:
        arr_name = array with property values
        to query
        property = name of property value
    Returns:
        result = result of dc query
    """
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug {property} ?id .
    ?drug {property} {value} .
    }}
    """.format(property=property_name, value=arr_name)
    result = dc.query(query_str)
    return result


def shard(list_to_shard, shard_size):
    """
    Breaks down a list into smaller 
    sublists, converts it into an array
    and appends the array to the master
    list
    Args:
        list_to_shard = original list
        shard_size = size of subist
    Returns:
        sharded_list = master list with
        smaller sublists 
    """
    sharded_list = []
    for i in range(0, len(list_to_shard), shard_size):
        shard = list_to_shard[i:i + shard_size]
        arr = np.array(shard)
        sharded_list.append(arr)
    return sharded_list


def add_property_matches(df, df_col_name, property_name):
    """
    Takes in the dataframe and property to be queried on data
    commons and adds the dcids for the corresponding matches
    to the original dataframe
    Args:
        df = name of original dataframe
        df_col_name = column name of property to be queried
        property_name = property to be queried
    Returns:
        df = modified dataframe
    """
    list_prop = df[[df_col_name]].T.stack().tolist()
    if property_name == "chebiID":
        for i in range(len(list_prop)):
            list_prop[i] = "CHEBI:" + str(list_prop[i])
    arr_prop = shard(list_prop, 1000)
    for i in range(len(arr_prop)):
        result = property_query(property_name, arr_prop[i])
        dcid = clean_result(result)
        df = add_query_result(df, df_col_name, dcid)
    return df


def add_chembl_bioservices(df):
    """
    Takes in the dataframe to be modfied and adds the chembl
    ids using the bioservices packages
    Args:
        df = name of original dataframe
    Returns:
        df = modified dataframe
    """
    uni = UniChem()
    mapping = uni.get_mapping("kegg_ligand", "chembl")
    chembl_list = [0] * len(df['keggId'])
    df.insert(7, 'ChEMBL', chembl_list)
    for index, row in df.iterrows():
        try:
            chembl_list[index] = mapping[row['keggId']]
        except:
            pass
    df['ChEMBL'] = chembl_list
    df['ChEMBL'] = df['ChEMBL'].replace({'0': np.nan, 0: np.nan})
    return df


def generate_dcid(df):
    """
    Takes in the dataframe to be modfied and generates
    the dcids based on chembl, hmdb, metanetx
    and full name
    Args:
        df = name of original dataframe
    Returns:
        df = modified dataframe
    """
    for i in df.index:
        if df.loc[i, 'ChEMBL'] != 0:
            df.loc[i, 'Id'] = 'bio/' + str(df.loc[i, 'ChEMBL'])
        elif ~(isNaN(df.loc[i, 'hmdb'])):
            df.loc[i, 'Id'] = 'bio/' + str(df.loc[i, 'hmdb'])
        elif ~(isNaN(df.loc[i, 'metanetx'])):
            df.loc[i, 'Id'] = 'bio/' + str(df.loc[i, 'metanetx'])
    # Add dcids based on IUPAC names if no previous matches
    for i in df.index:
        l = df.loc[i, 'fullName']
        l = l.replace(' ', '_')
        l = l.replace(',', '_')
        df.loc[i, 'fullName'] = l

    for i in df.index:
        if df.loc[i, 'Id'] == "bio/nan":
            df.loc[i, 'Id'] = "bio/" + df.loc[i, 'fullName']

    return df


def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    file_hmdb = sys.argv[3]

    df = pd.read_csv(file_input, sep='\t')
    dfh = pd.read_csv(file_hmdb)

    #inchikey matches with dc
    df = add_property_matches(df, 'inchiKey', "inChIKey")
    #hmdb matches with dc
    df = add_property_matches(df, 'hmdb', "humanMetabolomeDatabaseID")
    #kegg matches with dc
    df = add_property_matches(df, 'keggId', "keggCompoundID")
    #chebi matches with dc
    df = add_property_matches(df, 'cheBlId', "chebiID")
    #drug bank matches with dc
    df = add_property_matches(df, 'drugbank', "drugBankMetaboliteID")
    #Add chemblID column in the dataframe and add the corresponding chembl ids
    #for each entry
    df = add_chembl_bioservices(df)
    #Get hmdb IDs from the hmdb data
    df = name_map(df, dfh)
    df = kegg_map(df, dfh)
    df = chebi_map(df, dfh)
    # Add dcids w.r.t chembl ids, hmdb and metanetx
    df = generate_dcid(df)
    # Add "CHEBI:" to all chebi ids
    df['cheBlId'] = "CHEBI:" + df['cheBlId'].astype(str)
    df.to_csv(file_output, index=None)


if __name__ == '__main__':
    main()
