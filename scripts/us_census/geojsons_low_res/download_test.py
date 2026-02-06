# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for scripts/us_census/geojsons_low_res/download.py."""

from pathlib import Path
import sys
import unittest
from unittest import mock

from datacommons_client.endpoints.response import NodeResponse

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

import scripts.us_census.geojsons_low_res.download as download


def _build_node_response(data):
    return NodeResponse.model_validate({'data': data})


class _FakeNodeEndpoint:

    def __init__(self, children_response=None, geojson_response=None):
        self._children_response = children_response or {}
        self._geojson_response = geojson_response
        self.fetch_place_children_call_count = 0
        self.fetch_property_values_calls = []

    def fetch_property_values(self, node_dcids, properties):
        self.fetch_property_values_calls.append((list(node_dcids), properties))
        if properties == 'geoJsonCoordinates':
            if self._geojson_response is None:
                raise AssertionError(
                    'geoJsonCoordinates response was not configured')
            return self._geojson_response
        raise AssertionError(f'Unexpected property request: {properties}')

    def fetch_place_children(self, place_dcids, children_type, as_dict):
        del place_dcids, children_type, as_dict
        self.fetch_place_children_call_count += 1
        return self._children_response


class _FakeClient:

    def __init__(self, node_endpoint):
        self.node = node_endpoint


class DownloadTest(unittest.TestCase):

    def test_download_data_parses_geoid_subareas_only(self):
        children_response = {
            'country/USA': [{
                'dcid': 'geoId/06'
            }, {
                'dcid': 'wikidataId/Q30'
            }]
        }
        geojson_response = _build_node_response({
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
            'wikidataId/Q30': {
                'arcs': {
                    'geoJsonCoordinates': {
                        'nodes': [{
                            'value':
                                '{"type":"Polygon","coordinates":[[[2,2],[2,3],[3,3],[3,2],[2,2]]]}'
                        }]
                    }
                }
            }
        })
        client = _FakeClient(
            _FakeNodeEndpoint(children_response, geojson_response))

        with mock.patch.object(download,
                               'get_datacommons_client',
                               return_value=client), mock.patch.object(
                                   download,
                                   'dc_api_get_node_property',
                                   return_value={
                                       'country/USA': {
                                           'typeOf': 'Country'
                                       }
                                   }):
            loader = download.GeojsonDownloader()
            loader.download_data(place='country/USA', level=1)

        self.assertEqual(client.node.fetch_place_children_call_count, 1)
        self.assertEqual(loader.geojsons['geoId/06'][0]['type'], 'Polygon')
        self.assertIsInstance(loader.geojsons['geoId/06'][0], dict)
        self.assertIsInstance(loader.geojsons['wikidataId/Q30'][0], str)

    def test_download_data_raises_for_invalid_level(self):
        client = _FakeClient(_FakeNodeEndpoint())

        with mock.patch.object(download,
                               'get_datacommons_client',
                               return_value=client), mock.patch.object(
                                   download,
                                   'dc_api_get_node_property',
                                   return_value={
                                       'country/USA': {
                                           'typeOf': 'Country'
                                       }
                                   }):
            loader = download.GeojsonDownloader()
            with self.assertRaisesRegex(ValueError,
                                        'Desired level does not exist.'):
                loader.download_data(place='country/USA', level=4)

        self.assertEqual(client.node.fetch_place_children_call_count, 0)
        self.assertEqual(client.node.fetch_property_values_calls, [])


if __name__ == '__main__':
    unittest.main()
