# Copyright 2021 Google LLC
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
"""Populates a list of downloadable world bank datasets.

It can also optionally download these datasets.

To run this script:

python3 datasets.py

Be default, the script will only produce a CSV with the list of datasets.
Once the CSV is created, to download the datasets, the download_datasets method will need to be called explicitly.

"""

import requests
from absl import app
from absl import logging
import os
import json
import multiprocessing
import csv
import re
import urllib3
from urllib3.util.ssl_ import create_urllib3_context

ctx = create_urllib3_context()
ctx.load_default_certs()
ctx.options |= 0x4  # ssl.OP_LEGACY_SERVER_CONNECT

DATASET_LIST_URL = 'https://datacatalogapi.worldbank.org/ddhxext/DatasetList'
DATASET_VIEW_URL = 'https://datacatalogapi.worldbank.org/ddhxext/DatasetView'

OUTPUT_DIR = 'output'
RESPONSE_DIR = f"{OUTPUT_DIR}/response"
DATASET_LISTS_RESPONSE_DIR = f"{RESPONSE_DIR}/lists"
DATASET_VIEWS_RESPONSE_DIR = f"{RESPONSE_DIR}/views"
DATASETS_CSV_FILE_PATH = f"{OUTPUT_DIR}/wb-datasets.csv"
DOWNLOADS_DIR = f"{OUTPUT_DIR}/downloads"

os.makedirs(DATASET_LISTS_RESPONSE_DIR, exist_ok=True)
os.makedirs(DATASET_VIEWS_RESPONSE_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

POOL_SIZE = max(2, multiprocessing.cpu_count() - 1)

DOWNLOADABLE_RESOURCE_TYPES = set(["Download", "Dataset"])

DATASET_NAME_COLUMN_NAME = "Dataset Name"
DATASET_RESOURCE_NAME_COLUMN_NAME = "Resource Name"
DATASET_VIEW_FILE_COLUMN_NAME = "Dataset View File"
DATASET_FORMAT_COLUMN_NAME = "Format"
DATASET_SIZE_COLUMN_NAME = "Size"
DATASET_DOWNLOAD_URL_COLUMN_NAME = "Download URL"

DATASETS_CSV_COLUMNS = [
    DATASET_NAME_COLUMN_NAME, DATASET_RESOURCE_NAME_COLUMN_NAME,
    DATASET_VIEW_FILE_COLUMN_NAME, DATASET_FORMAT_COLUMN_NAME,
    DATASET_SIZE_COLUMN_NAME, DATASET_DOWNLOAD_URL_COLUMN_NAME
]


def download_datasets():
    '''Downloads dataset files. This is a very expensive operation so run it with care. It assumes that the datasets CSV is already available.'''

    with open(DATASETS_CSV_FILE_PATH, 'r') as f:
        csv_rows = list(csv.DictReader(f))
        download_urls = []
        for csv_row in csv_rows:
            download_url = csv_row.get(DATASET_DOWNLOAD_URL_COLUMN_NAME)
            if download_url:
                download_urls.append(download_url)

        with multiprocessing.Pool(POOL_SIZE) as pool:
            pool.starmap(download, zip(download_urls))

        logging.info('# files downloaded: %s', len(download_urls))


def download(url):
    file_name = re.sub(r'[^a-zA-Z0-9\.\-_/]', '', url.split('/')[-1])
    file_path = f"{DOWNLOADS_DIR}/{file_name}"
    if os.path.exists(file_path):
        logging.info('Already downloaded %s to file %s', url, file_path)
        return

    logging.info('Downloading %s to file %s', url, file_path)
    try:
        # response = requests.get(url)
        # Using urllib3 for downloading content to avoid SSL issue.
        # See: https://github.com/urllib3/urllib3/issues/2653#issuecomment-1165418616
        with urllib3.PoolManager(ssl_context=ctx) as http:
            response = http.request("GET", url)
        with open(file_path, 'wb') as f:
            f.write(response.data)
    except Exception as e:
        logging.error("Error downloading %s", url, exc_info=e)


def fetch_and_write_datasets_csv():
    fetch_dataset_lists()
    fetch_dataset_views()
    write_datasets_csv()


def write_datasets_csv():
    csv_rows = get_datasets_csv_rows()
    with open(DATASETS_CSV_FILE_PATH, 'w', newline='') as out:
        csv_writer = csv.DictWriter(out,
                                    fieldnames=DATASETS_CSV_COLUMNS,
                                    lineterminator='\n')
        csv_writer.writeheader()
        csv_writer.writerows(csv_rows)


def get_datasets_csv_rows():
    # Assumes all dataset view responses have been saved to disk
    view_files = os.listdir(DATASET_VIEWS_RESPONSE_DIR)
    csv_rows = []
    for view_file in view_files:
        json = load_json_file(f"{DATASET_VIEWS_RESPONSE_DIR}/{view_file}")
        dataset_name = json.get('name')
        for resource in json.get('Resources', []):
            resource_type = resource.get('resource_type', '')

            if resource_type in DOWNLOADABLE_RESOURCE_TYPES:
                csv_row = to_dataset_csv_row(resource, dataset_name, view_file)
                if csv_row:
                    csv_rows.append(csv_row)

    logging.info('# downloadable datasets: %s', len(csv_rows))
    return csv_rows


DATASET_URL_FIELDS = ['harvet_source', 'url', 'website_url']

# URLs with this pattern are downloadable only if the URL is trunctated until it. Probably a bug in WB APIs.
VERSION_ID_PATTERN = '?versionId='


def to_dataset_csv_row(resource, dataset_name, view_file):
    format = resource.get('format')
    if format is None:
        return None

    url = None
    for field in DATASET_URL_FIELDS:
        url = resource.get(field)
        if url is not None:
            url = url.split(VERSION_ID_PATTERN)[0]
            break

    if url is None:
        return None

    return {
        DATASET_NAME_COLUMN_NAME: dataset_name,
        DATASET_RESOURCE_NAME_COLUMN_NAME: resource.get('name'),
        DATASET_VIEW_FILE_COLUMN_NAME: view_file,
        DATASET_FORMAT_COLUMN_NAME: format,
        DATASET_SIZE_COLUMN_NAME: resource.get('distribution_size'),
        DATASET_DOWNLOAD_URL_COLUMN_NAME: url
    }


def fetch_dataset_view(dataset_unique_id):
    params = f"dataset_unique_id={dataset_unique_id}"
    response_file = f"{DATASET_VIEWS_RESPONSE_DIR}/view-{dataset_unique_id}.json"
    return load_json(url=DATASET_VIEW_URL,
                     params=params,
                     response_file=response_file)


def fetch_dataset_views():
    # Assumes all dataset list responses have been saved to disk
    list_files = os.listdir(DATASET_LISTS_RESPONSE_DIR)
    dataset_unique_ids = []
    for list_file in list_files:
        json = load_json_file(f"{DATASET_LISTS_RESPONSE_DIR}/{list_file}")
        for dataset in json.get('data', []):
            dataset_unique_id = dataset.get('dataset_unique_id')
            if dataset_unique_id:
                dataset_unique_ids.append(dataset_unique_id)

    with multiprocessing.Pool(POOL_SIZE) as pool:
        pool.starmap(fetch_dataset_view, zip(dataset_unique_ids))


def fetch_dataset_list(skip):
    params = f"$skip={skip}&$top=1000"
    response_file = f"{DATASET_LISTS_RESPONSE_DIR}/list-{skip}.json"
    return load_json(url=DATASET_LIST_URL,
                     params=params,
                     response_file=response_file)


def fetch_dataset_lists():
    # 6000+ datasets, fetching 1000 at a time
    skips = range(0, 7000, 1000)
    with multiprocessing.Pool(POOL_SIZE) as pool:
        pool.starmap(fetch_dataset_list, zip(skips))


def load_json(url, params, response_file):
    if os.path.exists(response_file):
        logging.info('Reading response from file %s', response_file)
        with open(response_file, 'r') as f:
            return json.load(f)

    logging.info("Fetching url %s, params %s", url, params)
    response = requests.get(url, params=params).json()
    with open(response_file, 'w') as f:
        logging.info('Writing response to file %s', response_file)
        json.dump(response, f, indent=2)
    return response


def load_json_file(json_file):
    with open(json_file, 'r') as f:
        return json.load(f)


def main(_):
    fetch_and_write_datasets_csv()
    # download_datasets()


if __name__ == '__main__':
    app.run(main)
