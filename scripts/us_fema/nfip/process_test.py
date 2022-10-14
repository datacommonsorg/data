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
'''Unit tests for stat_var_processor.py.'''

import os
import pandas as pd
import sys
import tempfile
import unittest

from absl import app
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.join(_SCRIPT_DIR, '..', '..', 'statvar'))

from mcf_diff import diff_mcf_files
from process import NFIPStatVarDataProcessor
from stat_var_processor_test import TestStatVarProcessor

class TestNFIPStatVarProcessor(TestStatVarProcessor):

    def setUp(self):
      self.data_processor_class = NFIPStatVarDataProcessor
      self.test_files = [
            os.path.join(_SCRIPT_DIR, 'test_data', 'us_flood_nfip'),
      ]
      self.pv_maps = [
          'floodZone:' + os.path.join(_SCRIPT_DIR, 'us_flood_nfip_floodzone_pv_map.py'),
          'observationAbout:' + os.path.join(_SCRIPT_DIR, 'us_state_codes.py'),

      ]

