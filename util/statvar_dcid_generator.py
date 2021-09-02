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

#Constants
_QUANTITY_REGEX = r"\[(?P<value>-|-?\d+(\.\d+)?) (?P<quantity>[A-Za-z]+)\]"
_QUANTITY_RANGE_REGEX = (r"\[(?P<lower_limit>-|-?\d+(\.\d+)?) "
                         r"(?P<upper_limit>-|-?\d+(\.\d+)?) "
                         r"(?P<quantity>[A-Za-z]+)\]")

# This is a lookup to ensure "Mean" and "Median" are used in the dcid when
# statType is meanValue or medianValue"
_stat_type_lookup = {"meanValue": "Mean", "medianValue": "Median"}

# These properties are ignored during dcid generation
_ignore_props = {"unit", "Node", "memberOf", "typeOf"}


def capitalize_word(word):
    """Capitalizes the first character of a string.

    This function differs from the builtin function str.capitalize() in that it
    changes only the case of the first character and ignores the case of other
    characters.
    """
    if word:
        return word[0].upper() + word[1:]
    return None


def generate_quantity_range_name(match_dict):
    """Generate a name for a quantity range.

    Args:
        match_dict: A dictionary containing quantity range regex groups.
          Expected syntax of match_dict is
          {
            "lower_limit": <value>,
            "upper_limit": <value>,
            "quantity": <value>
          }

    Returns:
        A string representing the quantity range name to be used in the dcid.
    """
    lower_limit = match_dict["lower_limit"]
    upper_limit = match_dict["upper_limit"]
    quantity = match_dict["quantity"]

    quantity = capitalize_word(quantity)
    if upper_limit == "-":
        return f"{lower_limit}OrMore{quantity}"

    if lower_limit == "-":
        return f"{upper_limit}OrLess{quantity}"

    return f"{lower_limit}To{upper_limit}{quantity}"


def generate_quantity_name(match_dict):
    """Generate a name for a quantity.

    Args:
        match_dict: A dictionary containing quantity regex groups.
          Expected syntax of match_dict
          {
            "value": <value>,
            "quantity": <value>
          }

    Returns:
        A string representing the quantity name to be used in the dcid.
    """
    value = match_dict["value"]
    quantity = match_dict["quantity"]

    quantity = capitalize_word(quantity)
    return f"{value}{quantity}"


def get_stat_var_dcid(stat_var_dict, ignore_props=None):
    """Generates the dcid given a statistical variable.

    Args:
        stat_var_dict: A dictionary with property: values of the statistical
          variable as key-value pairs.
        ignore_props: A list of properties to ignore from stat_var_dict when
          generating the dcid. This list of ignore_props will be added to the
          default set of properties that are ignored. The ignore_props can be
          used to account for dependent PVs to ignore when generating the dcid.
          For example in the following statVar,
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
          ["armedForceStatus", "institutionalization"]. During the dcid
          generation process, these PVs will not be considered.

    Returns:
        A string represting the dcid of the statistical variable.
    """
    # TODO: Allow support for values with namespaces (dcs: , schema:, ...)
    # TODO: Add support for naming boolean constraints
    # TODO: Stripping measurement properties (USC_) from constraints
    # TODO: Replacing NAICS industry codes with the NAICS names
    # TODO: Renaming cause of death properties
    # TODO: Renaming DEA drug names
    # TODO: Prepend or append text to some constraints to improve readability
    # TODO: InsuredUmemploymentRate should become Rate_Insured_Unemployment

    dcid_list = list()
    denominator_suffix = ''
    svd = copy.deepcopy(stat_var_dict)

    if ignore_props is None:
        ignore_props = _ignore_props
    else:
        ignore_props.extend(_ignore_props)

    for prop in ignore_props:
        if prop in svd:
            del svd[prop]

    if "measurementDenominator" in svd:
        denominator_suffix = "AsAFractionOf_" + svd["measurementDenominator"]
        del svd["measurementDenominator"]

    if "measurementQualifier" in svd:
        token = capitalize_word(svd["measurementQualifier"])
        dcid_list.append(token)
        del svd["measurementQualifier"]

    if ("statType" in svd) and (svd["statType"]
                                not in ["measuredValue", "Unknown"]):
        if svd["statType"] in _stat_type_lookup:
            dcid_list.append(_stat_type_lookup[svd["statType"]])
        else:
            token = capitalize_word(svd["statType"])
            dcid_list.append(token)
    del svd["statType"]

    if "measuredProperty" in svd:
        token = capitalize_word(svd["measuredProperty"])
        dcid_list.append(token)
        del svd["measuredProperty"]

    if "populationType" in svd:
        token = capitalize_word(svd["populationType"])
        dcid_list.append(token)
        del svd["populationType"]

    constraint_props = sorted(svd.keys(), key=str.casefold)
    for prop in constraint_props:
        match = re.match(_QUANTITY_RANGE_REGEX, svd[prop])
        if match:
            q_name = generate_quantity_range_name(match.groupdict())
            dcid_list.append(q_name)

        else:
            match = re.match(_QUANTITY_REGEX, svd[prop])
            if match:
                q_name = generate_quantity_name(match.groupdict())
                dcid_list.append(q_name)

            else:
                token = capitalize_word(svd[prop])
                dcid_list.append(token)

    if denominator_suffix:
        dcid_list.append(denominator_suffix)

    dcid = "_".join(dcid_list)
    return dcid
