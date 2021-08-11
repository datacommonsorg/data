"""
This script formats reactions.tsv to
combine with tMCF files for import to data commons
"""
import sys
import os
import pandas as pd

# information of this dictionary is from the original
# HUMAN-GEM xml file (read Download URL section)
KINETIC_DICT = {"FB2N0": 0, "FB1N1000": -1000, "FB3N1000": 1000}


def format_reactions_data(reactions_tsv):
    """Format reactions.tsv file
    Args:
        reactions_tsv: reactions.tsv file path
    Returns:
        Write formatted csv file: reactions.csv
    """
    df_reactions = pd.read_csv(reactions_tsv, sep='\t')
    # map lowerFluxBound and upperFluxBound to dictionary
    df_reactions["lowerFluxBound"] = \
        df_reactions["lowerFluxBound"].map(KINETIC_DICT)
    df_reactions["upperFluxBound"] = \
        df_reactions["upperFluxBound"].map(KINETIC_DICT)
    # modify reaction ID to humanGEMID format
    df_reactions["id"] = df_reactions["id"].str[2:]
    df_reactions["dcid"] = "bio/" + df_reactions["id"].astype(str)
    # create a fluxRange columns from lowerFluxBound and upperFluxBound
    df_reactions["fluxRange"] = "[" +\
         df_reactions["lowerFluxBound"].astype(str) + \
        " " + df_reactions["upperFluxBound"].astype(str) + " mmol/gDW" + "]"
    # rop lowerFluxBound and upperFluxBound columns
    df_reactions = df_reactions.drop(columns=\
        ["lowerFluxBound", "upperFluxBound"], axis=1)
    # generate output file path at current directory
    output_path = os.path.join(os.getcwd(), "reactions.csv")
    df_reactions.to_csv(output_path, index=None)


def main():

    # read in 1 data file as the second argument
    reactions_tsv = sys.argv[1]
    # format reactions.tsv
    format_reactions_data(reactions_tsv)

if __name__ == '__main__':
    main()
