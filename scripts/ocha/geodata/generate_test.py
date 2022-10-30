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
"""Tests for generate.py"""

import csv
import os
import tempfile
import sys
import unittest

# Allows the following module imports to work when running as a script
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from ocha.geodata import generate

_TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_data')


class GenerateTest(unittest.TestCase):

    def test_id_map(self):
        self.maxDiff = None
        input_gj_pattern = os.path.join(
            _TESTDIR, 'input/bgd_admbnda_adm2_bbs_20201113.shp.geojson')
        with tempfile.TemporaryDirectory() as tmp_dir:
            generate.generate_id_map(input_gj_pattern, tmp_dir)
            with open(os.path.join(_TESTDIR, 'expected/id_map.csv')) as wantf:
                with open(os.path.join(tmp_dir, 'id_map.csv')) as gotf:
                    self.assertEqual(gotf.read(), wantf.read())

    def test_mcf(self):
        self.maxDiff = None
        input_gj_pattern = os.path.join(
            _TESTDIR, 'input/bgd_admbnda_adm2_bbs_20201113.shp.geojson')
        input_id_map = os.path.join(_TESTDIR, 'input/resolved_id_map.csv')
        with tempfile.TemporaryDirectory() as tmp_dir:
            generate.generate_mcf(input_gj_pattern, input_id_map, tmp_dir)
            for f in [
                    'Bangladesh_AdministrativeArea2_GeoJSON.mcf',
                    'Bangladesh_AdministrativeArea2_GeoJSON_Simplified.mcf',
                    'Bangladesh_AdministrativeArea2_PCode.mcf'
            ]:
                with open(os.path.join(_TESTDIR, 'expected', f)) as wantf:
                    with open(os.path.join(tmp_dir, f)) as gotf:
                        got = gotf.read()
                        want = wantf.read()
                        with open('/tmp/bg.geojson', 'w') as text_file:
                            text_file.write(got)
                        self.assertEqual(got, want)
