# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
from pathlib import Path
import sys

from absl import app
from absl import logging
import requests
from retry import retry

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import importlib.util

try:
    from statvar_imports.us_federal_reserve_h15_interest_rates.us_federal_rates import config
except (ImportError, ModuleNotFoundError):
    import config

if not hasattr(config, 'us_fed_urls'):
    _config_path = os.path.join(_SCRIPT_DIR, 'config.py')
    _spec = importlib.util.spec_from_file_location('us_fed_rates_config',
                                                   _config_path)
    config = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(config)

INPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "input_files")

date = datetime.date.today().strftime('%Y-%m-%d')


@retry(exceptions=requests.exceptions.RequestException,
       tries=5,
       delay=10,
       backoff=2)
def retry_method(url, headers=None):
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    if (not response.content or not response.content.lstrip(
            b'\xef\xbb\xbf"').startswith(b"Series Description") or
            response.content.count(b"\n") <= 6):
        logging.warning(
            f"Empty or invalid CSV response ({len(response.content)} bytes) from {url}; retrying..."
        )
        raise requests.exceptions.RequestException(
            f"Received empty or invalid CSV response ({len(response.content)} bytes) from {url}"
        )
    return response


def download_files(us_fed_urls):
    logging.info("Starting download...")
    Path(INPUT_DIR).mkdir(parents=True, exist_ok=True)
    count = 1
    try:
        for url in us_fed_urls:
            response = retry_method(url.format(date))
            input_path = os.path.join(INPUT_DIR, f"us_fed_input_{count}.csv")
            with open(input_path, "wb") as f:
                f.write(response.content)
            count += 1
        logging.info(f"Downloaded file saved to {INPUT_DIR}")
    except requests.exceptions.RequestException as e:
        logging.fatal(f"Failed to download file: {e}")


def main(argv):
    us_fed_urls = config.us_fed_urls
    download_files(us_fed_urls)


if __name__ == "__main__":
    app.run(main)
