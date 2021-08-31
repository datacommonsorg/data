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

import copy
import re


class StatVarDcidGenerator:
    """Helper class to generate dcid for a statistical variable."""
    STAT_TYPE_LOOKUP = {'meanValue': 'mean', 'medianValue': 'median'}

    def __init__(self):
        pass

    def capitalize_word(self, word):
        """Changes the first letter of a word to upper case."""
        if (len(word) != 0):
            return (word[0].upper() + word[1:])
        else:
            return None

    def append_to_dcid(self, dcid, value, end_underscore=False):
        """Append a value to a dcid."""
        dcid += self.capitalize_word(value)
        if (end_underscore == True):
            dcid += '_'

        return dcid

    def generate_quantity_range_name(self, s):
        """Generate a name for a quantity range.
        Expected syntax of s - [<lower_limit> <upper_limit> <quantity>]
        """
        str_list = s.split()

        lower_limit = str_list[0][1:]
        upper_limit = str_list[1]
        quantity = str_list[2][:-1]

        quantity = self.capitalize_word(quantity)
        if (upper_limit == '-'):
            return f"{lower_limit}OrMore{quantity}"
        elif (lower_limit == '-'):
            return f"{upper_limit}OrLess{quantity}"
        else:
            return f"{lower_limit}to{upper_limit}{quantity}"

    def generate_quantity_name(self, s):
        """Generate a name for a quantity.
        Expected syntax of s- [<value> <quantity>]
        """
        str_list = s.split()

        value = str_list[0][1:]
        quantity = str_list[1][:-1]

        quantity = self.capitalize_word(quantity)
        return f"{value}{quantity}"

    def get_stat_var_name(self, stat_var_dict, ignore_props=None):
        """Generates the dcid given a statistical variable
        
        Arguments:
        stat_var_dict -- A dictionary with property:values of the statistical variable as key-value pairs
        ignore_props -- A list of properties to ignore from stat_var_dict when generating the dcid
        """
        dcid = ''
        has_denominator = False
        svd = copy.deepcopy(stat_var_dict)

        if ignore_props is not None:
            for prop in ignore_props:
                del svd[prop]

        if 'measurementDenominator' in svd:
            has_denominator = True
            denominator_dcid = svd['measurementDenominator']
            del svd['measurementDenominator']

        if 'measurementQualifier' in svd:
            dcid = self.append_to_dcid(dcid,
                                       svd['measurementQualifier'],
                                       end_underscore=True)
            del svd['measurementQualifier']

        if (svd['statType'] != 'measuredValue'):
            if svd['statType'] in self.STAT_TYPE_LOOKUP:
                dcid = self.append_to_dcid(
                    dcid,
                    self.STAT_TYPE_LOOKUP[svd['statType']],
                    end_underscore=True)
            else:
                dcid = self.append_to_dcid(dcid,
                                           svd['statType'],
                                           end_underscore=True)
        del svd['statType']

        dcid = self.append_to_dcid(dcid,
                                   svd['measuredProperty'],
                                   end_underscore=True)
        del svd['measuredProperty']

        dcid = self.append_to_dcid(dcid,
                                   svd['populationType'],
                                   end_underscore=True)
        del svd['populationType']

        constraint_props = sorted(svd.keys(), key=str.casefold)
        for prop in constraint_props:
            if re.match('\[(-|\d(\.\d+)?) (-|\d(\.\d+)?) [a-zA-Z]+\]',
                        svd[prop]):  #quantity range
                q_name = self.generate_quantity_range_name(svd[prop])
                dcid = self.append_to_dcid(dcid, q_name, end_underscore=True)

            elif re.match('\[(-|\d(\.\d+)?) [a-zA-Z]+\]', svd[prop]):  #quantity
                q_name = self.generate_quantity_name(svd[prop])
                dcid = self.append_to_dcid(dcid, q_name, end_underscore=True)

            else:
                dcid = self.append_to_dcid(dcid, svd[prop], end_underscore=True)

        if (has_denominator):
            dcid += ('AsAFractionOf_' + denominator_dcid)
        else:
            dcid = dcid[:-1]  #Remove the last underscore

        return dcid
