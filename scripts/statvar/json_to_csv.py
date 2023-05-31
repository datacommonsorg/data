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

import os
import sys
import json

from absl import app
from absl import flags
from absl import logging
from typing import Union

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import file_util

flags.DEFINE_string('input_json', '', 'JSON file to be converted into csv')
flags.DEFINE_string('csv_output', '', 'Output CSV file')

_FLAGS = flags.FLAGS


def flatten_dict(nested_dict: dict, key_prefix: str = '') -> dict:
    '''Returns a flattened dict with key:values from the  nested dict
  { prop1: { prop2: value }}, concatenating keys: { prop1.prop2: <value> }
  '''
    output_dict = {}
    if nested_dict is None:
        return {}
    if isinstance(nested_dict, str):
        return nested_dict.replace('\n', ' ')
    if isinstance(nested_dict, int) or isinstance(nested_dict, float):
        # value is a basic type. Keep it as is.
        return nested_dict
    if isinstance(nested_dict, list):
        nested_dict = {str(i): nested_dict[i] for i in range(len(nested_dict))}
    # Expand any nested values
    for key, value in nested_dict.items():
        key = flatten_dict(key)
        value = flatten_dict(value)
        if isinstance(value, dict):
            for nkey, nvalue in value.items():
                nvalue = flatten_dict(nvalue)
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


def file_json_to_csv(json_file: str, output_csv: str = '') -> str:
    '''Returns the CSV file generated from the json file.'''
    input_files = file_util.file_get_matching(json_file)
    if not input_files:
        return ''
    input_list = []
    for filename in input_files:
        file_dict = file_util.file_load_py_dict(filename)
        if isinstance(file_dict, list):
            input_list.extend(file_dict)
            logging.info(f'Loaded {len(file_dict)} items from {filename}')
        elif isinstance(file_dict, dict):
            input_list.append(file_dict)
            logging.info(f'Loaded row from {filename}')

    csv_rows = list_to_dict(input_list)
    if not output_csv:
        output_csv = file_util.file_get_name(input_files[-1], file_ext='.csv')
    logging.info(
        f'Writing {len(csv_rows)} rows from {input_files} into {output_csv}')
    file_util.file_write_csv_dict(csv_rows, output_csv)
    return output_csv


def main(_):
    if not _FLAGS.input_json:
        logging.error(
            f'Please provide a JSON file to be converted to CSV with --input_json'
        )
        return 1
    file_json_to_csv(_FLAGS.input_json, _FLAGS.csv_output)


if __name__ == '__main__':
    app.run(main)
