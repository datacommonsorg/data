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
'''Class to generate StatVar and StatVarObs from data files.

Create a file mapping data columns to a set of property-values.
See test_data/sample_column_map.py.

To process data files, run the following command:
  python3 stat_var_processor.py --input_data=<path-to-csv> \
      --pv_map=<column-pv-map-file> \
      --output_path=<output-prefix>

This will generate the following outputs:
  <output-prefix>.mcf: MCF file with StatVar definitions.
  <output-prefix>.csv: CSV file with StatVarObservations.
  <output-prefix>.tmcf: MCF file mapping CSV columns to StatVar PVs.
'''

import ast
import csv
import datetime
import glob
import itertools
import multiprocessing
import os
import pandas as pd
import re
import requests
import sys
import time
import traceback

from absl import app
from absl import flags
from absl import logging
from collections import OrderedDict
#from pypprof.net_http import start_pprof_server

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.join(_SCRIPT_DIR,
                             '../../util/'))  # for statvar_dcid_generator

from mcf_file_util import load_mcf_nodes, write_mcf_nodes, add_namespace, strip_namespace
from mcf_filter import dc_api_get_defined_dcids
import statvar_dcid_generator

_FLAGS = flags.FLAGS

flags.DEFINE_string('config', '', 'File with configuration parameters.')
flags.DEFINE_list('data_url', '', 'URLs to download the data from.')
flags.DEFINE_string('shard_input_by_column', '',
                    'Shard input data by unique values in column.')
flags.DEFINE_string('shard_prefix_length', '',
                    'Shard input data by value prefix of given length.')
flags.DEFINE_list(
    'pv_map', [],
    'Comma separated list of namespace:file with property values.')
flags.DEFINE_list('input_data', [],
                  'Comma separated list of data files to be processed.')
flags.DEFINE_integer(
    'input_rows', -1,
    'Number of rows per input file to process. Default: -1 for all rows.')
flags.DEFINE_integer(
    'skip_rows', 0, 'Number of rows to skip at the begining of the input file.')
flags.DEFINE_integer(
    'header_rows', -1,
    'Number of header rows with property-value mappings for columns. If -1, will lookup PVs for all rows.'
)
flags.DEFINE_integer(
    'header_columns', -1,
    'Number of header columns with property-value mappings for rows. If -1, will lookup PVs for all columns.'
)
flags.DEFINE_string(
    'aggregate_duplicate_svobs', '',
    'Aggregate SVObs with same place, date by one of the following: sum, min or max.'
)
flags.DEFINE_bool('schemaless', False, 'Allow schemaless StatVars.')
flags.DEFINE_string('output_path', '',
                    'File prefix for output mcf, csv and tmcf.')
flags.DEFINE_integer('parallelism', 0, 'Number of parallel processes to use.')
flags.DEFINE_integer('pprof_port', 0, 'HTTP port for pprof server.')
flags.DEFINE_bool('debug', False, 'Enable debug messages.')
flags.DEFINE_integer('log_level', logging.INFO,
                     'Log level messages to be shown.')
_FLAGS(sys.argv)  # Allow invocation without app.run()

# Enable debug messages
_DEBUG = True

# Dictionary of config parameters and values.
_DEFAULT_CONFIG = {
    # 'config parameter in snake_case': value
    'ignore_numeric_commas':
        True,  # Numbers may have commas
    'input_reference_column':
        '#input',
    'input_min_columns_per_row':
        3,
    'pv_map_drop_undefined_nodes':
        False,  # Don't drop undefined PVs in the column PV Map.
    'duplicate_svobs_key':
        '#ErrorDuplicateSVObs',
    'duplicate_statvars_key':
        '#ErrorDuplicateStatVar',
    'drop_statvars_without_obs':
        True,
    # Aggregate values for duplicate SVObs with the same statvar, place, date
    # and units with one of the following functions:
    #   sum: Add all values.
    #   min: Set the minimum value.
    #   max: Set the maximum value.
    # Internal property in PV map to aggregate values for a specific statvar.
    'aggregate_key':
        '#Aggregate',
    # Aggregation type duplicate SVObs for all statvars.
    'aggregate_duplicate_svobs':
        None,
    'merged_pvs_property':
        '#MergedSVObs',

    # Enable schemaless StatVars,
    # If True, allow statvars with capitalized property names.
    # Those properties are commented out when generating MCF but used for
    # statvar dcid.
    'schemaless':
        _FLAGS.schemaless,
    # Whether to lookup DC API and drop undefined PVs in statvars.
    'schemaless_statvar_comment_undefined_pvs':
        False,
    'default_statvar_pvs':
        OrderedDict({
            'typeOf': 'dcs:StatisticalVariable',
            'measurementQualifier': '',
            'statType': 'dcs:measuredValue',
            'measuredProperty': 'dcs:count',
            'populationType': ''
        }),
    'statvar_dcid_ignore_values': ['measuredValue', 'StatisticalVariable'],
    'default_svobs_pvs':
        OrderedDict({
            'typeOf': 'dcs:StatVarObservation',
            'observationDate': '',
            'observationAbout': '',
            'value': '',
            'observationPeriod': '',
            'measurementMethod': '',
            'unit': '',
            'scalingFactor': '',
            'variableMeasured': '',
            '#Aggregate': '',
        }),
    'required_statvar_properties': [
        'measuredProperty',
        'populationType',
    ],
    'required_statvarobs_properties': [
        'variableMeasured', 'observationAbout', 'observationDate', 'value'
    ],
    # Use numeric data in any column as a value.
    # It may still be dropped if no SVObs can be constructed out of it.
    # If False, SVObs is only emitted for PVs that have a map for 'value',
    # for example, 'MyColumn': { 'value': '@Data' }
    'use_all_numeric_data_values':
        False,
    # Word separator, used to split words into phrases for PV map lookups.
    'word_delimiter':
        ' ',
    'show_counters_every_n':
        0,
    'show_counters_every_sec':
        30,
    # Output options
    'generate_statvar_mcf':
        True,  # Generate MCF file with all statvars
    'generate_csv':
        True,  # Generate CSV with SVObs
    'output_csv_mode':
        'w',  # Overwrite output CSV file.
    'output_csv_columns':
        None,  # Emit all SVObs PVs into output csv
    'generate_tmcf':
        True,  # Generate tMCF for CSV columns
    'skip_constant_csv_columns':
        False,  # Skip emitting columns with constant values in the csv

    # Settings for DC API.
    'dc_api_root':
        'http://autopush.api.datacommons.org',
    'dc_api_use_cache':
        False,
    'dc_api_batch_size':
        100,
}


def _get_config_from_flags() -> dict:
    '''Returns a dictionary of config options from command line flags.'''
    _DEBUG = _FLAGS.debug
    return {
        # 'flag_name':  _FLAGS.flag_name
        'pv_map':
            _FLAGS.pv_map,
        'data_url':
            _FLAGS.data_url,
        'shard_input_by_column':
            _FLAGS.shard_input_by_column,
        'shard_prefix_length':
            _FLAGS.shard_prefix_length,
        'input_rows':
            _FLAGS.input_rows,
        'skip_rows':
            _FLAGS.skip_rows,
        'header_rows':
            _FLAGS.header_rows,
        'header_columns':
            _FLAGS.header_columns,
        'schemaless':
            _FLAGS.schemaless,
        'debug':
            _FLAGS.debug,
        'log_level':
            max(_FLAGS.log_level, logging.DEBUG if _FLAGS.debug else 0),
    }


def get_py_dict_from_file(filename: str) -> dict:
    '''Load a python dict from a file.
    Args:
      filename: JSON or a python file containing parameter to value mappings.
    '''
    logging.info(f'Loading python dict from {filename}...')
    with open(filename) as file:
        pv_map_str = file.read()


# Load the map assuming a python dictionary.
# Can also be used with JSON with trailing commas and comments.
    param_dict = ast.literal_eval(pv_map_str)
    _DEBUG and logging.debug(f'Loaded {filename} into dict {param_dict}')
    return param_dict


def is_valid_property(prop: str, schemaless: bool = False) -> bool:
    '''Returns True if the property begins with a letter, lowercase if schemaless.'''
    if prop and isinstance(prop, str) and prop[0].isalpha():
        if schemaless or prop[0].islower():
            return True
    return False


def is_valid_value(value: str) -> bool:
    '''Returns True is the value is a valid property value without any references.'''
    if not value:
        return False
    if isinstance(value, str):
        # Check there are no unresolved references.
        if '@' in value:
            return False
        if '{' in value and '}' in value:
            return False
    return True


def is_schema_node(value: str) -> bool:
    '''Returns True is the value is a schema node reference.'''
    if not value or not isinstance(value, str):
        return False
    if not value[0].isalpha() and value[0] != '[':
        # Numbers or quoted strings are not schema nodes.
        return False
    # Check if string has any non alpha or non numeric codes
    non_alnum_chars = [
        c for c in strip_namespace(value)
        if not c.isalnum() and c != '_' and c != '/'
    ]
    if non_alnum_chars:
        return False
    return True


def get_numeric_value(value: str) -> float:
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


def get_words(value: str, word_delimiter: str) -> list:
    '''Returns the list of non-empty words separated by the delimiter.'''
    return [w for w in re.split(word_delimiter, value) if w]


def add_key_value(key: str,
                  value: str,
                  pvs: dict,
                  multi_value_keys: set = {},
                  overwrite: bool = True) -> dict:
    '''Adds a key:value to the dict.
    If the key already exists, adds value to a list if key is a multi_value key,
    else replaces the value.'''
    if key not in pvs:
        pvs[key] = value
    else:
        if key not in multi_value_keys:
            # Replace existing value with a new one.
            if overwrite:
                pvs[key] = value
        else:
            # This key can have multiple values. Add if it doesn't exist already.
            new_values = set()
            if isinstance(value, list):
                new_values.update(value)
            else:
                new_values.add(value)
            current_value = pvs[key]
            if isinstance(current_value, list):
                new_values.update(current_value)
            else:
                new_values.add(current_value)
            pvs[key] = list(new_values)
    return pvs


def pvs_update(new_pvs: dict, pvs: dict, multi_value_keys: set = {}) -> dict:
    '''Add the key:value pairs from the new_pvs into the pvs.'''
    for prop, value in new_pvs.items():
        add_key_value(prop, value, pvs, multi_value_keys)
    return pvs


class Config:
    '''Class to store config mapping of named parameters to values.'''

    def __init__(self, config_dict: dict = None, filename: str = None):
        self._config_dict = dict(_DEFAULT_CONFIG)
        self.add_configs(_get_config_from_flags())
        if config_dict:
            self._config_dict.update(config_dict)
        if filename:
            self.load_config_file(filename)
        logging.set_verbosity(self.get_config('log_level'))
        _DEBUG and logging.debug(f'Using config: {self.get_configs()}')

    def load_config_file(self, filename: str):
        '''Load configs from a file.'''
        self.add_configs(get_py_dict_from_file(filename))

    def add_configs(self, configs: dict):
        '''Add new or replace existing config parameters.'''
        self._config_dict.update(configs)

    def get_config(self, parameter: str, default_value=None) -> str:
        '''Return the value of a named config parameter.'''
        return self._config_dict.get(parameter, default_value)

    def get_configs(self) -> dict:
        return self._config_dict

    def set_config(self, name: str, value):
        self._config_dict[name] = value


def get_config_from_file(filename: str) -> Config:
    '''Returns configs loaded from a file.'''
    return Config(filename=filename)


class Counters():
    '''Dictionary of named counters.'''

    def __init__(self,
                 counters_dict: dict = None,
                 debug: bool = False,
                 config_dict: dict = None):
        self._counters = counters_dict
        self._debug = debug
        if counters_dict is None:
            self._counters = {}
        self._counter_config = config_dict
        if config_dict is None:
            self._counter_config = {}
        self._num_calls = 0
        self._show_counters_every_n = self._counter_config.get(
            'show_counters_every_n', 0)
        self._show_counters_every_secs = self._counter_config.get(
            'show_counters_every_sec', 0)

    def add_counter(self, name: str, value: int = 1, context: str = None):
        '''Increment a named counter by the given value.'''
        self._counters[name] = self._counters.get(name, 0) + value
        if context and self._debug:
            ext_name = f'{name}-{context}'
            self._counters[ext_name] = self._counters.get(ext_name, 0) + value
        self._num_calls += 1
        self.show_counters_periodically()

    def set_counter(self, name: str, value: int, context: str = None):
        self._counters[name] = 0
        self.add_counter(name, value, context)

    def get_counters(self):
        return self._counters

    def get_counter(self, name: str) -> int:
        return self._counters.get(name, 0)

    def get_counters_string(self) -> str:
        lines = ['Counters:']
        for c in sorted(self._counters.keys()):
            v = self._counters[c]
            if isinstance(v, int):
                lines.append(f'{c:>50s} = {v:>10d}')
            elif isinstance(v, float):
                lines.append(f'{c:>50s} = {v:>10.2f}')
            else:
                lines.append(f'{c:>50s} = {v}')

        return '\n'.join(lines)

    def show_counters(self, file=sys.stderr):
        print(self.get_counters_string(), file=file)

    def show_counters_periodically(self):
        # Show counters periodically.
        if self._show_counters_every_n > 0 and self._num_calls % self._show_counters_every_n:
            self.show_counters()
        else:
            if self._show_counters_every_secs and (
                    time.perf_counter() -
                    self._last_display_time) > self._show_counters_every_secs:
                self.show_counters()
                self._last_display_time = time.perf_counter()

    def log_counters(self):
        logging.info(self.get_counters_string())


class PropertyValueMapper(Config, Counters):
    '''Class to map strings to set of property values.
  Supports multiple maps with a namespace or context string.
  '''

    def __init__(self,
                 pv_map_files: list = [],
                 config_dict: dict = None,
                 counters_dict: dict = None):
        Config.__init__(self, config_dict=config_dict)
        Counters.__init__(self,
                          counters_dict=counters_dict,
                          debug=self.get_config('debug', False))
        # Map from a namespace to dictionary of string-> { p:v}
        self._pv_map = OrderedDict({'GLOBAL': {}})
        self._num_pv_map_keys = 0
        self._max_words_in_keys = 0
        for filename in pv_map_files:
            namespace = 'GLOBAL'
            if ':' in filename:
                namespace, filename = filename.split(':', 1)
            self.load_pvs_from_file(filename, namespace)
        _DEBUG and logging.debug(
            f'Loaded PV map {self._pv_map} with max words {self._max_words_in_keys}'
        )

    def load_pvs_from_file(self, filename: str, namespace: str = 'GLOBAL'):
        '''Loads a map from string -> { P: V }.
    File is a python dictionary or a JSON file with python equivalents
    such as True(true), False(false), None(null).'''
        _DEBUG and logging.debug(f'Loading PV map from {filename}...')
        if namespace not in self._pv_map:
            self._pv_map[namespace] = {}

        # Append new PVs to existing map.
        pv_map_input = get_py_dict_from_file(filename)
        pv_map = self._pv_map[namespace]
        word_delimiter = self.get_config('word_delimiter', ' ')
        num_keys_added = 0
        for key, pvs_input in pv_map_input.items():
            if key not in pv_map:
                pv_map[key] = {}
            pvs_dict = pv_map[key]
            if isinstance(pvs_input, str):
                pvs_input = {namespace: pvs_input}
            for p, v in pvs_input.items():
                if p in pvs_dict:
                    # Concatenate new value to existing one with '__'
                    if v not in pvs_dict[p]:
                        pvs_dict[p] = '__'.join(sorted([pvs_dict[p], v]))
                        logging.info(
                            f'Joining values for {key}[{p}] into {pvs_dict[p]}')
                else:
                    pvs_dict[p] = v
                    num_keys_added += 1
            num_words_key = len(get_words(key, word_delimiter))
            self._max_words_in_keys = max(self._max_words_in_keys,
                                          num_words_key)
            _DEBUG and logging.log(2, f'Setting PVMap[{key}] = {pvs_dict}')

        self._num_pv_map_keys += num_keys_added
        logging.info(
            f'Loaded {num_keys_added} property-value mappings for "{namespace}" from {filename}'
        )
        _DEBUG and logging.debug(f'Loaded pv map {namespace}:{pv_map_input}')

    def get_pv_map(self) -> dict:
        return self._pv_map

    def process_pvs_for_data(self, key: str, pvs: dict) -> bool:
        '''Returns true if PVs are processed successfully.
      Processes actionable props such as '#Regex', '#Eval', '#Format'.
      '''
        _DEBUG and logging.debug(f'Processing data PVs:{key}:{pvs}')
        data_key = self.get_config('data_key', '@Data')
        data = pvs.get(data_key, key)
        is_modified = False

        # Process regular expression and collect named group matches in the PV.
        regex_key = self.get_config('regex_key', '#Regex')
        if regex_key in pvs and data:
            re_pattern = pvs[regex_key]
            re_matches = re.finditer(re_pattern, data)
            regex_pvs = {}
            for match in re_matches:
                regex_pvs.update(match.groupdict())
            _DEBUG and logging.debug(
                f'Processed regex: {re_pattern} on {key}:{data} to get {regex_pvs}'
            )
            if regex_pvs:
                self.add_counter('processed-regex', 1, re_pattern)
                pvs_update(regex_pvs, pvs,
                           self.get_config('multi_value_properties', {}))
                pvs.pop(regex_key)
                is_modified = True

        # Format the data substituting properties with values.
        format_key = self.get_config('format_key', '#Format')
        if format_key in pvs:
            format_str = pvs[format_key]
            format_data = format_str.format(**pvs)
            _DEBUG and logging.debug(
                f'Processed format {format_str} on {key}:{data} to get {format_data}'
            )
            if format_data != data:
                pvs[data_key] = format_data
                self.add_counter('processed-format', 1, format_str)
                pvs.pop(format_key)
                is_modified = True

        # Evaluate the expression properties as local variables.
        eval_key = self.get_config('eval_key', '#Eval')
        if eval_key in pvs:
            eval_str = pvs[eval_key]
            eval_data = eval(eval_str, {}, pvs)
            _DEBUG and logging.debug(
                f'Processed eval {eval_str} on {key}:{data} to get {eval_data}')
            if eval_data != data:
                pvs[data_key] = eval_data
                self.add_counter('processed-eval', 1, eval_str)
                pvs.pop(eval_key)
                is_modified = True
        return is_modified

    def get_pvs_for_key(self, key: str, namespace: str = 'GLOBAL') -> dict:
        '''Return a dict of property-values for the given key.'''
        pvs = None
        if namespace in self._pv_map:
            pvs = self._pv_map[namespace].get(key, None)
        else:
            # Check if key is unique and exists in any other map.
            dicts_with_key = []
            pvs = {}
            for namespace, pv_map in self._pv_map.items():
                if key in pv_map:
                    dicts_with_key.append(namespace)
                    pvs_update(pv_map[key], pvs,
                               self.get_config('multi_value_properties', {}))
            if len(dicts_with_key) > 1:
                logging.warning(
                    f'Duplicate key {key} in property maps: {dicts_with_key}')
                self.add_counter(f'warning-multiple-property-key', 1,
                                 f'{key}:' + ','.join(dicts_with_key))
        if not pvs:
            _DEBUG and logging.log(3, f'Missing key {key} in property maps')
            self.add_counter(f'warning-missing-property-key', 1, key)
            return pvs
        _DEBUG and logging.log(3, f'Got PVs for {key}:{pvs}')
        return pvs

    def is_key_in_value(self, key: str, value: str) -> bool:
        '''Returns True is key is found inside value string.'''
        if self.get_config('match_substring_word_boundary', True):
            # Match substring around word boundaries.
            key_pat = f'\\b{key}\\b'
            if re.match(key_pat, value):
                return True
            else:
                return False
        # Simple substring without b=word boundary checks.
        if key in value:
            return True
        return False

    def get_pvs_for_key_substring(self,
                                  value: str,
                                  namespace: str = 'GLOBAL') -> dict:
        '''Return a dict of property-values for any key is a substring of value.'''
        namespaces = []
        if namespace and namespace in self._pv_map:
            namespaces.append(namespace)
        else:
            namespaces = list(self._pv_map.keys())
        pvs_list = []
        keys_list = []
        for n in namespaces:
            # Lookup keys from shortest to longest.
            # Caller will merge PVs in the reverse order.
            pv_map = self._pv_map[n]
            sorted_keys = sorted(pv_map.keys(), key=len, reverse=False)
            for key in sorted_keys:
                if self.is_key_in_value(key, value):
                    pvs_list.append(pv_map[key])
                    keys_list.append(key)
                    value.replace(key, '')
        _DEBUG and logging.debug(
            f'Returning pvs for substrings of {value} from {keys_list}:{pvs_list}'
        )
        return pvs_list

    def get_all_pvs_for_value(self,
                              value: str,
                              namespace: str = 'GLOBAL',
                              max_fragment_size: int = None) -> list:
        '''Process a single data cell from a row:column and return set of PVs in the output.'''
        _DEBUG and logging.log(3, f'Looking up PVs for {namespace}:{value}')
        if not value:
            return None
        pvs = self.get_pvs_for_key(value, namespace)
        if pvs:
            return [pvs]
        # Check if GLOBAL map has key namesapce:column-value
        pvs = self.get_pvs_for_key(f'{namespace}:{value}')
        if pvs:
            return [pvs]
        pvs = self.get_pvs_for_key(value.lower(), namespace)
        if pvs:
            return [pvs]
        # Split the value into n-grams and lookup PVs for each fragment.
        word_delimiter = self.get_config('word_delimiter', ' ')
        word_joiner = word_delimiter.split('|')[0]
        #words = value.split(word_delimiter)
        words = get_words(value, word_delimiter)
        if len(words) <= 1:
            return None
        max_fragment_words = len(words) - 1
        if not max_fragment_size:
            max_fragment_size = self._max_words_in_keys
        max_fragment_words = min(max_fragment_words, max_fragment_size)

        num_grams = ((len(words) - max_fragment_size)**2)
        if self._num_pv_map_keys < num_grams:
            # Fewer keys than n-grams in input.
            # Get PVs for keys in pv_map that are a substring of the input value.
            return self.get_pvs_for_key_substring(value, namespace)
        # Fewer n-grams than number of keys in map.
        # Check if any input n-gram matches a key.
        _DEBUG and logging.log(
            2, f'Looking up PVs for {max_fragment_words} words in {words}')
        for num_words in range(max_fragment_words, 0, -1):
            for start_index in range(0, len(words) - num_words + 1):
                sub_value = word_joiner.join(words[start_index:start_index +
                                                   num_words])
                sub_pvs = self.get_all_pvs_for_value(sub_value, namespace)
                if sub_pvs:
                    # Got PVs for a fragment.
                    # Also lookup remaining fragments before and after this.
                    pvs_list = []
                    before_value = word_delimiter.join(words[0:start_index])
                    before_pvs = self.get_all_pvs_for_value(
                        before_value, namespace, max_fragment_size=num_words)
                    after_value = word_delimiter.join(words[start_index +
                                                            num_words:])
                    after_pvs = self.get_all_pvs_for_value(
                        after_value, namespace, max_fragment_size=num_words)
                    if before_pvs:
                        pvs_list.extend(before_pvs)
                    pvs_list.extend(sub_pvs)
                    if after_pvs:
                        pvs_list.extend(after_pvs)
                    return pvs_list
        return None


# PVs for StatVarObs ignored when looking for dups
_IGNORE_SVOBS_KEY_PVS = {
    'value': '',
}


class StatVarsMap(Config, Counters):
    '''Class to store statvars and statvar obs in a map.'''

    def __init__(self, config_dict: dict = None, counters_dict: dict = None):
        Config.__init__(self, config_dict=config_dict)
        Counters.__init__(self,
                          counters_dict=counters_dict,
                          debug=self.get_config('debug', False))
        # Dictionary of statvar dcid->{PVs}
        self._statvars_map = {}
        # Dictionary of statvar obs_key->{PVs}
        self._statvar_obs_map = {}
        self._statvar_obs_props = dict()  # Properties across SVObs.
        # Cache for DC API lookups.
        self._dc_api_ids_cache = {}

    def add_default_pvs(self, pvs: dict, default_pvs: dict) -> dict:
        '''Add default values for any missing PVs.'''
        for prop, value in default_pvs.items():
            if is_valid_property(prop, self.get_config(
                    'schemaless', False)) and value and prop not in pvs:
                pvs[prop] = value
        return pvs

    def get_valid_pvs(self, pvs: dict) -> dict:
        '''Return all valid PVs.'''
        valid_pvs = {}
        for prop, value in pvs.items():
            if is_valid_property(prop, self.get_config(
                    'schemaless', False)) and is_valid_value(value):
                valid_pvs[prop] = value
        return valid_pvs

    def add_dict_to_map(self,
                        key: str,
                        pvs: dict,
                        pv_map: dict,
                        duplicate_prop: str = None,
                        allow_equal_pvs: bool = True) -> bool:
        '''Returns true if the key is added,
        False if key already exists and values don't match.'''
        if key in pv_map:
            if allow_equal_pvs and self.get_valid_pvs(
                    pvs) == self.get_valid_pvs(pv_map[key]):
                return True
            else:
                _DEBUG and logging.debug(
                    f'Duplicate entry {key} in map for {pvs}')
                if duplicate_prop:
                    map_pvs = pv_map[key]
                    if duplicate_prop not in map_pvs:
                        map_pvs[duplicate_prop] = []
                    map_pvs[duplicate_prop].append(pvs)
                return False
        pv_map[key] = pvs
        return True

    def get_value_term(self, prop: str, value: str) -> str:
        '''Returns the dcid term for the value.'''
        if not value:
            return ''
        if not isinstance(value, str):
            return str(value)
        prefix = ''
        if self.get_config('schemaless', False):
            # Add the property prefix for schemaless PVs.
            if prop and isinstance(prop,
                                   str) and prop[0].isupper() and prop != value:
                prefix = f'{prop}_'
        value = strip_namespace(value)
        if value[0] == '[':
            # Generate term for quantity range with start and optional end, unit.
            quantity_pat = r'\[ *(?P<unit1>[A-Z][A-Za-z0-9_/]*)? *(?P<start>[0-9]+|-)? *(?P<end>[0-9]+|-)? *(?P<unit2>[A-Z][A-Za-z0-9_]*)? *\]'
            matches = re.search(quantity_pat, value)
            if matches:
                match_dict = matches.groupdict()
                if match_dict:
                    start = match_dict.get('start', None)
                    end = match_dict.get('end', None)
                    unit1 = match_dict.get('unit1', None)
                    unit2 = match_dict.get('unit2', None)
                    if unit1:
                        unit = f'{unit1}'
                    elif unit2:
                        unit = f'{unit2}'
                    value_term = ''
                    if start == '-' and end:
                        value_term = f'{end}OrLess'
                    elif start and end == '-':
                        value_term = f'{start}OrMore'
                    elif not end:
                        value_term = f'{start}'
                    else:
                        value_term = f'{start}To{end}'
                    value_term += unit
                    return prefix + value_term
        return prefix + value[0].upper() + value[1:]

    def generate_statvar_dcid(self, pvs: dict) -> str:
        '''Return the dcid for the statvar.'''

        dcid = pvs.get('Node', '')
        dcid = pvs.get('dcid', dcid)
        if dcid:
            return dcid
        # Create a new dcid from PVs.
        return statvar_dcid_generator.get_statvar_dcid(pvs)
        dcid_terms = []
        props = list(pvs.keys())
        dcid_ignore_values = self.get_config('statvar_dcid_ignore_values', [])
        for p in self.get_config('default_statvar_pvs', {}).keys():
            if p in props:
                props.remove(p)
                value = strip_namespace(pvs[p])
                if value and value not in dcid_ignore_values:
                    dcid_terms.append(self.get_value_term(p, value))
        dcid_suffixes = []
        if 'measurementDenominator' in props:
            dcid_suffixes.append('AsAFractionOf')
            dcid_suffixes.append(strip_namespace(pvs['measurementDenominator']))
            props.remove('measurementDenominator')
        for p in sorted(props, key=str.casefold):
            value = pvs[p]
            if is_valid_property(p, self.get_config(
                    'schemaless', False)) and is_valid_value(value):
                dcid_terms.append(self.get_value_term(p, value))
        dcid_terms.extend(dcid_suffixes)
        dcid = re.sub(r'[^A-Za-z_0-9/]', '_', '_'.join(dcid_terms))
        pvs['Node'] = add_namespace(dcid)
        _DEBUG and logging.debug(f'Generated dcid {dcid} for {pvs}')
        return dcid

    def remove_undefined_properties(
            self,
            pv_map_dict: dict,
            ignore_props: list = [],
            comment_removed_props: bool = False) -> list:
        '''Remove any property:value tuples with undefined property or values
        Returns list of properties removed.'''
        # Collect all PVs to be checked.
        props_removed = []
        lookup_dcids = set()
        for namespace, pv_map in pv_map_dict.items():
            for key, pvs in pv_map.items():
                # Add Node dcids as defined in cache.
                dcid = pvs.get('Node', '')
                dcid = pvs.get('Node', dcid)
                if dcid:
                    dcid = strip_namespace(dcid)
                    self._dc_api_ids_cache[dcid] = True
                # Collect property and values not in cache and to be looked up.
                for prop, value in pvs.items():
                    if value:
                        value = strip_namespace(value)
                    if prop in ignore_props:
                        continue
                    if is_valid_property(prop,
                                         self.get_config('schemaless', False)):
                        lookup_dcids.add(prop)
                    if is_schema_node(value):
                        lookup_dcids.add(value)

        # Lookup new Ids on the DC API.
        if lookup_dcids:
            api_lookup_dcids = [
                dcid for dcid in lookup_dcids
                if dcid not in self._dc_api_ids_cache
            ]
            if api_lookup_dcids:
                _DEBUG and logging.debug(
                    f'Looking up DC API for dcids: {api_lookup_dcids} from PV map.'
                )
                schema_nodes = dc_api_get_defined_dcids(api_lookup_dcids,
                                                        self.get_configs())
                # Update cache
                self._dc_api_ids_cache.update(schema_nodes)
                _DEBUG and logging.debug(
                    f'Got {len(schema_nodes)} of {len(api_lookup_dcids)} dcids from DC API.'
                )

        # Remove any PVs not in schema.
        counter_prefix = 'error-pvmap-dropped'
        if comment_removed_props:
            counter_prefix = 'commented-pvmap'
        for namespace, pv_map in pv_map_dict.items():
            for key, pvs in pv_map.items():
                for prop in list(pvs.keys()):
                    if prop in ignore_props:
                        continue
                    value = strip_namespace(pvs[prop])
                    if prop in lookup_dcids and not self._dc_api_ids_cache.get(
                            prop, False):
                        logging.error(
                            f'Removing undefined property "{prop}" from PV Map:{namespace}:{key}:{prop}:{value}'
                        )
                        value = pvs.pop(prop)
                        if comment_removed_props:
                            pvs[f'# {prop}: '] = value
                        self.add_counter(f'{counter_prefix}-undefined-property',
                                         1, prop)
                    if value in lookup_dcids and not self._dc_api_ids_cache.get(
                            value, False):
                        logging.error(
                            f'Removing undefined value "{value}" from PV Map:{namespace}:{key}:{prop}:{value}'
                        )
                        if prop in pvs:
                            pvs.pop(prop)
                        if comment_removed_props:
                            pvs[f'# {prop}: '] = value
                            props_removed.append(prop)
                        self.add_counter(f'{counter_prefix}-undefined-value', 1,
                                         prop)
                self.add_counter(f'pvmap-defined-properties', len(pvs))
        return props_removed

    def convert_to_schemaless_statvar(self, pvs: dict) -> dict:
        '''Converts a dictionary of property values to schemaless StatVar
        and returns True if pvs are modified.
        If there are properties starting with capital letters,
        they are commented and measuredProperty is set to the statvar dcid.'''
        _DEBUG and logging.debug(f'Converting to schemaless statvar {pvs}')
        schemaless_props = []
        for prop in pvs.keys():
            if prop != 'Node' and not is_valid_property(
                    prop, schemaless=False) and is_valid_property(
                        prop, schemaless=True):
                schemaless_props.append(prop)

        # Got some capitalized properties.
        # Convert to schemaless PV:
        # - set measuredProperty to the dcid.
        # - comment out any capitalized (invalid) property
        dcid = self.generate_statvar_dcid(pvs)
        for prop in schemaless_props:
            value = pvs.pop(prop)
            pvs[f'# {prop}: '] = value
        # Comment out any PVs with undefined property or value.
        if self.get_config('schemaless_statvar_comment_undefined_pvs', False):
            schemaless_props.extend(
                self.remove_undefined_properties({'StatVar': {
                    'SV': pvs
                }},
                                                 ignore_props=['Node'],
                                                 comment_removed_props=True))
        _DEBUG and logging.debug(f'Generated schemaless statvar {pvs}')
        if schemaless_props:
            # Found some schemaless properties. Change mProp to statvar dcid.
            if 'measuredProperty' in pvs:
                pvs['# measuredProperty:'] = pvs.pop('measuredProperty')
            pvs['measuredProperty'] = add_namespace(dcid)
            return True
        return False

    def add_statvar(self, statvar_pvs: dict) -> bool:
        '''Add unique statvars.'''
        pvs = self.get_valid_pvs(statvar_pvs)
        statvar_dcid = strip_namespace(self.generate_statvar_dcid(pvs))
        is_schemaless = False
        if self.get_config('schemaless', False):
            is_schemaless = self.convert_to_schemaless_statvar(pvs)
        if not self.add_dict_to_map(statvar_dcid, pvs, self._statvars_map,
                                    self.get_config('duplicate_statvars_key')):
            logging.error(
                f'Cannot add duplicate statvars for {statvar_dcid}: old: {self._statvars_map[statvar_dcid]}, new: {pvs}'
            )
            self.add_counter(f'error-duplicate-statvars', 1, statvar_dcid)
            return False
        # Check if the required properties are present.
        missing_props = set(self.get_config('required_statvar_properties',
                                            [])).difference(set(pvs.keys()))
        if missing_props:
            logging.error(
                f'Missing statvar properties {missing_props} in {pvs}')
            self.add_counter(f'error-statvar-missing-property', 1,
                             f'{statvar_dcid}:missing-{missing_props}')
            pvs['#ErrorMissingStatVarProperties'] = missing_props
            return False
        _DEBUG and logging.debug(f'Adding statvar {pvs}')
        self.add_counter('generated-statvars', 1, statvar_dcid)
        if is_schemaless:
            self.add_counter('generated-statvars-schemaless', 1, statvar_dcid)
        return True

    def get_svobs_key(self, pvs: dict) -> str:
        '''Returns the key for SVObs concatenating all PVs, except place, date and value.'''
        key_pvs = [
            f'{p}={pvs[p]}' for p in sorted(pvs.keys())
            if is_valid_property(p, self.get_config('schemaless', False)) and
            p not in _IGNORE_SVOBS_KEY_PVS
        ]
        return ';'.join(key_pvs)

    def aggregate_value(self, aggregation_type: str, current_pvs: str,
                        new_pvs: dict, aggregate_property: str):
        '''Aggregate value for the given aggregate_property from new_pvs into current_pvs.'''
        current_value = get_numeric_value(current_pvs.get(
            aggregate_property, 0))
        new_value = get_numeric_value(new_pvs.get(aggregate_property, 0))
        if current_value is None or new_value is None:
            log.error(
                f'Invalid values to aggregate in {current_pvs}, {new_pvs}')
            return False
        aggregation_funcs = {
            'sum': lambda a, b: a + b,
            'min': lambda a, b: min(a, b),
            'max': lambda a, b: max(a, b),
            'list': lambda a, b: f'{a},{b}',
            # TODO: support mean with totals and counts
        }
        if aggregation_type not in aggregation_funcs:
            log.error(
                f'Unsupported aggregation {aggregation_type} for {current_pvs}, {new_pvs}'
            )
            return False
        updated_value = aggregation_funcs[aggregation_type](current_value,
                                                            new_value)
        current_pvs[aggregate_property] = updated_value
        merged_pvs_prop = self.get_config('merged_pvs_property', '#MergedSVObs')
        if merged_pvs_prop:
            if merged_pvs_prop not in current_pvs:
                current_pvs[merged_pvs_prop] = []
            current_pvs[merged_pvs_prop].append(new_pvs)
        dup_svobs_key = self.get_config('duplicate_svobs_key')
        if dup_svobs_key in current_pvs:
            # Dups have been merged for this SVObs.
            # Remove #Error tag so it is not flagged as an error.
            current_pvs.pop(dup_svobs_key)
        self.add_counter(f'aggregated-pvs-{aggregation_type}', 1)
        _DEBUG and logging.debug(
            f'Aggregation: {aggregation_type}:{aggregate_property}: ' +
            f'value {current_value}, {new_value} into {updated_value} ' +
            f'from {current_pvs} and {new_pvs}')
        return True

    def set_statvar_dup_svobs(self, svobs_key: str, svobs: dict):
        '''Add a duplicate SVObs for a statvar.
      Statvars with duplicate observations are likely missing constraint properties.
      The statvar and related observations will be dropped from the output.'''
        # Check if SVObs aggregation is enabled.
        if svobs_key not in self._statvar_obs_map:
            log.error(f'Unexpected missing SVObs: {svobs_key}:{svobs}')
            self.add_counter('error-statvar-obs-missing-for-dup-svobs', 1,
                             statvar_dcid)
            return
        existing_svobs = self._statvar_obs_map.get(svobs_key, None)
        if not existing_svobs:
            logging.error(f'Missing duplicate svobs for key {svobs_key}')
            return
        dup_svobs_key = self.get_config('duplicate_svobs_key')
        if dup_svobs_key not in existing_svobs:
            existing_svobs[dup_svobs_key] = []
        # Add the duplicate SVObs to the original SVObs.
        existing_svobs[dup_svobs_key].append(svobs)
        statvar_dcid = strip_namespace(svobs.get('variableMeasured', None))
        if not statvar_dcid:
            logging.error(f'Missing Statvar dcid for duplicate svobs {svobs}')
            self.add_counter('error-statvar-dcid-missing-for-dup-svobs', 1,
                             statvar_dcid)
            return
        if statvar_dcid not in self._statvars_map:
            logging.error(
                f'Missing Statvar {statvar_dcid} for duplicate svobs {svobs}')
            self.add_counter('error-statvar-missing-for-dup-svobs', 1,
                             statvar_dcid)
            return
        # Add the duplicate SVObs to the statvar
        statvar = self._statvars_map[statvar_dcid]
        if dup_svobs_key not in statvar:
            statvar[dup_svobs_key] = []
            self.add_counter('error-statvar-with-dup-svobs', 1, statvar_dcid)
        if not svobs_key:
            svobs_key = self.get_svobs_key(svobs)
        statvar[dup_svobs_key].append(svobs_key)
        _DEBUG and logging.debug(
            f'Added duplicate SVObs to statvar {statvar_dcid}: {statvar[dup_svobs_key]}'
        )

    def add_statvar_obs(self, pvs: dict):
        # Check if the required properties are present.
        missing_props = set(
            self.get_config('required_statvarobs_properties',
                            [])).difference(set(pvs.keys()))
        if missing_props:
            logging.error(f'Missing SVObs properties {missing_props} in {pvs}')
            self.add_counter(f'error-svobs-missing-property', 1,
                             f'{missing_props}')
            return False
        # Check if the SVObs already exists.
        allow_equal_pvs = True
        svobs_aggregation = self.get_config('aggregate_duplicate_svobs', None)
        svobs_aggregation = pvs.get(
            self.get_config('aggregate_key', '#Aggregate'), svobs_aggregation)
        if svobs_aggregation:
            # PVs with same value are not considered same, need to be aggregated.
            allow_equal_pvs = False
        svobs_key = self.get_svobs_key(pvs)
        if not self.add_dict_to_map(svobs_key,
                                    pvs,
                                    self._statvar_obs_map,
                                    self.get_config('duplicate_svobs_key'),
                                    allow_equal_pvs=allow_equal_pvs):
            existing_svobs = self._statvar_obs_map.get(svobs_key, None)
            if not existing_svobs:
                logging.error(f'Missing duplicate svobs for key {svobs_key}')
                return False
            if svobs_aggregation and self.aggregate_value(
                    svobs_aggregation, existing_svobs, pvs, 'value'):
                self.add_counter(f'aggregated-svobs-{svobs_aggregation}', 1,
                                 pvs.get('variableMeasured', ''))
                return True

            logging.error(
                f'Duplicate SVObs with mismatched values: {self._statvar_obs_map[svobs_key]} != {pvs}'
            )
            self.add_counter(f'error-mismatched-svobs', 1,
                             pvs.get('variableMeasured', ''))
            self.set_statvar_dup_svobs(svobs_key, pvs)
            return False
        self.add_counter('svobs-added', 1, pvs.get('variableMeasured', ''))

        # Count distinct values for each svobs prop.
        all_svobs_props = set(self._statvar_obs_props.keys())
        all_svobs_props.update(pvs.keys())
        for prop in all_svobs_props:
            value = pvs.get(prop, '')
            if prop not in self._statvar_obs_props:
                self._statvar_obs_props[prop] = []
            value_list = self._statvar_obs_props[prop]
            if value not in value_list and len(value_list) < 2:
                value_list.append(value)
        return True

    def is_valid_pvs(self, pvs: dict) -> bool:
        '''Returns True if there are no error PVs.'''
        dup_svobs_key = self.get_config('duplicate_svobs_key')
        dup_statvars_key = self.get_config('duplicate_statvars_key')
        for prop in pvs.keys():
            if prop in [dup_svobs_key, dup_statvars_key]:
                logging.error(f'Error duplicate property {prop} in {pvs}')
                return False
            if prop.startswith('#Error'):
                logging.error(f'Error property {prop} in {pvs}')
                return False
        return True

    def is_valid_statvar(self, pvs: dict) -> bool:
        '''Returns True if the statvar is valid.'''
        # Check if there are any duplicate StatVars or SVObs or errors.
        if not self.is_valid_pvs(pvs):
            logging.error(f'Invalid StatVar: {pvs}')
            return False
        # Check if the statvar has all mandatory properties.
        missing_props = set(self.get_config('required_statvar_properties',
                                            [])).difference(set(pvs.keys()))
        if missing_props:
            logging.error(
                f'Missing properties {missing_props} for statvar {pvs}')
            return False

        statvar_dcid = pvs.get('Node', None)
        statvar_dcid = pvs.get('dcid', statvar_dcid)
        if not statvar_dcid:
            statvar_dcid = self.generate_statvar_dcid(pvs)
        if not statvar_dcid:
            logging.error(f'Missing dcid for statvar {pvs}')
            return False
        pvs['Node'] = add_namespace(statvar_dcid)

        # Check if the statvar has any error properties.
        error_props = [
            f'{p}:{v}' for p, v in pvs.items() if p.startswith('#Err')
        ]
        if error_props:
            logging.error(f'Statvar {pvs} with error properties {error_props}')
            return False

        # TODO: Check if the statvar has any blocked properties
        return True

    def is_valid_svobs(self, pvs: dict) -> bool:
        '''Returns True if the SVObs is valid and refers to an existing StatVar.'''
        if not self.is_valid_pvs(pvs):
            logging.error(f'Invalid SVObs: {pvs}')
            return False
        # Check if the StatVar exists.
        statvar_dcid = strip_namespace(pvs.get('variableMeasured', ''))
        if not statvar_dcid:
            logging.error(f'Missing statvar_dcid for SVObs {pvs}')
            return False
        if statvar_dcid not in self._statvars_map:
            logging.error(
                f'Missing {statvar_dcid} in StatVarMap for SVObs {pvs}')
            return False
        # Check if the statvarobs has any error properties.
        error_props = [
            f'{p}:{v}' for p, v in pvs.items() if p.startswith('#Err')
        ]
        if error_props:
            logging.error(
                f'StatvarObs {pvs} with error properties {error_props}')
        return True

    def drop_statvars_without_svobs(self):
        '''Drop any Statvars without any observations.'''
        statvars_with_obs = set()
        for svobs_key, pvs in self._statvar_obs_map.items():
            statvar_dcid = strip_namespace(pvs.get('variableMeasured', None))
            if statvar_dcid:
                statvars_with_obs.add(statvar_dcid)
        drop_statvars = set(
            self._statvars_map.keys()).difference(statvars_with_obs)
        for statvar_dcid in drop_statvars:
            pvs = self._statvars_map.pop(statvar_dcid)
            logging.error(
                f'Dropping statvar {statvar_dcid} without SVObs {pvs}')
            self.add_counter('dropped-statvars-without-svobs', 1, statvar_dcid)
        return

    def drop_invalid_statvars(self):
        '''Drop invalid statvars and corresponding SVObs.
      Statvars dropped include:
      - statvars with missing required properties
      - statvars with duplicate SVObs.
      - statvars with any dropped properties
      '''
        # Collect valid statvars
        valid_statvars = {}
        for statvar, pvs in self._statvars_map.items():
            if self.is_valid_statvar(pvs):
                valid_statvars[statvar] = pvs
            else:
                self.add_counter(f'dropped-invalid-statvars', 1, statvar)
        self._statvars_map = valid_statvars

        # Collect valid SVObs with valid statvars.
        valid_svobs = {}
        for svobs_key, pvs in self._statvar_obs_map.items():
            if self.is_valid_svobs(pvs):
                valid_svobs[svobs_key] = pvs
            else:
                self.add_counter(f'dropped-invalid-svobs', 1, svobs_key)
        self._statvar_obs_map = valid_svobs

        # Drop any statvars without any observations.
        if self.get_config('drop_statvars_without_svobs', True):
            self.drop_statvars_without_svobs()

    def write_statvars_mcf(self,
                           filename: str,
                           mode: str = 'w',
                           stat_var_nodes: dict = None,
                           header: str = None):
        '''Save the statvars into an MCF file.'''
        if not stat_var_nodes:
          stat_var_nodes = self._statvars_map
        commandline = ' '.join(sys.argv)
        if not header:
          header=f'# Autogenerated using command: "{commandline}" on {datetime.datetime.now()}\n'
        logging.info(
            f'Generating {len(stat_var_nodes)} statvars into {filename}')
        write_mcf_nodes([stat_var_nodes],
                        filename=filename,
                        mode=mode,
                        sort=True,
                        header=header)
        self.add_counter('output-statvars-mcf', len(self._statvars_map),
                         os.path.basename(filename))

    def get_constant_svobs_pvs(self) -> dict:
        '''Return PVs that have a fixed value across SVObs.'''
        if len(self._statvar_obs_map) < 2:
            return {'typeOf': 'dcs:StatVarObservation'}
        pvs = {}
        for prop, value_list in self._statvar_obs_props.items():
            if len(value_list) == 1:
                pvs[prop] = value_list[0]
        return pvs

    def get_multi_value_svobs_pvs(self) -> dict:
        '''Return SVObs properties that have multiple values.'''
        svobs_pvs = set(self._statvar_obs_props)
        return list(svobs_pvs.difference(self.get_constant_svobs_pvs().keys()))

    def get_statvar_obs_columns(self) -> list:
        '''Returns the list of columns for statvar Obs.'''
        columns = self.get_config('output_columns', None)
        if not columns:
            columns = self.get_multi_value_svobs_pvs()
            if not self.get_config('debug', False):
                # Remove debug columns.
                for col in columns:
                    if not is_valid_property(
                            col, self.get_config('schemaless', False)):
                        columns.remove(col)
                input_column = self.get_config('input_reference_column')
                if input_column in columns:
                    columns.remove(input_column)
        # Return output columns in order configured.
        output_columns = []
        for col in self.get_config('default_svobs_pvs', {}).keys():
            if col in columns:
                output_columns.append(col)
        # Add any additional valid columns.
        debug_columns = []
        for col in columns:
            if col not in output_columns:
                if is_valid_property(col, self.get_config('schemaless', False)):
                    output_columns.append(col)
                else:
                    debug_columns.append(col)
        output_columns.extend(debug_columns)
        return output_columns

    def write_statvar_obs_csv(self,
                              filename: str,
                              mode: str = 'w',
                              columns: list = None,
                              output_tmcf: bool = True):
        '''Save the StatVar observations into a CSV file and tMCF.'''
        filename_base, filename_ext = os.path.splitext(filename)
        filename_csv = filename_base + '.csv'
        if not columns:
            columns = self.get_statvar_obs_columns()

        logging.info(
            f'Writing {len(self._statvar_obs_map)} SVObs  into {filename_csv} with {columns}'
        )
        svobs_unique_values = {}
        with open(filename_csv, mode, newline='') as f_out_csv:
            csv_writer = csv.DictWriter(f_out_csv,
                                        fieldnames=columns,
                                        extrasaction='ignore',
                                        lineterminator='\n')
            if mode == 'w':
                csv_writer.writeheader()
            for key, svobs in self._statvar_obs_map.items():
                csv_writer.writerow(svobs)
                for p, v in svobs.items():
                    if is_valid_property(p,
                                         self.get_config('schemaless', False)):
                        if p not in svobs_unique_values:
                            svobs_unique_values[p] = set()
                        svobs_unique_values[p].add(v)

        self.add_counter('output-svobs-csv-rows', len(self._statvar_obs_map),
                         filename_csv)
        for p, s in svobs_unique_values.items():
            self.add_counter(f'output-svobs-unique-{p}', len(s))

        if output_tmcf:
            self.write_statvar_obs_tmcf(filename=filename_base + '.tmcf',
                                        columns=columns)

    def write_statvar_obs_tmcf(self,
                               filename: str,
                               mode: str = 'w',
                               columns: list = None,
                               constant_pvs: dict = None,
                               dataset_name: str = None):
        '''Generate the tMCF for the listed StatVar observation columns.'''
        if not dataset_name:
            dataset, ext = os.path.splitext(filename)
            dataset_name = os.path.basename(dataset)
        if not columns:
            columns = self.get_multi_value_svobs_pvs()
        if not constant_pvs and self.get_config('skip_constant_csv_columns',
                                                False):
            constant_pvs = self.get_constant_svobs_pvs()

        logging.info(
            f'Writing SVObs tmcf {filename} with {columns} into {filename}.')

        tmcf = [f'Node: E:{dataset_name}->E0']
        default_svobs_pvs = dict(self.get_config('default_svobs_pvs', {}))
        for prop in columns:
            # Emit any SVObs columns. Others are ignored.
            if prop in default_svobs_pvs:
                tmcf.append(f'{prop}: C:{dataset_name}->{prop}')
                default_svobs_pvs.pop(prop)
                if constant_pvs and prop in constant_pvs:
                    constant_pvs.pop(prop)
        if constant_pvs:
            for prop, value in constant_pvs.items():
                tmcf.append(f'{prop}: {value}')
                default_svobs_pvs.pop(prop)
        # Add any remaining default PVs
        for prop, value in default_svobs_pvs.items():
            if value:
                tmcf.append(f'{prop}: {value}')

        with open(filename, mode, newline='') as f_out_tmcf:
            f_out_tmcf.write('\n'.join(tmcf))
            f_out_tmcf.write('\n')


class StatVarDataProcessor(Config, Counters):
    '''Class to process data and generate StatVars and StatVarObs.'''

    def __init__(self,
                 pv_mapper: PropertyValueMapper = None,
                 config_dict: dict = None,
                 counters_dict: dict = None):
        Config.__init__(self, config_dict=config_dict)
        Counters.__init__(self,
                          counters_dict=counters_dict,
                          debug=self.get_config('debug', False))
        if not pv_mapper:
            pv_map_files = self.get_config('pv_map', [])
            _DEBUG and logging.debug(
                f'Creating PropertyValueMapper with {pv_map_files}, config: {config_dict}'
            )
            self._pv_mapper = PropertyValueMapper(
                pv_map_files,
                config_dict=config_dict,
                counters_dict=self.get_counters())
        else:
            self._pv_mapper = pv_mapper
        self._statvars_map = StatVarsMap(config_dict=config_dict,
                                         counters_dict=self.get_counters())
        if self.get_config('pv_map_drop_undefined_nodes', False):
            self._statvars_map.remove_undefined_properties(
                self._pv_mapper.get_pv_map())
        # Regex for references within values, such as, '@Variable' or '{Variable}'
        self._reference_pattern = re.compile(
            r'@([a-zA-Z0-9_]+)\b|{([a-zA-Z0-9_]+)}')
        # Internal PVs created implicitly.
        self._internal_reference_keys = [
            self.get_config('data_key', '@Data'),
            self.get_config('numeric_data_key', '@Number')
        ]

    # Functions that can be overridden by child classes.
    def preprocess_row(self, row: list, row_index) -> list:
        '''Modify the contents of the row and return new values.
      Can add additional columns or change values of a column.
      To ignore the row, return an empty list.'''
        return row

    def preprocess_stat_var_pbs_pvs(self, pvs: dict) -> dict:
        '''Modify the PVs for a stat var and stat var observation.
      New PVs can be added or PVs can be removed.
      Return an empty dict to ignore the PVs.'''
        return [pvs]

    def init_file_state(self, filename: str):
        # State while processing data files.
        # Dict of PVs per column by the column index -> {P:V}.
        # PVs for non-numeric values in the header are stored per column
        # and applied to any data found later in the column.
        self._column_pvs = {}
        self._column_keys = OrderedDict()
        # List of PVs for the current row from non-data columns in that row.
        self._row_pvs = []
        self._context = {}
        self._set_input_context(filename=filename)
        self._context = {
            '__FILE__': filename,  # Current filename.
            '__LINE__': 0,  # Current line number in input file.
            '__COLUMN__': 0,  # Current column in input file.
            'header_rows': 0,  # Number of header rows.
        }
        self.set_file_header_pvs(self.generate_file_pvs(filename))
        self.init_file_section()

    def _set_input_context(self,
                           filename: str = None,
                           line_number: int = None,
                           column_number: int = None):
        if filename:
            self._context['__FILE__'] = filename
            self._current_filename = os.path.basename(filename)
        if line_number:
            self._context['__LINE__'] = line_number
        if column_number:
            self._context['__COLUMN__'] = column_number
        self._file_context = f'{self._context.get("__FILE__")}:{self._context.get("__LINE__")}:{self._context.get("__COLUMN__")}'

    def init_file_section(self):
        self._section_column_pvs = {}
        self._section_svobs = 0
        self.add_counter(f'input-sections', 1, self.get_current_filename())

    def get_current_filename(self) -> str:
        return self._current_filename

    def get_last_column_header(self, column_index: int) -> str:
        '''Get the last string for the column header.'''
        if column_index in self._column_keys:
            col_keys_dict = self._column_keys[column_index]
            last_key = next(reversed(col_keys_dict))
            return col_keys_dict[last_key]
        return None

    def generate_file_pvs(self, filename: str) -> dict:
        '''Generate the PVs that apply to all data in the file.'''
        word_delimiter = self.get_config('word_delimiter', ' ')
        word_joiner = word_delimiter.split('|')[0]
        normalize_filename = re.sub(r'[^A-Za-z0-9_\.-]', word_joiner, filename)
        _DEBUG and logging.debug(
            f'Getting PVs for filename {normalize_filename}')
        pvs_list = self._pv_mapper.get_all_pvs_for_value(normalize_filename)
        return self.resolve_value_references(pvs_list)

    def set_file_header_pvs(self, pvs: dict):
        _DEBUG and logging.debug(f'Setting file header PVs to {pvs}')
        self._file_pvs = dict(pvs)

    def get_file_header_pvs(self):
        return self._file_pvs

    def set_column_header_pvs(self, row_index: int, column_index: int,
                              column_key: str, column_pvs: dict,
                              header_pvs: dict) -> dict:
        '''Set the PVs for the column header.'''
        if column_index not in self._column_keys:
            self._column_keys[column_index] = OrderedDict({0: column_key})
        self._column_keys[column_index][row_index] = column_key
        if column_index not in header_pvs:
            header_pvs[column_index] = {}
        header_pvs[column_index].update(column_pvs)
        _DEBUG and logging.debug(
            f'Setting header for column:{row_index}:{column_index}:{column_key}:{header_pvs[column_index]}'
        )

    def get_column_header_pvs(self, column_index: int) -> dict:
        '''Return the dict for column headers if any.'''
        return self._column_pvs.get(column_index, {})

    def get_column_header_key(self, column_index) -> str:
        '''Return the last column header.'''
        if column_index in self._column_keys:
            col_keys = self._column_keys[column_index]
            for row_index, column_key in col_keys.items():
                return column_key
        return None

    def get_last_column_header_key(self, column_index) -> str:
        '''Return the last column header.'''
        if column_index in self._column_keys:
            col_keys = self._column_keys[column_index]
            return list(col_keys.values())[-1]
        return None

    def get_section_header_pvs(self, column_index: int) -> dict:
        '''Return the dict for column headers if any.'''
        return self._section_column_pvs.get(column_index, {})

    def add_column_header_pvs(self, row_index: int, row_col_pvs: dict,
                              columns: list):
        '''Add PVs per column as file column header or section column headers.'''
        column_headers = self._column_pvs
        num_svobs = self.get_counter('output-svobs-' +
                                     self.get_current_filename())
        if num_svobs:
            # Some SVObs already generated for earlier rows.
            # Add column PVS as section headers.
            if self._section_svobs:
                # Start a new section as earlier section had some SVObs.
                self.init_file_section()
            column_headers = self._section_column_pvs
        # Save the column header PVs.
        prev_col_pvs = {}
        for col_index in range(0, len(columns)):
            col_pvs = row_col_pvs.get(col_index, {})
            # Remove any empty @Data PVs.
            data_key = self.get_config('data_key', '@Data')
            if data_key in col_pvs and not col_pvs[data_key]:
                col_pvs.pop(data_key)
            column_value = columns[col_index]
            if not col_pvs and not column_value:
                # Empty column without any PVs could be a multi-column-span
                # header. Carry over previous column PVs if any.
                col_pvs = prev_col_pvs
            if col_pvs:
                self.set_column_header_pvs(row_index, col_index, column_value,
                                           col_pvs, column_headers)
            prev_col_pvs = col_pvs
        _DEBUG and logging.debug(f'Setting column headers: {column_headers}')

    def get_reference_names(self, value: str) -> str:
        '''Return any named references, such as '@var' or '{@var}' in the value.'''
        refs = []
        if not value or not isinstance(value, str):
            return refs
        for n1, n2 in self._reference_pattern.findall(value):
            if n1:
                refs.append(n1)
            if n2:
                refs.append(n2)
        return refs

    def resolve_value_references(self,
                                 pvs_list: list,
                                 process_pvs: bool = False) -> dict:
        '''Return a single dict merging a list of dicts and resolving any references.'''
        # Merge all PVs resolving references from last to first.
        if not pvs_list:
            return {}
        pvs = dict()
        for d in reversed(pvs_list):
            for prop, value_list in d.items():
                if not isinstance(value_list, list):
                    value_list = [value_list]
                for value in value_list:
                    # Check if the value has any references with @
                    unresolved_refs = []
                    refs = self.get_reference_names(value)
                    # Replace each reference with its value.
                    for ref in refs:
                        replacement = None
                        for ref_key in [f'@{ref}', ref]:
                            if ref_key in pvs:
                                replacement = str(pvs[ref_key])
                            elif ref_key in d:
                                replacement = str(d[ref_key])
                        if replacement:
                            _DEBUG and logging.debug(
                                f'Replacing reference {ref} with {replacement} for {prop}:{value}'
                            )
                            value = value.replace('{' + ref + '}',
                                                  replacement).replace(
                                                      '{@' + ref + '}',
                                                      replacement).replace(
                                                          '@' + ref,
                                                          replacement)
                        else:
                            unresolved_refs.append(ref)
                    if unresolved_refs:
                        _DEBUG and logging.debug(
                            f'Unresolved refs {unresolved_refs} remain in {prop}:{value} at {self._file_context}'
                        )
                        self.add_counter('warning-unresolved-value-ref', 1,
                                         ','.join(unresolved_refs))
                    add_key_value(prop,
                                  value,
                                  pvs,
                                  self.get_config('multi_value_properties', {}),
                                  overwrite=False)
                    _DEBUG and logging.debug(
                        f'Adding {value} for {prop}:{pvs[prop]}')
        _DEBUG and logging.debug(
            f'Resolved references in {pvs_list} into {pvs}')
        if process_pvs:
            if self._pv_mapper.process_pvs_for_data(key=None, pvs=pvs):
                # PVs were processed. Resolve any references again.
                return self.resolve_value_references([pvs], process_pvs=False)
        return pvs

    def process_data_files(self, filenames: list):
        '''Process a data file to generate statvars.'''
        time_start = time.perf_counter()
        # Expand any wildcard in filenames
        files = []
        for file_pat in filenames:
            files.extend(glob.glob(file_pat))
        # Process all input data files, one at a time.
        for filename in files:
            logging.info(f'Processing input data file {filename}...')
            file_start_time = time.perf_counter()
            with open(filename, newline='', encoding="utf-8") as csvfile:
                self.add_counter('input-files-processed', 1)
                # Guess the input format.
                try:
                    dialect = csv.Sniffer().sniff(csvfile.read(5024))
                except csv.Error:
                    dialect = self.get_config('input_data_dialect', 'excel')
                max_rows_per_file = self.get_config('input_rows', -1)
                csvfile.seek(0)
                reader = csv.reader(csvfile, dialect)
                line_number = 0
                self.init_file_state(filename)
                skip_rows = self.get_config('skip_rows', 0)
                # Process each row in the input data file.
                for row in reader:
                    line_number += 1
                    if line_number <= skip_rows:
                        _DEBUG and logging.debug(
                            f'Skipping row {filename}:{line_number}:{row}')
                        continue
                    if max_rows_per_file >= 0 and line_number > max_rows_per_file:
                        _DEBUG and logging.debug(
                            f'Stopping at input {filename}:{line_number}:{row}')
                        break
                    self.add_counter('input-lines', 1, filename)
                    self._set_input_context(filename=filename,
                                            line_number=line_number)
                    self.process_row(row, line_number)
            time_end = time.perf_counter()
            time_taken = time_end - time_start
            self.set_counter('processing-time-seconds', time_taken, filename)
            line_rate = line_number / (time_end - file_start_time)
            self.log_counters()
            logging.info(
                f'Processed {line_number} lines from {filename} @ {line_rate:.2f} lines/sec.'
            )
            self.set_counter(f'processing-input-rows-rate', line_rate, filename)
        time_end = time.perf_counter()
        rows_processed = self.get_counter('input-rows-processed')
        time_taken = time_end - time_start
        input_rate = rows_processed / time_taken
        logging.info(
            f'Processed {rows_processed} rows from {len(files)} files @ {input_rate:.2f} rows/sec.'
        )
        self.set_counter(f'processing-input-rows-rate', input_rate)

    def should_lookup_pv_for_row_column(self, row_index: int,
                                        column_index: int) -> bool:
        '''Returns True if PVs should be looked up for cell row_index:column_index
      Assumes row_index and column_index start from 1.'''
        header_rows = self.get_config('header_rows', 0)
        header_columns = self.get_config('header_columns', 0)
        if header_rows > 0 and row_index <= header_rows:
            return True
        if header_columns > 0 and column_index <= header_columns:
            return True
        column_header = self.get_column_header_key(column_index - 1)
        if column_header and column_header in self._pv_mapper.get_pv_map():
            # Column header has a PV mapping file. Allow PV lookup.
            return True
        return header_rows <= 0 and header_columns <= 0

    def process_row(self, row: list, row_index: int):
        '''Process a row of data with multiple columns.
        The row cold be a file header or a section header with SVObs or
        the row could have SVObs in some columns.'''
        _DEBUG and logging.debug(f'Processing row:{row_index}: {row}')
        row = self.preprocess_row(row, row_index)
        if not row:
            _DEBUG and logging.debug(f'Preprocess dropping row {row_index}')
            self.add_counter('input-rows-ignored-preprocess', 1,
                             self.get_current_filename())
            return
        if not row or len(row) < self.get_config('input_min_columns_per_row',
                                                 3):
            _DEBUG and logging.debug(
                f'Ignoring row with too few columns: {row}')
            self.add_counter('input-rows-ignored-too-few-columns', 1,
                             self.get_current_filename())
            return
        self.add_counter('input-rows-processed', 1, self.get_current_filename())
        # Collect all PVs for the columns in the row.
        row_col_pvs = OrderedDict()
        cols_with_pvs = 0
        for col_index in range(len(row)):
            col_value = row[col_index].strip()
            col_pvs = {}
            if self.should_lookup_pv_for_row_column(row_index, col_index + 1):
                self._set_input_context(column_number=col_index)
                _DEBUG and logging.debug(
                    f'Getting PVs for column:{row_index}:{col_index}:{col_value}'
                )
                pvs_list = self._pv_mapper.get_all_pvs_for_value(
                    col_value, self.get_last_column_header_key(col_index))
                #if pvs_list:
                #    pvs_list.append(
                #        {self.get_config('data_key', '@Data'): col_value})
                #else:
                #if not pvs_list:
                #    pvs_list = [{self.get_config('data_key', '@Data'): col_value}]
                col_pvs = self.resolve_value_references(pvs_list,
                                                        process_pvs=True)
            if col_pvs:
                # Column has mapped PVs.
                # It could be a header or be applied to other values in the row.
                row_col_pvs[col_index] = col_pvs
                cols_with_pvs += 1
                _DEBUG and logging.debug(
                    f'Got pvs for column:{row_index}:{col_index}:{col_pvs}')
            else:
                # Column has no PVs. Check if it has a value.
                col_numeric_val = get_numeric_value(col_value)
                if col_numeric_val:
                    if self.get_config('use_all_numeric_data_values', False):
                        row_col_pvs[col_index] = {'value': col_numeric_val}
                    else:
                        row_col_pvs[col_index] = {
                            self.get_config('numeric_data_key', '@Number'):
                                col_numeric_val
                        }
                    _DEBUG and logging.debug(
                        f'Got PVs for column:{row_index}:{col_index}: value:{row[col_index]}, PVS: {row_col_pvs[col_index]}'
                    )
                else:
                    _DEBUG and logging.debug(
                        f'Got no PVs for column:{row_index}:{col_index}: value:{row[col_index]}'
                    )

        _DEBUG and logging.debug(
            f'Processing row:{row_index}:{row}: into PVs: {row_col_pvs} in {self._file_context}'
        )
        if not row_col_pvs:
            # No interesting data or PVs in the row. Ignore it.
            _DEBUG and logging.debug(
                f'Ignoring row without PVs: {row} in {self._file_context}')
            self.add_counter('input-rows-ignored', 1,
                             self.get_current_filename())
            return

        # Process values in the row, applying row and column PVs.
        row_pvs = {}  # All PVs in the row from the leftmost column to right.
        column_pvs = {}  # PVs per column, indexed by the column number.
        for col_index in range(0, len(row)):
            col_value = row[col_index].strip()
            # Get column header PVs and resolved any references
            self._set_input_context(column_number=col_index)
            col_pvs_list = []
            # Collect PVs that apply to the cell from from column headers
            col_pvs_list.append(self.get_file_header_pvs())
            col_pvs_list.append(self.get_column_header_pvs(col_index))
            col_pvs_list.append(self.get_section_header_pvs(col_index))
            col_pvs_list.append(row_col_pvs.get(col_index, {}))
            col_pvs_list.append(
                {self.get_config('data_key', '@Data'): col_value})
            merged_col_pvs = self.resolve_value_references(col_pvs_list,
                                                           process_pvs=True)
            # Collect PVs that apply to the row
            merged_row_pvs = self.resolve_value_references(
                [row_pvs,
                 row_col_pvs.get(col_index, {}), col_pvs_list[-1]],
                process_pvs=True)
            # Collect resolved PVs for the cell from row and column headers.
            cell_pvs = self.resolve_value_references(
                [merged_row_pvs, merged_col_pvs])
            _DEBUG and logging.debug(
                f'Merged PVs for column:{row_index}:{col_index}: {col_pvs_list} and {row_pvs} into {cell_pvs}'
            )
            self._set_input_context(column_number=col_index)
            cell_pvs[self.get_config(
                'input_reference_column')] = self._file_context
            column_pvs[col_index] = cell_pvs
            if 'value' not in cell_pvs:
                # Carry forward the non-SVObs PVs to the next column.
                # Collect resolved PVs or PVs with references for a cell
                # to be applied to the whole row.
                for prop, value in cell_pvs.items():
                    if value and prop not in self._internal_reference_keys and not self.get_reference_names(
                            value):
                        add_key_value(
                            prop, value, row_pvs,
                            self.get_config('multi_value_properties', {}))
                for prop, value in row_col_pvs.get(col_index, {}).items():
                    if value and prop not in self._internal_reference_keys:
                        add_key_value(
                            prop, value, row_pvs,
                            self.get_config('multi_value_properties', {}))
        # Process per-column PVs after merging with row-wide PVs.
        # If a cell has a statvar obs, save the svobs and the statvar.
        _DEBUG and logging.debug(
            f'Looking for SVObs in row:{row_index}: with row PVs: {row_pvs}, column PVs: {column_pvs}'
        )
        row_svobs = 0
        for col_index, col_pvs in column_pvs.items():
            self._set_input_context(column_number=col_index)
            merged_col_pvs = self.resolve_value_references([row_pvs, col_pvs],
                                                           process_pvs=True)
            merged_col_pvs[self.get_config(
                'input_reference_column')] = self._file_context
            if self.process_stat_var_obs_pvs(merged_col_pvs):
                row_svobs += 1
        # If row has no SVObs but has PVs, it must be a header.
        if not row_svobs and cols_with_pvs > 0 and self.should_lookup_pv_for_row_column(
                row_index, col_index + 1):
            # Any column with PVs must be a header applicable to entire column.
            _DEBUG and logging.debug(
                f'Setting column header PVs for row:{row_index}:{row_col_pvs}')
            self.add_column_header_pvs(row_index, row_col_pvs, row)
            self.add_counter(f'input-header-rows', 1,
                             self.get_current_filename())
        else:
            _DEBUG and logging.debug(
                f'Found {row_svobs} SVObs in row:{row_index}')
            self.add_counter(f'input-data-rows', 1, self.get_current_filename())

    def process_stat_var_obs_value(self, pvs: dict) -> bool:
        '''Process the value applying any multiplication factor if required.'''
        if not 'value' in pvs:
            return False
        value = pvs['value']
        if not is_valid_value(value):
            return False
        numeric_value = get_numeric_value(value)
        if numeric_value:
            multiply_prop = self.get_config('multiply_factor', 'MultiplyFactor')
            if multiply_prop in pvs:
                multiply_factor = pvs[multiply_prop]
                pvs['value'] = numeric_value * multiply_factor
                pvs.pop(multiply_prop)
        return True

    def process_stat_var_obs_pvs(self, pvs: dict) -> bool:
        '''Process a set of SVObs PVs flattening list values.'''
        _DEBUG and logging.debug(
            f'Processing SVObs PVs: {pvs} for {self._file_context}')
        singular_pvs = {}
        list_keys = []
        for prop, value in pvs.items():
            if isinstance(value, list):
                list_keys.append(prop)
            else:
                singular_pvs[prop] = value

        if not list_keys:
            return self.process_stat_var_obs(pvs)

        # Flatten all list PVs.
        _DEBUG and logging.debug(
            f'Flattening list values for keys: {list_keys} in PVs:{pvs}')
        status = True
        list_values = [pvs[key] for key in list_keys]
        for items in itertools.product(*list_values):
            flattened_pvs = dict(singular_pvs)
            for index in range(len(list_keys)):
                flattened_pvs[list_keys[index]] = items[index]
            status &= self.process_stat_var_obs(flattened_pvs)
        return status

    def process_stat_var_obs(self, pvs: dict) -> bool:
        '''Process PV for a statvar obs.'''
        svobs_pvs_list = self.preprocess_stat_var_pbs_pvs(pvs)
        if not svobs_pvs_list:
            _DEBUG and logging.debug(
                f'Preprocess dropping SVObs PVs for {self._file_context}')
            return False
        _DEBUG and logging.debug(
            f'Got {len(svobs_pvs_list)} SVOVs pvs after preprocess: {svobs_pvs_list}'
        )
        status = True
        for svobs_pvs in svobs_pvs_list:
            status &= self.process_single_stat_var_obs(svobs_pvs)
        return status

    def process_single_stat_var_obs(self, pvs: dict) -> bool:
        if not self.process_stat_var_obs_value(pvs):
            # No values in this data cell. May be a header.
            _DEBUG and logging.debug(
                f'No SVObs value in dict {pvs} in {self._file_context}')
            return False

        _DEBUG and logging.debug(
            f'Creating SVObs for {pvs} in {self._file_context}')
        # Separate out PVs for StatVar and StatvarObs
        statvar_pvs = {}
        svobs_pvs = {}
        for prop, value in pvs.items():
            if prop == self.get_config('aggregate_key', '#Aggregate'):
                svobs_pvs[prop] = value
            elif is_valid_property(prop, self.get_config(
                    'schemaless', False)) and is_valid_value(value):
                if prop in self.get_config('default_svobs_pvs'):
                    svobs_pvs[prop] = value
                else:
                    statvar_pvs[prop] = value
        if not svobs_pvs:
            logging.error(f'No SVObs PVs in {pvs} in file:{self._file_context}')
            return False
        # Remove internal PVs
        for p in [
                self.get_config('data_key', 'Data'),
                self.get_config('numeric_data_key', 'Number')
        ]:
            if p in statvar_pvs:
                statvar_pvs.pop(p)

        # Set the dcid for the StatVar
        self._statvars_map.add_default_pvs(
            statvar_pvs, self.get_config('default_statvar_pvs'))
        statvar_dcid = strip_namespace(svobs_pvs.get('variableMeasured', None))
        statvar_dcid = strip_namespace(statvar_pvs.get('dcid', statvar_dcid))
        if not statvar_dcid:
            statvar_dcid = strip_namespace(
                self._statvars_map.generate_statvar_dcid(statvar_pvs))
        if not statvar_dcid or not statvar_pvs:
            logging.error(
                f'Unable to get statvar:{statvar_dcid}:{statvar_pvs} for SVObs {pvs} in {self._file_context}'
            )
            self.add_counter(f'error-missing-statvar-in-svobs', 1)
            return False
        svobs_pvs['variableMeasured'] = add_namespace(statvar_dcid)
        svobs_pvs[self.get_config(
            'input_reference_column')] = self._file_context

        # Create and add StatVar.
        if not self._statvars_map.add_statvar(statvar_pvs):
            logging.error(
                f'Dropping SVObs {svobs_pvs} for invalid statvar {statvar_pvs} in {self._file_context}'
            )
            self.add_counter(f'dropped-svobs-with-invalid-statvar', 1,
                             statvar_dcid)
            return False

        # Create and add SVObs.
        self._statvars_map.add_default_pvs(
            svobs_pvs, self.get_config('default_svobs_pvs', {}))
        if not self.resolve_svobs_place(svobs_pvs):
            logging.error(f'Unable to resolve SVObs place in {pvs}')
            return False
        if not self._statvars_map.add_statvar_obs(svobs_pvs):
            logging.error(
                f'Dropping invalid SVObs {svobs_pvs} for statvar {statvar_pvs} in {self._file_context}'
            )
            self.add_counter(f'dropped-svobs-invalid', 1, statvar_dcid)
            return False
        self.add_counter(f'generated-svobs', 1, statvar_dcid)
        self.add_counter('generated-svobs-' + self.get_current_filename(), 1)
        self._section_svobs += 1
        _DEBUG and logging.debug(
            f'Added SVObs {svobs_pvs} in {self._file_context}')
        return True

    def resolve_svobs_place(self, pvs: dict) -> bool:
        '''Resolve any references in the StatVarObs PVs, such as places.'''
        place = pvs.get('observationAbout', None)
        if not place:
            logging.warning(f'No place in SVObs {pvs}')
            self.add_counter(f'warning-svobs-missing-place', 1,
                             pvs.get('variableMeasured', ''))
            return False
        if ':' in place:
            # Place is a resolved dcid or a place property.
            return True

        # Lookup dcid for the place.
        place_id = self.resolve_value_references(
            self._pv_mapper.get_all_pvs_for_value(place, 'observationAbout'))
        if place_id:
            pvs.update(place_id)
            _DEBUG and logging.debug(f'Resolved place {place} to {place_id}')
            self.add_counter(f'resolved-places', 1)
            return True

        logging.warning(f'Unable to resolve place {place} in {pvs}')
        self.add_counter(f'warning-unresolved-place', 1,
                         pvs.get('variableMeasured', ''))
        return False

    def merge_outputs(self,
                      statvars: dict = None,
                      statvar_obs: dict = None) -> bool:
        '''Merge statvars and statvar obs from other runs.'''

    def write_outputs(self, output_path: str):
        '''Generate output mcf, csv and tmcf.'''
        logging.info(f'Generating output: {output_path}')
        self._statvars_map.drop_invalid_statvars()
        if self.get_config('generate_statvar_mcf', True):
            statvar_mcf_file = output_path + '.mcf'
            self._statvars_map.write_statvars_mcf(
                filename=statvar_mcf_file,
                mode='w')
        if self.get_config('generate_csv', True):
            self._statvars_map.write_statvar_obs_csv(
                output_path + '.csv',
                mode=self.get_config('output_csv_mode', 'w'),
                columns=self.get_config('output_csv_columns', None),
                output_tmcf=self.get_config('generate_tmcf', True))
        self.log_counters()


def download_data_from_url(urls: list, data_path: str) -> list:
    '''Download data from the URL into the given file.
    Returns a list of files downloaded.'''
    data_files = []
    if not isinstance(urls, list):
        urls = [urls]
    for url in urls:
        # Extract the output filename from the URL.
        data_file = re.search(r'^[a-zA-Z0-9_:/\.-]*/(?P<file>[A-Za-z0-9_\.-]+)',
                              url).groupdict().get(
                                  'file', f'input{len(data_files)}.csv')
        # TODO: retry download on error or timeout.
        output_file = os.path.join(data_path, data_file)
        if not os.path.exists(output_file):
            logging.info(f'Downloading {url} into {output_file}...')
            response = requests.get(url)
            if response.status_code != 200:
                logging.error(f'Failed to download {url}: {response}')
                return []
            with open(output_file, 'w') as output_data:
                output_data.write(response.text)
        data_files.append(output_file)
    logging.info(f'Downloaded {urls} into {data_files}.')
    return data_files


def shard_csv_data(files: list,
                   column: str = None,
                   prefix_len: int = 2) -> list:
    '''Shard CSV file by unique values in column.
    Returns the list of output files.'''
    logging.info(
        f'Loading data files: {files} for sharding by column: {column}...')
    dfs = []
    for file in files:
        dfs.append(pd.read_csv(file, dtype=str, na_filter=False))
    df = pd.concat(dfs)
    if not column:
        # Pick the first column.
        column = list(df.columns)[0]
    # Convert nan to empty string to sharding doesn't drop any rows.
    # df[column] = df[column],fillna('')
    # Get unique shard prefix values from column.
    shards = list(
        sorted(set([str(x)[:prefix_len] for x in df[column].unique()])))
    (file_prefix, file_ext) = os.path.splitext(file)
    column_suffix = re.sub(r'[^A-Za-z0-9_-]', '-', column)
    output_path = f'{file_prefix}-{column_suffix}'
    logging.info(
        f'Sharding {files} into {len(shards)} shards by column {column}:{shards} into {output_path}-*.csv.'
    )
    output_files = []
    num_shards = len(shards)
    for shard_index in range(num_shards):
        shard_value = shards[shard_index]
        suffix = re.sub(r'[^A-Za-z0-9_-]', '-', shard_value)
        output_file = f'{output_path}-{suffix}-{shard_index:05d}-of-{num_shards:05d}.csv'
        logging.info(
            f'Sharding by {column}:{shard_value} into {output_file}...')
        if shard_value:
            df[df[column].str.startswith(shard_value)].to_csv(output_file,
                                                              index=False)
        else:
            df[df[column] == ''].to_csv(output_file, index=False)
        output_files.append(output_file)
    return output_files


def prepare_input_data(config: dict) -> bool:
    '''Prepare the input data, download and shard if needed.'''
    input_data = config.get('input_data', '')
    input_files = []
    for file in input_data:
        input_files.extend(glob.glob(file))
    if input_files:
        # Input files already exist. Nothing to download.
        return input_files

    # Download data from the URL.
    data_url = config.get('data_url', '')
    if not data_url:
        logging.fatal(f'Provide data with --data_url or --input_data.')
        return False
    input_files = download_data_from_url(data_url,
                                         os.path.dirname(input_data[0]))
    shard_column = config.get('shard_input_by_column', '')
    if shard_column:
        return shard_csv_data(input_files, shard_column,
                              config.get('shard_prefix_length', 100))
    return input_files


def process(data_processor_class: StatVarDataProcessor,
            input_data: list,
            output_path: str,
            config_file: str,
            pv_map_files: list,
            counters: dict = None,
            parallelism: int = 0) -> bool:
    '''Process all input_data files to extract StatVars and StatvarObs.
    Emit the StatVars and StataVarObs into output mcf and csv files.
    '''
    config = get_config_from_file(config_file)
    config_dict = config.get_configs()
    if input_data:
        config_dict['input_data'] = input_data
    input_data = prepare_input_data(config_dict)
    output_dir = os.path.dirname(output_path)
    traceback.print_stack()
    if output_dir:
      logging.info(f'Creating output directory: {output_dir}')
      os.makedirs(output_dir, exist_ok=True)
    if parallelism <= 1:
        logging.info(f'Processing data {input_data} into {output_path}...')
        if pv_map_files:
            config_dict['pv_map'] = pv_map_files
        if counters is None:
            counters = {}
        if not data_processor_class:
            data_processor_class = StatVarDataProcessor

        data_processor = data_processor_class(config_dict=config_dict,
                                              counters_dict=counters)
        data_processor.process_data_files(input_data)
        data_processor.write_outputs(output_path)
        # Check if there were any errors.
        error_counters = [
            f'{c}={v}' for c, v in counters.items() if c.startswith('err')
        ]
        if error_counters:
            logging.info(f'Error Counters: {error_counters}')
            return False
    else:
        # Process files in parallel, one per process.
        logging.info(
            f'Processing {input_data} with {parallelism} parallel proceses.')
        input_files = []
        for input_path in input_data:
            input_files.extend(glob.glob(input_path))
        num_inputs = len(input_files)
        with multiprocessing.Pool(parallelism) as pool:
            for input_index in range(num_inputs):
                input_file = input_files[input_index]
                output_file_path = f'{output_path}-{input_index:05d}-of-{num_inputs:05d}'
                logging.info(
                    f'Processing {input_file} into {output_file_path}...')
                process_args = {
                    'data_processor_class': data_processor_class,
                    'input_data': [input_file],
                    'output_path': output_file_path,
                    'config_file': config_file,
                    'pv_map_files': pv_map_files,
                    'counters': counters,
                    'parallelism': 0
                }
                pool.apply_async(process, kwds=process_args)
            pool.close()
            pool.join()

        # Merge statvar mcf files into a single mcf output.
        mcf_files = f'{output_path}-*-of-*.mcf'
        statvar_nodes = load_mcf_nodes(mcf_files)
        output_mcf_file = f'{output_path}.mcf'
        self._statvars_map.write_statvars_mcf(filename=output_mcf_file, mode=w,
                                              stat_var_nodes=statvar_nodes)
        logging.info(
            f'Merged {len(statvar_nodes)} stat var MCF nodes from {mcf_files} into {output_mcf_file}.'
        )

        # Create a common TMCF from output, removing the shard suffix.
        with open(f'{output_path}-00000-of-{num_inputs:05d}.tmcf',
                  mode='r') as tmcf:
            tmcf_node = tmcf.read()
            tmcf_node = re.sub(r'-[0-9]*-of-[0-9]*', '', tmcf_node)
            with open(f'{output_path}.tmcf', mode='w') as output_tmcf:
                output_tmcf.write(tmcf_node)
        logging.info(f'Generated TMCF {output_path}.tmcf')

    return True


def main(_):
    _DEBUG = _FLAGS.debug
    # TODO(ajaits): uncomment after fixing google.protobuf import error
    # if _FLAGS.pprof_port > 0:
    #     start_pprof_server(port=_FLAGS.pprof_port)
    process(StatVarDataProcessor,
            input_data=_FLAGS.input_data,
            output_path=_FLAGS.output_path,
            config_file=_FLAGS.config,
            pv_map_files=_FLAGS.pv_map,
            parallelism=_FLAGS.parallelism)


if __name__ == '__main__':
    app.run(main)
