# Copyright 2021 Google LLC
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
"""Tests for process.py"""

import csv
import os
import tempfile
import sys
import unittest

# Allows the following module imports to work when running as a script
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from us_epa.ghgrp import process
from us_epa.util import crosswalk as cw

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
_RAW_DATA_DIR = os.path.join(_CODEDIR, 'test_data')
_EXPECTED_DIR = os.path.join(_CODEDIR, 'test_data')

_CROSSWALK_PATH = os.path.join(_RAW_DATA_DIR, 'input_crosswalks.csv')


class ProcessTest(unittest.TestCase):

    def test_process_direct_emitters(self):
        self.maxDiff = None
        crosswalk = cw.Crosswalk(_CROSSWALK_PATH)
        with tempfile.TemporaryDirectory() as tmp_dir:
            fname = 'ghgrp_output_all_data.csv'
            got_filepath = os.path.join(tmp_dir, fname)
            process.process_data([
                (2010,
                 os.path.join(_RAW_DATA_DIR, 'input_2010_direct_emitters.csv')),
                (2011,
                 os.path.join(_RAW_DATA_DIR, 'input_2011_direct_emitters.csv')),
                (2012, os.path.join(_RAW_DATA_DIR,
                                    'input_2012_elec_equip.csv')),
                (2013,
                 os.path.join(_RAW_DATA_DIR,
                              'input_2013_local_distribution.csv')),
                (2014,
                 os.path.join(_RAW_DATA_DIR,
                              'input_2014_local_distribution.csv')),
                (2016,
                 os.path.join(_RAW_DATA_DIR,
                              'input_2016_gathering_and_boosting.csv')),
                (2016, os.path.join(_RAW_DATA_DIR,
                                    'input_2016_oil_and_gas.csv'))
            ], crosswalk, got_filepath)
            with open(got_filepath) as gotf:
                got = gotf.read()
                with open(os.path.join(_EXPECTED_DIR, fname)) as wantf:
                    want = wantf.read()
                    self.assertEqual(got, want)


if __name__ == '__main__':
    unittest.main()
