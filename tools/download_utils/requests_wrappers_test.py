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
from .requests_wrappers import *


class TestCommonUtil(unittest.TestCase):

    def test_request_url_json(self):
        self.assertEqual(
            request_url_json('https://httpbin.org/get?a=1')['args'], {'a': '1'})
        self.assertEqual(request_url_json('https://httpbin.org/status/204'),
                         {'http_err_code': 204})
        self.assertEqual(request_url_json('https://httpbin.org/status/404'),
                         {'http_err_code': 404})

    def test_request_post_json(self):
        self.assertEqual(
            request_post_json('https://httpbin.org/post', {'a': '1'})['data'],
            '{"a": "1"}')
        self.assertEqual(
            request_post_json('https://httpbin.org/status/204', {}),
            {'http_err_code': 204})
        self.assertEqual(
            request_post_json('https://httpbin.org/status/404', {}),
            {'http_err_code': 404})


if __name__ == '__main__':
    unittest.main()
