import pandas as pd
import sys
import os
import numpy as np
import re

# Convert string to list 
def Convert(string):
    list1=[]
    list1[:0]=string
    return list1


#is_subset function for checking if the small string (metabolite abbreviation) is an exact match with a substring 
#of the larger string (reaction abbreviation), keeping the order in place and retaining the starts with condition 
def is_subset(list_long,list_short):
    short_length = len(list_short)
    subset_list = []
    for i in range(len(list_long)-short_length+1):
        subset_list.append(list_long[i:i+short_length])
    for j in range(len(subset_list)):
        if(subset_list[j] == list_short):
            return True
        else:
            return False

#check nan           
def isNaN(num):
    return num != num

def main():
    
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    file_gemid = sys.argv[3]
    file_metabolite = sys.argv[4]

    df_rxn = pd.read_csv(file_input, sep = '\t')
    df_map = pd.read_csv(file_gemid)
    df_metabolite = pd.read_csv(file_metabolite)
    
    df_rxn["subsystem"]  = df_rxn["subsystem"].str.lower()
  
    
    # Format the subsystem field
    for i in df_rxn.index:
        l = df_rxn.loc[i, 'subsystem']
        l = l.replace(',', '')
        df_rxn.loc[i, 'subsystem'] = l
    for i in df_rxn.index:
        l = df_rxn.loc[i, 'subsystem']
        l = l.replace(' ', '_')
        df_rxn.loc[i, 'subsystem'] = l
    list_match = ['0']*len(df_rxn['abbreviation'])
    list_dcids = ['0']*len(df_rxn['abbreviation'])
  
    # Perform a match between metabolites and reactions
    # Using abbreviations for both
    for p in range(len(df_rxn['abbreviation'])):
        for q in df_metabolite.index:
            test_list = Convert(df_rxn.loc[p, 'abbreviation'])
            for i in range(len(test_list)):
                test_list[i] = test_list[i].lower()
            sub_list = Convert(df_metabolite.loc[q, "abbreviation"])
            if(is_subset(test_list, sub_list)):
                if(list_match[p] != '0'):
                    if(len(list_match[p]) < len(sub_list)):
                        list_match[p] = sub_list
                        list_dcids[p] = df_metabolite.loc[q, "Id"]
                else:
                    list_dcids[p] = sub_list
                    list_dcids[p] = df_metabolite.loc[q, "Id"]

    df_rxn['metaboliteMatch'] = list_dcids
    
    
    #Map the metanetx to humanGemIDs using human1D data

    # create new db with compartments from human gem id (2)
    #df_map_new = pd.DataFrame()
    df_map_new = df_map[["id", "reactant_compartment", "product_compartment"]].copy()
    l1 = df_map_new['id'].str[2:]
    df_map_new = df_map_new.drop('id', 1)
    df_map_new['humanGEMID'] = l1

    hgem_col = []
    for i in df_rxn["metanetx"].values:
        hgem_col.append(df_map[df_map["metanetx"] == i]["id"].values)
    df_rxn.insert(value = hgem_col, column = "humanGEMID", loc = 0)
    df_rxn = df_rxn.explode(column = "humanGEMID")
    df_rxn["humanGEMID"] = np.where(pd.isnull(df_rxn['humanGEMID']),df_rxn['humanGEMID'] \
                                    ,df_rxn['humanGEMID'].str[2:])
    df_rxn["Id"] = np.where(pd.isnull(df_rxn['humanGEMID']),df_rxn['humanGEMID'] \
                                   ,"bio/" +df_rxn['humanGEMID'].astype(str))


    #merge two db with compartment info from human gemid (4)
    df = pd.merge(df_rxn, df_map_new, on='humanGEMID')

    db = df
    db_dup = db
    #db_dup = db.sample(n = 400)
    # dict to map compartment info b/w gemid and formula (vhm -> human 1d)
    matchdict = {
    "e": "s",
    "x": "p",
    "i": "c_i",
    "c": "c",
    "s": "s",
    "l": "l",
    "r": "r",
    "m": "m",
    "g": "g",
    "n": "n"
        
    }
    chars_to_check = '='
    for i, row in db_dup.iterrows():
        if any(c in chars_to_check for c in db_dup.loc[i,"formula"]):
                #print(i)
            p = db_dup.loc[i,"formula"]
            m = re.findall(r"\[([A-Za-z0-9_]+)\]", row["formula"])
                #print(m)
                #print("in <=>")
                #print(p)
            reactants, products = p.split('<=>')
            num_r = len(reactants.split("+"))
                #print(reactants)
                #print("Num_reactants", len(reactants.split("+")))
                #print("Num_products", len(products.split("+")))
            db_dup.loc[i, "r_comp"] = m[0]
            db_dup.loc[i, "p_comp"] = m[0+num_r]
            if(db_dup.loc[i, "humanGEMID"] == db_dup.loc[i, "humanGEMID"]):
                if m[0] in matchdict:
                    if((matchdict.get(m[0]) == db_dup.loc[i, "reactant_compartment"]) & (matchdict.get(m[0+num_r]) == db_dup.loc[i, "product_compartment"])) | ((matchdict.get(m[0]) == db_dup.loc[i, "product_compartment"]) & (matchdict.get(m[0+num_r]) == db_dup.loc[i, "reactant_compartment"])):
                        db_dup.loc[i, "bool-val"] = 1
                    #elif(matchdict.get(m[0]) == db_dup.loc[i,"reactant_compartment"][0]) & (matchdict.get(m[0+num_r]) == db_dup.loc[i,"product_compartment"][0]) | ((matchdict.get(m[0]) == db_dup.loc[i,"product_compartment"][0]) & (matchdict.get(m[0+num_r]) == db_dup.loc[i,"reactant_compartment"][0])):
                        #db_dup.loc[i,"bool-val"] = 1
                    else:
                        db_dup.loc[i, "bool-val"] = 0
        else:
            #print(i)
            p = db_dup.loc[i, "formula"]
            m = re.findall(r"\[([A-Za-z0-9_]+)\]", row["formula"])
                #print(m)
                #print("in ->")
                #print(p)
            reactants, products = p.split('->')
            num_r = len(reactants.split("+"))
            num_p = len(products.split("+"))
                #print("Num_reactants", len(reactants.split("+")))
                #print("Num_products", len(products.split("+")))
            db_dup.loc[i, "r_comp"] = m[0]
            db_dup.loc[i, "p_comp"] = m[0+num_r]
            if(db_dup.loc[i, "humanGEMID"] == db_dup.loc[i, "humanGEMID"]):
                if m[0] in matchdict:
                    if(matchdict.get(m[0]) == db_dup.loc[i, "reactant_compartment"]) & (matchdict.get(m[0+num_r]) == db_dup.loc[i, "product_compartment"]):
                        db_dup.loc[i, "bool-val"] = 1
                    elif(matchdict.get(m[0]) == db_dup.loc[i, "reactant_compartment"][0]) & (matchdict.get(m[0+num_r]) == db_dup.loc[i, "product_compartment"][0]):
                        db_dup.loc[i, "bool-val"] = 1
                    else:
                        db_dup.loc[i, "bool-val"] = 0

       # drop duplicated abbreviations based on bool vals, keep 1s, remove the zeroes
    sorted_df = db_dup.sort_values("bool-val", ascending=False)
    dropped_df = sorted_df.drop_duplicates("abbreviation").sort_index()
    #dropped_df.head(50)
    
    # give zeroes to all with no human gemid match at first
    for i in dropped_df.index:
        if isNaN(dropped_df.loc[i, 'bool-val']):
            dropped_df.loc[i, 'bool-val'] = 0

    # remove human gem ids for bool-val = 0 as it is indicative of imperfect match
    for i in dropped_df.index:
        if dropped_df.loc[i, 'bool-val'] == 0:
            dropped_df.loc[i, 'humanGEMID'] = float("NaN")
            dropped_df.loc[i, 'Id'] = float("NaN")
            

    # so all zeroes in the bool-val column have no match with human gem
    for i in dropped_df.index:
        if dropped_df.loc[i, 'bool-val'] == 0:
            dropped_df.loc[i, 'Id'] = "bio/" + dropped_df.loc[i, 'abbreviation']

    dict_comp_name = {
    "e": "Extracellular",
    "x": "Peroxisome",
    "i": "InnerMitochondria",
    "c": "Cytosol",
    "s": "Extracellular",
    "l": "Lysosome",
    "r": "EndoplasmicReticulum",
    "m": "Mitochondria",
    "g": "GolgiApparatus",
    "n": "Nucleus"
    }

    for i in dropped_df.index:
        if dropped_df.loc[i, 'bool-val'] == 0:
            if dropped_df.loc[i, 'MetaboliteMatch'] != '0':
                if "Transport" in dropped_df.loc[i, 'description']:
                    dropped_df.loc[i, 'rcc'] = dropped_df.loc[i, 'MetaboliteMatch'] + "_" + dict_comp_name.get(dropped_df.loc[i, 'r_comp'])
                    dropped_df.loc[i, 'pcc'] = dropped_df.loc[i, 'MetaboliteMatch'] + "_" + dict_comp_name.get(dropped_df.loc[i, 'p_comp'])
                else:
                    dropped_df.loc[i, 'rcc'] = dropped_df.loc[i, 'MetaboliteMatch'] + "_" + dict_comp_name.get(dropped_df.loc[i, 'r_comp'])
                    dropped_df.loc[i, 'pcc'] = dropped_df.loc[i, 'MetaboliteMatch'] + "_" + dict_comp_name.get(dropped_df.loc[i, 'r_comp'])
    
    #dropped_df.update('"' + df_rxn[['description', 'formula', 'ecnumber']].astype(str) + '"')
    
    dropped_df.to_csv(file_output, index = None)


if __name__ == '__main__':
    main()

