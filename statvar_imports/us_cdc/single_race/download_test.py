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
"""Unit tests for CDC WONDER Single Race Downloader."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import sys

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _MODULE_DIR)

try:
    from statvar_imports.us_cdc.single_race import download
except ModuleNotFoundError:
    import download


class DownloadTest(unittest.TestCase):

    def test_parse_year_list_range(self):
        years = download.parse_year_list("2018-2023")
        self.assertEqual(years,
                         ["2018", "2019", "2020", "2021", "2022", "2023"])

    def test_parse_year_list_comma(self):
        years = download.parse_year_list("2018, 2020, 2022")
        self.assertEqual(years, ["2018", "2020", "2022"])

    def test_parse_year_list_single(self):
        years = download.parse_year_list("2024")
        self.assertEqual(years, ["2024"])

    @mock.patch.object(download.requests, "Session")
    def test_init_session_success(self, mock_session_cls):
        mock_session = mock.MagicMock()
        mock_session_cls.return_value = mock_session

        # 1. Landing page response
        mock_res1 = mock.MagicMock()
        mock_res1.text = """
        <html>
            <body>
                <form id="wonderform" action="/controller/datarequest/D158">
                    <input type="hidden" name="stage" value="about" />
                </form>
            </body>
        </html>
        """
        mock_res1.raise_for_status.return_value = None

        # 2. Agreement POST response
        mock_res2 = mock.MagicMock()
        mock_res2.text = """
        <html>
            <body>
                <form id="wonderform" action="/controller/datarequest/D158;jsessionid=TEST1234">
                    <input type="hidden" name="B_1" value="default_b1" />
                    <input type="hidden" name="F_D158.V9" value="*All*" />
                    <input type="hidden" name="dummy" value="123" />
                </form>
            </body>
        </html>
        """
        mock_res2.raise_for_status.return_value = None

        mock_session.get.return_value = mock_res1
        mock_session.post.return_value = mock_res2

        downloader = download.CdcWonderSingleRaceDownloader()
        downloader.init_session()

        self.assertIn("controller/datarequest/D158;jsessionid=TEST1234",
                      downloader.action_url)
        self.assertTrue(len(downloader.base_post_data) > 0)
        self.assertEqual(mock_session.post.call_count, 1)

    @mock.patch.object(download.requests, "Session")
    def test_init_session_missing_form(self, mock_session_cls):
        mock_session = mock.MagicMock()
        mock_session_cls.return_value = mock_session

        mock_res = mock.MagicMock()
        mock_res.text = "<html><body>No form here</body></html>"
        mock_res.raise_for_status.return_value = None
        mock_session.get.return_value = mock_res

        downloader = download.CdcWonderSingleRaceDownloader()
        with self.assertRaisesRegex(ValueError,
                                    "Could not find initial wonderform"):
            downloader.init_session.__wrapped__(downloader)

    def test_build_post_data(self):
        downloader = download.CdcWonderSingleRaceDownloader()
        downloader.base_post_data = [
            ("B_1", "old_val"),
            ("B_2", "old_val"),
            ("B_3", "old_val"),
            ("B_4", "old_val"),
            ("B_5", "old_val"),
            ("F_D158.V9", "*All*"),
            ("F_D158.V1", "*All*"),
            ("other_key", "other_val"),
        ]

        payload = downloader._build_post_data("02", ["2018", "2019"])
        payload_dict = dict(payload)

        self.assertEqual(payload_dict["B_1"], "D158.V1-level1")
        self.assertEqual(payload_dict["B_2"], "D158.V9-level2")
        self.assertEqual(payload_dict["B_3"], "D158.V7")
        self.assertEqual(payload_dict["B_4"], "D158.V42")
        self.assertEqual(payload_dict["B_5"], "D158.V4")
        self.assertEqual(payload_dict["F_D158.V9"], "02")
        self.assertEqual(payload_dict["action-Export Results"],
                         "Export Results")

        year_params = [v for k, v in payload if k == "F_D158.V1"]
        self.assertEqual(year_params, ["2018", "2019"])

    @mock.patch.object(download.CdcWonderSingleRaceDownloader, "execute_query")
    def test_download_state_single_query(self, mock_query):
        tsv_output = ("Notes\tYear\tCounty\tCounty Code\tDeaths\n"
                      "\t2018\tAnchorage Borough, AK\t02020\t20\n")
        mock_query.return_value = tsv_output

        downloader = download.CdcWonderSingleRaceDownloader()
        results = downloader.download_state("02", ["2018", "2019"])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], "all")
        self.assertEqual(results[0][1], tsv_output)
        mock_query.assert_called_once_with("02", ["2018", "2019"])

    @mock.patch.object(download.CdcWonderSingleRaceDownloader, "execute_query")
    def test_download_state_row_limit_partitioning(self, mock_query):
        err_msg = (
            "This request produces 168,754 rows, but 75,000 is the maximum allowed. "
            "Simplify this request, or send a series of smaller ones.")
        tsv_chunk1 = "Notes\tYear\tCounty Code\n\t2018\t06001\n"
        tsv_chunk2 = "Notes\tYear\tCounty Code\n\t2020\t06001\n"
        tsv_chunk3 = "Notes\tYear\tCounty Code\n\t2022\t06001\n"

        # Test dynamic partitioning when 75k limit is hit for a non-preemptive state
        mock_query.side_effect = [err_msg, tsv_chunk1, tsv_chunk2, tsv_chunk3]

        downloader = download.CdcWonderSingleRaceDownloader(delay=0.0)
        results = downloader.download_state(
            "99", ["2018", "2019", "2020", "2021", "2022", "2023"])

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0][0], "2018_2019")
        self.assertEqual(results[1][0], "2020_2021")
        self.assertEqual(results[2][0], "2022_2023")
        self.assertEqual(mock_query.call_count, 4)

    @mock.patch.object(download.CdcWonderSingleRaceDownloader, "execute_query")
    def test_download_state_large_state_preemptive(self, mock_query):
        tsv_chunk1 = "Notes\tYear\tCounty Code\n\t2018\t06001\n"
        tsv_chunk2 = "Notes\tYear\tCounty Code\n\t2020\t06001\n"
        tsv_chunk3 = "Notes\tYear\tCounty Code\n\t2022\t06001\n"
        mock_query.side_effect = [tsv_chunk1, tsv_chunk2, tsv_chunk3]

        downloader = download.CdcWonderSingleRaceDownloader(delay=0.0)
        # California ("06") is in LARGE_STATES, should directly query 3 chunks (no 6-year attempt)
        results = downloader.download_state(
            "06", ["2018", "2019", "2020", "2021", "2022", "2023"])

        self.assertEqual(len(results), 3)
        self.assertEqual(mock_query.call_count, 3)

    def test_save_tsv_as_csv(self):
        raw_tsv = ("Notes\tYear\tCounty\tCounty Code\tDeaths\n"
                   "\t2018\tAnchorage Borough, AK\t02020\t20\n"
                   "\t2018\tFairbanks North Star Borough, AK\t02090\t15\n"
                   "---\n"
                   "Query Parameters:\n"
                   "Caveats:\n")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_csv = os.path.join(temp_dir, "test_output.csv")
            rows = download.save_tsv_as_csv(raw_tsv, output_csv)

            self.assertEqual(rows, 3)
            self.assertTrue(os.path.exists(output_csv))
            lines = Path(output_csv).read_text(encoding="utf-8").splitlines()

            self.assertEqual(len(lines), 3)
            self.assertEqual(lines[0], "Notes,Year,County,County Code,Deaths")
            self.assertEqual(lines[1],
                             ',2018,"Anchorage Borough, AK",02020,20')

    def test_is_state_downloaded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertFalse(download.is_state_downloaded(temp_dir, "02"))

            # Create empty file
            f = Path(temp_dir) / "UnderlyingCauseofDeath_SingleRace_02.csv"
            f.write_text("")
            self.assertFalse(download.is_state_downloaded(temp_dir, "02"))

            # Create valid file > 100 bytes
            f.write_text("Header,col1,col2,col3\n" +
                         "val1,val2,val3,val4\n" * 10)
            self.assertTrue(download.is_state_downloaded(temp_dir, "02"))

    @mock.patch.object(download.time, "sleep")
    @mock.patch.object(download.CdcWonderSingleRaceDownloader, "init_session")
    def test_execute_query_429_backoff(self, mock_init, mock_sleep):
        downloader = download.CdcWonderSingleRaceDownloader()
        downloader.action_url = "https://wonder.cdc.gov/test"
        downloader.base_post_data = [("B_1", "test")]

        mock_res_429 = mock.MagicMock()
        mock_res_429.status_code = 429
        mock_res_429.headers = {"Retry-After": "1"}

        mock_res_200 = mock.MagicMock()
        mock_res_200.status_code = 200
        mock_res_200.text = "Notes\tCounty Code\n"
        mock_res_200.raise_for_status.return_value = None

        downloader.session.post = mock.MagicMock(
            side_effect=[mock_res_429, mock_res_200])

        result = downloader.execute_query("02", ["2018"], max_retries=2)
        self.assertEqual(result, "Notes\tCounty Code\n")
        self.assertEqual(downloader.session.post.call_count, 2)
        mock_sleep.assert_called_with(1)
        mock_init.assert_called_once()


if __name__ == "__main__":
    unittest.main()
