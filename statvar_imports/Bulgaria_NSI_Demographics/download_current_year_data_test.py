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

from download_current_year_data import (
    EXPECTED_AGES,
    EXPECTED_DISTRICTS,
    check_and_download_nsi,
    list_gcs_files,
    normalize_cell,
    to_num,
    validate_file_format,
)


class DownloadCurrentYearDataTest(unittest.TestCase):

    def test_to_num(self):
        self.assertEqual(to_num("123"), 123)
        self.assertEqual(to_num(" 456 "), 456)
        self.assertEqual(to_num("-"), 0)
        self.assertEqual(to_num("0"), 0)

    def test_normalize_cell(self):
        self.assertEqual(normalize_cell("1-4"), "1 - 4")
        self.assertEqual(normalize_cell("100+"), "100 +")
        self.assertEqual(normalize_cell("AS OF 31.12.*"), "AS OF 31.12.")
        self.assertEqual(normalize_cell(" 1 234.0 ", is_numeric_col=True),
                         "1234")

    def _create_mock_csv(self, year=2025, tamper_type=None):
        rows = [
            [
                ("POPULATION BY DISTRICTS, AGE, PLACE OF RESIDENCE AND SEX"
                 f" AS OF 31.12.{year} (MOCK)"),
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ],
            [
                "Districts Age (years)",
                "Total",
                "",
                "",
                "Urban residence",
                "",
                "",
                "Rural residence",
                "",
                "",
            ],
            [
                "",
                "Total",
                "Male",
                "Female",
                "Total",
                "Male",
                "Female",
                "Total",
                "Male",
                "Female",
            ],
        ]
        n_ages = len(EXPECTED_AGES)
        for d in EXPECTED_DISTRICTS:
            d_tot = 100 * n_ages
            d_m = 60 * n_ages
            d_fem = 40 * n_ages
            d_urb = 70 * n_ages
            d_urb_m = 42 * n_ages
            d_urb_fem = 28 * n_ages
            d_rur = 30 * n_ages
            d_rur_m = 18 * n_ages
            d_rur_fem = 12 * n_ages
            if tamper_type == "district_row_sex" and d == EXPECTED_DISTRICTS[0]:
                d_fem = 100  # breaks d_tot == d_m + d_fem
            elif tamper_type == "vertical_sum" and d == EXPECTED_DISTRICTS[0]:
                # Keep horizontal sums valid on the district row, but break vertical sum
                d_tot = 200 * n_ages
                d_m = 120 * n_ages
                d_fem = 80 * n_ages
                d_urb = 140 * n_ages
                d_urb_m = 84 * n_ages
                d_urb_fem = 56 * n_ages
                d_rur = 60 * n_ages
                d_rur_m = 36 * n_ages
                d_rur_fem = 24 * n_ages

            rows.append([
                d,
                str(d_tot),
                str(d_m),
                str(d_fem),
                str(d_urb),
                str(d_urb_m),
                str(d_urb_fem),
                str(d_rur),
                str(d_rur_m),
                str(d_rur_fem),
            ])
            for a in EXPECTED_AGES:
                tot = 100
                m = 60
                fem = 40
                urb_tot = 70
                urb_m = 42
                urb_fem = 28
                rur_tot = 30
                rur_m = 18
                rur_fem = 12

                if (tamper_type == "arithmetic_residence" and
                        d == EXPECTED_DISTRICTS[0] and a == EXPECTED_AGES[0]):
                    rur_tot = 50  # 70 + 50 != 100
                elif (tamper_type == "arithmetic_sex" and
                      d == EXPECTED_DISTRICTS[0] and a == EXPECTED_AGES[0]):
                    fem = 30  # 60 + 30 != 100
                elif (tamper_type == "arithmetic_urban_sex" and
                      d == EXPECTED_DISTRICTS[0] and a == EXPECTED_AGES[0]):
                    urb_fem = 20  # 42 + 20 != 70
                elif (tamper_type == "arithmetic_rural_sex" and
                      d == EXPECTED_DISTRICTS[0] and a == EXPECTED_AGES[0]):
                    rur_fem = 10  # 18 + 10 != 30

                row = [
                    a,
                    str(tot),
                    str(m),
                    str(fem),
                    str(urb_tot),
                    str(urb_m),
                    str(urb_fem),
                    str(rur_tot),
                    str(rur_m),
                    str(rur_fem),
                ]
                rows.append(row)

        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".csv",
            newline="",
            dir="/tmp",
        )
        writer = csv.writer(temp_file)
        writer.writerows(rows)
        temp_file.close()
        return temp_file.name

    def _build_mock_html(self, year=2025, tight_hyphens=False):
        n_ages = len(EXPECTED_AGES)
        trs = []
        for d in EXPECTED_DISTRICTS:
            d_vals = [
                d,
                100 * n_ages,
                60 * n_ages,
                40 * n_ages,
                70 * n_ages,
                42 * n_ages,
                28 * n_ages,
                30 * n_ages,
                18 * n_ages,
                12 * n_ages,
            ]
            tds = "".join(f"<td>{v}</td>" for v in d_vals)
            trs.append(f"<tr>{tds}</tr>")
            for a in EXPECTED_AGES:
                age_label = a.replace(" - ", "-") if tight_hyphens else a
                a_vals = [age_label, "100.0", 60, 40, 70, 42, 28, 30, 18, 12]
                tds = "".join(f"<td>{v}</td>" for v in a_vals)
                trs.append(f"<tr>{tds}</tr>")
        table_body = "\n".join(trs)
        return (
            f'<div id="ttitle">POPULATION BY DISTRICTS, AGE, PLACE OF RESIDENCE'
            f" AND SEX AS OF 31.12.{year}</div>"
            f'<table class="nsit3">{table_body}</table>')

    def test_validate_file_format_success(self):
        csv_path = self._create_mock_csv(year=2025)
        try:
            self.assertTrue(validate_file_format(csv_path, expected_year=2025))
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_validate_file_format_district_row_failure(self):
        csv_path = self._create_mock_csv(year=2025,
                                         tamper_type="district_row_sex")
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_file_format(csv_path, expected_year=2025)
            self.assertIn(
                "Total (2200) != Male (1320) + Female (100)",
                str(ctx.exception),
            )
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_validate_file_format_arithmetic_residence_failure(self):
        csv_path = self._create_mock_csv(year=2025,
                                         tamper_type="arithmetic_residence")
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_file_format(csv_path, expected_year=2025)
            self.assertIn(
                "Total (100) != Urban (70) + Rural (50)",
                str(ctx.exception),
            )
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_validate_file_format_arithmetic_sex_failure(self):
        csv_path = self._create_mock_csv(year=2025,
                                         tamper_type="arithmetic_sex")
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_file_format(csv_path, expected_year=2025)
            self.assertIn(
                "Total (100) != Male (60) + Female (30)",
                str(ctx.exception),
            )
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_validate_file_format_urban_sex_failure(self):
        csv_path = self._create_mock_csv(year=2025,
                                         tamper_type="arithmetic_urban_sex")
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_file_format(csv_path, expected_year=2025)
            self.assertIn(
                "Urban (70) != Urban Male (42) + Urban Female (20)",
                str(ctx.exception),
            )
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_validate_file_format_rural_sex_failure(self):
        csv_path = self._create_mock_csv(year=2025,
                                         tamper_type="arithmetic_rural_sex")
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_file_format(csv_path, expected_year=2025)
            self.assertIn(
                "Rural (30) != Rural Male (18) + Rural Female (10)",
                str(ctx.exception),
            )
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_validate_file_format_vertical_sum_failure(self):
        csv_path = self._create_mock_csv(year=2025, tamper_type="vertical_sum")
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_file_format(csv_path, expected_year=2025)
            self.assertIn(
                "District 'Total', col 1: District header (4400) != sum of age rows (2200).",
                str(ctx.exception),
            )
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    @mock.patch("download_current_year_data.list_gcs_files", return_value=[])
    @mock.patch("download_current_year_data._create_retry_session")
    def test_check_and_download_nsi_html_parsing_and_dry_run(
        self,
        mock_create_session,
        mock_list_gcs,
    ):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self._build_mock_html(year=2026, tight_hyphens=True)
        mock_session = mock.MagicMock()
        mock_session.get.return_value = mock_resp
        mock_create_session.return_value = mock_session

        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            check_and_download_nsi(
                local_dir=tmp_dir,
                gcs_dir="gs://mock-bucket/input_files",
                force=True,
                dry_run=True,
            )
            expected_csv = os.path.join(
                tmp_dir, "BulgariaNSI_Demographics_Year_input_2026.csv")
            self.assertTrue(os.path.exists(expected_csv))
            self.assertTrue(validate_file_format(expected_csv, 2026))
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
        "download_current_year_data.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "gcloud"),
    )
    def test_list_gcs_files_raises_on_failure(self, mock_run):
        with self.assertRaises(RuntimeError):
            list_gcs_files("gs://mock-bucket/input_files")


if __name__ == "__main__":
    unittest.main()
