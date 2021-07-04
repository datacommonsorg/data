import sys
import os
import pandas as pd
import numpy as np
import csv
from SPARQLWrapper import SPARQLWrapper, JSON
import datacommons as dc
import bioservices 
from bioservices import *

def isNaN(num):
    return num != num

def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]

    df = pd.read_csv(file_input, sep='\t')

    '''

    ## Add dcid column
    list_dcid = ['0'] * len(df['abbreviation'])
    for i in df.index:
        l = df.loc[i,'abbreviation']
        list_dcid[i] = "bio/" + l
    
    df.insert(0,'Id', list_dcid)
    '''
    
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

    ind_count = 0
    dcid_inch = []
    result = dc.query(query_str)
    for index in range(len(result)):
        for key in result[index]:
            dcid_inch.insert(ind_count, result[index][key])
            ind_count += 1

    count_query = 0
    for i in df.index:
        for j in range(1,len(dcid_inch)):
            if df.loc[i,'inchiKey'] == dcid_inch[j]:
                count_query += 1
                df.loc[i,'Id'] = dcid_inch[j - 1]
                j += 2
    #inchi match complete  (1)          

    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug inChIKey ?id .
    ?drug inChIKey {0} .
    }}
    """.format(arr_inchi_2)
    result = dc.query(query_str)

    ind_count = 0
    dcid_inch = []
    result = dc.query(query_str)
    for index in range(len(result)):
        for key in result[index]:
            dcid_inch.insert(ind_count, result[index][key])
            ind_count += 1

    count_query = 0
    for i in df.index:
        for j in range(1,len(dcid_inch)):
            if df.loc[i,'inchiKey'] == dcid_inch[j]:
                count_query += 1
                df.loc[i,'Id'] = dcid_inch[j - 1]
                j += 2
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

    ind_count = 0
    dcid_inch = []
    result = dc.query(query_str)
    for index in range(len(result)):
        for key in result[index]:
            dcid_inch.insert(ind_count, result[index][key])
            ind_count += 1

    count_query = 0
    for i in df.index:
        for j in range(1,len(dcid_inch)):
            if df.loc[i,'inchiKey'] == dcid_inch[j]:
                count_query += 1
                df.loc[i,'Id'] = dcid_inch[j - 1]
                j += 2
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

    ind_count = 0
    dcid_hmdb = []
    result = dc.query(query_str)
    for index in range(len(result)):
        for key in result[index]:
            dcid_hmdb.insert(ind_count, result[index][key])
            ind_count += 1

    count_query = 0
    for i in df.index:
        for j in range(1,len(dcid_hmdb)):
            if df.loc[i,'hmdb'] == dcid_hmdb[j]:
                count_query += 1
                df.loc[i,'Id'] = dcid_hmdb[j - 1]
    #hmdb match complete (1)

    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug humanMetabolomeDatabaseID ?id .
    ?drug humanMetabolomeDatabaseID {0} .
    }}
    """.format(arr_hmdb_2)
    result = dc.query(query_str)

    ind_count = 0
    dcid_hmdb = []
    result = dc.query(query_str)
    for index in range(len(result)):
        for key in result[index]:
            dcid_hmdb.insert(ind_count, result[index][key])
            ind_count += 1

    count_query = 0
    for i in df.index:
        for j in range(1,len(dcid_hmdb)):
            if df.loc[i,'hmdb'] == dcid_hmdb[j]:
                count_query += 1
                df.loc[i,'Id'] = dcid_hmdb[j - 1]
    #hmdb match complete (2)

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

    ind_count = 0
    dcid = []
    result = dc.query(query_str)
    for index in range(len(result)):
        for key in result[index]:
            dcid.insert(ind_count, result[index][key])
            ind_count += 1

    count_query = 0
    for i in df.index:
        for j in range(1,len(dcid)):
            if df.loc[i,'keggId'] == dcid[j]:
                count_query += 1
                df.loc[i,'Id'] = dcid[j - 1]
    #kegg match complete (2)

    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug keggCompoundID ?id .
    ?drug keggCompoundID {0} .
    }}
    """.format(arr_kegg_2)
    result = dc.query(query_str)

    ind_count = 0
    dcid = []
    result = dc.query(query_str)
    for index in range(len(result)):
        for key in result[index]:
            dcid.insert(ind_count, result[index][key])
            ind_count += 1

    count_query = 0
    for i in df.index:
        for j in range(1,len(dcid)):
            if df.loc[i,'keggId'] == dcid[j]:
                count_query += 1
                df.loc[i,'Id'] = dcid[j - 1]
    #kegg match complete (2)

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

    ind_count = 0
    dcid = []
    result = dc.query(query_str)
    for index in range(len(result)):
        for key in result[index]:
            dcid.insert(ind_count, result[index][key])
            ind_count += 1

    count_query = 0
    for i in df.index:
        for j in range(1,len(dcid)):
            if df.loc[i,'cheBlId'] == dcid[j]:
                count_query += 1
                df.loc[i,'Id'] = dcid[j - 1]
    #chebi match complete (1)

    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug chebiID ?id .
    ?drug chebiID {0} .
    }}
    """.format(arr_chebi_2)
    result = dc.query(query_str)

    ind_count = 0
    dcid = []
    result = dc.query(query_str)
    for index in range(len(result)):
        for key in result[index]:
            dcid.insert(ind_count, result[index][key])
            ind_count += 1

    count_query = 0
    for i in df.index:
        for j in range(1,len(dcid)):
            if df.loc[i,'cheBlId'] == dcid[j]:
                count_query += 1
                df.loc[i,'Id'] = dcid[j - 1]
    #chebi match complete (2)

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

    ind_count = 0
    dcid = []
    result = dc.query(query_str)
    for index in range(len(result)):
        for key in result[index]:
            dcid.insert(ind_count, result[index][key])
            ind_count += 1

    count_query = 0
    for i in df.index:
        for j in range(1,len(dcid)):
            if df.loc[i,'pubChemId'] == dcid[j]:
                count_query += 1
                df.loc[i,'Id'] = dcid[j - 1]
    #pubchem match complete (1)

    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug pubChemCompoundID ?id .
    ?drug pubChemCompoundID {0} .
    }}
    """.format(arr_pub_2)
    result = dc.query(query_str)

    ind_count = 0
    dcid = []
    result = dc.query(query_str)
    for index in range(len(result)):
        for key in result[index]:
            dcid.insert(ind_count, result[index][key])
            ind_count += 1

    count_query = 0
    for i in df.index:
        for j in range(1,len(dcid)):
            if df.loc[i,'pubChemId'] == dcid[j]:
                count_query += 1
                df.loc[i,'Id'] = dcid[j - 1]
    #pubchem match complete (2)

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

    ind_count = 0
    dcid = []
    result = dc.query(query_str)
    for index in range(len(result)):
        for key in result[index]:
            dcid.insert(ind_count, result[index][key])
            ind_count += 1

    count_query = 0
    for i in df.index:
        for j in range(1,len(dcid)):
            if df.loc[i,'chemspider'] == dcid[j]:
                count_query += 1
                df.loc[i,'Id'] = dcid[j - 1]
    #chemspider match complete (1)

    query_str = """
    SELECT DISTINCT ?drug ?id
    WHERE {{
    ?drug typeOf ChemicalCompound .
    ?drug chemSpiderID ?id .
    ?drug chemSpiderID {0} .
    }}
    """.format(arr_chem_2)
    result = dc.query(query_str)

    ind_count = 0
    dcid = []
    result = dc.query(query_str)
    for index in range(len(result)):
        for key in result[index]:
            dcid.insert(ind_count, result[index][key])
            ind_count += 1

    count_query = 0
    for i in df.index:
        for j in range(1,len(dcid)):
            if df.loc[i,'chemspider'] == dcid[j]:
                count_query += 1
                df.loc[i,'Id'] = dcid[j - 1]
    #chemspider match complete (2)

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

    ind_count = 0
    dcid = []
    result = dc.query(query_str)
    for index in range(len(result)):
        for key in result[index]:
            dcid.insert(ind_count, result[index][key])
            ind_count += 1

    count_query = 0
    for i in df.index:
        for j in range(1,len(dcid)):
            if df.loc[i,'drugbank'] == dcid[j]:
                count_query += 1
                df.loc[i,'Id'] = dcid[j - 1]
    #drug bank match complete



    uni = UniChem()
    mapping = uni.get_mapping("kegg_ligand", "chembl")

    # Add chemblID column in the dataframe and add the corresponding chembl ids for each entry 
    chembl_list = [0]*len(df['keggId'])
    df.insert(7, 'ChEMBL',chembl_list )

    for index, row in df.iterrows():
        try:
    #chembl_list.insert(index, mapping[row['keggId']] )
            chembl_list[index] = mapping[row['keggId']]
        except:
            pass
    df['ChEMBL'] = chembl_list 

    # Add dcids w.r.t chembl ids and chemical formulae(where chembl is missing)
    for i in df.index:
        if df.loc[i,'ChEMBL'] != 0:
            df.loc[i, 'Id'] = 'bio/' + str(df.loc[i,'ChEMBL'])
        

    # Add dcids based on IUPAC names if no previous matches
    for i in df.index: 
        l = df.loc[i,'fullName']
        l = l.replace(' ','_')
        l = l.replace(',','_')
        df.loc[i,'fullName'] = l

    for i in df.index:  
        if isNaN(df.loc[i,'Id']):
            df.loc[i,'Id'] = "bio/" + df.loc[i,'fullName'] 


        #p = n.replace(",","")
        #m = p.replace(" ","_")        
    # Change column names to avoid any abbreviations
    #df.columns = ['Id','Abbreviation', 'Name', 'Charged_Formula', 'Charge', 'Average_Molecular_Weight', 'Monoisotopic_Weight', 'ChEMBL','KEGGID' , 'PubChemID', 'ChebiID', 'HMDB' , 'PDMapName', 'Reconmap', 'ReconMap3', 'FoodDB', 'ChemSpider', 'BioCyc', 'BiggID', 'Wikipedia', 'DrugBank', 'Seed', 'MetaNetX', 'KNApSAck', 'METLIN', 'CAS_REGISTRY', 'epa_ID', 'InCHIKey', 'InCHIString', 'SMILES']
    
    #df.update('"' + df[['Name']].astype(str) + '"')
    # Add output file to the current directory
    df.to_csv(file_output, index = None)
    

if __name__ == '__main__':
    main()

