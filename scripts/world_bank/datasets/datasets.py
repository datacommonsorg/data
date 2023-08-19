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

Run: python3 datasets.py --mode=fetch_datasets

============================

download_datasets: Downloads datasets listed in 'output/wb-datasets.csv' to the 'output/downloads' folder.

Run: python3 datasets.py --mode=download_datasets

============================

write_wb_codes: Extracts World Bank indicator codes (and related information) from files downloaded in the  'output/downloads' folder to 'output/wb-codes.csv'.

It only operates on files that are named '*_CSV.zip'.

Run: python3 datasets.py --mode=write_wb_codes

============================

load_stat_vars: Loads stat vars from a mapping file specified via the `stat_vars_file` flag.

Use this for debugging to ensure that the mappings load correctly and fix any errors logged by this operation.

Run: python3 datasets.py --mode=load_stat_vars --stat_vars_file=/path/to/sv_mappings.csv

See `sample-svs.csv` for a sample mappings file.

============================

write_observations: Extracts observations from files downloaded in the 'output/downloads' folder and saves them to CSVs in the 'output/observations' folder.

The stat vars file to be used for mappings should be specified using the `stat_vars_file' flag.

It only operates on files that are named '*_CSV.zip'.

Run: python3 datasets.py --mode=write_observations --stat_vars_file=/path/to/sv_mappings.csv
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
from itertools import repeat
from datetime import datetime

FLAGS = flags.FLAGS


class Mode:
    FETCH_DATASETS = 'fetch_datasets'
    DOWNLOAD_DATASETS = 'download_datasets'
    WRITE_WB_CODES = 'write_wb_codes'
    LOAD_STAT_VARS = 'load_stat_vars'
    WRITE_OBSERVATIONS = 'write_observations'


flags.DEFINE_string(
    'mode', Mode.WRITE_OBSERVATIONS,
    f"Specify one of the following modes: {Mode.FETCH_DATASETS}, {Mode.DOWNLOAD_DATASETS}, {Mode.WRITE_WB_CODES}, {Mode.LOAD_STAT_VARS}, {Mode.WRITE_OBSERVATIONS}"
)

flags.DEFINE_string('stat_vars_file', 'statvars.csv',
                    'Path to CSV file with Stat Var mappings.')

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
OBSERVATIONS_DIR = f"{OUTPUT_DIR}/observations"

os.makedirs(DATASET_LISTS_RESPONSE_DIR, exist_ok=True)
os.makedirs(DATASET_VIEWS_RESPONSE_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(OBSERVATIONS_DIR, exist_ok=True)

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
NUM_DATASETS_KEY = 'numdatasets'
INDICATOR_NAME_KEY = 'indicatorname'
TOPIC_KEY = 'topic'
UNIT_OF_MEASURE_KEY = 'unitofmeasure'
UNIT_KEY = 'unit'
SHORT_DEFINITION_KEY = 'shortdefinition'
LONG_DEFINITION_KEY = 'longdefinition'
LICENSE_TYPE_KEY = 'licensetype'
STAT_VAR_KEY = 'statvar'
COUNTRY_CODE_KEY = 'countrycode'
INDICATOR_CODE_KEY = 'indicatorcode'
OBSERVATION_DATE_KEY = 'observationdate'
OBSERVATION_ABOUT_KEY = 'observationabout'
OBSERVATION_VALUE_KEY = 'observationvalue'
MEASUREMENT_METHOD_KEY = 'measurementmethod'
CODES_FILE_PATH = os.path.join(OUTPUT_DIR, 'wb-codes.csv')
CODES_CSV_COLUMNS = [
    SERIES_CODE_KEY, INDICATOR_NAME_KEY, NUM_DATASETS_KEY, TOPIC_KEY,
    UNIT_OF_MEASURE_KEY, SHORT_DEFINITION_KEY, LONG_DEFINITION_KEY,
    LICENSE_TYPE_KEY
]
OBS_CSV_COLUMNS = [
    INDICATOR_CODE_KEY, STAT_VAR_KEY, MEASUREMENT_METHOD_KEY,
    OBSERVATION_ABOUT_KEY, OBSERVATION_DATE_KEY, OBSERVATION_VALUE_KEY, UNIT_KEY
]
EARTH_DCID = 'dcid:Earth'
COUNTRY_DCID_PREFIX = 'dcid:country'
WORLD_BANK_STAT_VAR_PREFIX = 'worldBank'
WORLD_BANK_MEASUREMENT_METHOD_PREFIX = 'WorldBank'


def load_stat_vars(stat_var_file):
    with open(stat_var_file, 'r') as f:
        csv_rows = sanitize_csv_rows(list(csv.DictReader(f)))
        svs = {}
        for csv_row in csv_rows:
            if csv_row.get(SERIES_CODE_KEY) and csv_row.get(STAT_VAR_KEY):
                svs[csv_row[SERIES_CODE_KEY]] = csv_row
            else:
                logging.error('SKIPPED stat var row: %s', csv_row)

        logging.info(svs)
        return svs


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
                for key, value in codes.items():
                    if key in all_codes:
                        all_codes[key][NUM_DATASETS_KEY] = all_codes[key][
                            NUM_DATASETS_KEY] + 1
                    else:
                        all_codes[key] = value
    logging.info('# total codes: %s', len(all_codes))
    return all_codes


def get_codes_from_zip(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip:
        (_, series_file) = get_data_and_series_file_names(zip)
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
                        NUM_DATASETS_KEY:
                            1,
                        TOPIC_KEY:
                            series_row.get(TOPIC_KEY),
                        UNIT_OF_MEASURE_KEY:
                            series_row.get(UNIT_OF_MEASURE_KEY),
                        SHORT_DEFINITION_KEY:
                            series_row.get(SHORT_DEFINITION_KEY),
                        LONG_DEFINITION_KEY:
                            series_row.get(LONG_DEFINITION_KEY),
                        LICENSE_TYPE_KEY:
                            series_row.get(LICENSE_TYPE_KEY),
                    }
                return codes
        return {}


def write_csv(csv_file_path, csv_columns, csv_rows):
    with open(csv_file_path, 'w', newline='') as out:
        csv_writer = csv.DictWriter(out,
                                    fieldnames=csv_columns,
                                    lineterminator='\n')
        csv_writer.writeheader()
        csv_writer.writerows(csv_rows)


def write_all_observations(stat_vars_file):
    start = datetime.now()
    logging.info('Start: %s', start)

    svs = load_stat_vars(stat_vars_file)

    zip_files = []
    for file_name in os.listdir(DOWNLOADS_DIR):
        if file_name.endswith(CSV_ZIP_FILE_SUFFIX):
            zip_files.append(f"{DOWNLOADS_DIR}/{file_name}")

    with multiprocessing.Pool(POOL_SIZE) as pool:
        pool.starmap(write_observations_from_zip, zip(zip_files, repeat(svs)))

    end = datetime.now()
    logging.info('End: %s', end)
    logging.info('Duration: %s', str(end - start))


def write_observations_from_zip(zip_file, svs):
    csv_rows = get_observations_from_zip(zip_file, svs)
    if len(csv_rows) == 0:
        logging.info(
            'SKIPPED writing obs file, no observations extracted from %s',
            zip_file)
        return

    obs_file_name = f"{zip_file.split('/')[-1].split('.')[0]}_obs.csv"
    obs_file_path = os.path.join(OBSERVATIONS_DIR, obs_file_name)
    logging.info('Writing %s observations from %s to %s', len(csv_rows),
                 zip_file, obs_file_path)
    write_csv(obs_file_path, OBS_CSV_COLUMNS, csv_rows)


def get_observations_from_zip(zip_file, svs):
    with zipfile.ZipFile(zip_file, 'r') as zip:
        (data_file, _) = get_data_and_series_file_names(zip)
        if data_file is None:
            logging.warning('No data file found in ZIP file: %s', zip_file)
            return []
        else:
            # Use name of file (excluding the extension) as the measurement method
            measurement_method = f"{WORLD_BANK_MEASUREMENT_METHOD_PREFIX}_{zip_file.split('/')[-1].split('.')[0]}"
            with zip.open(data_file, 'r') as csv_file:
                data_rows = sanitize_csv_rows(
                    list(csv.DictReader(codecs.iterdecode(csv_file, 'utf-8'))))
                num_rows = len(data_rows)
                logging.info('# data rows in %s: %s', zip_file, num_rows)

                obs_csv_rows = []
                for data_row in data_rows:
                    obs_csv_rows.extend(
                        get_observations_from_data_row(data_row, svs,
                                                       measurement_method))

                return obs_csv_rows


def get_observations_from_data_row(data_row, svs, measurement_method):
    code = data_row.get(INDICATOR_CODE_KEY)
    if code is None:
        logging.error('SKIPPED data row, no indicator code: %s', data_row)
        return []

    sv = get_stat_var_from_code(code, svs)
    if sv is None:
        return []

    place_dcid = data_row.get(COUNTRY_CODE_KEY)
    if place_dcid:
        if len(place_dcid) != 3:
            logging.error('SKIPPED data row, not a country code: %s',
                          place_dcid)
            return []
        else:
            place_dcid = f"{COUNTRY_DCID_PREFIX}/{place_dcid}"
    else:
        place_dcid = EARTH_DCID

    obs_csv_rows = []
    for key in data_row.keys():
        # Flatten year columns with values into rows.
        # Each year is a column and columns are integers.
        # So we ignore those that are not.
        if not key.isdecimal():
            continue

        year = key

        # We are only interested in numeric values.
        value = data_row[year]
        if not is_numeric(value):
            continue

        obs_csv_rows.append({
            INDICATOR_CODE_KEY: code,
            STAT_VAR_KEY: sv[STAT_VAR_KEY],
            MEASUREMENT_METHOD_KEY: measurement_method,
            OBSERVATION_ABOUT_KEY: place_dcid,
            OBSERVATION_DATE_KEY: year,
            OBSERVATION_VALUE_KEY: value,
            UNIT_KEY: sv.get(UNIT_KEY)
        })

    return obs_csv_rows


def get_stat_var_from_code(code, svs):
    sv_mapping = svs.get(code)
    if sv_mapping is None or sv_mapping.get(STAT_VAR_KEY) is None:
        logging.warning('SKIPPED, WB code not mapped: %s', code)
        return None
    return sv_mapping


def is_numeric(value):
    if value is None:
        return False

    if value.isdecimal():
        return True

    try:
        float(value)
        return True
    except:
        return False


def sanitize_csv_rows(csv_rows):
    sanitized_rows = []
    for csv_row in csv_rows:
        sanitized_rows.append(
            dict((sanitize_csv_key(key), value)
                 for (key, value) in csv_row.items()))
    return sanitized_rows


def sanitize_csv_key(key):
    return re.sub(r'[^a-zA-Z0-9]', '', key).lower()


def get_data_and_series_file_names(zip):
    for file_name in zip.namelist():
        if file_name.endswith(DATA_FILE_SUFFIX):
            series_file_name = file_name.replace(DATA_FILE_SUFFIX,
                                                 SERIES_FILE_SUFFIX)
            if series_file_name in zip.namelist():
                return (file_name, series_file_name)
    return (None, None)


def main(_):
    match FLAGS.mode:
        case Mode.FETCH_DATASETS:
            download_datasets()
        case Mode.DOWNLOAD_DATASETS:
            fetch_and_write_datasets_csv()
        case Mode.WRITE_WB_CODES:
            write_wb_codes()
        case Mode.LOAD_STAT_VARS:
            load_stat_vars(FLAGS.stat_vars_file)
        case Mode.WRITE_OBSERVATIONS:
            write_all_observations(FLAGS.stat_vars_file)
        case _:
            logging.error('No mode specified.')


if __name__ == '__main__':
    app.run(main)
