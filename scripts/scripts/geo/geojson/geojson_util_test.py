# Copyright 2024 Google LLC
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
"""Tests for geojson_util.py"""

import json
import os
import sys
import unittest

from shapely import geometry

# Allows the following module imports to work when running as a script
_SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))

import geojson_util


class GeojsonUtilTest(unittest.TestCase):

  def setUp(self):
    self.maxDiff = None
    self.valid_polygon_dict = {
        "type":
            "Polygon",
        "coordinates":
            [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
    }
    self.valid_polygon_str = json.dumps(json.dumps(self.valid_polygon_dict))
    self.invalid_polygon_dict = {
        "type":
            "Polygon",
        "coordinates":
            [[[0, 0], [1, 1], [0, 1], [1, 0], [0, 0]]],
    }
    self.multipolygon = geometry.MultiPolygon([
        geometry.Polygon([(0, 0), (1, 1), (1, 0), (0, 0)]),
        geometry.Polygon([(2, 2), (3, 4), (4, 2), (2, 2)])
    ])

  def test_get_geojson_dict(self):
    self.assertEqual(
        geojson_util.get_geojson_dict(self.valid_polygon_str),
        self.valid_polygon_dict)
    self.assertEqual(
        geojson_util.get_geojson_dict(self.valid_polygon_dict),
        self.valid_polygon_dict)
    self.assertIsNone(geojson_util.get_geojson_dict("invalid json"))

  def test_get_geojson_polygon(self):
    polygon = geojson_util.get_geojson_polygon(self.valid_polygon_dict)
    self.assertIsInstance(polygon, geometry.Polygon)
    self.assertTrue(polygon.is_valid)

    # Test with invalid polygon
    self.assertIsNone(
        geojson_util.get_geojson_polygon(self.invalid_polygon_dict))
    fixed_polygon = geojson_util.get_geojson_polygon(self.invalid_polygon_dict,
                                                     fix_polygon=True)
    self.assertIsInstance(fixed_polygon, geometry.Polygon)
    self.assertTrue(fixed_polygon.is_valid)

  def test_merge_geojson_str(self):
    poly1 = {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 0]]]}
    poly2 = {"type": "Polygon", "coordinates": [[[1, 1], [2, 2], [2, 1], [1, 1]]]}
    merged_geojson_str = geojson_util.merge_geojson_str([poly1, poly2])
    self.assertIsNotNone(merged_geojson_str)
    merged_polygon = geojson_util.get_geojson_polygon(merged_geojson_str)
    self.assertAlmostEqual(merged_polygon.area, 1.0)

  def test_round_floats(self):
    data = {"a": 1.23456789, "b": [2.3456789, {"c": 3.456789}]}
    rounded_data = geojson_util.round_floats(data, 3)
    self.assertEqual(rounded_data["a"], 1.235)
    self.assertEqual(rounded_data["b"][0], 2.346)
    self.assertEqual(rounded_data["b"][1]["c"], 3.457)

  def test_get_geojson_str(self):
    geojson_dict = {
        "type": "Polygon",
        "coordinates": [[[0.12345678, 0.12345678]]],
    }
    geojson_str = geojson_util.get_geojson_str(geojson_dict)
    expected_dict = {
        "type": "Polygon",
        "coordinates": [[[0.1234568, 0.1234568]]],
    }
    self.assertEqual(json.loads(json.loads(geojson_str)), expected_dict)

  def test_get_limited_geojson_str(self):
    # Create a large polygon
    from shapely.geometry import Point
    circle = Point(0, 0).buffer(1)
    large_polygon = geometry.Polygon(circle.exterior.coords)
    large_geojson_str = geojson_util.get_geojson_str(large_polygon)
    self.assertGreater(len(large_geojson_str), 500)

    limited_geojson_str, tolerance = geojson_util.get_limited_geojson_str(
        '', polygon=large_polygon, max_length=500)
    self.assertLessEqual(len(limited_geojson_str), 500)
    self.assertGreater(tolerance, 0)

  def test_polygon_remove_small_loops(self):
    # Polygon with a small inner loop
    outer = [(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)]
    inner = [(0.1, 0.1), (0.2, 0.1), (0.2, 0.2), (0.1, 0.2), (0.1, 0.1)]
    polygon = geometry.Polygon(outer, [inner])
    self.assertEqual(len(polygon.interiors), 1)

    # Remove the small loop
    processed_polygon = geojson_util.polygon_remove_small_loops(
        polygon, min_area_degrees=0.02)
    self.assertEqual(len(processed_polygon.interiors), 0)

    # Test with multipolygon
    processed_multipolygon = geojson_util.polygon_remove_small_loops(
        self.multipolygon, min_area_degrees=0.6)
    self.assertEqual(len(processed_multipolygon.geoms), 1)


if __name__ == '__main__':
  unittest.main()