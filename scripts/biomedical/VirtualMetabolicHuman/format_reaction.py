'''
Author: Suhana Bedi
Date: 07/10/2021
Name: format_reaction.py
Description: Add dcids for all the reactions in the VMH database.
Map the reactions with corresponding VHM metabolites using
longest substring match and add it to the dataframe.
For dcid generation, map the reactions with reactions in
human1 data using metanetx and reaction and product compartment
match, if there is no perfect match, use the abbreviations for
dcid generation. Also, extract reactant and product compartment
using the 'formula' column.
@file_input: input .tsv from VMH with reactions list, csv from human1 data
and metabolite data from VMH.
@file_output: csv output file with metabolite match and
product and reactant compartments.
'''

import sys
import re
import pandas as pd
import numpy as np


# Convert string to list
def Convert(string):
    list1 = []
    list1[:0] = string
    return list1


#This function is used for checking if the small string (metabolite abbreviation) is
#an exact match with a substring, of the larger string (reaction abbreviation),
#keeping the order in place and retaining the starts with condition
def is_subset(list_long, list_short):
    short_length = len(list_short)
    subset_list = []
    for i in range(len(list_long) - short_length + 1):
        subset_list.append(list_long[i:i + short_length])
    for j in range(len(subset_list)):
        if (subset_list[j] == list_short):
            return True
        else:
            return False


#check nan
def isNaN(num):
    return num != num


# Perform a match between metabolites and reactions using abbreviations for both
def metabolite_rxn_match(df_rxn, df_metabolite):
    list_match = ['0'] * len(df_rxn['abbreviation'])
    list_dcids = ['0'] * len(df_rxn['abbreviation'])
    for p in range(len(df_rxn['abbreviation'])):
        for q in df_metabolite.index:
            test_list = Convert(df_rxn.loc[p, 'abbreviation'])
            for i in range(len(test_list)):
                test_list[i] = test_list[i].lower()
            sub_list = Convert(df_metabolite.loc[q, "abbreviation"])
            if (is_subset(test_list, sub_list)):
                if (list_match[p] != '0'):
                    if (len(list_match[p]) < len(sub_list)):
                        list_match[p] = sub_list
                        list_dcids[p] = df_metabolite.loc[q, "Id"]
                else:
                    list_dcids[p] = sub_list
                    list_dcids[p] = df_metabolite.loc[q, "Id"]
    df_rxn['metaboliteMatch'] = list_dcids
    return (df_rxn)


#Map the metanetx to humanGemIDs using human1D data
def vhm_human1_match(df_map, df_rxn):
    df_map_new = df_map[["id", "reactant_compartment",
                         "product_compartment"]].copy()
    l1 = df_map_new['id'].str[2:]
    df_map_new = df_map_new.drop('id', 1)
    df_map_new['humanGEMID'] = l1
    hgem_col = []
    for i in df_rxn["metanetx"].values:
        hgem_col.append(df_map[df_map["metanetx"] == i]["id"].values)
    df_rxn.insert(value=hgem_col, column="humanGEMID", loc=0)
    df_rxn = df_rxn.explode(column="humanGEMID")
    df_rxn["humanGEMID"] = np.where(pd.isnull(df_rxn['humanGEMID']),df_rxn['humanGEMID'] \
                                    ,df_rxn['humanGEMID'].str[2:])
    df_rxn["Id"] = np.where(pd.isnull(df_rxn['humanGEMID']),df_rxn['humanGEMID'] \
                                   ,"bio/" +df_rxn['humanGEMID'].astype(str))
    #merge two db with compartment info from human gemid (4)
    df = pd.merge(df_rxn, df_map_new, how="left", on='humanGEMID')
    return df


#Add reactant and product compartment columns
def reactant_product_comp(db_dup):
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
        if any(c in chars_to_check for c in db_dup.loc[i, "formula"]):
            p = db_dup.loc[i, "formula"]
            m = re.findall(r"\[([A-Za-z0-9_]+)\]", row["formula"])
            reactants, products = p.split('<=>')
            num_r = len(reactants.split("+"))
            db_dup.loc[i, "r_comp"] = m[0]
            db_dup.loc[i, "p_comp"] = m[0 + num_r]
            if (db_dup.loc[i, "humanGEMID"] == db_dup.loc[i, "humanGEMID"]):
                if m[0] in matchdict:
                    if((matchdict.get(m[0]) == db_dup.loc[i, "reactant_compartment"]) & \
                    (matchdict.get(m[0+num_r]) == db_dup.loc[i, "product_compartment"])) | \
                    ((matchdict.get(m[0]) == db_dup.loc[i, "product_compartment"]) & \
                    (matchdict.get(m[0+num_r]) == db_dup.loc[i, "reactant_compartment"])):
                        db_dup.loc[i, "bool-val"] = 1
                    else:
                        db_dup.loc[i, "bool-val"] = 0
        else:
            p = db_dup.loc[i, "formula"]
            m = re.findall(r"\[([A-Za-z0-9_]+)\]", row["formula"])
            reactants, products = p.split('->')
            num_r = len(reactants.split("+"))
            db_dup.loc[i, "r_comp"] = m[0]
            db_dup.loc[i, "p_comp"] = m[0 + num_r]
            if (db_dup.loc[i, "humanGEMID"] == db_dup.loc[i, "humanGEMID"]):
                if m[0] in matchdict:
                    if(matchdict.get(m[0]) == db_dup.loc[i, "reactant_compartment"]) & \
                    (matchdict.get(m[0+num_r]) == db_dup.loc[i, "product_compartment"]):
                        db_dup.loc[i, "bool-val"] = 1
                    elif(matchdict.get(m[0]) == db_dup.loc[i, "reactant_compartment"][0]) & \
                    (matchdict.get(m[0+num_r]) == db_dup.loc[i, "product_compartment"][0]):
                        db_dup.loc[i, "bool-val"] = 1
                    else:
                        db_dup.loc[i, "bool-val"] = 0
    # drop duplicated abbreviations based on bool vals, keep 1s, remove the zeroes
    sorted_df = db_dup.sort_values("bool-val", ascending=False)
    dropped_df = sorted_df.drop_duplicates("abbreviation").sort_index()
    return dropped_df


def main():

    file_input = sys.argv[1]
    file_output = sys.argv[2]
    file_gemid = sys.argv[3]
    file_metabolite = sys.argv[4]

    df_rxn = pd.read_csv(file_input, sep='\t')
    df_map = pd.read_csv(file_gemid)
    df_metabolite = pd.read_csv(file_metabolite)

    # Format the subsystem field
    df_rxn["subsystem"] = df_rxn["subsystem"].str.lower()
    for i in df_rxn.index:
        l = df_rxn.loc[i, 'subsystem']
        l = l.replace(',', '')
        l = l.replace(' ', '_')
        df_rxn.loc[i, 'subsystem'] = l

    # Perform a match between metabolites and reactions using abbreviations for both
    df_rxn = metabolite_rxn_match(df_rxn, df_metabolite)
    #Map the metanetx to humanGemIDs using human1D data
    db_dup = vhm_human1_match(df_map, df_rxn)
    # Add reactant and product compartment columns
    dropped_df = reactant_product_comp(db_dup)
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
            if dropped_df.loc[i, 'metaboliteMatch'] != '0':
                if "Transport" in dropped_df.loc[i, 'description']:
                    dropped_df.loc[i, 'rcc'] = dropped_df.loc[i, 'metaboliteMatch'] + \
                        "_" + dict_comp_name.get(dropped_df.loc[i, 'r_comp'])
                    dropped_df.loc[i, 'pcc'] = dropped_df.loc[i, 'metaboliteMatch'] + \
                    "_" + dict_comp_name.get(dropped_df.loc[i, 'p_comp'])
                else:
                    dropped_df.loc[i, 'rcc'] = dropped_df.loc[i, 'metaboliteMatch'] + \
                    "_" + dict_comp_name.get(dropped_df.loc[i, 'r_comp'])
                    dropped_df.loc[i, 'pcc'] = dropped_df.loc[i, 'metaboliteMatch'] + \
                    "_" + dict_comp_name.get(dropped_df.loc[i, 'r_comp'])

    dropped_df.update(
        '"' + dropped_df[['description', 'formula', 'ecnumber']].astype(str) + '"')
    dropped_df.drop(columns=['reactant_compartment', 'product_compartment'])
    dropped_df.to_csv(file_output, index=None)


if __name__ == '__main__':
    main()
