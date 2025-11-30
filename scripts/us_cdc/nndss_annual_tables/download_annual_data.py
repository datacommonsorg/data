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
"""
import datetime
import time
import os
import requests
import pandas as pd
from absl import flags, app
from bs4 import BeautifulSoup

_START = 2016
_END = 2021  #to make the last year inclusive, add +1 to last year. Here 2019 + 1 = 2020

_BASE_URL = "https://wonder.cdc.gov/nndss/"
_FILENAME_TEMPLATE = "mmwr_year_{year}_mmwr_table_{id}"
_BAD_URLS = []


def parse_html_table(table_url: str, file_path: str) -> None:
    if table_url not in _BAD_URLS:
        table_content = requests.get(table_url)
        t_soup = BeautifulSoup(table_content.content, 'html.parser')
        try:
            table_result_set = t_soup.find_all('table')[1]

            df = pd.read_html(table_result_set.prettify())[0]
            # save the file in output path for each file
            df.to_csv(file_path, index=False)
        except IndexError:
            # this case is observed from 2016 onwards
            try:
                table_result_set = t_soup.find_all('table')[0]
                df = pd.read_html(table_result_set.prettify())[0]
                # save the file in output path for each file
                df.to_csv(file_path, index=False)
            except IndexError:
                # This case occurs when downloading https://wonder.cdc.gov/nndss/nndss_reps.asp?mmwr_year=2007&mmwr_week=13&mmwr_table=1&request=Submit
                # The link is unaccessible even from the website and we need to skip this table's download
                print("Link not working. Skipping table...")
                pass


def extract_table_from_link(table_url: str,
                            filename: str,
                            output_path: str,
                            update: bool = False) -> None:
    """
	"""
    num_tries = 10
    file_path = os.path.join(output_path, f'{filename}.csv')
    if not os.path.exists(file_path) or update:
        print(f"Downloading {table_url}", end=" ..... ", flush=True)
        try:
            parse_html_table(table_url, file_path)
            print("Done.", flush=True)
        except:
            print("Terminated with error. Please check the link.", flush=True)
            while num_tries > 1:
                num_tries = num_tries - 1
                parse_html_table(table_url, file_path)
                print(f"Attempting download again. Tries remaining {num_tries}")
                time.sleep(1)
        time.sleep(2)
    else:
        print(f"Download from {table_url} already exists in {output_path}")
        time.sleep(0.2)


def scrape_table_links_from_page(page_url: str,
                                 output_path: str,
                                 update: bool = False) -> None:
    """
	"""
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    # get link to all tables in the page
    table_link_list = [
        tag.find("a")["href"] for tag in soup.select("td:has(a)")
    ]
    for table_link in table_link_list:
        print(table_link)
        if table_link.endswith('.html') and 'table' in table_link:
            # skip /nndss/ in the table_link, since it is already part of the _BASE_URL
            table_url = _BASE_URL + table_link[7:]
            print(table_url)
            # extract year, week, table_id from link
            filename_components = table_link.split('/')[-1].split(
                '.html')[0].split('-')

            filename = _FILENAME_TEMPLATE.format(
                year=filename_components[0],
                id=filename_components[1].split('table')[1])
            extract_table_from_link(table_url, filename, output_path, update)


def download_annual_nnds_data_across_years(year_range: str,
                                           output_path: str) -> None:
    """
	"""
    output_path = os.path.join(output_path, './nndss_annual_data_all')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    for year in year_range:
        index_url = f"https://wonder.cdc.gov/nndss/nndss_annual_tables_menu.asp?mmwr_year={year}"
        print(f"Fetching data from {index_url}")
        scrape_table_links_from_page(index_url, output_path, update=False)


def main(_) -> None:
    FLAGS = flags.FLAGS
    flags.DEFINE_string(
        'output_path', './data',
        'Path to the directory where generated files are to be stored.')
    year_range = range(_START, _END)
    download_annual_nnds_data_across_years(year_range, FLAGS.output_path)


if __name__ == '__main__':
    app.run(main)
