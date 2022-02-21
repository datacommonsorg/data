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

_CITY = {
    'las vegas metropolitan police department nv': '3240000',
    'honolulu hi': '1571550',
    'charlotte-mecklenburg nc': '3712000',
    'indianapolis in': '1836003',
    'louisville metro ky': '2148006',
    'nashville metropolitan tn': '4752006',
    'lexington ky': '2146027',
    'athens-clarke county ga': '1303440',
    'greece town ny': '3630279',
    'colonie town ny': '3617332',
    'cheektowaga town ny': '3615000',
    'camden county police department nj': '3410000',
    'waterford township mi': '2612584240',
    'southampton town ny': '3668462',
    'methuen ma': '2540710',
    'irondequoit town ny': '3637737',
    'west seneca town ny': '3680907',
    'webster town and village ny': '3678960',
    'pocono mountain regional pa': '4251912',
    'braintree ma': '2507740',
    'lancaster town ny': '3641135',
    'grand blanc township mi': '2633300',
    'brighton town ny': '3608257',
    'watertown ma': '2573440',
    'austintown oh': '3903184',
    'brownstown township mi': '2611220',
    'newburgh town ny': '3650045',
    'flint township mi': '2629020',
    'rotterdam town ny': '3663924',
    'los alamos nm': '3542320',
    'big bear ca': '0606406',
    'spring valley tx': '4869830',
    'washington dc': '1150000',
    'boise id': '1608830',
    'west valley ut': '4983470',
    'amherst town ny': '3602902000',
    'ventura ca': '0665042',
    'ramapo town ny': '3608760510',
    'canton township mi': '2613120',
    'clarkstown town ny': '3608715968',
    'west bloomfield township mi': '2612585480',
    'weymouth ma': '2578972',
    'hempstead village ny': '3633139',
    'irvington nj': '3401334450',
    'bloomfield nj': '3401306260',
    'west orange nj': '3401379800',
    'redford township mi': '2616367625',
    'greenburgh town ny': '3611930367',
    'barnstable ma': '2503690',
    'freeport village ny': '3627485',
    'de kalb il': '1719161',
    'meridian township mi': '2606553140',
    'greenacres city fl': '1227322',
    'saginaw township mi': '2614570540',
    'pittsfield township mi': '2616164560',
    'montclair nj': '3401347500',
    'commerce township mi': '2612517640',
    'orangetown town ny': '3608755211',
    'haverstraw town ny': '3608732765',
    'yorktown town ny': '3611984077',
    'blackman township mi': '2607508760',
    'independence township mi': '2612540400',
    'belleville nj': '3401304695',
    'orion township mi': '2612561100',
    'bethlehem town ny': '3600106354',
    'carmel town ny': '3607912529',
    'guilderland town ny': '3600131104',
    'houma la': '2236255',
    'franklin ma': '2525172',
    'spring valley village ny': '3670420',
    'mount lebanon pa': '4200351696',
    'paso robles ca': '0622300',
    'white lake township mi': '2612586860',
    'orange city nj': '3401313045',
    'orchard park town ny': '3602955277',
    'port chester village ny': '3659223',
    'la canada flintridge ca': '0639003',
    'espanola nm': '3525170',
    'kensington ca': '0638086',
    'sansom park village tx': '4865660',
    'broadmoor ca': '0608338',
    'carmel ca': '0611250',
    'angels camp ca': '0602112',
    'port mansfield tx': '4858928'
}

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
