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
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from urllib import parse

import openpyxl
import pandas as pd

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from statvar_imports.commerce_eda_poverty.download_poverty import (
    EDA_PPC_MIRROR_URL,
    EDA_PPC_XLSX_URL,
    HTTP_HEADERS,
    download_file,
    download_poverty_dataset,
    extract_sheet_to_csv,
)


def _create_mock_eda_workbook(filepath=None):
    """Creates a mock Excel workbook containing the Underlying_Data worksheet."""
    wb = openpyxl.Workbook()
    try:
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
        ws_data.append([
            "Autauga County, AL",
            "01001",
            15.7,
            10.9,
            13.3,
            "SAIPE, 2021",
            "No",
            1,
        ])
        ws_data.append([
            "Barbour County, AL",
            "01005",
            25.2,
            26.8,
            29.0,
            "SAIPE, 2021",
            "Yes",
            2,
        ])
        ws_data.append([
            "Eastern District, AS",
            "60010",
            56.0,
            58.6,
            52.2,
            "Decennial Census, 2020",
            "Yes",
            2,
        ])

        if filepath:
            wb.save(filepath)
            return filepath

        bio = io.BytesIO()
        wb.save(bio)
        return bio.getvalue()
    finally:
        wb.close()


class TestDownloadPoverty(unittest.TestCase):

    def test_download_file_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "test.xlsx")
            test_content = b"PK\x03\x04test_content"

            with mock.patch(
                    "statvar_imports.commerce_eda_poverty.download_poverty"
                    ".request_url",
                    return_value=test_content,
            ) as mock_request_url:
                content = download_file(
                    "https://example.gov/EDA_FY23_PPCs.xlsx",
                    out_file,
                    max_retries=1,
                )

            self.assertEqual(content, test_content)
            mock_request_url.assert_called_once_with(
                url="https://example.gov/EDA_FY23_PPCs.xlsx",
                headers=HTTP_HEADERS,
                output="bytes",
                timeout=60,
                retries=1,
            )
            self.assertTrue(os.path.exists(out_file))
            with open(out_file, "rb") as f:
                self.assertEqual(f.read(), test_content)

    def test_download_file_passes_headers_and_timeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "params.xlsx")
            test_content = b"PK\x03\x04param_test"

            with mock.patch(
                    "statvar_imports.commerce_eda_poverty.download_poverty"
                    ".request_url",
                    return_value=test_content,
            ) as mock_request_url:
                content = download_file(
                    "https://example.gov/EDA_FY23_PPCs.xlsx",
                    out_file,
                    max_retries=5,
                    timeout=45,
                    require_zip_signature=True,
                )

            self.assertEqual(content, test_content)
            mock_request_url.assert_called_once_with(
                url="https://example.gov/EDA_FY23_PPCs.xlsx",
                headers=HTTP_HEADERS,
                output="bytes",
                timeout=45,
                retries=5,
            )

    def test_download_file_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "fail.xlsx")

            with mock.patch(
                    "statvar_imports.commerce_eda_poverty.download_poverty"
                    ".request_url",
                    return_value=None,
            ) as mock_request_url:
                with self.assertRaises(RuntimeError):
                    download_file(
                        "https://example.gov/EDA_FY23_PPCs.xlsx",
                        out_file,
                        max_retries=2,
                    )

            mock_request_url.assert_called_once()
            self.assertFalse(os.path.exists(out_file))

    def test_download_file_empty_body_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "empty.xlsx")

            with mock.patch(
                    "statvar_imports.commerce_eda_poverty.download_poverty"
                    ".request_url",
                    return_value=b"",
            ) as mock_request_url:
                with self.assertRaises(RuntimeError):
                    download_file(
                        "https://example.gov/EDA_FY23_PPCs.xlsx",
                        out_file,
                        max_retries=1,
                    )

            mock_request_url.assert_called_once()
            self.assertFalse(os.path.exists(out_file))

    def test_download_file_session_without_mount_supported(self):

        class DuckSession:

            def __init__(self):
                self.call_count = 0

            def get(self, url, headers=None, timeout=None, **kwargs):
                self.call_count += 1
                resp = mock.MagicMock()
                resp.__enter__.return_value = resp
                resp.status_code = 200
                resp.content = b"duck_data"
                return resp

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "duck.xlsx")
            duck_session = DuckSession()
            content = download_file(
                "https://example.gov/duck.xlsx",
                out_file,
                session=duck_session,
            )

            self.assertEqual(content, b"duck_data")
            self.assertEqual(duck_session.call_count, 1)
            self.assertTrue(os.path.exists(out_file))
            with open(out_file, "rb") as f:
                self.assertEqual(f.read(), b"duck_data")

    def test_extract_sheet_to_csv_from_bytes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "extracted.csv")
            excel_bytes = _create_mock_eda_workbook()

            extract_sheet_to_csv(excel_bytes,
                                 csv_path,
                                 target_sheet_name="Underlying_Data")
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

            def mock_request(url, **kwargs):
                if parse.urlparse(url).netloc == "www.eda.gov":
                    raise RuntimeError("HTTP 403")
                return excel_bytes

            with mock.patch(
                    "statvar_imports.commerce_eda_poverty.download_poverty"
                    ".request_url",
                    side_effect=mock_request,
            ):
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

    def test_download_poverty_dataset_all_urls_fail_raises_and_cleans_stale_files(
        self,):
        with tempfile.TemporaryDirectory() as tmpdir:
            dst_xlsx = os.path.join(tmpdir, "EDA_FY23_PPCs.xlsx")
            dst_csv = os.path.join(tmpdir, "Poverty.csv")
            dst_raw_csv = os.path.join(tmpdir, "Poverty_original.csv")
            for p in [dst_xlsx, dst_csv, dst_raw_csv]:
                with open(p, "w", encoding="utf-8") as f:
                    f.write("stale_data")

            with mock.patch(
                    "statvar_imports.commerce_eda_poverty.download_poverty"
                    ".request_url",
                    side_effect=RuntimeError("HTTP 503"),
            ):
                with self.assertRaises(RuntimeError) as ctx:
                    download_poverty_dataset(
                        source_url="https://example.gov/p1.xlsx",
                        mirror_url="https://example.gov/m1.xlsx",
                        output_xlsx_path=dst_xlsx,
                        output_csv_path=dst_csv,
                        raw_csv_path=dst_raw_csv,
                        max_retries=1,
                    )

            self.assertIn("Failed to acquire dataset from all URLs",
                          str(ctx.exception))
            self.assertFalse(os.path.exists(dst_xlsx))
            self.assertFalse(os.path.exists(dst_csv))
            self.assertFalse(os.path.exists(dst_raw_csv))

    def test_download_poverty_dataset_primary_html_challenge_mirror_succeed(
        self,):
        with tempfile.TemporaryDirectory() as tmpdir:
            dst_xlsx = os.path.join(tmpdir, "EDA_FY23_PPCs.xlsx")
            dst_csv = os.path.join(tmpdir, "Poverty.csv")
            raw_csv = os.path.join(tmpdir, "Poverty_original.csv")

            excel_bytes = _create_mock_eda_workbook()

            def mock_request(url, **kwargs):
                if parse.urlparse(url).netloc == "www.eda.gov":
                    return (b"<!DOCTYPE html><html><title>Just a moment..."
                            b"</title></html>")
                return excel_bytes

            with mock.patch(
                    "statvar_imports.commerce_eda_poverty.download_poverty"
                    ".request_url",
                    side_effect=mock_request,
            ):
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


class TestPovertyPvMapProcessor(unittest.TestCase):
    """Tests for direct raw CSV processing via poverty_pvmap.csv and stat_var_processor.py."""

    def setUp(self):
        self.processor_script = os.path.join(PROJECT_ROOT, "tools",
                                             "statvar_importer",
                                             "stat_var_processor.py")
        self.pv_map = os.path.join(MODULE_DIR, "poverty_pvmap.csv")
        self.config_file = os.path.join(MODULE_DIR, "poverty_metadata.csv")
        self.golden_input = os.path.join(MODULE_DIR, "test_data",
                                         "Poverty_input.csv")
        self.golden_expected = os.path.join(MODULE_DIR, "test_data",
                                            "Poverty_expected_output.csv")
        self.statvar_mcf_content = (
            "Node: dcid:Count_Person_BelowPovertyLevelInThePast12Months_AsFractionOf_Count_Person\n"
            "typeOf: dcs:StatisticalVariable\n"
            "populationType: dcs:Person\n"
            "measuredProperty: dcs:count\n"
            "statType: dcs:measuredValue\n"
            "measurementDenominator: dcs:Count_Person\n"
            "povertyStatus: dcs:BelowPovertyLevelInThePast12Months\n")

    def _run_stat_var_processor(self, input_csv, tmpdir):
        mcf_path = os.path.join(tmpdir, "stat_vars.mcf")
        with open(mcf_path, "w", encoding="utf-8") as f:
            f.write(self.statvar_mcf_content)
        output_prefix = os.path.join(tmpdir, "Poverty_output")
        counters_path = os.path.join(tmpdir, "Poverty_counters.csv")
        subprocess.run(
            [
                sys.executable,
                self.processor_script,
                f"--input_data={input_csv}",
                f"--pv_map={self.pv_map}",
                f"--config_file={self.config_file}",
                f"--existing_statvar_mcf={mcf_path}",
                f"--output_path={output_prefix}",
                f"--output_counters={counters_path}",
            ],
            cwd=tmpdir,
            check=True,
            capture_output=True,
            text=True,
        )
        return output_prefix + ".csv", counters_path

    def test_pvmap_end_to_end_golden_fixture(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_csv, _ = self._run_stat_var_processor(self.golden_input, tmpdir)
            actual_df = pd.read_csv(out_csv, dtype=str)
            expected_df = pd.read_csv(self.golden_expected, dtype=str)
            pd.testing.assert_frame_equal(actual_df, expected_df)

    def test_pvmap_geoid_padding_state_filtering_and_dynamic_years(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_csv = os.path.join(tmpdir, "synthetic_raw.csv")
            with open(raw_csv, "w", encoding="utf-8") as f:
                f.write(
                    "Table. FY2023 Persistent Poverty County Status - as of Data Year 2021,,,,,,,,,\n"
                    "Identifing Information,,Census Bureau Data,,,,FY23 Persistent Poverty,Census GEO PPC Code,Notes,\n"
                    'Name,GEOID,"1990 Decennial Census, % in Poverty","2000 Decennial Census, % in Poverty","Most Recent Estimate, % in Poverty* ",Data Source―Most Recent Estimate,,,,\n'
                    '"Alabama State",01000,18.3,16.1,16.3,"SAIPE, 2021",No,1,,\n'
                    '"Autauga County, AL",1001,15.7,10.9,13.3,"SAIPE, 2023",No,1,,\n'
                    '"Adjuntas Municipio, PR",72001,59.9,50.5,63.4,"ACS 5-YEAR, 2017-2021",Yes,2,,\n'
                    '"Eastern District, AS",60010,56.0,105.0,52.2,"Decennial Census, 2020",Yes,2,,\n'
                )

            out_csv, _ = self._run_stat_var_processor(raw_csv, tmpdir)
            df = pd.read_csv(out_csv, dtype=str)

            # 01000 state summary row filtered out; 105.0 out-of-range value filtered out
            self.assertNotIn("geoId/01000", set(df["observationAbout"]))
            self.assertEqual(
                set(df["observationAbout"]),
                {"geoId/01001", "geoId/72001", "geoId/60010"},
            )

            # Verify 4-digit GEOID 1001 padded to geoId/01001 and dynamic year 2023
            autauga_recent = df[(df["observationAbout"] == "geoId/01001") &
                                (df["observationDate"] == "2023")]
            self.assertEqual(len(autauga_recent), 1)
            self.assertEqual(autauga_recent.iloc[0]["measurementMethod"],
                             "dcs:EDA_Estimate")

            # Verify PR ACS 5-YEAR 2017-2021 resolves to end year 2021 with dcs:EDA_Estimate
            pr_recent = df[(df["observationAbout"] == "geoId/72001") &
                           (df["observationDate"] == "2021")]
            self.assertEqual(len(pr_recent), 1)
            self.assertEqual(pr_recent.iloc[0]["measurementMethod"],
                             "dcs:EDA_Estimate")

            # Verify Island Area Decennial Census 2020 resolves to 2020 with dcs:USDecennialCensus,
            # and out-of-range 2000 value (105.0) was dropped
            as_rows = df[df["observationAbout"] == "geoId/60010"]
            self.assertEqual(set(as_rows["observationDate"]), {"1990", "2020"})
            as_recent = as_rows[as_rows["observationDate"] == "2020"]
            self.assertEqual(as_recent.iloc[0]["measurementMethod"],
                             "dcs:USDecennialCensus")


if __name__ == "__main__":
    unittest.main()
