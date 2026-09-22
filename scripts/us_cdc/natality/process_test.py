# Copyright 2026 Google LLC
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
"""Tests for process.py of the CDC Natality import automation."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import pandas as pd

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))


class ProcessPipelineTest(unittest.TestCase):

    def test_end_to_end_pipeline_with_preprocessed_data(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_dir = os.path.join(tmp_dir, 'input_files')
            output_dir = os.path.join(tmp_dir, 'output')
            os.makedirs(input_dir, exist_ok=True)

            sample_country_csv = os.path.join(input_dir, 'country_cleaned_16-20.csv')
            sample_state_csv = os.path.join(input_dir, 'state_cleaned_16-20.csv')
            sample_county_csv = os.path.join(input_dir, 'county_cleaned_16-20.csv')

            country_df = pd.DataFrame([{
                'Year': '2020',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '3613647'
            }, {
                'Year': '2019',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '3747540'
            }])
            country_df.to_csv(sample_country_csv, index=False)

            state_df = pd.DataFrame([{
                'Year': '2020',
                'Geo': 'geoId/01',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '57647',
                'Unit': ''
            }, {
                'Year': '2020',
                'Geo': 'geoId/02',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '9469',
                'Unit': ''
            }])
            state_df.to_csv(sample_state_csv, index=False)

            county_df = pd.DataFrame([{
                'Year': '2020',
                'Geo': 'geoId/01003',
                'StatVar': 'Count_BirthEvent_LiveBirth',
                'Quantity': '2245',
                'Unit': ''
            }])
            county_df.to_csv(sample_county_csv, index=False)

            process_py = os.path.join(_SCRIPT_PATH, 'process.py')
            cmd = [
                sys.executable, process_py, f'--input_path={input_dir}',
                f'--output_path={output_dir}'
            ]
            subprocess.check_call(cmd)

            expected_files = [
                'country.csv', 'state.csv', 'county.csv', 'country.tmcf',
                'state.tmcf', 'county.tmcf'
            ]
            for filename in expected_files:
                out_path = os.path.join(output_dir, filename)
                self.assertTrue(os.path.exists(out_path),
                                f'Missing expected file: {filename}')
                self.assertGreater(os.path.getsize(out_path), 0,
                                   f'Output file is empty: {filename}')

            result_country = pd.read_csv(os.path.join(output_dir, 'country.csv'))
            self.assertEqual(len(result_country), 2)
            self.assertIn('StatVar', result_country.columns)

            result_state = pd.read_csv(os.path.join(output_dir, 'state.csv'))
            self.assertEqual(len(result_state), 2)
            self.assertIn('Geo', result_state.columns)

            result_county = pd.read_csv(os.path.join(output_dir, 'county.csv'))
            self.assertEqual(len(result_county), 1)

    def test_pipeline_with_testdata_fallback(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_dir = os.path.join(tmp_dir, 'empty_inputs')
            output_dir = os.path.join(tmp_dir, 'output')
            os.makedirs(input_dir, exist_ok=True)

            process_py = os.path.join(_SCRIPT_PATH, 'process.py')
            cmd = [
                sys.executable, process_py, f'--input_path={input_dir}',
                f'--output_path={output_dir}', '--use_test_data'
            ]
            subprocess.check_call(cmd)

            for filename in ['country.csv', 'state.csv', 'county.csv']:
                out_path = os.path.join(output_dir, filename)
                self.assertTrue(os.path.exists(out_path),
                                f'Missing expected file: {filename}')
                self.assertGreater(os.path.getsize(out_path), 0)


if __name__ == '__main__':
    unittest.main()
