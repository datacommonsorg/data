# Copyright 2022 Google LLC
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
"""Tests for process_sites.py"""

import os
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from .process_sites import process_sites, check_geo_resolution

_EXPECTED_SITE_COUNT = 1


class ProcessTest(unittest.TestCase):

    def test_e2e(self):
        self.maxDiff = None
        base_path = os.path.dirname(__file__)
        base_path = os.path.join(base_path, './data/test_data')
        processed_count = process_sites(base_path, base_path)

        ## validate the sites processed
        self.assertEqual(_EXPECTED_SITE_COUNT, processed_count)

        ## validate the csvs
        test_df = pd.read_csv(os.path.join(base_path, 'superfund_sites.csv'))
        expected_df = pd.read_csv(
            os.path.join(base_path, 'superfund_sites_expected.csv'))
        assert_frame_equal(test_df, expected_df)

        ## clean up
        os.remove(os.path.join(base_path, 'superfund_sites.csv'))
        os.remove(os.path.join(base_path, 'superfund_sites.tmcf'))


if __name__ == '__main__':
    unittest.main()
