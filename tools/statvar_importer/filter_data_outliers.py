# Copyright 2024 Google LLC
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
""" Utility functions to filter StatVarObservations.

To filter CSV with SVObs removing rows with value <= 1 or rows change > 500%,
run the command:
  python filter_data_outliers.py --filter_data_input=<input-csv> \
      --filter_data_output=<output-csv> \
      --filter_data_min_value=2 \
      --filter_data_max_change_ratio=5
"""

import calendar
import os
import sys

from absl import app
from absl import flags
from absl import logging
from datetime import datetime

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import file_util

from config_map import ConfigMap
from counters import Counters
from mcf_file_util import get_numeric_value

flags.DEFINE_string('filter_data_input', '',
                    'input CSV file with statvar observations')
flags.DEFINE_string('filter_data_output', '', 'output CSV file')
flags.DEFINE_float('filter_data_max_change_ratio', None,
                   'Maximum change alowed between successive values.')
flags.DEFINE_float('filter_data_max_yearly_change_ratio', None,
                   'Maximum change alowed between successive years.')
flags.DEFINE_float('filter_data_min_value', None, 'Minumum value allowed')
flags.DEFINE_float('filter_data_max_value', None, 'Maximum value allowed')
flags.DEFINE_list('data_series_value_properties', ['value'],
                  'Properties with the value to be checked')
flags.DEFINE_list(
    'data_series_date_properties', ['observationDate'],
    'Properties that can be used to sort values within a series such as date')
flags.DEFINE_bool('filter_data_keep_recent', True,
                  'Keep the most recent value for a time series.')

_FLAGS = flags.FLAGS


def get_default_filter_data_config() -> dict:
    '''Returns the default filter config settings form flags as dict.'''
    return {
        'filter_data_keep_recent':
            _FLAGS.filter_data_keep_recent,
        'filter_data_max_change_ratio':
            _FLAGS.filter_data_max_change_ratio,
        'filter_data_max_yearly_change_ratio':
            _FLAGS.filter_data_max_yearly_change_ratio,
        'filter_data_min_value':
            _FLAGS.filter_data_min_value,
        'filter_data_max_value':
            _FLAGS.filter_data_max_value,
        'data_series_value_properties':
            _FLAGS.data_series_value_properties,
        'data_series_date_properties':
            _FLAGS.data_series_date_properties,
    }


def filter_data_get_series_key(pvs: dict,
                               ignore_props={'observationDate',
                                             'value'}) -> str:
    '''Returns the key for timeseries for the pvs without date and value.'''
    key_tokens = []
    for prop in sorted(pvs.keys()):
        val = pvs[prop]
        if prop not in ignore_props:
            key_tokens.append(f'{prop}={val}')
    return ';'.join(key_tokens)


def filter_data_get_date_key(pvs: dict,
                             select_props: list = ['observationDate']) -> str:
    '''Return the value of the prop in the order of selected props.'''
    for prop in select_props:
        val = pvs.get(prop)
        if val is not None:
            return val
    return ''


def filter_data_get_value(pvs: dict, value_props: list = ['value']) -> float:
    '''Returns the numeric value from the pvs.'''
    value = None
    for prop in value_props:
        value = pvs.get(prop)
        if value is not None:
            return get_numeric_value(value)
    return value


def filter_data_series(data: dict,
                       min_value: float = None,
                       max_value: float = None,
                       max_change_ratio: float = None,
                       max_yearly_change: float = None,
                       keep_recent: bool = True,
                       counters: Counters = None,
                       value_props: list = ['value']) -> dict:
    '''Returns filtered values from series that pass thresholds.
    Scans data values in decreasing order of series key like date
    and compares the change in value against thresholds.

    Args:
      data: dictionary with values keyed by date
        { <date1>: { 'value': <number>, <prop1>: <value1>, ...},
          <date2>: { 'value': <number>, ... }
          ...
        }
      min_value: if not None, values lower than this are dropped.
      max_value: if not None, Values more than this are dropped.
      max_change_ratio: Maximum change in value compared to previous.
      counters: Counters object updated with drop counts
      value_props: list of properties in order to get numeric value from data

    Returns:
      data dictionary with entries with values not matching filter thresholds removed.
    '''
    if counters is None:
        counters = Counters()
    data_dropped = False
    prev_value = None
    prev_dt = None
    change_pct = None
    dates = sorted(list(data.keys()))
    if keep_recent:
        # process in reverse chronological order to keep most recent data.
        dates = reversed(dates)
    for date in dates:
        dt = _get_date_from_string(date)
        pvs = data[date]
        value = filter_data_get_value(pvs, value_props)
        allow = True
        if value is not None:
            if min_value is not None and value < min_value:
                allow = False
                counters.add_counter(f'filter-data-dropped-min-{min_value}', 1)
                logging.level_debug() and logging.debug(
                    f'Dropping date: {date} for {data}, {value} < {min_value}')
            if max_value is not None and value > max_value:
                allow = False
                counters.add_counter(f'filter-data-dropped-max-{max_value}', 1)
                logging.level_debug() and logging.debug(
                    f'Dropping date: {date} for {data}, {value} > {max_value}')
            if prev_value is not None:
                # Check if the data has changed too much
                change = abs(prev_value - value)
                change_pct = change / min(abs(prev_value), abs(value))
                if max_change_ratio is not None and change_pct > max_change_ratio:
                    allow = False
                    counters.add_counter(
                        f'filter-data-dropped-change-{max_change_ratio}', 1)
                    logging.level_debug() and logging.debug(
                        f'Dropping date: {date} for {data}, change_pct: {change_pct}'
                    )
                if max_yearly_change is not None:
                    years_diff = _get_years_difference(prev_dt, dt)
                    yearly_change = change_pct / years_diff
                    if yearly_change > max_yearly_change:
                        allow = False
                        counters.add_counter(
                            f'filter-data-dropped-change-yearly-{max_yearly_change}',
                            1)
                        logging.level_debug() and logging.debug(
                            f'Dropping date: {date} for {data}, yearly change_pct: {yearly_change} for {change_pct} over {years_diff} years'
                        )
        if not allow:
            # Remove date from series
            if '#Key' in pvs:
                pvs.pop('#Key')
            data.pop(date)
            data_dropped = True
            counters.add_counter(f'filter-data-dropped', 1)
        else:
            prev_value = value
            prev_dt = dt
    if data_dropped:
        counters.add_counter(f'filter-data-series-with-drops', 1)
    return data


def filter_data_svobs(svobs: dict,
                      config: ConfigMap = None,
                      counters: Counters = None) -> dict:
    '''Returns data filtered by svobs values.

    Args:
      svobs: dictionary of SVObs with 'value' key having the value
      config: COnfigMap with filter parameters:
        filter_data_min_value:
        filter_data_max_value
        filter_data_max_change_ratio
      counters: counters updated with filter counts
    '''
    if config is None:
        config = ConfigMap(get_default_filter_data_config())
    if counters is None:
        counters = Counters()

    filter_min = get_numeric_value(config.get('filter_data_min_value', None))
    filter_max = get_numeric_value(config.get('filter_data_max_value', None))
    filter_max_change = get_numeric_value(
        config.get('filter_data_max_change_ratio', None))
    filter_max_yearly_change = get_numeric_value(
        config.get('filter_data_max_yearly_change_ratio', None))
    filter_keep_recent = config.get('filter_data_keep_recent', True)
    if filter_max_change is None and filter_max is None and filter_min is None and filter_max_yearly_change is None:
        # No filtering required.
        return svobs

    # Group SVObs into time series
    # { <key> : { <date1> : <pvs>, <date2>: <pvs> ... }
    # where key is the concatenation of pvs except date and value.
    date_props = config.get('data_series_date_properties', ['observationDate'])
    value_props = config.get('data_series_value_properties', ['value'])
    ignore_props = set(date_props)
    ignore_props.update(value_props)
    series_svobs = {}
    for key, data_pvs in svobs.items():
        series_key = filter_data_get_series_key(data_pvs, ignore_props)
        date = filter_data_get_date_key(data_pvs, date_props)
        if series_key is None or date is None:
            counters.add_counter('filter-data-dropped-invalid-key', 1)
            continue
        series = series_svobs.get(series_key)
        if series is None:
            series = dict()
            series_svobs[series_key] = series
        # Copy the original key to restore filtered data
        data_pvs['#Key'] = key
        series[date] = data_pvs
    counters.add_counter('filter-data-input-series', len(series_svobs))
    logging.info(
        f'Filtering {len(series_svobs)} series with min: {filter_min}, max: {filter_max}, change: {filter_max_change}'
    )

    # Filter each time series
    filtered_series = {}
    for key, series in series_svobs.items():
        filter_data_series(series, filter_min, filter_max, filter_max_change,
                           filter_max_yearly_change, filter_keep_recent,
                           counters, value_props)
        for date, pvs in series.items():
            # Add the svobs PVs keyed by the input key.
            key = pvs.pop('#Key')
            filtered_series[key] = pvs

    return filtered_series


def filter_data_files(input_file: str,
                      output_file: str,
                      config: ConfigMap = None,
                      counters: Counters = None):
    '''Filter input data files with the config and save to output data file.

    Args:
      input_data: CSV files with a 'value' column
      output_date: output file for flitered data
      config: ConfigMap with config parameters for filtering.
      counters: dictionary of counters.
    '''

    if counters is None:
        counters = Counters()

    # Load csv data from input files into a dictionary per row.
    svobs = file_util.file_load_csv_dict(input_file, key_index=True)
    logging.info(f'Filtering {len(svobs)} rows from {input_file}')
    counters.add_counter('filter-data-inputs', len(svobs))
    filtered_data = filter_data_svobs(svobs, config, counters)
    counters.add_counter('filter-data-outputs', len(filtered_data))
    if output_file:
        file_util.file_write_csv_dict(filtered_data,
                                      output_file,
                                      key_column_name='')


def _get_date_from_string(dt_str: str) -> datetime:
    '''Returns a datetime object for the datetime.'''
    if not dt_str:
        return None
    tokens = dt_str.split('-')
    if len(tokens) >= 2:
        # Date has month and day. Parse ISO format.
        return datetime.fromisoformat(dt_str)
    # Date doesn't have day. Create a date from year and month.
    year = get_numeric_value(tokens[0])
    month = 12
    if len(tokens) > 1:
        month = get_numeric_value(tokens[1])
    first_day, last_day = calendar.monthrange(year, month)
    return datetime(year, month, last_day)


def _get_years_difference(dt1: datetime, dt2: datetime) -> float:
    '''Returns the difference between dates in years.'''
    dt_diff = dt1 - dt2
    return float(abs(dt_diff.days) / 365.0)


def main(_):
    logging.set_verbosity(1)
    filter_data_files(_FLAGS.filter_data_input, _FLAGS.filter_data_output)


if __name__ == '__main__':
    app.run(main)
