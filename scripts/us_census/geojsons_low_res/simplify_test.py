# Copyright 2020 Google LLC
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
"""Tests the import_data.py script.

    Typical usage:
    python3 simplify_test.py
"""
import unittest
import geojson
import simplify
import os

TEST_DATA_DIR = "test-data"


class GeojsonSimplifierTest(unittest.TestCase):
    @staticmethod
    def get_file_output(raw_file, simple_file):
        simplifier = simplify.GeojsonSimplifier()
        simplifier.read_geojson(os.path.join(TEST_DATA_DIR, raw_file))
        simplifier.simplify()
        result = simplifier.geojson
        file = os.path.join(TEST_DATA_DIR, simple_file)
        with open(file, 'r') as f:
            expected_result = geojson.load(f)
        return result, expected_result

    def test_california(self):
        """Simplifies file ./test-data/california.geojson and compares result
        against ./test-data/california-simple.geojson
        """
        result, exp_result = self.get_file_output('california.geojson',
                                                  'california-simple.geojson')
        self.assertDictEqual(result, exp_result)

    def test_alabama(self):
        """Simplifies file ./test-data/alabama.geojson and compares result
        against ./test-data/alabama-simple.geojson
        """
        result, exp_result = self.get_file_output('alabama.geojson',
                                                  'alabama-simple.geojson')
        self.assertDictEqual(result, exp_result)

    def test_small_adjustement(self):
        """Tests a small adjustement (removed point is very well approximated
        by the resulting line) on a small, custom-made Polygon.
        """
        polygon_ex = {
            'type': 'Polygon',
            'coordinates': [[[[1, 1], [2, 2], [3, 3.1], [4, 0]]]]
        }
        polygon_simple_ex = {
            'type': 'Polygon',
            'coordinates': [[[[1, 1], [3, 3.1], [4, 0]]]]
        }
        simplifier = simplify.GeojsonSimplifier()
        simplifier.geojson = polygon_ex
        simplifier.simplify(epsilon=0.1)
        self.assertDictEqual(simplifier.geojson, polygon_simple_ex)

    def test_larger_adjustement(self):
        """Tests a moderate adjustement (removed point is poorly approximated
        by the resulting line) on a small, custom-made Polygon.
        """
        polygon_ex = {
            'type': 'Polygon',
            'coordinates': [[[[1, 0], [2, 5], [3, 0.25], [4, -0.5], [5, 0.1]]]]
        }
        polygon_simple_ex = {
            'type': 'Polygon',
            'coordinates': [[[[1, 0], [2, 5], [5, 0.1]]]]
        }
        simplifier = simplify.GeojsonSimplifier()
        simplifier.geojson = polygon_ex
        simplifier.simplify(epsilon=2)
        self.assertDictEqual(simplifier.geojson, polygon_simple_ex)

    def shortDescription(self):
        """Tells Unittest to print out the full docstrings of any failing tests.
        By default, it only prints the first line.
        """
        return " ".join(self._testMethodDoc.split())


if __name__ == '__main__':
    unittest.main()
