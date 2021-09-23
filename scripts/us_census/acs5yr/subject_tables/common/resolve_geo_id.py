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

The code maps the place dcid based on the summary level (eg. state, zip code)
and the Federal Information Processing Standards (FIPS) code for a given place.
The expected length of the fips_code for each summary level is tabulated in [1].

Reference:
1. https://www.census.gov/programs-surveys/geography/guidance/geo-identifiers.html
2. https://mcdc.missouri.edu/geography/sumlevs/
"""

# Map for summary levels with expected geo prefix and FIPS code length
_SUMMARY_LEVELS_FIPS_CODE = {
    # State-level
    '040': ('geoId/', 2),
    # County-level
    '050': ('geoId/', 5),
    # State-County-County Subdivision
    '060': ('geoId/', 10),
    # Census tract
    '140': ('geoId/', 11),
    # Block group
    '150': ('geoId', 12),
    # City (places)
    '160': ('geoId/', 7),
    # Congressional district (111th)
    '500': ('geoId', 4),
    # 5-Digit ZIP code Tabulation Area
    '860': ('zip/', 5),
    # State-School District (Elementary)/Remainder
    '950': ('geoId/sch', 7),
    # State-School District (Secondary)/Remainder
    '960': ('geoId/sch', 7),
    # State-School District (Unified)/Remainder
    '970': ('geoId/sch', 7),
    # Country-level
    '010': ('country/USA', 1)
}


def convert_to_place_dcid(row):
    """resolves GEOID based on the Census Summary level and the expected FIPS
    code length for that summary level. If a geoId could not be resolved,
    the fucntion returns an empty string ('').
    """
    geographic_component, fips_code = row.split('US')

    summary_level = geographic_component[:3]

    ## Based on summary level and FIPS code, genereate geoId
    if summary_level in _SUMMARY_LEVELS_FIPS_CODE:
        return _SUMMARY_LEVELS_FIPS_CODE[summary_level][0] + fips_code
    else:
        ## if not an interesting summary level
        return ''
