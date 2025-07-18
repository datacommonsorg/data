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
import csv
import tempfile

from absl import app
from absl import logging
from property_value_cache import PropertyValueCache, flatten_dict


class PropertyValueCacheTest(unittest.TestCase):

    def test_add_simple_entry(self):
        """Tests that a simple entry is added to the cache correctly."""
        pv_cache = PropertyValueCache()
        entry = {'name': 'California', 'dcid': 'geoId/06'}
        pv_cache.add(entry)
        self.assertEqual(entry, pv_cache.get_entry('California'))

    def test_add_merges_properties(self):
        """Tests that adding an entry with a matching key merges the new properties."""
        pv_cache = PropertyValueCache()
        pv_cache.add({'name': 'California', 'dcid': 'geoId/06'})
        pv_cache.add({'dcid': 'geoId/06', 'typeOf': 'AdministrativeArea1'})
        pv_cache.add({'dcid': 'geoId/06', 'typeOf': 'State', 'name': 'CA'})

        expected_entry = {
            'name': ['California', 'CA'],
            'dcid': 'geoId/06',
            'typeOf': ['AdministrativeArea1', 'State'],
        }
        self.assertEqual(expected_entry, pv_cache.get_entry('California'))

    def test_get_entry_for_dict_success(self):
        """Tests successful entry lookup using a dictionary of property values."""
        pv_cache = PropertyValueCache()
        entry = {
            'dcid': 'country/IND',
            'name': 'India',
            'placeId': 'ChIJkbeSa_BfYzARphNChaFPjNc'
        }
        pv_cache.add(entry)

        lookup_dict = {
            'placeId': 'ChIJkbeSa_BfYzARphNChaFPjNc',
            'name': 'Non-matching name'
        }
        self.assertEqual(entry, pv_cache.get_entry_for_dict(lookup_dict))

    def test_get_entry_for_dict_failure(self):
        """Tests failed entry lookup when the dictionary has no matching keys."""
        pv_cache = PropertyValueCache()
        pv_cache.add({'name': 'India', 'dcid': 'country/IND'})
        self.assertEqual({}, pv_cache.get_entry_for_dict({'name': 'IND'}))

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

    @unittest.skip(
        "TODO: The cache currently merges entries with conflicting key property values instead of overwriting them. The desired behavior needs to be determined."
    )
    def test_conflicting_key_property_value_overwrites_existing(self):
        """Tests that adding an entry with a conflicting key property value overwrites the existing entry."""
        pv_cache = PropertyValueCache()
        entry1 = {'name': 'Conflict', 'dcid': 'dcid/1'}
        entry2 = {'name': 'Conflict', 'dcid': 'dcid/2'}

        pv_cache.add(entry1)
        self.assertEqual(pv_cache.get_entry('Conflict'), entry1)

        pv_cache.add(entry2)
        self.assertEqual(pv_cache.get_entry('Conflict'), entry2)

    def test_save_to_file_successfully(self):
        """Tests that the cache is saved to a file successfully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'test_save_cache.csv')
            pv_cache = PropertyValueCache(file_path)

            # Add an entry and assert that the cache is dirty
            pv_cache.add({
                'dcid': 'geoId/01',
                'name': 'Alabama',
                'typeOf': 'State'
            })
            self.assertTrue(pv_cache.is_dirty())

            # Save the cache and assert that it is no longer dirty
            pv_cache.save_cache_file()
            self.assertFalse(pv_cache.is_dirty())

            # Load the cache from the file and assert that it has the correct entry
            new_pv_cache = PropertyValueCache(file_path)
            reloaded_entry = new_pv_cache.get_entry('geoId/01')
            self.assertEqual(reloaded_entry['dcid'], 'geoId/01')
            self.assertEqual(reloaded_entry['name'], 'Alabama')
            self.assertEqual(reloaded_entry['typeOf'], 'State')

    def test_load_from_file_successfully(self):
        """Tests that the cache is loaded from a file successfully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary CSV file
            file_path = os.path.join(temp_dir, 'test_cache.csv')
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['dcid', 'name', 'typeOf'])
                writer.writerow(['geoId/01', 'Alabama', 'State'])
                writer.writerow(['geoId/02', 'Alaska', 'State'])

            # Load the cache from the file
            pv_cache = PropertyValueCache(file_path)

            # Assert that the cache has the correct number of entries
            self.assertEqual(pv_cache.num_entries(), 2)

            # Assert that an entry can be retrieved correctly
            expected_entry = {
                'dcid': 'geoId/01',
                'name': 'Alabama',
                'typeOf': 'State'
            }
            reloaded_entry = pv_cache.get_entry('geoId/01')
            self.assertEqual(reloaded_entry['dcid'], expected_entry['dcid'])
            self.assertEqual(reloaded_entry['name'], expected_entry['name'])
            self.assertEqual(reloaded_entry['typeOf'], expected_entry['typeOf'])

    def test_flatten_dict_by_single_property(self):
        """Tests flattening a dictionary by a single multi-valued property."""
        pvs = {
            'name': ['California', 'CA'],
            'dcid': 'geoId/06',
            'typeOf': ['AdministrativeArea1', 'State'],
        }
        expected = [
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
        ]
        self.assertEqual(expected, flatten_dict(pvs, ['name']))

    def test_flatten_dict_by_single_value_property(self):
        """Tests flattening a dictionary by a single-valued property."""
        pvs = {
            'name': ['California', 'CA'],
            'dcid': 'geoId/06',
            'typeOf': ['AdministrativeArea1', 'State'],
        }
        expected = [{
            'name': 'California,CA',
            'dcid': 'geoId/06',
            'typeOf': 'AdministrativeArea1,State',
        }]
        self.assertEqual(expected, flatten_dict(pvs, ['dcid']))

    def test_flatten_dict_by_multiple_properties(self):
        """Tests flattening a dictionary by multiple multi-valued properties."""
        pvs = {
            'name': ['California', 'CA'],
            'dcid': 'geoId/06',
            'typeOf': ['AdministrativeArea1', 'State'],
        }
        expected = [
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
        ]
        self.assertCountEqual(expected, flatten_dict(pvs, ['name', 'typeOf']))


class KeyNormalizationTest(unittest.TestCase):

    def test_lookup_with_normalization_enabled(self):
        """Tests that lookups are case-insensitive with normalization enabled."""
        pv_cache = PropertyValueCache(normalize_key=True)
        entry = {'name': 'California', 'dcid': 'geoId/06'}
        pv_cache.add(entry)
        self.assertEqual(entry, pv_cache.get_entry('california'))

    def test_lookup_with_normalization_disabled(self):
        """Tests that lookups are case-sensitive with normalization disabled."""
        pv_cache = PropertyValueCache(normalize_key=False)
        entry = {'name': 'California', 'dcid': 'geoId/06'}
        pv_cache.add(entry)
        self.assertEqual({}, pv_cache.get_entry('california'))
        self.assertEqual(entry, pv_cache.get_entry('California'))


class ListValuedPropertiesTest(unittest.TestCase):

    def test_add_and_get_list_valued_property(self):
        """Tests that a property with a list of values is added and retrieved correctly."""
        pv_cache = PropertyValueCache()
        entry = {
            'dcid': 'geoId/06',
            'name': 'California',
            'containedInPlace': ['country/USA', 'northamerica/USA']
        }
        pv_cache.add(entry)
        retrieved_entry = pv_cache.get_entry('geoId/06')
        self.assertEqual(entry, retrieved_entry)


class CustomKeyPropertiesTest(unittest.TestCase):

    def test_lookup_succeeds_with_custom_keys(self):
        """Tests that lookups succeed with a custom set of key properties."""
        pv_cache = PropertyValueCache(key_props=['custom_id', 'name'])
        entry = {'name': 'California', 'custom_id': 'CA', 'dcid': 'geoId/06'}
        pv_cache.add(entry)
        self.assertEqual(entry, pv_cache.get_entry('California'))
        self.assertEqual(entry, pv_cache.get_entry('CA'))

    def test_lookup_fails_for_non_key_property(self):
        """Tests that lookups fail for a property not in the custom key list."""
        pv_cache = PropertyValueCache(key_props=['custom_id', 'name'])
        entry = {'name': 'California', 'custom_id': 'CA', 'dcid': 'geoId/06'}
        pv_cache.add(entry)
        self.assertEqual({}, pv_cache.get_entry('geoId/06'))


class NegativeCachingTest(unittest.TestCase):

    def test_cache_stores_entries_with_empty_values(self):
        """Tests that the cache can store and retrieve entries with empty values."""
        pv_cache = PropertyValueCache()
        entry = {'name': 'KnownFailure', 'dcid': ''}
        pv_cache.add(entry)
        retrieved_entry = pv_cache.get_entry('KnownFailure')
        self.assertEqual(entry, retrieved_entry)


class SharedCacheTest(unittest.TestCase):

    def test_shared_cache_reflects_changes(self):
        """Tests that changes made to a shared cache file are reflected when reloaded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, 'shared_cache.csv')

            # Create the first cache instance and add an entry.
            cache1 = PropertyValueCache(cache_file)
            entry1 = {'name': 'California', 'dcid': 'geoId/06'}
            cache1.add(entry1)
            cache1.save_cache_file()

            # Create a second cache instance pointing to the same file.
            cache2 = PropertyValueCache(cache_file)
            reloaded_entry1 = cache2.get_entry('California')
            self.assertEqual(entry1['name'], reloaded_entry1['name'])
            self.assertEqual(entry1['dcid'], reloaded_entry1['dcid'])

            # Add a new entry to the second cache instance.
            entry2 = {'name': 'Nevada', 'dcid': 'geoId/32'}
            cache2.add(entry2)
            cache2.save_cache_file()

            # Reload the first cache instance and verify that it sees the new entry.
            cache1.load_cache_file(cache_file)
            reloaded_entry2 = cache1.get_entry('Nevada')
            self.assertEqual(entry2['name'], reloaded_entry2['name'])
            self.assertEqual(entry2['dcid'], reloaded_entry2['dcid'])


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


if __name__ == '__main__':
    app.run(unittest.main)
