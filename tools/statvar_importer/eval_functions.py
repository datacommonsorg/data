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
"""A collection of utility functions for dynamically evaluating expressions.

This module provides a set of functions that can be used within `eval()`
statements, primarily for data transformation tasks in a property-value
mapping context. It offers a safe and convenient way to perform common
operations like date formatting and string manipulation.

The core function is `evaluate_statement`, which serves as a secure wrapper
around Python's built-in `eval()`. This function is designed to execute simple
expressions, optionally assigning the result to a variable.

The module also includes helper functions for common data transformations:
- `format_date`: Parses and formats date strings.
- `str_to_camel_case`: Converts strings to CamelCase.

These utilities can be invoked within a configuration that uses `#Eval` directives
for data processing. For example, to format a 'DateTime' column into ISO-8601
format, you could use:

'DateTime': {
  '#Eval': 'observationDate = format_date("{Data}")',
}
"""

from datetime import datetime
import re

from absl import logging
import dateutil
from dateutil import parser
from dateutil.relativedelta import relativedelta

# String utility functions


def format_date(date_str: str, format_str: str = '%Y-%m-%d') -> str:
    """Parses a date string and returns it in a specified format.

    This function uses `dateutil.parser.parse` to convert a date string into a
    datetime object, which is then formatted into a string.

    Args:
        date_str: The input date string to be parsed (e.g., 'Jan 31, 2023',
          '2022/01/31').
        format_str: The desired output format for the date, using standard
          strftime codes (e.g., '%Y-%m-%d', '%B %d, %Y').

    Returns:
        The date formatted as a string according to `format_str`. If parsing
        fails (e.g., for an invalid date string), it returns an empty string.

    Examples:
        >>> format_date('Jan 31, 2023')
        '2023-01-31'
        >>> format_date('2022, Jan 1st', '%Y-%m')
        '2022-01'
        >>> format_date('Not a valid date')
        ''
    """
    try:
        return dateutil.parser.parse(date_str).strftime(format_str)
    except dateutil.parser._parser.ParserError:
        return ''


def str_to_camel_case(input_string: str,
                      strip_re: str = r'[^A-Za-z_0-9]') -> str:
    """Converts a string to CamelCase, removing specified characters.

    This function cleans a string by removing characters that match the
    `strip_re` pattern, then converts the remaining parts into CamelCase.

    Args:
        input_string: The string to be converted.
        strip_re: A regular expression of characters to be removed. The
          default pattern removes any character that is not a letter, number, or
          underscore.

    Returns:
        A string in CamelCase.

    Examples:
        >>> str_to_camel_case("Abc-def(HG)")
        'AbcDefHg'
        >>> str_to_camel_case("my_variable_name", r"[^A-Za-z]")
        'MyVariableName'
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


# A dictionary of functions and modules that are safe to use in `eval()`.
# This dictionary acts as a safelist, defining the execution environment for
# the `evaluate_statement` function. By controlling the available globals,
# we can prevent the execution of arbitrary or unsafe code.
EVAL_GLOBALS = {
    # Date time functions:
    # - `dateutil.parser.parse`: For flexible date string parsing.
    # - `format_date`: Custom function to format dates.
    # - `datetime`: The datetime class from the datetime module.
    # - `datetime.strptime`: For parsing dates with a specific format.
    # - `relativedelta`: For date calculations.
    'dateutil_parser_parse': dateutil.parser.parse,
    'format_date': format_date,
    'datetime': datetime,
    'datetime_strptime': datetime.strptime,
    'relativedelta': relativedelta,

    # String functions:
    # - `str_to_camel_case`: Custom function for string case conversion.
    'str_to_camel_case': str_to_camel_case,

    # Regex functions:
    # - `re`: The 're' module for regular expression operations.
    # - `re.sub`: The 'sub' function for string substitution.
    're': re,
    're_sub': re.sub,
}


def evaluate_statement(eval_str: str,
                       variables: dict = {},
                       functions: dict = EVAL_GLOBALS) -> (str, str):
    """Evaluates a Python expression and returns the result.

    This function is a safe wrapper around Python's `eval()` built-in. It
    is designed to execute simple expressions, often used for data
    transformations. The expression can optionally assign a value to a
    variable.

    Args:
        eval_str: The string containing the expression to be evaluated, in the
          format 'variable = statement' or just 'statement'.
        variables: A dictionary of variables and their values that are
          accessible within the `eval()` context.
        functions: A dictionary of functions that are accessible within the
          `eval()` context. Defaults to `EVAL_GLOBALS`.

    Returns:
        A tuple containing the variable name and the result of the evaluation.
        - If `eval_str` includes a variable assignment, the tuple will be
          (`variable_name`, `result`).
        - If `eval_str` is a simple statement, the tuple will be
          ('', `result`).
        - If the evaluation raises a `SyntaxError`, `NameError`, `ValueError`,
          or `TypeError`, the result will be `None`.

    Examples:
        >>> # Simple arithmetic
        >>> evaluate_statement('num = 1 + x', {'x': 2})
        ('num', 3)
        >>> # Using a function from EVAL_GLOBALS
        >>> evaluate_statement('date = format_date(data)', {'data': '2022, Jan 1st'})
        ('date', '2022-01-01')
        >>> # Statement without a variable
        >>> evaluate_statement('2 * 2')
        ('', 4)
        >>> # Invalid expression
        >>> evaluate_statement('name = 1 + "2"')
        ('name', None)
    """
    variable = ''
    statement = eval_str
    if '=' in eval_str:
        variable, statement = eval_str.split('=', 1)
    variable = variable.strip()
    try:
        result = eval(statement, functions, variables)
    except Exception as e:
        logging.debug(
            f'Failed to evaluate: {variable}={statement}, {e} in {variables}')
        result = None
    return (variable, result)
