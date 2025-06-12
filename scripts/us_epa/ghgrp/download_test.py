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
"""Module to test the methods in Downloader Class"""

import unittest
from unittest.mock import patch, MagicMock
import os
from download import (Downloader, get_csv_filename, _DIRECT_EMITTERS_SHEET,
                      SHEET_NAMES_TO_CSV_FILENAMES)


class TestDownloader(unittest.TestCase):

    def setUp(self):
        self.test_dir = "tmp_test"
        self.downloader = Downloader(save_path=self.test_dir, url_year=2023)
        os.makedirs(self.test_dir, exist_ok=True)

    def test_csv_path_with_explicit_year(self):
        path = self.downloader._csv_path("example.csv", year=2020)
        expected = os.path.join(self.test_dir, "2020_example.csv")
        self.assertEqual(path, expected)

    def test_csv_path_without_year_uses_current(self):
        self.downloader.current_year = 2019
        path = self.downloader._csv_path("example.csv")
        expected = os.path.join(self.test_dir, "2019_example.csv")
        self.assertEqual(path, expected)

    def test_get_csv_filename_for_direct_emitters(self):
        name = "Direct GHG Emitters"
        result = get_csv_filename(name)
        self.assertEqual(result, "direct_emitters.csv")

    def test_get_csv_filename_for_known_sheets(self):
        for sheet, expected_file in SHEET_NAMES_TO_CSV_FILENAMES.items():
            self.assertEqual(get_csv_filename(sheet), expected_file)

    def test_get_csv_filename_for_unknown_sheet(self):
        self.assertIsNone(get_csv_filename("Unknown Sheet Name"))

    def tearDown(self):
        # Clean up temporary files and directory
        if os.path.exists(self.test_dir):
            for f in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, f))
            os.rmdir(self.test_dir)


if __name__ == '__main__':
    unittest.main()
