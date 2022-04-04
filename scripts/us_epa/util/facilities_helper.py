# Copyright 2022 Google LLC
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
"""Helper functions used in the facilities and parent_company processing."""

import os
import ssl

import datacommons
import pandas as pd

_COUNTY_CANDIDATES_CACHE = {}


def download(api_root, table_name, max_rows, output_path):
    # Per https://stackoverflow.com/a/56230607
    ssl._create_default_https_context = ssl._create_unverified_context

    idx = 0
    out_file = os.path.join(output_path, table_name + '.csv')
    first_time = True
    while True:
        # Since 10K rows shouldn't consume too much memory, just use pandas.
        url = api_root + table_name + '/ROWS/' + str(idx) + ':' + str(
            idx + max_rows - 1) + '/csv'
        df = pd.read_csv(url, dtype=str)
        print('Downloaded ' + str(len(df)) + ' rows from ' + url)
        if len(df) == 0:
            break
        if first_time:
            mode = 'w'
            header = True
            first_time = False
        else:
            mode = 'a'
            header = False
        df.to_csv(out_file, mode=mode, header=header, index=False)
        idx = idx + max_rows


def get_cip(zip, county):
    cip = []
    if zip:
        cip.append('dcid:' + zip)
    if county:
        cip.append('dcid:' + county)
    return cip


def get_county_candidates(zcta):
    """Returns counties that the zcta is associated with.

       Returns: two candidate county lists corresponding to zip and geoOverlaps respectively.
    """
    if zcta in _COUNTY_CANDIDATES_CACHE:
        return _COUNTY_CANDIDATES_CACHE[zcta]
    candidate_lists = []
    for prop in ['containedInPlace', 'geoOverlaps']:
        resp = datacommons.get_property_values([zcta],
                                               prop,
                                               out=True,
                                               value_type='County')
        candidate_lists.append(sorted(resp[zcta]))
    _COUNTY_CANDIDATES_CACHE[zcta] = candidate_lists
    return candidate_lists
