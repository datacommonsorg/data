# Copyright 2025 Google LLC
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
"""Unit tests for California School Performance (CAASPP) download and normalization."""

import io
import os
import sys
import unittest
from unittest.mock import patch

# Ensure import directory is in sys.path
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import download


class CaliforniaSchoolPerformanceDownloadTest(unittest.TestCase):

    def test_discover_year_urls_known_years(self):
        """Verify known year URL mapping retrieval."""
        urls_2015 = download.discover_year_urls(2015)
        self.assertIsNotNone(urls_2015)
        self.assertEqual(urls_2015,
                         ('sb_ca2015_all_csv_v3.zip', 'sb_ca2015_1_csv_v3.zip'))

        urls_2024 = download.discover_year_urls(2024)
        self.assertIsNotNone(urls_2024)
        self.assertEqual(urls_2024,
                         ('sb_ca2024_all_csv_v1.zip', 'sb_ca2024_1_csv_v1.zip'))

    @patch.object(download, 'probe_url_exists', return_value=False)
    def test_download_parse_years(self, _):
        """Verify year string parsing logic for single, list, range, and 'all'."""
        self.assertEqual(download.parse_years('2023'), [2023])
        self.assertEqual(download.parse_years('2023, 2024'), [2023, 2024])
        self.assertEqual(download.parse_years('2021-2023'), [2021, 2022, 2023])
        all_years = download.parse_years('all')
        self.assertIn(2015, all_years)
        self.assertIn(2024, all_years)

    def test_normalize_and_filter_stream_caret_delimited(self):
        """Verify record normalization and entity filtering for caret-delimited format."""
        sample_caret = (
            'County Code^District Code^School Code^Type ID^Test Year^Test ID^Student Group ID^Grade^'
            'Total Students Tested with Scores^Mean Scale Score^Percentage Standard Exceeded^'
            'Percentage Standard Met^Percentage Standard Met and Above^Percentage Standard Nearly Met^Percentage Standard Not Met\n'
            '00^00000^0000000^4^2024^1^1^3^100^2400.0^20.0^25.0^45.0^25.0^30.0\n'
            '01^00000^0000000^5^2024^1^1^3^60^2410.0^22.0^28.0^50.0^20.0^30.0\n'
            '01^12345^6789012^7^2024^1^1^3^50^2350.0^10.0^20.0^30.0^30.0^40.0\n'
        )
        stream = io.StringIO(sample_caret)
        rows = list(
            download.normalize_and_filter_stream(stream,
                                                 keep_all_entities=False))
        # School-level entity (Type ID 7) should be filtered out; State (4) and County (5) kept
        self.assertEqual(len(rows), 2)
        # State record
        self.assertEqual(rows[0][0], '00')
        self.assertEqual(rows[0][1], '2024')
        self.assertEqual(rows[0][2], '1')  # Student Group ID
        self.assertEqual(rows[0][3], '3')  # Grade
        self.assertEqual(rows[0][4], '1')  # Test ID
        self.assertEqual(rows[0][5], '100')  # Tested with scores
        # County record
        self.assertEqual(rows[1][0], '01')
        self.assertEqual(rows[1][1], '2024')

    def test_normalize_and_filter_stream_comma_delimited_legacy_headers(self):
        """Verify record normalization for comma-delimited data with older header aliases."""
        sample_comma = (
            '"County Code","District Code","School Code","Type ID","Test Year","Test Id","Subgroup ID","Grade",'
            '"Students with Scores","Mean Scale Score","Percentage Standard Exceeded",'
            '"Percentage Standard Met","Percentage Standard Met and Above","Percentage Standard Nearly Met","Percentage Standard Not Met"\n'
            '"00","00000","0000000","4","2016","1","1","4","120","2450.0","25.0","30.0","55.0","20.0","25.0"\n'
        )
        stream = io.StringIO(sample_comma)
        rows = list(
            download.normalize_and_filter_stream(stream,
                                                 keep_all_entities=False))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], '00')
        self.assertEqual(rows[0][1], '2016')
        self.assertEqual(rows[0][2], '1')  # Mapped Subgroup ID -> index 2
        self.assertEqual(rows[0][3], '4')  # Grade
        self.assertEqual(rows[0][4], '1')  # Mapped Test Id -> index 4
        self.assertEqual(rows[0][5],
                         '120')  # Mapped Students with Scores -> index 5

    def test_normalize_and_filter_stream_keep_all_entities(self):
        """Verify keep_all_entities=True retains school and district level entities."""
        sample_caret = (
            'County Code^District Code^School Code^Type ID^Test Year^Test ID^Student Group ID^Grade^'
            'Total Students Tested with Scores^Mean Scale Score^Percentage Standard Exceeded^'
            'Percentage Standard Met^Percentage Standard Met and Above^Percentage Standard Nearly Met^Percentage Standard Not Met\n'
            '00^00000^0000000^4^2024^1^1^3^100^2400.0^20.0^25.0^45.0^25.0^30.0\n'
            '01^12345^6789012^7^2024^1^1^3^50^2350.0^10.0^20.0^30.0^30.0^40.0\n'
        )
        stream = io.StringIO(sample_caret)
        rows = list(
            download.normalize_and_filter_stream(stream,
                                                 keep_all_entities=True))
        self.assertEqual(len(rows), 2)


if __name__ == '__main__':
    unittest.main()
