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

# Splits the series code from constraint properties in SDG variable codes.
SDG_CODE_SEPARATOR = '@'

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
statType: dcs:measuredValue{cprops}{footnote}
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

# Series where zero should be treated as null and removed.
ZERO_NULL = {
    'SE_ACS_CMPTR',
    'SE_ACS_H2O',
    'SE_AGP_CPRA',
    'SE_ALP_CPLR',
    'SE_AWP_CPRA',
    'SE_ACC_HNDWSH',
    'SE_INF_DSBL',
    'SE_TOT_CPLR',
    'SE_TRA_GRDL',
    'SE_ACS_INTNT',
}

# Footnote text indicated that a zero point should be treated as null and removed.
ZERO_NULL_TEXT = 'This data point is NIL for the submitting nation.'

DROP_VARIABLE = {'VC_DTH_TOTPT'}

DROP_SERIES = {
    'TX_IMP_GBMRCH',
    'TX_EXP_GBMRCH',
    'TX_IMP_GBSVR',
    'TX_EXP_GBSVR',
    'SH_SAN_SAFE',
    'AG_PRD_XSUBDY',
}

MAP = {
    'Education level': 'education',
    'Frequency of Chlorophyll-a concentration': 'frequency',
    'Report Ordinal': 'ordinal',
    'Grounds of discrimination': 'discrimination',
    'Deviation Level': 'deviation'
}

PLACE_MAPPINGS = {}
with open('geography/place_mappings.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        PLACE_MAPPINGS[str(row['sdg'])] = str(row['dcid'])


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
    # Remove references indicated by 'million USD'.
    formatted = formatted.split(', million USD')[0]
    # Remove extra spaces.
    formatted = formatted.replace(' , ', ', ').replace('  ', ' ').strip()
    # Remove trailing commas.
    if formatted[-1] == ',':
        formatted = formatted[:-1]
    # Replace 100,000 with 100K.
    formatted = formatted.replace('100,000', '100K')
    # Remove some apostrophe.
    formatted = formatted.replace("Developing countries’",
                                  'Developing countries')
    # Replace DRR with Disaster Risk Reduction.
    formatted = formatted.replace('DRR', 'Disaster Risk Reduction')
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


def replace_me(text, mappings):
    new_text = text.split('[')
    if len(new_text) == 1:
        return text
    next_text = new_text[1][0:-1]
    new_string = new_text[0] + '['
    raw_pairs = next_text.split('|')

    new_pairs = []
    for raw_pair in raw_pairs:
        new_pair = ''

        temp = raw_pair.split('=')
        left_equal, right_equal = temp[0], temp[1]
        left_equal = left_equal.strip()
        right_equal = right_equal.strip()

        if left_equal in mappings:
            if left_equal == 'Education level':
                if 'education' in right_equal:
                    new_pair = right_equal
                else:
                    new_pair = right_equal + ' ' + mappings[left_equal]
            elif '(' in right_equal:
                level, percentage = right_equal.split('(')
                level = level.strip()
                percentage = percentage[:-1]
                new_pair = level + ' ' + mappings[
                    left_equal] + ' (' + percentage + ')'
            else:
                new_pair = right_equal + ' ' + mappings[left_equal]
        else:
            new_pair = raw_pair.strip()

        new_pairs.append(new_pair)
    new_string += ', '.join(new_pairs)
    new_string += ']'
    return new_string


def format_variable_description(variable, series):
    '''Curates variable descriptions.

    Args:
      variable: Full variable description.
      series: Series portion of description.

    Returns:
      Formatted description.
    '''
    head = format_description(series)
    pvs = variable.removeprefix(series)
    if not pvs:
        return head
    pvs = re.sub(r'\(ISIC[^)]*\)', '', pvs)
    pvs = re.sub(r'\(isco[^)]*\)', '', pvs)
    pvs = replace_me(pvs, MAP)
    pvs = pvs.replace('Age = ', '')
    pvs = pvs.replace('Name of non-communicable disease = ', '')
    pvs = pvs.replace('Substance use disorders = ', '')
    pvs = pvs.replace('Quantile = ', '')
    pvs = pvs.replace('Type of skill = Skill: ', '')
    pvs = pvs.replace('Type of skill = ', '')
    pvs = pvs.replace('Sex = ', '')
    pvs = pvs.replace('Land cover = ', '')
    pvs = pvs.replace('Level/Status = ', '')
    pvs = pvs.replace('Policy instruments = ', '')
    pvs = pvs.replace('Type of product = ', '')
    pvs = pvs.replace('Type of waste treatment = ', '')
    pvs = pvs.replace('Activity = ', '')
    pvs = pvs.replace('Type of renewable technology = ', '')
    pvs = pvs.replace('Location = ', '')
    pvs = pvs.replace('Level_of_government = ', '')
    pvs = pvs.replace('Fiscal intervention stage = ', '')
    pvs = pvs.replace('Name of international institution = ', '')
    pvs = pvs.replace('Policy Domains = ', '')
    pvs = pvs.replace('Mode of transportation = ', '')
    pvs = pvs.replace('Food Waste Sector = ', '')
    pvs = pvs.replace('24 to 59 months old', '2 to 5 years old')
    pvs = pvs.replace('36 to 47 months old', '3 to 4 years old')
    pvs = pvs.replace('36 to 59 months old', '3 to 5 years old')
    pvs = pvs.replace('12 to 23 months', '1 to 2 years old')
    pvs = pvs.replace('24 to 35 months', '2 to 3 years old')
    pvs = pvs.replace('36 to 47 months old', '3 to 4 years old')
    pvs = pvs.replace('48 to 59 months', '4 to 5 years old')
    return head + pvs


def format_variable_code(code):
    '''Curates variable codes with URL-safe encoding.

    Args:
      code: Input code.

    Returns:
      Formatted code.
    '''
    return code.replace(SDG_CODE_SEPARATOR, SV_CODE_SEPARATOR).replace(' ', '')


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
