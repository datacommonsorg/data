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

from .status_file_utils import *


class TestCommonUtil(unittest.TestCase):
    url_list = []

    def setUp(self) -> None:
        os.makedirs('./tmp/', exist_ok=True)

        if os.path.isfile('./tmp/1.json'):
            os.remove('./tmp/1.json')
        if os.path.isfile('./tmp/2.json'):
            os.remove('./tmp/2.json')

        self.url_list = [{
            'url': 'https://httpbin.org/get?a=1',
            'store_path': './tmp/1.json',
            'status': 'ok'
        }, {
            'url': 'https://httpbin.org/get?b=2',
            'store_path': './tmp/2.json',
            'status': 'pending'
        }, {
            'url': 'https://httpbin.org/get?b=2',
            'store_path': './tmp/2.json'
        }, {
            'url': 'https://httpbin.org/status/204',
            'store_path': './tmp/3.json',
            'status': 'fail'
        }, {
            'url': 'https://httpbin.org/status/404',
            'store_path': './tmp/4.json',
            'status': 'fail_http',
            'http_code': '404'
        }]

    # def tearDown(self) -> None:
    #     if os.path.isfile('./tmp/1.json'):
    #         os.remove('./tmp/1.json')
    #     if os.path.isfile('./tmp/2.json'):
    #         os.remove('./tmp/2.json')

    def test_url_to_download(self):
        self.assertTrue(url_to_download(self.url_list[0]))
        self.assertTrue(url_to_download(self.url_list[1]))
        self.assertTrue(url_to_download(self.url_list[2]))

        with open('./tmp/2.json', 'w') as fp:
            json.dump({}, fp)
        self.assertFalse(url_to_download(self.url_list[1]))
        self.url_list[1]['force_fetch'] = True
        self.assertTrue(url_to_download(self.url_list[1]))

        self.assertTrue(url_to_download(self.url_list[3]))
        self.assertTrue(url_to_download(self.url_list[4]))

    def test_get_pending_url_list(self):
        ret_list = get_pending_url_list(self.url_list)
        self.assertEqual(ret_list,
                         [self.url_list[0], self.url_list[1], self.url_list[2]])
        with open('./tmp/2.json', 'w') as fp:
            json.dump({}, fp)

        ret_list = get_pending_url_list(self.url_list)
        self.assertEqual(ret_list, [self.url_list[0]])

    def test_get_failed_url_list(self):
        ret_list = get_failed_url_list(self.url_list)
        self.assertEqual(ret_list, [self.url_list[3], self.url_list[4]])
        self.url_list[3]['status'] = 'pending'
        ret_list = get_failed_url_list(self.url_list)
        self.assertEqual(ret_list, [self.url_list[4]])

    def test_get_failed_http_url_list(self):
        ret_list = get_failed_http_url_list(self.url_list)
        self.assertEqual(ret_list, [self.url_list[4]])
        self.url_list[4]['status'] = 'pending'
        ret_list = get_failed_http_url_list(self.url_list)
        self.assertEqual(ret_list, [])

    def test_get_pending_or_fail_url_list(self):
        ret_list = get_pending_or_fail_url_list(self.url_list)
        self.assertEqual(ret_list, self.url_list)
        with open('./tmp/2.json', 'w') as fp:
            json.dump({}, fp)
        ret_list = get_pending_or_fail_url_list(self.url_list)
        self.assertEqual(ret_list,
                         [self.url_list[0], self.url_list[3], self.url_list[4]])

    # TODO test sync_status_list


if __name__ == '__main__':
    unittest.main()