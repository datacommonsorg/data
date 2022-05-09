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
"""Download and webpage scraping utilites

The scraper module uses beautifulsoup to parse the html script of a webpage and
extract the tabular data from the webpage. This module is intended to be used
with a wrapper script.
"""

import requests
from bs4 import BeautifulSoup

_BASE_URL = "https://wonder.cdc.gov/nndss/"

def get_all_links_in_page(page_url:str)->list:
  """
  Given a url, get all href links in the page. This function assumes links are
  table data in the webpage.

  The extracted links are returned as a list
  """
  page = requests.get(page_url)
  soup = BeautifulSoup(page.content, 'html.parser')
  # extract links from table
  list_links = [tag.find('a')['href'] for tag in soup.select("td:has(a)")]
  # prefix the _BASE_URL to the extracted partial links
  list_links = [(_BASE_URL + link) for link in list_links]
  return list_links




