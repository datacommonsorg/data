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
"""Unit tests for statvar_imports/school_retention/download_script.py."""

import os
import sys
import tempfile
import unittest

import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.school_retention import download_script


class DownloadScriptTest(unittest.TestCase):
    """Tests ID cleaning, column pruning, reserve code masking, and CSV output."""

    def setUp(self):
        super().setUp()
        self.mapped_cols = download_script.load_pv_mapped_columns()

    def test_load_pv_mapped_columns_includes_all_schema_eras(self):
        """Verifies mapped columns include 2010-2014, 2016-2022, and 2022-2024."""
        self.assertIn("M_AME_7_RET_G1", self.mapped_cols)
        self.assertIn("SCH_RET_KG_IND", self.mapped_cols)
        self.assertIn("SCH_RET_G01_HI_M", self.mapped_cols)
        self.assertIn("SCH_RET_G12_LEP_F", self.mapped_cols)
        self.assertIn("SCH_RET_KG_EL_M", self.mapped_cols)
        self.assertIn("SCH_RET_G12_EL_F", self.mapped_cols)
        self.assertIn("JJ", self.mapped_cols)
        self.assertIn("SCH_JUST", self.mapped_cols)

    def test_pad_id_series_preserves_alphanumeric_and_rejects_invalid(self):
        """Verifies ASCII alnum IDs are uppercased/padded and invalid rejected."""
        leaid_series = pd.Series([
            "100005",
            "100005.0",
            "100005.00",
            "01000ab",
            "",
            "nan",
            None,
            "0000000",
            "123é",
            "²0000",
        ])
        padded_leaid = download_script._pad_id_series(leaid_series, 7)
        self.assertEqual(
            list(padded_leaid),
            [
                "0100005",
                "0100005",
                "0100005",
                "01000AB",
                "",
                "",
                "",
                "",
                "",
                "",
            ],
        )

        schid_series = pd.Series(
            ["870", "870a", "870.0", "00000", "None", "123456"])
        padded_schid = download_script._pad_id_series(schid_series, 5)
        self.assertEqual(
            list(padded_schid),
            ["00870", "0870A", "00870", "", "", ""],
        )

    def test_transform_crdc_data_ncesid_dedup_and_sch_just_normalization(self):
        """Verifies NCESID dedup, SCH_JUST->JJ, and negative code masking."""
        raw_df = pd.DataFrame({
            "LEAID": ["100005", "100005.0", "0100006", "", "0000000"],
            "SCHID": ["870a", "870A", "251", "", "00000"],
            "SCH_JUST": [" No ", "No", "Yes", "No", "No"],
            "SCH_RET_KG_IND": [" Yes ", "No", "No", "Yes", "Yes"],
            "SCH_RET_KG_EL_M": ["5", "99", "-9", "3", "4"],
            "SCH_RET_G01_HI_F": ["-9", "-9", "0", "2", "1"],
            "UNMAPPED_EXTRA_COL": ["100", "200", "300", "400", "500"],
        })

        out_df = download_script.transform_crdc_data(
            raw_df,
            year=2024,
            filename="2024_Retention.csv",
            mapped_cols=self.mapped_cols,
        )

        # Duplicate ('2024', '01000050870A') and invalid NCESIDs are dropped
        self.assertEqual(list(out_df["NCESID"]),
                         ["01000050870A", "010000600251"])

        # First 3 columns must always be ['observationDate', 'NCESID', 'JJ']
        self.assertEqual(
            list(out_df.columns[:3]),
            ["observationDate", "NCESID", "JJ"],
        )
        self.assertEqual(list(out_df["JJ"]), ["No", "Yes"])

        # Unmapped columns must be pruned
        self.assertNotIn("UNMAPPED_EXTRA_COL", out_df.columns)
        self.assertNotIn("SCH_JUST", out_df.columns)

        # Indicator 'Yes'/'No' becomes 1/0; negative code -9 becomes <NA>
        self.assertEqual(list(out_df["SCH_RET_KG_IND"]), [1, 0])
        self.assertEqual(out_df["SCH_RET_KG_EL_M"].iloc[0], 5)
        self.assertTrue(pd.isna(out_df["SCH_RET_KG_EL_M"].iloc[1]))
        self.assertTrue(pd.isna(out_df["SCH_RET_G01_HI_F"].iloc[0]))
        self.assertEqual(out_df["SCH_RET_G01_HI_F"].iloc[1], 0)

    def test_transform_crdc_data_drops_negative_and_non_finite_rows(self):
        """Verifies rows with only negative/inf values are dropped."""
        raw_df = pd.DataFrame({
            "COMBOKEY": ["010000500870", "010000500871", "010000500872"],
            "M_AME_7_RET_G1": ["-9", "4", "inf"],
            "F_AME_7_RET_G1": ["-5", "-9", "-2"],
        })

        out_df = download_script.transform_crdc_data(
            raw_df,
            year=2010,
            filename="2010_Retention.xlsx",
            mapped_cols=self.mapped_cols,
        )

        # First and third schools have only negative or inf values
        self.assertEqual(len(out_df), 1)
        self.assertEqual(out_df["NCESID"].iloc[0], "010000500871")
        self.assertEqual(out_df["JJ"].iloc[0], "")
        self.assertEqual(
            list(out_df.columns[:3]),
            ["observationDate", "NCESID", "JJ"],
        )

        # Verify CSV serialization has no '.0' float suffixes
        csv_text = out_df.to_csv(index=False)
        self.assertNotIn(".0", csv_text)
        self.assertIn("2010,010000500871,,4,", csv_text)

    def test_select_matched_files_excludes_lea_and_prefers_retention(self):
        """Verifies LEA/layout files are excluded and Retention.csv preferred."""
        namelist_with_retention = [
            "2021-22-crdc-data/SCH/Retention.csv",
            "2021-22-crdc-data/LEA/CRDC_LEA_Retention.csv",
            "2021-22-crdc-data/SCH/Retention_layout.xlsx",
            "2021-22-crdc-data/SCH/~$Retention.xlsx",
            "2021-22-crdc-data/SCH/School Data.csv",
        ]
        selected = download_script.select_matched_files(namelist_with_retention)
        self.assertEqual(selected, ["2021-22-crdc-data/SCH/Retention.csv"])

        namelist_2015_16 = [
            "2015-16-crdc-data/CRDC 2015-16 LEA Data.csv",
            "2015-16-crdc-data/CRDC 2015-16 School Data layout.xlsx",
            "2015-16-crdc-data/CRDC 2015-16 School Data.csv",
        ]
        selected_fallback = download_script.select_matched_files(
            namelist_2015_16)
        self.assertEqual(
            selected_fallback,
            ["2015-16-crdc-data/CRDC 2015-16 School Data.csv"],
        )

    def test_get_survey_years_includes_known_crdc_cycles(self):
        """Verifies get_survey_years returns odd years 2009-2017 and 2020+."""
        years = download_script.get_survey_years(current_year=2026)
        for known_year in download_script._KNOWN_SURVEY_YEARS:
            self.assertIn(known_year, years)
        self.assertNotIn(2010, years)
        self.assertNotIn(2018, years)

    def test_process_dataframe_converts_xlsx_fixture_to_csv(self):
        """Verifies process_dataframe converts 2010 XLSX fixture into CSV."""
        fixture_name = (
            "2010_CRDC-collected data_SCH_Pt 2-Retention of Students_"
            "pt 2-students retained in grade 05_input.xlsx")
        fixture_path = os.path.join(download_script.SCRIPT_DIR, "test_data",
                                    fixture_name)
        self.assertTrue(os.path.exists(fixture_path))

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_csv = download_script.process_dataframe(
                fixture_path,
                year=2010,
                mapped_cols=self.mapped_cols,
                output_folder=tmp_dir,
            )
            self.assertTrue(out_csv.endswith(".csv"))
            self.assertTrue(os.path.exists(out_csv))

            df_out = pd.read_csv(out_csv, dtype=str, keep_default_na=False)
            self.assertGreater(len(df_out), 0)
            self.assertEqual(
                list(df_out.columns[:3]),
                ["observationDate", "NCESID", "JJ"],
            )
            for nces_id in df_out["NCESID"]:
                self.assertEqual(len(nces_id), 12)
                self.assertNotEqual(nces_id, "000000000000")
                self.assertTrue(nces_id.isalnum())

    def test_try_download_url_truncates_temp_file_on_retry(self):
        """Verifies try_download_url rewinds/truncates temp_file on retry."""
        import io
        from unittest import mock
        import requests

        class _FlakyRawStream:

            def __init__(self, fail_after_write=False):
                self._fail = fail_after_write
                self._done = False

            def read(self, _size=-1):
                if self._done:
                    return b""
                self._done = True
                if self._fail:
                    raise requests.ConnectionError("mid-stream disconnect")
                return b"CLEAN_ZIP_BYTES"

        class _FakeResponse:

            def __init__(self, raw_stream):
                self.status_code = 200
                self.headers = {"Content-Type": "application/zip"}
                self.raw = raw_stream

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

        session = mock.MagicMock()
        # First attempt writes partial bytes into temp_file before failing
        temp_buf = io.BytesIO(b"STALE_PARTIAL_BYTES")
        temp_buf.seek(len(b"STALE_PARTIAL_BYTES"))
        session.get.side_effect = [
            _FakeResponse(_FlakyRawStream(fail_after_write=True)),
            _FakeResponse(_FlakyRawStream(fail_after_write=False)),
        ]

        with mock.patch("time.sleep"):
            ok = download_script.try_download_url(
                "https://example.com/archive.zip", temp_buf, session=session)
        self.assertTrue(ok)
        self.assertEqual(temp_buf.getvalue(), b"CLEAN_ZIP_BYTES")


if __name__ == "__main__":
    unittest.main()
