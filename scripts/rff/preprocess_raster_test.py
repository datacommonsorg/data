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
import sys
from pathlib import Path
import types
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

if "osgeo" not in sys.modules:
    osgeo_module = types.ModuleType("osgeo")
    gdal_module = types.ModuleType("gdal")
    osgeo_module.gdal = gdal_module
    sys.modules["osgeo"] = osgeo_module
    sys.modules["osgeo.gdal"] = gdal_module

from scripts.rff import preprocess_raster


class FakeNodeEndpoint:

    def __init__(self, place_children):
        self._place_children = place_children

    def fetch_place_children(self, place_dcids, children_type, as_dict):
        return {"country/USA": self._place_children}

    def fetch_property_values(self, node_dcids, properties):
        raise AssertionError("fetch_property_values should not be called")


class FakeClient:

    def __init__(self, node):
        self.node = node


class PreprocessRasterTest(unittest.TestCase):

    def test_get_county_geoid_dp1(self):
        county = "geoId/06085"
        geojson = (
            '{"type":"Polygon","coordinates":[[[0,0],[0,2],[2,2],[2,0],[0,0]]]}'
        )
        dp1_properties = {
            county: {
                "arcs": {
                    "geoJsonCoordinatesDP1": {
                        "nodes": [{
                            "value": geojson
                        }],
                    },
                },
            },
        }
        node = FakeNodeEndpoint(place_children=[{"dcid": county}])
        client = FakeClient(node)
        with mock.patch.object(preprocess_raster,
                               "get_datacommons_client",
                               return_value=client), mock.patch.object(
                                   preprocess_raster,
                                   "dc_api_batched_wrapper",
                                   return_value=dp1_properties) as mock_wrapper:
            result = preprocess_raster.get_county_geoid(1.0, 1.0)
        self.assertEqual(result, county)
        self.assertEqual(mock_wrapper.call_count, 1)

    def test_get_county_geoid_fallback(self):
        county = "geoId/06085"
        geojson = (
            '{"type":"Polygon","coordinates":[[[0,0],[0,2],[2,2],[2,0],[0,0]]]}'
        )
        dp1_properties = {
            county: {
                "arcs": {
                    "geoJsonCoordinatesDP1": {
                        "nodes": [],
                    },
                },
            },
        }
        fallback_properties = {
            county: {
                "arcs": {
                    "geoJsonCoordinates": {
                        "nodes": [{
                            "value": geojson
                        }],
                    },
                },
            },
        }
        node = FakeNodeEndpoint(place_children=[{"dcid": county}])
        client = FakeClient(node)
        with mock.patch.object(preprocess_raster,
                               "get_datacommons_client",
                               return_value=client), mock.patch.object(
                                   preprocess_raster,
                                   "dc_api_batched_wrapper",
                                   side_effect=[
                                       dp1_properties, fallback_properties
                                   ]) as mock_wrapper:
            result = preprocess_raster.get_county_geoid(1.0, 1.0)
        self.assertEqual(result, county)
        self.assertEqual(mock_wrapper.call_count, 2)


if __name__ == '__main__':
    unittest.main()
