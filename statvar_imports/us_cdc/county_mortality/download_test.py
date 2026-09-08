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

"""Unit tests for CDC WONDER County Mortality Downloader."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import requests

import download


class DownloadTest(unittest.TestCase):

    def test_parse_year_list_range(self):
        years = download.parse_year_list("2018-2024")
        self.assertEqual(years, ["2018", "2019", "2020", "2021", "2022", "2023", "2024"])

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

        downloader = download.CdcWonderCountyMortalityDownloader()
        downloader.init_session()

        self.assertIn("controller/datarequest/D158;jsessionid=TEST1234", downloader.action_url)
        self.assertTrue(len(downloader.base_post_data) > 0)
        self.assertEqual(mock_session.post.call_count, 1)

    def test_build_post_data(self):
        downloader = download.CdcWonderCountyMortalityDownloader()
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

        payload = downloader._build_post_data("10", ["2018", "2019"])
        payload_dict = dict(payload)

        # Check that County and ICD-10 113 Cause List are selected, while B_4/B_5 are *None*
        self.assertEqual(payload_dict["B_1"], "D158.V1-level1")
        self.assertEqual(payload_dict["B_2"], "D158.V9-level2")
        self.assertEqual(payload_dict["B_3"], "D158.V4")
        self.assertEqual(payload_dict["B_4"], "*None*")
        self.assertEqual(payload_dict["B_5"], "*None*")
        self.assertEqual(payload_dict["F_D158.V9"], "10")
        self.assertEqual(payload_dict["action-Export Results"], "Export Results")

        year_params = [v for k, v in payload if k == "F_D158.V1"]
        self.assertEqual(year_params, ["2018", "2019"])

    @mock.patch.object(download.CdcWonderCountyMortalityDownloader, "execute_query")
    def test_download_state_single_query(self, mock_query):
        tsv_output = (
            "Notes\tYear\tCounty\tCounty Code\tICD-10 113 Cause List\tDeaths\n"
            "\t2018\tKent County, DE\t10001\tSepticemia\t20\n"
        )
        mock_query.return_value = tsv_output

        downloader = download.CdcWonderCountyMortalityDownloader()
        results = downloader.download_state("10", ["2018", "2019"])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], "all")
        self.assertEqual(results[0][1], tsv_output)
        mock_query.assert_called_once_with("10", ["2018", "2019"])

    def test_save_tsv_as_csv(self):
        raw_tsv = (
            "Notes\tYear\tCounty\tCounty Code\tDeaths\n"
            "\t2018\tKent County, DE\t10001\t20\n"
            "---\n"
            "Query Parameters:\n"
            "Caveats:\n"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_csv = os.path.join(temp_dir, "test_output.csv")
            rows = download.save_tsv_as_csv(raw_tsv, output_csv)

            self.assertEqual(rows, 2)
            self.assertTrue(os.path.exists(output_csv))
            lines = Path(output_csv).read_text(encoding="utf-8").splitlines()

            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0], "Notes,Year,County,County Code,Deaths")
            self.assertEqual(lines[1], ',2018,"Kent County, DE",10001,20')

    def test_is_state_downloaded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertFalse(download.is_state_downloaded(temp_dir, "10"))

            # Create empty file
            f = Path(temp_dir) / "UnderlyingCauseofDeath_County_10.csv"
            f.write_text("")
            self.assertFalse(download.is_state_downloaded(temp_dir, "10"))

            # Create file with only 2024 (missing 2018 initial year) -> should be False
            f.write_text("Header,col1,col2,col3\n" + ",2024,val2,val3\n" * 10)
            self.assertFalse(download.is_state_downloaded(temp_dir, "10", years=["2018", "2024"]))

            # Create file with both initial (2018) and latest (2024) -> should be True
            f.write_text("Header,col1,col2,col3\n" + ",2018,val2,val3\n" * 5 + ",2024,val2,val3\n" * 5)
            self.assertTrue(download.is_state_downloaded(temp_dir, "10", years=["2018", "2024"]))
            self.assertFalse(download.is_state_downloaded(temp_dir, "10", years=["2018", "2025"]))

            # Test partitioned chunk files
            f.unlink()
            chunk_2024 = Path(temp_dir) / "UnderlyingCauseofDeath_County_10_2024.csv"
            chunk_2024.write_text("Header,col1\n" + "val1,val2\n" * 10)
            # Only latest chunk present -> should be False
            self.assertFalse(download.is_state_downloaded(temp_dir, "10", years=["2018", "2024"]))

            # Both initial chunk and latest chunk present -> should be True for 2018, 2024
            chunk_2018 = Path(temp_dir) / "UnderlyingCauseofDeath_County_10_2018_2019.csv"
            chunk_2018.write_text("Header,col1\n" + "val1,val2\n" * 10)
            self.assertTrue(download.is_state_downloaded(temp_dir, "10", years=["2018", "2024"]))

            # If intermediate year (e.g. 2021) is requested but missing chunk -> should be False
            self.assertFalse(download.is_state_downloaded(temp_dir, "10", years=["2018", "2021", "2024"]))

            # Add intermediate chunk covering 2021 -> should now be True
            chunk_2020 = Path(temp_dir) / "UnderlyingCauseofDeath_County_10_2020_2021.csv"
            chunk_2020.write_text("Header,col1\n" + "val1,val2\n" * 10)
            self.assertTrue(download.is_state_downloaded(temp_dir, "10", years=["2018", "2021", "2024"]))

    @mock.patch.object(download.time, "sleep")
    @mock.patch.object(download.CdcWonderCountyMortalityDownloader, "init_session")
    def test_execute_query_429_backoff(self, mock_init, mock_sleep):
        downloader = download.CdcWonderCountyMortalityDownloader()
        downloader.action_url = "https://wonder.cdc.gov/test"
        downloader.base_post_data = [("B_1", "test")]

        mock_res_429 = mock.MagicMock()
        mock_res_429.status_code = 429
        mock_res_429.headers = {"Retry-After": "1"}

        mock_res_200 = mock.MagicMock()
        mock_res_200.status_code = 200
        mock_res_200.text = "Notes\tCounty Code\n"
        mock_res_200.raise_for_status.return_value = None

        downloader.session.post = mock.MagicMock(side_effect=[mock_res_429, mock_res_200])

        result = downloader.execute_query("10", ["2018"], max_retries=2)
        self.assertEqual(result, "Notes\tCounty Code\n")
        self.assertEqual(downloader.session.post.call_count, 2)
        mock_sleep.assert_called_with(1)
        mock_init.assert_called_once()

    @mock.patch.object(download.time, "sleep")
    @mock.patch.object(download.CdcWonderCountyMortalityDownloader, "execute_query")
    def test_download_state_timeout_fallback_to_single_years(self, mock_query, mock_sleep):
        def query_side_effect(state_fips, years, **kwargs):
            if len(years) > 1:
                raise requests.exceptions.HTTPError("504 Server Error: Gateway Time-out")
            return f"Notes\tYear\tCounty Code\n\t{years[0]}\t01001\n"

        mock_query.side_effect = query_side_effect
        downloader = download.CdcWonderCountyMortalityDownloader()
        results = downloader.download_state("01", ["2018", "2019", "2020"])

        self.assertEqual(len(results), 3)
        self.assertEqual([r[0] for r in results], ["2018", "2019", "2020"])

    @mock.patch.object(download.CdcWonderCountyMortalityDownloader, "init_session")
    @mock.patch.object(download.CdcWonderCountyMortalityDownloader, "download_state")
    def test_download_county_mortality_data_continues_and_raises_on_failure(
        self, mock_download, mock_init
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            def side_effect(state_fips, years):
                if state_fips == "10":
                    raise requests.exceptions.ConnectionError("Connection dropped")
                return [("all", "Notes\tCounty Code\tDeaths\n\t11001\t50\n")]

            mock_download.side_effect = side_effect

            with self.assertRaises(RuntimeError) as ctx:
                download.download_county_mortality_data(
                    states=["10", "11"],
                    years=["2024"],
                    output_dir=temp_dir,
                    skip_existing=False,
                )

            # Assert error message contains the failed state name
            self.assertIn("Delaware", str(ctx.exception))
            # Assert state 11 was still attempted and saved despite state 10 failure
            state_11_csv = Path(temp_dir) / "UnderlyingCauseofDeath_County_11.csv"
            self.assertTrue(state_11_csv.exists())


if __name__ == "__main__":
    unittest.main()
