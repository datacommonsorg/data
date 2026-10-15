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
"""Unit tests for download_data.py."""

import os
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import download_data


class DownloadDataTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_dir = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()
        super().tearDown()

    def test_unzip_inputfile_success_and_cleans_stale_csv(self):
        stale_csv = os.path.join(self.input_dir, "wb_subnational_input.csv")
        with open(stale_csv, "w", encoding="utf-8") as f:
            f.write("stale,data\n1,2\n")

        zip_path = os.path.join(self.input_dir, "test_extract.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr(
                "uuid_Data.csv",
                "Country Name,2016 [YR2016]\nAfghanistan, Badakhshan,1216000.0\n",
            )
            zf.writestr("uuid_Series - Metadata.csv", "Meta,Value\n")

        download_data.unzip_inputfile(self.input_dir)

        output_csv = os.path.join(self.input_dir, "wb_subnational_input.csv")
        self.assertTrue(os.path.exists(output_csv))
        self.assertFalse(
            os.path.exists(
                os.path.join(self.input_dir, "uuid_Series - Metadata.csv")
            )
        )
        with open(output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Afghanistan, Badakhshan", content)

    def test_unzip_inputfile_missing_zip_raises(self):
        with self.assertRaises(RuntimeError):
            download_data.unzip_inputfile(self.input_dir)

    def test_unzip_inputfile_missing_data_csv_does_not_fallback_to_stale(self):
        stale_csv = os.path.join(self.input_dir, "wb_subnational_input.csv")
        with open(stale_csv, "w", encoding="utf-8") as f:
            f.write("stale,data\n1,2\n")

        zip_path = os.path.join(self.input_dir, "empty_extract.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("uuid_Series - Metadata.csv", "Meta,Value\n")

        with self.assertRaises(RuntimeError):
            download_data.unzip_inputfile(self.input_dir)
        self.assertFalse(os.path.exists(stale_csv))

    def test_preprocess_replaces_comma_in_country_name(self):
        csv_path = os.path.join(self.input_dir, "wb_subnational_input.csv")
        with open(csv_path, "w", encoding="latin1") as f:
            f.write(
                'Series Name, Country Name ,2016 [YR2016]\n'
                '"Population, total"," Afghanistan, Badakhshan ",1216000.0\n'
            )

        download_data.preprocess(self.input_dir)

        df = pd.read_csv(csv_path, encoding="utf-8")
        self.assertEqual(df.loc[0, "Country Name"], "Afghanistan- Badakhshan")

    @mock.patch.object(download_data.time, "sleep")
    @mock.patch.object(download_data.WebDriverWait, "until")
    @mock.patch.object(download_data.webdriver, "Chrome")
    def test_download_worldbank_polls_until_zip_ready(
        self, mock_chrome, mock_until, mock_sleep
    ):
        mock_driver = mock.MagicMock()
        mock_chrome.return_value = mock_driver
        mock_until.return_value = mock.MagicMock()

        stale_file = os.path.join(self.input_dir, "old.crdownload")
        with open(stale_file, "w", encoding="utf-8") as f:
            f.write("partial")

        def create_zip_on_poll(seconds):
            if seconds == 2:
                zip_path = os.path.join(self.input_dir, "downloaded.zip")
                with open(zip_path, "wb") as zf:
                    zf.write(b"PK\x03\x04dummy")

        mock_sleep.side_effect = create_zip_on_poll

        download_data.download_worldbank.__wrapped__(
            "https://example.com", self.input_dir
        )

        self.assertFalse(os.path.exists(stale_file))
        self.assertTrue(
            os.path.exists(os.path.join(self.input_dir, "downloaded.zip"))
        )
        mock_driver.set_page_load_timeout.assert_called_once_with(60)
        mock_driver.quit.assert_called_once()

    @mock.patch.object(download_data.time, "sleep")
    @mock.patch.object(download_data.WebDriverWait, "until")
    @mock.patch.object(download_data.webdriver, "Chrome")
    def test_download_worldbank_timeout_raises_and_closes_driver(
        self, mock_chrome, mock_until, mock_sleep
    ):
        mock_driver = mock.MagicMock()
        mock_chrome.return_value = mock_driver
        mock_until.return_value = mock.MagicMock()

        with self.assertRaises(RuntimeError):
            download_data.download_worldbank.__wrapped__(
                "https://example.com", self.input_dir
            )

        mock_driver.quit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
