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
"""
This script generate a csv with mapping between
reactions and their reactant. product compartments
"""

import pandas as pd
import sys


def metabolite_to_compartment(df, metabolites, compartment_column):
    """convert a list of metabolites to
    a list of their corresponding compartments
    Args:
        df: dataframe contain metabolite id and compartment columns
        metabolites: list of metabolite id
        compartment_column: compartment column name
    Returns:
        compartment_list: list of corresponding comparments
    """
    compartment_list = list(df[df["id"].\
        isin(metabolites)][compartment_column].unique())
    return compartment_list


def main():
    metabolite_tsv, reactant_roles, product_roles, reaction_tsv =\
                    sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    ### Generate metabolites.csv# read csv file
    df_metabolites = pd.read_csv(metabolite_tsv, sep="\t")
    df_reactant_roles = pd.read_csv(reactant_roles, sep="\t")
    df_product_roles = pd.read_csv(product_roles, sep="\t")
    df_reactions = pd.read_csv(reaction_tsv, sep="\t")

    # Generate dictionary between reaction id and metabolite id
    reactant_dict = df_reactant_roles.groupby("reactionID")['speciesID']\
                                                    .apply(list).to_dict()
    product_dict = df_product_roles.groupby("reactionID")['speciesID']\
                                                    .apply(list).to_dict()
    # Map reactions to list of reactants and products
    reactant_metabolites_list = df_reactions["id"].map(reactant_dict)
    product_metabolites_list = df_reactions["id"].map(product_dict)
    product_compartments, reactant_compartments = [], []
    # Convert product metabolites to compartments
    for i in product_metabolites_list:
        if isinstance(i, list):
            compartments = metabolite_to_compartment(df_metabolites,\
                                                     i, "compartment")
            product_compartments.append(compartments)
        else:
            product_compartments.append([])
    # Convert reactant metabolites to compartments
    for i in reactant_metabolites_list:
        if isinstance(i, list):
            compartments = metabolite_to_compartment(df_metabolites,\
                                                      i, "compartment")
            reactant_compartments.append(compartments)
        else:
            reactant_compartments.append([])
    # Add compartment columns for reactants and products
    df_reactions["reactant_compartment"] = reactant_compartments
    df_reactions["product_compartment"] = product_compartments
    # Change list to string
    df_reactions['reactant_compartment'] = df_reactions['reactant_compartment']\
                                            .apply(lambda x: ','.join(map(str, x)))
    df_reactions['product_compartment'] = df_reactions['product_compartment']\
                                            .apply(lambda x: ','.join(map(str, x)))
    # Output csv
    df_reactions.to_csv("human1_reaction_compartment.csv", index=False)


if __name__ == "__main__":
    main()
