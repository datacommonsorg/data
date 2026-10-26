# Copyright 2024 Google LLC
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
This script runs
all the national state and
county python script and generate
four output CSV, MCF and TMCF.
"""

import os
import json
import sys
from absl import app
from absl import flags
import requests
import shutil
import time
from datetime import datetime as dt
from absl import logging
import pandas as pd

import io
from requests.adapters import HTTPAdapter
from retry import retry
from urllib3.util.retry import Retry

if __name__ == '__main__':
    sys.modules.setdefault('preprocess', sys.modules['__main__'])

if 'mode' not in flags.FLAGS:
    flags.DEFINE_string('mode', '', 'Options: download or process')

_MODULE_DIR = os.path.dirname(__file__)
_LAST_FETCHED_URL = (None, None)


def _create_retry_session(retries=5, backoff_factor=2):
    """Creates a requests.Session with automatic retry on transient HTTP errors."""
    session = requests.Session()
    session.headers.update({
        'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) DataCommonsImport/1.0 (https://datacommons.org)',
        'Accept':
            '*/*',
    })
    retry_strategy = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504, 520],
        allowed_methods=['HEAD', 'GET'],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


def _is_html_response(response_or_content_type, first_bytes=b''):
    """Returns True if the response headers or body indicate an HTML/WAF error page."""
    if hasattr(response_or_content_type, 'headers'):
        content_type = response_or_content_type.headers.get('Content-Type', '')
    else:
        content_type = str(response_or_content_type or '')
    if 'html' in content_type.lower():
        return True
    if first_bytes:
        head = first_bytes[:512].lstrip().lower()
        if (head.startswith(b'<html') or head.startswith(b'<!doctype html') or
                b'<title>request rejected</title>' in head or
                b'the requested url was rejected' in head):
            return True
    return False


@retry(exceptions=(requests.exceptions.RequestException, ValueError),
       tries=3,
       delay=5,
       backoff=2)
def _head_with_html_retry(session, url, timeout=30):
    """Performs a HEAD request with retry when the server returns HTML for a non-HTML URL."""
    response = session.head(url, timeout=timeout, allow_redirects=True)
    content_type = response.headers.get('Content-Type', '').lower()
    if (response.status_code == 200 and 'html' in content_type and
            not url.lower().endswith(('.html', '.htm'))):
        raise ValueError(
            f'Server returned HTML (Content-Type: {content_type}) for non-HTML URL: {url}'
        )
    return response


@retry(exceptions=(requests.exceptions.RequestException, ValueError),
       tries=5,
       delay=5,
       backoff=2)
def _fetch_url_bytes(url: str) -> bytes:
    """Fetches URL content with retries and WAF/HTML rejection."""
    session = _create_retry_session()
    try:
        with session.get(url, timeout=60) as response:
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')
            content = response.content
            if not content:
                raise ValueError(f'Downloaded empty response from URL: {url}')
            if (not url.lower().endswith(('.html', '.htm')) and
                    _is_html_response(content_type, content[:512])):
                raise ValueError(
                    f'Server returned HTML/WAF response (Content-Type: {content_type}) for non-HTML URL: {url}'
                )
            return content
    finally:
        session.close()


def load_url_or_path(url_or_path: str):
    """Returns a BytesIO buffer for HTTP/HTTPS URLs (with retries, WAF checks, and single-URL cache) or the local path."""
    global _LAST_FETCHED_URL
    if isinstance(url_or_path, str):
        if url_or_path.lower().startswith(('http://', 'https://')):
            if _LAST_FETCHED_URL[0] == url_or_path and _LAST_FETCHED_URL[
                    1] is not None:
                return io.BytesIO(_LAST_FETCHED_URL[1])
            content = _fetch_url_bytes(url_or_path)
            _LAST_FETCHED_URL = (url_or_path, content)
            return io.BytesIO(content)
        if not os.path.isabs(url_or_path) and not os.path.exists(url_or_path):
            candidate = os.path.join(_MODULE_DIR, url_or_path)
            if os.path.exists(candidate):
                return candidate
    return url_or_path


from national.national_1900_1970 import process_national_1900_1970
from national.national_1980_1990 import process_national_1980_1990
from national.national_1990_2000 import process_national_1990_2000
from national.national_2000_2010 import process_national_2000_2010
from national.national_2010_2020 import process_national_2010_2020
from national.national_2020_2022 import process_national_2020_2022
from national.national_2020_2029 import process_national_2020_2029
from state.state_1970_1979 import process_state_1970_1979
from state.state_1980_1990 import process_state_1980_1990
from state.state_1990_2000 import process_state_1990_2000
from state.state_2000_2010 import process_state_2000_2010
from state.state_2010_2020 import process_state_2010_2020
from state.state_2020_2022 import process_state_2020_2022
from state.state_2020_2029 import process_state_2020_2029
from county.county_1970_1979 import process_county_1970_1979
from county.county_1980_1989 import process_county_1980_1989
from county.county_1990_2000 import process_county_1990_2000
from county.county_2000_2009 import process_county_2000_2009
from county.county_2010_2020 import process_county_2010_2020
from county.county_2020_2022 import process_county_2020_2022
from county.county_2020_2029 import process_county_2020_2029
from postprocess import create_single_csv, generate_mcf, generate_tmcf
from common import (
    Outputfiles,
    _OUTPUTFINAL,
    _OUTPUTINTERMEDIATE,
    __INPUTFILES,
)

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "config_files"
if 'input_path' not in flags.FLAGS:
    flags.DEFINE_string("input_path", default_input_path,
                        "Import Data File's List")
_INPUT_FILE_PATH = os.path.join(_MODULE_DIR, 'output_files/intermediate')
_FILES_TO_DOWNLOAD = None
_BASELINE_YEAR = 2025


def _get_urls(json_file_path, key, test):
    """
    Extracting dataset urls from json_config_files.

    Args:
        json_file_path: path to config json files.
        key: provies the key for json file.

    Returns:
        urls: dataset url.
    """
    url_json = None
    with open(json_file_path, encoding="UTF-8") as file:
        url_json = json.load(file)
    urls = url_json[key]

    if test:
        if (type(urls) == str):
            urls = os.path.join(_MODULE_DIR, urls)
        elif (type(urls) == list):
            urls = [os.path.join(_MODULE_DIR, url) for url in urls]

    return urls


def add_future_year_urls():
    global _FILES_TO_DOWNLOAD
    _FILES_TO_DOWNLOAD = []
    urls_to_scan = [
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/counties/asrh/cc-est{YEAR}-alldata.csv"
    ]
    # This method will generate URLs for the years 2025 to 2029
    session = _create_retry_session()
    try:
        for url in urls_to_scan:
            url_found = False
            for future_year in range(2030, _BASELINE_YEAR - 1, -1):
                url_to_check = url.format(YEAR=future_year)
                try:
                    check_url = _head_with_html_retry(session, url_to_check)
                    if check_url.status_code == 200:
                        _FILES_TO_DOWNLOAD.append(
                            {"download_path": url_to_check})
                        url_found = True
                        break
                except Exception as e:
                    logging.warning(
                        f"URL is not accessible {url_to_check}: {e}")

            if not url_found:
                fallback_url = url.format(YEAR=_BASELINE_YEAR)
                logging.warning(
                    f"All HEAD probes failed for {url}; falling back to baseline year {_BASELINE_YEAR}: {fallback_url}"
                )
                _FILES_TO_DOWNLOAD.append({"download_path": fallback_url})
    finally:
        session.close()


def downloadFiles(config_files: list, test=False):
    #This method is use to download the file from URL
    '''
    arguments
        config_files: List of config file
        test=False
    '''
    os.makedirs(os.path.join(_MODULE_DIR, _OUTPUTFINAL), exist_ok=True)
    os.makedirs(os.path.join(_MODULE_DIR, _OUTPUTINTERMEDIATE), exist_ok=True)
    os.makedirs(os.path.join(_MODULE_DIR, __INPUTFILES), exist_ok=True)
    try:
        for config_file in config_files:
            try:
                files = _get_urls(config_file, "urls", test)
                if "national_1980_1990.json" in config_file:
                    process_national_1980_1990(files)
                elif "national_1900_1970.json" in config_file:
                    process_national_1900_1970(files)
                elif "national_1990_2000.json" in config_file:
                    process_national_1990_2000(files)
                elif "national_2000_2010.json" in config_file:
                    process_national_2000_2010(files)
                elif "national_2010_2020.json" in config_file:
                    process_national_2010_2020(files)
                #Added for data refresh from 2020-2023
                elif "national_2020_2022.json" in config_file:
                    process_national_2020_2022(files)
                elif "state_1970_1979.json" in config_file:
                    process_state_1970_1979(files)
                elif "state_1980_1990.json" in config_file:
                    process_state_1980_1990(files)
                elif "state_1990_2000.json" in config_file:
                    process_state_1990_2000(files)
                elif "state_2000_2010.json" in config_file:
                    process_state_2000_2010(files)
                elif "state_2010_2020.json" in config_file:
                    process_state_2010_2020(files)
                #Added for 2020-2023 part of data refresh
                elif "state_2020_2022.json" in config_file:
                    process_state_2020_2022(files)
                elif "county_1970_1979.json" in config_file:
                    process_county_1970_1979(files)
                elif "county_1980_1989.json" in config_file:
                    process_county_1980_1989(files)
                elif "county_1990_2000.json" in config_file:
                    process_county_1990_2000(files)
                elif "county_2000_2009.json" in config_file:
                    process_county_2000_2009(files)
                elif "county_2010_2020.json" in config_file:
                    process_county_2010_2020(files)
                #added for 2020-2022 data refresh
                elif "county_2020_2022.json" in config_file:
                    process_county_2020_2022(files)
            except Exception as e:
                logging.fatal(f"Failed to process {config_file}: {e}")

        if not test:
            global _FILES_TO_DOWNLOAD
            for file in _FILES_TO_DOWNLOAD or []:
                url = file['download_path']
                #Calling 2023 onwards methods
                try:
                    process_national_2020_2029(url)
                except Exception as e:
                    logging.fatal(
                        f"Failed to process national 2020-2029 for {url}: {e}")
                try:
                    process_county_2020_2029(url)
                except Exception as e:
                    logging.fatal(
                        f"Failed to process county 2020-2029 for {url}: {e}")
                try:
                    process_state_2020_2029(url)
                except Exception as e:
                    logging.fatal(
                        f"Failed to process state 2020-2029 for {url}: {e}")
    except Exception as e:
        logging.fatal(f"There is an error while downloading the files {e}")
    finally:
        global _LAST_FETCHED_URL
        _LAST_FETCHED_URL = (None, None)


def process(config_files: list, test=False):
    """
    This method calls the required methods
    and generate final csv, mcf and tmcf.

    Args:
        config_files (List) : list of json files containing dataset url.
        test=False

    Returns:
        None.
    """
    if test:
        downloadFiles(config_files, test=True)

    input_files = []
    # Walk through the directory and its subdirectories
    for root, dirs, files in os.walk(_INPUT_FILE_PATH):
        for file in sorted(files):  # Sort the files alphabetically
            file_path = os.path.join(root, file)
            input_files.append(file_path)
    # Now `input_files` contains paths to all the files in `_INPUT_FILE_PATH` and its subdirectories

    processed_count = len(input_files)
    logging.info(f"No of files to be processed {processed_count}")
    # list of national output files before year 2000
    national_before_2000 = [
        "nationals_result_1900_1959.csv", "nationals_result_1960_1979.csv",
        "nationals_result_1980_1990.csv", "nationals_result_1990_2000.csv"
    ]

    # list of state and county output files before year 2000
    state_county_before_2000 = [
        "state_result_1970_1979.csv", "state_result_1980_1990.csv",
        "state_result_1990_2000.csv", "county_result_1970_1979.csv",
        "county_result_1980_1989.csv", "county_result_1990_2000.csv"
    ]

    # list of state and county output files after year 2000
    state_county_after_2000 = [
        "state_result_2000_2010.csv", "state_result_2010_2020.csv",
        "county_result_2000_2009.csv", "county_result_2010_2020.csv"
    ]
    if not test:
        state_county_after_2000.extend([
            "state_result_2020_2022.csv", "state_result_2020_2029.csv",
            "county_result_2020_2022.csv", "county_result_2020_2029.csv"
        ])

    # list of national output files after year 2000
    national_after_2000 = [
        "nationals_result_2000_2010.csv", "nationals_result_2010_2020.csv"
    ]
    if not test:
        national_after_2000.extend([
            "nationals_result_2020_2022.csv", "nationals_result_2020_2029.csv"
        ])

    output_files_names = {
        Outputfiles.NationalBefore2000.value: national_before_2000,
        Outputfiles.StateCountyBefore2000.value: state_county_before_2000,
        Outputfiles.StateCountyAfter2000.value: state_county_after_2000,
        Outputfiles.NationalAfter2000.value: national_after_2000
    }
    try:
        column_names = create_single_csv(output_files_names)
        for flag, columns in column_names.items():
            generate_mcf(columns, flag)
            generate_tmcf(columns, flag)
    except Exception as e:
        logging.fatal(f"Error while generating csv,mcf and tmcf files{e}")


def main(_):
    mode = FLAGS.mode
    """
    Creating and processing input files
    """
    input_path = FLAGS.input_path
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]

    if mode == "" or mode == "download":
        # download & process
        add_future_year_urls()
        downloadFiles(ip_files)

    if mode == "" or mode == "process":
        process(ip_files)


if __name__ == "__main__":
    app.run(main)
