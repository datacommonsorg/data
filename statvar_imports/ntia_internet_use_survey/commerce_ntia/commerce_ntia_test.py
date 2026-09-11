# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Hermetic unit tests for commerce_ntia preprocess module."""

import os
import sys
import tempfile
import unittest
from unittest import mock
import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
import preprocess


class PreprocessTest(unittest.TestCase):

    def test_move_column_left_success(self):
        """Tests that move_column_left places column immediately left of target."""
        df = pd.DataFrame({'a': [1], 'b': [2], 'c': [3], 'd': [4]})
        result = preprocess.move_column_left(df, 'd', 'b')
        self.assertEqual(list(result.columns), ['a', 'd', 'b', 'c'])

    def test_move_column_left_missing_cols(self):
        """Tests that move_column_left returns original df if columns are not present."""
        df = pd.DataFrame({'a': [1], 'b': [2]})
        result = preprocess.move_column_left(df, 'missing', 'b')
        self.assertEqual(list(result.columns), ['a', 'b'])

    def test_preprocess_data(self):
        """Tests data preprocessing and splitting into age-only and general survey CSVs."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_file = os.path.join(tmp_dir, 'ntia-analyze-table.csv')
            output_age = os.path.join(tmp_dir, 'ntia-data-age-only.csv')
            output_data = os.path.join(tmp_dir, 'ntia-data.csv')

            raw_data = {
                'dataset': ['Nov 2023', 'Nov 2023', 'Nov 2023'],
                'variable': ['Streaming', 'Email', 'Broadband'],
                'description': ['Desc 1', 'Desc 2', 'Desc 3'],
                'universe': ['isPerson', 'isAdult', 'isHousehold'],
                'age314Count': [10, 20, 30],
                'age1524Count': [11, 21, 31],
                'age2544Count': [12, 22, 32],
                'age4564Count': [13, 23, 33],
                'age65pCount': [14, 24, 34],
                'totalCount': [100, 200, 300],
                'otherMetric': [1.5, 2.5, 3.5]
            }
            pd.DataFrame(raw_data).to_csv(input_file, index=False)

            with mock.patch.object(preprocess, 'INPUT_DIR', tmp_dir), \
                 mock.patch.object(preprocess, 'INPUT_FILE', input_file), \
                 mock.patch.object(preprocess, 'INPUT_FILE_1', output_age), \
                 mock.patch.object(preprocess, 'INPUT_FILE_2', output_data):
                preprocess.preprocess_data()

            self.assertTrue(os.path.exists(output_age))
            self.assertTrue(os.path.exists(output_data))

            df_age = pd.read_csv(output_age)
            cols_age = list(df_age.columns)
            self.assertEqual(
                cols_age.index('universe') + 1, cols_age.index('variable'))
            for age_col in preprocess.AGE_COLUMNS:
                self.assertIn(age_col, cols_age)
            self.assertNotIn('totalCount', cols_age)
            self.assertNotIn('otherMetric', cols_age)
            self.assertIn('universeAgeResol', cols_age)
            self.assertIn('variableAgeResol', cols_age)
            self.assertEqual(df_age.loc[0, 'universeAgeResol'], 'CivilPerson')
            self.assertEqual(df_age.loc[1, 'universeAgeResol'], 'Adult')
            self.assertTrue(pd.isna(df_age.loc[2, 'universeAgeResol']))

            df_data = pd.read_csv(output_data)
            cols_data = list(df_data.columns)
            self.assertEqual(
                cols_data.index('universe') + 1, cols_data.index('variable'))
            self.assertIn('totalCount', cols_data)
            self.assertIn('otherMetric', cols_data)
            self.assertIn('universeAgeResol', cols_data)
            self.assertIn('variableAgeResol', cols_data)
            self.assertEqual(df_data.loc[0, 'universeAgeResol'], 'CivilPerson')
            self.assertEqual(df_data.loc[1, 'universeAgeResol'], 'Adult')
            self.assertTrue(pd.isna(df_data.loc[2, 'universeAgeResol']))
            for age_col in preprocess.AGE_COLUMNS:
                self.assertNotIn(age_col, cols_data)

    @mock.patch('preprocess.preprocess_data')
    @mock.patch('preprocess.download_file')
    def test_main_download_success(self, mock_download, mock_preprocess):
        """Tests that main downloads file and executes preprocess_data on success."""
        mock_download.return_value = True
        with mock.patch('os.path.exists', return_value=True):
            preprocess.main([])
            mock_download.assert_called_once_with(
                url=preprocess.Commerce_NTIA_URL,
                output_folder=preprocess.INPUT_DIR,
                unzip=False,
                headers=preprocess.HEADERS,
                tries=3,
                delay=5,
                backoff=2,
            )
            mock_preprocess.assert_called_once()

    @mock.patch('preprocess.preprocess_data')
    @mock.patch('preprocess.download_file')
    @mock.patch('preprocess.logging.fatal')
    def test_main_download_failure(self, mock_fatal, mock_download,
                                   mock_preprocess):
        """Tests that main logs fatal error and halts when download returns False."""
        mock_download.return_value = False
        preprocess.main([])
        mock_fatal.assert_called_once_with(
            "Failed to download Commerce_NTIA file.")
        mock_preprocess.assert_not_called()

    @mock.patch('preprocess.preprocess_data')
    @mock.patch('preprocess.download_file')
    @mock.patch('preprocess.logging.fatal')
    def test_main_download_exception(self, mock_fatal, mock_download,
                                     mock_preprocess):
        """Tests that main logs fatal error when download raises an exception."""
        mock_download.side_effect = Exception("Connection timeout")
        preprocess.main([])
        self.assertTrue(mock_fatal.called)
        self.assertIn("Connection timeout", str(mock_fatal.call_args))
        mock_preprocess.assert_not_called()


if __name__ == '__main__':
    unittest.main()
