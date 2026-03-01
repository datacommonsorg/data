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
"""Unit tests for NgramMatcher."""

import unittest

from absl import app
from absl import logging
import ngram_matcher


class NgramMatcherTest(unittest.TestCase):

    def setUp(self):
        # logging.set_verbosity(2)
        return

    def test_lookup_string(self):
        matcher = ngram_matcher.NgramMatcher(config={'ngram_size': 4})
        matcher.add_key_value('Test Key 1', 1)
        matcher.add_key_value('TESTKey Two', 'two')
        matches = matcher.lookup('Test')
        self.assertEqual([('TESTKey Two', 'two'), ('Test Key 1', 1)], matches)
        self.assertTrue(
            matcher.lookup('Tester', config={'min_match_fraction': 0.1}))
        self.assertFalse(matcher.lookup('ABCDEF'))


if __name__ == '__main__':
    app.run()
    unittest.main()
