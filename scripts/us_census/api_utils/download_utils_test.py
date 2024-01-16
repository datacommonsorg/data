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

import os
import unittest
from .download_utils import *


class TestCommonUtil(unittest.TestCase):

    def test_download_url_list(self):
        url_list = [{
            'url': 'https://httpbin.org/get?a=1',
            'store_path': './tmp/1.json',
            'status': 'pending'
        }, {
            'url': 'https://httpbin.org/get?b=2',
            'store_path': './tmp/2.json'
        }, {
            'url': 'https://httpbin.org/status/204',
            'store_path': './tmp/3.json'
        }, {
            'url': 'https://httpbin.org/status/404',
            'store_path': './tmp/4.json',
            'status': 'pending'
        }]

        r = download_url_list(url_list, None, '', async_save_resp_json, {})

        self.assertEqual(r, 2)
        self.assertTrue(os.path.isfile('./tmp/1.json'))
        self.assertTrue(os.path.isfile('./tmp/2.json'))
        self.assertFalse(os.path.isfile('./tmp/3.json'))
        self.assertFalse(os.path.isfile('./tmp/4.json'))
        with open('./tmp/1.json') as fp:
            self.assertEqual(json.load(fp)['args'], {'a': '1'})
        with open('./tmp/2.json') as fp:
            self.assertEqual(json.load(fp)['args'], {'b': '2'})


if __name__ == '__main__':
    unittest.main()