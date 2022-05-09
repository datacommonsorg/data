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
#
"""Tests for scraper."""

import unittest
import scraper

PAGE_URL = "https://wonder.cdc.gov/nndss/nndss_weekly_tables_menu.asp?&mmwr_year=2022&mmwr_week=17"

class ScraperTest(unittest.TestCase):

  def test_get_links_from_page(self):
    link_list = scraper.get_all_links_in_page(PAGE_URL)
    print(link_list)
    pass


if __name__ == '__main__':
  unittest.main()
