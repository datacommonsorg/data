# Copyright 2021 Google LLC
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
"""Tests for Hate Crime Table 1."""

import os
import sys
import unittest
import tempfile
import json
import pandas as pd
from . import preprocess

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '..'))  # for utils

import utils

_YEAR_INDEX = 0

_OUTPUT_COLUMNS = ['Year', 'StatVar', 'Quantity']


class HateCrimeTable1Test(unittest.TestCase):

    def test_csv(self):
        csv_files = []
        test_config = {
            'type': 'xls',
            'path': 'testdata/2019.xls',
            'args': {
                'header': 3,
                'skipfooter': 3
            }
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            xls_file_path = os.path.join(_SCRIPT_PATH, test_config['path'])
            csv_file_path = os.path.join(tmp_dir, '2019.csv')

            read_file = pd.read_excel(xls_file_path, **test_config['args'])
            read_file = preprocess._clean_dataframe(read_file)
            read_file.insert(_YEAR_INDEX, 'Year', '2019')
            read_file.to_csv(csv_file_path, index=None, header=True)
            csv_files.append(csv_file_path)

            config_path = os.path.join(_SCRIPT_PATH, 'config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            cleaned_csv_path = os.path.join(tmp_dir, 'cleaned.csv')
            utils.create_csv_mcf(csv_files, cleaned_csv_path, config,
                                 _OUTPUT_COLUMNS, preprocess._write_output_csv)

            with open(cleaned_csv_path, 'r', encoding='utf-8') as f_result:
                test_result = f_result.read()
                expected_csv_path = os.path.join(_SCRIPT_PATH, 'testdata',
                                                 'expected.csv')
                with open(expected_csv_path, 'r',
                          encoding='utf-8') as f_expected:
                    expected_result = f_expected.read()
                self.assertEqual(test_result, expected_result)
