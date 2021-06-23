def main():
    import sys
    import os
    import numpy as np
    import pandas as pd
    
    metabolite_tsv, reactant_tsv, product_tsv = sys.argv[1],sys.argv[2],sys.argv[3]

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

    df_metabolites = pd.read_csv(metabolite_tsv, sep = "\t")
    # Remove metabolites with no chemicalFormula
    df_metabolites = df_metabolites[~pd.isna(df_metabolites["chemicalFormula"])]
    # modify id to humanGEMID format
    df_metabolites["id"] = df_metabolites["id"].str[2:]
    # Create new column for dcid
    df_metabolites["dcid"] = df_metabolites["chembl"]
    # use chemcialFormula as dcid if chemblID is not available
    df_metabolites["dcid"] = df_metabolites["dcid"].fillna(df_metabolites["chemicalFormula"])
    # use chemcialFormula as dcid if chemblID is not available
    df_metabolites["dcid"] = df_metabolites["dcid"].fillna(df_metabolites["id"])
    # format dcid -> bio/
    df_metabolites["dcid"] = "bio" + "/" + df_metabolites["dcid"].str.replace(":","")
    # Format chemblID, remove ":"
    df_metabolites["chembl"] = df_metabolites["chembl"].str.replace(":","")
    #convert chebiID and chemicalName to string with quotation
    df_metabolites['chebi'] = np.where(pd.isnull(df_metabolites['chebi']),df_metabolites['chebi']                                    ,'"' + df_metabolites['chebi'].astype(str) + '"')
    df_metabolites['name'] = np.where(pd.isnull(df_metabolites['name']),df_metabolites['name']                                    ,'"' + df_metabolites['name'].astype(str) + '"')
    # Pubchem Compound float -> int 
    df_metabolites["pubchem.compound"] = df_metabolites["pubchem.compound"].fillna(-1)
    df_metabolites["pubchem.compound"] = df_metabolites["pubchem.compound"].astype(int)
    df_metabolites["pubchem.compound"] = df_metabolites["pubchem.compound"].astype(str)
    df_metabolites["pubchem.compound"] = df_metabolites["pubchem.compound"].replace('-1', np.nan)
    # modify compartment to Enum type
    df_metabolites["compartment"] = df_metabolites["compartment"].map(compartment_dict)

    output_path = os.path.join(os.getcwd(), "metabolites.csv")
    df_metabolites.to_csv(output_path, index = None)

    ### generate productRoles.csv
    df_productRoles = pd.read_csv(product_tsv, sep='\t') # add to Metabolite property
    df_productRoles["speciesID"] = df_productRoles["speciesID"].str[2:]
    df_productRoles["reactionID"] = df_productRoles["reactionID"].str[2:]
    df_productRoles = df_productRoles.merge(df_metabolites, left_on = "speciesID", right_on="id")[["reactionID", "dcid"]]
    df_productRoles["reactionID"] = "bio/" +  df_productRoles["reactionID"].astype("str")

    output_path = os.path.join(os.getcwd(), "productRoles.csv")
    df_productRoles.to_csv(output_path, index = None)

    ### generate reactantRoles.csv
    df_reactantRoles = pd.read_csv(reactant_tsv, sep='\t')
    df_reactantRoles["speciesID"] = df_reactantRoles["speciesID"].str[2:]
    df_reactantRoles["reactionID"] = df_reactantRoles["reactionID"].str[2:]
    df_reactantRoles = df_reactantRoles.merge(df_metabolites, left_on = "speciesID", right_on="id")[["reactionID", "dcid"]]
    df_reactantRoles["reactionID"] = "bio/" +  df_reactantRoles["reactionID"].astype(str)

    output_path = os.path.join(os.getcwd(), "reactantRoles.csv")
    df_reactantRoles.to_csv(output_path, index = None)

if __name__ == '__main__':
    main()


