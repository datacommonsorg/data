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

import json
import os
import pathlib
import sys
import tempfile
from unittest import mock

from absl.testing import absltest, flagsaver
import pandas as pd
import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

import rbi_download


class PreprocessFilesTest(absltest.TestCase):

    def test_preserves_workbook_and_original_error(self):
        with tempfile.TemporaryDirectory() as directory:
            workbook = pathlib.Path(directory) / 'source.xlsx'
            workbook.write_bytes(b'original workbook')
            sheets = {'Sheet1': pd.DataFrame([['State/Union Territory']])}

            with mock.patch.object(
                    rbi_download.pd, 'read_excel', return_value=sheets), \
                 mock.patch.object(
                     pd.DataFrame,
                     'map',
                     side_effect=ValueError('transform failed')), \
                 mock.patch.object(rbi_download.logging, 'error') as mock_error:
                rbi_download.preprocess_files(directory)

            self.assertEqual(workbook.read_bytes(), b'original workbook')
            mock_error.assert_called_once_with(
                'Error processing source.xlsx: transform failed')

    def test_preprocess_files_converts_numeric_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = pathlib.Path(directory) / 'source.xlsx'
            initial_df = pd.DataFrame(
                [['State/Union Territory', '2015*', '2016@', '2017-18'],
                 ['Andhra Pradesh', '10.5', '20.0', '30.5']])
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                initial_df.to_excel(writer,
                                    sheet_name='Sheet1',
                                    index=False,
                                    header=False)

            rbi_download.preprocess_files(directory)

            processed = pd.read_excel(file_path,
                                      sheet_name='Sheet1',
                                      header=None)
            self.assertEqual(processed.iloc[0, 0], 'State/Union Territory')
            self.assertEqual(processed.iloc[0, 1], 2015)
            self.assertEqual(processed.iloc[0, 2], 2016)
            self.assertEqual(processed.iloc[0, 3], '2017-18')
            self.assertEqual(processed.iloc[1, 0], 'Andhra Pradesh')

    def test_preprocess_files_preserves_nan(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = pathlib.Path(directory) / 'source.xlsx'
            initial_df = pd.DataFrame(
                [['State/Union Territory', '2015*', None],
                 ['Andhra Pradesh', None, '30.5']])
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                initial_df.to_excel(writer,
                                    sheet_name='Sheet1',
                                    index=False,
                                    header=False)

            rbi_download.preprocess_files(directory)

            processed = pd.read_excel(file_path,
                                      sheet_name='Sheet1',
                                      header=None)
            self.assertTrue(pd.isna(processed.iloc[0, 2]))
            self.assertTrue(pd.isna(processed.iloc[1, 1]))

    def test_preprocess_files_fatal_on_missing_dir(self):
        with mock.patch.object(rbi_download.logging, 'fatal') as fatal:
            rbi_download.preprocess_files('/non/existent/directory/path')
            fatal.assert_called_once()
            self.assertIn("Directory not found", fatal.call_args[0][0])

    def test_preprocess_files_fatal_on_empty_dir(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(rbi_download.logging, 'fatal') as fatal:
                rbi_download.preprocess_files(directory)
                fatal.assert_called_once()
                self.assertIn("No XLSX files found", fatal.call_args[0][0])

    def test_preprocess_files_handles_flexible_state_header(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = pathlib.Path(directory) / 'source.xlsx'
            initial_df = pd.DataFrame([['State / Union Territory', '2018-19'],
                                       ['State/Union Territory', '2019-20'],
                                       ['Karnataka', '120.5']])
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                initial_df.to_excel(writer,
                                    sheet_name='Sheet1',
                                    index=False,
                                    header=False)

            rbi_download.preprocess_files(directory)

            processed = pd.read_excel(file_path,
                                      sheet_name='Sheet1',
                                      header=None)
            self.assertEqual(processed.iloc[0, 0], 'State / Union Territory')
            self.assertEqual(processed.iloc[1, 0], 'State/Union Territory')
            self.assertEqual(processed.iloc[0, 1], '2018-19')
            self.assertEqual(processed.iloc[1, 1], '2019-20')
            self.assertEqual(processed.iloc[2, 0], 'Karnataka')
            self.assertEqual(processed.iloc[2, 1], '120.5')

    def test_preprocess_files_avoids_literal_nan_and_preserves_numeric(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = pathlib.Path(directory) / 'source.xlsx'
            initial_df = pd.DataFrame(
                [['State/Union Territory', '2020', '2021', '2022'],
                 ['Bihar', 100, 200.5, '   '], ['Assam', 'nan', 'NAN', '300']])
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                initial_df.to_excel(writer,
                                    sheet_name='Sheet1',
                                    index=False,
                                    header=False)

            rbi_download.preprocess_files(directory)

            processed = pd.read_excel(file_path,
                                      sheet_name='Sheet1',
                                      header=None)
            # Empty/whitespace and 'nan' strings become NaN, NOT literal string 'nan'
            self.assertTrue(pd.isna(processed.iloc[1, 3]))
            self.assertTrue(pd.isna(processed.iloc[2, 1]))
            self.assertTrue(pd.isna(processed.iloc[2, 2]))
            # Numeric values preserved
            self.assertEqual(processed.iloc[1, 1], 100)
            self.assertEqual(processed.iloc[1, 2], 200.5)


class ReadsConfigFileTest(absltest.TestCase):

    def test_reads_local_config_file(self):
        with tempfile.NamedTemporaryFile('w', suffix='.json',
                                         delete=False) as f:
            json.dump(
                {
                    'URLS_CONFIG': [{
                        'url': 'http://example.com/test.xlsx',
                        'category': 'test',
                        'filename': 'test.xlsx'
                    }]
                }, f)
            temp_path = f.name
        try:
            with flagsaver.flagsaver(config_file_path=temp_path):
                configs = rbi_download.reads_config_file()
                self.assertIn('URLS_CONFIG', configs)
                self.assertEqual(len(configs['URLS_CONFIG']), 1)
                self.assertEqual(configs['URLS_CONFIG'][0]['filename'],
                                 'test.xlsx')
        finally:
            os.remove(temp_path)

    def test_falls_back_to_local_configs_json(self):
        with flagsaver.flagsaver(config_file_path='gs://nonexistent_bucket/configs.json'), \
             mock.patch.object(rbi_download.storage, 'Client', side_effect=Exception('GCS unavailable')):
            configs = rbi_download.reads_config_file()
            self.assertIn('URLS_CONFIG', configs)
            self.assertGreater(len(configs['URLS_CONFIG']), 0)


class DownloadFilesTest(absltest.TestCase):

    def test_skips_existing_valid_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cat_dir = os.path.join(temp_dir, 'agri')
            os.makedirs(cat_dir, exist_ok=True)
            existing_file = os.path.join(cat_dir, 'existing.xlsx')
            with open(existing_file, 'wb') as f:
                f.write(b'PK\x03\x04valid_zip_content')

            configs = [{
                'url': 'http://example.com/existing.xlsx',
                'category': 'agri',
                'filename': 'existing.xlsx'
            }]
            mock_session = mock.MagicMock()
            with mock.patch.object(rbi_download, 'INPUT_DIR', temp_dir):
                rbi_download.download_files(configs,
                                            session=mock_session,
                                            delay=0)
                mock_session.get.assert_not_called()

    def test_redownloads_invalid_existing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cat_dir = os.path.join(temp_dir, 'agri')
            os.makedirs(cat_dir, exist_ok=True)
            corrupt_file = os.path.join(cat_dir, 'corrupt.xlsx')
            with open(corrupt_file, 'wb') as f:
                f.write(b'<html>error page</html>')

            configs = [{
                'url': 'http://example.com/corrupt.xlsx',
                'category': 'agri',
                'filename': 'corrupt.xlsx'
            }]
            mock_session = mock.MagicMock()
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            mock_response.content = b'PK\x03\x04valid_content'
            mock_session.get.return_value = mock_response

            with mock.patch.object(rbi_download, 'INPUT_DIR', temp_dir):
                rbi_download.download_files(configs,
                                            session=mock_session,
                                            delay=0)
                mock_session.get.assert_called_once()
                self.assertEqual(
                    pathlib.Path(corrupt_file).read_bytes(),
                    b'PK\x03\x04valid_content')

    def test_download_files_uses_browser_headers_in_session(self):
        session = rbi_download.create_retry_session()
        headers = session.headers
        self.assertIn('User-Agent', headers)
        self.assertIn('Mozilla', headers['User-Agent'])

    def test_rejects_html_error_response(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            configs = [{
                'url': 'http://example.com/blocked.xlsx',
                'category': 'agri',
                'filename': 'blocked.xlsx'
            }]
            mock_session = mock.MagicMock()
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            mock_response.content = b'<!DOCTYPE html><html><body>Access Denied</body></html>'
            mock_session.get.return_value = mock_response

            with mock.patch.object(rbi_download, 'INPUT_DIR', temp_dir):
                rbi_download.download_files(configs,
                                            session=mock_session,
                                            delay=0)
                target_file = pathlib.Path(temp_dir) / 'agri' / 'blocked.xlsx'
                self.assertFalse(target_file.exists())

    def test_isolates_download_failures(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            configs = [
                {
                    'url': 'http://example.com/fail.xlsx',
                    'category': 'agri',
                    'filename': 'fail.xlsx'
                },
                {
                    'url': 'http://example.com/success.xlsx',
                    'category': 'agri',
                    'filename': 'success.xlsx'
                },
            ]
            mock_session = mock.MagicMock()
            mock_success = mock.MagicMock()
            mock_success.status_code = 200
            mock_success.content = b'PK\x03\x04success content'
            mock_session.get.side_effect = [
                requests.exceptions.RequestException('404 Not Found'),
                mock_success
            ]

            with mock.patch.object(rbi_download, 'INPUT_DIR', temp_dir):
                rbi_download.download_files(configs,
                                            session=mock_session,
                                            delay=0)

            success_file = pathlib.Path(temp_dir) / 'agri' / 'success.xlsx'
            self.assertTrue(success_file.exists())
            self.assertEqual(success_file.read_bytes(),
                             b'PK\x03\x04success content')


if __name__ == '__main__':
    absltest.main()
