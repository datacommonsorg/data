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
"""Unit tests for CDCWonder_NNDSS_InfectiousWeekly download.py."""

import importlib.util
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

import pandas as pd

_DOWNLOAD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "download.py")
_SPEC = importlib.util.spec_from_file_location("cdc_nndss_weekly_download",
                                               _DOWNLOAD_PATH)
assert _SPEC is not None and _SPEC.loader is not None
download = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(download)


class DownloadTest(unittest.TestCase):

    def test_get_mmwr_week_start_date(self):
        self.assertEqual(download.get_mmwr_week_start_date(2022, 1),
                         "2022-01-02")
        self.assertEqual(download.get_mmwr_week_start_date(2022, 10),
                         "2022-03-06")
        self.assertIsNone(download.get_mmwr_week_start_date(2022, 0))
        self.assertIsNone(download.get_mmwr_week_start_date(2022, 54))
        self.assertIsNone(download.get_mmwr_week_start_date("bad", 1))

    def test_preprocess_csv_filters_and_ny_sum(self):
        rows = [
            {
                "Reporting Area": "US RESIDENTS",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Chlamydia trachomatis infection",
                "Current week": "500.0",
                "Current week, flag": "-",
            },
            {
                "Reporting Area": "NEW YORK",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Campylobacteriosis",
                "Current week": "20.0",
                "Current week, flag": "-",
            },
            {
                "Reporting Area": "NEW YORK CITY",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Campylobacteriosis",
                "Current week": "30.0",
                "Current week, flag": "-",
            },
            {
                "Reporting Area": "ALABAMA",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Campylobacteriosis",
                "Current week": "5.0",
                "Current week, flag": "N",
            },
            {
                "Reporting Area": "ALABAMA",
                "Current MMWR Year": "2021",
                "MMWR WEEK": "52",
                "Label": "Campylobacteriosis",
                "Current week": "12.0",
                "Current week, flag": "-",
            },
            {
                "Reporting Area": "NEW YORK",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Hansen's disease",
                "Current week": "",
                "Current week, flag": "N",
            },
            {
                "Reporting Area": "NEW YORK CITY",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Hansen's disease",
                "Current week": "1.0",
                "Current week, flag": "-",
            },
            {
                "Reporting Area": "NEW YORK",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Anthrax",
                "Current week": "7.0",
                "Current week, flag": "-",
            },
            {
                "Reporting Area": "NEW YORK CITY",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Anthrax",
                "Current week": "",
                "Current week, flag": "-",
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            in_csv = os.path.join(tmpdir, "rows.csv")
            out_csv = os.path.join(tmpdir, "NNDSS_Weekly_Data.csv")
            pd.DataFrame(rows).to_csv(in_csv, index=False)
            out_df = download.preprocess_csv(in_csv, out_csv)

        records = {
            (r["Reporting Area"], r["Label"]): r["Current week"]
            for _, r in out_df.iterrows()
        }
        self.assertEqual(
            records.get(("US RESIDENTS", "Chlamydia trachomatis infection")),
            "500",
        )
        self.assertEqual(records.get(("NEW YORK CITY", "Campylobacteriosis")),
                         "30")
        self.assertEqual(records.get(("NEW YORK", "Campylobacteriosis")), "50")
        self.assertEqual(records.get(("NEW YORK CITY", "Hansen's disease")),
                         "1")
        self.assertNotIn(("NEW YORK", "Hansen's disease"), records)
        self.assertNotIn(("NEW YORK", "Anthrax"), records)
        self.assertEqual(len(records), 4)

    def test_preprocess_csv_header_only_missing_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            in_csv = os.path.join(tmpdir, "rows.csv")
            out_csv = os.path.join(tmpdir, "NNDSS_Weekly_Data.csv")
            with open(in_csv, "w", encoding="utf-8") as f:
                f.write("Reporting Area,Current MMWR Year\n")
            with self.assertRaises(KeyError):
                download.preprocess_csv(in_csv, out_csv)

    def test_normalize_output_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "nndss_weekly_output.csv")
            tmcf_path = os.path.join(tmpdir, "nndss_weekly_output.tmcf")
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write(
                    "observationDate,observationAbout,value,variableMeasured\n"
                    "2024-03-03,country/USA,3,StatVar1\n")
            with open(tmcf_path, "w", encoding="utf-8") as f:
                f.write("Node: E:nndss_weekly_output->E0\n"
                        "observationPeriod: P1W\n"
                        "typeOf: dcs:StatVarObservation\n")
            download.normalize_output_files(output_dir=tmpdir)
            with open(csv_path, "r", encoding="utf-8") as f:
                csv_text = f.read()
            with open(tmcf_path, "r", encoding="utf-8") as f:
                tmcf_text = f.read()
            self.assertIn("observationPeriod", csv_text.splitlines()[0])
            self.assertIn("2024-03-03,country/USA,3,StatVar1,P1W", csv_text)
            self.assertIn(
                "observationPeriod: C:nndss_weekly_output->observationPeriod",
                tmcf_text,
            )

    def _run_download_source_csv(self, fake_download_file):
        fake_mod = types.ModuleType("download_util_script")
        fake_mod.download_file = fake_download_file
        fake_spec = mock.Mock()
        fake_spec.loader = mock.Mock()
        with mock.patch.object(
                download.importlib.util,
                "spec_from_file_location",
                return_value=fake_spec,
        ), mock.patch.object(
                download.importlib.util,
                "module_from_spec",
                return_value=fake_mod,
        ), mock.patch.object(download.time, "sleep"):
            return download.download_source_csv()

    def test_download_source_csv_retries_then_succeeds(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_path = os.path.join(tmpdir, "rows.csv")
            calls = []

            def _fake_download(**kwargs):
                calls.append(kwargs)
                if len(calls) == 1:
                    return False
                with open(raw_path, "wb") as f:
                    f.write(b"x" * (200 * 1024))
                return True

            with mock.patch.object(download, "INPUT_DIR", tmpdir), \
                 mock.patch.object(download, "RAW_FILE", raw_path):
                out = self._run_download_source_csv(_fake_download)

            self.assertEqual(out, raw_path)
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0]["tries"], 1)

    def test_download_source_csv_raises_ioerror_after_retries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_path = os.path.join(tmpdir, "rows.csv")
            calls = []

            def _always_fail(**kwargs):
                calls.append(kwargs)
                return False

            with mock.patch.object(download, "INPUT_DIR", tmpdir), \
                 mock.patch.object(download, "RAW_FILE", raw_path):
                with self.assertRaises(IOError):
                    self._run_download_source_csv(_always_fail)

            self.assertEqual(len(calls), 3)

    def test_download_source_csv_raises_valueerror_on_small_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_path = os.path.join(tmpdir, "rows.csv")

            def _write_tiny(**kwargs):
                del kwargs
                with open(raw_path, "wb") as f:
                    f.write(b"tiny")
                return True

            with mock.patch.object(download, "INPUT_DIR", tmpdir), \
                 mock.patch.object(download, "RAW_FILE", raw_path):
                with self.assertRaises(ValueError):
                    self._run_download_source_csv(_write_tiny)

    def test_download_historical_files_atomic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            downloaded_paths = []

            def _fake_blob(blob_path):
                blob = mock.Mock()

                def _download_to(path):
                    downloaded_paths.append(path)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(f"data:{blob_path}\n")

                blob.download_to_filename.side_effect = _download_to
                return blob

            fake_bucket = mock.Mock()
            fake_bucket.blob.side_effect = _fake_blob
            fake_client = mock.Mock()
            fake_client.bucket.return_value = fake_bucket
            fake_storage = types.SimpleNamespace(Client=mock.Mock(
                return_value=fake_client))
            fake_gcloud = types.SimpleNamespace(storage=fake_storage)

            with mock.patch.dict(
                    sys.modules,
                {
                    "google.cloud": fake_gcloud,
                    "google.cloud.storage": fake_storage,
                },
            ):
                download.download_historical_files(history_dir=tmpdir)

            self.assertTrue(
                all(p.endswith(".tmp") for p in downloaded_paths),
                downloaded_paths,
            )
            for fname in download.HISTORY_FILES:
                dest = os.path.join(tmpdir, fname)
                self.assertTrue(os.path.exists(dest))
                self.assertFalse(os.path.exists(f"{dest}.tmp"))


if __name__ == "__main__":
    unittest.main()
