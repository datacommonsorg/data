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

import unittest
from unittest.mock import patch, Mock
import pandas as pd

import download_script

class DownloadScriptTest(unittest.TestCase):

    @patch('download_script.file_util.file_load_py_dict')
    @patch('download_script._retry_method')
    def test_download_data(self, mock_retry, mock_file_load):
        # Mock config file
        mock_file_load.return_value = {
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
                'I7300_6': {'TotalPopulationWeight': 100},
                'I7300_7': {'avg': 50},
                'I7300_8': {'avg': 25},
                'Year': '2017'
            }]
        }
        mock_response_page2 = Mock()
        mock_response_page2.json.return_value = {'Data': []}
        mock_retry.side_effect = [mock_response_page1, mock_response_page2]

        # Run the function
        data, output_dir = download_script.download_data('gs://fake/path')

        # Assertions
        self.assertEqual(output_dir, '/fake/output')
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0][0], 'State1')
        self.assertEqual(data[0][8], '2017')
        self.assertEqual(data[0][9], '2018')
        
        # Check if retry method was called correctly for pagination
        self.assertEqual(mock_retry.call_count, 2)
        mock_retry.assert_any_call('http://fake-api.com?param=1&pageno=1', None, 3, 5, 2)
        mock_retry.assert_any_call('http://fake-api.com?param=1&pageno=2', None, 3, 5, 2)

    @patch('os.makedirs')
    @patch('pandas.DataFrame.to_csv')
    def test_preprocess_and_save(self, mock_to_csv, mock_makedirs):
        # Sample data
        data = [('State1', 'Total', 'Male', 'Category1', '15-29', 100, 50, 25, '2017', '2018', '2017', '2017')]
        
        # Run the function
        download_script.preprocess_and_save(data, '/fake/output')

        # Assertions
        mock_makedirs.assert_called_once_with('/fake/output', exist_ok=True)
        
        # Check that to_csv was called with a dataframe
        self.assertEqual(mock_to_csv.call_count, 1)
        
        # The mock is on the to_csv method of the DataFrame. The instance
        # on which it was called is the first argument to the mock's call_args.
        # However, the mock is on the *class* method, so we don't get the instance.
        # Instead, we can patch the DataFrame constructor itself.
        
        with patch('pandas.DataFrame') as mock_df_constructor:
            download_script.preprocess_and_save(data, '/fake/output')
            
            # Get the DataFrame instance
            self.assertEqual(mock_df_constructor.call_count, 1)
            df_instance = mock_df_constructor.return_value
            
            # Check that to_csv was called on our instance
            df_instance.to_csv.assert_called_once_with(
                '/fake/output/IndiaNSS_HealthAilments.csv', index=False
            )
            
            # Now we can check the data that was passed to the constructor
            constructor_args = mock_df_constructor.call_args
            passed_data = constructor_args[0][0]
            self.assertEqual(len(passed_data), 1)
            self.assertEqual(passed_data[0][0], 'State1')
            
            # And we can check the columns
            passed_columns = constructor_args[1]['columns']
            self.assertEqual(passed_columns[9], 'futureYear')


if __name__ == '__main__':
    unittest.main()