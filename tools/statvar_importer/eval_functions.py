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
"""Utility functions for eval statements with PropertyValueMapper.

The functions can be invoked within '#Eval' in the pv_map.py.
For Example, for format values in 'DateTime' column into ISO-8601 format:
'DateTime': {
  '#Eval': 'observationDate=format_date("{Data}")',
 }
"""

import datetime
from datetime import datetime
import os
import re
import sys

from absl import logging
import dateutil
from dateutil import parser
from dateutil.relativedelta import relativedelta

# String utility functions


def format_date(date_str: str, format_str: str = '%Y-%m-%d') -> str:
    """Parse the date string and return formated date string.

  Args:
    date_str: Input date string to be parsed.
    format_str: output format for date

  Returns:
    date formatted by the format_str.
    In case of parse error, returns the original date_str.
  Raises
    NameError in case of any exceptions in parsing.
    This will cause any Eval using it to fail.
  """
    try:
        return dateutil.parser.parse(date_str).strftime(format_str)
    except dateutil.parser._parser.ParserError:
        return ''


def str_to_camel_case(input_string: str,
                      strip_re: str = r'[^A-Za-z_0-9]') -> str:
    """Returns the string in CamelCase without spaces and special characters.

  Example: "Abc-def(HG-123)" -> "AbcDefHG".

  Args:
    input_string: string to be converted to CamelCase
    strip_chars: regular expression of characters to be removed.

  Returns:
    string with non-alpha characters removed and remaining words capitalized.
  """
    if not str:
        return ''
    if not isinstance(input_string, str):
        input_string = str(input_string)
    # Replace any non-alpha characters with space
    clean_str = re.sub(strip_re, ' ', input_string)
    clean_str = clean_str.strip()
    # Split by space and capitalize first letter, preserving any other capitals
    return ''.join(
        [w[0].upper() + w[1:] for w in clean_str.split(' ') if len(w) > 0])


EVAL_GLOBALS = {
    # Date time functions
    'dateutil_parser_parse': dateutil.parser.parse,
    'format_date': format_date,
    'datetime': datetime,
    'datetime_strptime': datetime.strptime,
    'relativedelta': relativedelta,
    # String functions
    'str_to_camel_case': str_to_camel_case,
    # Regex functions
    're': re,
    're_sub': re.sub,
}


def evaluate_statement(eval_str: str,
                       variables: dict = {},
                       functions: dict = EVAL_GLOBALS) -> (str, str):
    """Returns the tuple: (variable, result) after evaluating statement in eval.

   Args:
     eval_str: string with statement to be evaluated of the form:
       'variable=statement' if the variable is not specified, an empty string is
       retured as variable.
      variables: dictionary of variables and values to be used in statement.
      functions: dictionary of global functoins that can be invoked within
        statement.

  Returns:
      tuple of the (variable , result) after evaluating the statement.
      in case of exception during eval, None is returned as result
  """
    variable = ''
    statement = eval_str
    if '=' in eval_str:
        variable, statement = eval_str.split('=', 1)
    variable = variable.strip()
    try:
        result = eval(statement, functions, variables)
    except (SyntaxError, NameError, ValueError, TypeError) as e:
        logging.debug(
            f'Failed to evaluate: {variable}={statement}, {e} in {variables}')
        result = None
    return (variable, result)
