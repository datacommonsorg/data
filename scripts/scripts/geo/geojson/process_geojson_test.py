# Copyright 2023 Google LLC
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
"""Tests for process_geojson.py"""

import os
import sys
import tempfile
import unittest

from absl import logging

# Allows the following module imports to work when running as a script
_SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))

import process_geojson

_TESTDIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'test_data')


class ProcessGeoJsonTest(unittest.TestCase):

  def _compare_files(self, actual_files: list, expected_files: list):
    """Raise a test failure if actual and expected files differ."""
    self.assertEqual(len(actual_files), len(expected_files))
    for i in range(0, len(actual_files)):
      logging.debug(
          f'Comparing file: {actual_files[i]} with {expected_files[i]}')
      with open(actual_files[i], 'r') as actual_f:
        actual_str = actual_f.read()
      with open(expected_files[i], 'r') as expected_f:
        expected_str = expected_f.read()
      self.assertEqual(
          actual_str,
          expected_str,
          f'Mismatched actual:{actual_files[i]} expected:{expected_files[i]}',
      )

  def setUp(self):
    # Log complete strings in assertEqual failures.
    self.maxDiff = None
    # logging.set_verbosity(2)

  def test_merge_nodes(self):
    nodes = [{
        'prop1': 'val1',
        'prop2': 'val2'
    }, {
        'prop1': 'val1',
        'prop3': 'val3'
    }]
    merged_node = process_geojson.merge_nodes(nodes)
    self.assertEqual(merged_node, {
        'prop1': 'val1',
        'prop2': 'val2',
        'prop3': 'val3'
    })

    # Test merging geojson
    nodes_with_geo = [{
        '#Geometry': {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 0]]]
        }
    }, {
        '#Geometry': {
            "type": "Polygon",
            "coordinates": [[[1, 1], [2, 2], [2, 1], [1, 1]]]
        }
    }]
    merged_node_with_geo = process_geojson.merge_nodes(nodes_with_geo)
    self.assertIn('#Geometry', merged_node_with_geo)

  def test_get_place_name(self):
    pvs = {'prop1': 'name1', 'prop2': 'name2'}
    self.assertEqual(
        process_geojson._get_place_name(pvs, ['prop1', 'prop2']), 'name1, name2')
    self.assertEqual(process_geojson._get_place_name(pvs, ['prop1']), 'name1')

  def test_get_dcid(self):
    pvs = {'dcid': 'test/dcid1'}
    self.assertEqual(process_geojson._get_dcid(pvs), 'test/dcid1')
    pvs_node = {'Node': 'dcid:test/dcid2'}
    self.assertEqual(process_geojson._get_dcid(pvs_node), 'test/dcid2')

  def test_eval_format_str(self):
    pvs = {'VAL1': 'Formatted', 'VAL2': 'Value'}

    # Get string value without any substitution
    self.assertEqual(
        'myProp: dcid:TestValue',
        process_geojson.eval_format_str('myProp: dcid:TestValue', pvs),
    )
    self.assertEqual(
        'dcid:TestDcid',
        process_geojson.eval_format_str('dcid:TestDcid', pvs),
    )

    # Format string value with quotes
    self.assertEqual(
        'myProp: "Formatted Value"',
        process_geojson.eval_format_str('myProp: "{VAL1} {VAL2}"', pvs),
    )

    # Evaluate an expression
    self.assertEqual(
        'myProp: "NewValue"',
        process_geojson.eval_format_str(
            """myProp: ='"NewValue"' if len(VAL1) > 2 else VAL2""", pvs),
    )

  def test_process_geojson(self):
    with tempfile.TemporaryDirectory() as tmp_dir:
      input_geojson = os.path.join(_TESTDIR, 'sample_input.geojson')
      output_mcf_prefix = os.path.join(tmp_dir, 'sample_output')
      geojson_dict = process_geojson.process_geojson_files(
          input_files=[input_geojson],
          num_input_nodes=sys.maxsize,
          properties=[],
          key_property='',
          place_name_props=['shapeName'],
          dcid_template='custom/{shapeName}',
          output_csv_file='',
          place_csv_files=os.path.join(_TESTDIR, 'places.csv'),
          place_csv_key='place_name',
          output_mcf_prefix=output_mcf_prefix,
          output_mcf_props=[
              (
                  'typeOf: ="dcid:AdministrativeArea1" if shapeType == "ADM1"'
                  ' else "dcid:AdministrativeArea2"'
              ),
              'name: "{place_name}"',
          ],
          simplification_levels=process_geojson.SIMPLIFICATION_LEVELS,
      )
      self.assertEqual(3, len(geojson_dict))
      # Check if dcid is generated correctly
      self.assertIn('custom/ADM1_PCODE_1', geojson_dict)
      out_files = [
          'sample_output.mcf',
          'sample_output_simplified_DP1.mcf',
          'sample_output_simplified_DP2.mcf',
          'sample_output_simplified_DP3.mcf',
      ]
      self._compare_files(
          actual_files=[os.path.join(tmp_dir, file) for file in out_files],
          expected_files=[os.path.join(_TESTDIR, file) for file in out_files],
      )


if __name__ == '__main__':
  unittest.main()