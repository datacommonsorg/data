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
"""Script to process data sets from OpenDataAfrica."""

import ast
import csv
import os
import sys

from absl import app
from absl import flags
from absl import logging
from typing import Union

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import file_util
import download_util

flags.DEFINE_list('country', 'egypt', 'URL for the list of tables to download.')
flags.DEFINE_list('dataset_id', '', 'ID of dataset to process.')
flags.DEFINE_string('output_path', '', 'Directory to save output files.')
flags.DEFINE_integer('max_pages', 10,
                     'maximum number of pages to download per table.')
flags.DEFINE_bool('debug', False, 'Enable debug messages.')

_FLAGS = flags.FLAGS


def get_country_tables_url(country: str):
    '''Returns the URL to get the list of tables for a country.'''
    return f'https://{country}.opendataforafrica.org/api/1.0/meta/dataset'


def get_dataset_url(country: str,
                    dataset_id: str,
                    continue_token: str = '') -> (str, dict):
    '''Returns the URL and params to download the dataset of the given id.'''
    if not dataset_id:
        # No dataset specified. return URL to list all datasets.
        return get_country_tables_url(country), {}
    if continue_token:
        # Use API 1.0 to get the next page with the continueToken
        return f'https://{country}.opendataforafrica.org/api/1.0/data/raw', {
            'datasetId': dataset_id,
            'continuationToken': continue_token,
        }
    else:
        # Use api 2.0 to get the first continueToken
        # return f'https://egypt.opendataforafrica.org/api/1.0/data/dataset/{dataset_id}', {}
        return f'https://{country}.opendataforafrica.org/api/2.0/data', {
            'datasetId': dataset_id
        }


def flatten_dict(nested_dict: dict, key_prefix: str = '') -> dict:
    '''Returns a flattened dict with key:values from the  nested dict
  { prop1: { prop2: value }}, concatenating keys: { prop1.prop2: <value> }
  '''
    output_dict = {}
    if nested_dict is None:
        return {}
    if isinstance(nested_dict, str) or isinstance(
            nested_dict, int) or isinstance(nested_dict, float):
        # value is a basic type. Keep it as is.
        return nested_dict
    if isinstance(nested_dict, list):
        nested_dict = {str(i): nested_dict[i] for i in range(len(nested_dict))}
    # Expand any nested values
    for key, value in nested_dict.items():
        value = flatten_dict(value)
        if isinstance(value, dict):
            for nkey, nvalue in value.items():
                output_dict[f'{key_prefix}{key}.{nkey}'] = nvalue
        else:
            output_dict[f'{key_prefix}{key}'] = value
    return output_dict


def list_to_dict(input_list: list, output_dict: dict = None) -> dict:
    '''Returns a dict with each element in the list as a value of the index.'''
    if output_dict is None:
        output_dict = dict()
    if isinstance(input_list, dict):
        output_dict.update(flatten_dict(input_list))
    elif isinstance(input_list, list):
        for item in input_list:
            output_dict[len(output_dict)] = flatten_dict(item)
    return output_dict


def download_url_dict(country: str,
                      dataset_id: str = '',
                      output_file: str = 'output.csv') -> dict:
    '''Returns the content of the downloaded URL as a flattened dict.'''
    output_dict = file_util.file_load_csv_dict(output_file)
    if output_dict:
        logging.info(f'Using {len(output_dict)} cached in {output_file}')
        return output_dict
    url, params = get_dataset_url(country, dataset_id)
    output_dict = dict()
    logging.info(f'Downloading {url} with {params}')
    url_json = download_util.request_url(url=url,
                                         params=params,
                                         output='json',
                                         timeout=300)
    if url_json is None:
        return {}
    continuation_token = ''
    if isinstance(url_json, dict):
        data_dict = url_json.get('data')
        output_dict = list_to_dict(data_dict)
        continuation_token = url_json.get('continuationToken')
    elif isinstance(url_json, list):
        output_dict = list_to_dict(url_json)
    else:
        logging.error(
            f'Got unsupported response for {url}:{params}: {url_json}')
    if output_dict:
        file_util.file_write_csv_dict(output_dict, output_file)
    page_count = 0
    num_rows = len(output_dict)
    shard_rows = len(output_dict)
    max_pages = _FLAGS.max_pages
    while continuation_token is not None and shard_rows > 0 and page_count < max_pages:
        page_count += 1
        url, params = get_dataset_url(country, dataset_id, continuation_token)
        logging.info(f'Continue download {page_count}: {url} with {params}')
        url_json = download_util.request_url(url=url,
                                             params=params,
                                             output='json',
                                             timeout=300)
        shard_rows = 0
        if isinstance(url_json, dict):
            data_dict = url_json.get('data')
            shard_dict = list_to_dict(data_dict)
            if output_dict:
                shard_rows = len(shard_dict)
                num_rows += shard_rows
                shard_file = file_util.file_get_name(file_path=output_file,
                                                     suffix=f'-{page_count}',
                                                     file_ext='.csv')
                logging.info(
                    f'Downloaded shard:{page_count} with {shard_rows} rows for {url}:{params} into {shard_file}'
                )
                file_util.file_write_csv_dict(shard_dict, shard_file)
                output_dict.update(shard_dict)
            continuation_token = url_json.get('continuationToken')
            logging.info(
                f'Got continuationToken {continuation_token} for page: {page_count}, {dataset_id}, {url}'
            )
    logging.info(
        f'Downloaded {page_count} pages with {num_rows} rows, columns: {output_dict.keys()} for {url}:{params} into {output_file}'
    )
    return output_dict


def download_tables_list(country: str, output_file: str) -> dict:
    '''Returns the dictionary of tables as a dict and also writes to the output file.'''
    output_dict = download_url_dict(country=country, output_file=output_file)
    logging.info(f'Downloaded {len(output_dict)} tables into {output_file}')
    return output_dict


def main(_):
    if _FLAGS.debug:
        logging.set_verbosity(2)
    countries = _FLAGS.country
    for country in countries:
        datasets = _FLAGS.dataset_id
        if not datasets:
            # get list of all datasets for the country
            tables_file = file_util.file_get_name(_FLAGS.output_path,
                                                  f'-{country}-tables')
            logging.info('Downloading tables for {country} into {tables-file}')
            tables_dict = download_tables_list(country, tables_file)
            datasets = []
            for table in tables_dict.values():
                dataset = table.get('id')
                if dataset:
                    datasets.append(dataset)
        # Download each dataset table
        logging.info(f'Downloading datasets for {country}: {datasets}')
        for dataset_id in datasets:
            dataset_file = file_util.file_get_name(
                _FLAGS.output_path,
                f'/{country}/{dataset_id}/{country}-dataset-{dataset_id}')
            logging.info(
                f'Downloading {country}, dataset: {dataset_id} into {dataset_file}'
            )
            download_url_dict(country, dataset_id, dataset_file)


if __name__ == '__main__':
    app.run(main)
