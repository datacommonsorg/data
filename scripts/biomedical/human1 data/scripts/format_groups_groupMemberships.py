def main():
    import sys
    import os
    import numpy as np
    import pandas as pd


    hierachy_dict = {
        "partonomy":"dcs:HierachyTypePartonomy"
    }
    
    groups_tsv, groupMemberships_tsv = sys.argv[1], sys.argv[2]
    
    df_groups = pd.read_csv(groups_tsv, sep='\t')
    df_groups["kind"] = df_groups["kind"].map(hierachy_dict)
    df_groups["dcid"] = "bio/" + df_groups["name"].str.replace(" ", "_")
    df_groups["dcid"] = df_groups["dcid"].str.lower()
    df_groups["dcid"] = df_groups["dcid"].str.replace(",","")
    df_groups["sboTerm"] = '"' + df_groups["sboTerm"] + '"'

    output_path = os.path.join(os.getcwd(), "groups.csv")
    df_groups.to_csv(output_path, index = None)

    ### generate groupMemberships.csv
    df_groupMemberships = pd.read_csv(groupMemberships_tsv, sep='\t')
    df_groupMemberships = df_groupMemberships.merge(df_groups, left_on = "groupID", right_on = "id")[["dcid", "reactionID"]]
    df_groupMemberships["reactionID"] = "bio/" + df_groupMemberships["reactionID"].str[2:]
    output_path = os.path.join(os.getcwd(), "groupMemberships.csv")
    df_groupMemberships.to_csv(output_path, index = None)

if __name__ == '__main__':
    main()
