"""
This script formats group.tsv and groupMembrships.tsv files to
combine with tMCF files for import to data commons
"""
import sys
import os
import numpy as np
import pandas as pd
def main():
    # Define dictionary to map values in "kind" column, value is mapped to
    # a category of HierachyTypeEnum class
    hierachy_dict = {
        "partonomy":"dcs:HierachyTypePartonomy"
    }
    # read in 2 data files as the second and third arguments
    groups_tsv, group_memberships_tsv = sys.argv[1], sys.argv[2]

    ### generate groups.csv
    df_groups = pd.read_csv(groups_tsv, sep='\t')
    # map values in "kind" columns to hierachy_dict
    df_groups["kind"] = df_groups["kind"].map(hierachy_dict)
    # use "name" as dcid, format name:
    # empty space to underscore, lower string, remove comma
    df_groups["dcid"] = "bio/" + df_groups["name"].str.replace(" ", "_")
    df_groups["dcid"] = df_groups["dcid"].str.lower()
    df_groups["dcid"] = df_groups["dcid"].str.replace(",","_")
    # add quotation mark around SBO term
    df_groups["sboTerm"] = '"' + df_groups["sboTerm"] + '"'
    # generate output file path at current directory
    output_path = os.path.join(os.getcwd(), "groups.csv")
    # create formatted csv
    df_groups.to_csv(output_path, index = None)

    ### generate groupMemberships.csv
    df_group_memberships = pd.read_csv(group_memberships_tsv, sep='\t')
    # merge groupMemberships datafram with groups dataframe
    # for groups/subsystems dcid mapping
    df_group_memberships = df_group_memberships.merge(df_groups, \
        left_on = "groupID", right_on = "id")[["dcid", "reactionID"]]
    # modify reaction ID to reaction dcid format
    df_group_memberships["reactionID"] = "bio/" +\
         df_group_memberships["reactionID"].str[2:]
    # generate output file path at current directory
    output_path = os.path.join(os.getcwd(), "groupMemberships.csv")
    # create formatted csv
    df_group_memberships.to_csv(output_path, index = None)

if __name__ == '__main__':
    main()
