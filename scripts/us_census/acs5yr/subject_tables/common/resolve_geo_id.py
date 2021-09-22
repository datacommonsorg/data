"""
Resolving geoIds given the GEOID string from data,census.gov
"""

## The map between summary level and FIPS code is based on
## https://www.census.gov/programs-surveys/geography/guidance/geo-identifiers.html
## A detailed note of summary levels is available at https://mcdc.missouri.edu/geography/sumlevs/
_SUMMARY_LEVELS_FIPS_CODE = {
  '040': 2,
  '050': 5,
  '060': 10,
  '140': 11,
  '150': 12,
  '160': 7,
  '500': 4
}

def _convert_to_geoId(row):
    """resolves GEOID based on the Census Summary level and the expected FIPS code
    length for that summary level. If a geoId could not be resolved, fucntion returns.
    an empty string ('').
    """
    ## Classification of geos is based on
    ## https://www.census.gov/programs-surveys/geography/guidance/geo-identifiers.html
    geographic_component, fips_code = row.split('US')

    summary_level = geographic_component[:3]

    ## Based on summary level and FIPS code, genereate geoId
    if summary_level in _SUMMARY_LEVELS_FIPS_CODE:
      if len(fips_code) == _SUMMARY_LEVELS_FIPS_CODE[summary_level]:
        ### state/ county/ county_subdivision/ census_tract/ places/ congressional_district
        return 'dcid:geoId/' + fips_code

    elif summary_level == '010' and len(fips_code) == 1:
      ### country
      return 'dcid:country/USA'

    #TODO[sharadshriram]: Support for zip code resolution is tested
    # But will be supported in the subsequent PR
    #elif summary_level =='860' and len(fips_code) == 5:
    #  ### ZCTA
    #  return 'dcid:zip/' + fips_code

    #TODO[sharadshriram]: Support for school district resolution is tested
    # But will be supported in the subsequent PR
    #elif summary_level in ['950', '960', '970']:
    #  ### School district
    #  return 'dcid:geoId/sch' + fips_code

    else:
      ## if not an interesting summary level
      return ''
