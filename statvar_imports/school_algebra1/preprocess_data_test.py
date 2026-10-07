# Copyright 2025 Google LLC
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
"""Unit tests for preprocess_data.py."""

import os
import tempfile
import unittest
import pandas as pd
import preprocess_data


class PreprocessDataTest(unittest.TestCase):
    """Tests preprocessing helpers for CRDC Algebra 1 import."""

    def test_extract_survey_end_year(self):
        self.assertEqual(
            preprocess_data.extract_survey_end_year(
                'crdc_2015-16_school_data.csv'), 2016)
        self.assertEqual(
            preprocess_data.extract_survey_end_year(
                'crdc_2023-24_algebra_i.csv'), 2024)
        self.assertEqual(
            preprocess_data.extract_survey_end_year('unknown_file.csv'), 0)

    def test_preprocess_dataframe_leaid_schid(self):
        df = pd.DataFrame({
            'LEAID': ['100005'],
            'SCHID': ['870'],
            'SCH_ALGENR_G0708_HI_M': ['12'],
            'UNMAPPED_COL': ['99'],
        })
        mapped_cols = {'YEAR', 'ncesid', 'SCH_ALGENR_G0708_HI_M'}
        result = preprocess_data.preprocess_dataframe(
            df, 'crdc_2023-24_algebra_i.csv', mapped_cols)

        self.assertIn('ncesid', result.columns)
        self.assertIn('YEAR', result.columns)
        self.assertIn('SCH_ALGENR_G0708_HI_M', result.columns)
        self.assertNotIn('UNMAPPED_COL', result.columns)
        self.assertEqual(result['ncesid'].iloc[0], '010000500870')
        self.assertEqual(result['YEAR'].iloc[0], 2024)

    def test_process_file_writes_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            orig_processed = preprocess_data._PROCESSED_DIR
            try:
                input_dir = os.path.join(tmp_dir, 'input')
                output_dir = os.path.join(tmp_dir, 'output')
                os.makedirs(input_dir)
                os.makedirs(output_dir)
                preprocess_data._PROCESSED_DIR = output_dir
                input_csv = os.path.join(input_dir, 'crdc_2021-22_algebra_i.csv')
                pd.DataFrame({
                    'COMBOKEY': ['10000500870'],
                    'SCH_ALGENR_G08_HI_M': ['5'],
                }).to_csv(input_csv, index=False)

                preprocess_data.process_file(
                    input_csv, {'YEAR', 'ncesid', 'SCH_ALGENR_G08_HI_M'})
                output_csv = os.path.join(output_dir,
                                          'crdc_2021-22_algebra_i.csv')
                out_df = pd.read_csv(output_csv, dtype=str)
                self.assertEqual(out_df['ncesid'].iloc[0], '010000500870')
                self.assertEqual(out_df['YEAR'].iloc[0], '2022')
            finally:
                preprocess_data._PROCESSED_DIR = orig_processed


if __name__ == '__main__':
    unittest.main()
