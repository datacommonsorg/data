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

# Note 1: The summary level codes 950, 960, 970 which broadly belong to school districts  have duplicates. The duplicates are for places that are represented as "Remainder of <US State>" for which we do not have node on the KG.
# Note 2: For places that are named in the subject table as "Remainder of <US State>" the length of the FIPS code matches for the summary level of school districts and the FIPS code ends with 5-`9`s. Since we know that this yields duplicate rows, we return an empty string for all FIPS code that ends with 5-`9`s

# Map for summary levels with expected geo prefix
_US_SUMMARY_LEVEL_GEO_PREFIX_MAP = {
    # Country-level, fips_code is expected to be empty string(fips_code length=1)
    '010': 'country/USA',
    # Census Divisions (code_length=1)
    '030': 'US',
    # State-level (fips_code length=2)
    '040': 'geoId/',
    # County-level (fips_code length=5)
    '050': 'geoId/',
    # State-County-County Subdivision (fips_code length=10)
    '060': 'geoId/',
    # Census tract (fips_code length=11)
    '140': 'geoId/',
    # Block group (fips_code length=12)
    '150': 'geoId/',
    # City/ Places (fips_code length=7)
    '160': 'geoId/',
    # Metropolitan and Micropolitan statistical area (fips_code length=?)
    '310': 'geoId/C',
    # Congressional district [111th] (fips_code length=4)
    '500': 'geoId/',
    # 5-Digit ZIP code Tabulation Area (fips_code length=5)
    '860': 'zip/',
    # State-School District [Elementary](fips_code length=7)
    '950': 'geoId/sch',
    # State-School District [Secondary](fips_code length=7)
    '960': 'geoId/sch',
    # State-School District [Unified](fips_code length=7)
    '970': 'geoId/sch'
}

_US_CENSUS_DIVISIONS_MAP = {
    # usc/NortheastRegion
    '1': 'usc/NewEnglandDivision',
    '2': 'usc/MiddleAtlanticDivision',
    # usc/MidwestRegion
    '3': 'usc/EastNorthCentralDivision',
    '4': 'usc/WestNorthCentralDivision',
    # usc/SouthRegion',
    '5': 'usc/SouthAtlanticDivision',
    '6': 'usc/EastSouthCentralDivision',
    '7': 'usc/WestSouthCentralDivision',
    # usc/WestRegion',
    '8': 'usc/MountainDivision',
    '9': 'usc/PacificDivision',
}

_US_GEO_CODE_UPDATE_MAP = {
    # Replacing/Updating GeoID given in the data. Required in case of wrong geoid mentioned in the data.
    # Reference : https://www.census.gov/programs-surveys/acs/technical-documentation/table-and-geography-changes/2017/geography-changes.html
    # Invalid FIPS code for Tucker City 1377625 replaced by 1377652
    '1377625': '1377652'
}


def convert_to_place_dcid(geoid_str):
    """resolves GEOID based on the Census Summary level. If a geoId could not be
    resolved, the function returns an empty string ('').
    """
    geographic_component, fips_code = geoid_str.split('US')

    summary_level = geographic_component[:3]

    ## Based on summary level and FIPS code generate place dcid
    if summary_level in _US_SUMMARY_LEVEL_GEO_PREFIX_MAP:
        if summary_level == '030':
            # Census Divisions are not prefix based fips codes. Lookup map.
            if fips_code in _US_CENSUS_DIVISIONS_MAP:
                return _US_CENSUS_DIVISIONS_MAP[fips_code]
            else:
                # Invalid division code.
                return ''
        ## Update FIPS code
        if fips_code in _US_GEO_CODE_UPDATE_MAP:
            fips_code = _US_GEO_CODE_UPDATE_MAP[fips_code]

        ## Skip resolving geoIds for "Remainder of <US State>" school districts that ends with 5-(9)'s
        if fips_code.endswith('99999'):
            return ''
        return _US_SUMMARY_LEVEL_GEO_PREFIX_MAP[summary_level] + fips_code
    else:
        ## if not an interesting summary level
        return ''
