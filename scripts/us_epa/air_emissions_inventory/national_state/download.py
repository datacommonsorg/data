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
This Python Script downloads the EPA files, into the input_files folder to be 
made available for further processing.
"""

import os
import json
import re
import urllib.parse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from google.cloud import storage  # For GCS integration
from absl import flags, app, logging  # Use absl for flag handling

# Define flags
_FLAGS = flags.FLAGS
flags.DEFINE_string('config_path', '',
                    'Path to the configuration file in the GCS bucket.')

# EPA Air Pollutant Emissions Trends Data provenance page
EPA_TRENDS_PAGE_URL = ("https://www.epa.gov/air-emissions-inventories/"
                       "air-pollutant-emissions-trends-data")

# Download path for files
_DOWNLOAD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'input_files')

_HTTP_TIMEOUT_SECONDS = 60
_DEFAULT_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
}


def _create_http_session() -> requests.Session:
    """Creates an HTTP session with retry and exponential backoff."""
    session = requests.Session()
    session.headers.update(_DEFAULT_HEADERS)
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def check_url_status(url: str, session: requests.Session = None) -> bool:
    """
    Check if the given URL is reachable and log URL info.

    Args:
        url (str): The URL to check.
        session (requests.Session, optional): HTTP session to reuse.

    Returns:
        bool: True if the URL is reachable (status code 200), False otherwise.
    """
    own_session = session is None
    if own_session:
        session = _create_http_session()
    try:
        logging.info(f"Checking URL status: {url}")
        response = session.head(url,
                                allow_redirects=True,
                                timeout=_HTTP_TIMEOUT_SECONDS)
        status_code = response.status_code
        response.close()
        if status_code in (403, 405):
            with session.get(url, stream=True,
                             timeout=_HTTP_TIMEOUT_SECONDS) as get_response:
                status_code = get_response.status_code
        if status_code == 200:
            logging.info(f"URL {url} is reachable. Status code: {status_code}")
            return True
        logging.warning(
            f"URL {url} returned non-200 status code: {status_code}")
        return False
    except Exception as e:
        logging.warning(f"Failed to reach URL {url}. Details: {e}")
        return False
    finally:
        if own_session:
            session.close()


def scrape_epa_trends_urls(session: requests.Session = None) -> list:
    """
    Scrapes the EPA Air Pollutant Emissions Trends Data page for the current
    National Tier 1 CAPS and State Tier 1 CAPS .xlsx download URLs.

    Args:
        session (requests.Session, optional): HTTP session to reuse.

    Returns:
        list: Discovered [national_xlsx_url, state_xlsx_url], or empty list.
    """
    own_session = session is None
    if own_session:
        session = _create_http_session()
    try:
        logging.info(
            f"Discovering latest .xlsx URLs via GET: {EPA_TRENDS_PAGE_URL}")
        response = session.get(EPA_TRENDS_PAGE_URL,
                               timeout=_HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        html = response.text

        hrefs = re.findall(r'href=["\']([^"\']+\.xlsx(?:\?[^"\']*)?)["\']',
                           html, re.IGNORECASE)
        national_url = None
        state_url = None
        for href in hrefs:
            full_url = urllib.parse.urljoin(EPA_TRENDS_PAGE_URL, href)
            filename = os.path.basename(
                urllib.parse.urlsplit(full_url).path).lower()
            if not national_url and re.match(r"^national_tier1_caps.*\.xlsx$",
                                             filename):
                national_url = full_url
            elif not state_url and re.match(r"^state_tier1.*ktons\.xlsx$",
                                            filename):
                state_url = full_url

        discovered = [u for u in (national_url, state_url) if u]
        if len(discovered) == 2:
            logging.info(f"Discovered current EPA trend URLs: {discovered}")
            return discovered
        logging.warning(f"Incomplete URL discovery from {EPA_TRENDS_PAGE_URL}; "
                        f"expected 2 URLs, found: {discovered}")
        return []
    except Exception as e:
        logging.warning(
            f"Failed to scrape EPA trends page {EPA_TRENDS_PAGE_URL}. "
            f"Details: {e}")
        return []
    finally:
        if own_session:
            session.close()


def parse_gcs_path(full_path: str) -> tuple:
    """
    Splits a full GCS path into the bucket name and object path.

    Args:
        full_path (str): GCS path in the form 'bucket_name/path/to/file'.

    Returns:
        tuple: (bucket_name, object_path)
    """
    if '/' not in full_path:
        raise ValueError(f"Invalid GCS path format: {full_path}")
    bucket_name, object_path = full_path.split('/', 1)
    return bucket_name, object_path


def read_config_from_gcs(bucket_name: str, config_path: str) -> list:
    """
    Reads a configuration file from GCS and parses the download URLs.

    Args:
        bucket_name (str): GCS bucket name.
        config_path (str): Path to the config file inside the bucket.

    Returns:
        list: A list of download URLs.
    """
    try:
        client = storage.Client()
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(config_path)
        config_data = json.loads(blob.download_as_text())
        logging.info(f"Successfully read configuration from GCS: {config_path}")

        urls = [
            entry["download_path"]
            for entry in config_data
            if "download_path" in entry
        ]
        return urls
    except Exception as e:
        logging.warning(
            f"Failed to read configuration file from GCS. Details: {e}")
        return []


def resolve_download_urls(config_urls: list,
                          session: requests.Session = None) -> list:
    """
    Verifies configured URLs and falls back to scraping the EPA trends page
    if any configured URL is missing or returns non-200 (e.g., HTTP 404 after
    an EPA release update).
    """
    own_session = session is None
    if own_session:
        session = _create_http_session()
    try:
        if (config_urls and len(config_urls) >= 2 and
                all(check_url_status(u, session=session) for u in config_urls)):
            return config_urls

        logging.warning(
            "Configured GCS URLs are missing or unreachable; falling back to "
            "live EPA trends page discovery.")
        scraped_urls = scrape_epa_trends_urls(session=session)
        if (len(scraped_urls) == 2 and all(
                check_url_status(u, session=session) for u in scraped_urls)):
            return scraped_urls

        return []
    finally:
        if own_session:
            session.close()


def _clean_download_directory(download_dir: str) -> None:
    """Removes stale Excel or temporary files from previous runs."""
    if not os.path.exists(download_dir):
        return
    for existing_file in sorted(os.listdir(download_dir)):
        if existing_file.lower().endswith(('.xlsx', '.xls', '.tmp')):
            stale_path = os.path.join(download_dir, existing_file)
            if os.path.isfile(stale_path):
                os.remove(stale_path)
                logging.info(f"Removed stale file: {stale_path}")


def download_files(urls: list) -> None:
    """
    Download files from specified URLs and log the status.

    Args:
        urls (list): A list of file URLs to download.

    Returns:
        None
    """
    os.makedirs(_DOWNLOAD_PATH, exist_ok=True)

    session = _create_http_session()
    try:
        resolved_urls = resolve_download_urls(urls, session=session)
        if not resolved_urls:
            raise ValueError("No reachable URLs found to download.")

        _clean_download_directory(_DOWNLOAD_PATH)

        for file_url in resolved_urls:
            file_name = os.path.basename(urllib.parse.urlsplit(file_url).path)
            file_path = os.path.join(_DOWNLOAD_PATH, file_name)
            tmp_path = f"{file_path}.tmp"

            try:
                logging.info(f"Downloading GET {file_url} to {file_path}")
                with session.get(file_url,
                                 stream=True,
                                 timeout=_HTTP_TIMEOUT_SECONDS) as response:
                    response.raise_for_status()
                    with open(tmp_path, "wb") as f_out:
                        for chunk in response.iter_content(chunk_size=65536):
                            if chunk:
                                f_out.write(chunk)
                file_size = os.path.getsize(tmp_path)
                if file_size == 0:
                    raise IOError(f"Downloaded file is empty: {tmp_path}")
                os.replace(tmp_path, file_path)
                logging.info(
                    f"Successfully downloaded: {file_name} ({file_size} bytes) "
                    f"to {file_path}")
            except Exception as e:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                logging.fatal(
                    f"Failed to download {file_name} from {file_url}. "
                    f"Details: {e}")
    finally:
        session.close()


def main(argv):
    del argv
    # Get the config path from the flags
    config_path_flag = _FLAGS.config_path

    if not config_path_flag:
        raise ValueError(
            "Please provide the --config_path flag with a valid GCS path.")

    try:
        bucket_name, config_path = parse_gcs_path(config_path_flag)
    except ValueError as e:
        logging.fatal(f"Invalid GCS path: {e}")

    # Read URLs from the GCS-hosted config file (with live EPA page fallback)
    urls = read_config_from_gcs(bucket_name, config_path)
    download_files(urls)


if __name__ == '__main__':
    app.run(main)
