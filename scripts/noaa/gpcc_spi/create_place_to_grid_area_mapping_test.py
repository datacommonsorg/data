# Copyright 2022 Google LLC
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
"""Unit tests for create_place_to_grid_area_mapping.py."""

from pathlib import Path
import sys
import unittest
from unittest import mock

from shapely import geometry

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.noaa.gpcc_spi import create_place_to_grid_area_mapping as mapping


class _FakeNodeEndpoint:

    def fetch_place_children(self, place_dcids, children_type, as_dict):
        del place_dcids, children_type, as_dict
        return {}

    def fetch_property_values(self, node_dcids, properties):
        del node_dcids, properties
        return {}


class _FakeClient:

    def __init__(self):
        self.node = _FakeNodeEndpoint()


class PlaceToGridMappingTest(unittest.TestCase):

    def test_get_place_by_type_parses_v2_children_response(self):
        client = _FakeClient()
        responses = [{
            'country/USA': [{
                'dcid': 'geoId/06'
            }, {
                'dcid': 'geoId/12'
            }]
        }, {
            'country/USA': [{
                'dcid': 'geoId/06085'
            }]
        }]
        with mock.patch.object(mapping,
                               'get_datacommons_client',
                               return_value=client), mock.patch.object(
                                   mapping,
                                   'dc_api_wrapper',
                                   side_effect=responses):
            got = mapping.get_place_by_type(['country/USA'],
                                            ['State', 'County'])
        self.assertEqual(got, ['geoId/06', 'geoId/12', 'geoId/06085'])

    def test_places_to_geo_jsons_parses_v2_property_response(self):
        client = _FakeClient()
        response = {
            'geoId/06': {
                'arcs': {
                    'geoJsonCoordinates': {
                        'nodes': [{
                            'value':
                                '{"type":"Polygon","coordinates":[[[0,0],[0,1],[1,1],[1,0],[0,0]]]}'
                        }]
                    }
                }
            },
            'geoId/12': {
                'arcs': {
                    'geoJsonCoordinates': {
                        'nodes': []
                    }
                }
            }
        }
        with mock.patch.object(mapping,
                               'get_datacommons_client',
                               return_value=client), mock.patch.object(
                                   mapping,
                                   'dc_api_batched_wrapper',
                                   return_value=response):
            got = mapping.places_to_geo_jsons(['geoId/06', 'geoId/12'])
        self.assertIn('geoId/06', got)
        self.assertNotIn('geoId/12', got)
        self.assertAlmostEqual(got['geoId/06'].area, 1.0)

    def test_create_place_to_grid_mapping(self):
        fully_contained = geometry.shape({
            'type':
                'Polygon',
            'coordinates': [[[0.2, 0.2], [0.2, 0.8], [0.8, 0.8], [0.8, 0.2],
                             [0.2, 0.2]]]
        })
        split_across_two_grids = geometry.shape({
            'type':
                'Polygon',
            'coordinates': [[[0.5, 0.2], [0.5, 0.8], [1.5, 0.8], [1.5, 0.2],
                             [0.5, 0.2]]]
        })
        with mock.patch.object(mapping,
                               'get_geojsons',
                               return_value={
                                   'geoId/06': fully_contained,
                                   'geoId/12': split_across_two_grids
                               }):
            got = mapping.create_place_to_grid_mapping(['geoId/06', 'geoId/12'],
                                                       write_results=False)
        self.assertEqual(got['geoId/06'], [{'grid': '0^0', 'ratio': 1}])
        self.assertEqual(got['geoId/12'][0]['grid'], '0^0')
        self.assertEqual(got['geoId/12'][1]['grid'], '0^1')
        self.assertAlmostEqual(got['geoId/12'][0]['ratio'], 0.5)
        self.assertAlmostEqual(got['geoId/12'][1]['ratio'], 0.5)


if __name__ == '__main__':
    unittest.main()
