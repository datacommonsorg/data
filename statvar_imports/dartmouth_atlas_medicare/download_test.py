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
import gzip
import io
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock
import zipfile

import requests

from statvar_imports.dartmouth_atlas_medicare import consolidate_historical
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
        self.assertEqual(download.format_place_dcid("99999", False),
                         "country/USA")
        self.assertEqual(download.format_place_dcid("99", False), "country/USA")
        # CMS/SSA state codes map to US Census FIPS state codes.
        self.assertEqual(download.format_place_dcid("1", True), "geoId/01")
        self.assertEqual(download.format_place_dcid("3", True), "geoId/04")
        self.assertEqual(download.format_place_dcid("5", True), "geoId/06")
        self.assertEqual(download.format_place_dcid("7", True), "geoId/09")
        self.assertEqual(download.format_place_dcid("9", True), "geoId/11")
        self.assertEqual(download.format_place_dcid("14", True), "geoId/17")
        self.assertEqual(download.format_place_dcid("43", True), "geoId/46")
        self.assertEqual(download.format_place_dcid("52", True), "geoId/55")
        self.assertEqual(download.format_place_dcid("53", True), "geoId/56")
        self.assertEqual(download.format_place_dcid("99", True), "country/USA")
        # Invalid, residual, and out-of-range codes return None.
        self.assertIsNone(download.format_place_dcid("", False))
        self.assertIsNone(download.format_place_dcid("abc", False))
        self.assertIsNone(download.format_place_dcid("0", True))
        self.assertIsNone(download.format_place_dcid("-1", True))
        self.assertIsNone(download.format_place_dcid("40", True))
        self.assertIsNone(download.format_place_dcid("48", True))
        self.assertIsNone(download.format_place_dcid("54", True))
        self.assertIsNone(download.format_place_dcid("100", True))
        self.assertIsNone(download.format_place_dcid("99999", True))
        self.assertIsNone(download.format_place_dcid("1", False))
        self.assertIsNone(download.format_place_dcid("999", False))
        self.assertIsNone(download.format_place_dcid("1000", False))
        self.assertIsNone(download.format_place_dcid("33929", False))
        self.assertIsNone(download.format_place_dcid("99003", False))
        self.assertIsNone(download.format_place_dcid("100000", False))
        self.assertIsNone(download.format_place_dcid("4617620", False))
        self.assertIsNone(download.format_place_dcid("999999", False))

    def test_clean_numeric_value(self):
        self.assertEqual(download.clean_numeric_value(" 7,128 "), "7128")
        self.assertEqual(download.clean_numeric_value("$9,903.76"), "9903.76")
        self.assertEqual(download.clean_numeric_value("218.80"), "218.8")
        for bad in ("", ".", "-", "NaN", "nan", "suppressed", "*", "-5",
                    "-88888", "-99999"):
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

    def test_process_state_stdprices_ssa_to_fips(self):
        csv_text = ("Geo_code,Geo_label,Population,Year,Cohort,Eventname,"
                    "Adjusted_Rate\n"
                    "05,STATE,2313885,2019,StdPrice,stdprice_total,9500.50\n"
                    "53,STATE,66500,2019,StdPrice,stdprice_total,8900.25\n"
                    "99,STATE,26707061,2019,StdPrice,stdprice_total,10100.00\n")
        zip_bytes = _build_zip_bytes(
            {"state_stdprices_ffs.csv": csv_text.encode("utf-8")})
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = Path(tmpdir) / "state_stdprices_ffs.csv.zip"
            archive.write_bytes(zip_bytes)
            obs: dict[tuple[str, str, str], str] = {}
            download.process_archive(archive,
                                     kind="stdprices",
                                     is_state=True,
                                     observations=obs)
        self.assertEqual(
            obs,
            {
                ("2019", "geoId/06", "MedicareEnrollee_Count"): "2313885",
                ("2019", "geoId/06", "MedicareEnrollee_MeanPrice"): "9500.5",
                ("2019", "geoId/56", "MedicareEnrollee_Count"): "66500",
                ("2019", "geoId/56", "MedicareEnrollee_MeanPrice"): "8900.25",
                ("2019", "country/USA", "MedicareEnrollee_Count"): "26707061",
                ("2019", "country/USA", "MedicareEnrollee_MeanPrice"): "10100",
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
                ("2019", "country/USA", "MedicareEnrollee_Count"): "26707061",
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
                        "26707061"
                    ],
                    ["2019", "geoId/01001", "MedicareEnrollee_Count", "3774"],
                ],
            )

    def test_copy_historical_files_from_gcs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "output_files"
            with mock.patch.object(download.file_util,
                                   "file_copy") as mock_copy:
                # Empty historical_gcs_dir is a no-op.
                self.assertEqual(
                    download.copy_historical_files_from_gcs("", out_dir), [])
                mock_copy.assert_not_called()
                self.assertFalse((out_dir / "common_tmcf.tmcf").exists())

                gcs_dir = ("gs://unresolved_mcf/dartmouth_atlas_medicare/"
                           "historical/")
                copied = download.copy_historical_files_from_gcs(
                    gcs_dir, out_dir)
                self.assertEqual(
                    copied,
                    [out_dir / fname for fname in download.HISTORICAL_CSVS])
                self.assertEqual(
                    (out_dir / "common_tmcf.tmcf").read_text(encoding="utf-8"),
                    download.COMMON_TMCF_CONTENT,
                )
                expected_calls = [
                    mock.call(
                        "gs://unresolved_mcf/dartmouth_atlas_medicare/"
                        f"historical/{fname}",
                        str(out_dir / fname),
                    ) for fname in download.HISTORICAL_CSVS
                ]
                mock_copy.assert_has_calls(expected_calls)

            # Local self-copy skips file_copy cleanly.
            local_hist = out_dir / download.HISTORICAL_CSVS[0]
            local_hist.write_text(
                "observationDate,observationAbout,variableMeasured,value,"
                "observationPeriod\n",
                encoding="utf-8",
            )
            with mock.patch.object(download.file_util,
                                   "file_copy") as mock_copy:
                copied_self = download.copy_historical_files_from_gcs(
                    str(out_dir), out_dir)
                self.assertEqual(copied_self, [local_hist])
                mock_copy.assert_not_called()

            # GCS copy errors propagate cleanly.
            with (
                    mock.patch.object(
                        download.file_util,
                        "file_copy",
                        side_effect=RuntimeError("GCS copy failed"),
                    ),
                    self.assertRaisesRegex(RuntimeError, "GCS copy failed"),
            ):
                download.copy_historical_files_from_gcs(
                    "gs://unresolved_mcf/dartmouth_atlas_medicare/historical",
                    out_dir,
                )

    def test_load_historical_keys_and_filter_observations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hist_csv = Path(tmpdir) / "historical.csv"
            hist_csv.write_text(
                "observationDate,observationAbout,variableMeasured,value,"
                "observationPeriod\n"
                "2016,dcid:geoId/01001,dcid:Count_MedicareEnrollee,4100,P1Y\n"
                "2016,dcid:geoId/01001,dcid:dc/rn90czcrqcv06,10200,P1Y\n"
                "2014,dcid:geoId/06083,dcs:Count_MedicareEnrollee_MedicareB,"
                "3100,P1Y\n",
                encoding="utf-8",
            )
            keys = download.load_historical_observation_keys([hist_csv])
            self.assertEqual(
                keys,
                {
                    ("2016", "geoId/01001", "Count_MedicareEnrollee"),
                    ("2016", "geoId/01001", "dc/rn90czcrqcv06"),
                    ("2014", "geoId/06083", "Count_MedicareEnrollee_MedicareB"),
                },
            )

            live_obs = {
                ("2016", "geoId/01001", "MedicareEnrollee_Count"): "4101",
                ("2016", "geoId/01001", "MedicareEnrollee_MeanPrice"): "10205",
                ("2017", "geoId/01001", "MedicareEnrollee_Count"): "4200",
                ("2017", "geoId/01001", "MedicareEnrollee_MeanPrice"): "10500",
                ("2014", "geoId/06083", "MedicareEnrollee_MedicareB"): "3105",
                ("2015", "geoId/06083", "MedicareEnrollee_MedicareB"): "3150",
                ("2016", "geoId/06", "MedicareEnrollee_Count"): "2200000",
            }
            filtered = download.filter_out_historical_observations(
                live_obs, keys)
            self.assertEqual(
                filtered,
                {
                    ("2017", "geoId/01001", "MedicareEnrollee_Count"):
                        "4200",
                    ("2017", "geoId/01001", "MedicareEnrollee_MeanPrice"):
                        "10500",
                    ("2015", "geoId/06083", "MedicareEnrollee_MedicareB"):
                        "3150",
                    ("2016", "geoId/06", "MedicareEnrollee_Count"):
                        "2200000",
                },
            )


class ConsolidateHistoricalTest(unittest.TestCase):
    """Tests legacy CNS MCF consolidation in consolidate_historical.py."""

    def _write_subtable_mcf(self, root: Path, subtable: str,
                            content: str) -> None:
        sub_dir = root / subtable
        sub_dir.mkdir(parents=True, exist_ok=True)
        (sub_dir / "nodes.mcf-00000-of-00001").write_text(content,
                                                          encoding="utf-8")

    def test_consolidate_baseline_all_10_statvars_and_dedup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cns_root = Path(tmpdir) / "stat_pop"
            out_dir = Path(tmpdir) / "historical"

            self._write_subtable_mcf(
                cns_root,
                "dartmouth_reim_count",
                ("Node: E:Obs0\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2016"\n'
                 "observationAbout: dcid:geoId/01001\n"
                 "variableMeasured: dcid:Count_MedicareEnrollee\n"
                 "value: 4100\n"
                 'observationPeriod: "P1Y"\n\n'
                 "Node: E:Obs1\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2008"\n'
                 "observationAbout: dcid:geoId/02201\n"
                 "variableMeasured: dcid:Count_MedicareEnrollee\n"
                 "value: 520\n"
                 'observationPeriod: "P1Y"\n\n'
                 "Node: E:ObsBadNaN\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2016"\n'
                 "observationAbout: dcid:geoId/4617620\n"
                 "variableMeasured: dcid:Count_MedicareEnrollee\n"
                 "value: NaN\n"
                 'observationPeriod: "P1Y"\n\n'
                 "Node: E:ObsLegacyBogus99999\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2010"\n'
                 "observationAbout: dcid:geoId/99999\n"
                 "variableMeasured: dcid:Count_MedicareEnrollee\n"
                 "value: 25450227\n"
                 'observationPeriod: "P1Y"\n\n'
                 "Node: E:ObsLegacyBogus999999\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2011"\n'
                 "observationAbout: dcid:geoId/999999\n"
                 "variableMeasured: dcid:Count_MedicareEnrollee_MedicareA\n"
                 "value: 28423229\n"
                 'observationPeriod: "P1Y"\n\n'
                 "Node: E:ObsLegacyBogus99003\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2009"\n'
                 "observationAbout: dcid:geoId/99003\n"
                 "variableMeasured: dcid:Count_MedicareEnrollee\n"
                 "value: 835\n"
                 'observationPeriod: "P1Y"\n\n'
                 "Node: E:ObsLegacyBogus33929\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2010"\n'
                 "observationAbout: dcid:geoId/33929\n"
                 "variableMeasured: dcid:Count_MedicareEnrollee\n"
                 "value: 79\n"
                 'observationPeriod: "P1Y"\n'),
            )
            # dartmouth_reim has multiple collapsed slices (DME vs Total);
            # consolidation must pick the largest value (Total).
            self._write_subtable_mcf(
                cns_root,
                "dartmouth_reim",
                ("Node: E:ReimDme\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2016"\n'
                 "observationAbout: dcid:geoId/01001\n"
                 "variableMeasured: dcid:dc/rn90czcrqcv06\n"
                 'value: " 218.50 "\n'
                 'observationPeriod: "P1Y"\n\n'
                 "Node: E:ReimTotal\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2016"\n'
                 "observationAbout: dcid:geoId/01001\n"
                 "variableMeasured: dcid:dc/rn90czcrqcv06\n"
                 'value: " 10,450.25 "\n'
                 'observationPeriod: "P1Y"\n'),
            )
            self._write_subtable_mcf(
                cns_root,
                "dartmouth_num_overall",
                ("Node: E:PartA\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2014"\n'
                 "observationAbout: dcid:geoId/06083\n"
                 "variableMeasured: dcid:Count_MedicareEnrollee_MedicareA\n"
                 "value: 3500\n"
                 'observationPeriod: "P1Y"\n\n'
                 "Node: E:PartB\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2007"\n'
                 "observationAbout: dcid:geoId/06083\n"
                 "variableMeasured: dcid:Count_MedicareEnrollee_MedicareB\n"
                 "value: 3000\n"
                 'observationPeriod: "P1Y"\n'),
            )
            self._write_subtable_mcf(
                cns_root,
                "dartmouth_num_enrollees",
                ("Node: E:PartABlack\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2014"\n'
                 "observationAbout: dcid:geoId/06083\n"
                 "variableMeasured: "
                 "dcid:Count_MedicareEnrollee_MedicareA_Black\n"
                 "value: 130\n"
                 'observationPeriod: "P1Y"\n\n'
                 "Node: E:PartANonBlack\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2014"\n'
                 "observationAbout: dcid:geoId/06083\n"
                 "variableMeasured: "
                 "dcid:Count_MedicareEnrollee_MedicareA_NonBlack\n"
                 "value: 3370\n"
                 'observationPeriod: "P1Y"\n\n'
                 "Node: E:PartBBlack\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2007"\n'
                 "observationAbout: dcid:geoId/06083\n"
                 "variableMeasured: "
                 "dcid:Count_MedicareEnrollee_MedicareB_Black\n"
                 "value: 110\n"
                 'observationPeriod: "P1Y"\n\n'
                 "Node: E:PartBNonBlack\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2007"\n'
                 "observationAbout: dcid:geoId/06083\n"
                 "variableMeasured: "
                 "dcid:Count_MedicareEnrollee_MedicareB_NonBlack\n"
                 "value: 2890\n"
                 'observationPeriod: "P1Y"\n'),
            )
            self._write_subtable_mcf(
                cns_root,
                "dartmouth_num_diabetics",
                ("Node: E:DiabBlack\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2007"\n'
                 "observationAbout: dcid:geoId/06083\n"
                 "variableMeasured: "
                 "dcid:Count_MedicareEnrollee_ConditionDiabetic_Black\n"
                 "value: 45\n"
                 'observationPeriod: "P1Y"\n\n'
                 "Node: E:DiabNonBlack\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2007"\n'
                 "observationAbout: dcid:geoId/06083\n"
                 "variableMeasured: "
                 "dcid:Count_MedicareEnrollee_ConditionDiabetic_NonBlack\n"
                 "value: 410\n"
                 'observationPeriod: "P1Y"\n'),
            )
            # dartmouth_mortality_count adds 1999 HRR/HSA city AND attempts to
            # overwrite 2016 geoId/01001 (which dartmouth_reim_count wins).
            self._write_subtable_mcf(
                cns_root,
                "dartmouth_mortality_count",
                ("Node: E:City1999\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "1999"\n'
                 "observationAbout: dcid:geoId/0203000\n"
                 "variableMeasured: dcid:Count_MedicareEnrollee\n"
                 "value: 15200\n"
                 'observationPeriod: "P1Y"\n\n'
                 "Node: E:OverlapIgnored\n"
                 "typeOf: dcs:StatVarObservation\n"
                 'observationDate: "2016"\n'
                 "observationAbout: dcid:geoId/01001\n"
                 "variableMeasured: dcid:Count_MedicareEnrollee\n"
                 "value: 99999\n"
                 'observationPeriod: "P1Y"\n'),
            )

            csv_path, tmcf_path, mcf_path = (
                consolidate_historical.consolidate_baseline(
                    source_dir=str(cns_root),
                    output_dir=out_dir,
                ))

            with csv_path.open("r", encoding="utf-8") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows[0], consolidate_historical.OUTPUT_COLUMNS)
            by_key = {(r[0], r[1], r[2]): (r[3], r[4]) for r in rows[1:]}
            self.assertEqual(len(by_key), 12)
            # Total reimbursement selected over DME slice.
            self.assertEqual(
                by_key[("2016", "dcid:geoId/01001", "dcid:dc/rn90czcrqcv06")],
                ("10450.25", "P1Y"),
            )
            # dartmouth_reim_count takes precedence over mortality overlap.
            self.assertEqual(
                by_key[("2016", "dcid:geoId/01001",
                        "dcid:Count_MedicareEnrollee")],
                ("4100", "P1Y"),
            )
            # 1999 HRR/HSA City and retired Alaska FIPS preserved.
            self.assertEqual(
                by_key[("1999", "dcid:geoId/0203000",
                        "dcid:Count_MedicareEnrollee")],
                ("15200", "P1Y"),
            )
            self.assertEqual(
                by_key[("2008", "dcid:geoId/02201",
                        "dcid:Count_MedicareEnrollee")],
                ("520", "P1Y"),
            )
            # All 10 production StatVars present.
            unique_svs = {r[2].removeprefix("dcid:") for r in rows[1:]}
            self.assertEqual(unique_svs,
                             consolidate_historical.ALLOWED_STAT_VARS)
            self.assertEqual(
                tmcf_path.read_text(encoding="utf-8"),
                consolidate_historical.COMMON_TMCF_CONTENT,
            )
            csv_text = csv_path.read_text(encoding="utf-8")
            mcf_text = mcf_path.read_text(encoding="utf-8")
            self.assertIn("variableMeasured: dcid:dc/rn90czcrqcv06", mcf_text)
            self.assertIn("value: 10450.25", mcf_text)
            # Numeric years must be unquoted to match import-tool genmcf and
            # import_differ mcf_file_util.normalize_value().
            self.assertIn("observationDate: 2016\n", mcf_text)
            self.assertNotIn('observationDate: "2016"', mcf_text)
            # Consolidated CSV drops unresolved legacy geoIds (0 lint errors),
            # while baseline MCF retains all unaltered CNS observations so
            # import_differ audits against the true previous refresh.
            for bad_place in ("geoId/99999", "geoId/999999", "geoId/99003",
                              "geoId/33929"):
                self.assertNotIn(f"dcid:{bad_place},", csv_text)
                self.assertIn(f"observationAbout: dcid:{bad_place}\n", mcf_text)

    def test_is_valid_historical_place(self):
        for valid in ("country/USA", "geoId/01", "geoId/56", "geoId/72",
                      "geoId/01001", "geoId/02201", "geoId/51840",
                      "geoId/0203000", "geoId/4617620"):
            self.assertTrue(
                consolidate_historical.is_valid_historical_place(valid), valid)
        for invalid in ("", "USA", "geoId/", "geoId/03", "geoId/07", "geoId/99",
                        "geoId/01000", "geoId/33929", "geoId/99003",
                        "geoId/99999", "geoId/999999", "geoId/0100000"):
            self.assertFalse(
                consolidate_historical.is_valid_historical_place(invalid),
                invalid)

    def test_consolidate_baseline_with_reim_csv_override(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cns_root = Path(tmpdir) / "stat_pop"
            out_dir = Path(tmpdir) / "historical"
            for tbl in consolidate_historical.ACTIVE_SUBTABLES:
                self._write_subtable_mcf(
                    cns_root,
                    tbl,
                    ("Node: E:Obs0\n"
                     "typeOf: dcs:StatVarObservation\n"
                     'observationDate: "2016"\n'
                     "observationAbout: dcid:geoId/01001\n"
                     "variableMeasured: dcid:dc/rn90czcrqcv06\n"
                     "value: 11111\n"
                     'observationPeriod: "P1Y"\n'),
                )
            reim_csv = Path(tmpdir) / "dartmouth_reim.csv"
            reim_csv.write_text(
                "year,geoId,hasMedicareReimbursementFor,adjustmentType,value\n"
                "2016,geoId/01001,TotalMedicareReimbursement,"
                "ageSexRace,11111\n"
                "2016,geoId/01001,TotalMedicareReimbursement,"
                "priceAgeSexRace,10321.50\n"
                "2016,geoId/01001,HospitalReimbursement,"
                "priceAgeSexRace,4000\n",
                encoding="utf-8",
            )
            csv_path, _, _ = consolidate_historical.consolidate_baseline(
                source_dir=str(cns_root),
                output_dir=out_dir,
                reim_csv=str(reim_csv),
            )
            with csv_path.open("r", encoding="utf-8") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(
                rows[1],
                [
                    "2016", "dcid:geoId/01001", "dcid:dc/rn90czcrqcv06",
                    "10321.5", "P1Y"
                ],
            )

    def _encode_varint(self, val: int) -> bytes:
        out = bytearray()
        while True:
            to_write = val & 0x7F
            val >>= 7
            if val:
                out.append(to_write | 0x80)
            else:
                out.append(to_write)
                return bytes(out)

    def _encode_len_field(self, field_num: int, payload: bytes) -> bytes:
        tag = (field_num << 3) | 2
        return (self._encode_varint(tag) + self._encode_varint(len(payload)) +
                payload)

    def _encode_double_field(self, field_num: int, val: float) -> bytes:
        tag = (field_num << 3) | 1
        return self._encode_varint(tag) + struct.pack("<d", val)

    def _encode_extra_pvs(self, pvs: dict[str, str]) -> bytes:
        entries = bytearray()
        for k, v in pvs.items():
            # TypedVal: field 2 = string val
            typed_val = self._encode_len_field(2, v.encode("utf-8"))
            # Vals: field 2 = TypedVal
            vals_msg = self._encode_len_field(2, typed_val)
            # MapEntry: field 1 = key, field 2 = Vals
            entry = (self._encode_len_field(1, k.encode("utf-8")) +
                     self._encode_len_field(2, vals_msg))
            entries.extend(self._encode_len_field(1, entry))
        return bytes(entries)

    def _build_tfrecord_gz(self, records: list[bytes]) -> bytes:
        raw = io.BytesIO()
        for rec in records:
            raw.write(struct.pack("<QI", len(rec), 0))
            raw.write(rec)
            raw.write(struct.pack("<I", 0))
        gz_buf = io.BytesIO()
        with gzip.GzipFile(fileobj=gz_buf, mode="wb") as gz:
            gz.write(raw.getvalue())
        return gz_buf.getvalue()

    def test_consolidate_tfrecord_gzip_with_schema_only_nodes_mcf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cns_root = Path(tmpdir) / "stat_pop"
            out_dir = Path(tmpdir) / "historical"

            for idx, tbl in enumerate(consolidate_historical.ACTIVE_SUBTABLES):
                sub_dir = cns_root / tbl
                sub_dir.mkdir(parents=True, exist_ok=True)
                # Mimic CNS stat_pop/: nodes.mcf contains only StatVar schema!
                (sub_dir / "nodes.mcf").write_text(
                    "Node: dcid:Count_MedicareEnrollee\n"
                    "typeOf: dcs:StatisticalVariable\n",
                    encoding="utf-8",
                )
                if tbl == "dartmouth_reim":
                    key_msg = (self._encode_len_field(1, b"geoId/01001") +
                               self._encode_len_field(2, b"dc/rn90czcrqcv06") +
                               self._encode_len_field(4, b"P1Y"))
                    # Slice 1: higher ageSexRace Total (should be ignored
                    # because slice tags identify Slice 2 as priceAgeSexRace).
                    obs_asr = (self._encode_len_field(1, b"2016") +
                               self._encode_double_field(2, 11500.0) +
                               self._encode_len_field(
                                   4,
                                   self._encode_extra_pvs({
                                       "adjustmentType":
                                           "ageSexRace",
                                       "hasMedicareReimbursementFor":
                                           "TotalMedicareReimbursement",
                                   }),
                               ))
                    obs_pasr = (self._encode_len_field(1, b"2016") +
                                self._encode_double_field(2, 10450.25) +
                                self._encode_len_field(
                                    4,
                                    self._encode_extra_pvs({
                                        "adjustmentType":
                                            "priceAgeSexRace",
                                        "hasMedicareReimbursementFor":
                                            "TotalMedicareReimbursement",
                                    }),
                                ))
                    series = (self._encode_len_field(1, key_msg) +
                              self._encode_len_field(2, obs_asr) +
                              self._encode_len_field(2, obs_pasr))
                else:
                    key_msg = (
                        self._encode_len_field(
                            1, f"geoId/0100{idx + 1}".encode()) +
                        self._encode_len_field(2, b"Count_MedicareEnrollee") +
                        self._encode_len_field(4, b"P1Y"))
                    obs_good = (self._encode_len_field(1, b"2015") +
                                self._encode_double_field(2, 3000.0 + idx))
                    obs_nan = (self._encode_len_field(1, b"2016") +
                               self._encode_double_field(2, float("nan")))
                    series = (self._encode_len_field(1, key_msg) +
                              self._encode_len_field(2, obs_good) +
                              self._encode_len_field(2, obs_nan))

                opt_graph = self._encode_len_field(1, series)
                (sub_dir / "graph.tfrecord-00000-of-00001.gz").write_bytes(
                    self._build_tfrecord_gz([opt_graph]))

            csv_path, _, _ = consolidate_historical.consolidate_baseline(
                source_dir=str(cns_root),
                output_dir=out_dir,
            )
            with csv_path.open("r", encoding="utf-8") as handle:
                rows = list(csv.reader(handle))
            by_key = {(r[0], r[1], r[2]): r[3] for r in rows[1:]}
            self.assertEqual(len(by_key), 6)
            self.assertEqual(
                by_key[("2016", "dcid:geoId/01001", "dcid:dc/rn90czcrqcv06")],
                "10450.25",
            )
            self.assertEqual(
                by_key[("2015", "dcid:geoId/01001",
                        "dcid:Count_MedicareEnrollee")],
                "3000",
            )

    def test_consolidate_baseline_raises_on_missing_subtable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cns_root = Path(tmpdir) / "stat_pop"
            out_dir = Path(tmpdir) / "historical"
            self._write_subtable_mcf(
                cns_root,
                "dartmouth_reim_count",
                "Node: E:Obs0\ntypeOf: dcs:StatVarObservation\n",
            )
            with self.assertRaisesRegex(RuntimeError,
                                        "Missing required legacy"):
                consolidate_historical.consolidate_baseline(
                    source_dir=str(cns_root),
                    output_dir=out_dir,
                )


if __name__ == "__main__":
    unittest.main()
