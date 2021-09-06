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
"""A utility to generate dcid for statistical variables."""

import copy
import re

# Global constants
# Regex to match the quantity notations - [value quantity], [quantity value]
# Example matches: [2 Person], [Person 2]
_QUANTITY_REGEX_1 = re.compile(
    r'\[(?P<value>-|-?\d+(\.\d+)?) (?P<quantity>[A-Za-z_/\d]+)\]')
_QUANTITY_REGEX_2 = re.compile(
    r'\[(?P<quantity>[A-Za-z_/\d]+) (?P<value>-|-?\d+(\.\d+)?)\]')

# Regex to match the quantity range notations -
# [lower_limit upper_limit quantity], [quantity lower_limit upper_limit]
# Example matches: [10000 14999 USDollar], [USDollar 10000 14999]
_QUANTITY_RANGE_REGEX_1 = re.compile(r'\[(?P<lower_limit>-|-?\d+(\.\d+)?) '
                                     r'(?P<upper_limit>-|-?\d+(\.\d+)?) '
                                     r'(?P<quantity>[A-Za-z_/\d]+)\]')
_QUANTITY_RANGE_REGEX_2 = re.compile(r'\[(?P<quantity>[A-Za-z_/\d]+) '
                                     r'(?P<lower_limit>-|-?\d+(\.\d+)?) '
                                     r'(?P<upper_limit>-|-?\d+(\.\d+)?)\]')

# These are the default properties ignored during dcid generation
_DEFAULT_IGNORE_PROPS = ('unit', 'Node', 'memberOf', 'typeOf',
                         'constraintProperties', 'name')


def _capitalize_process_word(word):
    """Capitalizes, removes namespaces and removes underscores from a word.

    This function changes the case of the first character to upper case.
    Manual upper casing is preferred compared to the builtin function
    str.capitalize() because we want to change only the case of the first
    character and ignore the case of other characters. After upper casing,
    all namespaces and underscores are removed from the string.

    Args:
        word: A string literal to capitalize and process.

    Returns:
        Returns a string that can be used in dcid generation.
        Returns None if the string is empty.
    """
    if word:
        word = word[word.find(':') + 1:]
        word = word.replace('_', '')
        word = word[0].upper() + word[1:]
        return word
    return None


def _generate_quantity_range_name(match_dict):
    """Generate a name for a quantity range.

    Args:
        match_dict: A dictionary containing quantity range regex groups.
          Expected syntax of match_dict is
          {
            'lower_limit': <value>,
            'upper_limit': <value>,
            'quantity': <value>
          }

    Returns:
        A string representing the quantity range name to be used in the dcid.
        Returns None if any of the expected keys are not in the dictionary.
    """
    try:
        lower_limit = match_dict['lower_limit']
        upper_limit = match_dict['upper_limit']
        quantity = match_dict['quantity']
    except KeyError:
        return None

    quantity = _capitalize_process_word(quantity)
    if upper_limit == '-':
        return f'{lower_limit}OrMore{quantity}'

    if lower_limit == '-':
        return f'{upper_limit}OrLess{quantity}'

    return f'{lower_limit}To{upper_limit}{quantity}'


def _generate_quantity_name(match_dict):
    """Generate a name for a quantity.

    Args:
        match_dict: A dictionary containing quantity regex groups.
          Expected syntax of match_dict
          {
            'value': <value>,
            'quantity': <value>
          }

    Returns:
        A string representing the quantity name to be used in the dcid.
        Returns None if any of the expected keys are not in the dictionary.
    """
    try:
        value = match_dict['value']
        quantity = match_dict['quantity']
    except KeyError:
        return None

    quantity = _capitalize_process_word(quantity)
    return f'{value}{quantity}'


def get_stat_var_dcid(stat_var_dict, ignore_props=None):
    """Generates the dcid given a statistical variable.

    Args:
        stat_var_dict: A dictionary with property: value of the statistical
          variable as key-value pairs.
        ignore_props: A list of properties to ignore from stat_var_dict when
          generating the dcid. This list of ignore_props will be added to the
          default set of properties that are ignored. The ignore_props can be
          used to account for dependent properties to ignore when generating
          the dcid. For example in the following statVar,
          {
            populationType: Person
            measuredProperty: count
            statType: measuredValue
            healthInsurance: NoHealthInsurance
            armedForceStatus: Civilian
            institutionalization: USC_NonInstitutionalized
          }
          since the healthInsurance property indicates they are Civilian and
          USC_NonInstitutionalized, ignore_props can be the list
          ['armedForceStatus', 'institutionalization']. During the dcid
          generation process, these properties will not be considered.

    Returns:
        A string representing the dcid of the statistical variable.
    """

    # TODO: Add support for naming boolean constraints
    # TODO: Stripping measurement properties (USC_) from constraints
    # TODO: Replacing NAICS industry codes with the NAICS names
    # TODO: Renaming cause of death properties
    # TODO: Renaming DEA drug names
    # TODO: Prepend or append text to some constraints to improve readability
    # TODO: InsuredUmemploymentRate should become Rate_Insured_Unemployment

    # Helper function to add a property to the dcid list.
    def add_prop_to_list(prop: str, svd: dict, dcid_list: list):
        if prop in svd:
            token = _capitalize_process_word(svd[prop])
            if token is not None:
                dcid_list.append(token)
            del svd[prop]

    dcid_list = list()
    denominator_suffix = ''
    svd = copy.deepcopy(stat_var_dict)

    if ignore_props is None:
        ig_p = _DEFAULT_IGNORE_PROPS
    else:
        ig_p = copy.deepcopy(ignore_props)
        ig_p.extend(_DEFAULT_IGNORE_PROPS)

    for prop in ig_p:
        if prop in svd:
            del svd[prop]

    if 'measurementDenominator' in svd:
        denominator_suffix = 'AsAFractionOf_' + svd['measurementDenominator']
        del svd['measurementDenominator']

    add_prop_to_list('measurementQualifier', svd, dcid_list)

    if ('statType' in svd) and (svd['statType'].find("measuredValue") == -1):
        token = svd['statType']
        # Removing suffix 'Value' from statTypes
        svd['statType'] = token[:token.find("Value")]
        add_prop_to_list('statType', svd, dcid_list)
    else:
        del svd['statType']

    add_prop_to_list('measuredProperty', svd, dcid_list)
    add_prop_to_list('populationType', svd, dcid_list)

    constraint_props = sorted(svd.keys(), key=str.casefold)
    for prop in constraint_props:
        match1 = _QUANTITY_RANGE_REGEX_1.match(svd[prop])
        match2 = _QUANTITY_RANGE_REGEX_2.match(svd[prop])
        if match1 or match2:
            m_dict = match1.groupdict() if match1 else match2.groupdict()
            q_name = _generate_quantity_range_name(m_dict)
            dcid_list.append(q_name)
        else:
            match1 = _QUANTITY_REGEX_1.match(svd[prop])
            match2 = _QUANTITY_REGEX_2.match(svd[prop])
            if match1 or match2:
                m_dict = match1.groupdict() if match1 else match2.groupdict()
                q_name = _generate_quantity_name(m_dict)
                dcid_list.append(q_name)
            else:
                add_prop_to_list(prop, svd, dcid_list)

    if denominator_suffix:
        dcid_list.append(denominator_suffix)

    dcid = '_'.join(dcid_list)
    return dcid
