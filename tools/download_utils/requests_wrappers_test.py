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
import unittest
from unittest import mock

from tools.download_utils import requests_wrappers


class RequestWrappersTest(unittest.TestCase):

    @mock.patch('tools.download_utils.requests_wrappers.requests.post')
    def test_request_post_json_merges_headers(self, mock_post):
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response

        result = requests_wrappers.request_post_json(
            'https://example.com/v2/node', {'k': 'v'},
            headers={'X-API-Key': 'secret'})

        self.assertEqual(result, {'ok': True})
        called_headers = mock_post.call_args.kwargs['headers']
        self.assertEqual(called_headers['Content-Type'], 'application/json')
        self.assertEqual(called_headers['X-API-Key'], 'secret')

    @mock.patch('tools.download_utils.requests_wrappers.requests.post')
    def test_request_post_json_defaults_headers(self, mock_post):
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response

        requests_wrappers.request_post_json('https://example.com/v2/node',
                                            {'k': 'v'})

        called_headers = mock_post.call_args.kwargs['headers']
        self.assertEqual(called_headers, {'Content-Type': 'application/json'})

    @mock.patch('tools.download_utils.requests_wrappers.requests.get')
    def test_request_url_json_success(self, mock_get):
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'hello': 'world'}
        mock_get.return_value = mock_response

        result = requests_wrappers.request_url_json('https://example.com/data')

        self.assertEqual(result, {'hello': 'world'})
        mock_get.assert_called_once_with('https://example.com/data')


if __name__ == '__main__':
    unittest.main()
