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
                "Reporting Area": "US RESIDENTS",
                "Current MMWR Year": "2022",
                "MMWR WEEK": "10",
                "Label": "Gonorrhea",
                "Current week": "6,911",
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
            in_csv = os.path.join(tmpdir, "export.csv")
            out_csv = os.path.join(tmpdir, "nndss_weekly_input.csv")
            pd.DataFrame(rows).to_csv(in_csv, index=False)
            out_df = download.preprocess_csv(in_csv, out_csv)

        records = {
            (r["Reporting Area"], r["Label"]):
                (r["Current week"], r["measurementMethod"])
            for _, r in out_df.iterrows()
        }
        self.assertEqual(
            records.get(("US RESIDENTS", "Chlamydia trachomatis infection")),
            ("500", download.RAW_MEASUREMENT_METHOD),
        )
        self.assertEqual(
            records.get(("US RESIDENTS", "Gonorrhea")),
            ("6911", download.RAW_MEASUREMENT_METHOD),
        )
        self.assertEqual(
            records.get(("NEW YORK CITY", "Campylobacteriosis")),
            ("30", download.RAW_MEASUREMENT_METHOD),
        )
        self.assertEqual(
            records.get(("NEW YORK", "Campylobacteriosis")),
            ("50", download.AGGREGATE_MEASUREMENT_METHOD),
        )
        self.assertEqual(
            records.get(("NEW YORK CITY", "Hansen's disease")),
            ("1", download.RAW_MEASUREMENT_METHOD),
        )
        self.assertNotIn(("NEW YORK", "Hansen's disease"), records)
        self.assertNotIn(("NEW YORK", "Anthrax"), records)
        self.assertEqual(len(records), 5)

    def test_preprocess_csv_header_only_missing_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            in_csv = os.path.join(tmpdir, "export.csv")
            out_csv = os.path.join(tmpdir, "nndss_weekly_input.csv")
            with open(in_csv, "w", encoding="utf-8") as f:
                f.write("Reporting Area,Current MMWR Year\n")
            with self.assertRaises(KeyError):
                download.preprocess_csv(in_csv, out_csv)

    def test_preprocess_csv_raises_on_zero_valid_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            in_csv = os.path.join(tmpdir, "export.csv")
            out_csv = os.path.join(tmpdir, "nndss_weekly_input.csv")
            pd.DataFrame([
                {
                    "Reporting Area": "ALABAMA",
                    "Current MMWR Year": "2021",
                    "MMWR WEEK": "52",
                    "Label": "Campylobacteriosis",
                    "Current week": "12",
                    "Current week, flag": "-",
                },
            ]).to_csv(in_csv, index=False)
            with self.assertRaises(ValueError) as ctx:
                download.preprocess_csv(in_csv, out_csv)
            self.assertIn(in_csv, str(ctx.exception))
            self.assertIn("2022", str(ctx.exception))
            self.assertFalse(os.path.exists(out_csv))

    def test_preprocess_csv_raises_on_malformed_csv_row(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            in_csv = os.path.join(tmpdir, "export.csv")
            out_csv = os.path.join(tmpdir, "nndss_weekly_input.csv")
            with open(in_csv, "w", encoding="utf-8") as f:
                f.write(
                    "Reporting Area,Current MMWR Year,MMWR WEEK,Label,Current week\n"
                    "ALABAMA,2022,10,Anthrax,5\n"
                    "BAD,2022,10,Anthrax,5,EXTRA_COL_1,EXTRA_COL_2\n")
            with self.assertRaises(ValueError) as ctx:
                download.preprocess_csv(in_csv, out_csv)
            self.assertIn("malformed", str(ctx.exception))
            self.assertFalse(os.path.exists(out_csv))

    def test_sample_export_fixture_matches_test_data(self):
        test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "test_data")
        sample_raw = os.path.join(test_data_dir, "sample_export.csv")
        expected_preprocessed = os.path.join(test_data_dir,
                                             "nndss_weekly_input.csv")
        with tempfile.TemporaryDirectory() as tmpdir:
            out_csv = os.path.join(tmpdir, "nndss_weekly_input.csv")
            download.preprocess_csv(sample_raw, out_csv)
            with open(out_csv, "r", encoding="utf-8") as got_f, open(
                    expected_preprocessed, "r", encoding="utf-8") as exp_f:
                self.assertEqual(got_f.read(), exp_f.read())

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
            raw_path = os.path.join(tmpdir, "export.csv")
            calls = []

            def _fake_download(**kwargs):
                calls.append(kwargs)
                if len(calls) == 1:
                    raise OSError("transient socket drop")
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
            raw_path = os.path.join(tmpdir, "export.csv")
            calls = []

            def _always_fail(**kwargs):
                calls.append(kwargs)
                return False

            with mock.patch.object(download, "INPUT_DIR", tmpdir), \
                 mock.patch.object(download, "RAW_FILE", raw_path):
                with self.assertRaises(IOError) as ctx:
                    self._run_download_source_csv(_always_fail)

            self.assertEqual(len(calls), 3)
            self.assertIn(download.SOURCE_URL, str(ctx.exception))
            self.assertIn(raw_path, str(ctx.exception))

    def test_download_source_csv_retries_small_file_then_succeeds(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_path = os.path.join(tmpdir, "export.csv")
            calls = []

            def _tiny_then_valid(**kwargs):
                calls.append(kwargs)
                with open(raw_path, "wb") as f:
                    if len(calls) == 1:
                        f.write(b"tiny")
                    else:
                        f.write(b"x" * (200 * 1024))
                return True

            with mock.patch.object(download, "INPUT_DIR", tmpdir), \
                 mock.patch.object(download, "RAW_FILE", raw_path):
                out = self._run_download_source_csv(_tiny_then_valid)

            self.assertEqual(out, raw_path)
            self.assertEqual(len(calls), 2)

    def test_download_source_csv_raises_valueerror_on_small_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_path = os.path.join(tmpdir, "export.csv")
            calls = []

            def _write_tiny(**kwargs):
                calls.append(kwargs)
                with open(raw_path, "wb") as f:
                    f.write(b"tiny")
                return True

            with mock.patch.object(download, "INPUT_DIR", tmpdir), \
                 mock.patch.object(download, "RAW_FILE", raw_path):
                with self.assertRaises(ValueError) as ctx:
                    self._run_download_source_csv(_write_tiny)

            self.assertEqual(len(calls), 3)
            self.assertFalse(os.path.exists(raw_path))
            self.assertIn(download.SOURCE_URL, str(ctx.exception))
            self.assertIn(raw_path, str(ctx.exception))
            self.assertIn("MB", str(ctx.exception))

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
