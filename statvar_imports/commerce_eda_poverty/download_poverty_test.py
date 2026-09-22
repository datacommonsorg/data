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

import io
import os
import tempfile
import unittest
from unittest import mock
import pandas as pd
import requests

from statvar_imports.commerce_eda_poverty.download_poverty import (
    CDFI_REPORTS_URL,
    DEFAULT_PPC_XLSX_URL,
    download_file,
    download_poverty_dataset,
    export_raw_csv_from_excel,
    fetch_ppc_excel_url,
)


class TestDownloadPoverty(unittest.TestCase):

    def test_fetch_ppc_excel_url_direct(self):
        direct_url = "https://example.gov/custom/PPC_file.xlsx"
        self.assertEqual(fetch_ppc_excel_url(direct_url), direct_url)

    def test_fetch_ppc_excel_url_from_landing_page(self):
        mock_html = (
            '<html><body>'
            '<a href="/system/files?file=2024-05/PPC_2020_ACS_May_10_2024.xlsx">'
            'Persistent Poverty Counties</a>'
            '</body></html>'
        )
        mock_resp = mock.MagicMock()
        mock_resp.text = mock_html
        mock_resp.status_code = 200

        mock_session = mock.MagicMock()
        mock_session.get.return_value = mock_resp

        resolved = fetch_ppc_excel_url(CDFI_REPORTS_URL, session=mock_session)
        expected = "https://www.cdfifund.gov/system/files?file=2024-05/PPC_2020_ACS_May_10_2024.xlsx"
        self.assertEqual(resolved, expected)

    def test_fetch_ppc_excel_url_fallback_on_network_error(self):
        mock_session = mock.MagicMock()
        mock_session.get.side_effect = requests.RequestException("Network down")

        resolved = fetch_ppc_excel_url(CDFI_REPORTS_URL, session=mock_session)
        self.assertEqual(resolved, DEFAULT_PPC_XLSX_URL)

    def test_fetch_ppc_excel_url_fallback_when_no_match(self):
        mock_html = '<html><body><a href="/reports/unrelated.pdf">Report</a></body></html>'
        mock_resp = mock.MagicMock()
        mock_resp.text = mock_html
        mock_resp.status_code = 200

        mock_session = mock.MagicMock()
        mock_session.get.return_value = mock_resp

        resolved = fetch_ppc_excel_url(CDFI_REPORTS_URL, session=mock_session)
        self.assertEqual(resolved, DEFAULT_PPC_XLSX_URL)

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
                "https://example.gov/ppc.xlsx",
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

            mock_fail = mock.MagicMock()
            mock_fail.side_effect = requests.ConnectionError("Temporary failure")

            mock_success = mock.MagicMock()
            mock_success.content = test_content
            mock_success.status_code = 200

            mock_session = mock.MagicMock()
            mock_session.get.side_effect = [requests.ConnectionError("Temporary failure"), mock_success]

            download_file(
                "https://example.gov/ppc.xlsx",
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
                    "https://example.gov/ppc.xlsx",
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
                    "https://example.gov/ppc.xlsx",
                    out_file,
                    session=mock_session,
                    max_retries=1,
                )

    def test_export_raw_csv_from_excel(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "exported.csv")
            # Build an in-memory Excel file
            df_in = pd.DataFrame({
                "County FIPS": ["01005", "60"],
                "County, State": ["Barbour County, Alabama", "American Samoa"],
                "1990 Poverty %": [25.2, 57.8],
                "2000 Poverty %": [26.8, 61.0],
                "2016-2020 Poverty %": [28.6, 54.6],
            })
            bio = io.BytesIO()
            with pd.ExcelWriter(bio, engine="openpyxl") as writer:
                # Add title row in row 0
                title_df = pd.DataFrame([["Persistent Poverty Counties Notice", None, None, None, None]])
                title_df.to_excel(writer, sheet_name="Sheet1", index=False, header=False)
                df_in.to_excel(writer, sheet_name="Sheet1", startrow=1, index=False)

            export_raw_csv_from_excel(bio.getvalue(), csv_path)
            self.assertTrue(os.path.exists(csv_path))
            df_out = pd.read_csv(csv_path, dtype={"County FIPS": str})
            self.assertEqual(len(df_out), 2)
            self.assertIn("County FIPS", df_out.columns)


if __name__ == "__main__":
    unittest.main()
