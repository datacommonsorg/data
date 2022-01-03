"""Tests for process_sites.py"""

import os
import unittest
from .process_sites import process_sites

_EXPECTED_SITE_COUNT = 1715

class ProcessTest(unittest.TestCase):

    def test_e2e(self):
        self.maxDiff = None
        base_path = os.path.dirname(__file__)
        print("Processing superfund sites base data...")
        processed_count = process_sites(base_path, '')
        self.assertEqual(_EXPECTED_SITE_COUNT, processed_count)


if __name__ == '__main__':
    unittest.main()
