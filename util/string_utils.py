# Copyright 2022 Google LLC
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
"""String utilities."""

import csv


def str_to_list(value: str) -> list:
    """Returns the value as a list

  Args:
    value: string with a single value or comma seperated list of values

  Returns:
    value as a list.
  """
    if isinstance(value, list):
        return value
    value_list = []
    # Read the string as a comma separated line.
    is_quoted = '"' in value
    try:
        if is_quoted and "," in value:
            # Read the string as a quoted comma separated line.
            row = list(
                csv.reader([value],
                           delimiter=',',
                           quotechar='"',
                           skipinitialspace=True))[0]
        else:
            # Without " quotes, the line can be split on commas.
            # Avoiding csv reader calls for performance.
            row = value.split(',')
        for v in row:
            val_normalized = to_quoted_string(v, is_quoted=is_quoted)
            value_list.append(val_normalized)
    except csv.Error:
        logging.error(
            f'Too large value {len(value)}, failed to convert to list')
        value_list = [value]
    return value_list

def to_quoted_string(value: str, is_quoted: bool = None) -> str:
    """Returns a quoted string if there are spaces and special characters.

  Args:
    value: string value to be quoted if necessary.
    is_quoted: if True, returns values as quotes strings.

  Returns:
    value with optional double quotes.
  """
    if not value or not isinstance(value, str):
        return value

    value = value.strip('"')
    value = value.strip()
    if value.startswith('[') and value.endswith(']'):
        return normalize_range(value)
    if value and (' ' in value or ',' in value or is_quoted):
        if value and value[0] != '"':
            return '"' + value + '"'
    return value


