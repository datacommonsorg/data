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
Author: Khoa Hoang
Date: 08/11/2021
Name: format_metabolites.py
Description: This script formats metabolites.tsv, reactantRoles.tsv
and productRoles.tsv files to combine with tMCF files
for import to data commons
@file_input: metabolites.tsv, reactantRoles, productRoles.tsv
in human1 dataset and humanGEM_HMDB_map.csv
@file_output: formatted metabolites.csv, reactantRoles.csv,
productRoles.csv, and metabolicCellularCompartment.csv
'''

import sys
import os
import numpy as np
import pandas as pd
import datacommons as dc
from bioservices import UniChem

# dictionary to map values in "compartment"
# column to CellularCompartmentEnum values
COMPARTMENT_DICT = {
    "c": "dcs:CellularCompartmentCytosol",
    "s": "dcs:CellularCompartmentExtracellular",
    "l": "dcs:CellularCompartmentLysosome",
    "r": "dcs:CellularCompartmentEndoplasmicReticulum",
    "m": "dcs:CellularCompartmentMitochondria",
    "p": "dcs:CellularCompartmentPeroxisome",
    "g": "dcs:CellularCompartmentGolgiApparatus",
    "n": "dcs:CellularCompartmentNucleus",
    "c_i": "dcs:CellularCompartmentInnerMitochondria"
}


def format_df_metatbolites(df_metabolites):
    """format df_metabolites to match datacommons format
   Args:
       df_metabolites: pd.DataFrame of metabolites file
   Returns:
       df_metabolites: formatted metabolites Dataframe
   """
    # modify id to humanGEMID format
    df_metabolites["id"] = df_metabolites["id"].str[2:]
    # Create new column for dcid
    df_metabolites["metabolite_dcid"] = df_metabolites["chembl"]
    # use hmdb as dcid if chemblID is not available
    df_metabolites["metabolite_dcid"] =\
                df_metabolites["metabolite_dcid"].fillna(\
                               df_metabolites["hmdb"])
    # use metaNetX as dcid if hmdb id is not available
    df_metabolites["metabolite_dcid"] =\
                df_metabolites["metabolite_dcid"].fillna(\
                               df_metabolites["metanetx.chemical"])
    # use chemical name as dcid if metaNetX is not available
    df_metabolites["metabolite_dcid"] =\
                df_metabolites["metabolite_dcid"].fillna(df_metabolites["name"])
    # format dcid -> bio/
    df_metabolites["metabolite_dcid"] = "bio" + "/" +\
                df_metabolites["metabolite_dcid"].str.replace(":", "")
    df_metabolites["metabolite_dcid"] =\
                 df_metabolites["metabolite_dcid"].str.replace(",", "_")
    # Format chemblID, remove ":"
    df_metabolites["chembl"] = df_metabolites["chembl"].str.replace(":", "")
    #convert chebiID and chemicalName to string with quotation
    df_metabolites['chebi'] = np.where(pd.isnull(df_metabolites['chebi']),\
               df_metabolites['chebi'],\
                              '"' + df_metabolites['chebi'].astype(str) + '"')
    df_metabolites['name'] = np.where(pd.isnull(df_metabolites['name']),\
               df_metabolites['name'],\
                              '"' + df_metabolites['name'].astype(str) + '"')
    # modify compartment to Enum type
    df_metabolites["compartment"] = \
               df_metabolites["compartment"].map(COMPARTMENT_DICT)
    return df_metabolites

def fill_chembl_from_hmdb(df):
    """convert all chebi to pubchem with
    Data Commons query and fill missing
    chembl with converted results inplace
    Args:
        df: pandas.Dataframe with chemble and chebi info
    Returs:
        None
    """
    human_met_list = list(df\
                [df["chembl"].isna()]["hmdb"].unique())
    if np.nan in human_met_list:
        human_met_list.remove(np.nan)
    human_met_list = np.array(human_met_list)
    result = query_chembl_from_hmdb(human_met_list[:1000])
    result2 = query_chembl_from_hmdb(human_met_list[1000:])
    for res in result:
        df.loc[df["hmdb"] == res["?hmdb"], "chembl"]\
                        = res["?chembl"].split("/")[1]
    for res in result2:
        df.loc[df["hmdb"] == res["?hmdb"], "chembl"]\
                        = res["?chembl"].split("/")[1]
    print("DONE converting hmdb to chembl with data common query")


def fill_chembl_from_pubchem(df):
    """convert all chebi to pubchem with
    Data Commons query and fill missing
    chembl with converted results inplace
    Args:
        df: pandas.Dataframe with chemble and chebi info
    Returs:
        None
    """
    pub_chem_list = df[df["chembl"].isna()]\
        ["pubchem.compound"].unique()[1:].astype(int).astype(str)
    result = query_chembl_from_pubchem(pub_chem_list)
    for res in result:
        df.loc[df["pubchem.compound"] == res["?pubChem"], "chembl"]\
                         = res["?chembl"].split("/")[1]
    print("DONE converting pubchem to chembl with data common query")


def fill_chembl_from_kegg(df):
    """convert all chebi to kegg with
   Data Commons queryand fill missing
   chembl with converted results inplace
   Args:
       df: pandas.Dataframe with chemble and chebi info
   Returs:
       None
   """
    val_list = list(df[df["chembl"].isna()]\
               ["kegg.compound"].unique())
    if np.nan in val_list:
        val_list.remove(np.nan)
    kegg_list = np.array(val_list)
    result = query_chembl_from_kegg(kegg_list)
    for res in result:
        df.loc[df["kegg.compound"] == res["?kegg"], "chembl"] \
                       = res["?chembl"].split("/")[1]
    print("DONE converting kegg to chembl with data common query")


def fill_chembl_from_chebi(df):
    """convert all chebi to chembl with
    Data Commons query and fill missing
    chembl with converted results inplace
    Args:
        df: pandas.Dataframe with chemble and chebi info
    Returs:
        None
    """
    val_list = list(df[df["chembl"].isna()]["chebi"].unique())
    if np.nan in val_list:
        val_list.remove(np.nan)
    chebi_list = np.array(val_list)
    result = query_chembl_from_chebi(chebi_list)
    for res in result:
        df.loc[df["chebi"] == res["?chebi"], "chembl"]\
                         = res["?chembl"].split("/")[1]
    print("DONE converting chebi to chembl with data common query")


def bioservice_kegg_to_chembl(df, uni):
    """convert exisitn kegg id to chembl id
    and fill in (in-place) missing chemble with bioservices
    Args:
        df: pd.DataFrame with kegg and chembl columns
        uni: bioservice mapping object
    Returns:
        None
    """
    from_, to_ = "kegg.compound", "chembl"
    from_list = list(df[df[to_].isna()][from_].unique())
    if np.nan in from_list:
        from_list.remove(np.nan)
    mapping = uni.get_mapping("kegg_ligand", "chembl")
    for val in from_list:
        try:
            df.loc[df[from_] == val, "chembl"] = mapping[val]
        except KeyError:
            pass
    print("DONE converting kegg to chembl with boservices")


def bioservice_chebi_to_chembl(df, uni):
    """convert exisitn chebi id to chembl id
    and fill in (in-place) missing chemble with bioservices
    Args:
        df: pd.DataFrame with chebi and chembl columns
        uni: bioservice mapping object
    Returns:
        None
    """
    from_, to_ = "chebi", "chembl"
    from_list = list(df[df[to_].isna()][from_].unique())
    #Remove nan
    for i in from_list:
        if not isinstance(i, str):
            from_list.remove(i)

    mapping = uni.get_mapping("chebi", "chembl")
    for val in from_list:
        try:
            df.loc[df[from_] == val, "chembl"] = mapping[val.split(":")[1]]
        except KeyError:
            pass
    print("DONE converting chebi to chembl with bioservices")


def query_chembl_from_chebi(chebi_dcids):
    """query chembl id from chebi id
    with data commons
    Args:
        chebi_dcids: list of chebi dcids
    Returns:
        data common query result with chembl\
        and chebi dcid mapping
    """
    query_str = """
    SELECT DISTINCT ?chembl ?chebi
    WHERE{{
    ?chembl typeOf ChemicalCompound .
    ?chembl chebiID ?chebi .
    ?chembl chebiID {0} .
    }}
    """.format(chebi_dcids)
    result = dc.query(query_str)
    return result


def query_chembl_from_pubchem(pubchem_dcids):
    """query chembl id from pubchem id
    with data commons
    Args:
        pubchem_dcids: list of pubchem dcids
    Returns:
        data common query result with chembl\
        and pubchem dcid mapping
    """
    query_str = """
    SELECT DISTINCT ?chembl ?pubChem
    WHERE{{
    ?chembl typeOf ChemicalCompound .
    ?chembl pubChemCompoundID ?pubChem .
    ?chembl pubChemCompoundID {0} .
    }}
    """.format(pubchem_dcids)
    result = dc.query(query_str)
    return result


def query_chembl_from_kegg(kegg_dcids):
    """query chembl id from hmdb id
    with data commons
    Args:
        kegg_dcids: list of kegg dcids
    Returns:
        data common query result with chembl\
        and kegg dcid mapping
    """
    query_str = """
    SELECT DISTINCT ?chembl ?kegg
    WHERE{{
    ?chembl typeOf ChemicalCompound .
    ?chembl keggCompoundID ?kegg .
    ?chembl keggCompoundID {0} .
    }}
    """.format(kegg_dcids)
    result = dc.query(query_str)
    return result


def query_chembl_from_hmdb(hmdb_dcids):
    """query chembl id from hmdb id
    with data commons
    Args:
        hmdb_dcids: list of hmdb dcids
    Returns:
        data common query result with chembl\
        and hmdb dcid mapping
    """
    query_str = """
    SELECT DISTINCT ?chembl ?hmdb
    WHERE{{
    ?chembl typeOf ChemicalCompound .
    ?chembl humanMetabolomeDatabaseID ?hmdb .
    ?chembl humanMetabolomeDatabaseID {0} .
    }}
    """.format(hmdb_dcids)
    result = dc.query(query_str)
    return result


def make_csv(df, name):
    """create csv file at the
    current directory path
    Args:
        df: pandas dataframe to be created
        name: name of csv file (e.g result.csv)
    Returns:
        None
    """
    output_path = os.path.join(os.getcwd(), name)
    df.to_csv(output_path, index=None)
    return None


def convert_float_to_int(df, column):
    """convert type of pd.Datafarme column
    from float to int, ignore missing values
    Args:
        df: pandas.DataFrame
        column: column name
    Returns:
        None
    """
    df[column] = df[column].fillna(-1)
    df[column] = df[column].astype(int)
    df[column] = df[column].astype(str)
    df[column] = df[column].replace('-1', np.nan)
    return None

def format_product_role_data(product_tsv, df_metabolic_cellular_compartment):
    """Format product role data
    Args:
        product_tsv: productRoles.tsv file path
        df_metabolic_cellular_compartment:
    Returns:
        df_product_roles: formattted product role dataframe
    """
    ### generate productRoles.csv
    df_product_roles = pd.read_csv(product_tsv, sep='\t')
    # Remove "M_" in speciesID/humanGEMID of metabolites
    df_product_roles["speciesID"] = df_product_roles["speciesID"].str[2:]
    # Remove "R_" in speciesID/humanGEMID of reactions
    df_product_roles["reactionID"] = df_product_roles["reactionID"].str[2:]
    # merge productRoles and metabolicCellularCompartment for dcid mapping
    df_product_roles = df_product_roles.merge(\
                df_metabolic_cellular_compartment,\
                left_on="speciesID", right_on="id")\
                [["reactionID", "metabolic_compartment_dcid"]]
    # modify reaction id to reaction dcid format
    df_product_roles["reactionID"] = "bio/" +\
                  df_product_roles["reactionID"].astype("str")
    return df_product_roles

def format_reactant_role_data(reactant_tsv, df_metabolic_cellular_compartment):
    """Format reactant role data
    Args:
        reactant_tsv: reactantRoles.tsv file path
        df_metabolic_cellular_compartment:
    Returns:
        df_reactant_roles: formattted reactant role dataframe
    """
    ### generate reactantRoles.csv
    df_reactant_roles = pd.read_csv(reactant_tsv, sep='\t')
    # Remove "M_" in speciesID/humanGEMID of metabolites
    df_reactant_roles["speciesID"] = df_reactant_roles["speciesID"].str[2:]
    # Remove "R_" in speciesID/humanGEMID of reactions
    df_reactant_roles["reactionID"] = df_reactant_roles["reactionID"].str[2:]
    # merge reactantRoles and metabolicCellularCompartment for dcid mapping
    df_reactant_roles = df_reactant_roles.merge(\
        df_metabolic_cellular_compartment, left_on="speciesID", right_on="id")\
            [["reactionID", "metabolic_compartment_dcid"]]
    # modify reaction id to reaction dcid format
    df_reactant_roles["reactionID"] = "bio/" +  \
        df_reactant_roles["reactionID"].astype(str)
    return df_reactant_roles

def generate_metabolic_cellular_compartment(df_metabolites):
    """Generate metabolicCellularCompartment.csv
    Args:
        df_metabolites: human1 metabolite dataframe
    Returns:
        df_metabolic_cellular_compartment
    """
    df_metabolic_cellular_compartment = df_metabolites\
                [["id", "compartment", "metabolite_dcid"]].copy()
    df_metabolic_cellular_compartment["metabolic_compartment_dcid"] = "bio/" +\
                 df_metabolic_cellular_compartment["id"]

    return df_metabolic_cellular_compartment

def mapping_across_columns(df_metabolites):
    """Using bioservice and google datacommons to map
    different IDs in df_metabolites columns
    Args:
        df_metabolites: metabolites dataframe
    Returns
        format data in place
    """
    # init mapping tool (bioservices)
    uni = UniChem()
    # Convert Chebi to chembl with bioservices
    # and fill in chembl column
    bioservice_chebi_to_chembl(df_metabolites, uni)
    # Convert kegg to chembl with bioservices
    # and fill in chembl column
    bioservice_kegg_to_chembl(df_metabolites, uni)
    #fill chemble from other columns with data commons query
    fill_chembl_from_chebi(df_metabolites)
    fill_chembl_from_kegg(df_metabolites)
    # Pubchem Compound float -> int
    convert_float_to_int(df_metabolites, "pubchem.compound")
    fill_chembl_from_pubchem(df_metabolites)
    fill_chembl_from_hmdb(df_metabolites)

def format_metabolite_and_metabolite_relationships(metabolite_tsv, \
                        human1_hmdb_map, reactant_tsv, product_tsv):
    """Format metabolites.tsv, reactantRoles.tsv, productRoes.tsv files
    Args:
        metabolite_tsv: metabolite file path
        human1_hmdb_map: human1_hmdb file path
        reactant_tsv: reactantRole file path
        product_tsv: productRole file path
    Returns:
        Write formatted csv files
    """
    # read metabolite file to dataframe
    df_metabolites = pd.read_csv(metabolite_tsv, sep="\t")
    df_map = pd.read_csv(human1_hmdb_map)
    # map humangem_id to hmdb_id
    humangem_hmdb_dict = df_map.set_index("id").to_dict()['master_hmdb']
    df_metabolites["hmdb"] = df_metabolites["id"].map(humangem_hmdb_dict)
    # Remove values in chebi column that has wrong format
    # does not start with "CHEBI"
    condition = df_metabolites['chebi'].str.\
                findall("CHE").explode() == np.array("CHE")
    df_metabolites["chebi"] =\
                 np.where(condition, df_metabolites["chebi"], np.nan)
    mapping_across_columns(df_metabolites)
    df_metabolites = format_df_metatbolites(df_metabolites)
    df_metabolic_cellular_compartment = \
        generate_metabolic_cellular_compartment(df_metabolites)
    df_reactant_roles = format_reactant_role_data(reactant_tsv, \
        df_metabolic_cellular_compartment)
    df_product_roles = format_product_role_data(product_tsv, \
        df_metabolic_cellular_compartment)
    make_csv(df_metabolites, "metabolites.csv")
    make_csv(df_metabolic_cellular_compartment,\
         "metabolicCellularCompartment.csv")
    make_csv(df_reactant_roles, "reactantRoles.csv")
    make_csv(df_product_roles, "productRoles.csv")

def main():
    """Main function"""
    # read in 3 data files as the second, third, and fourth arguments
    metabolite_tsv, reactant_tsv, product_tsv, human1_hmdb_map =\
                 sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    format_metabolite_and_metabolite_relationships(\
        metabolite_tsv, human1_hmdb_map, reactant_tsv, product_tsv)

if __name__ == '__main__':
    main()
