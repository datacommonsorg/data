"""Tests for process_sites_hazards.py"""

import os
import unittest
from .process_sites_hazards import process_site_hazards

_EXPECTED_SITE_COUNT = 1364


class ProcessTest(unittest.TestCase):

    def test_e2e(self):
        self.maxDiff = None
        base_path = os.path.dirname(__file__)
        processed_count = process_site_hazards(base_path, '')
        self.assertEqual(_EXPECTED_SITE_COUNT, processed_count)


if __name__ == '__main__':
    unittest.main()
