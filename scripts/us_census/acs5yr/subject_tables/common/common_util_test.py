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

from .common_util import *


class TestCommonUtil(unittest.TestCase):

    def test_token_in_list(self):
        self.assertTrue(token_in_list_ignore_case('a', ['a', 'b']))
        self.assertTrue(token_in_list_ignore_case('a', ['A', 'b']))
        self.assertTrue(token_in_list_ignore_case('A', ['a', 'b']))
        self.assertFalse(token_in_list_ignore_case('c', ['a', 'b']))
        self.assertFalse(token_in_list_ignore_case('C', ['a', 'b']))

    def test_column_ignore(self):
        spec_dict = {'ignoreColumns': ['a', 'B', 'C!!d!!e']}
        # token
        self.assertTrue(column_to_be_ignored('a!!e', spec_dict))
        self.assertTrue(column_to_be_ignored('A!!e', spec_dict))
        self.assertTrue(column_to_be_ignored('A!!b', spec_dict))
        self.assertFalse(column_to_be_ignored('f!!g', spec_dict))
        # entire column
        self.assertTrue(column_to_be_ignored('c!!D!!e', spec_dict))
        self.assertTrue(column_to_be_ignored('C!!d!!e', spec_dict))
        self.assertFalse(column_to_be_ignored('f!!g!!', spec_dict))
        # prefix
        self.assertFalse(column_to_be_ignored('C!!d', spec_dict))
        self.assertFalse(column_to_be_ignored('c!!d', spec_dict))
        # substring
        self.assertFalse(column_to_be_ignored('d!!e', spec_dict))
        self.assertFalse(column_to_be_ignored('d!!E', spec_dict))

    def test_tokens_from_column_list(self):
        self.assertEqual(
            sorted(get_tokens_list_from_column_list(['a!!b', 'a!!c', 'd!!e'])),
            sorted(['a', 'b', 'c', 'd', 'e']))

    # TODO test columns_from_CSVreader
    def test_columns_from_CSVreader(self):
        cur_dir = os.path.dirname(__file__)
        with open(os.path.join(cur_dir, './testdata/test1.csv')) as fp:
            r = csv.reader(fp)
            self.assertEqual(sorted(columns_from_CSVreader(r, True)),
                             sorted(['a!!b', 'c!!d', 'e!!f', 'g!!h', 'i!!j']))
        with open(os.path.join(cur_dir, './testdata/test2.csv')) as fp:
            r = csv.reader(fp)
            self.assertEqual(sorted(columns_from_CSVreader(r, False)),
                             sorted(['a!!b', 'c!!d', 'e!!f', 'g!!h', 'i!!j']))

    def test_get_spec_token_list(self):
        spec = {
            'pvs': {
                'p1': {
                    'a': 'v1',
                    'b': 'v2',
                    '_a': 'v1'
                },
                'p2': {
                    'c': 'v3',
                    'b': 'v4'
                }
            },
            'populationType': {
                'd': 'pop1',
                'e': 'pop2',
                'c': 'pop3'
            },
            'measurement': {
                'f': 'm1',
                'e': 'm2'
            },
            'ignoreTokens': ['j'],
            'ignoreColumns': ['k']
        }
        ret = get_spec_token_list(spec)
        self.assertEqual(sorted(ret['token_list']),
                         sorted(['a', 'b', 'c', 'd', 'e', 'f', 'j', 'k']))
        self.assertEqual(sorted(ret['repeated_list']), sorted(['b', 'c', 'e']))

    def test_find_missing_tokens(self):
        spec = {
            'pvs': {
                'p1': {
                    'a': 'v1',
                    'b': 'v2',
                    '_a': 'v1'
                },
                'p2': {
                    'c': 'v3',
                    'b': 'v4'
                }
            },
            'populationType': {
                'd': 'pop1',
                'e': 'pop2',
                'c': 'pop3'
            },
            'measurement': {
                'f': 'm1',
                'e': 'm2'
            },
            'ignoreTokens': ['j'],
            'ignoreColumns': ['k']
        }
        ret = find_missing_tokens(
            ['a', 'b', 'c', 'd', 'e', 'f', 'j', 'k', 'm', 'n'], spec)
        self.assertEqual(sorted(ret), sorted(['m', 'n']))
        ret = find_missing_tokens(['a', 'b', 'c', 'd', 'm', 'n'], spec)
        self.assertEqual(sorted(ret), sorted(['m', 'n']))


if __name__ == '__main__':
    unittest.main()
