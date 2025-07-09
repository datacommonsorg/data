# Copyright 2025 Google LLC
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

import os
import sys
import tempfile
import csv
import unittest
from unittest.mock import patch, call

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR))),
                 'util'))

from place_resolver import PlaceResolver


class GetLookupNameTest(unittest.TestCase):

    def test_get_lookup_name(self):
        """Tests that the lookup name is correctly formed from place name and country."""
        resolver = PlaceResolver()
        place = {'place_name': 'Mountain View', 'country': 'USA'}
        self.assertEqual(resolver._get_lookup_name('key', place),
                         'Mountain View USA')

    def test_get_lookup_name_country_in_name(self):
        """Tests that the country is not appended if it's already in the place name."""
        resolver = PlaceResolver()
        place = {'place_name': 'Mountain View, USA', 'country': 'USA'}
        self.assertEqual(resolver._get_lookup_name('key', place),
                         'Mountain View, USA')

    def test_get_lookup_name_use_key(self):
        """Tests that the key is used as the place name if 'place_name' is not present."""
        resolver = PlaceResolver()
        place = {'country': 'USA'}
        self.assertEqual(resolver._get_lookup_name('Mountain View', place),
                         'Mountain View USA')


class ResolveNameDcApiTest(unittest.TestCase):

    @patch('place_resolver.PlaceResolver.resolve_name_dc_api_batch')
    def test_resolve_name_dc_api(self, mock_dc_api):
        """Tests that the DC API is called and returns the correct dcids."""
        resolver = PlaceResolver(config_dict={'dc_api_key': 'test_key'})
        places = {
            'p1': {
                'place_name': 'Mountain View'
            },
            'p2': {
                'place_name': 'Sunnyvale'
            },
        }
        mock_dc_api.return_value = {
            'Mountain View': ['geoId/0649670'],
            'Sunnyvale': ['geoId/0677000'],
        }
        resolved_places = resolver.resolve_name_dc_api(places)
        self.assertEqual(len(resolved_places), 2)
        self.assertEqual(resolved_places['p1']['dcid'], 'geoId/0649670')
        self.assertEqual(resolved_places['p2']['dcid'], 'geoId/0677000')

    @patch('place_resolver.PlaceResolver.resolve_name_dc_api_batch')
    def test_resolve_name_dc_api_writes_to_cache(self, mock_dc_api):
        """Tests that the resolved places are written to a cache file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, 'cache.csv')
            places = {
                'p1': {
                    'place_name': 'Mountain View'
                },
                'p2': {
                    'place_name': 'Sunnyvale'
                },
            }
            mock_dc_api.return_value = {
                'Mountain View': ['geoId/0649670'],
                'Sunnyvale': ['geoId/0677000'],
            }

            with PlaceResolver(config_dict={
                    'dc_api_key': 'test_key',
                    'places_resolved_csv': cache_file
            }) as resolver:
                resolver.resolve_name_dc_api(places)

            # Check that the cache file was written to correctly.
            with open(cache_file, 'r') as f:
                reader = csv.DictReader(f)
                # Extract only the relevant columns into a list of lists.
                actual_rows = [
                    [row['place_name'], row['dcid']] for row in reader
                ]
                self.assertIn(['Mountain View', 'geoId/0649670'], actual_rows)
                self.assertIn(['Sunnyvale', 'geoId/0677000'], actual_rows)

    @patch('place_resolver.PlaceResolver.resolve_name_dc_api_batch')
    def test_resolve_name_dc_api_no_results(self, mock_dc_api):
        """Tests that the DC API handles cases where no results are found for a place."""
        resolver = PlaceResolver(config_dict={'dc_api_key': 'test_key'})
        places = {
            'p1': {
                'place_name': 'Mountain View'
            },
            'p2': {
                'place_name': 'PlaceThatDoesNotExist'
            },
        }
        mock_dc_api.return_value = {
            'Mountain View': ['geoId/0649670'],
        }
        resolved_places = resolver.resolve_name_dc_api(places)
        self.assertEqual(len(resolved_places), 1)
        self.assertEqual(resolved_places['p1']['dcid'], 'geoId/0649670')
        self.assertFalse('p2' in resolved_places)

    @patch('place_resolver.PlaceResolver.resolve_name_dc_api_batch')
    def test_resolve_name_dc_api_no_key(self, mock_dc_api):
        """Tests that the DC API is not called if no API key is provided."""
        resolver = PlaceResolver()
        places = {
            'p1': {
                'place_name': 'Mountain View'
            },
        }
        resolved_places = resolver.resolve_name_dc_api(places)
        self.assertEqual(len(resolved_places), 0)
        mock_dc_api.assert_not_called()


class ResolveLatLngTest(unittest.TestCase):

    @patch('place_resolver.dc_api_batched_wrapper')
    def test_resolve_latlng_single(self, mock_dc_api):
        """Tests resolving a single lat/lng to a dcid."""
        resolver = PlaceResolver()
        places = {'loc1': {'latitude': 37.42, 'longitude': -122.08}}
        mock_dc_api.return_value = {
            '37.420000,-122.080000': {
                'latitude': 37.42,
                'longitude': -122.08,
                'placeDcids': ['geoId/0649670']
            }
        }
        resolved_places = resolver.resolve_latlng(places)
        self.assertEqual(len(resolved_places), 1)
        self.assertEqual(resolved_places['loc1']['placeDcids'],
                         ['geoId/0649670'])

    @patch('place_resolver.dc_api_batched_wrapper')
    def test_resolve_latlng_multiple(self, mock_dc_api):
        """Tests resolving multiple lat/lngs to dcids."""
        resolver = PlaceResolver()
        places = {
            'loc1': {
                'latitude': 37.42,
                'longitude': -122.08
            },
            'loc2': {
                'latitude': 37.35,
                'longitude': -122.03
            }
        }
        mock_dc_api.return_value = {
            '37.420000,-122.080000': {
                'latitude': 37.42,
                'longitude': -122.08,
                'placeDcids': ['geoId/0649670']
            },
            '37.350000,-122.030000': {
                'latitude': 37.35,
                'longitude': -122.03,
                'placeDcids': ['geoId/0677000']
            }
        }
        resolved_places = resolver.resolve_latlng(places)
        self.assertEqual(len(resolved_places), 2)
        self.assertEqual(resolved_places['loc1']['placeDcids'],
                         ['geoId/0649670'])
        self.assertEqual(resolved_places['loc2']['placeDcids'],
                         ['geoId/0677000'])


class LookupNamesTest(unittest.TestCase):

    # TODO: Fix this test to not mock PlaceNameMatcher.
    @patch('place_resolver.PlaceNameMatcher.lookup')
    def test_lookup_names_single(self, mock_lookup):
        """Tests looking up a single place name."""
        resolver = PlaceResolver()
        places = {'p1': {'place_name': 'Mountain View'}}
        mock_lookup.return_value = [('Mountain View, CA', 'geoId/0649670')]
        resolved_places = resolver.lookup_names(places)
        self.assertEqual(len(resolved_places), 1)
        self.assertEqual(resolved_places['p1']['dcid'], 'geoId/0649670')
        self.assertEqual(resolved_places['p1']['place-name'],
                         'Mountain View, CA')

    # TODO: Fix this test to not mock PlaceNameMatcher.
    @patch('place_resolver.PlaceNameMatcher.lookup')
    def test_lookup_names_multiple(self, mock_lookup):
        """Tests looking up multiple place names."""
        resolver = PlaceResolver()
        places = {
            'p1': {
                'place_name': 'Mountain View'
            },
            'p2': {
                'place_name': 'Sunnyvale'
            }
        }

        mock_lookup.side_effect = [[('Mountain View, CA', 'geoId/0649670')],
                                   [('Sunnyvale, CA', 'geoId/0677000')]]

        resolved_places = resolver.lookup_names(places)
        self.assertEqual(len(resolved_places), 2)
        self.assertEqual(resolved_places['p1']['dcid'], 'geoId/0649670')
        self.assertEqual(resolved_places['p1']['place-name'],
                         'Mountain View, CA')
        self.assertEqual(resolved_places['p2']['dcid'], 'geoId/0677000')
        self.assertEqual(resolved_places['p2']['place-name'], 'Sunnyvale, CA')

        # Verify that the mock was called with the correct arguments.
        calls = [call('Mountain View', 10, {}), call('Sunnyvale', 10, {})]
        mock_lookup.assert_has_calls(calls)

    # TODO: Fix this test to not mock PlaceNameMatcher.
    @patch('place_resolver.PlaceNameMatcher.lookup')
    def test_lookup_names_no_results(self, mock_lookup):
        """Tests that no results are returned for a place that does not exist."""
        resolver = PlaceResolver()
        places = {'p1': {'place_name': 'PlaceThatDoesNotExist'}}
        mock_lookup.return_value = []
        resolved_places = resolver.lookup_names(places)
        self.assertEqual(len(resolved_places), 0)


class GetMapsPlaceIdTest(unittest.TestCase):

    @patch('place_resolver.request_url')
    def test_get_maps_placeid_single(self, mock_request):
        """Tests getting a single place id from the Maps API."""
        resolver = PlaceResolver(maps_api_key='test_key')
        mock_request.return_value = {
            'results': [{
                'place_id': 'ChIJ2eUge_W7j4ARb_3Yc41SgLg',
                'geometry': {
                    'location': {
                        'lat': 37.4224082,
                        'lng': -122.0840496
                    }
                }
            }]
        }
        result = resolver.get_maps_placeid('Mountain View')
        self.assertEqual(result['placeId'], 'ChIJ2eUge_W7j4ARb_3Yc41SgLg')
        self.assertEqual(result['latitude'], 37.4224082)
        self.assertEqual(result['longitude'], -122.0840496)

    @patch('place_resolver.request_url')
    def test_get_maps_placeid_no_results(self, mock_request):
        """Tests that no results are returned for a place that does not exist."""
        resolver = PlaceResolver(maps_api_key='test_key')
        mock_request.return_value = {'results': []}
        result = resolver.get_maps_placeid('PlaceThatDoesNotExist')
        self.assertEqual(result, {})

    @patch('place_resolver.request_url')
    def test_get_maps_placeid_no_key(self, mock_request):
        """Tests that the Maps API is not called if no API key is provided."""
        resolver = PlaceResolver()
        result = resolver.get_maps_placeid('Mountain View')
        self.assertEqual(result, {})
        mock_request.assert_not_called()

    @patch('place_resolver.request_url')
    def test_get_maps_placeid_return_format(self, mock_request):
        """Tests that get_maps_placeid returns lat and lng keys correctly."""
        resolver = PlaceResolver(maps_api_key='test_key')
        mock_request.return_value = {
            'results': [{
                'place_id': 'ChIJ2eUge_W7j4ARb_3Yc41SgLg',
                'geometry': {
                    'location': {
                        'lat': 37.4224082,
                        'lng': -122.0840496
                    }
                }
            }]
        }
        result = resolver.get_maps_placeid('Mountain View')
        self.assertIn('latitude', result)
        self.assertIn('longitude', result)
        self.assertNotIn('lat', result)
        self.assertNotIn('lng', result)


if __name__ == '__main__':
    unittest.main()
