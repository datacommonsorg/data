# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for download_current_year_data.py."""

import csv
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

# Ensure the parent directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from download_current_year_data import _validate_horizontal_and_vertical_sums
from download_current_year_data import check_and_download_nsi
from download_current_year_data import list_gcs_files
from download_current_year_data import normalize_cell
from download_current_year_data import sanitize_csv_content
from download_current_year_data import sanitize_directory_files
import requests


class DownloadCurrentYearDataTest(unittest.TestCase):

    def test_normalize_cell(self):
        self.assertEqual(normalize_cell("1-4"), "1 - 4")
        self.assertEqual(normalize_cell("100+"), "100 +")
        self.assertEqual(normalize_cell("AS OF 31.12.*"), "AS OF 31.12.")
        self.assertEqual(normalize_cell(" 1 234.0 ", is_numeric_col=True),
                         "1234")
        self.assertEqual(normalize_cell("-", is_numeric_col=True), "-")

    def test_sanitize_csv_content(self):
        raw = ("POPULATION AS OF 31.12.**2025,col1\n"
               "Districts Age (years),Total\n"
               ",Total\n"
               "Total, 6 423 207.0 \n"
               "100+, - \n")
        rows = sanitize_csv_content(raw)
        self.assertEqual(rows[0][0], "POPULATION AS OF 31.12.2025")
        self.assertEqual(rows[3], ["Total", "6423207"])
        self.assertEqual(rows[4], ["100 +", "-"])

    def test_sanitize_directory_files(self):
        in_dir = tempfile.mkdtemp(dir="/tmp")
        out_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            in_csv = os.path.join(
                in_dir, "BulgariaNSI_Demographics_Year_input_2025.csv")
            with open(in_csv, "w", encoding="utf-8") as f:
                f.write("POPULATION AS OF 31.12.*2025,col1\n"
                        "Districts Age (years),Total\n"
                        ",Total\n"
                        "Total, 6 423 207.0 \n")
            sanitize_directory_files(in_dir, out_dir)
            out_csv = os.path.join(
                out_dir, "BulgariaNSI_Demographics_Year_input_2025.csv")
            self.assertTrue(os.path.exists(out_csv))
            with open(out_csv, "r", encoding="utf-8") as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[0][0], "POPULATION AS OF 31.12.2025")
            self.assertEqual(rows[3], ["Total", "6423207"])
        finally:
            shutil.rmtree(in_dir, ignore_errors=True)
            shutil.rmtree(out_dir, ignore_errors=True)

    def _build_mock_html(self, year=2025, total_val=6423207):
        return (
            f'<div id="ttitle">POPULATION BY DISTRICTS, AGE, PLACE OF RESIDENCE'
            f" AND SEX AS OF 31.12.{year}</div>"
            '<table class="nsit3">'
            f"<tr><td>Total</td><td>{total_val}</td><td>3088245</td>"
            "<td>3334962</td><td>4745686</td><td>2258418</td><td>2487268</td>"
            "<td>1677521</td><td>829827</td><td>847694</td></tr>"
            "<tr><td>1-4</td><td>228158.0</td><td>116800</td>"
            "<td>111358</td><td>171543</td><td>87739</td><td>83804</td>"
            "<td>56615</td><td>29061</td><td>27554</td></tr>"
            "<tr><td>100+</td><td>501</td><td>133</td>"
            "<td>368</td><td>374</td><td>100</td><td>274</td>"
            "<td>127</td><td>-</td><td>94</td></tr>"
            "</table>")

    @mock.patch("download_current_year_data._create_retry_session")
    def test_check_and_download_nsi_saves_html_and_prefers_live_source(
        self,
        mock_create_session,
    ):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._build_mock_html(year=2026, total_val=6423207)
        mock_session = mock.MagicMock()
        mock_session.get.return_value = mock_resp
        mock_create_session.return_value = mock_session

        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            # Pre-populate a stale local CSV to verify live source overwrites it
            expected_csv = os.path.join(
                tmp_dir, "BulgariaNSI_Demographics_Year_input_2026.csv")
            with open(expected_csv, "w", encoding="utf-8") as f:
                f.write("stale_content\n")

            check_and_download_nsi(
                local_dir=tmp_dir,
                gcs_dir="gs://mock-bucket/input_files",
                dry_run=True,
            )
            expected_html = os.path.join(
                tmp_dir, "BulgariaNSI_Demographics_Year_input_2026.html")
            self.assertTrue(os.path.exists(expected_html))
            self.assertTrue(os.path.exists(expected_csv))

            with open(expected_csv, "r", encoding="utf-8") as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[3][0], "Total")
            self.assertEqual(rows[3][1], "6423207")
            self.assertEqual(rows[4][0], "1 - 4")
            self.assertEqual(rows[4][1], "228158")
            # Verify '-' is preserved untouched for stat_var_processor
            self.assertEqual(rows[5][0], "100 +")
            self.assertEqual(rows[5][8], "-")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @mock.patch("download_current_year_data._create_retry_session")
    def test_check_and_download_nsi_http_403_fail_closed(
        self,
        mock_create_session,
    ):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 403
        mock_session = mock.MagicMock()
        mock_session.get.return_value = mock_resp
        mock_create_session.return_value = mock_session

        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            with self.assertRaises(SystemExit) as ctx:
                check_and_download_nsi(
                    local_dir=tmp_dir,
                    gcs_dir="gs://mock-bucket/input_files",
                    allow_staged_fallback=False,
                )
            self.assertEqual(ctx.exception.code, 1)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @mock.patch("download_current_year_data._create_retry_session")
    def test_check_and_download_nsi_http_404_fails_even_with_fallback(
        self,
        mock_create_session,
    ):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 404
        mock_session = mock.MagicMock()
        mock_session.get.return_value = mock_resp
        mock_create_session.return_value = mock_session

        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            with self.assertRaises(SystemExit) as ctx:
                check_and_download_nsi(
                    local_dir=tmp_dir,
                    gcs_dir="gs://mock-bucket/input_files",
                    allow_staged_fallback=True,
                )
            self.assertEqual(ctx.exception.code, 1)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @mock.patch(
        "download_current_year_data.list_gcs_files",
        return_value=["BulgariaNSI_Demographics_Year_input_2025.csv"],
    )
    @mock.patch("download_current_year_data._create_retry_session")
    def test_check_and_download_nsi_http_403_staged_fallback(
        self,
        mock_create_session,
        mock_list_gcs,
    ):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 403
        mock_session = mock.MagicMock()
        mock_session.get.return_value = mock_resp
        mock_create_session.return_value = mock_session

        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            check_and_download_nsi(
                local_dir=tmp_dir,
                gcs_dir="gs://mock-bucket/input_files",
                allow_staged_fallback=True,
            )
            mock_list_gcs.assert_called_once_with(
                "gs://mock-bucket/input_files")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @mock.patch(
        "download_current_year_data.list_gcs_files",
        return_value=["BulgariaNSI_Demographics_2001to2010_input.csv"],
    )
    @mock.patch("download_current_year_data._create_retry_session")
    def test_check_and_download_nsi_http_403_fails_without_annual_files(
        self,
        mock_create_session,
        mock_list_gcs,
    ):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 403
        mock_session = mock.MagicMock()
        mock_session.get.return_value = mock_resp
        mock_create_session.return_value = mock_session

        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            with self.assertRaises(SystemExit) as ctx:
                check_and_download_nsi(
                    local_dir=tmp_dir,
                    gcs_dir="gs://mock-bucket/input_files",
                    allow_staged_fallback=True,
                )
            self.assertEqual(ctx.exception.code, 1)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @mock.patch(
        "download_current_year_data.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "gcloud"),
    )
    def test_list_gcs_files_raises_on_failure(self, mock_run):
        with self.assertRaises(RuntimeError):
            list_gcs_files("gs://mock-bucket/input_files")

    @mock.patch("download_current_year_data._create_retry_session")
    def test_check_and_download_nsi_missing_ttitle_fails(
        self,
        mock_create_session,
    ):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html><body>Updated 31.12.2025</body></html>"
        mock_session = mock.MagicMock()
        mock_session.get.return_value = mock_resp
        mock_create_session.return_value = mock_session

        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            with self.assertRaises(SystemExit) as ctx:
                check_and_download_nsi(
                    local_dir=tmp_dir,
                    gcs_dir="gs://mock-bucket/input_files",
                )
            self.assertEqual(ctx.exception.code, 1)
            # Verify raw HTML was still saved for debugging before failing
            self.assertTrue(
                os.path.exists(
                    os.path.join(tmp_dir, "nsi_demographics_page.html")))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _create_test_csv(self, rows):
        tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv")
        writer = csv.writer(tmp)
        writer.writerow(["Title", "", "", "", "", "", "", "", "", ""])
        writer.writerow(["Sub", "", "", "", "", "", "", "", "", ""])
        writer.writerow([
            "Header", "Total", "Male", "Female", "Urban Total", "Urban Male",
            "Urban Female", "Rural Total", "Rural Male", "Rural Female"
        ])
        for r in rows:
            writer.writerow(r)
        tmp.close()
        return tmp.name

    def test_validate_horizontal_and_vertical_sums_success(self):
        rows = [
            ["Total", "100", "50", "50", "60", "30", "30", "40", "20", "20"],
            ["0", "40", "20", "20", "24", "12", "12", "16", "8", "8"],
            ["1 - 4", "60", "30", "30", "36", "18", "18", "24", "12", "12"],
        ]
        csv_path = self._create_test_csv(rows)
        try:
            self.assertTrue(_validate_horizontal_and_vertical_sums(csv_path))
        finally:
            os.remove(csv_path)

    def test_validate_horizontal_and_vertical_sums_horizontal_failure(self):
        rows = [
            ["Total", "100", "60", "30", "60", "30", "30", "40", "20", "20"],
        ]
        csv_path = self._create_test_csv(rows)
        try:
            with self.assertRaises(ValueError) as ctx:
                _validate_horizontal_and_vertical_sums(csv_path)
            self.assertIn("Total (100) != Male (60) + Female (30)",
                          str(ctx.exception))
        finally:
            os.remove(csv_path)

    def test_validate_horizontal_and_vertical_sums_vertical_failure(self):
        rows = [
            ["Total", "100", "50", "50", "60", "30", "30", "40", "20", "20"],
            ["0", "40", "20", "20", "24", "12", "12", "16", "8", "8"],
            ["1 - 4", "50", "25", "25", "30", "15", "15", "20", "10", "10"],
        ]
        csv_path = self._create_test_csv(rows)
        try:
            with self.assertRaises(ValueError) as ctx:
                _validate_horizontal_and_vertical_sums(csv_path)
            self.assertIn("District header (100) != sum of 2 age cohorts (90)",
                          str(ctx.exception))
        finally:
            os.remove(csv_path)

    def test_validate_horizontal_and_vertical_sums_with_dash_allowed(self):
        rows = [
            ["Total", "100", "50", "50", "60", "30", "30", "40", "20", "20"],
            ["0", "100", "50", "50", "60", "30", "30", "40", "-", "20"],
        ]
        csv_path = self._create_test_csv(rows)
        try:
            self.assertTrue(_validate_horizontal_and_vertical_sums(csv_path))
        finally:
            os.remove(csv_path)

    @mock.patch("download_current_year_data.list_gcs_files",
                return_value=["BulgariaNSI_Demographics_Year_input_2025.csv"])
    @mock.patch("download_current_year_data._create_retry_session")
    def test_check_and_download_nsi_network_exception_fallback(
            self, mock_create_session, mock_list_gcs):
        mock_session = mock.MagicMock()
        mock_session.get.side_effect = requests.RequestException(
            "Connection timeout")
        mock_create_session.return_value = mock_session

        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            check_and_download_nsi(
                local_dir=tmp_dir,
                gcs_dir="gs://mock-bucket/input_files",
                allow_staged_fallback=True,
            )
            mock_list_gcs.assert_called_once_with(
                "gs://mock-bucket/input_files")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @mock.patch("download_current_year_data._create_retry_session")
    def test_check_and_download_nsi_network_exception_fails_without_fallback(
            self, mock_create_session):
        mock_session = mock.MagicMock()
        mock_session.get.side_effect = requests.RequestException(
            "Connection timeout")
        mock_create_session.return_value = mock_session

        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            with self.assertRaises(SystemExit) as ctx:
                check_and_download_nsi(
                    local_dir=tmp_dir,
                    gcs_dir="gs://mock-bucket/input_files",
                    allow_staged_fallback=False,
                )
            self.assertEqual(ctx.exception.code, 1)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @mock.patch("download_current_year_data.list_gcs_files",
                return_value=["BulgariaNSI_Demographics_Year_input_2025.csv"])
    @mock.patch("download_current_year_data._create_retry_session")
    def test_check_and_download_nsi_http_503_fallback(self, mock_create_session,
                                                      mock_list_gcs):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 503
        mock_session = mock.MagicMock()
        mock_session.get.return_value = mock_resp
        mock_create_session.return_value = mock_session

        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            check_and_download_nsi(
                local_dir=tmp_dir,
                gcs_dir="gs://mock-bucket/input_files",
                allow_staged_fallback=True,
            )
            mock_list_gcs.assert_called_once_with(
                "gs://mock-bucket/input_files")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @mock.patch("download_current_year_data._create_retry_session")
    def test_check_and_download_nsi_http_503_fails_without_fallback(
            self, mock_create_session):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 503
        mock_session = mock.MagicMock()
        mock_session.get.return_value = mock_resp
        mock_create_session.return_value = mock_session

        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            with self.assertRaises(SystemExit) as ctx:
                check_and_download_nsi(
                    local_dir=tmp_dir,
                    gcs_dir="gs://mock-bucket/input_files",
                    allow_staged_fallback=False,
                )
            self.assertEqual(ctx.exception.code, 1)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
