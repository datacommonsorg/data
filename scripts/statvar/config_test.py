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
'''Tests for config.py'''

import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

_TEST_DIR = os.path.join(_SCRIPT_DIR, 'test_data')

from config import Config, get_config_from_file


class TestConfig(unittest.TestCase):

    _sample_config_json = '''
# Sample Config
{
    # Simple param
    'param1' : 'string-value',
    'list-param': ['list-element1', 2],
    # Nested dictionary parameter
    'dict-param': {
       'nested-dict': {
           'a': 1,
           'b': 2,
        },
        'nested-int': 0,
    },
}'''

    def test_load_config_file(self):
        '''Test loading of config dictionary from a file.'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_filename = os.path.join(tmp_dir, 'sample-config.json')
            with open(config_filename, 'w') as cfg_f:
                cfg_f.write(self._sample_config_json)

            # Load config.
            config = Config({'a': 1})
            config.load_config_file(config_filename)
            self.assertEqual(config.get_config('a'), 1)
            self.assertEqual(config.get_config('param1'), 'string-value')

            config.get_configs().pop('a')
            self.assertEqual(
                get_config_from_file(config_filename).get_configs(),
                config.get_configs())

    def test_update_config(self):
        cfg = Config()
        cfg.add_configs({
            'a': 1,
            'a1': 123,
            'b': {
                'c': 2,
                'd': 3,
            },
            'e': [4, 5],
        })
        self.assertEqual(cfg.get_config('a'), 1)
        self.assertEqual(cfg.get_config('a1'), 123)

        # Update config with a dictionary
        cfg.update_config({
            'a': 2,
            'b': {
                'c': 'new-str',
                'c1': 'abc'
            },
            'e': [6],
        })
        self.assertEqual(cfg.get_config('a'), 2)  # updated
        self.assertEqual(cfg.get_config('a1'), 123)  # original
        self.assertEqual(
            cfg.get_config('b'),
            {
                'c': 'new-str',  # changed
                'c1': 'abc',  # added
                'd': 3  # original
            })
        self.assertEqual(cfg.get_config('e'), [4, 5, 6])  # extended

    def test_default_config(self):
        cfg = Config()
        self.assertGreater(len(cfg.get_configs()), 1)
        self.assertFalse(cfg.get_config('debug'))
        self.assertEqual(cfg.get_config('input_reference_column'), '#input')
        self.assertEqual(cfg.get_config('unknown_param'), None)

    def test_set_config(self):
        cfg = Config()
        self.assertEqual(cfg.get_config('param', 0), 0)
        cfg.set_config('param', 123)
        self.assertEqual(cfg.get_config('param', 0), 123)
