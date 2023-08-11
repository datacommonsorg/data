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
"""Processes WB datasets.

Supports the following tasks:

============================

fetch_datasets: Fetches WB dataset lists and resources and writes them to 'output/wb-datasets.csv'

Run: python3 datasets.py mode=fetch_datasets

============================

download_datasets: Downloads datasets listed in 'output/wb-datasets.csv' to the  'output/downloads' folder.

Run: python3 datasets.py mode=download_datasets

============================

write_wb_codes: Extracts World Bank indicator codes (and related information) from files downloaded in the  'output/downloads' folder to 'output/wb-codes.csv'.

It only operates on files that are named '*_CSV.zip'.

Run: python3 datasets.py mode=write_wb_codes
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
from absl import flags
import zipfile
import codecs

FLAGS = flags.FLAGS


class Mode:
    FETCH_DATASETS = 'fetch_datasets'
    DOWNLOAD_DATASETS = 'download_datasets'
    WRITE_WB_CODES = 'write_wb_codes'


flags.DEFINE_string(
    'mode', Mode.WRITE_WB_CODES,
    f"Specify one of the following modes: {Mode.FETCH_DATASETS}, {Mode.DOWNLOAD_DATASETS}, {Mode.WRITE_WB_CODES}"
)

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


DATA_FILE_SUFFIX = 'Data.csv'
SERIES_FILE_SUFFIX = 'Series.csv'
CSV_ZIP_FILE_SUFFIX = '_CSV.zip'
SERIES_CODE_KEY = 'seriescode'
INDICATOR_NAME_KEY = 'indicatorname'
SHORT_DEFINITION_KEY = 'shortdefinition'
TOPIC_KEY = 'topic'
CODES_FILE_PATH = f"{OUTPUT_DIR}/wb-codes.csv"
CODES_CSV_COLUMNS = [
    SERIES_CODE_KEY, INDICATOR_NAME_KEY, SHORT_DEFINITION_KEY, TOPIC_KEY
]


def write_wb_codes():
    csv_rows = get_all_codes().values()
    with open(CODES_FILE_PATH, 'w', newline='') as out:
        csv_writer = csv.DictWriter(out,
                                    fieldnames=CODES_CSV_COLUMNS,
                                    lineterminator='\n')
        csv_writer.writeheader()
        csv_writer.writerows(csv_rows)


def get_all_codes():
    all_codes = {}
    for file_name in os.listdir(DOWNLOADS_DIR):
        if file_name.endswith(CSV_ZIP_FILE_SUFFIX):
            zip_file = f"{DOWNLOADS_DIR}/{file_name}"
            codes = get_codes_from_zip(zip_file)
            if codes:
                all_codes.update(codes)
    logging.info('# total codes: %s', len(all_codes))
    return all_codes


def get_codes_from_zip(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip:
        series_file = get_series_file_name(zip)
        if series_file is None:
            logging.warning('No series file found in ZIP file: %s', zip_file)
        else:
            with zip.open(series_file, 'r') as csv_file:
                series_rows = sanitize_csv_rows(
                    list(csv.DictReader(codecs.iterdecode(csv_file, 'utf-8'))))
                num_codes = len(series_rows)
                logging.info('# code(s) in %s: %s', zip_file, num_codes)
                if num_codes == 0:
                    return {}

                if series_rows[0].get(SERIES_CODE_KEY) is None:
                    logging.error('No series code found in %s, sample row: %s',
                                  zip_file, series_rows[0])
                    return {}

                codes = {}
                for series_row in series_rows:
                    code = series_row.get(SERIES_CODE_KEY)
                    codes[code] = {
                        SERIES_CODE_KEY:
                            code,
                        INDICATOR_NAME_KEY:
                            series_row.get(INDICATOR_NAME_KEY),
                        SHORT_DEFINITION_KEY:
                            series_row.get(SHORT_DEFINITION_KEY),
                        TOPIC_KEY:
                            series_row.get(TOPIC_KEY)
                    }
                return codes
        return {}


def sanitize_csv_rows(csv_rows):
    sanitized_rows = []
    for csv_row in csv_rows:
        sanitized_rows.append(
            dict((sanitize_csv_key(key), value)
                 for (key, value) in csv_row.items()))
    return sanitized_rows


def sanitize_csv_key(key):
    return re.sub(r'[^a-zA-Z0-9]', '', key).lower()


def get_series_file_name(zip):
    for file_name in zip.namelist():
        if file_name.endswith(DATA_FILE_SUFFIX):
            series_file_name = file_name.replace(DATA_FILE_SUFFIX,
                                                 SERIES_FILE_SUFFIX)
            if series_file_name in zip.namelist():
                return series_file_name
    return None


def main(_):
    match FLAGS.mode:
        case Mode.FETCH_DATASETS:
            download_datasets()
        case Mode.DOWNLOAD_DATASETS:
            fetch_and_write_datasets_csv()
        case Mode.WRITE_WB_CODES:
            write_wb_codes()
        case _:
            logging.error('No mode specified.')


if __name__ == '__main__':
    app.run(main)
