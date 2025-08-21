# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility functions for proerty:values."""

import os
import re
import sys

from typing import Union

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

from mcf_file_util import get_value_list, add_pv_to_node, strip_namespace


def is_valid_property(prop: str, schemaless: bool = False) -> bool:
    """Returns True if the property begins with a letter, lowercase.

  If schemaless is true, property can begin with uppercase as well.
  """
    if prop and isinstance(prop, str) and prop[0].isalpha():
        if schemaless or prop[0].islower():
            return True
    return False


def is_valid_value(value: str) -> bool:
    """Returns True if the value is valid without any references."""
    if value is None:
        return False
    if isinstance(value, str):
        # Check there are no unresolved references.
        if not value or value == '""':
            return False
        if '@' in value:
            # Quoted strings can have @<2-letter-lang> suffix.
            if not re.search('@[a-z]{2}"$', value):
                return False
        if '{' in value and '}' in value:
            return False
    return True


def is_schema_node(value: str) -> bool:
    """Returns True if the value is a schema node reference."""
    if not value or not isinstance(value, str):
        return False
    if not value[0].isalpha() and value[0] != '[':
        # Numbers or quoted strings are not schema nodes.
        return False
    # Check if string has any non alpha or non numeric codes
    non_alnum_chars = [
        c for c in strip_namespace(value)
        if not c.isalnum() and c not in ['_', '/', '[', ']', '.']
    ]
    if non_alnum_chars:
        return False
    return True


def has_namespace(value: str) -> bool:
    """Returns True if the value has a namespace of letters followed by ':'."""
    if not value or not isinstance(value, str):
        return False
    len_value = len(value)
    pos = 0
    while pos < len_value:
        if not value[pos].isalpha():
            break
        pos += 1
    if pos < len_value and value[pos] == ':':
        return True
    return False


def add_key_value(
    key: str,
    value: str,
    pvs: dict,
    multi_value_keys: set = {},
    overwrite: bool = True,
    normalize: bool = True,
) -> dict:
    """Adds a key:value to the dict.

  If the key already exists, adds value to a list if key is a multi_value key,
  else replaces the value if overwrite is True.
  """
    append_value = False
    if key in multi_value_keys:
        append_value = True
    if not append_value and not overwrite and key in pvs:
        # Do not add value if one exists and overwrite and append is disabled.
        return pvs
    return add_pv_to_node(key,
                          value,
                          pvs,
                          append_value=append_value,
                          normalize=normalize)


def get_value_as_list(value: str) -> Union[str, list]:
    """Returns the value as a list or string."""
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value:
        if "," in value:
            # Get a list of unique values
            values = set()
            values.update(get_value_list(value))
            value_list = list(values)
            if len(value_list) == 1:
                return value_list[0]
            return value_list
    return value


def pvs_update(new_pvs: dict, pvs: dict, multi_value_keys: set = {}) -> dict:
    """Add the key:value pairs from the new_pvs into the pvs dictionary."""
    for prop, value in new_pvs.items():
        add_key_value(prop,
                      value,
                      pvs,
                      multi_value_keys=multi_value_keys,
                      normalize=False)
    return pvs


def get_words(value: str, word_delimiter: str) -> list:
    """Returns the list of non-empty words separated by the delimiter."""
    return [w for w in re.split(word_delimiter, value) if w]


def get_delimiter_char(re_delimiter: str) -> str:
    """Returns a single delimiter character that can be used to join words

  from the first character in the delimiter regex.
  """
    if re_delimiter:
        if '|' in re_delimiter:
            return re_delimiter.split('|')[0]
        if re_delimiter[0] == '[':
            return re_delimiter[1]
    return ' '
