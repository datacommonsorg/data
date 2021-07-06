"""
This script formats reactions.tsv to
combine with tMCF files for import to data commons
"""
import sys
import os
import numpy as np
import pandas as pd


def main():

    # information of this dictionary is from the original
    # HUMAN-GEM xml file (read Download URL section)
    kinetic_dict = {"FB2N0": 0, "FB1N1000": -1000, "FB3N1000": 1000}
    # read in 1 data file as the second argument
    file_input = sys.argv[1]
    # read in dataframe
    df_reactions = pd.read_csv(file_input, sep='\t')
    # map lowerFluxBound and upperFluxBound to dictionary
    df_reactions["lowerFluxBound"] = \
        df_reactions["lowerFluxBound"].map(kinetic_dict)
    df_reactions["upperFluxBound"] = \
        df_reactions["upperFluxBound"].map(kinetic_dict)
    # modify reaction ID to humanGEMID format
    df_reactions["id"] = df_reactions["id"].str[2:]
    df_reactions["dcid"] = "bio/" + df_reactions["id"].astype(str)
    # create a fluxRange columns from lowerFluxBound and upperFluxBound
    df_reactions["fluxRange"] = "[" +\
         df_reactions["lowerFluxBound"].astype(str) + \
        " " + df_reactions["upperFluxBound"].astype(str) + " mmol/gDW" + "]"
    # rop lowerFluxBound and upperFluxBound columns
    df_reactions = df_reactions.drop(columns = \
        ["lowerFluxBound", "upperFluxBound"], axis = 1)
    # generate output file path at current directory
    output_path = os.path.join(os.getcwd(), "reactions.csv")
    df_reactions.to_csv(output_path, index=None)


if __name__ == '__main__':
    main()
