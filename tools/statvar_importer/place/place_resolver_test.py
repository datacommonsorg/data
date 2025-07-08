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
import unittest
from unittest.mock import patch

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR))),
                 'util'))

from place_resolver import PlaceResolver

class PlaceResolverTest(unittest.TestCase):

    def test_get_lookup_name(self):
        resolver = PlaceResolver()
        place = {
            'place_name': 'Mountain View',
            'country': 'USA'
        }
        self.assertEqual(resolver._get_lookup_name('key', place), 'Mountain View USA')

    def test_get_lookup_name_country_in_name(self):
        resolver = PlaceResolver()
        place = {
            'place_name': 'Mountain View, USA',
            'country': 'USA'
        }
        self.assertEqual(resolver._get_lookup_name('key', place), 'Mountain View, USA')

    def test_get_lookup_name_use_key(self):
        resolver = PlaceResolver()
        place = {
            'country': 'USA'
        }
        self.assertEqual(resolver._get_lookup_name('Mountain View', place), 'Mountain View USA')

    @patch('place_resolver.PlaceResolver.resolve_name_dc_api_batch')
    def test_resolve_name_dc_api(self, mock_dc_api):
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
            'Mountain View': ['dc/geoId/0649670'],
            'Sunnyvale': ['dc/geoId/0677000'],
        }
        resolved_places = resolver.resolve_name_dc_api(places)
        self.assertEqual(len(resolved_places), 2)
        self.assertEqual(resolved_places['p1']['dcid'], 'dc/geoId/0649670')
        self.assertEqual(resolved_places['p2']['dcid'], 'dc/geoId/0677000')

    @patch('place_resolver.PlaceResolver.resolve_name_dc_api_batch')
    def test_resolve_name_dc_api_no_results(self, mock_dc_api):
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
            'Mountain View': ['dc/geoId/0649670'],
        }
        resolved_places = resolver.resolve_name_dc_api(places)
        self.assertEqual(len(resolved_places), 1)
        self.assertEqual(resolved_places['p1']['dcid'], 'dc/geoId/0649670')
        self.assertFalse('p2' in resolved_places)

    @patch('place_resolver.PlaceResolver.resolve_name_dc_api_batch')
    def test_resolve_name_dc_api_no_key(self, mock_dc_api):
        resolver = PlaceResolver()
        places = {
            'p1': {
                'place_name': 'Mountain View'
            },
        }
        resolved_places = resolver.resolve_name_dc_api(places)
        self.assertEqual(len(resolved_places), 0)
        mock_dc_api.assert_not_called()

if __name__ == '__main__':
    unittest.main()
