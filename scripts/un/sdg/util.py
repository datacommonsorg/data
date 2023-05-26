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
import re

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
typeOf: dcs:UnitOfMeasure
name: "{name}"
description: "SDG unit type {dcid}."
'''

# Select concepts will be modeled differently.
SKIPPED_CONCEPTS = {
    'Cities', 'Freq', 'Nature', 'Observation Status', 'Report Ordinal',
    'Reporting Type', 'UnitMultiplier', 'Units'
}

# Use existing properties when they exist.
# TODO: Also map enums to existing nodes.
MAPPED_CONCEPTS = {
    'Age': 'age',
    'Cause of death': 'causeOfDeath',
    'Disability status': 'disabilityStatus',
    'Education level': 'educationalAttainment',
    'Sex': 'gender',
}

FORMATTED_UNITS = {
    'INDEX': 'idx',
    'NUM_M': '#m',
    'NUMBER': '#',
    'PERCENT': '%',
    'PH': 'pH',
    'TONNES': 't',
    'TONNES_M': 'Metric Tonnes'
}


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
    # Remove extra spaces
    formatted = formatted.replace(' , ', ', ').replace('  ', ' ').strip()
    # Remove trailing commas
    formatted = formatted.removesuffix(',')
    # Replace 100,000 with 100K
    formatted = formatted.replace('100,000', '100K')
    # Make ascii
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


def make_property(s):
    '''Formats property string.

    Args:
      s: Input string.

    Returns:
      Formatted string.
    '''
    return s.title().replace(' ', '').replace('-',
                                              '').replace('_',
                                                          '').replace('/', '')


def make_value(s):
    '''Formats value string.

    Args:
      s: Input string.

    Returns:
      Formatted string.
    '''
    return s.replace('<=', 'LEQ').replace('<',
                                          'LT').replace('+', 'GEQ').replace(
                                              ' ', '').replace('_', '')
