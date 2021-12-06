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
import io
import sys
import csv

from .manual_geocodes import MANUAL_COUNTY_MAP

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../util'))  # For State and County map
from alpha2_to_dcid import USSTATE_MAP
from county_to_dcid import COUNTY_MAP

city_geocodes_csv_path = os.path.join(_SCRIPT_PATH,
                                      '../crime/city_geocodes.csv')

_US_GEO_CODE_UPDATE_MAP = {
    # Replacing/Updating State abbreviations given in the data. Required in case of wrong state abbr mentioned in the data.
    'NB': 'NE',  # Nebraska State
    'GM': 'GU'  # Guam State
}

_IGNORE_STATE_ABBR = ['FS']  # Federal mentioned as State in data

_IGNORE_COUNTY_SUFFIX = [
    'Unified Police Department', 'Police Department', 'Public Safety'
]

city_geo_codes = {}
with open(os.path.join(city_geocodes_csv_path), encoding="utf8") as csvfile:
    csv_reader = csv.reader(csvfile)
    for a in csv_reader:
        city_geo_codes[a[0]] = a[1]


def update_state_abbr(state_abbr):
    """
    Replaces the incorrect state code with the correct one

    Parameters:
        state_abbr (str): Two letter code for US State
    
    Returns:
        state_abbr(str): Corrected two letter US State code
    """

    if state_abbr in _US_GEO_CODE_UPDATE_MAP:
        state_abbr = _US_GEO_CODE_UPDATE_MAP[state_abbr]
    return state_abbr


def get_city_variants(city):
    """
    Get a list of all the variants of the input city name available

    Parameters:
        city (str): input city name
    
    Returns:
        city_variants(list): list of all the variants of the input city name
    """

    city = city.strip().lower()
    city_variants = [city]

    # for delim in [",", "-"]:
    #     if delim in city:
    #         city_variants.extend(city.split(delim))

    city_variants.extend([
        city + " city", city + " village", city + " town", city + " township",
        city + " borough",
        city.removesuffix("city"),
        city.removesuffix("village"),
        city.removesuffix("town"),
        city.removesuffix("township"),
        city.removesuffix("borough")
    ])

    return city_variants


def city_to_dcid(state_abbr, city):
    """
    Resolve the input city name to geoId using city_geo_codes map

    Parameters:
        state_abbr(str): two digit US State code to uniquely identify the input city
        city (str): input city name
    
    Returns:
        geo_id(str): geoId string if the city name geoId is resolved else ''
    """

    geo_id = ''
    city_valid_names = get_city_variants(city)
    city_state_list = [
        city.strip().lower() + " " + state_abbr.lower()
        for city in city_valid_names
    ]

    for city_state in city_state_list:
        if city_state in city_geo_codes:
            geo_id = "geoId/" + city_geo_codes[city_state]
            break
    return geo_id


def preprocess_county(county):
    """
    Helper function to preprocess the input county name

    Parameters:
        county (str): input county name
    
    Returns:
        county(str): preprocessed county name
    """

    county = county.strip()
    for suffix in _IGNORE_COUNTY_SUFFIX:
        if county.endswith(suffix):
            return county.removesuffix(suffix).strip()
    return county


def get_county_variants(county):
    """
    Get a list of all the variants of the input county name available

    Parameters:
        county (str): input county name
    
    Returns:
        county_variants(list): list of all the variants of the input county name
    """
    county_variants = [
        county,
        county + " Parish",
        county + " County",
        county.removesuffix('County'),
    ]
    return county_variants


def county_to_dcid(state_abbr, county):
    """
    Resolve the input county name to geoId using county to dcid maps

    Parameters:
        state_abbr(str): two digit US State code to uniquely identify the input county
        county (str): input county name
    
    Returns:
        geo_id (str): geoId string if the county name geoId is resolved else ''
    """

    county = preprocess_county(county)
    county_valid_names = get_county_variants(county)
    geo_id = ''

    if state_abbr in COUNTY_MAP:
        for county in county_valid_names:
            if county in COUNTY_MAP[state_abbr]:
                geo_id = COUNTY_MAP[state_abbr][county]
                return geo_id

    if state_abbr in MANUAL_COUNTY_MAP:
        for county in county_valid_names:
            if county in MANUAL_COUNTY_MAP[state_abbr]:
                geo_id = MANUAL_COUNTY_MAP[state_abbr][county]
                return geo_id

    return geo_id


def state_to_dcid(state_code):
    """
    Resolve the input state code to geoId using state to dcid map

    Parameters:
        state_code(str): two digit US State code
        
    Returns:
        (str): geoId string if the state code geoId is resolved else ''
    """

    if state_code in _IGNORE_STATE_ABBR:
        return ''

    if state_code in USSTATE_MAP:
        return USSTATE_MAP[state_code]
    else:
        return ''


def convert_to_place_dcid(state_abbr, geo_name='', geo_type='State'):
    """
    Wrapper function to resolve the GEOID based on the FBI Hate crime dataset Agency Type and Name

    Parameters:
        state_abbr(str): two digit US State code
        geo_name (str): name of the geo (e.g. county/city name etc)
        geo_type (str): type of the input geo (State/County/City, default : State)
    
    Returns:
        (str): geoId string if the geoId is resolved else returns ''
    """

    # Update anonymous State Abbreviations
    state_abbr = update_state_abbr(state_abbr)

    if geo_type == 'State' and not geo_name:
        return state_to_dcid(state_abbr)

    elif geo_type == 'County':
        return county_to_dcid(state_abbr, geo_name)

    elif geo_type == 'City':
        return city_to_dcid(state_abbr, geo_name)

    else:
        # geo type currently not handled
        return ''
