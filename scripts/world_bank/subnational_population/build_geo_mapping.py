# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Script to process flood insurance claims data from US FEMA's
National Flood Insurance Program using the generic stat-var_processor.'''

import os
import sys
import pandas as pd
import datacommons
import numpy as np

from absl import app

default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")

default_output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "dcid_resolve")

tmp_out_file = os.path.join(default_output_path, 'tmp_geo_map.csv')
tmp_map_file = os.path.join(default_output_path, 'country_AA1_map.csv')

if not os.path.exists(default_output_path):
    os.mkdir(default_output_path)

ref_county_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "reference_files")
country_dcid_file = os.path.join(ref_county_file_path, 'country_dcid.csv')

country_df = pd.DataFrame()
admin1_df = pd.DataFrame()
input_geo_df = pd.DataFrame()


def read_country_file() -> pd.DataFrame:
    country_df = pd.read_csv(country_dcid_file)
    country_df.columns = ["country_id", "name"]
    return (country_df)


def build_admin_area_dict(country_df: pd.DataFrame) -> pd.DataFrame:

    country_list = list(pd.unique(country_df["country_id"]))
    contained_in_df = pd.DataFrame()
    level2_geo_type = ["AdministrativeArea1", "State", "EurostatNUTS2"]

    for lvl in level2_geo_type:
        resp = datacommons.get_places_in(country_list, lvl)
        for key, val_list in resp.items():
            temp_df = pd.DataFrame(val_list)
            temp_df["parent_dc_id"] = key
            contained_in_df = pd.concat([contained_in_df, temp_df],
                                        ignore_index=True,
                                        axis=0)

    contained_in_df.columns = ["leve2_geo_id", "country_id"]
    admin_area_id_list = list(pd.unique(contained_in_df["leve2_geo_id"]))
    geo_name_dict = datacommons.get_property_values(admin_area_id_list, 'name')
    contained_in_df['leve2_geo_name'] = contained_in_df['leve2_geo_id'].map(
        geo_name_dict)
    contained_in_df['country_name'] = contained_in_df['country_id'].map(
        country_df.set_index('country_id')['name'])
    #Split multiple names into separate rows
    level2name_series = contained_in_df.apply(
        lambda x: pd.Series(x['leve2_geo_name'], dtype='string'),
        axis=1).stack().reset_index(level=1, drop=True)
    level2name_series.name = 'leve2_geo_name'
    contained_in_df = contained_in_df.drop('leve2_geo_name',
                                           axis=1).join(level2name_series)
    return (contained_in_df)


def get_input_geo() -> pd.DataFrame():

    input_files = [
        os.path.join(default_input_path, file)
        for file in sorted(os.listdir(default_input_path))
        if file != ".DS_Store"
    ]
    final_input_df = pd.DataFrame()
    col_list = ['Level_attr', 'Country Name', 'Country Code']
    for input_file in sorted(input_files):
        raw_df = pd.read_excel(input_file, usecols=col_list, skipfooter=5)
        final_input_df = pd.concat([final_input_df, raw_df],
                                   ignore_index=True,
                                   axis=0)
    final_input_df.columns = ['level_name', 'geo_name', 'geo_code']
    return (final_input_df)


def map_admin_area(row) -> str:
    global admin1_df
    x = admin1_df.loc[(admin1_df['country_name'] == row['level_name']) &
                      (admin1_df['leve2_geo_name'] == row['geo_name']),
                      'leve2_geo_id']
    if len(x) > 0:
        return (x[0])
    else:
        return np.nan


def map_country(row) -> str:
    global country_df
    for index, maprow in country_df.iterrows():
        if (maprow["name"].lower() == str(row["level_name"]).lower()):
            return (maprow["country_id"])
    return np.nan


def dcid_resolve():
    global country_df, admin1_df, input_geo_df
    country_df = read_country_file()
    admin1_df = build_admin_area_dict(country_df)
    admin1_df.to_csv(tmp_map_file, index=False)


def main(_):
    dcid_resolve()


if __name__ == '__main__':
    app.run(main)