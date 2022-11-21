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

from config_map import ConfigMap, get_config_map_from_file


class TestConfigMap(unittest.TestCase):

    _sample_config_json = '''
# Sample ConfigMap with comments and trailing commas
{
    # Simple param
    'param1' : 'string-value',
    'float-param': 1.234,

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
            config = ConfigMap({'a': 1})
            config.load_config_file(config_filename)
            # Verify older params remain
            self.assertEqual(config.get('a'), 1)
            # Verify new params are added
            self.assertEqual(config.get('param1'), 'string-value')

            config.get_configs().pop('a')
            self.assertEqual(
                get_config_map_from_file(config_filename).get_configs(),
                config.get_configs())

    def test_config_map_with_override(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_filename = os.path.join(tmp_dir, 'sample-config.json')
            with open(config_filename, 'w') as cfg_f:
                cfg_f.write(self._sample_config_json)

            # Load config from file with a single param overridden in arg.
            config = ConfigMap({'a': 1},
                               filename=config_filename,
                               config_string='{ "param1": "new-value" }')
            self.assertEqual(config.get('param1'), 'new-value')

    def test_update_config(self):
        cfg = ConfigMap()
        cfg.add_configs({
            'a': 1,
            'a1': 123,
            'b': {
                'c': 2,
                'd': 3,
            },
            'e': [4, 5],
        })
        self.assertEqual(cfg.get('a'), 1)
        self.assertEqual(cfg.get('a1'), 123)

        # Update config with a dictionary
        cfg.update_config({
            'a': 2,
            'b': {
                'c': 'new-str',
                'c1': 'abc'
            },
            'e': [6],
        })
        self.assertEqual(cfg.get('a'), 2)  # updated
        self.assertEqual(cfg.get('a1'), 123)  # original
        self.assertEqual(
            cfg.get('b'),
            {
                'c': 'new-str',  # changed
                'c1': 'abc',  # added
                'd': 3  # original
            })
        self.assertEqual(cfg.get('e'), [4, 5, 6])  # extended

    def test_set_config(self):
        cfg = ConfigMap()
        self.assertEqual(cfg.get('param', 0), 0)
        cfg.set_config('param', 123)
        self.assertEqual(cfg.get('param', 0), 123)
