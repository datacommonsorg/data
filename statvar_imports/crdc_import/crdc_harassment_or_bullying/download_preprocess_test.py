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
"""Unit tests for CRDC Harassment or Bullying download, preprocess, and config."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "../../.."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.crdc_import.crdc_harassment_or_bullying import (  # noqa: E402, I001
    download, preprocess,
)
from tools.import_validation.validator import (  # noqa: E402, I001
    ValidationStatus, Validator,
)


class DownloadAndDiscoveryTest(unittest.TestCase):
    """Tests deterministic file discovery and download retry/fail-fast logic."""

    def test_survey_start_years_skips_non_biennial_historical_years(self):
        years = download.get_survey_start_years(current_year=2026)
        self.assertEqual(years,
                         [2011, 2013, 2017, 2020, 2021, 2023, 2024, 2025, 2026])
        for skipped in (2012, 2014, 2015, 2016, 2018, 2019, 2022):
            self.assertNotIn(skipped, years)

    def test_2011_12_ignores_allegations_lea_macosx_and_emits_6_parts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dl = os.path.join(tmpdir, "source_files")
            out_dir = os.path.join(tmpdir, "input_files")
            year_dir = os.path.join(base_dl, "crdc_data_2011-12")

            # 1. Decoy __MACOSX hidden folder
            macosx_dir = os.path.join(
                year_dir,
                "__MACOSX",
                "2011-12 Public Use File",
                "SCH",
                "Pt 2-Harassment or Bullying",
            )
            os.makedirs(macosx_dir, exist_ok=True)
            with open(os.path.join(macosx_dir, "._part1.xlsx"), "wb") as f:
                f.write(b"not an excel file")

            # 2. Decoy LEA folder
            lea_dir = os.path.join(
                year_dir,
                "2011-12 Public Use File",
                "LEA",
                "CRDC-collected data file for LEAs",
                "Pt 2-Harassment or Bullying",
            )
            os.makedirs(lea_dir, exist_ok=True)
            pd.DataFrame({
                "LEAID": ["0100005"],
                "M_AME_5_DISC_HAR_DIS": ["1"],
            }).to_excel(os.path.join(lea_dir, "lea_harassment.xlsx"),
                        index=False)

            # 3. Decoy sibling folder that caused the 5 production Batch failures:
            #    "Pt 2-Reported Allegations of Harassment or Bullying" (1 file)
            alleg_dir = os.path.join(
                year_dir,
                "2011-12 Public Use File",
                "SCH",
                "CRDC-collected data file for schools",
                "Pt 2-Reported Allegations of Harassment or Bullying",
            )
            os.makedirs(alleg_dir, exist_ok=True)
            pd.DataFrame({
                "COMBOKEY": ["010000500871"],
                "ALLEG_HAR_SEX": ["2"],
            }).to_excel(
                os.path.join(
                    alleg_dir,
                    "2011-12 Public Use File_SCH_CRDC-Pt 2-Rep Alleg of Harass or Bully_37.xlsx",
                ),
                index=False,
            )

            # 4. Actual 6 mapped school Harassment or Bullying Excel tables
            sch_dir = os.path.join(
                year_dir,
                "2011-12 Public Use File",
                "SCH",
                "CRDC-collected data file for schools",
                "Pt 2-Harassment or Bullying",
            )
            os.makedirs(sch_dir, exist_ok=True)
            metric_cols = [
                "M_AME_5_DISC_HAR_DIS",
                "M_AME_5_DISC_HAR_SEX",
                "M_AME_5_DISC_HAR_RACE",
                "M_AME_5_HARASSED_DIS",
                "M_AME_5_HARASSED_SEX",
                "M_AME_5_HARASSED_RACE",
            ]
            for idx, metric_col in enumerate(metric_cols, start=1):
                df = pd.DataFrame({
                    "LEAID": ["0100005", "0100006"],
                    "COMBOKEY": ["010000500871", "10000600123.0"],
                    metric_col: [str(idx), "-9"],
                })
                df.to_excel(
                    os.path.join(sch_dir, f"table_{idx:02d}_harassment.xlsx"),
                    index=False,
                )

            written = download.collect_and_convert_year_files(
                year_range="2011-12",
                base_download_dir=base_dl,
                output_dir=out_dir,
            )
            self.assertEqual(len(written), 6)
            expected_names = [
                f"crdc_harassment_or_bullying_2012_part_{i:02d}.csv"
                for i in range(1, 7)
            ]
            self.assertEqual([os.path.basename(p) for p in written],
                             expected_names)

            part1_df = pd.read_csv(written[0], dtype=str, keep_default_na=False)
            self.assertEqual(part1_df["COMBOKEY"].tolist(),
                             ["010000500871", "10000600123.0"])
            self.assertEqual(part1_df["M_AME_5_DISC_HAR_DIS"].tolist(),
                             ["1", "-9"])

    def test_2011_12_raises_when_expected_6_parts_incomplete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dl = os.path.join(tmpdir, "source_files")
            out_dir = os.path.join(tmpdir, "input_files")
            sch_dir = os.path.join(
                base_dl,
                "crdc_data_2011-12",
                "SCH",
                "Pt 2-Harassment or Bullying",
            )
            os.makedirs(sch_dir, exist_ok=True)
            pd.DataFrame({
                "COMBOKEY": ["010000500871"],
                "M_AME_5_DISC_HAR_DIS": ["3"],
            }).to_csv(os.path.join(sch_dir, "only_one_harassment.csv"),
                      index=False)

            with self.assertRaisesRegex(RuntimeError, "Expected exactly 6"):
                download.collect_and_convert_year_files(
                    year_range="2011-12",
                    base_download_dir=base_dl,
                    output_dir=out_dir,
                )

    @mock.patch.object(download, "download_file")
    def test_download_year_archive_retries_then_succeeds(self, mock_dl):
        mock_dl.side_effect = [False, False, True]
        session = mock.MagicMock()
        with tempfile.TemporaryDirectory() as tmpdir:
            ok = download.download_year_archive(
                year_range="2011-12",
                url=
                "https://civilrightsdata.ed.gov/assets/ocr/docs/2011-12-crdc-data.zip",
                output_dir_for_year=os.path.join(tmpdir, "crdc_data_2011-12"),
                is_required=True,
                session=session,
                sleep_fn=lambda _: None,
            )
        self.assertTrue(ok)
        self.assertEqual(mock_dl.call_count, 3)

    @mock.patch.object(download, "download_file")
    def test_download_year_archive_fails_fast_when_required_year_unavailable(
            self, mock_dl):
        mock_dl.return_value = False
        session = mock.MagicMock()
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(RuntimeError,
                                        "Failed to download and extract"):
                download.download_year_archive(
                    year_range="2017-18",
                    url=
                    "https://civilrightsdata.ed.gov/assets/ocr/docs/2017-18-crdc-data.zip",
                    output_dir_for_year=os.path.join(tmpdir,
                                                     "crdc_data_2017-18"),
                    is_required=True,
                    session=session,
                    sleep_fn=lambda _: None,
                )
        self.assertEqual(mock_dl.call_count, 3)

    @mock.patch.object(download, "download_file")
    def test_optional_future_year_skips_html_soft_404_without_get(
            self, mock_dl):
        session = mock.MagicMock()
        head_resp = mock.MagicMock()
        head_resp.status_code = 200
        head_resp.headers = {"Content-Type": "text/html; charset=utf-8"}
        session.head.return_value = head_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            ok = download.download_year_archive(
                year_range="2025-26",
                url=
                "https://civilrightsdata.ed.gov/assets/ocr/docs/2025-26-crdc-data.zip",
                output_dir_for_year=os.path.join(tmpdir, "crdc_data_2025-26"),
                is_required=False,
                session=session,
                sleep_fn=lambda _: None,
            )
        self.assertFalse(ok)
        mock_dl.assert_not_called()

    @mock.patch.object(download, "download_file")
    def test_optional_future_year_raises_if_confirmed_zip_fails_download(
            self, mock_dl):
        mock_dl.return_value = False
        session = mock.MagicMock()
        head_resp = mock.MagicMock()
        head_resp.status_code = 200
        head_resp.headers = {"Content-Type": "application/zip"}
        session.head.return_value = head_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(RuntimeError,
                                        "Failed to download and extract"):
                download.download_year_archive(
                    year_range="2025-26",
                    url=
                    "https://civilrightsdata.ed.gov/assets/ocr/docs/2025-26-crdc-data.zip",
                    output_dir_for_year=os.path.join(tmpdir,
                                                     "crdc_data_2025-26"),
                    is_required=False,
                    session=session,
                    sleep_fn=lambda _: None,
                )
        self.assertEqual(mock_dl.call_count, 3)


class PreprocessAndRunScriptTest(unittest.TestCase):
    """Tests non-destructive preprocessing and run.sh contract checks."""

    def test_preprocess_preserves_raw_input_leading_zeros_blanks_and_latin1(
            self):
        with tempfile.TemporaryDirectory() as tmpdir:
            in_dir = os.path.join(tmpdir, "input_files")
            out_dir = os.path.join(tmpdir, "preprocessed_files")
            os.makedirs(in_dir, exist_ok=True)

            raw_csv = os.path.join(in_dir,
                                   "crdc_harassment_or_bullying_2024.csv")
            raw_content = (
                "`LEAID`,\"SCH_NAME\",COMBOKEY,SCH_HBALLEGATIONS_SEX\n"
                "0100005,\"St. Mary's Café\",010000500871.0,`12`\n"
                "0100006,'Oak High',010000600999,\n")
            with open(raw_csv, "wb") as f:
                f.write(raw_content.encode("latin-1"))

            written = preprocess.run_preprocess(input_dir=in_dir,
                                                output_dir=out_dir)
            self.assertEqual(len(written), 1)

            # Raw input file must remain completely untouched.
            with open(raw_csv, "rb") as f:
                self.assertEqual(f.read(), raw_content.encode("latin-1"))

            cleaned = pd.read_csv(written[0], dtype=str, keep_default_na=False)
            self.assertEqual(
                cleaned.columns.tolist(),
                [
                    "LEAID", "Year", "SCH_NAME", "COMBOKEY",
                    "SCH_HBALLEGATIONS_SEX"
                ],
            )
            self.assertEqual(cleaned["Year"].tolist(), ["2024", "2024"])
            self.assertEqual(cleaned["COMBOKEY"].tolist(),
                             ["010000500871", "010000600999"])
            self.assertEqual(cleaned["SCH_NAME"].tolist(),
                             ["St. Marys Café", "Oak High"])
            self.assertEqual(cleaned["SCH_HBALLEGATIONS_SEX"].tolist(),
                             ["12", ""])

    def test_preprocess_raises_on_missing_year_or_empty_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            in_dir = os.path.join(tmpdir, "input_files")
            out_dir = os.path.join(tmpdir, "preprocessed_files")
            os.makedirs(in_dir, exist_ok=True)
            bad_path = os.path.join(in_dir, "crdc_no_year.csv")
            with open(bad_path, "w", encoding="utf-8") as f:
                f.write("LEAID,COMBOKEY\n01,010000500871\n")

            with self.assertRaisesRegex(ValueError, "4-digit survey year"):
                preprocess.run_preprocess(input_dir=in_dir, output_dir=out_dir)

    def test_run_sh_pre_flight_and_post_flight_contracts(self):
        run_sh = os.path.join(_THIS_DIR, "run.sh")
        with tempfile.TemporaryDirectory() as tmpdir:
            in_dir = os.path.join(tmpdir, "preprocessed_files")
            out_dir = os.path.join(tmpdir, "processed_output")
            os.makedirs(in_dir, exist_ok=True)

            # Create a lightweight stub processor that writes .tmcf and .csv
            stub_proc = os.path.join(tmpdir, "stub_processor.py")
            with open(stub_proc, "w", encoding="utf-8") as f:
                f.write(
                    "import sys\n"
                    "out = [a.split('=', 1)[1] for a in sys.argv[1:] "
                    "if a.startswith('--output_path=')][0]\n"
                    "with open(out + '.tmcf', 'w') as tf:\n"
                    "    tf.write('Node: E:t->E0\\n')\n"
                    "with open(out + '.csv', 'w') as cf:\n"
                    "    cf.write('observationAbout,observationDate,value\\n"
                    "nces/010000500871,2024,1\\n')\n")

            # 1. Missing 2012_part_01..06 -> must fail fast before processing
            with open(
                    os.path.join(in_dir,
                                 "crdc_harassment_or_bullying_2012.csv"),
                    "w",
                    encoding="utf-8",
            ) as f:
                f.write("LEAID,Year,COMBOKEY\n01,2012,010000500871\n")

            env = os.environ.copy()
            env.update({
                "INPUT_DIR": in_dir,
                "OUTPUT_DIR": out_dir,
                "PYTHON_SCRIPT": stub_proc,
                "PYTHON_BIN": sys.executable,
            })
            failed_proc = subprocess.run(
                ["bash", run_sh],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(failed_proc.returncode, 0)
            self.assertIn("crdc_harassment_or_bullying_2012_part_01.csv",
                          failed_proc.stderr)

            # 2. Populate all required partitions (+ future 2026) -> must succeed
            os.remove(
                os.path.join(in_dir, "crdc_harassment_or_bullying_2012.csv"))
            all_inputs = [
                f"crdc_harassment_or_bullying_2012_part_{i:02d}.csv"
                for i in range(1, 7)
            ] + [
                "crdc_harassment_or_bullying_2014.csv",
                "crdc_harassment_or_bullying_2018.csv",
                "crdc_harassment_or_bullying_2021.csv",
                "crdc_harassment_or_bullying_2022.csv",
                "crdc_harassment_or_bullying_2024.csv",
                "crdc_harassment_or_bullying_2026.csv",
            ]
            for name in all_inputs:
                with open(os.path.join(in_dir, name), "w",
                          encoding="utf-8") as f:
                    f.write("LEAID,Year,COMBOKEY\n01,2024,010000500871\n")

            ok_proc = subprocess.run(
                ["bash", run_sh],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(ok_proc.returncode, 0, msg=ok_proc.stderr)
            self.assertTrue(
                os.path.isfile(
                    os.path.join(
                        out_dir,
                        "crdc_harassment_or_bullying_2012_part_01.tmcf")))
            self.assertTrue(
                os.path.isfile(
                    os.path.join(
                        out_dir,
                        "crdc_harassment_or_bullying_2024Onwards.tmcf")))


class ManifestAndValidationConfigTest(unittest.TestCase):
    """Tests manifest.json contract and validation_config.json rules."""

    def test_manifest_references_valid_scripts_and_validation_config(self):
        manifest_path = os.path.join(_THIS_DIR, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        spec = manifest["import_specifications"][0]
        self.assertEqual(spec["validation_config_file"],
                         "validation_config.json")
        self.assertTrue(
            os.path.isfile(
                os.path.join(_THIS_DIR, spec["validation_config_file"])))
        for script in spec["scripts"]:
            self.assertTrue(os.path.isfile(os.path.join(_THIS_DIR, script)),
                            msg=f"Missing script: {script}")

    def test_validation_config_rules(self):
        cfg_path = os.path.join(_THIS_DIR, "validation_config.json")
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        rules = {r["rule_id"]: r for r in cfg["rules"]}
        self.assertNotIn("check_deleted_records_percent", rules)
        self.assertIn("check_max_date_consistent", rules)
        self.assertIn("check_latest_date_freshness", rules)

        validator = Validator()
        empty_differ = pd.DataFrame()

        # 1. Valid historical 2012 partition (132 StatVars, MinDate=MaxDate=2012)
        hist_df = pd.DataFrame({
            "StatVar": [f"Count_Student_{i}" for i in range(132)],
            "NumPlaces": [88000] * 132,
            "MinDate": ["2012"] * 132,
            "MaxDate": ["2012"] * 132,
        })
        res_hist_cons = validator.validate_max_date_consistent(
            hist_df, rules["check_max_date_consistent"]["params"])
        self.assertEqual(res_hist_cons.status,
                         ValidationStatus.PASSED,
                         msg=res_hist_cons.message)
        res_hist_sql = validator.validate_sql(
            hist_df,
            empty_differ,
            rules["check_latest_date_freshness"]["params"],
        )
        self.assertEqual(res_hist_sql.status,
                         ValidationStatus.PASSED,
                         msg=res_hist_sql.message)

        # 2. Valid 2024Onwards partition
        onwards_df = pd.DataFrame({
            "StatVar": [f"Count_Student_{i}" for i in range(123)],
            "NumPlaces": [94650] * 123,
            "MinDate": ["2024"] * 123,
            "MaxDate": ["2024"] * 123,
        })
        res_onwards_cons = validator.validate_max_date_consistent(
            onwards_df, rules["check_max_date_consistent"]["params"])
        self.assertEqual(res_onwards_cons.status,
                         ValidationStatus.PASSED,
                         msg=res_onwards_cons.message)
        res_onwards_sql = validator.validate_sql(
            onwards_df,
            empty_differ,
            rules["check_latest_date_freshness"]["params"],
        )
        self.assertEqual(res_onwards_sql.status,
                         ValidationStatus.PASSED,
                         msg=res_onwards_sql.message)

        # 3. Inconsistent MaxDate within a partition must FAIL
        bad_df = onwards_df.copy()
        bad_df.loc[0, "MaxDate"] = "2022"
        res_bad = validator.validate_max_date_consistent(
            bad_df, rules["check_max_date_consistent"]["params"])
        self.assertEqual(res_bad.status, ValidationStatus.FAILED)

        # 4. Empty stats or wrong/stale partition year must FAIL SQL freshness
        empty_stats = pd.DataFrame(
            columns=["StatVar", "NumPlaces", "MinDate", "MaxDate"])
        res_empty = validator.validate_sql(
            empty_stats,
            empty_differ,
            rules["check_latest_date_freshness"]["params"],
        )
        self.assertEqual(res_empty.status, ValidationStatus.FAILED)

        stale_df = pd.DataFrame({
            "StatVar": ["Count_Student_0"],
            "NumPlaces": [90000],
            "MinDate": ["2024"],
            "MaxDate": ["2019"],
        })
        res_stale = validator.validate_sql(
            stale_df,
            empty_differ,
            rules["check_latest_date_freshness"]["params"],
        )
        self.assertEqual(res_stale.status, ValidationStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
