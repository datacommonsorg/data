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
"""Unit tests for eval_functions.py."""

import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))

import eval_functions

# module_dir_ is the path to where this test is running from.
_module_dir_ = os.path.dirname(__file__)


class TestEvaluateStatement(unittest.TestCase):

    def test_evaluate_statement_with_variable(self):
        self.assertEqual(
            ('num', 3),
            eval_functions.evaluate_statement('num=1+Number', {'Number': 2}),
        )

    def test_evaluate_statement_without_variable(self):
        self.assertEqual(
            ('', 4), eval_functions.evaluate_statement('2*Number',
                                                       {'Number': 2}))

    def test_evaluate_statement_with_type_error(self):
        # Verify None is returned on error in statement
        self.assertEqual(
            ('name', None),
            eval_functions.evaluate_statement(
                'name=1+Data',
                {'Data': '2'}  # string should raise TypeError
            ),
        )

    def test_evaluate_statement_with_name_error(self):
        # Missing variable value for Data raises NameError
        self.assertEqual(('name', None),
                         eval_functions.evaluate_statement('name=1+Data'))

    def test_evaluate_statement_with_syntax_error(self):
        self.assertEqual(('var', None),
                         eval_functions.evaluate_statement('var=1+'))

    def test_evaluate_statement_with_eval_globals(self):
        self.assertEqual(
            ('date', '2022-01-01'),
            eval_functions.evaluate_statement('date=format_date(Data)',
                                              {'Data': '2022, Jan 1st'}))

    def test_evaluate_statement_with_spaces_around_equals(self):
        self.assertEqual(
            ('num', 3),
            eval_functions.evaluate_statement('num = 1 + Number',
                                              {'Number': 2}))

    def test_evaluate_statement_with_index_error(self):
        self.assertEqual(
            ('val', None),
            eval_functions.evaluate_statement('val = "abc"[5]', {}))


class TestFormatDate(unittest.TestCase):

    def test_format_date_with_valid_date(self):
        self.assertEqual('2023-01-31',
                         eval_functions.format_date('Jan 31, 2023'))

    def test_format_date_with_custom_format(self):
        self.assertEqual('2022-01',
                         eval_functions.format_date('2022, Jan 1st', '%Y-%m'))

    def test_format_date_with_datetime(self):
        self.assertEqual('2022-12-31',
                         eval_functions.format_date('Dec 31st, 2022, 10:00am'))

    def test_format_date_with_invalid_date(self):
        self.assertEqual('', eval_functions.format_date('Not A Date'))

    def test_format_date_with_empty_string(self):
        self.assertEqual('', eval_functions.format_date(''))


class TestStrToCamelCase(unittest.TestCase):

    def test_str_to_camel_case_with_hyphens_and_spaces(self):
        self.assertEqual('CamelCase123',
                         eval_functions.str_to_camel_case(' camel-case 123 '))

    def test_str_to_camel_case_with_dots_and_spaces(self):
        self.assertEqual('10MyDCID',
                         eval_functions.str_to_camel_case('1.0 my DCID'))

    def test_str_to_camel_case_with_parentheses_and_dots(self):
        self.assertEqual(
            'SnakeCaseString',
            eval_functions.str_to_camel_case('snake(case.) string'))

    def test_str_to_camel_case_with_custom_regex(self):
        self.assertEqual(
            'String_Value1',
            eval_functions.str_to_camel_case('string_ value(1)',
                                             r'[^A-Za-z0-9_]'))

    def test_str_to_camel_case_with_empty_string(self):
        self.assertEqual('', eval_functions.str_to_camel_case(''))

    def test_str_to_camel_case_with_non_string_input(self):
        self.assertEqual('123', eval_functions.str_to_camel_case(123))

    def test_str_to_camel_case_with_special_characters(self):
        self.assertEqual('', eval_functions.str_to_camel_case('@#$%^&*'))

    def test_str_to_camel_case_idempotent(self):
        self.assertEqual('AlreadyCamel',
                         eval_functions.str_to_camel_case('AlreadyCamel'))


if __name__ == '__main__':
    unittest.main()
