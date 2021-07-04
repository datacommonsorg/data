import sys
import pandas as pd
import os
import numpy as np
import csv
from SPARQLWrapper import SPARQLWrapper, JSON
import datacommons as dc

def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    
    df_microbes = pd.read_csv(file_input, sep ='\t')
    
    ## modify the organism name for a sparql query
    org_name = ['0']*818
    for i in df_microbes.index:
        l = df_microbes.loc[i,"organism"].split(' ')
        org_name[i] = l[0] + " " + l[1]


    ## sparql query on datacommons to extract dcids for pre-exisitng organism 
    query_str = '''
    SELECT ?node
    WHERE {
      ?node typeOf Species .
      ?node organismTaxonomicKingdom ?kingdom .
      ?kingdom name Bacteria .
    }
    '''

    result = dc.query(query_str)
    
    #wrap the specie_dcids obtained above, in a list
    specie_dcids = ['0'] * 3853
    for index in range(len(result)):
        for key in result[index]:
            specie_dcids[index] = result[index][key]
  
    #Obtain the scientific name of the organisms whose dcids were queried for
    df_specie = pd.DataFrame()
    df_specie['species_dcid'] =  specie_dcids

    df_specie['species_name'] = df_specie['species_dcid'].map(
        dc.get_property_values(df_specie['species_dcid'], 'scientificName'))
    df_specie = df_specie.explode('species_name')

    #find the rows where the organism name obtained doesnt match the dc query
    specie_count = ['0']*818
    for i in range(len(org_name)):
        for j in df_specie.index:
            if(org_name[i] == df_specie.loc[j, "species_name"]):
                org_name[i] = df_specie.loc[j, "species_dcid"]
                specie_count[i] = '1'

    #map dcids and create new ones, in case they don't exist on dc
    for j in range(len(specie_count)):
        if specie_count[j] == '0':
            p = org_name[j].split(' ')
            org_name[j] = "bio/" + p[0][0].upper() + p[0][1].upper() + p[0][2].upper() + p[1][0].upper() + p[1][1].upper()

    df_microbes.insert(0, 'Id', org_name)
   


    #format the columns declared as enums
    df_microbes['metabolism'] = df_microbes['metabolism'].str.replace(',','', regex=True)
    df_microbes['metabolism'] = df_microbes['metabolism'].str.replace(' ','_', regex=True)
    df_microbes['oxygenstat'] = df_microbes['oxygenstat'].str.replace(',','', regex=True)
    df_microbes['oxygenstat'] = df_microbes['oxygenstat'].str.replace(' ','_', regex=True)
    df_microbes['mtype'] = df_microbes['mtype'].str.replace(',','', regex=True)
    df_microbes['mtype'] = df_microbes['mtype'].str.replace(' ','_', regex=True)




    for i in df_microbes.index:
        concat_str = df_microbes.loc[i, "gram"]
        df_microbes.loc[i, "gram"] = "dcs:BacteriaGramStainType" + str(concat_str)

    for i in df_microbes.index:
        concat_str = df_microbes.loc[i, "platform"]
        df_microbes.loc[i, "platform"] = "dcs:DataCollectionPlatform" + str(concat_str)
    
    for i in df_microbes.index:
        concat_str = df_microbes.loc[i, "metabolism"]
        df_microbes.loc[i, "metabolism"] = "dcs:MicrobialMetabolismType" + str(concat_str)

    for i in df_microbes.index:
        concat_str = df_microbes.loc[i, "oxygenstat"]
        df_microbes.loc[i, "oxygenstat"] = "dcs:OxygenRequirementStatus" + str(concat_str)
    
    for i in df_microbes.index:
        concat_str = df_microbes.loc[i, "mtype"]
        df_microbes.loc[i, "oxygenstat"] = "dcs:PathogenMethodOfInvasionEnum" + str(concat_str)
    

    #Date conversion to ISO format
    for i in df_microbes.index:
        if df_microbes.loc[i,'draftcreated'] == df_microbes.loc[i,'draftcreated']:
            l = df_microbes.loc[i,'draftcreated'].split('/')
            iso_date = "20" + l[2] + "-" + l[0] + "-" + l[1]
            df_microbes.loc[i,'draftcreated'] = iso_date

    df_microbes.to_csv(file_output, index = None)
if __name__ == '__main__':
    main()
