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
"""Tests for earthengine_image.py"""

import os
import sys
import unittest
import ee

# Allows the following module imports to work when running as a script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import earthengine_image as eei

_TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_data')


class EarthengineImageTest(unittest.TestCase):

    def setUp(self):
        ee.Initialize()
        self.maxDiff = None

    def test_ee_generate_image(self):
        '''Verify creation of an earthengine image object.'''
        # Generate a flood image.
        config = dict(eei.EE_DEFAULT_CONFIG)
        config['ee_dataset'] = 'dynamic_world'
        config['band'] = 'water'
        config['band_min'] = 0.7
        config['ee_reducer'] = 'max'
        config['ee_dataset'] = 'dynamic_world'
        config['ee_mask'] = 'land'
        config['start_date'] = '2022-10-01'
        config['time_period'] = 'P1M'
        config['ee_bounds'] = '24.72,83.83,26.06,88.26'
        ee_image = eei.ee_generate_image(config)
        # Compare image id (description) with expected.
        ee_image_id = str(ee_image.id())
        with open(os.path.join(_TESTDIR, 'sample_floods_ee_image_id.txt'),
                  'r') as exp:
            expected_id = exp.read().strip()
            self.assertEqual(ee_image_id, expected_id)
