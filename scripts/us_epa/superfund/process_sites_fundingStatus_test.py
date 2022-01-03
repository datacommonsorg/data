"""Tests for process_sites_fundingStatus.py"""

import os
import unittest
from .process_sites_fundingStatus import process_site_funding

_EXPECTED_SITE_COUNT = 1715

class ProcessTest(unittest.TestCase):

    def test_e2e(self):
        self.maxDiff = None
        base_path = os.path.dirname(__file__)
        print("Processing superfund sites funding data...")
        processed_count = process_site_funding(base_path, '')
        self.assertEqual(_EXPECTED_SITE_COUNT, processed_count)


if __name__ == '__main__':
    unittest.main()