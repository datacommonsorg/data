# Copyright 2021 Google LLC
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
"""
Resolving place dcid given the Pub_agency_name, Agency_type_name, State_Abbr
from FBI hate crime dataset
"""

import os
import sys
import csv

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../util'))  # For State and County map

from alpha2_to_dcid import USSTATE_MAP
from county_to_dcid import COUNTY_MAP

city_geocodes_csv_path = os.path.join(_SCRIPT_PATH,
                                      '../crime/city_geocodes.csv')
manual_city_geocodes_csv_path = os.path.join(_SCRIPT_PATH,
                                             '../crime/manual_geocodes.csv')

_US_GEO_CODE_UPDATE_MAP = {
    # Mapping geos in data to geos in csv / map
    'NB': 'NE',
    'GM': 'GU'
}

_IGNORE_STATE_ABBR = ['FS']  # Ignoring federal codes
_IGNORE_CITIES = ['abington township pa',
                  'lone tree co']  # ignoring cities which have duplicates

city = {}
with open(os.path.join(city_geocodes_csv_path), encoding='utf8') as csvfile:
    csv_reader = csv.reader(csvfile)
    for a in csv_reader:
        city[a[0]] = a[1]


def state_to_dcid(state_code):
    if state_code in _IGNORE_STATE_ABBR:
        return ''

    if state_code in _US_GEO_CODE_UPDATE_MAP:
        state_code = _US_GEO_CODE_UPDATE_MAP[state_code]

    if state_code in USSTATE_MAP:
        return USSTATE_MAP[state_code]
    else:
        return ''


def get_county_variants(county):
    county = county.replace(' County Police Department', ' County')
    county_variants = [
        county, county + ' County', county + ' Parish', county + ' Borough'
    ]
    return county_variants


def county_to_dcid(state_abbr, county):
    if state_abbr in _IGNORE_STATE_ABBR:
        return ''

    if state_abbr in _US_GEO_CODE_UPDATE_MAP:
        state_abbr = _US_GEO_CODE_UPDATE_MAP[state_abbr]

    county_valid_names = get_county_variants(county)

    if state_abbr in COUNTY_MAP:
        for county in county_valid_names:
            if county in COUNTY_MAP[state_abbr]:
                return COUNTY_MAP[state_abbr][county]
        return ''
    else:
        return ''


def city_to_dcid(state_abbr, city_name):
    if state_abbr in _IGNORE_STATE_ABBR:
        return ''
    elif state_abbr in _US_GEO_CODE_UPDATE_MAP:
        state_abbr = _US_GEO_CODE_UPDATE_MAP[state_abbr]

    city_state = city_name.lower().strip() + ' ' + state_abbr.lower().strip()

    if city_state in _IGNORE_CITIES:
        return ''
    elif city_state in _US_GEO_CODE_UPDATE_MAP:
        city_state = _US_GEO_CODE_UPDATE_MAP[city_state]

    if city_state in city:
        return 'geoId/' + city[city_state]
    else:
        return ''


def convert_to_place_dcid(state_abbr, geo_name='', geo_type='State'):
    """resolves GEOID based on the FBI Hate crime dataset Agency Type and Name. 
    If a geoId could not be resolved, the function returns an empty string ('').
    """
    if state_abbr in _IGNORE_STATE_ABBR:
        return ''

    if state_abbr in _US_GEO_CODE_UPDATE_MAP:
        state_abbr = _US_GEO_CODE_UPDATE_MAP[state_abbr]

    if geo_type == 'State':
        return state_to_dcid(state_abbr)

    elif geo_type == 'County':
        return county_to_dcid(state_abbr, geo_name)

    elif geo_type == 'City':
        return city_to_dcid(state_abbr, geo_name)

    else:
        # geo type currently not handled
        return ''
