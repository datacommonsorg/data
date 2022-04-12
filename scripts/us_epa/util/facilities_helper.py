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
import json
import pandas as pd
import requests

from re import sub
from requests.structures import CaseInsensitiveDict
from requests.exceptions import HTTPError

_COUNTY_CANDIDATES_CACHE = {}


def v(table, row, col, table_prefix=""):
    if table_prefix:
        return row.get(table_prefix + "." + table + "." + col, "")
    else:
        return row.get(table + '.' + col, '')


def cv(table, row, col, table_prefix=""):
    return v(table, row, col, table_prefix=table_prefix).strip().title()


def get_name(table, row, col_name, table_prefix=""):
    name = cv(table, row, col_name, table_prefix)
    return name.replace(" Llc", " LLC")


def name_to_id(s):
    s = s.replace('&', 'And')
    s = s.replace('U.S.', 'US')
    s = s.replace('U. S.', 'US')
    s = s.replace('United States', 'US')
    s = sub(r'\W+', '', s)
    s = s.replace(' Llc', ' LLC')

    s = s.replace('Corporation', 'Corp')
    s = s.replace('Company', 'Co')
    s = s.replace('Incorportated', 'Inc')
    s = s.replace('Lp', 'LP')
    return ''.join([s[0].upper(), s[1:]])


def get_address(table, row, table_prefix=""):
    parts = []
    for k in ["PARENT_CO_STREET_ADDRESS", "PARENT_CO_CITY", "PARENT_CO_STATE"]:
        p = cv(table, row, k, table_prefix=table_prefix)
        if p:
            parts.append(p)
    address = ", ".join(parts)
    p = cv(table, row, "PARENT_CO_ZIP", table_prefix=table_prefix)
    if p:
        address += " - " + p
    return address


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


def _dc_sv_query(dc_api_url, data_string, svs=set()):
    headers = CaseInsensitiveDict()
    headers["Content-Type"] = "application/json"
    try:
        resp = requests.post(dc_api_url, headers=headers, data=data_string)
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        return set()
    except Exception as e:
        print(f'Some unkonw Exceptionoccurred: {e}')
        return set()

    d = json.loads(resp.content.decode('utf8').replace("'", '"'))
    for p, p_dict in d["places"].items():
        if "statVars" in p_dict:
            sv_list = d["places"][p]["statVars"]
            for sv in sv_list:
                svs.add(sv)
    return svs


# Returns a union all StatVars associated with all facilities using the
# Data Commons API.
def get_all_statvars(dc_api_url, facility_ids):
    if not facility_ids:
        return set()

    statVars = set()
    # 500 facilities at a time.
    n_facilities = 50
    print("****Getting existing StatVars for Facilities.")
    for i in range(0, len(facility_ids), n_facilities):
        if i % n_facilities == 0:
            print(f'**Processing facilities from index {i} to {i+n_facilities}')
        # Compose the API query params.
        # Need to be of the form:
        # '{"dcids":["epaGhgrpFacilityId/1004962","epaGhgrpFacilityId/1010899"]}'
        data_string = "{'dcids': ["
        for f in facility_ids[i:i + n_facilities]:
            data_string += '"%s",' % f
        data_string += ']}'

        statVars = _dc_sv_query(dc_api_url, data_string, statVars)

    print("****Done getting existing StatVars.")
    print("***********************************.")
    return statVars


# Returns a map of Facility ID : {SV: SV Observation} from the Data Commons API.
def get_all_svobs(facility_ids, svs):
    facility_svo_dict = {}

    # Process in batches of size n_facilities.
    n_facilities = 100
    print("****Getting all StatVar Observations for the Facilities.")
    for i in range(0, len(facility_ids), n_facilities):
        if i % n_facilities == 0:
            print(f'**Processing facilities from index {i} to {i+n_facilities}')
        facility_svo_dict.update(
            datacommons.get_stat_all(facility_ids[i:i + n_facilities], svs))

    print("****Done getting existing StatVarObs.")
    print("***********************************.")
    return facility_svo_dict
