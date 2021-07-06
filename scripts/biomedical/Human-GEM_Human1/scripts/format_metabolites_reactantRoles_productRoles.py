"""
This script formats metabolites.tsv, reactantRoles.tsv
and productRoles.tsv files to
combine with tMCF files for import to data commons
"""
import sys
import os
import numpy as np
import pandas as pd
import datacommons as dc
import bioservices
from bioservices import *


def get_unique_values(df, column):
    val_list = list(df[df["chembl"].isna()][column].unique())
    if np.nan in val_list:
        val_list.remove(np.nan)
    val_list = np.array(val_list)
    return val_list

def main():
    # dictionary to map values in "compartment" 
    # column to CellularCompartmentEnum values
    compartment_dict = {
        "c":"dcs:CellularCompartmentCytosol",
        "s": "dcs:CellularCompartmentExtracellular",
        "l": "dcs:CellularCompartmentLysosome",
        "r": "dcs:CellularCompartmentEndoplasmicReticulum",
        "m": "dcs:CellularCompartmentMitochondria",
        "p": "dcs:CellularCompartmentPeroxisome",
        "g": "dcs:CellularCompartmentGolgiApparatus",
        "n": "dcs:CellularCompartmentNucleus",
        "c_i": "dcs:CellularCompartmentInnerMitochondria"
    }

    # read in 3 data files as the second, third, and fourth arguments
    metabolite_tsv, reactant_tsv, product_tsv = \
        sys.argv[1],sys.argv[2],sys.argv[3]
    ### Generate metabolites.csv
    # read csv file
    df_metabolites = pd.read_csv(metabolite_tsv, sep = "\t")

    uni = UniChem()  # init mapping tool (bioservices)
    # Convert Chebi to chembl with bioservices
    # and fill in chmble column
    from_ , to_ = "chebi", "chembl"
    from_list = list(df_metabolites[df_metabolites[to_].isna()][from_].unique())
    if np.nan in from_list:
        from_list.remove(np.nan) 
    mapping = uni.get_mapping("chebi", "chembl")
    for val in from_list:
        try:
            df_metabolites.loc[df_metabolites[from_] == val, "chembl"] \
                =  mapping[val.split(":")[1]]
        except:
            pass
    print("DONE converting chebi to chembl with bioservices")

    # Convert kegg to chembl with bioservices and fill in chembl column
    from_ , to_ = "kegg.compound", "chembl"
    from_list = list(df_metabolites[df_metabolites[to_].isna()][from_].unique())
    if np.nan in from_list :
        from_list.remove(np.nan) 
    mapping = uni.get_mapping("kegg_ligand", "chembl")
    for val in from_list:
        try:
            df_metabolites.loc[df_metabolites[from_] \
                == val, "chembl"] =  mapping[val]
        except:
            pass

    print("DONE converting kegg to chembl with boservices")

    chebi_list = get_unique_values(df_metabolites, "chebi")
    query_str = """
    SELECT DISTINCT ?chembl ?chebi
    WHERE{{
    ?chembl typeOf ChemicalCompound .
    ?chembl chebiID ?chebi .
    ?chembl chebiID {0} .
    }}
    """.format(chebi_list)
    result = dc.query(query_str)
    for res in result:
        df_metabolites.loc[df_metabolites["chebi"] == res["?chebi"], "chembl"] \
            =  res["?chembl"].split("/")[1]
    print("DONE converting chebi to chembl with data common query")

    kegg_list = get_unique_values(df_metabolites,"kegg.compound")
    query_str = """
    SELECT DISTINCT ?chembl ?kegg
    WHERE{{
    ?chembl typeOf ChemicalCompound .
    ?chembl keggCompoundID ?kegg .
    ?chembl keggCompoundID {0} .
    }}
    """.format(kegg_list)
    result = dc.query(query_str)
    for res in result:
        df_metabolites.loc\
            [df_metabolites["kegg.compound"] == res["?kegg"], "chembl"] \
            =  res["?chembl"].split("/")[1]
    print("DONE converting kegg to chembl with data common query")
          
    pub_chem_list = df_metabolites[df_metabolites["chembl"].isna()]\
        ["pubchem.compound"].unique()[1:].astype(int).astype(str)
    # Pubchem Compound float -> int
    df_metabolites["pubchem.compound"] = \
        df_metabolites["pubchem.compound"].fillna(-1)
    df_metabolites["pubchem.compound"] = \
        df_metabolites["pubchem.compound"].astype(int)
    df_metabolites["pubchem.compound"] = \
        df_metabolites["pubchem.compound"].astype(str)
    df_metabolites["pubchem.compound"] = \
        df_metabolites["pubchem.compound"].replace('-1', np.nan)

    query_str = """
    SELECT DISTINCT ?chembl ?pubChem
    WHERE{{
    ?chembl typeOf ChemicalCompound .
    ?chembl pubChemCompoundID ?pubChem .
    ?chembl pubChemCompoundID {0} .
    }}
    """.format(pub_chem_list)
    result = dc.query(query_str)    
    for res in result:
        df_metabolites.loc[df_metabolites["pubchem.compound"] \
            == res["?pubChem"], "chembl"]\
             =  res["?chembl"].split("/")[1]
    print("DONE converting pubchem to chembl with data common query")

    human_met_list = df_metabolites\
        [df_metabolites["chembl"].isna()]["hmdb"].unique()[1:]
    query_str = """
    SELECT DISTINCT ?chembl ?hmdb
    WHERE{{
    ?chembl typeOf ChemicalCompound .
    ?chembl humanMetabolomeDatabaseID ?hmdb .
    ?chembl humanMetabolomeDatabaseID {0} .
    }}
    """.format(human_met_list)
    result = dc.query(query_str)
    for res in result:
        df_metabolites.loc[df_metabolites["hmdb"] == res["?hmdb"], "chembl"] \
            =  res["?chembl"].split("/")[1]
    print("DONE converting hmdb to chembl with data common query")

    # Remove metabolites with no chemicalFormula
    df_metabolites = df_metabolites[~pd.isna(df_metabolites["chemicalFormula"])]
    # modify id to humanGEMID format
    df_metabolites["id"] = df_metabolites["id"].str[2:]
    # Create new column for dcid
    df_metabolites["metabolite_dcid"] = df_metabolites["chembl"]
    # use metaNetX as dcid if chemblID is not available
    df_metabolites["metabolite_dcid"] = \
        df_metabolites["metabolite_dcid"].fillna(\
            df_metabolites["metanetx.chemical"])
    # use chemical name as dcid if metaNetX is not available
    df_metabolites["metabolite_dcid"] = \
        df_metabolites["metabolite_dcid"].fillna(df_metabolites["name"])
    # format dcid -> bio/
    df_metabolites["metabolite_dcid"] = "bio" + "/" + \
        df_metabolites["metabolite_dcid"].str.replace(":","")
    df_metabolites["metabolite_dcid"] =  \
        df_metabolites["metabolite_dcid"].str.replace(",","_")
    # Format chemblID, remove ":"
    df_metabolites["chembl"] = df_metabolites["chembl"].str.replace(":","")
    #convert chebiID and chemicalName to string with quotation
    df_metabolites['chebi'] = np.where(pd.isnull(df_metabolites['chebi']),\
        df_metabolites['chebi'],\
            '"' + df_metabolites['chebi'].astype(str) + '"')
    df_metabolites['name'] = np.where(pd.isnull(df_metabolites['name']),\
        df_metabolites['name'],\
            '"' + df_metabolites['name'].astype(str) + '"')
    # modify compartment to Enum type
    df_metabolites["compartment"] = \
        df_metabolites["compartment"].map(compartment_dict)
    # generate output file path at current directory
    output_path = os.path.join(os.getcwd(), "metabolites.csv")
    df_metabolites.to_csv(output_path, index = None)
    
    ### Generate metabolicCellularCompartment.csv
    df_metabolic_cellular_compartment = df_metabolites\
        [["id", "compartment","metabolite_dcid"]].copy()
    df_metabolic_cellular_compartment["metabolic_compartment_dcid"] = "bio/" +\
         df_metabolic_cellular_compartment["id"]
    # generate output file path at current directory
    output_path = os.path.join(os.getcwd(), "metabolicCellularCompartment.csv")
    df_metabolic_cellular_compartment.to_csv(output_path, index = None)

    ### generate productRoles.csv
    df_product_roles = pd.read_csv(product_tsv, sep='\t')
    # Remove "M_" in speciesID/humanGEMID of metabolites
    df_product_roles["speciesID"] = df_product_roles["speciesID"].str[2:]
    # Remove "R_" in speciesID/humanGEMID of reactions
    df_product_roles["reactionID"] = df_product_roles["reactionID"].str[2:]
    # merge productRoles and metabolicCellularCompartment for dcid mapping
    df_product_roles = df_product_roles.merge(\
        df_metabolic_cellular_compartment, \
        left_on = "speciesID", right_on="id")\
            [["reactionID", "metabolic_compartment_dcid"]]
    # modify reaction id to reaction dcid format
    df_product_roles["reactionID"] = "bio/" + \
         df_product_roles["reactionID"].astype("str")
    # generate output file path at current directory
    output_path = os.path.join(os.getcwd(), "productRoles.csv")
    df_product_roles.to_csv(output_path, index = None)

    ### generate reactantRoles.csv
    df_reactant_roles = pd.read_csv(reactant_tsv, sep='\t')
    # Remove "M_" in speciesID/humanGEMID of metabolites
    df_reactant_roles["speciesID"] = df_reactant_roles["speciesID"].str[2:]
    # Remove "R_" in speciesID/humanGEMID of reactions
    df_reactant_roles["reactionID"] = df_reactant_roles["reactionID"].str[2:]
    # merge reactantRoles and metabolicCellularCompartment for dcid mapping
    df_reactant_roles = df_reactant_roles.merge(\
        df_metabolic_cellular_compartment,left_on = "speciesID", right_on="id")\
             [["reactionID", "metabolic_compartment_dcid"]]
      # modify reaction id to reaction dcid format
    df_reactant_roles["reactionID"] = "bio/" + \
         df_reactant_roles["reactionID"].astype(str)
    # generate output file path at current directory
    output_path = os.path.join(os.getcwd(), "reactantRoles.csv")
    df_reactant_roles.to_csv(output_path, index = None)

if __name__ == '__main__':
    main()
