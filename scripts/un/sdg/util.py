# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Shared util functions and constants.'''
import csv
import math
import os
import re
import sys

module_dir_ = os.path.dirname(__file__)
sys.path.append(os.path.join(module_dir_))

# SDMX indicator for 'total' value in dimension.
TOTAL = '_T'

# Used to split the series code from constraint properties in stat var dcids.
SV_CODE_SEPARATOR = '.'

SERIES_TEMPLATE = '''
Node: dcid:{dcid}
name: "{description}"
typeOf: dcs:SDG_Series
'''
PROPERTY_TEMPLATE = '''
Node: dcid:sdg_{dcid}
typeOf: schema:Property
domainIncludes: dcs:Thing
rangeIncludes: dcs:SDG_{enum}
name: "{name}"
isProvisional: dcs:True
'''
ENUM_TEMPLATE = '''
Node: dcid:SDG_{enum}
typeOf: schema:Class
subClassOf: schema:Enumeration
name: "{enum}"
isProvisional: dcs:True
'''
VALUE_TEMPLATE = '''
Node: dcid:SDG_{enum}_{dcid}
typeOf: dcs:SDG_{enum}
name: "{name}"
isProvisional: dcs:True
'''
SV_TEMPLATE = '''
Node: dcid:{dcid}
typeOf: dcs:StatisticalVariable
measuredProperty: dcs:value
name: {name}
populationType: dcs:{popType}
statType: dcs:measuredValue{cprops}
'''
MMETHOD_TEMPLATE = '''
Node: dcid:{dcid}
typeOf: dcs:SDG_MeasurementMethodEnum
name: "{dcid}"
description: "{description}"
'''
UNIT_TEMPLATE = '''
Node: dcid:{dcid}
typeOf: dcs:SDG_UnitOfMeasure
name: "{name}"
'''

# Use existing properties.
# TODO: Also map enums to existing nodes.
MAPPED_DIMENSIONS = {
    'AGE': 'age',
    'CAUSE_OF_DEATH': 'causeOfDeath',
    'DISABILITY_STATUS': 'disabilityStatus',
    'EDUCATION_LEV': 'educationalAttainment',
    'SEX': 'gender'
}

# Shared dimensions across all input csv files.
BASE_DIMENSIONS = {
    'SERIES_CODE', 'SERIES_DESCRIPTION', 'VARIABLE_CODE',
    'VARIABLE_DESCRIPTION', 'VARIABLE_ACTIVE_DIMS', 'GEOGRAPHY_CODE',
    'GEOGRAPHY_NAME', 'GEOGRAPHY_TYPE', 'GEO_AREA_CODE', 'GEO_AREA_NAME',
    'CITIES', 'SAMPLING_STATIONS', 'IS_LATEST_PERIOD', 'TIME_PERIOD',
    'TIME_DETAIL', 'TIME_COVERAGE', 'FREQ', 'OBS_VALUE', 'VALUE_TYPE',
    'UPPER_BOUND', 'LOWER_BOUND', 'UNIT_MEASURE', 'UNIT_MULT', 'BASE_PERIOD',
    'NATURE', 'SOURCE', 'GEO_INFO_URL', 'FOOT_NOTE', 'REPORTING_TYPE',
    'OBS_STATUS', 'RELEASE_STATUS', 'RELEASE_NAME'
}

# Supported Regions.
# TODO: Add other regions.
REGIONS = {
    1: 'Earth',
    2: 'africa',
    5: 'southamerica',
    9: 'oceania',
    10: 'antarctica',
    21: 'northamerica',
    142: 'asia',
    150: 'europe',
}


def get_country_map(file):
    ''' Creates map of M49 -> ISO-alpha3 for countries.

  Args:
    file: Path to input file.

  Returns:
    Country map.
  '''
    with open(file) as f:
        places = {}
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if not row['ISO-alpha3 code']:  # Only countries for now.
                continue
            places[int(row['M49 code'])] = row['ISO-alpha3 code']
    return places


PLACES = get_country_map(os.path.join(module_dir_, 'm49.csv'))


def get_city_map(file):
    ''' Creates map of name -> dcid for supported cities.

  Args:
    file: Path to input file.

  Returns:
    City map.
  '''
    with open(file) as f:
        reader = csv.DictReader(f)
        return {row['name']: row['dcid'] for row in reader}


CITIES = get_city_map(os.path.join(module_dir_, 'cities.csv'))


def format_description(s):
    '''Formats input with curated style.

    Args:
        s: Input string.

    Returns:
        Curated string.
    '''
    # Remove <=2 levels of ().
    formatted = re.sub('\((?:[^)(]|\([^)(]*\))*\)', '', s)
    # Remove <=2 levels of [].
    formatted = re.sub('\[(?:[^)(]|\[[^)(]*\])*\]', '', formatted)
    # Remove attributes indicated with 'by'.
    formatted = formatted.split(', by')[0]
    # Remove references indicated by 'million USD'.
    formatted = formatted.split(', million USD')[0]
    # Remove extra spaces.
    formatted = formatted.replace(' , ', ', ').replace('  ', ' ').strip()
    # Remove trailing commas.
    if formatted[-1] == ',':
        formatted = formatted[:-1]
    # Replace 100,000 with 100K.
    formatted = formatted.replace('100,000', '100K')
    # Make ascii.
    return formatted.replace('Â',
                             '').replace('’', '\'').replace('₂', '2').replace(
                                 '\xa0', ' ').replace('−', '-')


def is_float(element):
    '''Checks if value can be interpreted as float.

    Args:
      element: Input.

    Returns:
      Whether the value can be cast as a float.
    '''
    if element is None:
        return False
    try:
        float(element)
        return True
    except ValueError:
        return False


def is_valid(v):
    '''Checks if value should be included in csv.

    Args:
      v: Input.

    Returns:
      Whether the value can be used.
    '''
    try:
        return not math.isnan(float(v))
    except ValueError:
        return v and not v == 'nan'


def format_variable_description(variable, series):
    '''Curates variable descriptions.

    Args:
      variable: Full variable description.
      series: Series portion of description.

    Returns:
      Formatted description.
    '''
    parts = variable.split(series)
    return format_description(series) + parts[1] if len(
        parts) > 1 else format_description(series)


def format_variable_code(code):
    '''Curates variable codes with URL-safe encoding.

    Args:
      code: Input code.

    Returns:
      Formatted code.
    '''
    return code.replace('@', SV_CODE_SEPARATOR).replace(' ', '')


def format_title(s):
    '''Formats string as title.

    Args:
      s: Input string.

    Returns:
      Formatted string.
    '''
    return s.replace('_', ' ').title()


def format_property(s):
    '''Formats string as property.

    Args:
      s: Input string.

    Returns:
      Formatted string.
    '''
    return format_title(s).replace(' ', '')
