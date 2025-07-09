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

import os
import tempfile
import unittest

from absl import app
from absl import logging
from property_value_cache import (_get_value_list, PropertyValueCache,
                                     flatten_dict)


class PropertyValueCacheCoreTest(unittest.TestCase):

    def test_add_new_entry(self):
        """Tests adding a new entry to the cache."""
        pv_cache = PropertyValueCache()
        pv_cache.add({'name': 'India', 'dcid': 'country/IND'})
        expected_entry = {
            'name': 'India',
            'dcid': 'country/IND',
        }
        self.assertEqual(expected_entry, pv_cache.get_entry('India', 'name'))

    def test_add_or_update_entry_with_new_pvs(self):
        """Tests updating an existing entry with new property values."""
        pv_cache = PropertyValueCache()
        pv_cache.add({'name': 'California', 'dcid': 'geoId/06'})
        pv_cache.add({'dcid': 'geoId/06', 'typeOf': 'AdministrativeArea1'})
        pv_cache.add({'dcid': 'geoId/06', 'typeOf': 'State', 'name': 'CA'})
        expected_entry = {
            'name': ['California', 'CA'],
            'dcid': 'geoId/06',
            'typeOf': ['AdministrativeArea1', 'State'],
        }
        self.assertEqual(expected_entry,
                         pv_cache.get_entry(prop='name', value='California'))

    def test_get_entry_with_different_keys(self):
        """Tests retrieving an entry using different key properties."""
        pv_cache = PropertyValueCache()
        pv_cache.add({
            'name': ['California', 'CA'],
            'dcid': 'geoId/06',
            'typeOf': ['AdministrativeArea1', 'State'],
        })
        expected_entry = {
            'name': ['California', 'CA'],
            'dcid': 'geoId/06',
            'typeOf': ['AdministrativeArea1', 'State'],
        }
        self.assertEqual(expected_entry,
                         pv_cache.get_entry(prop='name', value='California'))
        self.assertEqual(expected_entry,
                         pv_cache.get_entry('geoId/06', 'dcid'))

    def test_get_entry_with_list_value(self):
        """Tests that a lookup with a list value returns an empty dictionary."""
        pv_cache = PropertyValueCache()
        pv_cache.add({'name': 'California', 'dcid': 'geoId/06'})
        self.assertEqual({}, pv_cache.get_entry(['California'], 'name'))

    def test_get_entry_with_non_key_property(self):
        """Tests that a lookup with a non-key property returns an empty dictionary."""
        pv_cache = PropertyValueCache()
        pv_cache.add({'name': 'California', 'dcid': 'geoId/06', 'typeOf': 'State'})
        self.assertEqual({}, pv_cache.get_entry('State', 'typeOf'))

    def test_get_entry_for_dict(self):
        """Tests retrieving an entry using a dictionary of property values."""
        pv_cache = PropertyValueCache()
        pv_cache.add({
            'dcid': 'country/IND',
            'placeId': 'ChIJkbeSa_BfYzARphNChaFPjNc'
        })
        expected_entry = {
            'dcid': 'country/IND',
            'placeId': 'ChIJkbeSa_BfYzARphNChaFPjNc',
        }
        self.assertEqual(
            expected_entry,
            pv_cache.get_entry_for_dict({
                'placeId': 'ChIJkbeSa_BfYzARphNChaFPjNc',
                'name': 'IND',
            }))
        self.assertFalse({}, pv_cache.get_entry_for_dict({'name': 'IND'}))


class PropertyValueCacheHelpersTest(unittest.TestCase):

    def test_normalize_string(self):
        """Tests the normalization of strings for lookup."""
        pv_cache = PropertyValueCache()
        self.assertEqual('abc', pv_cache.normalize_string('Abc'))
        self.assertEqual('abc def', pv_cache.normalize_string('Abc Def'))
        self.assertEqual('abcdef', pv_cache.normalize_string('Abc-Def'))

    def test_update_entry(self):
        """Tests updating an existing entry with new values."""
        pv_cache = PropertyValueCache()
        src = {'typeOf': 'State', 'name': 'CA'}
        dst = {
            'name': ['California'],
            'dcid': 'geoId/06',
            'typeOf': ['AdministrativeArea1']
        }
        pv_cache.update_entry(src, dst)
        expected = {
            'name': ['California', 'CA'],
            'dcid': 'geoId/06',
            'typeOf': ['AdministrativeArea1', 'State']
        }
        self.assertEqual(expected, dst)

    def test_flatten_dict_by_single_property(self):
        """Tests flattening a dictionary by a single property with multiple values."""
        pvs = {
            'name': ['California', 'CA'],
            'dcid': 'geoId/06',
            'typeOf': ['AdministrativeArea1', 'State'],
        }
        flattened_pvs = flatten_dict(pvs, ['name'])
        self.assertCountEqual(
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

    def test_flatten_dict_by_multiple_properties(self):
        """Tests flattening a dictionary by multiple properties."""
        pvs = {
            'name': ['California', 'CA'],
            'dcid': 'geoId/06',
            'typeOf': ['AdministrativeArea1', 'State'],
        }
        name_type_pvs = flatten_dict(pvs, ['name', 'typeOf'])
        self.assertCountEqual(
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

    def test_flatten_dict_with_unlisted_property(self):
        """Tests flattening with a property that is not a list."""
        pvs = {
            'name': ['California', 'CA'],
            'dcid': 'geoId/06',
            'typeOf': ['AdministrativeArea1', 'State'],
        }
        merged_pvs = {
            'name': 'California,CA',
            'dcid': 'geoId/06',
            'typeOf': 'AdministrativeArea1,State',
        }
        self.assertCountEqual([merged_pvs], flatten_dict(pvs, ['dcid']))


class GetValueListTest(unittest.TestCase):

    def test_string_to_list(self):
        """Tests converting a comma-separated string."""
        self.assertCountEqual(['a', 'b', 'c'], _get_value_list('a,b,c'))

    def test_list_input(self):
        """Tests passing a list as input."""
        self.assertCountEqual(['a', 'b'], _get_value_list(['a', 'b']))

    def test_set_input(self):
        """Tests passing a set as input."""
        self.assertCountEqual(['a', 'b'], _get_value_list({'a', 'b'}))

    def test_duplicates(self):
        """Tests passing a list with duplicate values."""
        self.assertCountEqual(['a', 'b'], _get_value_list('a,b,a'))

    def test_empty_string(self):
        """Tests passing an empty string."""
        self.assertCountEqual([], _get_value_list(''))

    def test_none(self):
        """Tests passing None as input."""
        self.assertCountEqual([], _get_value_list(None))

    def test_unsupported_type(self):
        """Tests passing an unsupported type as input."""
        self.assertCountEqual([1], _get_value_list(1))


class IsDirtyTest(unittest.TestCase):

    def test_initial_state(self):
        """Tests that the cache is not dirty after initialization."""
        pv_cache = PropertyValueCache()
        self.assertFalse(pv_cache.is_dirty())

    def test_dirty_after_add(self):
        """Tests that the cache is dirty after adding a new entry."""
        pv_cache = PropertyValueCache()
        pv_cache.add({'name': 'India', 'dcid': 'country/IND'})
        self.assertTrue(pv_cache.is_dirty())

    def test_not_dirty_after_save(self):
        """Tests that the cache is not dirty after saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'test.csv')
            pv_cache = PropertyValueCache(file_path)
            pv_cache.add({'name': 'India', 'dcid': 'country/IND'})
            pv_cache.save_cache_file()
            self.assertFalse(pv_cache.is_dirty())

    def test_dirty_after_update(self):
        """Tests that the cache is dirty after updating an entry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'test.csv')
            pv_cache = PropertyValueCache(file_path)
            pv_cache.add({'name': 'India', 'dcid': 'country/IND'})
            pv_cache.save_cache_file()
            self.assertFalse(pv_cache.is_dirty())
            pv_cache.add({'name': 'India', 'typeOf': 'Country'})
            self.assertTrue(pv_cache.is_dirty())


class DunderDelTest(unittest.TestCase):

    def test_del(self):
        """Tests that the cache is saved when the object is deleted."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'test.csv')
            pv_cache = PropertyValueCache(file_path)
            pv_cache.add({'name': 'India', 'dcid': 'country/IND'})
            del pv_cache
            with open(file_path, 'r') as f:
                self.assertIn('country/IND', f.read())

    def test_del_not_dirty(self):
        """Tests that the cache is not saved if it is not dirty."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'test.csv')
            pv_cache = PropertyValueCache(file_path)
            del pv_cache
            self.assertFalse(os.path.exists(file_path))


class GetLookupKeyTest(unittest.TestCase):

    def test_normalization_enabled(self):
        """Tests that the key is normalized when normalization is enabled."""
        pv_cache = PropertyValueCache(normalize_key=True)
        self.assertEqual('abcdef', pv_cache.get_lookup_key('Abc-Def'))

    def test_normalization_disabled(self):
        """Tests that the key is not normalized when normalization is disabled."""
        pv_cache = PropertyValueCache(normalize_key=False)
        self.assertEqual('Abc-Def', pv_cache.get_lookup_key('Abc-Def'))

    def test_list_input(self):
        """Tests that the first element is used when the input is a list."""
        pv_cache = PropertyValueCache()
        self.assertEqual('abc', pv_cache.get_lookup_key(['Abc', 'Def']))

    def test_empty_list_input(self):
        """Tests that an empty string is returned for an empty list."""
        pv_cache = PropertyValueCache()
        self.assertEqual('', pv_cache.get_lookup_key([]))

    def test_unsupported_type(self):
        """Tests that a warning is logged for an unsupported type."""
        pv_cache = PropertyValueCache()
        with self.assertLogs(level='WARNING') as log:
            self.assertEqual('123', pv_cache.get_lookup_key(123))
            self.assertIn('Unexpected type', log.output[0])

    def test_empty_string_input(self):
        """Tests that an empty string is returned for an empty string."""
        pv_cache = PropertyValueCache()
        self.assertEqual('', pv_cache.get_lookup_key(''))


class PropertyValueCacheFileTest(unittest.TestCase):

    def test_save_cache_file(self):
        """Tests saving the cache to a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'test.csv')
            pv_cache = PropertyValueCache(file_path)
            pv_cache.add({'name': 'California', 'dcid': 'geoId/06'})
            pv_cache.add({'name': 'India', 'dcid': 'country/IND'})
            pv_cache.save_cache_file()
            self.assertTrue(os.path.exists(file_path))

    def test_load_cache_from_file(self):
        """Tests loading the cache from a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'test.csv')
            with open(file_path, 'w') as f:
                f.write('name,dcid\n')
                f.write('California,geoId/06\n')
                f.write('India,country/IND\n')

            new_cache = PropertyValueCache(file_path)
            expected_entry = {'name': 'California', 'dcid': 'geoId/06'}
            self.assertEqual(expected_entry,
                             new_cache.get_entry('California', 'name'))
