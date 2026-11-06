# Copyright 2026 Google LLC
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
"""Tests for config_flags.py"""

import os
import shutil
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import config_flags


class GetValueTypeTest(unittest.TestCase):
    """Tests for get_value_type with boolean defaults."""

    def test_bool_text(self):
        for value in ['True', 'true', ' TRUE ', 'yes', 'on', '1', 1, True]:
            self.assertIs(config_flags.get_value_type(value, False), True,
                          f'value: {value!r}')
        for value in [
                'False', 'false', ' False ', 'no', 'off', '0', '', 0, False
        ]:
            self.assertIs(config_flags.get_value_type(value, True), False,
                          f'value: {value!r}')

    def test_invalid_bool_uses_default(self):
        self.assertIs(config_flags.get_value_type('maybe', True), True)
        self.assertIs(config_flags.get_value_type('maybe', False), False)


class SetConfigValueTest(unittest.TestCase):
    """Tests for set_config_value with boolean settings."""

    def test_bool_flag_not_in_config(self):
        # 'resume' is also in get_default_config(), but an empty config tests
        # the fallback to the default of the flag with the same name.
        config = {}
        config_flags.set_config_value('resume', 'True', config)
        self.assertIs(config['resume'], True)
        config_flags.set_config_value('resume', '0', config)
        self.assertIs(config['resume'], False)

    def test_unknown_param_keeps_value(self):
        config = {}
        config_flags.set_config_value('my_custom_setting', 'False', config)
        self.assertEqual(config['my_custom_setting'], 'False')


class InitConfigTest(unittest.TestCase):
    """Tests for loading boolean settings from a CSV config file."""

    def setUp(self):
        self._tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmp_dir)

    def test_csv_config_bool_values(self):
        config_file = os.path.join(self._tmp_dir, 'config.csv')
        with open(config_file, 'w') as f:
            f.write('parameter,value\n'
                    'match_substring_word_boundary,False\n'
                    'reconcile_nodes,0\n'
                    'drop_statvars_with_dup_svobs,false\n'
                    'resume,1\n')
        config = config_flags.init_config_from_flags(config_file)
        self.assertIs(config.get('match_substring_word_boundary'), False)
        self.assertIs(config.get('reconcile_nodes'), False)
        self.assertIs(config.get('drop_statvars_with_dup_svobs'), False)
        self.assertIs(config.get('resume'), True)

    def test_bool_defaults(self):
        config = config_flags.init_config_from_flags({})
        for param in [
                'match_substring_word_boundary', 'reconcile_nodes',
                'drop_statvars_with_dup_svobs', 'check_url',
                'ignore_non_alphanum', 'maps_api_text_search',
                'resolver_normalize_key', 'use_place_names', 'recon_lookup_api',
                'llm_response_drop_extra_output'
        ]:
            self.assertIs(config.get(param), True, param)
        for param in ['resume', 'output_nodes_with_additions']:
            self.assertIs(config.get(param), False, param)

    def test_csv_config_turns_off_defaults(self):
        config_file = os.path.join(self._tmp_dir, 'config.csv')
        with open(config_file, 'w') as f:
            f.write('parameter,value\n'
                    'check_url,0\n'
                    'use_place_names,False\n'
                    'output_nodes_with_additions,yes\n')
        config = config_flags.init_config_from_flags(config_file)
        self.assertIs(config.get('check_url'), False)
        self.assertIs(config.get('use_place_names'), False)
        self.assertIs(config.get('output_nodes_with_additions'), True)


if __name__ == '__main__':
    unittest.main()
