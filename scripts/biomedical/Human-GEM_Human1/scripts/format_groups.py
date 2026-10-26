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
Name: format_groups.py
Description: This script formats group.tsv and groupMembrrships.tsv files to
combine with tMCF files for import to data commons
@file_input: groups.tsv and groupMemberhsips.tsv in human1 dataset
@file_output: formatted groups.csv and groupMemberhsips.csv
'''

import sys
import os
import pandas as pd

# Define dictionary to map values in "kind" column, value is mapped to
# a category of HierachyTypeEnum class
HIERACHY_DICT = {"partonomy": "dcs:HierachyTypePartonomy"}

def format_group_data(groups_tsv):
    """Format groups.tsv file
    Args:
        groups.tsv: groups.tsv file path
    Returns:
        Write formatted csv file: groups.csv
    """
    df_groups = pd.read_csv(groups_tsv, sep='\t')
    # map values in "kind" columns to hierachy_dict
    df_groups["kind"] = df_groups["kind"].map(HIERACHY_DICT)
    # use "name" as dcid, format name:
    # empty space to underscore, lower string, remove comma
    df_groups["dcid"] = "bio/" + df_groups["name"].str.replace(" ", "_")
    df_groups["dcid"] = df_groups["dcid"].str.lower()
    df_groups["dcid"] = df_groups["dcid"].str.replace(",", "_")
    # add quotation mark around SBO term
    df_groups["sboTerm"] = '"' + df_groups["sboTerm"] + '"'
    # generate output file path at current directory
    output_path = os.path.join(os.getcwd(), "groups.csv")
    # create formatted csv
    df_groups.to_csv(output_path, index=None)

    return df_groups

def format_group_membership_data(group_memberships_tsv, df_groups):
    """Format groupMemberships.tsv file
    Args:
        group_memberships_tsv: groupMemberships.tsv file path
        df_groups: formatted groups.csv dataframe
                result of format_group_data()
    Returns:
        Write formatted csv file: groupMemberships.csv
    """
    ### generate groupMemberships.csv
    df_group_memberships = pd.read_csv(group_memberships_tsv, sep='\t')
    # merge groupMemberships datafram with groups dataframe
    # for groups/subsystems dcid mapping
    df_group_memberships = df_group_memberships.merge(df_groups, \
        left_on="groupID", right_on="id")[["dcid", "reactionID"]]
    # modify reaction ID to reaction dcid format
    df_group_memberships["reactionID"] = "bio/" +\
         df_group_memberships["reactionID"].str[2:]
    # generate output file path at current directory
    output_path = os.path.join(os.getcwd(), "groupMemberships.csv")
    # create formatted csv
    df_group_memberships.to_csv(output_path, index=None)

def format_group_and_group_membership(groups_tsv, group_memberships_tsv):
    """Format groups.tsv and groupMemberships.tsv file
    Args:
        groups_tsv: groups.tsv file path
        group_memberships_tsv: groupMembersgips.tsv file path
    Returns:
        Write formatted csv file: groups.csv and groupMemberships.csv
    """
    # format groups.tsv
    df_groups = format_group_data(groups_tsv)
    # format groupMemberships.tsv
    format_group_membership_data(group_memberships_tsv, df_groups)

def main():

    # read in 2 data files as the second and third arguments
    groups_tsv, group_memberships_tsv = sys.argv[1], sys.argv[2]
    format_group_and_group_membership(groups_tsv, group_memberships_tsv)


if __name__ == '__main__':
    main()
