# Copyright 2020 Google LLC
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
"""Contains helper functions required by both clean.py and generate_mcf.py"""

import re


def get_qty_format(strength):
    """Returns a quantity format [# UNIT] of a given strength
    """
    strength = strength.strip()
    if strength == 'N/A':
        return '"N/A"'
    if 'N/A' in strength:
        #print(strength)
        return '"' + strength + '"'
    split_list = list(filter(None, re.split(r'(\d*[.,]?\d+)', strength)))
    if len(split_list) < 2:
        return '"' + strength + '"'
    return '[' + split_list[0] + ' ' + "".join(split_list[1:]).strip().replace(
        ' ', '_') + ']'


def get_qty_range_format(strength):
    """Retruns the quantity range format [# # UNIT] for a given strength.
    """
    split_list = list(filter(None, re.split(r'(\d*[.]?\d+)', strength)))
    first_val = split_list[0]
    second_val = ''
    units = ''.join(split_list[1:])
    for index, item in enumerate(split_list[1:]):
        if re.fullmatch(r'(\d*[.]?\d+)', item):
            second_val = item + ' '
            units = "".join(split_list[index + 2:])
            break
    return '[' + first_val + ' ' + second_val + units.strip() + ']'
