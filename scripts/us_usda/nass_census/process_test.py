# Copyright 2021 Google LLC
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
"""Tests for process.py"""

import csv
from datetime import datetime
import io
import os
import sys
import unittest
from unittest import mock

from absl import flags
import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from scripts.us_usda.nass_census import process


class ProcessTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if 'output' not in flags.FLAGS:
            process._define_flags()
        flags.FLAGS.mark_as_parsed()

    def test_write_csv(self):
        input_path = os.path.join(_SCRIPT_DIR, 'testdata',
                                  'ag_census_input.txt')
        statvars_path = os.path.join(_SCRIPT_DIR, 'statvars')
        expected_path = os.path.join(_SCRIPT_DIR, 'testdata',
                                     'ag_census_output.csv')
        with open(input_path) as f_in:
            d = process.get_statvars(statvars_path)
            reader = csv.DictReader(f_in, delimiter='\t')
            f_out = io.StringIO()
            with open(expected_path) as f_expected:
                expected = f_expected.read()
            process.write_csv(reader, f_out, d)
            self.assertEqual(expected, f_out.getvalue())

    def test_check_url_status_http_200(self):
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_session = mock.MagicMock()
        mock_session.head.return_value = mock_response

        # With explicit session
        self.assertTrue(
            process.check_url_status('https://example.com/test.gz',
                                     session=mock_session))
        mock_session.head.assert_called_once_with('https://example.com/test.gz',
                                                  timeout=30,
                                                  allow_redirects=True)

        # Without session (using requests)
        with mock.patch('requests.head', return_value=mock_response):
            self.assertTrue(
                process.check_url_status('https://example.com/test.gz'))

    def test_check_url_status_404(self):
        mock_response = mock.MagicMock()
        mock_response.status_code = 404
        with mock.patch('requests.head', return_value=mock_response):
            self.assertFalse(
                process.check_url_status('https://example.com/test.gz'))

    def test_check_url_status_5xx_retries_and_raises(self):
        mock_response = mock.MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            '500 Server Error')

        with mock.patch('requests.head', return_value=mock_response), \
             mock.patch('time.sleep') as mock_sleep:
            with self.assertRaises(requests.HTTPError):
                process.check_url_status('https://example.com/test.gz')
            # Should have retried 3 times (2 sleeps)
            self.assertEqual(mock_sleep.call_count, 2)

    def test_download_and_process_data_future_year_404_skip(self):
        with mock.patch.object(process, 'check_url_status', return_value=False):
            # Future year 2027 should skip and return None
            result = process.download_and_process_data(2027, {})
            self.assertIsNone(result)

    def test_download_and_process_data_historical_year_404_raises(self):
        with mock.patch.object(process, 'check_url_status', return_value=False):
            # Historical year 2022 should fail loudly
            with self.assertRaises(requests.HTTPError):
                process.download_and_process_data(2022, {})

    def test_download_and_process_data_overdue_year_404_raises(self):
        mock_dt = mock.MagicMock()
        mock_dt.now.return_value = datetime(2030, 1, 1)
        with mock.patch.object(process, 'check_url_status', return_value=False), \
             mock.patch.object(process, 'datetime', mock_dt):
            # In 2030, 2027 is overdue and should raise HTTPError
            with self.assertRaises(requests.HTTPError):
                process.download_and_process_data(2027, {})

    @mock.patch.object(process, 'check_url_status', return_value=True)
    @mock.patch.object(process, 'download_file')
    @mock.patch.object(process, 'unzip_file', return_value='input/test.txt')
    @mock.patch.object(process, 'write_csv')
    @mock.patch('file_util.FileIO')
    def test_download_and_process_data_success(self, mock_file_io,
                                               mock_write_csv, mock_unzip,
                                               mock_download, mock_check_url):
        mock_session = mock.MagicMock()
        result = process.download_and_process_data(2022, {},
                                                   session=mock_session)
        self.assertEqual(result, os.path.join('output', 'agriculture_2022.csv'))
        mock_check_url.assert_called_once()
        mock_download.assert_called_once_with(
            'https://www.nass.usda.gov/sites/default/files/datasets/qs.census2022.txt.gz',
            os.path.join('input', 'qs.census2022.txt.gz'),
            session=mock_session)

    @mock.patch.object(process, 'get_statvars', return_value={})
    @mock.patch.object(process, 'download_and_process_data', return_value=None)
    def test_main_empty_files_raises(self, mock_download, mock_get_statvars):
        process._FLAGS.mode = 'download'
        with self.assertRaises(RuntimeError) as ctx:
            process.main([])
        self.assertIn("No census files were downloaded or processed.",
                      str(ctx.exception))

    @mock.patch.object(process, 'get_statvars', return_value={})
    @mock.patch.object(process,
                       'download_and_process_data',
                       return_value='output/agriculture_2022.csv')
    @mock.patch.object(process, 'merge_csv_files')
    def test_main_download_and_merge_with_session(self, mock_merge,
                                                  mock_download,
                                                  mock_get_statvars):
        process._FLAGS.mode = ''
        process._FLAGS.output = 'output/agriculture.csv'
        process.main([])
        mock_merge.assert_called_once()
        self.assertTrue(mock_download.called)
        # Verify a session was passed to download_and_process_data
        session_arg = mock_download.call_args[1].get('session')
        self.assertIsInstance(session_arg, requests.Session)


if __name__ == '__main__':
    unittest.main()
