# Copyright 2021 Google LLC
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
import pandas as pd
from india.geo.states import IndiaStatesMapper

__author__ = ["Thejesh GN (i@thejeshgn.com)"]

DISTRICTS_MAPPING_CSV = os.path.join(os.path.dirname(__file__),
                                     "LocalGovernmentDirectory_Districts.csv")

# Some districts have entirely different names over time or in some datasets.
# Even the closestDistrictLabel can't be used for mapping these districts.
# We will use this to map them to resolve it when all other options fail.
#
# This is used for mapping them. Format of the dictionary
# is defined below
# ALTERNATIVE_NAMES_MAPPING = {
#     "state_lgd_code": {
#         "district_lgd_code" : ["alt name1","alt name2"],
#     }
# }
#

ALTERNATIVE_NAMES_MAPPING = {
    "11": {
        "225": ["east sikkim", "east district", "gangtok"],
        "226": ["north sikkim", "north district", "mangan"],
        "227": ["south sikkim", "south district", "namchi"],
        "228": ["west sikkim", "west district", "gyalshing"]
    },
    "03": {
        "031": ["firozpur", "ferozepore", "firozepur"]
    },
    "36": {
        "686": ["warangal urban", "hanumakonda"],
        "522": ["warangal rural", "warangal"]
    }
}


class IndiaDistrictsMapper:
    """Class for resolving various mappings for Indian districts """

    def __init__(self):
        self.districts_df = pd.read_csv(DISTRICTS_MAPPING_CSV, dtype=str)

    def get_district_name_to_lgd_code_mapping(self, state_name, district_name):
        """
        Function to get the the lgd code of a district
        
        Args:
            state_name :  Indian State or UT name
            district_name : India District name
        """
        state_lgd_code = IndiaStatesMapper.get_state_name_to_lgd_code_mapping(
            state_name)
        district_name = district_name.lower().strip()
        # Get the districts for the state. This will reduce
        # The mismatchs
        df_districts_by_state = self.districts_df.loc[
            self.districts_df['LGDStateCode'] == state_lgd_code]

        # Try match directly by name using LGD District Name
        df_districts = df_districts_by_state.loc[
            df_districts_by_state['LGDDistrictName'] == district_name]
        # If the match results in exactly one row, then that is the
        # matched district hence return.
        # If it's 0, then there are no matches
        # If it's more than one, then there are duplicate matches
        if len(df_districts.index) == 1:
            return list(df_districts["LGDDistrictCode"])[0]

        # Try match using districtLabel (WikiData District Name)
        df_districts = df_districts_by_state.loc[
            df_districts_by_state['districtLabel'] == district_name]
        if len(df_districts.index) == 1:
            return list(df_districts["LGDDistrictCode"])[0]

        # Try match using closestDistrictLabel (Close Name Alternatives)
        df_districts = df_districts_by_state.loc[
            df_districts_by_state['closestDistrictLabel'] == district_name]
        if len(df_districts.index) == 1:
            return list(df_districts["LGDDistrictCode"])[0]

        # May be name is completely different now
        if state_lgd_code in ALTERNATIVE_NAMES_MAPPING:
            district_name_alternatives = ALTERNATIVE_NAMES_MAPPING[
                state_lgd_code]
            for key, values in district_name_alternatives.items():
                if district_name in values:
                    return key

        # This shouldn't happen
        raise Exception(
            "{state_name} - District name - {district_name} is not found".
            format(district_name=district_name, state_name=state_name))
