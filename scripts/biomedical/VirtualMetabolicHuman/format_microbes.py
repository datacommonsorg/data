'''
Author: Suhana Bedi
Date: 07/10/2021
Name: format_microbe.py
Description: Add dcids for all the microbes present in the data base, and query
using the datacommons to see if a node the microbe already exists.
Declare the columns, 'oxygenstat', 'metabolism', 'gram', 'mtype' and 'platform'
as enums
@file_input: input .tsv from VMH with microbiome data
@file_output: csv output file with enums and dcids generated
'''
import sys
import pandas as pd
import datacommons as dc

def modify_org_name(df_microbes):
    """
    Modifies the organism name in the dataframe for an
    efficient sparql query
    Arg:
        Dataframe with microbe names
    Returns:
        List with modified microbe names    
    """
    org_name = ['0']*len(df_microbes['organism'])
    for i in df_microbes.index:
        l = df_microbes.loc[i, "organism"].split(' ')
        org_name[i] = l[0] + " " + l[1]
    return org_name

def org_name_query():
    """
    Performs a sparql query to retrieve all microbes names
    on datacommons and wraps the species_dcids in a list
    Arg: None
    Returns:
        list with specie dcids
    """
    query_str = '''
    SELECT ?node
    WHERE {
    ?node typeOf Species .
    ?node organismTaxonomicKingdom ?kingdom .
    ?kingdom name Bacteria .
    }
    '''
    result = dc.query(query_str)
    specie_dcids = ['0'] * len(result)
    for index in range(len(result)):
        for key in result[index]:
            specie_dcids[index] = result[index][key]
    return specie_dcids

def scientific_name_query(specie_dcids):
    """
    Fetches the scientific names from the list
    of dcids
    Arg:
        specie_dcids = list of dcids
    Returns:
        df_species = df with specie dcids and names
    """
    df_species = pd.DataFrame()
    df_species['species_dcid'] =  specie_dcids

    df_species['species_name'] = df_species['species_dcid'].map(
        dc.get_property_values(df_species['species_dcid'], 'scientificName'))
    df_species = df_species.explode('species_name')
    return df_species

def generate_dcid(df_species, org_name, df_microbes):
    """
    Adds dcids to name matches and generates
    new ones if they don't exist on dc
    Arg:
        df_species = df with species names 
        and dcids
        org_name = list of microbe names 
        from dc query
        df_microbes = original microbes df
    Returns:
        df_microbes = microbes df with dcid addeed
    """
    specie_count = ['0']*len(df_microbes['organism'])
    for i in range(len(org_name)):
        for j in df_species.index:
            if(org_name[i] == df_species.loc[j, "species_name"]):
                org_name[i] = df_species.loc[j, "species_dcid"]
                specie_count[i] = '1'

    #map dcids and create new ones, in case they don't exist on dc
    for j in range(len(specie_count)):
        if specie_count[j] == '0':
            p = org_name[j].split(' ')
            org_name[j] = "bio/" + ( p[0][0].upper() + 
            p[0][1].upper() + p[0][2].upper() + 
            p[1][0].upper() + p[1][1].upper() )

    df_microbes.insert(0, 'Id', org_name)
    return df_microbes

def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    df_microbes = pd.read_csv(file_input, sep = '\t')
    
    org_name = modify_org_name(df_microbes)
    specie_dcids = org_name_query

    df_species = scientific_name_query(specie_dcids)
    df_microbes = generate_dcid(df_species, org_name, df_microbes)
   
    #format the columns declared as enums
    list_col = ['metabolism', 'oxygenstat', 'mtype']
    for i in list_col:
        p = df_microbes[i]
        p = p.str.replace(',', '', regex=True)
        p = p.str.replace(' ', '_', regex=True)
        df_microbes[i] = p

    # enum-column dict
    col_enum_dict = {"gram":"dcs:BacteriaGramStainType", "platform":"dcs:DataCollectionPlatform",
    "metabolism":"dcs:MicrobialMetabolismType", "oxygenstat":"dcs:OxygenRequirementStatus",
    "mtype":"dcs:PathogenMethodOfInvasion"}
    for i in col_enum_dict:
        p = col_enum_dict.get(i) + df_microbes[i] 
        df_microbes[i] = p    
    #Date conversion to ISO format
    for i in df_microbes.index:
        if df_microbes.loc[i, 'draftcreated'] == df_microbes.loc[i, 'draftcreated']:
            l = df_microbes.loc[i, 'draftcreated'].split('/')
            iso_date = "20" + l[2] + "-" + l[0] + "-" + l[1]
            df_microbes.loc[i, 'draftcreated'] = iso_date
    df_microbes.to_csv(file_output, index = None)
if __name__ == '__main__':
    main()
