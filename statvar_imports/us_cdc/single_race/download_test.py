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
    """Unit test suite for CDC WONDER Single Race Downloader."""

    def test_parse_year_list_range(self):
        """Tests parsing a range of years string."""
        years = download.parse_year_list("2018-2023")
        self.assertEqual(years,
                         ["2018", "2019", "2020", "2021", "2022", "2023"])

    def test_parse_year_list_comma(self):
        """Tests parsing comma-separated years string."""
        years = download.parse_year_list("2018, 2020, 2022")
        self.assertEqual(years, ["2018", "2020", "2022"])

    def test_parse_year_list_single(self):
        """Tests parsing a single year string."""
        years = download.parse_year_list("2024")
        self.assertEqual(years, ["2024"])

    @mock.patch.object(download.requests, "Session")
    def test_init_session_success(self, mock_session_cls):
        """Tests successful session handshake and parameter extraction."""
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
        """Tests error handling when the initial landing form is missing."""
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
        """Tests constructing query payload with proper groupings and filters."""
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
        """Tests downloading state data that fits within a single query."""
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
        """Tests dynamic partitioning when CDC WONDER row limit is exceeded."""
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
        """Tests preemptive chunking for high-volume states."""
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
        """Tests converting CDC WONDER TSV output to CSV format."""
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
            self.assertEqual(lines[1], ',2018,"Anchorage Borough, AK",02020,20')

    def test_save_tsv_as_csv_empty_raises(self):
        """Tests that saving an empty or header-only TSV raises ValueError."""
        raw_tsv = "Notes\tYear\tCounty\tCounty Code\tDeaths\n---\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            output_csv = os.path.join(temp_dir, "empty_output.csv")
            with self.assertRaisesRegex(ValueError, "No data rows found"):
                download.save_tsv_as_csv(raw_tsv, output_csv)

    def test_is_state_downloaded(self):
        """Tests state download detection across monolithic and chunked files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertFalse(download.is_state_downloaded(temp_dir, "02"))

            # Create empty file
            f = Path(temp_dir) / "UnderlyingCauseofDeath_SingleRace_02.csv"
            f.write_text("")
            self.assertFalse(download.is_state_downloaded(temp_dir, "02"))

            # Create valid monolithic file covering 2018 and 2019
            f.write_text("Header,col1,col2,col3\n" +
                         ",2018,val\n,2019,val\n" * 10)
            self.assertTrue(download.is_state_downloaded(temp_dir, "02"))
            self.assertTrue(
                download.is_state_downloaded(temp_dir, "02", ["2018", "2019"]))
            self.assertFalse(
                download.is_state_downloaded(temp_dir, "02", ["2018", "2020"]))

            # Verify numeric value in another column does not trigger false positive
            f_other_col = (Path(temp_dir) /
                           "UnderlyingCauseofDeath_SingleRace_03.csv")
            f_other_col.write_text("Notes,Year,Deaths\n" + ",2020,2018\n" * 10)
            self.assertFalse(
                download.is_state_downloaded(temp_dir, "03", ["2018"]))
            self.assertTrue(
                download.is_state_downloaded(temp_dir, "03", ["2020"]))

            # Test chunk files
            f.unlink()
            f_chunk = (Path(temp_dir) /
                       "UnderlyingCauseofDeath_SingleRace_02_2018_2019.csv")
            f_chunk.write_text("Header,col1,col2,col3\n" +
                               "val1,val2,val3,val4\n" * 10)
            self.assertTrue(
                download.is_state_downloaded(temp_dir, "02", ["2018", "2019"]))
            self.assertFalse(
                download.is_state_downloaded(temp_dir, "02", ["2018", "2020"]))

    @mock.patch.object(download.time, "sleep")
    @mock.patch.object(download.CdcWonderSingleRaceDownloader, "init_session")
    def test_execute_query_429_backoff(self, mock_init, mock_sleep):
        """Tests rate-limit handling and backoff on HTTP 429."""
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

    @mock.patch.object(download.time, "sleep")
    def test_execute_query_429_final_attempt_fails_fast(self, mock_sleep):
        """Tests that HTTP 429 on the final attempt fails immediately without sleeping."""
        downloader = download.CdcWonderSingleRaceDownloader()
        downloader.action_url = "https://wonder.cdc.gov/test"
        downloader.base_post_data = [("B_1", "test")]

        mock_res_429 = mock.MagicMock()
        mock_res_429.status_code = 429
        mock_res_429.raise_for_status.side_effect = (
            download.requests.HTTPError("429 Client Error"))

        downloader.session.post = mock.MagicMock(return_value=mock_res_429)

        with self.assertRaises(download.requests.HTTPError):
            downloader.execute_query("02", ["2018"], max_retries=1)

        mock_sleep.assert_not_called()

    @mock.patch.object(download.CdcWonderSingleRaceDownloader, "execute_query")
    def test_download_state_network_exception_bubbles(self, mock_query):
        """Tests that network or runtime exceptions bubble up without entering chunking."""
        mock_query.side_effect = download.requests.ConnectionError("Connection aborted")

        downloader = download.CdcWonderSingleRaceDownloader()
        with self.assertRaises(download.requests.ConnectionError):
            downloader.download_state("02", ["2018", "2019"])

    @mock.patch.object(download.CdcWonderSingleRaceDownloader, "init_session")
    @mock.patch.object(download.CdcWonderSingleRaceDownloader, "download_state")
    def test_download_single_race_data_success(self, mock_download_state,
                                               mock_init):
        """Tests orchestration and file writing in download_single_race_data."""
        tsv_content = ("Notes\tYear\tCounty\tCounty Code\tDeaths\n"
                       "\t2018\tAnchorage Borough, AK\t02020\t20\n"
                       "---\n")
        mock_download_state.return_value = [("all", tsv_content)]

        with tempfile.TemporaryDirectory() as temp_dir:
            download.download_single_race_data(
                states=["02"],
                years=["2018"],
                output_dir=temp_dir,
                delay=0.0,
                skip_existing=False,
            )
            expected_file = (
                Path(temp_dir) / "UnderlyingCauseofDeath_SingleRace_02.csv")
            self.assertTrue(expected_file.exists())
            lines = expected_file.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            mock_init.assert_called_once()
            mock_download_state.assert_called_once_with("02", ["2018"])

    @mock.patch.object(download.CdcWonderSingleRaceDownloader, "init_session")
    @mock.patch.object(download.CdcWonderSingleRaceDownloader, "download_state")
    def test_download_single_race_data_purges_preexisting_files(
        self, mock_download_state, mock_init
    ):
        """Tests that stale monolithic or chunked files are purged before new downloads."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create old monolithic file and unrelated state file
            old_monolith = (
                Path(temp_dir) / "UnderlyingCauseofDeath_SingleRace_02.csv")
            old_monolith.write_text("old data")
            other_state = (
                Path(temp_dir) / "UnderlyingCauseofDeath_SingleRace_04.csv")
            other_state.write_text("other state data")

            # Mock new download returning a 2-year chunk
            tsv_chunk = ("Notes\tYear\tCounty\tCounty Code\tDeaths\n"
                         "\t2018\tAnchorage Borough, AK\t02020\t20\n"
                         "---\n")
            mock_download_state.return_value = [("2018_2019", tsv_chunk)]

            download.download_single_race_data(
                states=["02"],
                years=["2018", "2019"],
                output_dir=temp_dir,
                delay=0.0,
                skip_existing=False,
            )

            # Monolith for 02 should be purged, new chunk should exist, and other state intact
            self.assertFalse(old_monolith.exists())
            new_chunk = (
                Path(temp_dir) /
                "UnderlyingCauseofDeath_SingleRace_02_2018_2019.csv")
            self.assertTrue(new_chunk.exists())
            self.assertTrue(other_state.exists())
            mock_init.assert_called_once()

    @mock.patch.object(download.CdcWonderSingleRaceDownloader, "init_session")
    @mock.patch.object(download.CdcWonderSingleRaceDownloader, "download_state")
    def test_download_single_race_data_skip_existing(self, mock_download_state,
                                                     mock_init):
        """Tests skipping states that are already downloaded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create valid file covering 2018
            f = Path(temp_dir) / "UnderlyingCauseofDeath_SingleRace_02.csv"
            f.write_text("Notes,Year,County,County Code,Deaths\n" +
                         ",2018,Anchorage,02020,20\n" * 5)

            download.download_single_race_data(
                states=["02"],
                years=["2018"],
                output_dir=temp_dir,
                delay=0.0,
                skip_existing=True,
            )

            mock_download_state.assert_not_called()
            mock_init.assert_called_once()

    @mock.patch.object(download, "CdcWonderSingleRaceDownloader")
    def test_download_single_race_data_filters_unavailable_years(
        self, mock_downloader_cls
    ):
        """Tests that unpublished future years are filtered out from requested years."""
        mock_instance = mock.MagicMock()
        mock_instance.available_years = ["2018", "2019", "2020", "2024"]
        mock_instance.download_state.return_value = []
        mock_downloader_cls.return_value = mock_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            download.download_single_race_data(
                states=["02"],
                years=["2018", "2024", "2025", "2026"],
                output_dir=temp_dir,
                delay=0.0,
                skip_existing=False,
            )

            # download_state should only be called with published years (2018 and 2024)
            mock_instance.download_state.assert_called_once_with(
                "02", ["2018", "2024"])


if __name__ == "__main__":
    unittest.main()
