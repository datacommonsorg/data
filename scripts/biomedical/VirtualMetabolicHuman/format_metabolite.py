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

def name_map(dfm, dfh):
    """
    Finds the rows with the same name in the HMDB
    and VMH dataset.
    Args:
        dfm = VMH data, dfh = HMDB data
    Returns:
        VMH data with added HMDB ids
    """
    dfm['fullName'] = dfm['fullName'].map(lambda x: re.sub(r'\W+', '', x)).str.lower()
    dfh['name'] = dfh['name'].map(lambda x: re.sub(r'\W+', '', x)).str.lower()
    dfh['name'] = dfh['name'].str[2:]
    dfh['name'] = dfh['name'].str[:-1]
    dfh.rename(columns = {'name':'fullName'}, inplace = True)
    df = pd.merge(dfm, dfh, on = 'fullName', how = 'left')
    df['hmdb'].fillna(df['accession'])
    df = df.iloc[:,1:len(dfm.columns)]
    return df


def kegg_map(dfm, dfh):
    """
    Finds the rows with the same KEGG id in the HMDB
    and VMH dataset.
    Args:
        dfm = VMH data, dfh = HMDB data
    Returns:
        VMH data with added HMDB ids
    """
    dfh.rename(columns = {'kegg':'keggId'}, inplace = True)
    df = pd.merge(dfm, dfh, on = 'keggId', how = 'left')
    df['hmdb'].fillna(df['accession'])
    df = df.iloc[:,1:len(dfm.columns)]
    return df

def chebi_map(dfm, dfh):
    """
    Finds the rows with the same CHEBI id in the HMDB
    and VMH dataset.
    Args:
        dfm = VMH data, dfh = HMDB data
    Returns:
        VMH data with added HMDB ids
    """
    dfh.rename(columns = {'chebi_id':'cheBlId'}, inplace = True)
    df = pd.merge(dfm, dfh, on = 'cheBlId', how = 'left')
    df['hmdb'].fillna(df['accession'])
    df = df.iloc[:,1:len(dfm.columns)]
    return df

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

def inchi_query(arr_inchi):
    """
    Queries dc using the python api, to find
    if the elements of the input list, have a 
    pre-existing matching inchikey on dc
    Args:
        arr_inchi = array with inchikeys to query
    Returns:
        result = result of dc query
    """
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug inChIKey ?id .
    ?drug inChIKey {0} .
    }}
    """.format(arr_inchi)   
    result = dc.query(query_str)
    return result

def hmdb_query(arr_hmdb):
    """
    Queries dc using the python api, to find
    if the elements of the input list, have a 
    pre-existing matching hmdb ids on dc
    Args:
        arr_hmdb = array with hmdb ids to query
    Returns:
        result = result of dc query
    """    
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug humanMetabolomeDatabaseID ?id .
    ?drug humanMetabolomeDatabaseID {0} .
    }}
    """.format(arr_hmdb)
    result = dc.query(query_str)    
    return result

def kegg_query(arr_kegg):
    """
    Queries dc using the python api, to find
    if the elements of the input list, have a 
    pre-existing matching kegg ids on dc
    Args:
        arr_hmdb = array with kegg ids to query
    Returns:
        result = result of dc query
    """
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug keggCompoundID ?id .
    ?drug keggCompoundID {0} .
    }}
    """.format(arr_kegg)
    result = dc.query(query_str)
    return result

def chebi_query(arr_chebi):
    """
    Queries dc using the python api, to find
    if the elements of the input list, have a 
    pre-existing matching chebi ids on dc
    Args:
        arr_hmdb = array with chebi ids to query
    Returns:
        result = result of dc query
    """
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug chebiID ?id .
    ?drug chebiID {0} .
    }}
    """.format(arr_chebi)
    result = dc.query(query_str)
    return result

def drugbank_query(arr_drug):
    """
    Queries dc using the python api, to find
    if the elements of the input list, have a 
    pre-existing matching drugbank ids on dc
    Args:
        arr_hmdb = array with drugbank ids to query
    Returns:
        result = result of dc query
    """
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug drugBankMetaboliteID ?id .
    ?drug drugBankMetaboliteID {0} .
    }}
    """.format(arr_drug)
    result = dc.query(query_str)
    return result

def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    file_hmdb = sys.argv[3]

    df = pd.read_csv(file_input, sep='\t')
    dfh = pd.read_csv('hmdb.csv')

    #inchikey matches with dc 
    list_inchi = df[['inchiKey']].T.stack().tolist()
    list_inchi_1 = list_inchi[1:1000]
    list_inchi_2 = list_inchi[1000:2000]
    list_inchi_3 = list_inchi[2000:2982]
    arr_inchi_1 = np.array(list_inchi_1)
    arr_inchi_2 = np.array(list_inchi_2)
    arr_inchi_3 = np.array(list_inchi_3)
    arr_inchi_list = list(arr_inchi_1, arr_inchi_2,arr_inchi_3 )
    for i in len(range(arr_inchi_list)):
        result = inchi_query(arr_inchi_list[i])
        dcid_inch = clean_result(result)
        df = add_query_result(df, "inchiKey", dcid_inch)

    #hmdb matches with dc
    list_hmdb = df[['hmdb']].T.stack().tolist()
    list_hmdb_1 = list_hmdb[0:1000]
    list_hmdb_2 = list_hmdb[1000:1513]
    arr_hmdb_1 = np.array(list_hmdb_1)
    arr_hmdb_2 = np.array(list_hmdb_2)
    arr_hmdb_list = list(arr_hmdb_1, arr_hmdb_2)
    for i in len(range(arr_hmdb_list)):
        result = hmdb_query(arr_hmdb_list[i])
        dcid_hmdb = clean_result(result)
        df = add_query_result(df, "hmdb", dcid_hmdb)
  
    #kegg matches with dc 
    list_kegg = df[['keggId']].T.stack().tolist()
    list_kegg_1 = list_kegg[0:1000]
    list_kegg_2 = list_kegg[1000:1266]
    arr_kegg_1 = np.array(list_kegg_1)
    arr_kegg_2 = np.array(list_kegg_2)
    arr_kegg_list = list(arr_kegg_1, arr_kegg_2)
    for i in len(range(arr_kegg_list)):
        result = kegg_query(arr_kegg_list[i])
        dcid_kegg = clean_result(result)
        df = add_query_result(df, "keggId", dcid_kegg)

    #chebi matches with dc
    list_chebi = df[['cheBlId']].T.stack().tolist()
    for i in range(len(list_chebi)):
        list_chebi[i] = "CHEBI:" + str(list_chebi[i])
    list_chebi_1 = list_chebi[0:1000]
    list_chebi_2 = list_chebi[1000:1126]
    arr_chebi_1 = np.array(list_chebi_1)
    arr_chebi_2 = np.array(list_chebi_2)
    arr_chebi_list = list(arr_chebi_1, arr_chebi_2)
    for i in len(range(arr_chebi_list)):
        result = chebi_query(arr_chebi_list[i])
        dcid_chebi = clean_result(result)
        df = add_query_result(df, "cheBlId", dcid_chebi)

    #drug bank matches with dc
    list_drug = df[['drugbank']].T.stack().tolist()
    for i in range(len(list_drug)):
        list_drug[i] = str(list_drug[i])     
    arr_drug = np.array(list_drug)
    result = drugbank_query(arr_drug)
    dcid = clean_result(result)
    df = add_query_result(df, "drugbank", dcid)

    #Add chemblID column in the dataframe and add the corresponding chembl ids 
    #for each entry
    uni = UniChem()
    mapping = uni.get_mapping("kegg_ligand", "chembl")
    chembl_list = [0]*len(df['keggId'])
    df.insert(7, 'ChEMBL', chembl_list)
    for index, row in df.iterrows():
        try: #chembl_list.insert(index, mapping[row['keggId']] )
            chembl_list[index] = mapping[row['keggId']]
        except:
            pass
    df['ChEMBL'] = chembl_list
    df['ChEMBL'] = df['ChEMBL'].replace({'0':np.nan, 0:np.nan})
    #Get hmdb IDs from the hmdb data
    df = name_map(df, dfh)
    df = kegg_map(df, dfh)
    df = chebi_map(df, dfh)
    # Add dcids w.r.t chembl ids, hmdb and metanetx
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

    # Add "CHEBI:" to all chebi ids
    df['cheBlId'] = "CHEBI:" + df['cheBlId'].astype(str)
    
    df.to_csv(file_output, index=None)

if __name__ == '__main__':
    main()
