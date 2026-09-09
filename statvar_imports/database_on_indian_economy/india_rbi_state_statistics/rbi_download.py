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

import json
import os
import pathlib
import re
import sys
import tempfile
import time
from absl import app, flags, logging
from google.cloud import storage
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
import urllib3
from urllib3.util import Retry

# Suppress unverified HTTPS warnings for RBI endpoints
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")
DEFAULT_CONFIG_JSON = os.path.join(SCRIPT_DIR, 'configs.json')

flags.DEFINE_string('config_file_path', DEFAULT_CONFIG_JSON,
                    'Config file path (local json or gs:// path)')

DEFAULT_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/124.0.0.0 Safari/537.36'),
    'Accept':
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language':
    'en-US,en;q=0.9',
}

XLSX_ZIP_SIGNATURE = b'PK\x03\x04'


def create_retry_session(
        retries: int = 4,
        backoff_factor: float = 2.0,
        status_forcelist: tuple = (429, 500, 502, 503, 504),
) -> requests.Session:
    """Creates a requests.Session with connection pooling, retries, and browser headers."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["HEAD", "GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy,
                          pool_connections=10,
                          pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(DEFAULT_HEADERS)
    session.verify = False
    return session


def _load_local_config(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"Failed to read local config file '{file_path}': {e}")
    return None


def reads_config_file():
    _FLAGS = flags.FLAGS
    try:
        config_file_path = _FLAGS.config_file_path
    except (flags.UnparsedFlagAccessError, AttributeError):
        try:
            config_file_path = _FLAGS['config_file_path'].value
        except Exception:
            config_file_path = DEFAULT_CONFIG_JSON

    # 1. If it's a local file path (or doesn't start with gs://), try loading it
    if config_file_path and not config_file_path.startswith('gs://'):
        config = _load_local_config(config_file_path)
        if config and 'URLS_CONFIG' in config:
            logging.info(f"Loaded config from local path: {config_file_path}")
            return config
        logging.warning(
            f"Could not load config from local file '{config_file_path}'")

    # 2. If it's a GCS path, try loading from GCS
    if config_file_path and config_file_path.startswith('gs://'):
        try:
            storage_client = storage.Client()
            parts = config_file_path[5:].split('/', 1)
            bucket_name = parts[0]
            blob_name = parts[1] if len(parts) > 1 else ''
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            file_contents = blob.download_as_text()
            if config_file_path.endswith('.json'):
                return json.loads(file_contents)
            local_vars = {}
            exec(file_contents, {}, local_vars)
            return local_vars
        except Exception as e:
            logging.warning(
                f"Cannot extract url and related configs from GCS '{config_file_path}': {e}. "
                "Falling back to local configuration.")

    # 3. Fall back to local configs.json in SCRIPT_DIR
    config = _load_local_config(DEFAULT_CONFIG_JSON)
    if config and 'URLS_CONFIG' in config:
        logging.info(
            f"Loaded fallback configuration from {DEFAULT_CONFIG_JSON}")
        return config

    logging.error(
        "Cannot extract url and related configs: all sources failed.")
    raise RuntimeError(
        "Cannot extract url and related configs: all sources failed.")


def download_files(URL_CONFIG, session=None, delay=0.5):
    if not URL_CONFIG:
        logging.warning("No URL configurations provided to download.")
        return

    if session is None:
        session = create_retry_session()

    for config in URL_CONFIG:
        config_url = config.get("url")
        category_name = config.get("category")
        file_name = config.get("filename")
        if not config_url or not category_name or not file_name:
            logging.warning(f"Skipping incomplete config: {config}")
            continue

        target_dir = os.path.join(INPUT_DIR, category_name)
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, file_name)

        if os.path.exists(file_path):
            if os.path.getsize(file_path) > 0:
                with open(file_path, 'rb') as f:
                    magic = f.read(4)
                if magic == XLSX_ZIP_SIGNATURE:
                    logging.info(f"Skipping existing valid file: {file_name}")
                    continue
            # Remove stale, empty, or corrupt file
            try:
                os.remove(file_path)
            except OSError:
                pass

        try:
            logging.info(f"Attempting GET request to: {config_url}")
            response = session.get(config_url, timeout=45)

            if response.status_code == 404:
                logging.warning(
                    f"Table not found (HTTP 404) at {config_url}, skipping {file_name}"
                )
                continue

            response.raise_for_status()
            content = response.content

            if not content:
                logging.error(
                    f"Empty response received for {file_name} from {config_url}"
                )
                continue

            if not content.startswith(XLSX_ZIP_SIGNATURE):
                snippet = content[:50].decode('utf-8', errors='replace')
                logging.error(
                    f"Invalid file format received for {file_name} from {config_url}: "
                    f"expected XLSX ZIP signature, got: {snippet!r}")
                continue

            # Write atomically to a temporary file, then move into place
            with tempfile.NamedTemporaryFile('wb',
                                             dir=target_dir,
                                             delete=False) as tmp_file:
                tmp_file.write(content)
                temp_path = tmp_file.name

            os.replace(temp_path, file_path)
            logging.info(
                f"Downloaded the file {file_name} successfully ({len(content)} bytes)."
            )

            if delay > 0:
                time.sleep(delay)

        except Exception as e:
            logging.error(
                f"Failed to download table {file_name} from {config_url}: {e}")


def _apply_map(df, func):
    """Version-agnostic element-wise DataFrame mapping (uses df.map if available, else df.applymap)."""
    if hasattr(df, 'map'):
        return df.map(func)
    return df.applymap(func)


def preprocess_files(directory_path):
    if not os.path.isdir(directory_path):
        logging.fatal(f"Error: Directory not found at '{directory_path}'")
        return

    xlsx_files = [f for f in os.listdir(directory_path) if f.endswith('.xlsx')]

    if not xlsx_files:
        logging.fatal(
            f"No XLSX files found in the directory: {directory_path}")
        return

    logging.info(
        f"Found {len(xlsx_files)} XLSX files to process in '{directory_path}'."
    )

    for file_name in sorted(xlsx_files):
        file_path = os.path.join(directory_path, file_name)
        logging.info(f"Processing file: {file_path}")
        try:
            all_sheets_data = pd.read_excel(file_path,
                                            sheet_name=None,
                                            header=None,
                                            engine='openpyxl')

            def clean_cell(val):
                if pd.isna(val):
                    return val
                if isinstance(val, (int, float)):
                    return val
                val_str = str(val).replace('*', '').replace('@', '').strip()
                if not val_str or val_str.lower() == 'nan':
                    return float('nan')
                return val_str

            def safe_to_numeric(val):
                if pd.isna(val):
                    return val
                if isinstance(val, (int, float)):
                    return val
                val_str = str(val).strip()
                if not val_str or val_str.lower() == 'nan':
                    return float('nan')
                if val_str.isdigit():
                    return int(val_str)
                try:
                    float_val = float(val_str)
                    if float_val.is_integer():
                        return int(float_val)
                    return float_val
                except ValueError:
                    return val

            def is_state_header(val):
                if pd.isna(val):
                    return False
                return bool(
                    re.search(r'state\s*/\s*union\s*territory', str(val),
                              re.IGNORECASE))

            for sheet_name, df in all_sheets_data.items():
                df = _apply_map(df, clean_cell)
                is_state_cell = _apply_map(df, is_state_header)
                mask = is_state_cell.any(axis=1)

                if mask.any():
                    state_positions = is_state_cell.loc[mask]
                    df_num = _apply_map(df[mask], safe_to_numeric)
                    converted = df_num.mask(state_positions, df[mask])
                    df = df.astype(object)
                    df.loc[mask, :] = converted
                all_sheets_data[sheet_name] = df

            with tempfile.TemporaryDirectory(dir=directory_path) as output_dir:
                output_path = os.path.join(output_dir, file_name)
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    for sheet_name, df in all_sheets_data.items():
                        df.to_excel(writer,
                                    sheet_name=sheet_name,
                                    index=False,
                                    header=False)
                os.replace(output_path, file_path)

        except Exception as e:
            logging.error(f"Error processing {file_name}: {e}")

    logging.info("All specified XLSX files have been processed.")


def main(_):
    configs = reads_config_file()
    RBI_URL = configs['URLS_CONFIG']
    download_files(RBI_URL)
    logging.info("Download process Completed successfully")
    directories = [
        'agriculture', 'environment', 'infrastructure', 'price_and_wages'
    ]
    for directory in directories:
        preprocess_files(os.path.join(INPUT_DIR, directory))
    logging.info("Pre-process Completed successfully")


if __name__ == "__main__":
    app.run(main)
