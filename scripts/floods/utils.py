# Copyright 2022 Google LLC
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
"""Utility functions"""

import glob
import os
import sys

from absl import logging
from geopy import distance
from s2sphere import LatLng, CellId
from typing import Union


# Utilities for dicts.
def dict_aggregate_values(src: dict, dst: dict, config: dict) -> dict:
    '''Aggregate values for keys in src dict into dst.
  The mode of aggregation (sum, mean, min, max) per property is
  defined in the config.
  Assumes properties to be aggregated have numeric values.

  Args:
    src: dictionary with property:value to be aggregated into dst
    dst: dictionary with property:value which is updated.
    config: dictionary with aggregation settings per property.
  Returns:
    dst dictionary with updated property:values.
  '''
    default_aggr = config.get('aggregate', 'sum')
    for prop, new_val in src.items():
        if prop not in dst:
            # Add new property to dst without any aggregation.
            dst[prop] = new_val
        else:
            aggr = config.get(prop, {}).get('aggregate', default_aggr)
            cur_val = dst[prop]
            if aggr == 'sum':
                dst[prop] = cur_val + new_val
            elif aggr == 'min':
                dst[prop] = min(cur_val, new_val)
            elif aggr == 'max':
                dst[prop] = max(cur_val, new_val)
            elif aggr == 'mean':
                cur_num = dst.get(f'#{prop}:count', 1)
                new_num = src.get(f'#{prop}:count', 1)
                dst[prop] = ((cur_val * cur_num) +
                             (new_val * new_num)) / (cur_num + new_num)
                dst[f'#{prop}:count'] = cur_num + new_num
            else:
                logging.fatal(
                    f'Unsupported aggregation: {aggr} for {src}, config: {config}'
                )
    return dst


# Utilities related to S2 Cells
def s2_cells_distance(cell1: int, cell2: int) -> float:
    '''Returns the distance between the centroid of the S2 cells.'''
    p1 = CellId(cell1).to_lat_lng()
    p2 = CellId(cell2).to_lat_lng()
    return distance.distance((p1.lat().degrees, p1.lng().degrees),
                             (p2.lat().degrees, p2.lng().degrees)).km


# Utilities for files.
def file_get_matching(filepat: str) -> list:
    '''Return a list of matching file names.
    Args:
      filepat: string with comma seperated list of file patterns to lookup
    Returns:
      list of matching filenames.
    '''
    files = list()
    # Get a list of input file patterns to lookup
    input_files = []
    if isinstance(filepat, str):
        input_files = filepat.split(',')
    if isinstance(filepat, list):
        for files in input_files:
            for file in files.split(','):
                if file not in input_files:
                    input_files.append(file)
    # Get all matching files for each file pattern.
    for file in input_files:
        for f in glob.glob(file):
            if f not in files:
                files.append(f)
    return sorted(files)


def file_estimate_num_rows(filename: str) -> int:
    '''Returns an estimated number of rows based on size of the first few rows.
    Args:
      filename: string name of the file.
    Returns:
      An estimated number of rows.
    '''
    filesize = os.path.getsize(filename)
    with open(filename) as fp:
        lines = fp.read(4000)
    line_size = max(len(lines) / (lines.count('\n') + 1), 1)
    return int(filesize / line_size)


def file_get_name(file_path: str,
                  suffix: str = '',
                  file_ext: str = '.csv') -> str:
    '''Returns the filename with suffix and extension.
    Creates the directory path for the file if it doesn't exist.
    Args:
      file_path: file path with directory and file name prefix
      suffix: file name suffix
      file_ext: file extension
    Returns:
      file name combined from path, suffix and extension.
    '''
    # Create the file directory if it doesn't exist.
    file_dir = os.path.dirname(file_path)
    if file_dir:
        os.makedirs(file_dir, exist_ok=True)
    file_prefix, ext = os.path.splitext(file_path)
    if file_prefix.endswith(suffix):
        # Suffix already present in name, ignore it.
        suffix = ''
    # Set the file extension
    if file_ext and file_ext[0] != '.':
        file_ext = '.' + file_ext
    return file_prefix + suffix + file_ext


# String utilities
def str_get_numeric_value(value: str) -> Union[int, float, None]:
    '''Returns the float value from string or None.'''
    if isinstance(value, int) or isinstance(value, float):
        return value
    if value and isinstance(value, str):
        try:
            normalized_value = value
            if (value[0].isdigit() or value[0] == '.' or value[0] == '-' or
                    value[0] == '+'):
                # Input looks like a number. Remove allowed extra characters.
                normalized_value = normalized_value.replace(',', '')
                if value.count('.') > 1:
                    # Period may be used instead of commas. Remove it.
                    normalized_value = normalized_value.replace('.', '')
            if value.count('.') == 1:
                return float(normalized_value)
            return int(normalized_value)
        except ValueError:
            # Value is not a number. Ignore it.
            return None
    return None
