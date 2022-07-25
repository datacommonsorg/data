# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for preprocess.py of the CDC Natality import."""

import os
import unittest
import tempfile
import subprocess

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))


class CDCNatality(unittest.TestCase):

    def test_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = os.path.join(tmp_dir, 'cleaned.csv')
            mcf_path = os.path.join(tmp_dir, 'output.mcf')
            preprocess_path = os.path.join(_SCRIPT_PATH, 'preprocess.py')
            config_path = os.path.join(_SCRIPT_PATH, 'state',
                                       '16-20_state.json')
            input_path = os.path.join(_SCRIPT_PATH, 'testdata', 'cleaned_data')

            subprocess.call([
                'python', preprocess_path, f'--input_path={input_path}',
                f'--config_path={config_path}', f'--output_path={tmp_dir}'
            ])

            with open(csv_path, 'r', encoding='utf-8') as f_result:
                test_result = f_result.read()
                expected_csv_path = os.path.join(_SCRIPT_PATH, 'testdata',
                                                 'expected.csv')
                with open(expected_csv_path, 'r',
                          encoding='utf-8') as f_expected:
                    expected_result = f_expected.read()
                self.assertEqual(test_result, expected_result)

            with open(mcf_path, 'r', encoding='utf-8') as f_result:
                test_result = f_result.read()
                expected_mcf_path = os.path.join(_SCRIPT_PATH, 'testdata',
                                                 'output.mcf')
                with open(expected_mcf_path, 'r',
                          encoding='utf-8') as f_expected:
                    expected_result = f_expected.read()
                self.assertEqual(test_result, expected_result)
