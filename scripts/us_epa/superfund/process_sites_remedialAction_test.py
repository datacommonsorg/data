"""Tests for process_sites_remedialAction.py"""

import os
import unittest
from .process_sites_remedialAction import process_site_remedialAction

_EXPECTED_SITE_COUNT = 1426


class ProcessTest(unittest.TestCase):

    def test_e2e(self):
        self.maxDiff = None
        base_path = os.path.dirname(__file__)
        processed_count = process_site_remedialAction(base_path, '')
        self.assertEqual(_EXPECTED_SITE_COUNT, processed_count)


if __name__ == '__main__':
    unittest.main()
