# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Tests for download_util.py'''

import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

import download_util


class TestCounters(unittest.TestCase):

    def setUp(self):
        # Setup a response for non-existant URL for latest tests
        download_util.set_test_url_download_response('http://test.case.com/',
                                                     {'id': 123},
                                                     {"name": "abc"})
        download_util.set_test_url_download_response(
            url='gs://myproject/mybucket/config.json',
            params={},
            response=b'{"param": "value"}')

    def test_request_url(self):
        # Download URL with GET parameters
        response = download_util.request_url(
            url='https://api.datacommons.org/v2/resolve',
            params={
                'nodes': ['india'],
                'property': '<-description->dcid'
            },
            output='JSON')
        self.assertTrue(isinstance(response, dict))
        try:
            nodes = response['entities'][0]['candidates']
        except (KeyError, TypeError) as e:
            self.fail(
                f'Failed to parse nodes from API response. Check response structure. Error: {e}. Response: {response}'
            )
        country_dcids = [node.get('dcid', '') for node in nodes]
        self.assertIn('country/IND', country_dcids)

    def test_prefilled_url(self):
        test_response = download_util.request_url(url='http://test.case.com/',
                                                  params={'id': 123},
                                                  output='json')
        self.assertEqual({'name': 'abc'}, test_response)

    def test_download_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            filename = os.path.join(tmp_dir, 'test.json')
            download_util.download_file_from_url(
                url='gs://myproject/mybucket/config.json', output_file=filename)
            self.assertTrue(os.path.exists(filename))
            with open(filename) as fp:
                contents = fp.read()
                self.assertEqual('{"param": "value"}', contents)
