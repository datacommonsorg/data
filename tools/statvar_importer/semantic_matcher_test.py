# Copyright 2024 Google LLC
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
"""Test for semantic_matcher.py"""

import unittest

from absl import app
from absl import logging
from semantic_matcher import SemanticMatcher


class SemanticMatcherTest(unittest.TestCase):

    def setUp(self):
        # logging.set_verbosity(2)
        return

    def test_lookup(self):
        matcher = SemanticMatcher()
        # Add key values for lookup.
        matcher.add_key_value('child', 'age: [- 17 Years]')
        matcher.add_key_value('adult', 'age: [18 - Years]')
        matcher.add_key_value('USD', 'unit: USDollar')
        matcher.add_key_value('INR', 'unit: IndianRupee')

        # Lookup key:value for query strings.
        results = matcher.lookup('boy')
        # Should return list of keys, values matching the lookup string
        self.assertEqual(('child', 'age: [- 17 Years]'), results[0])
