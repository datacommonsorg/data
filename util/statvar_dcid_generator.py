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
"""A general class to generate dcid for statistical variables."""

import copy
import re


class StatVarDcidGenerator:
    """Helper class to generate dcid for a statistical variable."""
    def __init__(self, stat_type_lookup=None, ignore_props=None):
        if stat_type_lookup is None:
            self.STAT_TYPE_LOOKUP = {
                'meanValue': 'Mean',
                'medianValue': 'Median'
            }
        else:
            self.STAT_TYPE_LOOKUP = stat_type_lookup

        if ignore_props is None:
            self.IGNORE_PROPS = ['unit', 'Node', 'memberOf', 'typeOf']
        else:
            self.IGNORE_PROPS = ignore_props

        self.quantity_regex = '\[(-|\d+(\.\d+)?) [a-zA-Z]+\]'
        self.quantity_range_regex = '\[(-|\d+(\.\d+)?) (-|\d+(\.\d+)?) [a-zA-Z]+\]'

    def _capitalize_word(self, word):
        """Changes the first letter of a word to upper case."""
        if (len(word) != 0):
            return (word[0].upper() + word[1:])
        else:
            return None

    def _generate_quantity_range_name(self, s):
        """Generate a name for a quantity range.

        Expected syntax of s - [<lower_limit> <upper_limit> <quantity>]
        """
        str_list = s.split()

        lower_limit = str_list[0][1:]
        upper_limit = str_list[1]
        quantity = str_list[2][:-1]

        quantity = self._capitalize_word(quantity)
        if (upper_limit == '-'):
            return f"{lower_limit}OrMore{quantity}"
        elif (lower_limit == '-'):
            return f"{upper_limit}OrLess{quantity}"
        else:
            return f"{lower_limit}To{upper_limit}{quantity}"

    def _generate_quantity_name(self, s):
        """Generate a name for a quantity.

        Expected syntax of s- [<value> <quantity>]
        """
        str_list = s.split()

        value = str_list[0][1:]
        quantity = str_list[1][:-1]

        quantity = self._capitalize_word(quantity)
        return f"{value}{quantity}"

    def get_stat_var_dcid(self, stat_var_dict, ignore_props=None):
        """Generates the dcid given a statistical variable.
        
        Arguments:
        stat_var_dict -- A dictionary with property:values of the statistical variable as key-value pairs
        ignore_props -- A list of properties to ignore from stat_var_dict when generating the dcid

        The ignore_props can be used to account for dependent PVs which we want 
        to ignore when generating the dcid.
        For example in the following statVar,
        {
            populationType: Person
            measuredProperty: count
            statType: measuredValue
            healthInsurance: NoHealthInsurance
            armedForceStatus: Civilian
            institutionalization: USC_NonInstitutionalized
        }
        Since the healthInsurance property indicates they are Civilian and
        USC_NonInstitutionalized, ignore_props can be the list
        ['armedForceStatus', 'institutionalization']. During the dcid 
        generation process, these PVs will not be considered.
        """
        #TODO: Account for dependent PVs automatically
        #TODO: Add support for naming boolean constraints
        #TODO: Stripping measurement properties (USC_) from constraints
        #TODO: Replacing NAICS industry codes with the NAICS names
        #TODO: Renaming cause of death properties
        #TODO: Renaming DEA drug names
        #TODO: Prepend or append text to some constraints to improve readability
        #TODO: InsuredUmemploymentRate should become Rate_Insured_Unemployment

        dcid_list = list()
        has_denominator = False
        svd = copy.deepcopy(stat_var_dict)

        if ignore_props is None:
            ignore_props = self.IGNORE_PROPS

        for prop in ignore_props:
            if prop in svd:
                del svd[prop]

        if 'measurementDenominator' in svd:
            has_denominator = True
            denominator_suffix = 'AsAFractionOf_' + svd[
                'measurementDenominator']
            del svd['measurementDenominator']

        if 'measurementQualifier' in svd:
            token = self._capitalize_word(svd['measurementQualifier'])
            dcid_list.append(token)
            del svd['measurementQualifier']

        if (svd['statType'] not in ['measuredValue', 'Unknown']):
            if svd['statType'] in self.STAT_TYPE_LOOKUP:
                dcid_list.append(self.STAT_TYPE_LOOKUP[svd['statType']])
            else:
                token = self._capitalize_word(svd['statType'])
                dcid_list.append(token)

        del svd['statType']

        token = self._capitalize_word(svd['measuredProperty'])
        dcid_list.append(token)
        del svd['measuredProperty']

        token = self._capitalize_word(svd['populationType'])
        dcid_list.append(token)
        del svd['populationType']

        constraint_props = sorted(svd.keys(), key=str.casefold)
        for prop in constraint_props:
            if re.match(self.quantity_range_regex, svd[prop]):
                q_name = self._generate_quantity_range_name(svd[prop])
                dcid_list.append(q_name)

            elif re.match(self.quantity_regex, svd[prop]):
                q_name = self._generate_quantity_name(svd[prop])
                dcid_list.append(q_name)

            else:
                token = self._capitalize_word(svd[prop])
                dcid_list.append(token)

        if (has_denominator):
            dcid_list.append(denominator_suffix)

        dcid = '_'.join(dcid_list)
        return dcid
