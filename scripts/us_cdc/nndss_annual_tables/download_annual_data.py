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
from absl import logging

_BASE_URL = "https://wonder.cdc.gov/nndss/"
_FILENAME_TEMPLATE = "mmwr_year_{year}_mmwr_table_{id}"
_BAD_URLS = []
_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'output_path', './data',
    'Path to the directory where generated files are to be stored.')
# flags.DEFINE_string('start_year', '2016',
#                     'Start year for downloading source files')
# flags.DEFINE_string('end_year', '', 'End year for downloading source files')
# flags.mark_flag_as_required("end_year")


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
                logging.info("Link not working. Skipping table...")
                pass


def extract_table_from_link(table_url: str,
                            filename: str,
                            output_path: str,
                            update: bool = False) -> None:
    """
        Extracts data from a table located at the given URL and saves it to a file.

    Args:
        table_url (str): The URL of the webpage containing the table.
        filename (str): The desired filename for the saved data (e.g., "table_data.csv").
        output_path (str): The directory path where the file will be saved.
        update (bool, optional): If True, appends data to the existing file. 
                                 If False, overwrites the existing file. 
                                 Defaults to False.

    Returns:
        None: The function directly saves the extracted table data to the file.
	"""
    num_tries = 10
    file_path = os.path.join(output_path, f'{filename}.csv')
    if not os.path.exists(file_path) or update:
        logging.info(f"Downloading {table_url}")
        try:
            parse_html_table(table_url, file_path)
            logging.info("Done.")
        except:
            logging.info("Terminated with error. Please check the link.")
            while num_tries > 1:
                num_tries = num_tries - 1
                parse_html_table(table_url, file_path)
                logging.info(
                    f"Attempting download again. Tries remaining {num_tries}")
                time.sleep(1)
        time.sleep(2)
    else:
        logging.info(
            f"Download from {table_url} already exists in {output_path}")
        time.sleep(0.2)


def scrape_table_links_from_page(page_url: str,
                                 output_path: str,
                                 update: bool = False) -> None:
    """
    Scrapes all URLs of tables found on a given webpage.

    Args:
        page_url (str): The URL of the webpage to scrape.
        output_path (str): The path to the file where the scraped links will be saved.
        update (bool, optional): If True, appends new links to the existing file. 
                                 If False, overwrites the existing file. 
                                 Defaults to False.

    Returns:
        None: The function directly saves the scraped links to the output file.

	"""
    try:
        logging.info(f'Scrap Running For URL: {page_url}')
        page = requests.get(page_url)
        soup = BeautifulSoup(page.content, 'html.parser')
        # get link to all tables in the page
        table_link_list = [
            tag.find("a")["href"] for tag in soup.select("td:has(a)")
        ]
        for table_link in table_link_list:
            if table_link.endswith('.html') and 'table' in table_link:
                # skip /nndss/ in the table_link, since it is already part of the _BASE_URL
                table_url = _BASE_URL + table_link[7:]
                # extract year, week, table_id from link
                filename_components = table_link.split('/')[-1].split(
                    '.html')[0].split('-')

                filename = _FILENAME_TEMPLATE.format(
                    year=filename_components[0],
                    id=filename_components[1].split('table')[1])
                logging.info(f"Scrapping completed")
                extract_table_from_link(table_url, filename, output_path,
                                        update)
    except Exception as e:
        logging.fatal(f"Error while scraping {page_url}: {e}")


def download_annual_nnds_data_across_years(year_range: str,
                                           output_path: str) -> None:
    """
    Downloads annual NNDS (National Notifiable Diseases Surveillance System) data for 
    a specified range of years.

    Args:
        year_range (str): A string representing the year range, 
        output_path (str): The directory path where the downloaded data files will be saved.

    Returns:
        None: The function does not return any value. 
              It directly downloads and saves the data.
    """
    try:
        logging.info(f'Downloading starts : Annual NNDS Data')
        output_path = os.path.join(output_path, './nndss_annual_data_all')
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        for year in year_range:
            index_url = f"https://wonder.cdc.gov/nndss/nndss_annual_tables_menu.asp?mmwr_year={year}"
            logging.info(f"Fetching data from {index_url}")
            scrape_table_links_from_page(index_url, output_path, update=False)
            logging.info(f'Download completed : {output_path} from {index_url}')

    except Exception as e:
        logging.fatal(f'Download error for: {index_url}: {e}')


def main(_) -> None:
    start_year1 = "2016"
    end_year1 = datetime.datetime.now().year

    year_range = range(int(start_year1), int(end_year1))
    download_annual_nnds_data_across_years(year_range, _FLAGS.output_path)


if __name__ == '__main__':
    app.run(main)
