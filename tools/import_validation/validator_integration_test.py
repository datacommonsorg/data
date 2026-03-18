# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import pandas as pd
import unittest
import tempfile
import shutil
import csv

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from validator import Validator
from result import ValidationStatus


class TestGoldensValidation(unittest.TestCase):
    '''Test Class for the GOLDENS validation rule.'''

    def setUp(self):
        self.validator = Validator()
        self.test_dir = tempfile.mkdtemp()
        
        # Create a sample golden CSV
        self.golden_file = os.path.join(self.test_dir, 'goldens.csv')
        with open(self.golden_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['StatVar', 'NumPlaces'])
            writer.writerow(['sv1', '10'])
            writer.writerow(['sv2', '20'])

        # Create a sample input CSV that matches
        self.input_file_match = os.path.join(self.test_dir, 'input_match.csv')
        with open(self.input_file_match, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['StatVar', 'NumPlaces', 'Value'])
            writer.writerow(['sv1', '10', '100'])
            writer.writerow(['sv2', '20', '200'])

        # Create a sample input CSV that is missing a golden
        self.input_file_missing = os.path.join(self.test_dir, 'input_missing.csv')
        with open(self.input_file_missing, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['StatVar', 'NumPlaces', 'Value'])
            writer.writerow(['sv1', '10', '100'])
            # sv2 is missing

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_validate_goldens_passes_with_matching_files(self):
        params = {
            'golden_files': self.golden_file,
            'input_files': self.input_file_match,
            'goldens_key_property': ['StatVar', 'NumPlaces']
        }
        # df is not used when input_files is in params
        result = self.validator.validate_goldens(pd.DataFrame(), params)
        self.assertEqual(result.status, ValidationStatus.PASSED)

    def test_validate_goldens_fails_with_missing_records(self):
        params = {
            'golden_files': self.golden_file,
            'input_files': self.input_file_missing,
            'goldens_key_property': ['StatVar', 'NumPlaces']
        }
        result = self.validator.validate_goldens(pd.DataFrame(), params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertIn('Found 1 missing golden records', result.message)
        # Fingerprint of sv2: 'NumPlaces=20;StatVar=sv2' (alphabetical)
        self.assertIn('StatVar=sv2', result.details['missing_goldens'][0])

    def test_validate_goldens_uses_dataframe_when_input_files_missing(self):
        # Sample DataFrame representing the stats data source
        df = pd.DataFrame({
            'StatVar': ['sv1', 'sv2'],
            'NumPlaces': [10, 20],
            'Value': [100, 200]
        })
        params = {
            'golden_files': self.golden_file,
            'goldens_key_property': ['StatVar', 'NumPlaces']
        }
        result = self.validator.validate_goldens(df, params)
        self.assertEqual(result.status, ValidationStatus.PASSED)

    def test_validate_goldens_fails_with_missing_records_from_df(self):
        # Sample DataFrame missing sv2
        df = pd.DataFrame({
            'StatVar': ['sv1'],
            'NumPlaces': [10],
            'Value': [100]
        })
        params = {
            'golden_files': self.golden_file,
            'goldens_key_property': ['StatVar', 'NumPlaces']
        }
        result = self.validator.validate_goldens(df, params)
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(len(result.details['missing_goldens']), 1)

    def test_validate_goldens_missing_golden_files_param(self):
        params = {'input_files': self.input_file_match}
        result = self.validator.validate_goldens(pd.DataFrame(), params)
        self.assertEqual(result.status, ValidationStatus.CONFIG_ERROR)
        self.assertIn('golden_files', result.message)

    def test_validate_goldens_empty_df_error(self):
        params = {'golden_files': self.golden_file}
        result = self.validator.validate_goldens(pd.DataFrame(), params)
        self.assertEqual(result.status, ValidationStatus.DATA_ERROR)
        self.assertIn('provided data source is empty', result.message)


if __name__ == '__main__':
    unittest.main()
