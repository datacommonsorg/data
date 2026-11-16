# Copyright 2026 Google LLC
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
"""Unit tests for download_preprocess.py."""

import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch
import zipfile

import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import download_preprocess


class DownloadPreprocessTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "input_files")
        self.county_output_dir = os.path.join(self.output_dir,
                                              "county_input_file")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_check_and_create_dir(self):
        target_dir = os.path.join(self.temp_dir, "new_folder")
        self.assertFalse(os.path.exists(target_dir))
        download_preprocess.check_and_create_dir(target_dir)
        self.assertTrue(os.path.isdir(target_dir))

    @patch.object(download_preprocess, "_START_YEAR", 2008)
    @patch.object(download_preprocess, "_CYCLE_YEARS", 3)
    @patch.object(download_preprocess, "_CURRENT_YEAR", 2020)
    def test_get_target_years(self):
        years = download_preprocess.get_target_years()
        self.assertEqual(years, [2008, 2011, 2014, 2017, 2020])

    @patch("download_preprocess.requests.get")
    def test_resolve_file_url_selects_highest_ranked(self, mock_get):
        html = """
        <html><body>
            <a href="2014neiv1_tier1_summary.zip">v1</a>
            <a href="2014neiv2_tier1_summary.zip">v2</a>
            <a href="2014neiv1_final_tier1_summary.zip">final v1</a>
            <a href="other_file.csv">other</a>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html
        mock_get.return_value = mock_resp

        url, fname = download_preprocess.resolve_file_url(2014)
        self.assertEqual(fname, "2014neiv1_final_tier1_summary.zip")
        self.assertEqual(
            url,
            f"{download_preprocess._BASE_URL}/2014/tier_summaries/2014neiv1_final_tier1_summary.zip",
        )

    @patch("download_preprocess.requests.get")
    def test_resolve_file_url_http_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        url, fname = download_preprocess.resolve_file_url(2014)
        self.assertIsNone(url)
        self.assertIsNone(fname)

    @patch("download_preprocess.requests.get")
    def test_resolve_file_url_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException("Network failure")

        url, fname = download_preprocess.resolve_file_url(2014)
        self.assertIsNone(url)
        self.assertIsNone(fname)

    @patch("download_preprocess.requests.get")
    def test_download_file(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.iter_content.return_value = [b"chunk1_", b"chunk2"]
        mock_get.return_value = mock_resp

        dest_path = os.path.join(self.temp_dir, "test.zip")
        download_preprocess.download_file("https://example.com/test.zip",
                                          dest_path)

        self.assertTrue(os.path.exists(dest_path))
        with open(dest_path, "rb") as f:
            self.assertEqual(f.read(), b"chunk1_chunk2")

    def test_extract_databases_from_zip(self):
        os.makedirs(self.output_dir, exist_ok=True)
        zip_path = os.path.join(self.temp_dir, "sample.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("nested/test_db.accdb", b"dummy_db_content")
            zf.writestr("readme.txt", b"ignore_me")

        with patch.object(download_preprocess, "OUTPUT_DIR", self.output_dir):
            extracted = download_preprocess.extract_databases_from_zip(zip_path)

        expected_db = os.path.join(self.output_dir, "test_db.accdb")
        self.assertEqual(extracted, [expected_db])
        self.assertTrue(os.path.exists(expected_db))

    @patch("download_preprocess.subprocess.Popen")
    @patch("download_preprocess.subprocess.run")
    def test_export_db_to_csv_and_2014_tribal_fix(self, mock_run, mock_popen):
        mock_run_res = MagicMock()
        mock_run_res.stdout = "county_tier1\n"
        mock_run.return_value = mock_run_res

        mock_proc = MagicMock()
        mock_proc.stdout = [
            "stfips,state,pollutant,emissions\n",
            "01,Alabama,CO,100\n",
            ",Tribal,NOx,50\n",
        ]
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        db_path = os.path.join(self.temp_dir, "2014_summary.accdb")
        download_preprocess.export_db_to_csv(db_path, 2014)

        out_csv = os.path.join(self.temp_dir, "2014_summary_county_tier1.csv")
        self.assertTrue(os.path.exists(out_csv))

        with open(out_csv, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]

        self.assertEqual(
            lines,
            [
                "year,stfips,state,pollutant,emissions",
                "2014,01,Alabama,CO,100",
                "2014,88,Tribal,NOx,50",
            ],
        )

    @patch("download_preprocess.export_db_to_csv")
    @patch("download_preprocess.download_file")
    @patch("download_preprocess.resolve_file_url")
    @patch("download_preprocess.get_target_years")
    def test_main_moves_county_csv_files(
        self,
        mock_get_years,
        mock_resolve_url,
        mock_download,
        mock_export,
    ):
        mock_get_years.return_value = [2017]
        mock_resolve_url.return_value = (
            "https://example.com/2017_summary.mdb",
            "2017_summary.mdb",
        )

        def fake_download(url, dest_path):
            with open(dest_path, "wb") as f:
                f.write(b"mdb")

        def fake_export(db_path, year):
            county_csv = os.path.join(self.output_dir,
                                      "2017_county_summary.csv")
            state_csv = os.path.join(self.output_dir, "2017_state_summary.csv")
            with open(county_csv, "w", encoding="utf-8") as f:
                f.write("year,col\n2017,1\n")
            with open(state_csv, "w", encoding="utf-8") as f:
                f.write("year,col\n2017,2\n")

        mock_download.side_effect = fake_download
        mock_export.side_effect = fake_export

        with patch.object(download_preprocess, "OUTPUT_DIR", self.output_dir), \
             patch.object(download_preprocess, "COUNTY_OUTPUT_DIR", self.county_output_dir):
            download_preprocess.main()

        self.assertTrue(
            os.path.exists(
                os.path.join(self.county_output_dir,
                             "2017_county_summary.csv")))
        self.assertFalse(
            os.path.exists(
                os.path.join(self.output_dir, "2017_county_summary.csv")))
        self.assertTrue(
            os.path.exists(
                os.path.join(self.output_dir, "2017_state_summary.csv")))


if __name__ == "__main__":
    unittest.main()
