# Copyright 2023 Google LLC
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
"""Tests for aggregate_util.py"""

import os
import sys
import unittest

from absl import logging

# Allows the following module imports to work when running as a script
_SCRIPTS_DIR = os.path.dirname(__file__)

from aggregation_util import aggregate_value, aggregate_dict


class AggregationUtilTest(unittest.TestCase):

    def test_aggregate_value(self):
        # Numeric value aggregations
        self.assertEqual(3, aggregate_value(1, 2, aggregate='sum'))
        self.assertEqual(7, aggregate_value(3, 4))
        self.assertEqual(1, aggregate_value(1, 10, aggregate='min'))
        self.assertEqual(10, aggregate_value(1, 10, aggregate='max'))

        # String value aggregations
        self.assertEqual('abc', aggregate_value('abc', 'def', aggregate='min'))
        self.assertEqual('def', aggregate_value('abc', 'def', aggregate='max'))
        self.assertEqual('abc,def',
                         aggregate_value('def', 'abc', aggregate='list'))
        self.assertEqual('abc,def',
                         aggregate_value('def', 'abc', aggregate='sum'))
        self.assertEqual('123,abc,def',
                         aggregate_value('abc,123', 'def', aggregate='list'))
        self.assertEqual({'abc', 'def'},
                         aggregate_value({'abc'}, {'def'}, aggregate='set'))
        self.assertEqual('abc', aggregate_value('abc', '123',
                                                aggregate='first'))
        self.assertEqual('123', aggregate_value('abc', '123', aggregate='last'))

    def test_aggregate_dict(self):
        # Aggregate values in a dict
        dict1 = {
            'key1': 123,
            'key1-1': 345,
            'key2': 'abc',
            'key3': [1, 2, 3],
            'key4': 1.23,
        }
        dict2 = {
            'key1': 456,
            'key2': 'def',
            'key2-2': 'lmn',
            'key3': ['45'],
            'key4': 2.34,
        }
        config = {
            'aggregate': 'sum',  # default aggregation
            # Per key aggregation
            'key1': {
                'aggregate': 'min'
            },
            'key2': {
                'aggregate': 'list'
            },
            'key4': {
                'aggregate': 'mean'
            },
        }
        expected_dict = {
            'key1': 123,
            'key1-1': 345,
            'key2': 'abc,def',
            'key2-2': 'lmn',
            'key3': ['45', 1, 2, 3],
            'key4': 1.785,
            '#key4:count': 2,
        }
        self.assertEqual(expected_dict, aggregate_dict(dict1, dict2, config))
        self.assertEqual(expected_dict, dict2)

        expected_dict1 = {
            'key1': 123,
            'key1-1': 690,
            'key2': 'abc,def',
            'key2-2': 'lmn',
            'key3': ['45', 1, 2, 3, 1, 2, 3],
            'key4': 1.5999999999999999,
            '#key4:count': 3,
        }
        self.assertEqual(expected_dict1, aggregate_dict(dict1, dict2, config))
