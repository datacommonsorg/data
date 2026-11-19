# Copyright 2026 Google LLC
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
"""Unit tests for Dartmouth Atlas Medicare download and preprocessing."""

import csv
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

import requests

from statvar_imports.dartmouth_atlas_medicare import download


def _build_zip_bytes(entries: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()


class DownloadTest(unittest.TestCase):
    """Tests normalization, filtering, and error handling in download.py."""

    def test_format_place_dcid(self):
        self.assertEqual(download.format_place_dcid("1001", False),
                         "geoId/01001")
        self.assertEqual(download.format_place_dcid("55091", False),
                         "geoId/55091")
        self.assertEqual(download.format_place_dcid("1", True), "geoId/01")
        self.assertEqual(download.format_place_dcid("99", True), "country/USA")
        self.assertEqual(download.format_place_dcid("99", False), "country/USA")
        self.assertIsNone(download.format_place_dcid("", False))
        self.assertIsNone(download.format_place_dcid("abc", False))
        self.assertIsNone(download.format_place_dcid("0", True))
        self.assertIsNone(download.format_place_dcid("-1", True))
        self.assertIsNone(download.format_place_dcid("100", True))
        self.assertIsNone(download.format_place_dcid("1", False))
        self.assertIsNone(download.format_place_dcid("999", False))
        self.assertIsNone(download.format_place_dcid("100000", False))
        self.assertIsNone(download.format_place_dcid("4617620", False))

    def test_clean_numeric_value(self):
        self.assertEqual(download.clean_numeric_value(" 7,128 "), "7128")
        self.assertEqual(download.clean_numeric_value("$9,903.76"), "9903.76")
        self.assertEqual(download.clean_numeric_value("218.80"), "218.8")
        for bad in ("", ".", "-", "NaN", "nan", "suppressed", "*", "-5"):
            self.assertIsNone(download.clean_numeric_value(bad))

    def test_process_stdprices_bom_and_macosx_skip(self):
        csv_text = (
            "\ufeffGeo_code,Geo_label,Population,Year,Cohort,Eventname,"
            "Adjusted_Rate\n"
            '1001,COUNTY,"4,675",2019,StdPrice,stdprice_total,"11,377.40"\n'
            "1001,COUNTY,4675,2019,Payment,pmt_dme,218.83\n"
            "4617620,COUNTY,NaN,2019,StdPrice,stdprice_total,suppressed\n")
        zip_bytes = _build_zip_bytes({
            "__MACOSX/._county_stdprices_ffs.csv": b"\x00\x05\x16",
            "county_stdprices_ffs.csv": csv_text.encode("utf-8"),
        })
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = Path(tmpdir) / "county_stdprices_ffs.csv.zip"
            archive.write_bytes(zip_bytes)
            obs: dict[tuple[str, str, str], str] = {}
            download.process_archive(archive,
                                     kind="stdprices",
                                     is_state=False,
                                     observations=obs)
        self.assertEqual(
            obs,
            {
                ("2019", "geoId/01001", "MedicareEnrollee_Count"):
                    "4675",
                ("2019", "geoId/01001", "MedicareEnrollee_MeanPrice"):
                    "11377.4",
            },
        )

    def test_process_hedis_part_b_and_diabetic(self):
        csv_text = (
            "Geo_code,Geo_Label,Population,Year,Race,Cohort,Eventname\n"
            "6083,COUNTY,3162,2019,Overall,Ambulatory care,ptbjune_amcare2\n"
            "6083,COUNTY,120,2019,Black,Ambulatory care,ptbjune_amcare2\n"
            "6083,COUNTY,3042,2019,Non-Black,Ambulatory care,ptbjune_amcare2\n"
            "6083,COUNTY,450,2019,Black,Diabetic Events,diab_hgb\n"
            "6083,COUNTY,2700,2019,Non-Black,Diabetic Events,diab_hgb\n"
            "6083,COUNTY,999,2019,Overall,Diabetic Events,diab_hgb\n")
        zip_bytes = _build_zip_bytes(
            {"county_hedis_6575ffs.csv": csv_text.encode("utf-8")})
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = Path(tmpdir) / "county_hedis_6575ffs.csv.zip"
            archive.write_bytes(zip_bytes)
            obs: dict[tuple[str, str, str], str] = {}
            download.process_archive(archive,
                                     kind="hedis",
                                     is_state=False,
                                     observations=obs)
        self.assertEqual(
            obs,
            {
                ("2019", "geoId/06083", "MedicareEnrollee_MedicareB"):
                    "3162",
                ("2019", "geoId/06083", "MedicareEnrollee_MedicareB_Black"):
                    "120",
                (
                    "2019",
                    "geoId/06083",
                    "MedicareEnrollee_MedicareB_NonBlack",
                ):
                    "3042",
                ("2019", "geoId/06083", "MedicareEnrollee_Diabetic_Black"):
                    "450",
                (
                    "2019",
                    "geoId/06083",
                    "MedicareEnrollee_Diabetic_NonBlack",
                ):
                    "2700",
            },
        )

    def test_process_mortality_state(self):
        csv_text = ("Year,STATE #,STATE Name,Medicare Enrollees\n"
                    "2019,       1,Alabama,815424\n"
                    "2019,      99,United States,51303426\n")
        zip_bytes = _build_zip_bytes(
            {"state_mortality_2019.csv": csv_text.encode("utf-8")})
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = Path(tmpdir) / "state_mortality_2019.csv.zip"
            archive.write_bytes(zip_bytes)
            obs: dict[tuple[str, str, str], str] = {}
            download.process_archive(archive,
                                     kind="mortality_state",
                                     is_state=True,
                                     observations=obs)
        self.assertEqual(
            obs,
            {
                ("2019", "geoId/01", "MedicareEnrollee_Count"): "815424",
                ("2019", "country/USA", "MedicareEnrollee_Count"): "51303426",
            },
        )

    def test_download_file_raises_on_http_error(self):
        mock_session = mock.MagicMock()
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 404
        mock_resp.raise_for_status.side_effect = requests.HTTPError(
            "404 Not Found")
        mock_session.get.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "raw" / "missing.zip"
            with self.assertRaises(RuntimeError):
                download.download_file(mock_session,
                                       "https://example.com/missing.zip", dest)
            self.assertFalse(dest.exists())

    def test_download_file_raises_on_request_exception(self):
        mock_session = mock.MagicMock()
        mock_session.get.side_effect = requests.Timeout("timed out")

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "raw" / "timeout.zip"
            with self.assertRaises(RuntimeError):
                download.download_file(mock_session,
                                       "https://example.com/timeout.zip", dest)
            self.assertFalse(dest.exists())

    def test_write_cleaned_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "cleaned" / "out.csv"
            obs = {
                ("2019", "geoId/01001", "MedicareEnrollee_Count"): "3774",
                ("2019", "country/USA", "MedicareEnrollee_Count"): "51303426",
            }
            download.write_cleaned_csv(obs, out_path)
            with out_path.open("r", encoding="utf-8") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(
                rows,
                [
                    ["year", "place", "stat_var_key", "value"],
                    [
                        "2019", "country/USA", "MedicareEnrollee_Count",
                        "51303426"
                    ],
                    ["2019", "geoId/01001", "MedicareEnrollee_Count", "3774"],
                ],
            )


if __name__ == "__main__":
    unittest.main()
