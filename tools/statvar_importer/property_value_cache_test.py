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

from absl import app
from absl import logging
from property_value_cache import PropertyValueCache, flatten_dict


class PropertyValueCacheTest(unittest.TestCase):

    def test_add_entry(self):
        pv_cache = PropertyValueCache()

        # Add an entry with name and dcid
        pv_cache.add({'name': 'California', 'dcid': 'geoId/06'})
        pv_cache.add({'name': 'India', 'dcid': 'country/IND'})

        # Add entry with additional properties
        pv_cache.add({'dcid': 'geoId/06', 'typeOf': 'AdministrativeArea1'})
        pv_cache.add({'dcid': 'geoId/06', 'typeOf': 'State', 'name': 'CA'})
        pv_cache.add({
            'dcid': 'country/IND',
            'placeId': 'ChIJkbeSa_BfYzARphNChaFPjNc'
        })

        expected_entry1 = {
            'name': ['California', 'CA'],
            'dcid': 'geoId/06',
            'typeOf': ['AdministrativeArea1', 'State'],
        }
        self.assertEqual(expected_entry1,
                         pv_cache.get_entry(prop='name', value='California'))
        self.assertEqual(expected_entry1,
                         pv_cache.get_entry('geoId/06', 'dcid'))

        expected_entry2 = {
            'name': 'India',
            'dcid': 'country/IND',
            'placeId': 'ChIJkbeSa_BfYzARphNChaFPjNc',
        }
        self.assertEqual(expected_entry2, pv_cache.get_entry('India', 'name'))
        self.assertEqual(expected_entry2,
                         pv_cache.get_entry('country/IND', 'dcid'))
        self.assertEqual(expected_entry2, pv_cache.get_entry('India'))

        # Lookup by dict with placeId
        # Match of one property, placeId is sufficient.
        self.assertEqual(
            expected_entry2,
            pv_cache.get_entry_for_dict({
                # Matching key
                'placeId': 'ChIJkbeSa_BfYzARphNChaFPjNc',
                # Key not matching
                'name': 'IND',
            }),
        )
        self.assertFalse({}, pv_cache.get_entry_for_dict({'name': 'IND'}))

    def test_add_duplicate_entry_does_not_change_cache(self):
        """Tests that adding a duplicate entry does not change the cache."""
        pv_cache = PropertyValueCache()
        entry = {'name': 'California', 'dcid': 'geoId/06'}

        # Add the entry for the first time
        pv_cache.add(entry)

        # Get the initial state
        initial_entry = pv_cache.get_entry('geoId/06')
        initial_num_entries = pv_cache.num_entries()

        # Add the same entry again
        pv_cache.add(entry)

        # Get the final state
        final_entry = pv_cache.get_entry('geoId/06')
        final_num_entries = pv_cache.num_entries()

        # Assert that the state has not changed
        self.assertEqual(initial_num_entries, final_num_entries)
        self.assertEqual(initial_entry, final_entry)

    def test_get_entry_without_prop_success(self):
        """Tests successful entry lookup by value without a specific property."""
        pv_cache = PropertyValueCache()
        entry = {
            'dcid': 'geoId/06',
            'name': 'California',
            'placeId': 'ChIJPV4oX_65j4ARVW8IJ6IJUYs'
        }
        pv_cache.add(entry)

        # Lookup by a value that exists in one of the key properties
        self.assertEqual(entry, pv_cache.get_entry('geoId/06'))
        self.assertEqual(entry, pv_cache.get_entry('California'))
        self.assertEqual(entry,
                         pv_cache.get_entry('ChIJPV4oX_65j4ARVW8IJ6IJUYs'))

    def test_get_entry_without_prop_failure(self):
        """Tests failed entry lookup for a non-existent value."""
        pv_cache = PropertyValueCache()
        entry = {'dcid': 'geoId/06', 'name': 'California'}
        pv_cache.add(entry)

        # Lookup by a value that does not exist
        self.assertEqual({}, pv_cache.get_entry('non-existent-value'))

    def test_flatten_dict(self):
        pvs = {
            'name': ['California', 'CA'],
            'dcid': 'geoId/06',
            'typeOf': ['AdministrativeArea1', 'State'],
        }
        flattened_pvs = flatten_dict(pvs, ['name'])
        self.assertEqual(
            [
                {
                    'name': 'California',
                    'dcid': 'geoId/06',
                    'typeOf': 'AdministrativeArea1,State',
                },
                {
                    'name': 'CA',
                    'dcid': 'geoId/06',
                    'typeOf': 'AdministrativeArea1,State',
                },
            ],
            flattened_pvs,
        )
        # expected pvs have lists joined with ','
        merged_pvs = {}
        for p, v in pvs.items():
            if isinstance(v, list):
                v = ','.join(v)
            merged_pvs[p] = v
        self.assertEqual([merged_pvs], flatten_dict(pvs, ['dcid']))
        name_type_pvs = flatten_dict(pvs, ['name', 'typeOf'])
        self.assertEqual(
            [
                {
                    'name': 'California',
                    'dcid': 'geoId/06',
                    'typeOf': 'AdministrativeArea1',
                },
                {
                    'name': 'CA',
                    'dcid': 'geoId/06',
                    'typeOf': 'AdministrativeArea1'
                },
                {
                    'name': 'California',
                    'dcid': 'geoId/06',
                    'typeOf': 'State'
                },
                {
                    'name': 'CA',
                    'dcid': 'geoId/06',
                    'typeOf': 'State'
                },
            ],
            name_type_pvs,
        )


class NormalizeStringTest(unittest.TestCase):

    def setUp(self):
        self.pv_cache = PropertyValueCache()

    def test_handles_case_and_whitespace(self):
        """Tests that normalization handles case and whitespace."""
        self.assertEqual(self.pv_cache.normalize_string("  LoWeR  CaSe  "),
                         "lower case")

    def test_removes_punctuation(self):
        """Tests that normalization removes punctuation."""
        self.assertEqual(self.pv_cache.normalize_string("With, Punctuation!"),
                         "with punctuation")

    def test_handles_diacritics(self):
        """Tests that normalization handles diacritics."""
        self.assertEqual(self.pv_cache.normalize_string("Åland Islands"),
                         "aland islands")

    def test_handles_non_string_input(self):
        """Tests that normalization handles non-string input."""
        self.assertEqual(self.pv_cache.normalize_string(123), "123")
