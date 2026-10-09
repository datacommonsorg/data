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

import json
import os
import sys
import unittest
from unittest.mock import Mock, patch

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_PATH)

import download_script


class DownloadScriptTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        download_script._FLAGS.mark_as_parsed()

    @patch('download_script.storage.Client')
    def test_load_config_gcs(self, mock_storage_client):
        mock_blob = Mock()
        mock_blob.download_as_string.return_value = b'{"url": "http://fake-api.com"}'
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_client_instance = Mock()
        mock_client_instance.get_bucket.return_value = mock_bucket
        mock_storage_client.return_value = mock_client_instance

        config = download_script.load_config(
            'gs://fake_bucket/path/to/config.json')
        self.assertEqual(config, {'url': 'http://fake-api.com'})
        mock_client_instance.get_bucket.assert_called_once_with('fake_bucket')
        mock_bucket.blob.assert_called_once_with('path/to/config.json')

    @patch('download_script.file_util.file_load_py_dict')
    def test_load_config_local(self, mock_file_load):
        mock_file_load.return_value = {'url': 'http://fake-api.com'}
        config = download_script.load_config('/fake/path/config.json')
        self.assertEqual(config, {'url': 'http://fake-api.com'})
        mock_file_load.assert_called_once_with('/fake/path/config.json')

    @patch('download_script.load_config')
    @patch('download_script._retry_method')
    def test_download_data(self, mock_retry, mock_load_config):
        # Mock config file
        mock_load_config.return_value = {
            'url': 'http://fake-api.com?param=1',
            'input_files': '/fake/output'
        }

        # Mock API responses
        mock_response_page1 = Mock()
        mock_response_page1.json.return_value = {
            'Data': [{
                'StateName': 'State1',
                'TRU': 'Total',
                'D7300_3': 'Male',
                'D7300_4': 'Category1',
                'D7300_5': '15-29',
                'I7300_6': {
                    'TotalPopulationWeight': 100
                },
                'I7300_7': {
                    'avg': 50
                },
                'I7300_8': {
                    'avg': 25
                },
                'Year': '2017'
            }]
        }
        mock_response_page2 = Mock()
        mock_response_page2.json.return_value = {'Data': []}
        mock_retry.side_effect = [mock_response_page1, mock_response_page2]

        # Run the function
        data = download_script.download_data('gs://fake/path')

        # Assertions
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0][0], 'State1')
        self.assertEqual(data[0][8], '2017')
        self.assertEqual(data[0][9], '2018')

        # Check if retry method was called correctly for pagination
        self.assertEqual(mock_retry.call_count, 2)
        mock_retry.assert_any_call('http://fake-api.com?param=1&pageno=1', None,
                                   3, 5, 2)
        mock_retry.assert_any_call('http://fake-api.com?param=1&pageno=2', None,
                                   3, 5, 2)

    @patch('download_script.load_config')
    def test_download_data_no_url(self, mock_load_config):
        mock_load_config.return_value = {}
        data = download_script.download_data('gs://fake/path')
        self.assertEqual(data, [])

    @patch('download_script.load_config')
    @patch('download_script._retry_method')
    @patch('download_script.logging.fatal')
    def test_download_data_retry_fails(self, mock_fatal, mock_retry,
                                       mock_load_config):
        mock_load_config.return_value = {'url': 'http://fake-api.com?param=1'}
        mock_retry.return_value = None
        mock_fatal.side_effect = SystemExit('Fatal error')
        with self.assertRaises(SystemExit):
            download_script.download_data('gs://fake/path')
        mock_fatal.assert_called_once_with(
            'Failed to retrieve data from %s (page %d)',
            'http://fake-api.com?param=1&pageno=1', 1)

    @patch('download_script.load_config')
    @patch('download_script._retry_method')
    @patch('download_script.logging.fatal')
    def test_download_data_json_decode_error(self, mock_fatal, mock_retry,
                                            mock_load_config):
        mock_load_config.return_value = {'url': 'http://fake-api.com?param=1'}
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError('Expecting value', '', 0)
        mock_retry.return_value = mock_response
        mock_fatal.side_effect = SystemExit('Fatal error')
        with self.assertRaises(SystemExit):
            download_script.download_data('gs://fake/path')
        mock_fatal.assert_called_once()
        self.assertIn('Failed to parse JSON from %s (page %d):',
                      mock_fatal.call_args[0][0])

    @patch('pandas.DataFrame')
    def test_preprocess_and_save(self, mock_df_constructor):
        # Sample data
        data = [('State1', 'Total', 'Male', 'Category1', '15-29', 100, 50, 25,
                 '2017', '2018', '2017', '2017')]

        # Run the function
        download_script.preprocess_and_save(data)

        # Get the DataFrame instance
        self.assertEqual(mock_df_constructor.call_count, 1)
        df_instance = mock_df_constructor.return_value

        # Check that to_csv was called on the instance with expected path in script dir
        expected_output_path = os.path.join(download_script._SCRIPT_PATH,
                                            'india_nss_health_ailments.csv')
        df_instance.to_csv.assert_called_once_with(expected_output_path,
                                                   index=False)

        # Check the data that was passed to the constructor
        constructor_args = mock_df_constructor.call_args
        passed_data = constructor_args[0][0]
        self.assertEqual(len(passed_data), 1)
        self.assertEqual(passed_data[0][0], 'State1')

        # Check the columns
        passed_columns = constructor_args[1]['columns']
        self.assertEqual(passed_columns[9], 'futureYear')

    @patch('pandas.DataFrame')
    def test_preprocess_and_save_empty_data(self, mock_df_constructor):
        download_script.preprocess_and_save([])
        mock_df_constructor.assert_not_called()

    @patch('download_script.download_data')
    @patch('download_script.preprocess_and_save')
    def test_main(self, mock_preprocess_and_save, mock_download_data):
        mock_download_data.return_value = [('data',)]
        download_script.main(None)
        mock_download_data.assert_called_once()
        mock_preprocess_and_save.assert_called_once_with([('data',)])


if __name__ == '__main__':
    unittest.main()
