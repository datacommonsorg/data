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
"""Tests for validate_geojson_mcf.py"""

import os
import sys
import tempfile
import unittest
import json

# Allows the following module imports to work when running as a script
_SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), 'tools',
                 'statvar_importer'))

import validate_geojson_mcf

_TESTDIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'test_data')


class ValidateGeojsonMcfTest(unittest.TestCase):

  def setUp(self):
    self.maxDiff = None
    self.valid_mcf = os.path.join(_TESTDIR, 'valid_geo.mcf')
    self.invalid_mcf = os.path.join(_TESTDIR, 'invalid_geo.mcf')

  def test_get_valid_geocordinate_nodes(self):
    nodes = {
        "valid_node": {
            "geoJsonCoordinates":
                json.dumps(
                    json.dumps({
                        "type":
                            "Polygon",
                        "coordinates":
                            [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
                    }))
        },
        "invalid_node": {
            "geoJsonCoordinates":
                json.dumps(
                    json.dumps({
                        "type":
                            "Polygon",
                        "coordinates":
                            [[[0, 0], [1, 1], [0, 1], [1, 0], [0, 0]]]
                    }))
        }
    }
    valid_nodes, invalid_nodes = validate_geojson_mcf.get_valid_geocordinate_nodes(
        nodes)
    self.assertIn("valid_node", valid_nodes)
    self.assertIn("invalid_node", invalid_nodes)

  def process_geo_mcf(self):
    with tempfile.TemporaryDirectory() as tmp_dir:
      output_file = os.path.join(tmp_dir, 'output.mcf')
      validate_geojson_mcf.process_geo_mcf(self.valid_mcf, output_file)
      self.assertTrue(os.path.exists(output_file))
      with open(output_file, 'r') as f:
        content = f.read()
        self.assertIn("dcid:valid_place", content)

      # Test with invalid file
      output_invalid_file = os.path.join(tmp_dir, 'output_invalid.mcf')
      validate_geojson_mcf.process_geo_mcf(self.invalid_mcf,
                                           output_invalid_file)
      # No valid nodes, so no output file should be created.
      self.assertFalse(os.path.exists(output_invalid_file))
      invalid_output = os.path.join(tmp_dir, 'output_invalid_invalid.mcf')
      self.assertTrue(os.path.exists(invalid_output))
      with open(invalid_output, 'r') as f:
        content = f.read()
        self.assertIn("dcid:invalid_place", content)


if __name__ == '__main__':
  unittest.main()