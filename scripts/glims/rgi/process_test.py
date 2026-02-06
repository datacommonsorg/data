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
"""Tests for process.py"""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.glims.rgi import process

_TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_data')


class _FakeNodeEndpoint:

    def __init__(self):
        self.fetch_place_children_calls = []
        self.fetch_property_values_calls = []

    def fetch_place_children(self, place_dcids, children_type, as_dict):
        self.fetch_place_children_calls.append(
            (list(place_dcids), children_type, as_dict))
        return {'Earth': [{'dcid': 'country/USA'}, {'dcid': 'country/CAN'}]}

    def fetch_property_values(self, node_dcids, properties):
        self.fetch_property_values_calls.append((list(node_dcids), properties))
        if properties == 'geoJsonCoordinatesDP2':
            return {
                'country/USA': {
                    'arcs': {
                        'geoJsonCoordinatesDP2': {
                            'nodes': [{
                                'value':
                                    '{"type":"Polygon","coordinates":[[[0,0],[0,1],[1,1],[1,0],[0,0]]]}'
                            }]
                        }
                    }
                },
                'country/CAN': {
                    'arcs': {
                        'geoJsonCoordinatesDP2': {
                            'nodes': []
                        }
                    }
                },
            }
        if properties == 'containedInPlace':
            return {
                'country/USA': {
                    'arcs': {
                        'containedInPlace': {
                            'nodes': [{
                                'dcid': 'northamerica'
                            }]
                        }
                    }
                },
                'country/CAN': {
                    'arcs': {
                        'containedInPlace': {
                            'nodes': [{
                                'dcid': 'northamerica'
                            }]
                        }
                    }
                },
            }
        raise AssertionError(f'Unexpected property request: {properties}')


class _FakeClient:

    def __init__(self):
        self.node = _FakeNodeEndpoint()


class ProcessTest(unittest.TestCase):

    def test_e2e(self):
        self.maxDiff = None
        input_pattern = os.path.join(_TESTDIR, 'input*.csv')
        with tempfile.TemporaryDirectory() as tmp_dir:
            process._process(input_pattern, tmp_dir, {}, {})
            with open(os.path.join(_TESTDIR, 'expected.csv')) as wantf:
                with open(os.path.join(tmp_dir, "rgi6_glaciers.csv")) as gotf:
                    self.assertEqual(gotf.read(), wantf.read())

    def test_load_geojsons_with_v2_response(self):
        client = _FakeClient()
        with mock.patch.object(process,
                               'get_datacommons_client',
                               return_value=client):
            geojsons, cip = process._load_geojsons()

        self.assertEqual(client.node.fetch_place_children_calls,
                         [(['Earth'], 'Country', True)])
        self.assertEqual(client.node.fetch_property_values_calls, [
            (['country/USA', 'country/CAN'], 'geoJsonCoordinatesDP2'),
            (['country/USA', 'country/CAN'], 'containedInPlace'),
        ])
        self.assertIn('country/USA', geojsons)
        self.assertNotIn('country/CAN', geojsons)
        self.assertEqual(geojsons['country/USA'].geom_type, 'Polygon')
        self.assertEqual(cip['country/USA'], ['northamerica'])
        self.assertEqual(cip['country/CAN'], ['northamerica'])
