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
"""Resolving place dcid from FBI hate crime dataset."""

import os
import sys
import csv

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../util'))  # For State and County map

from alpha2_to_dcid import USSTATE_MAP
from county_to_dcid import COUNTY_MAP

_CITY_GEOCODES_PATH = os.path.join(_SCRIPT_PATH, '../crime/city_geocodes.csv')

_US_GEO_CODE_UPDATE_MAP = {
    # Mapping geos in data to geos in csv / map
    'NB': 'NE',
    'GM': 'GU'
}

_IGNORE_STATE_ABBR = ['FS']  # Ignoring federal codes
_IGNORE_CITIES = ['abington township pa',
                  'lone tree co']  # ignoring cities which have duplicates

_CITY = {}
with open(os.path.join(_CITY_GEOCODES_PATH), encoding='utf8') as csvfile:
    csv_reader = csv.reader(csvfile)
    for a in csv_reader:
        _CITY[a[0]] = a[1]


def _state_to_dcid(state_code: str) -> str:
    """
    Takes in the state alpha2 code and returns the dcid.

    Args:
        state_code: The alpha2 code of the state.

    Returns:
        The dcid of the state in DC. Returns an empty string if the state is not
        found.
    """
    if state_code in _IGNORE_STATE_ABBR:
        return ''

    if state_code in _US_GEO_CODE_UPDATE_MAP:
        state_code = _US_GEO_CODE_UPDATE_MAP[state_code]

    if state_code in USSTATE_MAP:
        return USSTATE_MAP[state_code]
    else:
        return ''


def _get_county_variants(county: str) -> list:
    """
    Given a county, returns a list of the possible variants of the county name.

    Args:
        county: A string literal that represents the county name.

    Returns:
        A list of the possible variants of the county name.
    """
    county = county.replace(' County Police Department', ' County')
    county_variants = [
        county, county + ' County', county + ' Parish', county + ' Borough'
    ]
    return county_variants


def _county_to_dcid(state_abbr: str, county: str) -> str:
    """
    Takes the county name and the state code it's contained in, the dcid of the
    county is returned.

    Args: 
        state_abbr: The alpha2 code of the state.
        county: The county name.

    Returns:
        The dcid of the county in DC. Returns an empty string if the county is
        not found.
    """
    if state_abbr in _IGNORE_STATE_ABBR:
        return ''

    if state_abbr in _US_GEO_CODE_UPDATE_MAP:
        state_abbr = _US_GEO_CODE_UPDATE_MAP[state_abbr]

    county_valid_names = _get_county_variants(county)

    if state_abbr in COUNTY_MAP:
        for county in county_valid_names:
            if county in COUNTY_MAP[state_abbr]:
                return COUNTY_MAP[state_abbr][county]
        return ''
    else:
        return ''


def _city_to_dcid(state_abbr: str, city_name: str) -> str:
    """
    Takes the city name and the alpha2 code of the state it is contained in, the
    dcid of the city is returned.

    Args:
        state_abbr:  The alpha2 code of the state.
        city_name: The city name.

    Returns:
        The dcid of the city in DC. Returns an empty string if the city is not
        found.
    """
    if state_abbr in _IGNORE_STATE_ABBR:
        return ''
    elif state_abbr in _US_GEO_CODE_UPDATE_MAP:
        state_abbr = _US_GEO_CODE_UPDATE_MAP[state_abbr]

    city_state = city_name.lower().strip() + ' ' + state_abbr.lower().strip()

    if city_state in _IGNORE_CITIES:
        return ''
    elif city_state in _US_GEO_CODE_UPDATE_MAP:
        city_state = _US_GEO_CODE_UPDATE_MAP[city_state]

    if city_state in _CITY:
        return 'geoId/' + _CITY[city_state]
    else:
        return ''


def convert_to_place_dcid(state_abbr: str,
                          geo: str = '',
                          geo_type: str = 'State') -> str:
    """
    Resolves the geoId based on the FBI Hate crime dataset Agency Type and Name. 
    If a geoId could not be resolved, the function returns an empty string ('').

    Args:
        state_abbr: The alpha2 code of the state.
        geo: The name of the geo.
        geo_type: The type of the geo. Can be 'State', 'County' or 'City'

    Returns:
        The dcid of the geo. Returns an empty string if the geo is not found.
    """
    if state_abbr in _IGNORE_STATE_ABBR:
        return ''

    if state_abbr in _US_GEO_CODE_UPDATE_MAP:
        state_abbr = _US_GEO_CODE_UPDATE_MAP[state_abbr]

    if geo_type == 'State':
        return _state_to_dcid(state_abbr)

    elif geo_type == 'County':
        return _county_to_dcid(state_abbr, geo)

    elif geo_type == 'City':
        return _city_to_dcid(state_abbr, geo)

    else:
        # geo type currently not handled
        return ''
