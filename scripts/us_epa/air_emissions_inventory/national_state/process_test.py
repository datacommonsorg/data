# Copyright 2022 Google LLC
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
"""
Script to automate the testing for US EPA Air Pollutant Emission Trends
(National and State) process script.
"""
import os
import sys
import tempfile
import unittest
from unittest import mock
import pandas as pd

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_COMMON_PATH = os.path.abspath(os.path.join(_MODULE_DIR, '..'))
sys.path.insert(1, _MODULE_DIR)
sys.path.insert(1, _COMMON_PATH)
# pylint: disable=wrong-import-position
import download
from process import USAirPollutionEmissionTrendsNationalAndState
from common.unitest_common_methods_test import CommonTestClass
# pylint: enable=wrong-import-position


class USAirPollutionEmissionTrendsNationalAndStateTest(
        CommonTestClass.CommonTestCases):
    _import_class = USAirPollutionEmissionTrendsNationalAndState
    _test_module_directory = os.path.dirname(__file__)

    def test_state_emissions_skiprows_zero_and_year_parsing(self):
        """Verifies _state_emissions handles skiprows=0 ('State Trends') and 2/4-digit years."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            xlsx_path = os.path.join(tmp_dir, "state_tier1_test.xlsx")
            sample_df = pd.DataFrame({
                "State FIPS": [1],
                "State": ["AL"],
                "Tier 1 Code": [1],
                "Tier 1 Description": ["Fuel Comb. Elec. Util."],
                "Pollutant": ["CO"],
                "emissions99": [1.5],
                "emissions01": [2.0],
                "emissions2025": [3.25],
            })
            with pd.ExcelWriter(xlsx_path) as writer:
                sample_df.to_excel(writer,
                                   sheet_name="State Trends",
                                   index=False)

            loader = USAirPollutionEmissionTrendsNationalAndState([xlsx_path])
            result_df = loader._state_emissions(xlsx_path)
            raw_df = result_df[result_df["Measurement_Method"] ==
                               "EPA_NationalEmissionInventory"]
            years_map = dict(zip(raw_df["year"], raw_df["observation"]))
            self.assertEqual(years_map, {1999: 1.5, 2001: 2.0, 2025: 3.25})
            self.assertTrue((raw_df["geo_Id"] == "geoId/01").all())

    def test_scrape_and_resolve_download_urls(self):
        """Verifies scrape_epa_trends_urls and resolve_download_urls fallback behavior."""
        sample_html = '''
        <html><body>
          <a href="/system/files/other-files/2026-09/national_tier1_caps_04sep2026.xlsx?ver=1">National</a>
          <a href="https://www.epa.gov/system/files/other-files/2026-09/state_tier1_1990_2025_04sep2026_ktons.xlsx">State</a>
        </body></html>
        '''
        mock_session = mock.MagicMock()
        mock_get_resp = mock.MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.text = sample_html
        mock_session.get.return_value = mock_get_resp

        discovered = download.scrape_epa_trends_urls(session=mock_session)
        self.assertEqual(
            discovered,
            [
                "https://www.epa.gov/system/files/other-files/2026-09/national_tier1_caps_04sep2026.xlsx?ver=1",
                "https://www.epa.gov/system/files/other-files/2026-09/state_tier1_1990_2025_04sep2026_ktons.xlsx",
            ],
        )

        # Simulate stale GCS URLs (404) falling back to scraped URLs (200)
        def side_effect_head(url, **_kwargs):
            resp = mock.MagicMock()
            resp.status_code = 404 if "2025-04" in url else 200
            return resp

        mock_session.head.side_effect = side_effect_head
        stale_urls = [
            "https://www.epa.gov/system/files/other-files/2025-04/national_tier1_caps_21feb2025.xlsx",
            "https://www.epa.gov/system/files/other-files/2025-04/state_tier1_21feb2005_ktons.xlsx",
        ]
        resolved = download.resolve_download_urls(stale_urls,
                                                  session=mock_session)
        self.assertEqual(resolved, discovered)

    def test_clean_download_directory(self):
        """Verifies _clean_download_directory removes stale .xlsx/.tmp files only."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            stale_xlsx = os.path.join(tmp_dir, "old.xlsx")
            stale_tmp = os.path.join(tmp_dir, "partial.xlsx.tmp")
            keep_txt = os.path.join(tmp_dir, "notes.txt")
            for p in (stale_xlsx, stale_tmp, keep_txt):
                with open(p, "w", encoding="utf-8") as f:
                    f.write("test")
            download._clean_download_directory(tmp_dir)
            self.assertFalse(os.path.exists(stale_xlsx))
            self.assertFalse(os.path.exists(stale_tmp))
            self.assertTrue(os.path.exists(keep_txt))
