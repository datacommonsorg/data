'''
Author: Suhana Bedi
Date: 07/10/2021
Name: format_metabolite.py
Description: Add dcids for all the metabolites in the VMH database. 
Extract Chembl ids from kegg and chebi matches, and query datacommons 
to check for pre-existing nodes for the same metabolite.
@file_input: input .tsv from VMH with metabolite list
@file_output: csv output file with addition chembl and dcid columns
'''

import sys
import pandas as pd
import numpy as np
import datacommons as dc
from bioservices import *

def isNaN(num):
    return num != num

def clean_result(result):
    ind_count = 0
    dcid_inch = []
    for index in range(len(result)):
        for key in result[index]:
            dcid_inch.insert(ind_count, result[index][key])
            ind_count += 1
    return dcid_inch

def add_query_result(df, col, dcid):
    count_query = 0
    for i in df.index:
        for j in range(1, len(dcid)):
            if df.loc[i, col] == dcid[j]:
                count_query += 1
                df.loc[i, 'Id'] = dcid[j - 1]
                j += 2
    return df

def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]

    df = pd.read_csv(file_input, sep='\t')
    #inchikey matches with dc 
    list_inchi = df[['inchiKey']].T.stack().tolist()
    list_inchi_1 = list_inchi[1:1000]
    list_inchi_2 = list_inchi[1000:2000]
    list_inchi_3 = list_inchi[2000:2982]
    arr_inchi_1 = np.array(list_inchi_1)
    arr_inchi_2 = np.array(list_inchi_2)
    arr_inchi_3 = np.array(list_inchi_3)

    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug inChIKey ?id .
    ?drug inChIKey {0} .
    }}
    """.format(arr_inchi_1)
    result = dc.query(query_str)
    dcid_inch = clean_result(result)
    df = add_query_result(df, "inchiKey", dcid_inch)


    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug inChIKey ?id .
    ?drug inChIKey {0} .
    }}
    """.format(arr_inchi_2)
    result = dc.query(query_str)
    dcid_inch = clean_result(result)
    df = add_query_result(df, "inchiKey", dcid_inch)
    #inchi match complete (2)

    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug inChIKey ?id .
    ?drug inChIKey {0} .
    }}
    """.format(arr_inchi_3)
    result = dc.query(query_str)
    dcid_inch = clean_result(result)
    df = add_query_result(df, "inchiKey", dcid_inch)
    #inchi match complete (3)

    #hmdb matches with dc
    list_hmdb = df[['hmdb']].T.stack().tolist()
    list_hmdb_1 = list_hmdb[0:1000]
    list_hmdb_2 = list_hmdb[1000:1513]
    arr_hmdb_1 = np.array(list_hmdb_1)
    arr_hmdb_2 = np.array(list_hmdb_2)
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug humanMetabolomeDatabaseID ?id .
    ?drug humanMetabolomeDatabaseID {0} .
    }}
    """.format(arr_hmdb_1)
    result = dc.query(query_str)
    dcid_hmdb = clean_result(result)
    df = add_query_result(df, "hmdb", dcid_hmdb)

    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug humanMetabolomeDatabaseID ?id .
    ?drug humanMetabolomeDatabaseID {0} .
    }}
    """.format(arr_hmdb_2)
    result = dc.query(query_str)
    dcid_hmdb = clean_result(result)
    df = add_query_result(df, "hmdb", dcid_hmdb)

    #kegg matches with dc 
    list_kegg = df[['keggId']].T.stack().tolist()
    list_kegg_1 = list_kegg[0:1000]
    list_kegg_2 = list_kegg[1000:1266]
    arr_kegg_1 = np.array(list_kegg_1)
    arr_kegg_2 = np.array(list_kegg_2)
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug keggCompoundID ?id .
    ?drug keggCompoundID {0} .
    }}
    """.format(arr_kegg_1)
    result = dc.query(query_str)
    dcid = clean_result(result)
    df = add_query_result(df, "keggId", dcid)
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug keggCompoundID ?id .
    ?drug keggCompoundID {0} .
    }}
    """.format(arr_kegg_2)
    result = dc.query(query_str)
    dcid = clean_result(result)
    df = add_query_result(df, "keggId", dcid) #kegg match complete (2)

    #chebi matches with dc
    list_chebi = df[['cheBlId']].T.stack().tolist()
    for i in range(len(list_chebi)):
        list_chebi[i] = "CHEBI:" + str(list_chebi[i])
    list_chebi_1 = list_chebi[0:1000]
    list_chebi_2 = list_chebi[1000:1126]
    arr_chebi_1 = np.array(list_chebi_1)
    arr_chebi_2 = np.array(list_chebi_2)
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug chebiID ?id .
    ?drug chebiID {0} .
    }}
    """.format(arr_chebi_1)
    result = dc.query(query_str)
    dcid = clean_result(result)
    df = add_query_result(df, "cheBlId", dcid)
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug chebiID ?id .
    ?drug chebiID {0} .
    }}
    """.format(arr_chebi_2)
    result = dc.query(query_str)
    dcid = clean_result(result)
    df = add_query_result(df, "cheBlId", dcid)

    #pubchem matches with dc
    list_pub = df[['pubChemId']].T.stack().tolist()
    for i in range(len(list_pub)):
        list_pub[i] = str(list_pub[i])
    list_pub_1 = list_pub[0:1000]
    list_pub_2 = list_pub[1000:1104]
    arr_pub_1 = np.array(list_pub_1)
    arr_pub_2 = np.array(list_pub_2)
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug pubChemCompoundID ?id .
    ?drug pubChemCompoundID {0} .
    }}
    """.format(arr_pub_1)
    result = dc.query(query_str)
    dcid = clean_result(result)
    df = add_query_result(df, "pubChemId", dcid)

    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug pubChemCompoundID ?id .
    ?drug pubChemCompoundID {0} .
    }}
    """.format(arr_pub_2)
    result = dc.query(query_str)
    dcid = clean_result(result)
    df = add_query_result(df, "pubChemId", dcid)

    #chemspider matches with dc
    list_chem = df[['chemspider']].T.stack().tolist()
    for i in range(len(list_chem)):
        list_chem[i] = str(list_chem[i])
    list_chem_1 = list_pub[0:1000]
    list_chem_2 = list_pub[1000:1052]
    arr_chem_1 = np.array(list_chem_1)
    arr_chem_2 = np.array(list_chem_2)
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug chemSpiderID ?id .
    ?drug chemSpiderID {0} .
    }}
    """.format(arr_chem_1)
    result = dc.query(query_str)
    dcid = clean_result(result)
    df = add_query_result(df, "chemspider", dcid)
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug chemSpiderID ?id .
    ?drug chemSpiderID {0} .
    }}
    """.format(arr_chem_2)
    result = dc.query(query_str)
    dcid = clean_result(result)
    df = add_query_result(df, "chemspider", dcid)

    #drug bank matches with dc
    list_drug = df[['drugbank']].T.stack().tolist()
    for i in range(len(list_drug)):
        list_drug[i] = str(list_drug[i])     
    arr_drug = np.array(list_drug)
    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug drugBankMetaboliteID ?id .
    ?drug drugBankMetaboliteID {0} .
    }}
    """.format(arr_drug)
    result = dc.query(query_str)
    dcid = clean_result(result)
    df = add_query_result(df, "drugbank", dcid)

    uni = UniChem()
    mapping = uni.get_mapping("kegg_ligand", "chembl")
    #Add chemblID column in the dataframe and add the corresponding chembl ids 
    #for each entry 
    chembl_list = [0]*len(df['keggId'])
    df.insert(7, 'ChEMBL', chembl_list)
    for index, row in df.iterrows():
        try: #chembl_list.insert(index, mapping[row['keggId']] )
            chembl_list[index] = mapping[row['keggId']]
        except:
            pass
    df['ChEMBL'] = chembl_list
    # Add dcids w.r.t chembl ids and chemical formulae(where chembl is missing)
    for i in df.index:
        if df.loc[i, 'ChEMBL'] != 0:
            df.loc[i, 'Id'] = 'bio/' + str(df.loc[i, 'ChEMBL'])
        elif ~(isNaN(df.loc[i, 'hmdb'])):
            df.loc[i, 'Id'] = 'bio/' + str(df.loc[i, 'hmdb'])
    # Add dcids based on IUPAC names if no previous matches
    for i in df.index:
        l = df.loc[i, 'fullName']
        l = l.replace(' ', '_')
        l = l.replace(',', '_')
        df.loc[i, 'fullName'] = l

    for i in df.index:
        if df.loc[i, 'Id'] == "bio/nan":
            df.loc[i, 'Id'] = "bio/" + df.loc[i, 'fullName']

    df.to_csv(file_output, index=None)

if __name__ == '__main__':
    main()
