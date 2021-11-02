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
Resolving place dcid given the GEOID string from data,census.gov.

GEOID strings from census are typically 14 characters long that uniquely
identifies a place based on summary level, geographic component and FIPS code.

For example: The GEOID for California is 0400000US06, where
040 - indicates summary-level (in this case, state-level)
00  - indicates geographic variant
00  - indicates geographic component
US  - represents the United States
06  - FIPS code for California State

The code maps the place dcid based on the summary level (eg. state, zip code).
The expected length of the fips_code for each summary level is tabulated in [1].
The expected length of the fips_code can be used to debug issues in geoId
resolution.

Reference:
1. https://www.census.gov/programs-surveys/geography/guidance/geo-identifiers.html
2. https://mcdc.missouri.edu/geography/sumlevs/
"""

# Map for summary levels with expected geo prefix
_US_SUMMARY_LEVEL_GEO_PREFIX_MAP = {
    # TODO: For the inital release, geos are restricted to state/county/places.
    # State-level (fips_code length=2)
    '040': 'geoId/',
    # County-level (fips_code length=5)
    '050': 'geoId/',
    # State-County-County Subdivision (fips_code length=10)
    #'060': 'geoId/',
    # Census tract (fips_code length=11)
    #'140': 'geoId/',
    # Block group (fips_code length=12)
    #'150': 'geoId/',
    # City/ Places (fips_code length=7)
    '160': 'geoId/',
    # Congressional district [111th] (fips_code length=4)
    #'500': 'geoId/',
    # 5-Digit ZIP code Tabulation Area (fips_code length=5)
    #'860': 'zip/',
    # TODO (sharadshriram) Look into the resolution of FIPS code for the school
    # districts summary-levels where the resolved geoId is being the same across
    # mulitple summary levels leading to duplicate observations.
    # State-School District [Elementary](fips_code length=7)
    #'950': 'geoId/sch',
    # State-School District [Secondary](fips_code length=7)
    #'960': 'geoId/sch',
    # State-School District [Unified](fips_code length=7)
    #'970': 'geoId/sch',
    # Country-level, fips_code is expected to be empty string(fips_code length=1)
    '010': 'country/USA'
}

_US_REPLACE_GEO_CODE_MAP = {
    # Replacing/Updating GeoID given in the data. Required in case of wrong geoid mentioned in the data.
    # Reference : https://www.census.gov/programs-surveys/acs/technical-documentation/table-and-geography-changes/2017/geography-changes.html
    # Invalid fips code for Tucker City 1377625 replaced by 1377652
    '1377625': '1377652'
}


def convert_to_place_dcid(geoid_str):
    """resolves GEOID based on the Census Summary level. If a geoId could not be
    resolved, the function returns an empty string ('').
    """
    geographic_component, fips_code = geoid_str.split('US')

    summary_level = geographic_component[:3]

    ## Based on summary level, generate place dcid
    if summary_level in _US_SUMMARY_LEVEL_GEO_PREFIX_MAP:
        ## Update fips code
        if fips_code in _US_REPLACE_GEO_CODE_MAP:
            fips_code = _US_REPLACE_GEO_CODE_MAP[fips_code]
        return _US_SUMMARY_LEVEL_GEO_PREFIX_MAP[summary_level] + fips_code
    else:
        ## if not an interesting summary level
        return ''
