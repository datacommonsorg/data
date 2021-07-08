# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import math
import json
import csv
import pandas as pd
import numpy as np
import urllib.request


class LocalGovermentDirectoryStatesDataLoader:

    def __init__(self, lgd_csv, wikidata_csv, clean_csv):
        self.lgd_csv = lgd_csv
        self.wikidata_csv = wikidata_csv
        self.clean_csv = clean_csv
        self.lgd_df = None
        self.wikidata_df = None
        self.clean_df = None

    @staticmethod
    def format_title(s):
        # Converts to title case, except for the words like `of`, `and` etc
        name_list = s.split(' ')
        first_list = [name_list[0].capitalize()]
        for name in name_list[1:]:
            first_list.append(name if name in
                              ["of", "and"] else name.capitalize())
        return " ".join(first_list)

    @staticmethod
    def format_code(s):
        # Converts into two character length code
        # If the value is `0` then it makes it empty
        # If the length is single character then it prepends it
        # with `0` to make it two character length
        if len(s) == 1:
            if s == "0":
                return ""
            else:
                return str("0" + s)
        else:
            return str(s)

    @staticmethod
    def format_wikidataid(s):
        return s.replace("http://www.wikidata.org/entity/", "")

    def process(self):
        # Load the lgd states data and set the type of columns to str
        # if there are NA values then replace it with '' character
        self.lgd_df = pd.read_csv(self.lgd_csv, dtype=str)
        self.lgd_df.fillna('', inplace=True)
        # Drop title rows in the top and empty rows after 39.
        # The actual data is between 2nd and 40th row. So keep only them.
        self.lgd_df = self.lgd_df.iloc[1:38]
        # Take the the header row and set it has column header
        new_header = self.lgd_df.iloc[0]
        self.lgd_df = self.lgd_df[1:]
        self.lgd_df.columns = new_header
        # Convert name to lower case for matching
        self.lgd_df['State Name(In English)'] = self.lgd_df[
            'State Name(In English)'].str.lower()

        # Load wikidata and set the type of columns to str
        self.wikidata_df = pd.read_csv(self.wikidata_csv, dtype=str)
        # Convert name to lower case for matching
        self.wikidata_df['SLabel'] = self.wikidata_df['SLabel'].str.lower()

        # Match both sets based on name
        # It will be left join on lgd_df
        self.clean_df = pd.merge(self.lgd_df,
                                 self.wikidata_df,
                                 how="left",
                                 left_on=["State Name(In English)"],
                                 right_on=["SLabel"])

        # Create a new clean name from LGD data
        self.clean_df["Name"] = self.clean_df["State Name(In English)"].apply(
            LocalGovermentDirectoryStatesDataLoader.format_title)

        # Delete the columns that are not required
        del self.clean_df["SDescription"]
        del self.clean_df["SLabel"]
        del self.clean_df["S.No."]
        del self.clean_df["State Name(In English)"]
        del self.clean_df["State Name (In Local)"]
        del self.clean_df["State Version"]
        del self.clean_df["State or UT"]

        # Rename the columns as per our CSV requirements
        self.clean_df.columns = [
            "StateCode", "Census2001Code", "Census2011Code", "WikiDataId",
            "IsoCode", "Name"
        ]

        # Reformat the columns as per our CSV requirements
        self.clean_df["StateCode"] = self.clean_df["StateCode"].apply(
            LocalGovermentDirectoryStatesDataLoader.format_code)
        self.clean_df["Census2001Code"] = self.clean_df["Census2001Code"].apply(
            LocalGovermentDirectoryStatesDataLoader.format_code)
        self.clean_df["Census2011Code"] = self.clean_df["Census2011Code"].apply(
            LocalGovermentDirectoryStatesDataLoader.format_code)
        self.clean_df["WikiDataId"] = self.clean_df["WikiDataId"].apply(
            LocalGovermentDirectoryStatesDataLoader.format_wikidataid)

        # Update the ISO code for Dadra and Nagar Haveli and Daman and Diu
        self.clean_df.loc[self.clean_df["Name"] ==
                          "Dadra and Nagar Haveli and Daman and Diu",
                          "IsoCode"] = "IN-DH"

    def save(self):
        self.clean_df.to_csv(self.clean_csv, index=False, header=True)


def main():
    """Runs the program."""
    lgd_csv = os.path.join(os.path.dirname(__file__),
                           "./data/lgd_allStateofIndia_export.csv")
    wikidata_csv = os.path.join(
        os.path.dirname(__file__),
        "./data/wikidata_india_states_and_ut_export.csv")
    clean_csv = os.path.join(os.path.dirname(__file__),
                             "LocalGovernmentDirectory_States.csv")
    loader = LocalGovermentDirectoryStatesDataLoader(lgd_csv, wikidata_csv,
                                                     clean_csv)
    loader.process()
    loader.save()


if __name__ == '__main__':
    main()
