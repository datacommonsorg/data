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
This Python script downloads the CDC PRAMS datasets from provided URLs,
verifies their contents, and saves them to the input files directory.
"""
import io
import logging
import os
import zipfile
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'curl/8.21.0-rc3',
        'Accept': 'application/pdf,*/*'
    })
    retries = Retry(total=5,
                    backoff_factor=1.0,
                    status_forcelist=[429, 500, 502, 503, 504],
                    raise_on_status=False)
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


def download_file(input_url: list,
                  download_directory: str,
                  overwrite: bool = False) -> None:
    """
    Function to download and extract files provided in input_url list.

    Args:
        input_url (list): List of URLs of the files to be downloaded.
        download_directory (str): Target directory where 'input_files' will be saved.
        overwrite (bool): If True, re-download existing files.

    Returns:
        None
    """
    path = os.path.join(download_directory, 'input_files')
    os.makedirs(path, exist_ok=True)
    session = _get_session()

    for download_file_url in input_url:
        file_name = os.path.basename(download_file_url)
        out_file = os.path.join(path, file_name)

        if not overwrite and os.path.exists(out_file) and os.path.getsize(
                out_file) > 1000:
            logger.info("File already exists, skipping: %s", file_name)
            continue

        logger.info("Downloading: %s", download_file_url)
        try:
            req = session.get(download_file_url, timeout=60)
            req.raise_for_status()
            if len(req.content) < 1000:
                raise ValueError(
                    f"Downloaded content too small ({len(req.content)} bytes) for {download_file_url}"
                )

            if download_file_url.endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(req.content)) as zipfileout:
                    zipfileout.extractall(path)
            else:
                with open(out_file, 'wb') as file:
                    file.write(req.content)
            logger.info("Successfully downloaded: %s (%d bytes)", file_name,
                        len(req.content))
        except Exception as exc:
            logger.error("Failed downloading %s: %s", download_file_url, exc)
            raise
