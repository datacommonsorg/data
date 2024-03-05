# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Class to run the events pipeline stage to download files from a URL."""

import os
import re
import sys
import time

from absl import logging

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), 'util'))

import file_util
import utils

from counters import Counters
from download_util import request_url
from pipeline_stage_runner import StageRunner, register_stage_runner


class DownloadRunner(StageRunner):
    """Class to download data files from URL source."""

    def __init__(self,
                 config_dicts: list = [],
                 state: dict = {},
                 counters=None):
        self.set_up('download', config_dicts, state, counters)

    def run(
        self,
        input_files: list = None,
        config_dict: dict = {},
        counters: Counters = None,
    ) -> list:
        """Returns the list of files downloaded from the URL in the config.

    URLs are downloaded for each time period until the current date.
    """
        # Download data from start_date up to end_date
        # advancing date by the time_period.
        start_date = self.get_config('start_date', '', config_dict)
        yesterday = utils.date_yesterday()
        end_date = self.get_config('end_date', yesterday, config_dict)
        if end_date > yesterday:
            end_date = yesterday
        logging.info(
            f'Running download with start_date: {start_date}, end_date:{end_date}'
        )
        data_files = []
        while start_date and start_date <= end_date:
            # Download data for the start_date
            download_files = self.download_file_with_config(self.get_configs())
            if download_files:
                data_files.extend(download_files)

            # Advance start_date to the next date.
            start_date = utils.date_advance_by_period(
                start_date, self.get_config('time_period', 'P1M', config_dict))
            if start_date:
                self.set_config_dates(start_date=start_date)
        return data_files

    def download_file_with_config(self, config_dict: dict = {}) -> list:
        """Returns list of files downloaded for config."""
        logging.info(f'Downloading data for config: {config_dict}')
        downloaded_files = []
        urls = config_dict.get('url', [])
        if not isinstance(urls, list):
            urls = [urls]
        for url in urls:
            if not url:
                continue
            url_params = config_dict.get('url_params', {})
            filename = self.get_output_filename(config_dict=config_dict)
            if self.should_skip_existing_output(filename):
                logging.info(f'Skipping download for existing file: {filename}')
                continue

            # Download the URL with retries.
            download_content = ''
            retry_count = 0
            retries = config_dict.get('retry_count', 5)
            retry_secs = config_dict.get('retry_interval', 5)
            while not download_content and retry_count < retries:
                download_content = request_url(
                    url,
                    params=url_params,
                    method=config_dict.get('http_method', 'GET'),
                    output=config_dict.get('response_type', 'text'),
                    timeout=config_dict.get('timeout', 60),
                    retries=config_dict.get('retry_count', 3),
                    retry_secs=retry_secs,
                )
                if download_content:
                    # Check if the downloaded content matches the regex.
                    regex = config_dict.get('successful_response_regex', '')
                    if regex:
                        match = re.search(regex, download_content)
                        if not match:
                            download_content = ''
                            retry_count += 1
                            logging.info(
                                f'Downloaded content for {url} does not match {regex}'
                            )
                            if retry_count < retries:
                                logging.info(
                                    f'retrying {url} #{retry_count} after {retry_secs}'
                                )
                                time.sleep(retry_secs)
            if not download_content:
                logging.error(
                    f'Failed to download {url} after {retries} retries')
                return None

            # Save downloaded content to file.
            with file_util.FileIO(filename, mode='w') as file:
                file.write(download_content)
            logging.info(
                f'Downloaded {len(download_content)} bytes from {url} into file:'
                f' {filename}')
            downloaded_files.append(filename)

        return downloaded_files


# Register the DownloadRunner
register_stage_runner('download', DownloadRunner)
