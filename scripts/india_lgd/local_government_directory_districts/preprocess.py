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

__author__ = ["Thejesh GN (i@thejeshgn.com)"]

import os
import csv
import difflib
import pandas as pd
from india.geo.states import IndiaStatesMapper
from india.formatters import CodeFormatter
# Some of the names don't match correctly while using
# difflib library. This is used to force the match manually.

MANUAL_OVERRIDE = {
    "delhi": {
        "south east": "south east delhi"
    },
    "assam": {
        "karbi anglong": "east karbi anglong"
    },
    "chhattisgarh": {
        "gaurella pendra marwahi": "gaurela-pendra-marwahi"
    },
    "gujarat": {
        "chhotaudepur": "chhota udaipur",
        "devbhumi dwarka": "devbhoomi dwarka"
    },
    "telangana": {
        "jagitial": "jagtial",
        "jangoan": "jangaon"
    },
}


class LocalGovermentDirectoryDistrictsDataLoader:

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
    def get_census2001_code(s):
        census2001_state_code = IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
            s["LGDStateName"], s["LGDDistrictName"])
        census2001_code = s["LGDCensus2001Code"]
        CodeFormatter.format_census2001_district_code(census2001_state_code,
                                                      census2001_code)

    def get_closest_district_label(self, lgddata_row):
        lgdStateName = lgddata_row["LGDStateName"]
        lgdDistrictName = lgddata_row["LGDDistrictName"]
        lgdCensus2011Code = lgddata_row["LGDCensus2011Code"]

        # Lets match them based on census code 2011 first
        if lgdCensus2011Code is not None and lgdCensus2011Code is not "":
            wikidata_df_row = self.wikidata_df.loc[
                self.wikidata_df["census2011Code"] == lgdCensus2011Code]
            if wikidata_df_row.empty:
                pass
            else:
                return wikidata_df_row.iloc[0]["districtLabel"]

        # Let's see if there are any manual overrides or corrections
        alternative_wikidata_districts = MANUAL_OVERRIDE[
            lgdStateName] if lgdStateName in MANUAL_OVERRIDE else {}
        if lgdDistrictName in alternative_wikidata_districts:
            return alternative_wikidata_districts[lgdDistrictName]

        # If nothing is found then let's try and match them by name
        # Only within the districts of that state
        wikidata_districts = self.wikidata_df.loc[(
            (self.wikidata_df["stateLabel"] == lgdStateName) &
            (self.wikidata_df["census2011Code"] == ""))]['districtLabel']
        match = difflib.get_close_matches(lgdDistrictName,
                                          wikidata_districts,
                                          n=1,
                                          cutoff=0.90)
        if match:
            return match[0]

        # Throw an exception if nothing is found
        raise Exception("No matching district was found.")

    @staticmethod
    def format_wikidataid(s):
        return s.replace("http://www.wikidata.org/entity/", "")

    def _load_and_format_lgd(self):
        # Load the lgd districts data and set the type of columns to str
        # if there are NA values then replace it with '' character
        self.lgd_df = pd.read_csv(self.lgd_csv, dtype=str)
        self.lgd_df.fillna('', inplace=True)
        # Drop title rows in the top and empty rows after 740.
        # The actual data is between 2nd and 740th row. So keep only them.
        self.lgd_df = self.lgd_df.iloc[1:739]
        # Take the the header row and set it as column header
        self.lgd_df = self.lgd_df[1:]
        self.lgd_df.columns = [
            "LGDDistrictCode", "LGDDistrictName", "LGDStateCode",
            "LGDStateName", "LGDCensus2001Code", "LGDCensus2011Code"
        ]

        # Convert name to lower case for matching
        self.lgd_df['LGDDistrictName'] = self.lgd_df[
            'LGDDistrictName'].str.lower()
        self.lgd_df['LGDStateName'] = self.lgd_df['LGDStateName'].str.lower()
        self.lgd_df['LGDStateName'] = self.lgd_df['LGDStateName'].str.replace(
            "the ", "")

        # Format state code, district code and census code
        self.lgd_df['LGDDistrictCode'] = self.lgd_df['LGDDistrictCode'].apply(
            CodeFormatter.format_lgd_district_code)
        self.lgd_df['LGDStateCode'] = self.lgd_df['LGDStateCode'].apply(
            CodeFormatter.format_lgd_state_code)
        self.lgd_df['LGDCensus2011Code'] = self.lgd_df[
            'LGDCensus2011Code'].apply(CodeFormatter.format_census2011_code)

        self.lgd_df['LGDCensus2001Code'] = self.lgd_df.apply(
            lambda row: LocalGovermentDirectoryDistrictsDataLoader.
            get_census2001_code(row),
            axis=1)

    def _load_and_format_wikidata(self):
        self.wikidata_df = pd.read_csv(self.wikidata_csv, dtype=str)
        # Note: Currently malerkotla is not mapped as district in wikidata
        # Hence I am adding it manually, here

        self.wikidata_df.loc[len(self.wikidata_df.index)] = [
            "http://www.wikidata.org/entity/Q1470987", "malerkotla",
            "malerkotla"
            "http://www.wikidata.org/entity/Q22424", "punjab", "punjab",
            "punjab", None
        ]
        self.wikidata_df.fillna('', inplace=True)

        # Convert name to lower case for matching
        self.wikidata_df['districtLabel'] = self.wikidata_df[
            'districtLabel'].str.lower()
        self.wikidata_df['districtLabel'] = self.wikidata_df[
            'districtLabel'].str.replace("district", "")
        self.wikidata_df['districtLabel'] = self.wikidata_df[
            'districtLabel'].str.strip()
        self.wikidata_df['stateLabel'] = self.wikidata_df[
            'stateLabel'].str.lower()
        self.wikidata_df['census2011Code'] = self.wikidata_df[
            'census2011Code'].apply(CodeFormatter.format_census2011_code)

    def process(self):
        self._load_and_format_lgd()
        self._load_and_format_wikidata()

        # Compare the number of states to validate
        lgd_df_states = sorted(self.lgd_df['LGDStateName'].unique())
        wikidata_df_states = sorted(self.wikidata_df['stateLabel'].unique())

        if lgd_df_states == wikidata_df_states:
            pass
        else:
            raise Exception("States in LGD and Wikidata doesn't match.")

        # Add the matched Wikidata district label into lgd_df data
        self.lgd_df['closestDistrictLabel'] = self.lgd_df.apply(
            lambda row: self.get_closest_district_label(row), axis=1)

        # We match by both state and district names
        self.clean_df = pd.merge(
            self.lgd_df,
            self.wikidata_df,
            how="inner",
            left_on=["closestDistrictLabel", "LGDStateName"],
            right_on=["districtLabel", "stateLabel"])

        # Reformat the columns as per our CSV requirements
        self.clean_df["WikiDataId"] = self.clean_df["district"].apply(
            LocalGovermentDirectoryDistrictsDataLoader.format_wikidataid)

        self.clean_df["LGDDistrictNameTitleCase"] = self.clean_df[
            "LGDDistrictName"].apply(
                LocalGovermentDirectoryDistrictsDataLoader.format_title)

        self.clean_df["districtLabelTitleCase"] = self.clean_df[
            "districtLabel"].apply(
                LocalGovermentDirectoryDistrictsDataLoader.format_title)

    def save(self):
        self.clean_df.to_csv(self.clean_csv, index=False, header=True)


def main():
    """Runs the program."""
    lgd_csv = os.path.join(os.path.dirname(__file__),
                           "./data/lgd_allDistrictofIndia_export.csv")
    wikidata_csv = os.path.join(os.path.dirname(__file__),
                                "./data/wikidata_india_districts_export.csv")
    clean_csv = os.path.join(os.path.dirname(__file__),
                             "LocalGovernmentDirectory_Districts.csv")
    loader = LocalGovermentDirectoryDistrictsDataLoader(lgd_csv, wikidata_csv,
                                                        clean_csv)
    loader.process()
    loader.save()


if __name__ == '__main__':
    main()
