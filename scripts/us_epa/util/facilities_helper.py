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
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from datacommons_client.models.observation import ObservationDate
from datacommons_client.models.observation import ObservationSelect
import pandas as pd

from re import sub

from util.dc_api_wrapper import dc_api_get_node_property
from util.dc_api_wrapper import dc_api_is_defined_dcid
from util.dc_api_wrapper import dc_api_wrapper
from util.dc_api_wrapper import get_datacommons_client

_COUNTY_CANDIDATES_CACHE = {}


def v(table, row, col, table_prefix=""):
    if table_prefix:
        key = table_prefix + "." + table + "." + col
        if key in row:
            return row.get(key, "") or ""
    prefixed_key = table + '.' + col
    if prefixed_key in row:
        return row.get(prefixed_key, '') or ''
    if col in row:
        return row.get(col, '') or ''
    return row.get(col.lower(), '') or ''


def cv(table, row, col, table_prefix=""):
    val = v(table, row, col, table_prefix=table_prefix)
    return " ".join(val.splitlines()).strip().title()


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
    if not s:
        return ''
    return ''.join([s[0].upper(), s[1:]])


def _parse_property_values(values):
    """Normalize DC API property values to a list of strings."""
    if isinstance(values, list):
        return values
    return [v for v in values.split(',') if v]


def _type_suffix(value_type):
    return value_type.split(':')[-1] if value_type else ''


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
        try:
            df = pd.read_csv(url, dtype=str)
        except pd.errors.EmptyDataError:
            print('Reached end of table at ' + url)
            break
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
    if first_time:
        raise RuntimeError(f'No rows downloaded for table {table_name}')


def get_cip(zip, county):
    cip = []
    if zip:
        cip.append('dcid:' + zip)
    if county:
        cip.append('dcid:' + county)
    return cip


def prefetch_county_candidates(zctas, cache_file=None):
    """Pre-fetches and caches county candidates for a collection of ZCTAs in batches."""
    if cache_file and os.path.exists(cache_file):
        import json
        try:
            with open(cache_file, 'r') as fp:
                _COUNTY_CANDIDATES_CACHE.update(json.load(fp))
        except Exception:
            pass
    missing_zctas = sorted(
        set(z for z in zctas
            if z and z != 'zip/00000' and z not in _COUNTY_CANDIDATES_CACHE))
    if not missing_zctas:
        return
    api_config = {
        'dc_api_batch_size': 200,
        'dc_api_retries': 6,
        'dc_api_retry_secs': 10,
        'dc_api_use_cache': True,
    }
    props = ['containedInPlace', 'geoOverlaps']
    resp = dc_api_get_node_property(missing_zctas, props, config=api_config)
    zcta_candidates = {}
    all_candidates = set()
    for zcta in missing_zctas:
        candidate_lists = []
        for prop in props:
            values = resp.get(zcta, {}).get(prop, '')
            candidates = [
                c for c in _parse_property_values(values)
                if len(c) == 11 and c.startswith('geoId/') and c[6:].isdigit()
            ]
            candidate_lists.append(candidates)
            all_candidates.update(candidates)
        zcta_candidates[zcta] = candidate_lists

    type_map = {}
    if all_candidates:
        type_resp = dc_api_get_node_property(sorted(all_candidates),
                                             'typeOf',
                                             config=api_config)
        for candidate in all_candidates:
            values = type_resp.get(candidate, {}).get('typeOf', '')
            type_map[candidate] = set(
                _type_suffix(value_type)
                for value_type in _parse_property_values(values))

    for zcta, candidate_lists in zcta_candidates.items():
        filtered_lists = []
        for candidates in candidate_lists:
            filtered = [
                candidate for candidate in candidates
                if 'County' in type_map.get(candidate, set())
            ]
            filtered_lists.append(sorted(filtered))
        _COUNTY_CANDIDATES_CACHE[zcta] = filtered_lists

    if cache_file:
        import json
        with open(cache_file, 'w') as fp:
            json.dump(_COUNTY_CANDIDATES_CACHE, fp)


def get_county_candidates(zcta):
    """Returns counties that the zcta is associated with.

       Returns: two candidate county lists corresponding to zip and geoOverlaps respectively.
    """
    if not zcta or zcta in ('zip/', 'zip/00000'):
        return [[], []]
    if zcta in _COUNTY_CANDIDATES_CACHE:
        return _COUNTY_CANDIDATES_CACHE[zcta]
    candidate_lists = []
    # Aggregate candidates to make a single typeOf lookup.
    all_candidates = set()
    for prop in ['containedInPlace', 'geoOverlaps']:
        resp = dc_api_get_node_property([zcta], prop)
        values = resp.get(zcta, {}).get(prop, '')
        candidates = _parse_property_values(values)
        candidate_lists.append(candidates)
        all_candidates.update(candidates)
    type_map = {}
    if all_candidates:
        # V2 node property values do not filter outgoing arcs by constraints.
        type_resp = dc_api_get_node_property(sorted(all_candidates), 'typeOf')
        for candidate in all_candidates:
            values = type_resp.get(candidate, {}).get('typeOf', '')
            type_map[candidate] = set(
                _type_suffix(value_type)
                for value_type in _parse_property_values(values))
    filtered_lists = []
    for candidates in candidate_lists:
        filtered = []
        for candidate in candidates:
            if 'County' in type_map.get(candidate, set()):
                filtered.append(candidate)
        filtered_lists.append(sorted(filtered))
    _COUNTY_CANDIDATES_CACHE[zcta] = filtered_lists
    return filtered_lists


# Returns a union all StatVars associated with all facilities using the
# Data Commons API.
def get_all_statvars(facility_ids):
    if not facility_ids:
        return set()

    client = get_datacommons_client()
    statVars = set()
    n_facilities = 50
    print("****Getting existing StatVars for Facilities.")
    for i in range(0, len(facility_ids), n_facilities):
        print(f'**Processing facilities from index {i} to {i+n_facilities}')
        response = dc_api_wrapper(
            client.observation.fetch,
            {
                'entity_dcids':
                    facility_ids[i:i + n_facilities],
                'variable_dcids': [],
                'select': [
                    ObservationSelect.VARIABLE,
                    ObservationSelect.ENTITY,
                ],
            },
            retries=5,
            retry_secs=5,
        ).to_dict()
        statVars.update(response.get('byVariable', {}).keys())

    print("****Done getting existing StatVars.")
    print("***********************************.")
    return statVars


# Returns V2 StatVar observations keyed by facility with facet metadata.
def get_all_svobs(facility_ids, svs):
    if not facility_ids or not svs:
        return {}, {}

    facility_sv_map = {}
    facets = {}
    client = get_datacommons_client()
    sv_list = sorted(svs) if isinstance(svs, set) else list(svs)

    # Process in batches of size n_facilities.
    n_facilities = 100
    print("****Getting all StatVar Observations for the Facilities.")
    for i in range(0, len(facility_ids), n_facilities):
        if i % n_facilities == 0:
            print(f'**Processing facilities from index {i} to {i+n_facilities}')
        response = dc_api_wrapper(
            client.observation.fetch,
            {
                'variable_dcids':
                    sv_list,
                'entity_dcids':
                    facility_ids[i:i + n_facilities],
                'date':
                    ObservationDate.ALL,
                'select': [
                    ObservationSelect.DATE,
                    ObservationSelect.VARIABLE,
                    ObservationSelect.ENTITY,
                    ObservationSelect.VALUE,
                    ObservationSelect.FACET,
                ],
            },
            retries=5,
            retry_secs=5,
        ).to_dict()
        batch_by_variable = response.get('byVariable', {})
        batch_facets = response.get('facets', {})
        for stat_var, var_data in batch_by_variable.items():
            by_entity = var_data.get('byEntity', {})
            if not by_entity:
                continue
            for facility_id, entity_data in by_entity.items():
                facility_sv_map.setdefault(facility_id, {})
                facility_sv_map[facility_id][stat_var] = entity_data
        facets.update(batch_facets)

    print("****Done getting existing StatVarObs.")
    print("***********************************.")
    return facility_sv_map, facets
