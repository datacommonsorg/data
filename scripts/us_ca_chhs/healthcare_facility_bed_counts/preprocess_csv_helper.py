# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import numpy as np

# This function is to return a map{county_name: geoId} given CA county name.
def generate_dcid_for_county(counties):
    county_to_geoID = {}
    sorted_counties = np.sort(counties)
    # see browser.datacommons.org/kg?dcid=geoId/06 for convention for geoId to county.
    counties_id = [i for i in range(1, len(counties) * 2 + 1, 2)]
    for i in range(len(sorted_counties)):
        county_to_geoID[sorted_counties[i]] = perserve_length(counties_id[i])
    return county_to_geoID


# A helper function to generate geoId for given county name.
def perserve_length(county):
    county = str(county)

    if len(county) >= 3:
        return 'geoId/06' + county

    diff = 3 - len(county)
    for i in range(diff):
        county = '0' + county

    return 'geoId/06' + county


# A helper function to perserve zero for FACID
def preserve_leading_zero(FACID):
    if len(FACID) >= 9:
        return FACID

    zero_missing = 9 - len(FACID)
    for i in range(zero_missing):
        FACID = '0' + FACID

    return FACID

def get_camel_formatting_name_list(name_list):
    formatting_list = []
    for name in name_list:
        formatting_list.append(get_camel_formatting_name(name))
    return formatting_list


def get_camel_formatting_name(name):
    after_spliter = name.split(' ')
    after_cap = [spliter.capitalize() for spliter in after_spliter]
    formatting_name = ''
    for word in after_cap:
        formatting_name = formatting_name + word
    return formatting_name
