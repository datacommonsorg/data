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
"""Utility functions for aggregations on dictionaries and strings."""

from absl import logging
from typing import Union


def aggregate_value(src: Union[str, int, float, list, set],
                    dst: Union[str, int, float, list, set],
                    aggregate: str = 'sum') -> str:
    '''Return value aggregated from src and dst as per the aggregate setting.

    Args:
      src: value to be aggregated from source
      dst: value to be aggregated into from destination
      aggregate: string setting for aggregation method which is one of
        sum, min, max, list, first, last

    Returns:
      aggregated value
    '''
    value = None
    if isinstance(src, str) or isinstance(dst, str):
        if aggregate == 'sum':
            # Use list for combining string values.
            aggregate = 'list'
    elif isinstance(src, set) or isinstance(dst, set):
        # If values are sets, use set aggregation
        aggregate = 'set'
    if aggregate == 'sum':
        value = src + dst
    elif aggregate == 'min':
        value = min(src, dst)
    elif aggregate == 'max':
        value = max(src, dst)
    elif aggregate == 'list':
        # Create a comma separated list of unique values combining lists.
        value = set(str(src).split(','))
        value.update(str(dst).split(','))
        value = ','.join(sorted(value))
    elif aggregate == 'set':
        value = set(src)
        value.update(dst)
    elif aggregate == 'first':
        return src
    elif aggregate == 'last':
        return dst
    else:
        logging.fatal(f'Unsupported aggregation: {aggregate} for {src}, {dst}')
    return value


def aggregate_dict(src: dict, dst: dict, config: dict) -> dict:
    '''Aggregate values for keys in src dict into dst.
  The mode of aggregation  per property is defined in the config.
  The supported aggregations are: sum, mean, min, max, first, last, list, set
  Assumes values to be aggregated have the right types,
   such as numeric values for sum, mean aggregations,
   strings for list.
  The config defines a default aggregation as well as an aggregation per key
  in the form:
    { 'aggregate': 'sum', # default aggregation for keys without aggregate
      # Per key aggregations
      '<key1>: { 'aggregate': 'mean' },
      '<key2>: { 'aggregate': '

  Args:
    src: dictionary with property:value to be aggregated into dst
    dst: dictionary with property:value which is updated.
    config: dictionary with aggregation settings per property.

  Returns:
    dst dictionary with updated property:values.
  '''
    if config is None:
        config = {}
    default_aggr = config.get('aggregate', 'sum')
    for prop, new_val in src.items():
        try:
            if prop not in dst:
                # Add new property to dst without any aggregation.
                dst[prop] = new_val
            else:
                # Combine new value in src with current value in dst by aggregation.
                aggr = config.get(prop, {}).get('aggregate', default_aggr)
                cur_val = dst[prop]
                if isinstance(cur_val, str) or isinstance(new_val, str):
                    if aggr == 'mean':
                        # Use list for combining string values.
                        aggr = 'list'
                if aggr == 'mean':
                    # For mean, add a new property for counts.
                    cur_num = dst.get(f'#{prop}:count', 1)
                    new_num = src.get(f'#{prop}:count', 1)
                    dst[prop] = ((cur_val * cur_num) +
                                 (new_val * new_num)) / (cur_num + new_num)
                    dst[f'#{prop}:count'] = cur_num + new_num
                else:
                    dst[prop] = aggregate_value(cur_val, new_val, aggr)
        except TypeError as e:
            logging.fatal(
                f'Failed to aggregate values for {prop}: {new_val}, {cur_val}, Error: {e}'
            )
    return dst
