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
"""Unit tests for property_value_cache.py."""

import unittest

import os
import sys

from absl import app
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

from place_name_matcher import PlaceNameMatcher

_TEST_DIR = os.path.join(_SCRIPT_DIR, "test_data")


class PlaceNameMatcherTest(unittest.TestCase):

    def test_place_name_lookup(self):
        # Load a place name matcher with sample names.
        p = PlaceNameMatcher(
            place_file=os.path.join(_TEST_DIR, 'sample-places.csv'))

        # Lookup name where all words match
        matches = p.lookup('Delhi')
        # Expect multiple matches for the name
        self.assertTrue(len(matches) > 1)
        for name, dcid in matches:
            self.assertIn('Delhi', name)
        self.assertIn(('Delhi, Texas Texas', 'wikidataId/Q48851198'), matches)
        self.assertIn(('Delhi', 'wikidataId/Q1353'), matches)

        # Lookup names with different case and spaces
        matches = p.lookup('new delhi')
        self.assertTrue(len(matches) > 1)
        self.assertIn(
            ('New Delhi National Capital Region of Delhi', 'wikidataId/Q987'),
            matches)

        # Lookup with place type restrict
        matches = p.lookup(place_name='Delhi',
                           property_filters={'typeOf': ['State']})
        # Verify only one matching result for State
        self.assertEqual(matches, [('Delhi', 'wikidataId/Q1353')])

        # Lookup normalized place name for places with diacritics.
        matches = p.lookup('fleury en biare')
        self.assertEqual([('Fleury-en-BiÃ¨re', 'wikidataId/Q1460847')], matches)

        # Lookup unknown place
        self.assertFalse(p.lookup('Unknown Place'))

    def test_places_within(self):
        # Load a place name matcher for places in India
        p = PlaceNameMatcher(
            place_file=os.path.join(_TEST_DIR, 'sample-places.csv'),
            places_within=['country/IND'],
        )

        # Lookup name
        matches = p.lookup('Delhi')
        # Expect multiple matches for the name
        self.assertTrue(len(matches) > 1)
        for name, dcid in matches:
            self.assertIn('Delhi', name)
        self.assertIn(('Delhi', 'wikidataId/Q1353'), matches)
        self.assertIn(
            ('New Delhi National Capital Region of Delhi', 'wikidataId/Q987'),
            matches)
        # Verify places outside India are not returned.
        self.assertNotIn(('Delhi, Texas TX', 'wikidataId/Q48851198'), matches)
