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


class GeoIdResolver:

    def __init__(self):
        self.city_geo_codes = self.read_city_geocodes()

    def update_state_abbr(self, state_abbr):
        if state_abbr in _US_GEO_CODE_UPDATE_MAP:
            state_abbr = _US_GEO_CODE_UPDATE_MAP[state_abbr]
        return state_abbr

    def get_city_variants(self, city):
        city = city.strip().lower()
        city_variants = [city]

        # for delim in [",", "-"]:
        #     if delim in city:
        #         city_variants.extend(city.split(delim))

        city_variants.extend([
            city + " city", city + " village",
            city.removesuffix("city"),
            city.removesuffix("village"),
            city.removesuffix("town"),
            city.removesuffix("township"),
            city.removesuffix("borough")
        ])

        return city_variants

    def read_city_geocodes(self):
        """ Read geo codes from city_geocodes """
        city = {}
        with open(os.path.join(city_geocodes_csv_path),
                  encoding="utf8") as csvfile:
            csv_reader = csv.reader(csvfile)
            for a in csv_reader:
                city[a[0]] = a[1]
        return city

    def city_to_dcid(self, state_abbr, city):
        city_valid_names = self.get_city_variants(city)
        city_state_list = [
            city.strip().lower() + " " + state_abbr.lower()
            for city in city_valid_names
        ]

        for city_state in city_state_list:
            if city_state in self.city_geo_codes:
                return "geoId/" + self.city_geo_codes[city_state]
        return ''

    def preprocess_county(self, county):
        for suffix in _IGNORE_COUNTY_SUFFIX:
            if suffix in county.strip():
                return county.removesuffix(suffix).strip()
        return county.strip()

    def get_county_variants(self, county):
        county_variants = [
            county,
            county + " County",
            county.removesuffix('County'),
            county + " Parish",
        ]
        return county_variants

    def county_to_dcid(self, state_abbr, county):

        county = self.preprocess_county(county)

        county_valid_names = self.get_county_variants(county)

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

    def state_to_dcid(self, state_code):

        if state_code in _IGNORE_STATE_ABBR:
            return ''

        if state_code in USSTATE_MAP:
            return USSTATE_MAP[state_code]
        else:
            return ''

    def convert_to_place_dcid(self, state_abbr, geo_name='', geo_type='State'):
        """resolves GEOID based on the FBI Hate crime dataset Agency Type and Name. 
        If a geoId could not be resolved, the function returns an empty string ('').
        """

        # Update anonymous State Abbreviations
        state_abbr = self.update_state_abbr(state_abbr)

        if geo_type == 'State':
            return self.state_to_dcid(state_abbr)

        elif geo_type == 'County':
            return self.county_to_dcid(state_abbr, geo_name)

        elif geo_type == 'City':
            return self.city_to_dcid(state_abbr, geo_name)

        else:
            # geo type currently not handled
            return ''
