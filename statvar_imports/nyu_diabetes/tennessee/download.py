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


from datetime import date
import os
from pathlib import Path
import re
from urllib.parse import urlparse

from absl import app
from absl import flags
from absl import logging
from google.api_core import exceptions
from google.cloud import storage
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util import Retry

FLAGS = flags.FLAGS

flags.DEFINE_enum(
    'download_source',
    'tn',
    ['tn', 'gcs'],
    'Source from which input files are downloaded.',
)

script_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(script_dir, "input_files")
Path(INPUT_DIR).mkdir(parents=True, exist_ok=True)

def create_retry_session(
    retries: int = 3,
    backoff_factor: float = 2.0,
    status_forcelist: tuple = (429, 500, 502, 503, 504),
) -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(
        max_retries=retry_strategy, pool_connections=10, pool_maxsize=10
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    })
    return session

def download_files(url_list, save_folder):
    os.makedirs(os.path.join(save_folder), exist_ok=True)
    downloaded_count = 0
    session = create_retry_session()

    for url in url_list:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        file_path = os.path.join(save_folder, filename)

        logging.info(
            f"Starting download: source={url}, destination={file_path}")

        try:
            response = session.get(url, timeout=120, stream=True)
            if response.status_code == 404:
                logging.info(f"File not yet available (404), skipping: {url}")
                continue
            response.raise_for_status()

            with response as r:
                total_size = int(r.headers.get('content-length', 0))
                block_size = 1024
                with open(file_path, 'wb') as f, tqdm(
                    total=total_size, unit='B', unit_scale=True, desc=filename, leave=False
                ) as progress_bar:
                    for chunk in r.iter_content(block_size):
                        f.write(chunk)
                        progress_bar.update(len(chunk))
            file_size = os.path.getsize(file_path)
            logging.info(
                f"Completed download: source={url}, destination={file_path}, size_bytes={file_size}"
            )
            downloaded_count += 1
        except requests.exceptions.RequestException as e:
            logging.error(
                f"Download failed: source={url}, destination={file_path}, error={e}"
            )
            raise

    if url_list and downloaded_count == 0:
        raise RuntimeError("No files were successfully downloaded.")


def download_files_from_gcs(url_list, save_folder):
    os.makedirs(save_folder, exist_ok=True)
    storage_client = storage.Client()
    downloaded_count = 0

    for url in url_list:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        file_path = os.path.join(save_folder, filename)
        Path(file_path).unlink(missing_ok=True)

        logging.info(
            f"Starting download: source={url}, destination={file_path}")

        try:
            blob = storage_client.bucket(parsed_url.netloc).blob(
                parsed_url.path.lstrip('/'))
            blob.download_to_filename(file_path)
        except exceptions.NotFound:
            Path(file_path).unlink(missing_ok=True)
            logging.warning(f"GCS object not found, skipping: source={url}")
            continue
        except Exception as e:
            Path(file_path).unlink(missing_ok=True)
            e.add_note(f"Failed to download GCS object {url}")
            raise

        file_size = os.path.getsize(file_path)
        logging.info(
            f"Completed download: source={url}, destination={file_path}, size_bytes={file_size}"
        )
        downloaded_count += 1

    if downloaded_count == 0:
        raise RuntimeError('No files were downloaded from GCS.')

def generate_urls(start_year, end_year, url_template):
    url_list = []
    for year in range(start_year,end_year+1):
        formatted_url = url_template.format(year=year)
        url_list.append(formatted_url)
    return url_list

def extract_year(filename):
    """Extracts a four-digit year from the filename using regex."""
    match = re.search(r'Diabetes_County_(\d{4}).xlsx', filename)
    if match:
        return int(match.group(1))
    return None

def process_excel_files(input_dir):
    """
    Iterates through downloaded Excel files, uses the provided map to determine 
    the year, adds a 'year' column, and saves the modified file.
    """
    logging.info("\nStarting Excel file processing: Adding 'year' column...")

    for root, _, files in os.walk(input_dir):
        excel_files = [f for f in files if f.endswith('.xlsx')]
        
        if not excel_files:
            continue
            
        logging.info(f"Processing {len(excel_files)} files in {os.path.basename(root)}...")

        for filename in tqdm(excel_files, desc=f"Adding Year Column to {os.path.basename(root)}"):
            file_path = os.path.join(root, filename)

            folder = os.path.basename(root)
            relative_key = os.path.join(folder, filename)
            year = extract_year(filename)
            
            if year is None:
                logging.warning(f"Could not find year for file in map: {relative_key}. Skipping processing.")
                continue

            try:
                df = pd.read_excel(file_path)
                df['year'] = year
                df.to_excel(file_path, index=False)
                
            except Exception as e:
                raise RuntimeError(f"Failed to process and save Excel file {filename}: {e}")

    logging.info("\nExcel file processing complete. 'year' column added to all processed files.")

def main(_):
    tn_url_template = "https://www.tn.gov/content/dam/tn/health/documents/vital-statistics/death/{year}/Diabetes_County_{year}.xlsx"
    gcs_url_template = "gs://unresolved_mcf/nyu_diabetes/tennessee/latest/input_files/Diabetes_County_{year}.xlsx"
    start_year = 2019
    current_year = date.today().year

    if FLAGS.download_source == 'gcs':
        final_urls = generate_urls(start_year, current_year, gcs_url_template)
        download_files_from_gcs(final_urls, save_folder=INPUT_DIR)
    else:
        final_urls = generate_urls(start_year, current_year, tn_url_template)
        download_files(final_urls, save_folder=INPUT_DIR)
    process_excel_files(INPUT_DIR)

if __name__ == "__main__":
    app.run(main)
