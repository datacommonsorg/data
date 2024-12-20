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
"""Tests for s2_mapper.py"""

import csv
import os
import tempfile
import sys
import unittest

# Allows the following module imports to work when running as a script
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from geolocation.s2cells import s2_mapper

_TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_data')


class S2MapperTest(unittest.TestCase):

    def test_e2e(self):
        self.maxDiff = None
        input_csv = os.path.join(_TESTDIR, 'input.csv')
        input_json = os.path.join(_TESTDIR, 'input.json')
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = s2_mapper.Processor(input_json, input_csv, tmp_dir)
            p.generate()
            with open(os.path.join(_TESTDIR, 'expected.csv')) as wantf:
                with open(os.path.join(tmp_dir, "mapped_input.csv")) as gotf:
                    self.assertEqual(gotf.read(), wantf.read())
            with open(os.path.join(_TESTDIR, 'expected.mcf')) as wantf:
                with open(os.path.join(tmp_dir, "s2cells_input.mcf")) as gotf:
                    self.assertEqual(gotf.read(), wantf.read())
