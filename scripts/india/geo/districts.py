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

        # Try match directly by name
        df_districts = df_districts_by_state.loc[
            df_districts_by_state['LGDDistrictName'] == district_name]
        if len(df_districts.index) == 1:
            return list(df_districts["LGDDistrictCode"])[0]

        # Try match using closestDistrictLabel
        df_districts = df_districts_by_state.loc[
            df_districts_by_state['closestDistrictLabel'] == district_name]
        if len(df_districts.index) == 1:
            return list(df_districts["LGDDistrictCode"])[0]

        # This shouldn't happen
        raise Exception("District name - {district_name} is not found".format(
            district_name=district_name))
