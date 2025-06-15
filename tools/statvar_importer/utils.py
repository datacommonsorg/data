# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility functions for the StatVar importer.

This module provides helper functions used across the StatVar import process.
"""

from typing import Union, Optional, Dict, List


def _capitalize_first_char(string: str) -> str:
    """Capitalizes the first character of a string.

    If the input is not a string, or is an empty string, it's returned as is.

    Args:
        string: The input string.

    Returns:
        The string with its first character capitalized, or the original input
        if it cannot be capitalized.

    Examples:
        >>> _capitalize_first_char("hello")
        'Hello'
        >>> _capitalize_first_char("World")
        'World'
        >>> _capitalize_first_char("")
        ''
        >>> _capitalize_first_char("1st")
        '1st'
        >>> _capitalize_first_char(None)

    """
    if not string or not isinstance(string, str):
        return string
    return string[0].upper() + string[1:]


def _str_from_number(number: Union[int, float],
                     precision_digits: Optional[int] = None) -> str:
    """Converts a number (int or float) to its string representation.

    Integers and floats that are whole numbers (e.g., 10.0) are returned as
    integer strings (e.g., "10").
    Floats are rounded to the specified number of precision digits if provided.

    Args:
        number: The number to convert.
        precision_digits: Optional number of decimal places to round a float to.

    Returns:
        The string representation of the number.

    Examples:
        >>> _str_from_number(123)
        '123'
        >>> _str_from_number(123.0)
        '123'
        >>> _str_from_number(123.456)
        '123.456'
        >>> _str_from_number(123.456, precision_digits=2)
        '123.46'
        >>> _str_from_number(123.451, precision_digits=2)
        '123.45'
    """
    # Check if number is an integer or float without any decimals.
    if int(number) == number:
        number_int = int(number)
        return f'{number_int}'
    # Return float rounded to precision digits.
    if precision_digits is not None:
        number = round(number, precision_digits)
    return f'{number}'


def _pvs_has_any_prop(pvs: Optional[Dict[str, any]],
                      columns: Optional[List[str]] = None) -> bool:
    """Checks if a dictionary of Property-Values (PVs) contains any of the specified columns (properties).

    This function iterates through the provided PVs dictionary and checks if any of its
    keys (properties) are present in the `columns` list and have a non-empty value.

    Args:
        pvs: A dictionary where keys are properties and values are their corresponding values.
        columns: A list of column names (properties) to check for in the PVs.

    Returns:
        True if any property in `pvs` is also in `columns` and has a truthy value,
        False otherwise.

    Examples:
        >>> _pvs_has_any_prop({'name': 'Test', 'age': 30}, ['age', 'city'])
        True
        >>> _pvs_has_any_prop({'name': 'Test', 'age': None}, ['age'])
        False
        >>> _pvs_has_any_prop({'name': 'Test'}, ['city'])
        False
        >>> _pvs_has_any_prop({}, ['name'])
        False
        >>> _pvs_has_any_prop(None, ['name'])
        False
        >>> _pvs_has_any_prop({'name': 'Test'}, None)
        False
    """
    if pvs and columns:
        for prop, value in pvs.items():
            if value and prop in columns:
                return True
    return False


def _is_place_dcid(place: str) -> bool:
    """Returns True if the place string is a valid DCID pattern.

    Examples:
        >>> _is_place_dcid("dcid:country/USA")
        True
        >>> _is_place_dcid("dcs:country/USA")
        True
        >>> _is_place_dcid("country/USA")
        True
        >>> _is_place_dcid("geoId/06")
        True
        >>> _is_place_dcid("dc/g/Establishment_School")
        True
        >>> _is_place_dcid("dcid:Person") 
        True
        >>> _is_place_dcid("countryUSA")
        False
        >>> _is_place_dcid("dcid:country/USA extra") 
        False
        >>> _is_place_dcid("dcid:!@#")
        False
        >>> _is_place_dcid("")
        False
        >>> _is_place_dcid(None)
        False
        >>> _is_place_dcid("dcid:")
        False
        >>> _is_place_dcid("dcs:")
        False
        >>> _is_place_dcid("country/")
        False
        >>> _is_place_dcid("/USA")
        False
        >>> _is_place_dcid("dcid//USA") # Double slash
        False
        >>> _is_place_dcid("dcid:country//USA") # Double slash after prefix
        False
    """
    if not place or not isinstance(place, str):
        return False

    original_place_str = place
    has_prefix = False

    if place.startswith('dcid:'):
        place_to_check = place[5:]
        has_prefix = True
    elif place.startswith('dcs:'):
        place_to_check = place[4:]
        has_prefix = True
    else:
        place_to_check = place

    if not place_to_check:  # Handles "dcid:", "dcs:", or empty string if it was initially empty
        return False

    # Core validation for the part after prefix (or the whole string if no prefix)
    if place_to_check.startswith('/') or place_to_check.endswith('/'):
        return False
    if '//' in place_to_check:  # Check for consecutive slashes
        return False

    contains_slash_internally = False
    for char_code in [ord(c) for c in place_to_check]:
        is_alnum = ((char_code >= ord('a') and char_code <= ord('z')) or
                    (char_code >= ord('A') and char_code <= ord('Z')) or
                    (char_code >= ord('0') and char_code <= ord('9')))
        is_allowed_symbol = (char_code == ord('_') or char_code == ord('/'))

        if not (is_alnum or is_allowed_symbol):
            return False  # Invalid character
        if char_code == ord('/'):
            contains_slash_internally = True

    if not has_prefix:
        # For non-prefixed DCIDs, an internal slash is mandatory
        return contains_slash_internally

    # For prefixed DCIDs, all checks on place_to_check have passed
    return True
