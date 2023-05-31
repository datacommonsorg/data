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
'''Unit tests for json_to_csv.py'''

import json
import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import json_to_csv
import file_util

# module_dir_ is the path to where this test is running from.
_module_dir_ = os.path.dirname(__file__)


class TestEvalFunctions(unittest.TestCase):

    json_list = [{
        'key': 123,
        'value': 'string-value',
        'list_value': ['a', 'b', 'c']
    }, {
        'key': 234,
        'value': 'another-string',
        'dict_value': {
            'prop': 'Number',
            'value': 1.234
        }
    }, {
        'key': 345,
        'nested_dict': {
            'inner_dict': {
                'param': 'lmn',
                'value': 'def',
            },
        },
    }]

    def test_list_to_dict(self):
        output_dict = json_to_csv.list_to_dict(self.json_list)
        expected_dict = {
            0: {
                'key': 123,
                'list_value.0': 'a',
                'list_value.1': 'b',
                'list_value.2': 'c',
                'value': 'string-value'
            },
            1: {
                'dict_value.prop': 'Number',
                'dict_value.value': 1.234,
                'key': 234,
                'value': 'another-string'
            },
            2: {
                'key': 345,
                'nested_dict.inner_dict.param': 'lmn',
                'nested_dict.inner_dict.value': 'def'
            }
        }
        self.assertEqual(expected_dict, output_dict)

    def test_file_json_to_csv(self):
        self._tmp_dir = tempfile.mkdtemp()
        json_file = os.path.join(self._tmp_dir, 'test.json')
        with open(json_file, 'w') as file:
            file.write(json.dumps(self.json_list))

        csv_file = json_to_csv.file_json_to_csv(json_file)
        csv_dict = file_util.file_load_csv_dict(csv_file)
        expected_csv_dict = {
            '123': {
                'dict_value.prop': '',
                'dict_value.value': '',
                'list_value.0': 'a',
                'list_value.1': 'b',
                'list_value.2': 'c',
                'value': 'string-value',
                'nested_dict.inner_dict.param': '',
                'nested_dict.inner_dict.value': '',
            },
            '234': {
                'dict_value.prop': 'Number',
                'dict_value.value': '1.234',
                'list_value.0': '',
                'list_value.1': '',
                'list_value.2': '',
                'value': 'another-string',
                'nested_dict.inner_dict.param': '',
                'nested_dict.inner_dict.value': '',
            },
            '345': {
                'dict_value.prop': '',
                'dict_value.value': '',
                'list_value.0': '',
                'list_value.1': '',
                'list_value.2': '',
                'value': '',
                'nested_dict.inner_dict.param': 'lmn',
                'nested_dict.inner_dict.value': 'def',
            }
        }
        self.assertEqual(expected_csv_dict, csv_dict)
