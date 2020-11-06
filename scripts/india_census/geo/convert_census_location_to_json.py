# Copyright 2020 Google LLC
#
# Licensed under the Apache License',' Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing',' software
# distributed under the License is distributed on an "AS IS" BASIS','
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND',' either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import json
import numpy as np
import pandas as pd


class ConvertResolvedLocationData:

    def __init__(self, census_data_dir, resolved_geos_file_name_pattern,
                 census_location_to_dcid_json_file_pattern, census_year):
        self.census_year = census_year
        self.census_data_dir = census_data_dir
        self.resolved_geos_file_name_pattern = resolved_geos_file_name_pattern
        self.census_location_to_dcid_json_file_pattern = census_location_to_dcid_json_file_pattern
        self.raw_df = None

    def _download(self):
        path = os.path.join(
            self.census_data_dir,
            self.resolved_geos_file_name_pattern.format(year=self.census_year))
        self.raw_df = pd.read_csv(path)

    def generate_location_json(self):
        self._download()
        #Drop the columns that we dont require
        columns_to_drop = [
            "State", "District", "Subdistt", "Town/Village", "Ward", "EB",
            "Level", "Name"
        ]
        self.raw_df.drop(columns_to_drop, axis=1, inplace=True)

        # Unset dcids for later rows if multiple rows resolved to the same dcid.
        self.raw_df.loc[self.raw_df['dcid'].duplicated(), 'dcid'] = np.nan
        self.raw_df.loc[self.raw_df['dcid'].duplicated(
        ), 'errors'] = 'DCID resolved to a duplicate parent or previous sibling.'

        # Create a new df with no NaNs.
        dfs = self.raw_df[['census_location_id', 'dcid']].dropna()

        dfs['dcid'] = 'dcid:' + dfs['dcid'].astype(str)
        location2dcid = dict(zip(dfs.census_location_id, dfs.dcid))

        output_path = os.path.join(
            self.census_data_dir,
            self.census_location_to_dcid_json_file_pattern.format(
                year=self.census_year))
        with open(output_path, 'w') as f_out:
            json.dump(location2dcid, f_out, indent=4, sort_keys=True)


if __name__ == '__main__':
    census_data_dir = os.path.join(os.path.dirname(__file__), "data")
    resolved_geos_file_name_pattern = "india_census_{year}_geo_resolved.csv"
    census_location_to_dcid_json_file_pattern = "india_census_{year}_location_to_dcid.json"
    census_year = 2011
    converter = ConvertResolvedLocationData(
        census_data_dir, resolved_geos_file_name_pattern,
        census_location_to_dcid_json_file_pattern, census_year)
    converter.generate_location_json()
