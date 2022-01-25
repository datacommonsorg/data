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
        geo_map = check_geo_resolution()
        processed_count = process_sites(base_path, base_path, geo_map)

        ## validate the sites processed
        self.assertEqual(_EXPECTED_SITE_COUNT, processed_count)

        ## validate the csvs
        test_df = pd.read_csv(os.path.join(base_path, 'superfund_sites.csv'))
        expected_df = pd.read_csv(os.path.join(base_path, 'superfund_sites_expected.csv'))
        assert_frame_equal(test_df, expected_df)

        ## clean up
        os.remove(os.path.join(base_path, 'superfund_sites.csv'))
        os.remove(os.path.join(base_path, 'superfund_sites.tmcf'))
        

if __name__ == '__main__':
    unittest.main()
