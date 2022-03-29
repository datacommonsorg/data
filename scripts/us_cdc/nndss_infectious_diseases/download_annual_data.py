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
Utility to download Nationally Notifiable Infectious Diseases and Conditions, United States: Annual Tables
from 2016-2019
"""
import datetime
import time
import os
import requests
import pandas as pd
from absl import flags, app
from bs4 import BeautifulSoup

_START = 2016
_END = 2019 + 1  #to make the last year inclusive
_TABLE_ID = ['4', '5', '6', '7']
_BASE_URL = "https://wonder.cdc.gov/nndss/"
_TABLE_URL = _BASE_URL + "static/{year}/annual/{year}-table{id}.html"

_FILENAME_TEMPLATE = "mmwr_year_{year}_mmwr_table_{id}"
_BAD_URLS = [
    'https://wonder.cdc.gov/nndss/nndss_weekly_tables_1995_2014.asp?mmwr_year=2007&mmwr_week=13&mmwr_table=1&request=Submit'
]


## same as download_weekly.py
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


## same as download_weekly.py
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


def download_annual_nnds_data_across_years(year_range: str,
                                           output_path: str) -> None:
    """
	"""
    output_path = os.path.join(output_path, './nndss_annual_data')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    for year in year_range:
        for table in _TABLE_ID:
            table_url = _TABLE_URL.format(year=year, id=table)
            filename = _FILENAME_TEMPLATE.format(year=year, id=table)
            extract_table_from_link(table_url, filename, output_path)


def main(_) -> None:
    FLAGS = flags.FLAGS
    flags.DEFINE_string(
        'output_path', './data',
        'Path to the directory where generated files are to be stored.')
    year_range = range(_START, _END)
    download_annual_nnds_data_across_years(year_range, FLAGS.output_path)


if __name__ == '__main__':
    app.run(main)
