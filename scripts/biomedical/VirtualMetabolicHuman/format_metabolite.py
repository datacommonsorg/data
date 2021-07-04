import sys
import os
import pandas as pd
import numpy as np
import csv
import bioservices 
from bioservices import *

def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]

    df = pd.read_csv(file_input, sep='\t')

    ## Add dcid column
    list_dcid = ['0'] * len(df['abbreviation'])
    for i in df.index:
        l = df.loc[i,'abbreviation']
        list_dcid[i] = "bio/" + l
    
    df.insert(0,'Id', list_dcid)
    
    ## Getting chembl ids from kegg ids


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
        if df.iloc[i]['ChEMBL'] != 0:
            df.loc[i, ['Id']] = 'bio/' + str(df.iloc[i]['ChEMBL'])
        else:
            df.loc[i, ['Id']] = 'bio/' + str(df.iloc[i]['chargedFormula'])
    # Change column names to avoid any abbreviations
    df.columns = ['Id','Abbreviation', 'Name', 'Charged_Formula', 'Charge', 'Average_Molecular_Weight', 'Monoisotopic_Weight', 'ChEMBL','KEGGID' , 'PubChemID', 'ChebiID', 'HMDB' , 'PDMapName', 'Reconmap', 'ReconMap3', 'FoodDB', 'ChemSpider', 'BioCyc', 'BiggID', 'Wikipedia', 'DrugBank', 'Seed', 'MetaNetX', 'KNApSAck', 'METLIN', 'CAS_REGISTRY', 'epa_ID', 'InCHIKey', 'InCHIString', 'SMILES']
    
    df.update('"' + df[['Name']].astype(str) + '"')
    # Add output file to the current directory
    df.to_csv(file_output, index = None)
    

if __name__ == '__main__':
    main()

