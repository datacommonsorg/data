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

_START = 2006
_END = 2025 #datetime.date.today().year + 1  #to make the last year inclusive

_BASE_URL = "https://wonder.cdc.gov/nndss/"
_WEEKLY_TABLE_2010 = _BASE_URL + "nndss_weekly_tables_menu.asp?mmwr_year={year}&mmwr_week={week}"
_WEEKLY_TABLE_2017 = _BASE_URL + 'nndss_weekly_tables_menu.asp?mmwr_year={year}&mmwr_week={week}'
_FILENAME_TEMPLATE = "mmwr_year_{year}_mmwr_week_{week}_mmwr_table_{id}"
_BAD_URLS = [
    'https://wonder.cdc.gov/nndss/nndss_weekly_tables_1995_2014.asp?mmwr_year=2007&mmwr_week=13&mmwr_table=1&request=Submit'
]


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
        tag.find("a")["href"] for tag in soup.select("tr:has(a)")
    ]
    
    for table_link in table_link_list:
        # Between years 1996 to 2016, select requestMode=Submit
        if 'Submit' in table_link:
            table_url = _BASE_URL + table_link
            # extract filename from link patterns like https://wonder.cdc.gov/nndss/nndss_reps.asp?mmwr_year=1996&mmwr_week=01&mmwr_table=2A&request=Submit
            filename = table_url.split('?')[1].split('&request')[0].replace(
                '=', '_').replace('&', '_')
            print("Submit" , table_url, filename, output_path, update)
            extract_table_from_link(table_url, filename, output_path, update)

        # From year 2017, the base link structure has changed to: https://wonder.cdc.gov/nndss/static/2017/01/2017-01-table1.html
        if table_link.endswith('.html') and 'table' in table_link:
            # skip /nndss/ in the table_link, since it is already part of the _BASE_URL
            table_url = _BASE_URL + table_link[7:]
            # extract year, week, table_id from link
            filename_components = table_link.split('/')[-1].split(
                '.html')[0].split('-')
            filename = _FILENAME_TEMPLATE.format(
                year=filename_components[0],
                week=filename_components[1],
                id=filename_components[2].split('table')[1])
            extract_table_from_link(table_url, filename, output_path, update)


def get_index_url(year, week):
    """
	"""
    if year < 2017:
        return _WEEKLY_TABLE_2010.format(year=year, week=week)
    else:
        return _WEEKLY_TABLE_2017.format(year=year, week=week)


def download_weekly_nnds_data_across_years(year_range: str,
                                           output_path: str) -> None:
    """
	"""
    output_path = os.path.join(output_path, './nndss_weekly_data')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    for year in year_range:
        # year + 1 for the range
        week_range = [str(x).zfill(2) for x in range(1, 53)]
        if year % 4 == 0:
            week_range = [str(x).zfill(2) for x in range(1, 54)]
        for week in week_range:
            index_url = get_index_url(year, week)
            print(f"Fetching data from {index_url}")
            scrape_table_links_from_page(index_url, output_path, update=False)


def update_downloaded_files(year, week, file_path):
    output_path = file_path.spli('/')[:-1]
    output_path = '/'.join(output_path)
    index_url = get_index_url(year, week)
    scrape_table_links_from_page(index_url, output_path, update=True)


def get_next_week(year: str, output_path: str) -> int:
    """
	"""
    all_files_in_dir = os.listdir(output_path)
    files_of_year = [files for files in all_files_in_dir if str(year) in files]
    last_downloaded_file = files_of_year[-1]
    week = last_downloaded_file.split('_mmwr_week_')[1].split('_mmwr_table')[0]
    return int(week) + 1


def download_latest_weekly_nndss_data(year: str, output_path: str) -> None:
    """
	"""
    index_url = "https://wonder.cdc.gov/nndss/nndss_weekly_tables_menu.asp"
    print(f"Fetching data from {index_url}")
    scrape_table_links_from_page(index_url, output_path)


def main(_) -> None:
    FLAGS = flags.FLAGS
    flags.DEFINE_string(
        'output_path', './data',
        'Path to the directory where generated files are to be stored.')
    year_range = range(_START, _END)
    download_weekly_nnds_data_across_years(year_range, FLAGS.output_path)


if __name__ == '__main__':
    app.run(main)
