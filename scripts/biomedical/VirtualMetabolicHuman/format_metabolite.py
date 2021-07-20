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
import os
import csv
from io import StringIO
from lxml import etree

## Taken from http://www.metabolomics-forum.com/index.php?topic=1588.0
def hmdbextract(name, file):
  ns = {'hmdb': 'http://www.hmdb.ca'}
  context = etree.iterparse(name, tag='{http://www.hmdb.ca}metabolite')
  csvfile = open(file, 'w')
  fieldnames = ['accession', 'monisotopic_molecular_weight', 'iupac_name', 
                'name', 'chemical_formula', 'InChIKey', 'cas_registry_number', 'smiles', 
                'drugbank','chebi_id', 'pubchem', 'phenol_explorer_compound_id','food','knapsack', 
                'chemspider', 'kegg', 'meta_cyc','bigg','metlin_id','pdb_id', 'logpexp','kingdom',  
                'direct_parent', 'super_class', 'class', 'sub_class', 'molecular_framework', 'vmh_id']
  writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
  writer.writeheader()
  for event, elem in context:
    accession = elem.xpath('hmdb:accession/text()', namespaces=ns)[0]
    try:
        monisotopic_molecular_weight = elem.xpath('hmdb:monisotopic_molecular_weight/text()', namespaces=ns)[0]
    except:
        monisotopic_molecular_weight = 'NA'
    try:
        iupac_name = elem.xpath('hmdb:iupac_name/text()', namespaces=ns)[0].encode('utf-8')
    except:
        iupac_name = 'NA'
    name = elem.xpath('hmdb:name/text()', namespaces=ns)[0].encode('utf-8')
    try:
        chemical_formula = elem.xpath('hmdb:chemical_formula/text()', namespaces=ns)[0]
    except:
        chemical_formula = 'NA'
    try:
        inchikey = elem.xpath('hmdb:inchikey/text()', namespaces=ns)[0]
    except:
        inchikey = 'NA'
    try:
        cas_registry_number = elem.xpath('hmdb:cas_registry_number/text()', namespaces=ns)[0]
    except:
        cas_registry_number = 'NA'
    try:
        smiles = elem.xpath('hmdb:smiles/text()', namespaces=ns)[0]
    except:
        smiles = 'NA'
    try:
        drugbank = elem.xpath('hmdb:drugbank_id/text()', namespaces=ns)[0]
    except:
        drugbank = 'NA'
    try:
        chebi_id = elem.xpath('hmdb:chebi_id/text()', namespaces=ns)[0]
    except:
        chebi_id = 'NA'
    try:
        pubchem = elem.xpath('hmdb:pubchem_compound_id/text()', namespaces=ns)[0]
    except:
        pubchem = 'NA'
    try:
        phenol_explorer_compound_idt = elem.xpath('hmdb:phenol_explorer_compound_id/text()', namespaces=ns)[0]
    except:
        phenol_explorer_compound_id = 'NA'
    try:
        food = elem.xpath('hmdb:foodb_id/text()', namespaces=ns)[0]
    except:
        food = 'NA'
    try:
        knapsack = elem.xpath('hmdb:knapsack_id/text()', namespaces=ns)[0]
    except:
        knapsack = 'NA'
    try:
        chemspider = elem.xpath('hmdb:chemspider_id/text()', namespaces=ns)[0]
    except:
        chemspider = 'NA'
    try:
        kegg = elem.xpath('hmdb:kegg_id/text()', namespaces=ns)[0]
    except:
        kegg = 'NA'
    try:
        meta_cyc = elem.xpath('hmdb:meta_cyc_id/text()', namespaces=ns)[0]
    except:
        meta_cyc = 'NA'
    try:
        bigg = elem.xpath('hmdb:bigg_id/text()', namespaces=ns)[0]
    except:
        bigg = 'NA'
    try:
        metlin_id = elem.xpath('hmdb:metlin_id/text()', namespaces=ns)[0]
    except:
        metlin_id = 'NA'
    try:
        pdb_id = elem.xpath('hmdb:pdb_id/text()', namespaces=ns)[0]
    except:
        pdb_id = 'NA'
    try:
        logpexp = elem.xpath('hmdb:experimental_properties/hmdb:property[hmdb:kind = "logp"]/hmdb:value/text()', namespaces=ns)[0]
    except:
        logpexp = 'NA'
    try:
        kingdom = elem.xpath('hmdb:taxonomy/hmdb:kingdom/text()', namespaces=ns)[0]
    except:
        kingdom = 'NA'
    try:
        direct_parent = elem.xpath('hmdb:taxonomy/hmdb:direct_parent/text()', namespaces=ns)[0]
    except:
        direct_parent = 'NA'
    try:
        super_class = elem.xpath('hmdb:taxonomy/hmdb:super_class/text()', namespaces=ns)[0]
    except:
        super_class = 'NA'
    try:
        classorg = elem.xpath('hmdb:taxonomy/hmdb:class/text()', namespaces=ns)[0]
    except:
        classorg = 'NA'
    try:
        sub_class = elem.xpath('hmdb:taxonomy/hmdb:sub_class/text()', namespaces=ns)[0]
    except:
        sub_class = 'NA'
    try:
        molecular_framework = elem.xpath('hmdb:taxonomy/hmdb:molecular_framework/text()', namespaces=ns)[0]
    except:
        molecular_framework = 'NA'
    try:
        vmh_id = elem.xpath('hmdb:vmh_id/text()', namespaces=ns)[0]
    except:
        vmh_id = 'NA'    

    writer.writerow({'accession': accession, 'monisotopic_molecular_weight': monisotopic_molecular_weight, 'iupac_name': iupac_name, 'name': name, 'chemical_formula': chemical_formula, 'InChIKey': inchikey, 'cas_registry_number': cas_registry_number, 'smiles': smiles,'drugbank': drugbank,'chebi_id': chebi_id,'pubchem': pubchem,'phenol_explorer_compound_id':phenol_explorer_compound_id, 'food': food,'knapsack': knapsack, 'chemspider': chemspider,'kegg': kegg, 'meta_cyc': meta_cyc, 'bigg':bigg, 'metlin_id': metlin_id, 'pdb_id':pdb_id,'logpexp':logpexp, 'kingdom': kingdom, 'direct_parent': direct_parent, 'super_class': super_class, 'class': classorg, 'sub_class': sub_class, 'molecular_framework': molecular_framework, 'vmh_id': vmh_id})
    # It's safe to call clear() here because no descendants will be
    # accessed
    elem.clear()
    # Also eliminate now-empty references from the root node to elem
    for ancestor in elem.xpath('ancestor-or-self::*'):
        while ancestor.getprevious() is not None:
            del ancestor.getparent()[0]
  del context
  return;

def name_map(dfm, dfh):
    dfm['fullName'] = dfm['fullName'].map(lambda x: re.sub(r'\W+', '', x))
    dfm['fullName'] = dfm['fullName'].str.lower()
    dfh['name'] = dfh['name'].map(lambda x: re.sub(r'\W+', '', x))
    dfh['name'] = dfh['name'].str.lower()
    dfh['name'] = dfh['name'].str[2:]
    dfh['name'] = dfh['name'].str[:-1]
    dfh.rename(columns = {'name':'fullName'}, inplace = True)
    df = pd.merge(dfm, dfh, on = 'fullName', how = 'left')
    df['hmdb'].fillna(df['accession'])
    df = df.iloc[:,1:len(dfm.columns)]
    return df

def kegg_map(dfm, dfh):
    dfh.rename(columns = {'kegg':'keggId'}, inplace = True)
    df = pd.merge(dfm, dfh, on = 'keggId', how = 'left')
    df['hmdb'].fillna(df['accession'])
    df = df.iloc[:,1:len(dfm.columns)]
    return df

def chebi_map(dfm, dfh):
    dfh.rename(columns = {'chebi_id':'cheBlId'}, inplace = True)
    df = pd.merge(dfm, dfh, on = 'cheBlId', how = 'left')
    df['hmdb'].fillna(df['accession'])
    df = df.iloc[:,1:len(dfm.columns)]
    return df

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
    file_hmdb = sys.argv[3]

    df = pd.read_csv(file_input, sep='\t')
    hmdbextract(file_hmdb, 'hmdb.csv')
    dfh = pd.read_csv('hmdb.csv')
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

    df.to_csv(file_output, index=None)

if __name__ == '__main__':
    main()
