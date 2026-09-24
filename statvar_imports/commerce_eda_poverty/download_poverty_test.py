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

"""Unit tests for Commerce EDA Persistent Poverty Counties download script."""

import csv
import io
import os
import tempfile
import unittest
from unittest import mock
from urllib import parse

import openpyxl
import pandas as pd
import requests

from statvar_imports.commerce_eda_poverty.download_poverty import (
    EDA_PPC_MIRROR_URL,
    EDA_PPC_XLSX_URL,
    copy_file_atomically,
    download_file,
    download_poverty_dataset,
    extract_sheet_to_csv,
)


def _create_mock_eda_workbook(filepath=None):
    """Creates a mock Excel workbook containing the Underlying_Data worksheet."""
    wb = openpyxl.Workbook()
    # Sheet 1: Readme
    ws_readme = wb.active
    ws_readme.title = "EDA Read Me"
    ws_readme.append(["FY2023 PERSISTENT POVERTY COUNTIES (PPCs)", ""])

    # Sheet 2: Underlying_Data
    ws_data = wb.create_sheet(title="Underlying_Data")
    ws_data.append([
        "Table. FY2023 Persistent Poverty County Status - as of Data Year 2021",
        "", "", "", "", "", "", ""
    ])
    ws_data.append([
        "Identifing Information", "", "Census Bureau Data", "", "", "",
        "FY23 Persistent Poverty", "Census GEO PPC Code"
    ])
    ws_data.append([
        "Name",
        "GEOID",
        "1990 Decennial Census, % in Poverty",
        "2000 Decennial Census, % in Poverty",
        "Most Recent Estimate, % in Poverty* ",
        "Data Source―Most Recent Estimate",
        "",
        "",
    ])
    ws_data.append(["Autauga County, AL", "01001", 15.7, 10.9, 13.3, "SAIPE, 2021", "No", 1])
    ws_data.append(["Barbour County, AL", "01005", 25.2, 26.8, 29.0, "SAIPE, 2021", "Yes", 2])
    ws_data.append([
        "Eastern District, AS", "60010", 56.0, 58.6, 52.2, "Decennial Census, 2020", "Yes", 2
    ])

    if filepath:
        wb.save(filepath)
        return filepath

    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


class TestDownloadPoverty(unittest.TestCase):

    def test_download_file_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "test.xlsx")
            test_content = b"PK\x03\x04test_content"

            mock_resp = mock.MagicMock()
            mock_resp.content = test_content
            mock_resp.status_code = 200

            mock_session = mock.MagicMock()
            mock_session.get.return_value = mock_resp

            download_file(
                "https://example.gov/EDA_FY23_PPCs.xlsx",
                out_file,
                session=mock_session,
                max_retries=1,
            )

            self.assertTrue(os.path.exists(out_file))
            with open(out_file, "rb") as f:
                self.assertEqual(f.read(), test_content)

    def test_download_file_retry_and_succeed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "retry.xlsx")
            test_content = b"PK\x03\x04retry_content"

            mock_success = mock.MagicMock()
            mock_success.content = test_content
            mock_success.status_code = 200

            mock_session = mock.MagicMock()
            mock_session.get.side_effect = [
                requests.ConnectionError("Temporary network glitch"),
                mock_success,
            ]

            download_file(
                "https://example.gov/EDA_FY23_PPCs.xlsx",
                out_file,
                session=mock_session,
                max_retries=3,
                backoff_factor=0.01,
            )

            self.assertTrue(os.path.exists(out_file))
            self.assertEqual(mock_session.get.call_count, 2)

    def test_download_file_fails_after_retries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "fail.xlsx")

            mock_session = mock.MagicMock()
            mock_session.get.side_effect = requests.ConnectionError("Persistent error")

            with self.assertRaises(RuntimeError):
                download_file(
                    "https://example.gov/EDA_FY23_PPCs.xlsx",
                    out_file,
                    session=mock_session,
                    max_retries=2,
                    backoff_factor=0.01,
                )

    def test_download_file_empty_body_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "empty.xlsx")

            mock_resp = mock.MagicMock()
            mock_resp.content = b""
            mock_resp.status_code = 200

            mock_session = mock.MagicMock()
            mock_session.get.return_value = mock_resp

            with self.assertRaises(RuntimeError):
                download_file(
                    "https://example.gov/EDA_FY23_PPCs.xlsx",
                    out_file,
                    session=mock_session,
                    max_retries=1,
                )

    def test_extract_sheet_to_csv_from_bytes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "extracted.csv")
            excel_bytes = _create_mock_eda_workbook()

            extract_sheet_to_csv(excel_bytes, csv_path, target_sheet_name="Underlying_Data")
            self.assertTrue(os.path.exists(csv_path))

            df = pd.read_csv(csv_path, skiprows=2, dtype=str)
            self.assertEqual(len(df), 3)
            self.assertIn("GEOID", df.columns)
            self.assertEqual(list(df["GEOID"]), ["01001", "01005", "60010"])

    def test_extract_sheet_to_csv_from_file_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            xlsx_path = os.path.join(tmpdir, "EDA_FY23_PPCs.xlsx")
            csv_path = os.path.join(tmpdir, "Poverty.csv")
            _create_mock_eda_workbook(xlsx_path)

            extract_sheet_to_csv(xlsx_path, csv_path)
            self.assertTrue(os.path.exists(csv_path))

            df = pd.read_csv(csv_path, skiprows=2, dtype=str)
            self.assertEqual(len(df), 3)
            self.assertIn("GEOID", df.columns)

    def test_download_poverty_dataset_with_input_file_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src_csv = os.path.join(tmpdir, "source_input.csv")
            dst_xlsx = os.path.join(tmpdir, "out.xlsx")
            dst_csv = os.path.join(tmpdir, "out.csv")
            raw_csv = os.path.join(tmpdir, "raw.csv")

            with open(src_csv, "w", encoding="utf-8") as f:
                f.write("Line 1\nLine 2\nName,GEOID\nCounty A,01001\n")

            res = download_poverty_dataset(
                input_file=src_csv,
                output_xlsx_path=dst_xlsx,
                output_csv_path=dst_csv,
                raw_csv_path=raw_csv,
            )

            self.assertEqual(res, dst_csv)
            self.assertTrue(os.path.exists(dst_csv))
            self.assertTrue(os.path.exists(raw_csv))
            with open(dst_csv, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("County A,01001", content)

    def test_download_poverty_dataset_with_input_file_xlsx(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src_xlsx = os.path.join(tmpdir, "source_input.xlsx")
            dst_xlsx = os.path.join(tmpdir, "EDA_FY23_PPCs.xlsx")
            dst_csv = os.path.join(tmpdir, "Poverty.csv")
            raw_csv = os.path.join(tmpdir, "Poverty_original.csv")

            _create_mock_eda_workbook(src_xlsx)

            res = download_poverty_dataset(
                input_file=src_xlsx,
                output_xlsx_path=dst_xlsx,
                output_csv_path=dst_csv,
                raw_csv_path=raw_csv,
            )

            self.assertEqual(res, dst_csv)
            self.assertTrue(os.path.exists(dst_xlsx))
            self.assertTrue(os.path.exists(dst_csv))
            self.assertTrue(os.path.exists(raw_csv))

            df = pd.read_csv(dst_csv, skiprows=2, dtype=str)
            self.assertEqual(len(df), 3)

    def test_download_poverty_dataset_primary_fail_mirror_succeed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dst_xlsx = os.path.join(tmpdir, "EDA_FY23_PPCs.xlsx")
            dst_csv = os.path.join(tmpdir, "Poverty.csv")
            raw_csv = os.path.join(tmpdir, "Poverty_original.csv")

            excel_bytes = _create_mock_eda_workbook()

            def mock_get(url, **kwargs):
                resp = mock.MagicMock()
                if parse.urlparse(url).netloc == "www.eda.gov":
                    resp.status_code = 403
                    resp.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
                    return resp
                resp.status_code = 200
                resp.content = excel_bytes
                return resp

            with mock.patch("requests.Session.get", side_effect=mock_get):
                res = download_poverty_dataset(
                    source_url=EDA_PPC_XLSX_URL,
                    mirror_url=EDA_PPC_MIRROR_URL,
                    output_xlsx_path=dst_xlsx,
                    output_csv_path=dst_csv,
                    raw_csv_path=raw_csv,
                    max_retries=1,
                )

            self.assertEqual(res, dst_csv)
            self.assertTrue(os.path.exists(dst_xlsx))
            self.assertTrue(os.path.exists(dst_csv))
            df = pd.read_csv(dst_csv, skiprows=2, dtype=str)
            self.assertEqual(len(df), 3)

    def test_download_poverty_dataset_missing_input_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            download_poverty_dataset(input_file="/nonexistent/path/Poverty.csv")


if __name__ == "__main__":
    unittest.main()
