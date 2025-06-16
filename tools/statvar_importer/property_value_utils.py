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
    """Checks if a property is valid according to Data Commons standards.

    A valid property must:
    - Start with a letter.
    - Be in lowerCamelCase.

    If `schemaless` is True, the lowerCamelCase check is skipped, allowing
    properties that start with an uppercase letter.

    Args:
        prop: The property string to validate.
        schemaless: If True, allows properties that are not in lowerCamelCase.
                    Defaults to False.

    Returns:
        True if the property is valid, False otherwise.

    Examples:
        >>> is_valid_property("measuredProperty")
        True
        >>> is_valid_property("populationType")
        True
        >>> is_valid_property("Observation")  # Starts with an uppercase letter
        False
        >>> is_valid_property("Observation", schemaless=True)
        True
        >>> is_valid_property("_invalid")  # Does not start with a letter
        False
        >>> is_valid_property(None)
        False
    """
    if prop and isinstance(prop, str) and prop[0].isalpha():
        if schemaless or prop[0].islower():
            return True
    return False


def is_valid_value(value: str) -> bool:
    """Checks if a given value is valid and does not contain unresolved references.

    A valid value must not be None, an empty string, or contain unresolved
    '{...}' or '@...' references.

    Args:
        value: The value to validate.

    Returns:
        True if the value is valid, False otherwise.

    Examples:
        >>> is_valid_value("someValue")
        True
        >>> is_valid_value(123)
        True
        >>> is_valid_value(None)
        False
        >>> is_valid_value("")
        False
        >>> is_valid_value('"{unresolved}"')
        False
        >>> is_valid_value('@unresolved')
        False
    """
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
    """Checks if a value is a valid reference to a schema node.

    A valid schema node reference must:
    - Be a non-empty string.
    - Start with a letter or a '['.
    - Contain only alphanumeric characters, underscores, slashes, or brackets.

    Args:
        value: The value to check.

    Returns:
        True if the value is a valid schema node reference, False otherwise.

    Examples:
        >>> is_schema_node("schema:Person")
        True
        >>> is_schema_node("dcid:country/USA")
        True
        >>> is_schema_node("[1 2 3]")
        True
        >>> is_schema_node("invalid-node")
        False
        >>> is_schema_node(123)
        False
    """
    if not value or not isinstance(value, str):
        return False
    if value.startswith('[') and value.endswith(']'):
        return True
    if not value[0].isalpha():
        # Numbers or quoted strings are not schema nodes.
        return False
    # Check if string has any non alpha or non numeric codes
    non_alnum_chars = [
        c for c in strip_namespace(value)
        if not c.isalnum() and c not in ['_', '/', '.']
    ]
    if non_alnum_chars:
        return False
    return True


def has_namespace(value: str) -> bool:
    """Checks if a value has a Data Commons namespace prefix.

    A namespace prefix consists of one or more letters followed by a colon,
    for example, "dcid:", "schema:", or "dcs:".

    Args:
        value: The string value to check.

    Returns:
        True if the value has a valid namespace prefix, False otherwise.

    Examples:
        >>> has_namespace("dcid:country/USA")
        True
        >>> has_namespace("schema:Person")
        True
        >>> has_namespace("country/USA")
        False
        >>> has_namespace("dcid:")
        True
        >>> has_namespace(":no_namespace")
        False
        >>> has_namespace(None)
        False
    """
    if not value or not isinstance(value, str):
        return False
    len_value = len(value)
    pos = 0
    while pos < len_value:
        if not value[pos].isalpha():
            break
        pos += 1
    if pos > 0 and pos < len_value and value[pos] == ':':
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
        add_key_value(prop, value, pvs, multi_value_keys)
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
