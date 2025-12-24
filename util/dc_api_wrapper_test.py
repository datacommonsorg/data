# Copyright 2022 Google LLC
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
"""Tests for dc_api_wrapper."""

import os
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

import dc_api_wrapper as dc_api
import datacommons as dc

from absl import logging


class TestDCAPIWrapper(unittest.TestCase):

    def test_dc_api_wrapper(self):
        """Test the wrapper for DC API."""
        api_function = dc.get_property_labels
        dcids = [
            'Count_Person',  # 'dcid:' namespace will be removed.
        ]
        args = {'dcids': dcids}
        response = dc_api.dc_api_wrapper(api_function, args)
        self.assertTrue(response is not None)
        self.assertTrue(dcids[0] in response)
        self.assertTrue('typeOf' in response['Count_Person'])

    def test_dc_api_batched_wrapper(self):
        """Test DC API wrapper for batched calls."""
        api_function = dc.get_property_values
        dcids = [
            'Count_Person',  # Statvar defined in DC
            'dcid:Count_Person_Male',  # 'dcid:' namespace will be removed.
            'dcid:NewStatVar_NotInDC',  # new statvar missing in DC
        ]
        args = {'prop': 'typeOf'}
        response = dc_api.dc_api_batched_wrapper(
            api_function, dcids, args, config={'dc_api_batch_size': 2})
        self.assertTrue(response is not None)
        self.assertEqual(response['Count_Person'], ['StatisticalVariable'])
        self.assertEqual(response['Count_Person_Male'], ['StatisticalVariable'])
        self.assertFalse(response['NewStatVar_NotInDC'])

    def test_dc_api_is_defined_dcid(self):
        """Test API wrapper for defined DCIDs."""
        dcids = [
            'geoId/06',  # Geo Id defined.
            'country/ZZZ',  # Geo Id not defined.
            'dcs:value',  # property defined
            'schema:Year',  # Class
        ]
        response = dc_api.dc_api_is_defined_dcid(
            dcids,
            {
                'dc_api_batch_size': 2,
            },
        )
        self.assertTrue(response is not None)
        self.assertEqual(len(response), len(dcids))
        self.assertTrue(response['geoId/06'])
        self.assertFalse(response['country/ZZZ'])
        # API wrapper preserves the namespace if any although DC API call is
        # without namespace prefix.
        self.assertTrue(response['dcs:value'])

    def test_dc_get_node_property_values(self):
        """Test API wrapper to get all property:values for a node."""
        node_pvs = dc_api.dc_api_get_node_property_values(['dcid:Count_Person'])
        self.assertTrue(node_pvs)
        # Verify the resposnse has dcid with the namespace prefix 'dcid:'
        self.assertTrue('dcid:Count_Person' in node_pvs)
        statvar_pvs = node_pvs['dcid:Count_Person']
        self.assertTrue('populationType' in statvar_pvs)
        self.assertTrue('measuredProperty' in statvar_pvs)
        self.assertEqual('StatisticalVariable', statvar_pvs['typeOf'])

    def test_dc_api_get_node_property(self):
        """Test API wrapper to get a single property for a node."""
        dcids = ['Count_Person']
        prop = 'name'
        response_v2 = dc_api.dc_api_get_node_property(dcids, prop,
                                                      {'dc_api_version': 'V2'})
        self.assertTrue(response_v2)
        self.assertIn('Count_Person', response_v2)
        # Note: The name of Count_Person is "Total population"
        self.assertEqual(response_v2['Count_Person'],
                         {'name': '"Total population"'})

    def test_dc_api_resolve_placeid(self):
        """Test API wrapper to resolve entity using a placeid."""
        placeids = ['ChIJT3IGqvxznW4Rqgw7pv9zYz8']
        response = dc_api.dc_api_resolve_placeid(placeids)
        self.assertTrue(response)
        self.assertIn('ChIJT3IGqvxznW4Rqgw7pv9zYz8', response)
        self.assertEqual(response['ChIJT3IGqvxznW4Rqgw7pv9zYz8'],
                         'wikidataId/Q9727')

    def test_dc_api_resolve_latlng(self):
        """Test API wrapper for latlng resolution."""
        latlngs = [{'latitude': 37.42, 'longitude': -122.08}]
        response = dc_api.dc_api_resolve_latlng(latlngs)

        # Truncate the dynamic parts of the response for a stable test.
        place_response = response.get('37.42-122.08', {})
        if place_response.get('placeDcids'):
            place_response['placeDcids'] = place_response['placeDcids'][:1]
        if place_response.get('places'):
            place_response['places'] = place_response['places'][:1]

        expected_response = {
            "37.42-122.08": {
                "latitude": 37.42,
                "longitude": -122.08,
                "placeDcids": ["geoId/0649670"],
                "places": [{
                    "dcid": "geoId/0649670",
                    "dominantType": "City"
                }]
            }
        }
        self.assertEqual(response, expected_response)

    def test_convert_v2_to_v1_coordinate_response(self):
        """Test coordinate response conversion from v2 to v1."""
        v2_response = {
            "entities": [{
                "node":
                    "37.42#-122.08",
                "candidates": [{
                    "dcid": "geoId/0649670",
                    "dominantType": "City"
                }, {
                    "dcid": "geoId/06085",
                    "dominantType": "County"
                }]
            }]
        }
        expected_v1_response = {
            "placeCoordinates": [{
                "latitude":
                    37.42,
                "longitude":
                    -122.08,
                "placeDcids": [
                    "geoId/0649670",
                    "geoId/06085",
                ],
                "places": [{
                    "dcid": "geoId/0649670",
                    "dominantType": "City"
                }, {
                    "dcid": "geoId/06085",
                    "dominantType": "County"
                }]
            }]
        }
        v1_response = dc_api._convert_v2_to_v1_coordinate_response(v2_response)
        self.assertEqual(v1_response, expected_v1_response)

    def test_convert_v1_to_v2_coordinate_request(self):
        """Test coordinate request conversion from v1 to v2."""
        v1_request = {
            "coordinates": [{
                "latitude": 37.42,
                "longitude": -122.08
            }]
        }
        expected_v2_request = {
            "nodes": ["37.42#-122.08"],
            "property": "<-geoCoordinate->dcid"
        }
        v2_request = dc_api._convert_v1_to_v2_coordinate_request(v1_request)
        self.assertEqual(v2_request, expected_v2_request)
