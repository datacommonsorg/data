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
extract the tabular data from the webpage.

This module is intended to be used with a wrapper script.
"""
import os
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

_BASE_URL = "https://wonder.cdc.gov/nndss/"

def _get_all_urls_in_page(page_url:str)->list:
  """
  Given a url, get all href links in the page. This function assumes links are
  table data in the webpage.

  The extracted links are returned as a list
  """
  page = requests.get(page_url)
  soup = BeautifulSoup(page.content, 'html.parser')
  # extract links from table
  list_links = [tag.find('a')['href'] for tag in soup.select("td:has(a)")]
  return list_links


def _construct_complete_urls(list_links:list)->list:
  """
  The href values extracted from the webpage are relative links. To remotely open,
  we will need to prefix the href links with the _BASE_URL.

  While scrapping the webpage, we observe two patterns of url requests which need
  to be considered while constructing the complete urls. This method constructs
  the appropriate URL based on the patterns seen.
  """
  for idx in range(len(list_links)):
    # For links in urls before 2016, select requestMode=Submit for scrapping
    if 'Submit' in list_links[idx]:
      list_links[idx] = _BASE_URL + list_links[idx]
    # For links in recent URLs (post-2016), need to skip a few characters
    if list_links[idx].endswith('.html') and 'table' in list_links[idx]:
      list_links[idx] = _BASE_URL + list_links[idx][7:] #skip nndss/ in url
  return list_links

def get_all_links_in_page(page_url:str)->list:
  """
  Wrapper method that combines _get_all_urls_in_page and _construct_complete_url
  function calls to make the urls that need to be scrapped for processing.
  """
  list_link = _get_all_urls_in_page(page_url)
  return _construct_complete_urls(list_links)

def parse_html_table(table_url:str)->pd.DataFrame:
  """
  Parse the html code from the webpage and extract tabular data to dataframe.
  """
  url_resp = requests.get(table_url)
  soup = BeautifulSoup(url_resp.content, 'html.parser')
  try:
    # attempt exrtacting tabular data to dataframe
    table_in_page = soup.find_all('table')[1]
    df = pd.read_html(table_in_page)[0]
    return df
  except IndexError:
    # The indexError is seen in urls from 2016
    try:
      table_in_page = soup.find_all('table')[0]
      df = pd.read_html(table_in_page)[0]
      return df
    except:
      # The generic exception catches empty responses and url errors
      print(f"Encountered issues while parsing {table_url}")
      pass

def construct_filename(table_url:str)->str:
  # for links before 2016
  if 'Submit' in table_url:
    components = table_url.split('?')[1].split('&request')[0]
    year = components.split('mmwr_year=')[1][:4]
    week = components.split('mmwr_week=')[1][:3]
    table_id = components.split('mmwr_table=')[1].split('.')[0]
    return f"mmwr_year_{year}_mmwr_week_{week}_mmwr_table_{table_id}"
  # for links on and after 2016
  elif table_url.endswith('.html') and 'table' in table_url:
    components = table_url.split('/')[-1].split('.html')[0].split('-')
    # based on length of components, differentiate weekly and annual tables
    if len(components) == 3: # weekly tables
      year = components[0]
      week = components[1]
      table_id = components[2]
      return "mmwr_year_{year}_mmwr_week_{week}_mmwr_table_{table_id}"
    if len(components) == 2: # annual tables
      year = components[0]
      table_id = components[1]
      return f"mmwr_year_{year}_mmwr_table_{table_id}"


def download_and_save(index_url:list, output_dir:str)->None:
  """
  This method requires the top-level url for the statistics to download.

  The logic constructs the complete urls for the files to download and extracts
  the table data from the constructed url which is saved as a csv file in the
  specified output directory.
  """
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)

  constr_links = get_all_links_in_page(index_url)
  for link in constr_links:
    try:
      df = parse_html_table(link)
      filename = construct_filename(link)
      out_path = os.path.join(output_dir, f'{filename}.csv')
      df.to_csv(out_path, index=False)
    except:
      # In the event there was a broken link, notify on stdout
      print(f"Encountered an issue while downloading files from {index_url}.")
      continue
