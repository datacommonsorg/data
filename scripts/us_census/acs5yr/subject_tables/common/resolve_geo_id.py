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
    # Congressional district [111th] (fips_code length=4)
    '500': 'geoId/',
    # 5-Digit ZIP code Tabulation Area (fips_code length=5)
    '860': 'zip/',
    # State-School District [Elementary](fips_code length=7)
    '950': 'geoId/sch',
    # State-School District [Secondary](fips_code length=7)
    '960': 'geoId/sch',
    # State-School District [Unified](fips_code length=7)
    '970': 'geoId/sch',
    # Country-level, fips_code is expected to be empty string(fips_code length=1)
    '010': 'country/USA'
}


def convert_to_place_dcid(geoid_str):
    """resolves GEOID based on the Census Summary level. If a geoId could not be
    resolved, the function returns an empty string ('').
    """
    geographic_component, fips_code = geoid_str.split('US')

    summary_level = geographic_component[:3]

    ## Based on summary level, generate place dcid
    if summary_level in _US_SUMMARY_LEVEL_GEO_PREFIX_MAP:
        return _US_SUMMARY_LEVEL_GEO_PREFIX_MAP[summary_level] + fips_code
    else:
        ## if not an interesting summary level
        return ''
