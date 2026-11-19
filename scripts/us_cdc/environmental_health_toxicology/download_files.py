# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
from pathlib import Path
import shutil
import sys

from absl import app
from absl import flags
from absl import logging
import requests
from retry import retry

_FLAGS = flags.FLAGS


def _define_flags() -> None:
    """Defines command-line flags for this script."""
    flags.DEFINE_string('input_file_path', 'input_files', 'Input files path')
    flags.DEFINE_string(
        'config_file',
        'gs://unresolved_mcf/cdc/environmental/import_configs.json',
        'Config file path')


_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = None
sys.path.append(os.path.join(_MODULE_DIR, '../../../util/'))
import file_util

record_count_query = '?$query=select%20count(*)%20as%20COLUMN_ALIAS_GUARD__count'

_CENSUS_TRACT_PAGE_SIZE = 4_000_000


def _stream_url_to_file(url: str, dest_path: str) -> None:
    """Streams an HTTP GET response to dest_path in 16MB binary chunks."""
    with requests.get(url, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=16 * 1024 * 1024):
                if chunk:
                    f.write(chunk)


def download_files(importname, configs):

    @retry(tries=3, delay=2, backoff=2)
    def download_with_retry(url, input_file_name):
        logging.info(f"Downloading file from URL: {url}")
        filename = os.path.join(_INPUT_FILE_PATH, input_file_name)
        tmp_filename = f"{filename}.tmp"
        try:
            _stream_url_to_file(url, tmp_filename)
            if not os.path.exists(tmp_filename) or os.path.getsize(
                    tmp_filename) <= 0:
                raise IOError(
                    f"Downloaded file {tmp_filename} is empty or missing.")
            shutil.move(tmp_filename, filename)
            logging.info(f"Successfully saved {filename} from URL {url} "
                         f"({os.path.getsize(filename)} bytes)")
        except Exception as e:
            logging.error(
                f"Failed to download {input_file_name} from URL {url}: {e}")
            if os.path.exists(tmp_filename):
                try:
                    os.remove(tmp_filename)
                except OSError:
                    pass
            raise e

    def download_paginated(base_url: str, input_file_name: str,
                           record_count: int) -> None:
        """Downloads large Census Tract datasets in deterministic Socrata pages."""
        filename = os.path.join(_INPUT_FILE_PATH, input_file_name)
        tmp_filename = f"{filename}.tmp"
        page_tmp = f"{tmp_filename}.page"

        @retry(exceptions=(requests.exceptions.RequestException, IOError),
               tries=5,
               delay=2,
               backoff=2)
        def fetch_page(page_url: str, expected_rows: int) -> None:
            try:
                _stream_url_to_file(page_url, page_tmp)
                if not os.path.exists(page_tmp) or os.path.getsize(
                        page_tmp) <= 0:
                    raise IOError(
                        f"Downloaded page {page_tmp} is empty or missing.")
                with open(page_tmp, 'rb') as pf:
                    header = pf.readline()
                    if not header:
                        raise IOError(f"Missing CSV header from {page_url}")
                    row_count = sum(1 for line in pf if line.strip())
                if row_count != expected_rows:
                    raise IOError(f"Incomplete page from {page_url}: expected "
                                  f"{expected_rows} rows, got {row_count}")
            except Exception as e:
                logging.error(f"Failed page download for {input_file_name} "
                              f"from {page_url}: {e}")
                if os.path.exists(page_tmp):
                    try:
                        os.remove(page_tmp)
                    except OSError:
                        pass
                raise

        try:
            with open(tmp_filename, 'wb') as out_f:
                offset = 0
                while offset < record_count:
                    page_limit = min(_CENSUS_TRACT_PAGE_SIZE,
                                     record_count - offset)
                    page_url = (f"{base_url}?$limit={page_limit}"
                                f"&$offset={offset}&$order=:id")
                    logging.info(
                        f"Downloading {input_file_name} rows {offset}.."
                        f"{offset + page_limit} of {record_count} from "
                        f"{page_url}")
                    fetch_page(page_url, page_limit)
                    with open(page_tmp, 'rb') as pf:
                        header = pf.readline()
                        if offset == 0:
                            out_f.write(header)
                        shutil.copyfileobj(pf, out_f, length=16 * 1024 * 1024)
                    os.remove(page_tmp)
                    offset += page_limit
            if not os.path.exists(tmp_filename) or os.path.getsize(
                    tmp_filename) <= 0:
                raise IOError(
                    f"Downloaded file {tmp_filename} is empty or missing.")
            shutil.move(tmp_filename, filename)
            logging.info(
                f"Successfully saved paginated {filename} from {base_url} "
                f"({os.path.getsize(filename)} bytes)")
        except Exception:
            for p in (page_tmp, tmp_filename):
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
            raise

    @retry(tries=3, delay=2, backoff=2)
    def get_record_count_with_retry(count_url):
        logging.info(f"Querying record count from URL: {count_url}")
        resp = requests.get(count_url, timeout=60)
        resp.raise_for_status()
        return json.loads(resp.text)[0]['COLUMN_ALIAS_GUARD__count']

    url_new = None
    import_found = False
    try:
        for config in configs:
            if config["import_name"] == importname:
                import_found = True
                files = config["files"]
                for file_info in files:
                    url_new = file_info["url"]
                    logging.info(f"URL from config file {url_new}")
                    input_file_name = file_info["input_file_name"]
                    logging.info(f"Input File Name {input_file_name}")

                    count_url = url_new.replace('.csv', record_count_query)
                    record_count = int(get_record_count_with_retry(count_url))
                    if record_count <= 0:
                        raise ValueError(
                            f"Invalid record count ({record_count}) returned "
                            f"for URL: {url_new}")
                    logging.info(
                        f"Numbers of records found for the URL {url_new} is "
                        f"{record_count}")
                    # Socrata API endpoints apply a default row limit (1,000)
                    # when $limit is omitted. Passing explicit $limit ensures
                    # the full dataset is downloaded.
                    # TODO: Evaluate incremental refresh by filtering latest
                    # years via Socrata $where queries once baseline is split.
                    if "CensusTract" in importname:
                        download_paginated(url_new, input_file_name,
                                           record_count)
                    else:
                        url_new = f"{url_new}?$limit={record_count}&$offset=0"
                        download_with_retry(url_new, input_file_name)
                    logging.info(
                        f"Successfully downloaded the source data from URL: "
                        f"{url_new}")
        if not import_found:
            raise ValueError(
                f"Import name '{importname}' not found in configuration")

    except Exception as e:
        logging.fatal(f"Error downloading URL {url_new or 'unknown'} - {e}")


def main(argv):
    """Main function to download the csv files."""
    if len(argv) < 2:
        logging.fatal(
            "Missing import name argument. Usage: download_files.py <import_name>"
        )
        return
    global _INPUT_FILE_PATH
    _INPUT_FILE_PATH = os.path.join(_MODULE_DIR, _FLAGS.input_file_path)
    Path(_INPUT_FILE_PATH).mkdir(parents=True, exist_ok=True)
    importname = argv[1]
    logging.info(f'Loading config: {_FLAGS.config_file}')
    with file_util.FileIO(_FLAGS.config_file, 'r') as f:
        config = json.load(f)
    download_files(importname, config)


if __name__ == "__main__":
    _define_flags()
    app.run(main)
