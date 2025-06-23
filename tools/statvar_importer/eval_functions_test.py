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


class TestEvalFunctions(unittest.TestCase):

    def test_evaluate_statement(self):
        self.assertEqual(
            ('num', 3),
            eval_functions.evaluate_statement('num=1+Number', {'Number': 2}),
        )
        self.assertEqual(
            ('', 4), eval_functions.evaluate_statement('2*Number',
                                                       {'Number': 2}))
        # Verify None is returned on error in statement
        self.assertEqual(
            ('name', None),
            eval_functions.evaluate_statement(
                'name=1+Data',
                {'Data': '2'}  # string should raise TypeError
            ),
        )
        # Missing variable value for Data raises NameError
        self.assertEqual(('name', None),
                         eval_functions.evaluate_statement('name=1+Data'))

    def test_format_date(self):
        self.assertEqual('2023-01-31',
                         eval_functions.format_date('Jan 31, 2023'))
        self.assertEqual(
            ('month', '2022-01'),
            eval_functions.evaluate_statement(
                'month=format_date(Data, "%Y-%m")', {'Data': '2022, Jan 1st'}),
        )
        self.assertEqual(
            ('', '2022-12-31'),
            eval_functions.evaluate_statement(
                'format_date(Data)', {'Data': 'Dec 31st, 2022, 10:00am'}),
        )
        self.assertEqual(
            ('', ''),
            eval_functions.evaluate_statement('format_date("SunMonTue")'),
        )

    def test_str_to_camel_case(self):
        self.assertEqual('CamelCase123',
                         eval_functions.str_to_camel_case(' camel-case 123 '))
        self.assertEqual(
            ('name', '10MyDCID'),
            eval_functions.evaluate_statement('name=str_to_camel_case(Data)',
                                              {'Data': '1.0 my DCID'}),
        )
        self.assertEqual(
            ('', 'SnakeCaseString'),
            eval_functions.evaluate_statement('str_to_camel_case(Data)',
                                              {'Data': 'snake(case.) string'}),
        )
        self.assertEqual(
            ('', 'String_Value1'),
            eval_functions.evaluate_statement(
                'str_to_camel_case(Data, r"[^A-Za-z0-9_]")',
                {'Data': 'string_ value(1)'},
            ),
        )
