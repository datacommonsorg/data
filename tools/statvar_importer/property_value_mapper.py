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
"""Utility class to store property:value mappings for data strings."""

import csv
import os
import re
import sys

from absl import app
from absl import flags
from absl import logging
from collections import OrderedDict

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import config_flags
import eval_functions
import file_util

import property_value_utils as pv_utils

from config_map import ConfigMap, read_py_dict_from_file
from counters import Counters, CounterOptions


class PropertyValueMapper:
    """Class to map strings to set of property values.

  Supports multiple maps with a namespace or context string. Stores string to
  property:value maps as a dictionary: _pv_map = {

    'GLOBAL': {
      '<input-data-string1>': {
        '<prop1>': '<value1>'
        '<prop2>': '<value2>'
        ...
      },
      ...
    },
    '<namespace>' : {
      '<input-data-string2>': {
        '<prop3>': '<value3>'
        ...
      },
      ...
    },
  }

  The first level keys in _pv_map are namespaces that are column-headers or
  'GLOBAL'.
  When looking up PVs for an input string, such as a column header or a cell
  value,
  first the namespace column-header is tried.
  If there are no values then other namespacs such as 'GLOBAL are tried.

  <value> within the PV can have a reference to another property.
  Such reference are replaced with that property's value after
  all PVs for a data cell have been collected.

  The references are indicated with the syntax '{Variable}' or '@Variable'.
  where 'Variable' is expected to be another property in the cell's PVs.

  Internal properties that require special processing begin with '#', such as:
  '#Regex': refers to a regular expression with names match groups
      to be applied on a cell value
  '#Format': a format string to be processed with other parameters
  '#Eval': a python statement to be evaluated. It could have some computations
    of the form <prop>=<expr> where the '<expr>' is evaluated and
    assigned to property <prop> or to 'Data'.

  The cell value is mapped to the following default properties:
  'Data': the string value in the cell
  'Number': the numeric value if the cell is a number.
  """

    def __init__(
        self,
        pv_map_files: list = [],
        config_dict: dict = None,
        counters_dict: dict = None,
    ):
        self._config = ConfigMap(config_dict=config_dict)
        self._counters = Counters(
            counters_dict=counters_dict,
            options=CounterOptions(debug=self._config.get('debug', False)),
        )
        self._log_every_n = self._config.get('log_every_n', 1)
        # Map from a namespace to dictionary of string-> { p:v}
        self._pv_map = OrderedDict({'GLOBAL': {}})
        self._num_pv_map_keys = 0
        self._max_words_in_keys = 0
        for filename in pv_map_files:
            namespace = 'GLOBAL'
            if not file_util.file_get_matching(filename):
                if ':' in filename:
                    namespace, filename = filename.split(':', 1)
            self.load_pvs_from_file(filename, namespace)
        logging.level_debug() and logging.debug(
            f'Loaded PV map with {len(self._pv_map)} keys: {str(self._pv_map)[:300]} with max words {self._max_words_in_keys}'
        )

    def load_pvs_from_file(self, filename: str, namespace: str = 'GLOBAL'):
        """Loads a map of the form 'string -> { P: V }' from a file.

    File is a python dictionary or a JSON file with python equivalents such as
    True(true), False(false), None(null).

    Args:
      filename: file containing the dictionary of string to dictionary of PVs
      namespace: the namespace key for the dictionary to be loaded against. the
        namespace is the first level key in the _pv_map.
    """
        # Append new PVs to existing map.
        pv_map_input = {}
        if file_util.file_is_csv(filename):
            pv_map_input = self._load_pvs_from_csv(filename, namespace)
        else:
            logging.info(
                f'Loading PV maps for {namespace} from dictionary file: {filename}'
            )
            pv_map_input = read_py_dict_from_file(filename)
        self.load_pvs_dict(pv_map_input, namespace)

    def _load_pvs_from_csv(self, filename: str, namespace: str) -> dict:
        pv_map_input = {}
        logging.log_every_n(
            logging.INFO,
            f'Loading PV maps for {namespace} from csv file: {filename}',
            self._log_every_n)
        with file_util.FileIO(filename) as csvfile:
            csv_reader = csv.reader(csvfile,
                                    skipinitialspace=True,
                                    escapechar='\\')
            for row in csv_reader:
                key, pvs = self._process_csv_row(row, namespace, filename)
                if key:
                    pv_map_input[key] = pvs
        return pv_map_input

    def _process_csv_row(self, row: list[str], namespace: str,
                         filename: str) -> tuple[str | None, dict | None]:
        # Drop trailing empty columns in the row
        last_col = len(row) - 1
        while last_col >= 0 and row[last_col].strip() == '':
            last_col -= 1
        row = row[:last_col + 1]
        if not row:
            return None, None
        key = row[0].strip()
        if key in self._config.get_configs():
            # Add value to the config with same type as original.
            value = ','.join(row[1:])
            config_flags.set_config_value(key, value, self._config)
            return None, None

        pvs = self._parse_pv_row(row[1:], namespace, filename)
        return key, pvs

    def _parse_pv_row(self, pvs_list: list[str], namespace: str,
                      filename: str) -> dict:
        if len(pvs_list) == 1:
            # PVs list has no property, just a value.
            # Use the namespace as the property
            pvs_list = [namespace, pvs_list[0]]
        if len(pvs_list) % 2 != 0:
            raise RuntimeError(
                f'Invalid list of property value: {pvs_list} in {filename}')
        # Get property,values from the columns
        pvs = {}
        for i in range(0, len(pvs_list), 2):
            prop = pvs_list[i].strip()
            if not prop:
                continue
            value = pvs_list[i + 1].strip()
            if value == '""':
                value = ''
            if value and value[0] != '[' and prop[0] != '#':
                if value[0] == "'" and value[-1] == "'":
                    # Replace single quote with double quotes
                    # To distinguish quote as delimiter vs value in CSVs
                    # single quote is used instead of double quote in CSV values.
                    value = f'"{value[1:-1]}"'
            normalize = True
            if '#' in prop or '=' in value:
                # Value is a formula. Set value as a string.
                normalize = False
            pv_utils.add_key_value(prop,
                                   value,
                                   pvs,
                                   self._config.get('multi_value_properties',
                                                    {}),
                                   normalize=normalize)
        return pvs

    def load_pvs_dict(self, pv_map_input: dict, namespace: str = 'GLOBAL'):
        if namespace not in self._pv_map:
            self._pv_map[namespace] = {}
        pv_map = self._pv_map[namespace]
        word_delimiter = self._config.get('word_delimiter', ' ')
        num_keys_added = 0
        for key, pvs_input in pv_map_input.items():
            if key not in pv_map:
                pv_map[key] = {}
            pvs_dict = pv_map[key]
            if isinstance(pvs_input, str):
                pvs_input = {namespace: pvs_input}
            for p, v in pvs_input.items():
                num_keys_added += 1
                pv_utils.add_key_value(p,
                                       v,
                                       pvs_dict,
                                       self._config.get(
                                           'multi_value_properties', {}),
                                       normalize=False)
            # Track the max number of words in any of the keys.
            # This is used when splitting input-string for lookups.
            num_words_key = len(pv_utils.get_words(key, word_delimiter))
            self._max_words_in_keys = max(self._max_words_in_keys,
                                          num_words_key)
            logging.level_debug() and logging.log_every_n(
                2, f'Setting PVMap[{key}] = {pvs_dict}', self._log_every_n)

        self._num_pv_map_keys += num_keys_added
        logging.info(
            f'Loaded {num_keys_added} property-value mappings for "{namespace}"'
        )
        logging.level_debug() and logging.debug(
            f'Loaded pv map {namespace}:{pv_map_input}')

    def get_pv_map(self) -> dict:
        """Returns the dictionary mapping input-strings to property:values."""
        return self._pv_map

    def process_pvs_for_data(self, key: str, pvs: dict) -> bool:
        """Processes property:value and returns true if processed successfully.

    Processes values for actionable props such as '#Regex', '#Eval', '#Format'.
    Args: pvs (input/output) dictionary of property:values Properties such as
    '#Regex', '#Eval', '#Format' are processed and resulting properties are
    updated into pvs.

    Returns:
       True if any property:values were processed and pvs dict was updated.
    """
        logging.level_debug() and logging.log_every_n(
            2, f'Processing data PVs:{key}:{pvs}', self._log_every_n)
        data_key = self._config.get('data_key', 'Data')
        data = pvs.get(data_key, key)
        is_modified = False

        is_modified |= self._process_regex(key, data, pvs)
        is_modified |= self._process_format(key, data, pvs, data_key)
        is_modified |= self._process_eval(pvs, data_key)

        logging.level_debug() and logging.log_every_n(
            2, f'Processed data PVs:{is_modified}:{key}:{pvs}',
            self._log_every_n)
        return is_modified

    def _process_regex(self, key: str, data: str, pvs: dict) -> bool:
        """Processes a #Regex property and updates pvs."""
        # Process regular expression and add named group matches to the PV.
        # Regex PV is of the form: '#Regex': '(?P<Start>[0-9]+) *- *(?P<End>[0-9])'
        # Parses 'Data': '10 - 20' to generate PVs:
        # { 'Start': '10', 'End': '20' }
        regex_key = self._config.get('regex_key', '#Regex')
        if regex_key not in pvs or not data:
            return False

        re_pattern = pvs[regex_key]
        re_matches = re.finditer(re_pattern, data)
        regex_pvs = {}
        for match in re_matches:
            regex_pvs.update(match.groupdict())
        logging.level_debug() and logging.log_every_n(
            2,
            f'Processed regex: {re_pattern} on {key}:{data} to get {regex_pvs}',
            self._log_every_n)
        if regex_pvs:
            self._counters.add_counter('processed-regex', 1, re_pattern)
            pv_utils.pvs_update(regex_pvs, pvs,
                                self._config.get('multi_value_properties', {}))
            pvs.pop(regex_key)
            return True
        return False

    def _process_format(self, key: str, data: str, pvs: dict,
                        data_key: str) -> bool:
        """Processes a #Format property and updates pvs."""
        format_key = self._config.get('format_key', '#Format')
        if format_key not in pvs:
            return False

        format_str = pvs[format_key]
        (format_prop, strf) = _get_variable_expr(format_str, data_key)
        try:
            format_data = strf.format(**pvs)
            logging.level_debug() and logging.log_every_n(
                2,
                f'Processed format {format_prop}={strf} on {key}:{data} to get'
                f' {format_data}', self._log_every_n)
        except (KeyError, ValueError) as e:
            format_data = format_str
            self._counters.add_counter('error-process-format', 1, format_str)
            logging.level_debug() and logging.log_every_n(
                2, f'Failed to format {format_prop}={strf} on {key}:{data} with'
                f' {pvs}, {e}', self._log_every_n)
        if format_prop != data_key and format_data != format_str:
            pvs[format_prop] = format_data
            self._counters.add_counter('processed-format', 1, format_str)
            pvs.pop(format_key)
            return True
        return False

    def _process_eval(self, pvs: dict, data_key: str) -> bool:
        """Processes a #Eval property and updates pvs."""
        eval_key = self._config.get('eval_key', '#Eval')
        if eval_key not in pvs:
            return False

        eval_str = pvs[eval_key]
        eval_prop, eval_data = eval_functions.evaluate_statement(
            eval_str,
            pvs,
            self._config.get('eval_globals', eval_functions.EVAL_GLOBALS),
        )
        logging.level_debug() and logging.log_every_n(
            2,
            f'Processed eval {eval_str} with {pvs} to get {eval_prop}:{eval_data}',
            self._log_every_n)
        if not eval_prop:
            eval_prop = data_key
        if eval_data is not None and eval_data != eval_str:
            pvs[eval_prop] = eval_data
            self._counters.add_counter('processed-eval', 1, eval_str)
            pvs.pop(eval_key)
            return True
        return False

    def get_pvs_for_key(self, key: str, namespace: str = 'GLOBAL') -> dict:
        """Return a dict of property-values that are mapped to the given key
    within the dictionary for the namespace.

    Args:
      key: input string to be looked up
      namespace: the top level dictionary key to get the map within which
        input-string is looked up.

    Returns:
      dictionary of property:values for the input string.
    """
        pvs = None
        logging.level_debug() and logging.log_every_n(
            3, f'Search PVs for {namespace}:{key}', self._log_every_n)
        if namespace in self._pv_map:
            pvs = self._pv_map[namespace].get(key, None)
        else:
            # Check if key is unique and exists in any other map.
            dicts_with_key = []
            pvs = {}
            namespaces = self._config.get('default_pv_maps', ['GLOBAL'])
            for namespace in namespaces:
                logging.level_debug() and logging.log_every_n(
                    3, f'Search PVs for {namespace}:{key}', self._log_every_n)
                if namespace in self._pv_map.keys():
                    pv_map = self._pv_map[namespace]
                    if key in pv_map:
                        dicts_with_key.append(namespace)
                        pv_utils.pvs_update(
                            pv_map[key], pvs,
                            self._config.get('multi_value_properties', {}))
            if len(dicts_with_key) > 1:
                logging.log_every_n(
                    logging.WARNING,
                    f'Duplicate key {key} in property maps: {dicts_with_key}',
                    self._log_every_n)
                self._counters.add_counter(
                    f'warning-multiple-property-key',
                    1,
                    f'{key}:' + ','.join(dicts_with_key),
                )
        if not pvs:
            logging.level_debug() and logging.log_every_n(
                3, f'Missing key {key} in property maps', self._log_every_n)
            self._counters.add_counter(f'warning-missing-property-key', 1, key)
            return pvs
        logging.level_debug() and logging.log_every_n(
            logging.DEBUG, f'Got PVs for {key}:{pvs}', self._log_every_n)
        return pvs

    def get_pvs_for_key_variants(self,
                                 key: str,
                                 namespace: str = 'GLOBAL') -> list:
        """Return a dict of property-values that are mapped to the given key
     or its variantes with case lower case.
    Args:
      key: input string to be looked up
      namespace: the top level dictionary key to get the map within which
        input-string is looked up.

    Returns:
      a list of dictionary of property:values for the input string.
    """
        if not key:
            return None
        pvs = self.get_pvs_for_key(key, namespace)
        if not pvs:
            # Check if GLOBAL map has key namespace:column-key
            pvs = self.get_pvs_for_key(f'{namespace}:{key}')
        if not pvs:
            pvs = self.get_pvs_for_key(key.lower(), namespace)
        if pvs:
            pvs_list = [pvs]
            pvs_list.append({self._config.get('pv_lookup_key', 'Key'): key})
            return pvs_list
        # Check for keys with extra characters removed.
        key_filtered = re.sub('[^A-Za-z0-9_%$-]+', ' ', key).strip()
        if key_filtered != key:
            return self.get_pvs_for_key_variants(key_filtered, namespace)
        return None

    def _is_key_in_value(self, key: str, value: str) -> bool:
        """Returns True if key is a substring of the value string.

    Only substrings separated by the word boundary are considered.
    """
        if self._config.get('match_substring_word_boundary', True):
            # Match substring around word boundaries.
            while value:
                pos = value.find(key)
                if pos < 0:
                    return False
                if (pos == 0 or not value[pos - 1].isalpha()) and (
                        pos + len(key) <= len(value) or
                        not value[pos + len(key)].isalpha()):
                    return True
                value = value[pos:]
            return False
            # key_pat = f'\\b{key}\\b'
            # try:
            #  if re.search(key_pat, value, flags=re.IGNORECASE):
            #    return True
            #  else:
            #    return False
            # except re.error as e:
            #    logging.log_every_n(logging.ERROR,
            #        f'Failed re.search({key_pat}, {value}) with exception: {e}'
            #    , self._log_every_n)
            #    return False

        # Simple substring without word boundary checks.
        if key.lower() in value.lower():
            return True
        return False

    def get_pvs_for_key_substring(self,
                                  value: str,
                                  namespace: str = 'GLOBAL') -> dict:
        """Return a dict of property-values for any key is a substring of value

    Args:
      value: input string to be mapped to property:values
      namespace: column header or context for the value string used as the key
        for the first level dictionary in the pv_map.

    Returns:
      List of dictionary of property:values that apply to the input string
      after collecting all PVs for any key that is a substring of the value.
    """
        # Get a list of namespaces to lookup.
        # If none given, lookup in all namespaces.
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
            sorted_keys = sorted(pv_map.keys(), key=len, reverse=True)
            for key in sorted_keys:
                if self._is_key_in_value(key, value):
                    pvs_list.append(pv_map[key])
                    keys_list.append(key)
                    logging.level_debug() and logging.log_every_n(
                        3, f'Got PVs for {key} in {value}: {pvs_list}',
                        self._log_every_n)
                    value = value.replace(key, ' ')
        logging.level_debug() and logging.log_every_n(
            2,
            f'Returning pvs for substrings of {value} from {keys_list}:{pvs_list}',
            self._log_every_n)
        return pvs_list

    def get_all_pvs_for_value(self,
                              value: str,
                              namespace: str = 'GLOBAL',
                              max_fragment_size: int = None) -> list:
        """Return a list of property:value dictionaries for an input string.

    Args:
      value: input string to be mapped to property:values
      namespace: context for the input string such as the column header.
      max_fragment_size: the maximum number of words into which value can be
        fragmented when looking for matching keys in the pv_map.

    Returns:
      a list of dictionary of property:values.
    """
        logging.level_debug() and logging.log_every_n(
            1, f'Looking up PVs for {namespace}:{value}', self._log_every_n)
        pvs = self.get_pvs_for_key_variants(value, namespace)
        if pvs:
            return pvs
        # Split the value into n-grams and lookup PVs for each fragment.
        word_delimiter = self._config.get('word_delimiter', ' ')
        if not word_delimiter:
            # Splitting of words is disabled. Don't match substrings.
            return None
        word_joiner = pv_utils.get_delimiter_char(word_delimiter)
        words = pv_utils.get_words(value, word_delimiter)
        if len(words) <= 1:
            return None
        max_fragment_words = len(words) - 1
        if not max_fragment_size:
            max_fragment_size = self._max_words_in_keys
        max_fragment_words = min(max_fragment_words, max_fragment_size)

        num_grams = (len(words) - max_fragment_size)**2
        if self._num_pv_map_keys < num_grams:
            # Fewer keys than n-grams in input.
            # Get PVs for keys in pv_map that are a substring of the input value.
            return self.get_pvs_for_key_substring(value, namespace)
        # Fewer n-grams than number of keys in map.
        # Check if any input n-gram matches a key.
        logging.level_debug() and logging.log_every_n(
            3, f'Looking up PVs for {max_fragment_words} words in {words}',
            self._log_every_n)
        for num_words in range(max_fragment_words, 0, -1):
            for start_index in range(0, len(words) - num_words + 1):
                sub_value = word_joiner.join(words[start_index:start_index +
                                                   num_words])
                sub_pvs = self.get_pvs_for_key_variants(sub_value, namespace)
                if sub_pvs:
                    # Got PVs for a fragment.
                    # Also lookup remaining fragments before and after this.
                    pvs_list = []
                    before_value = word_delimiter.join(words[0:start_index])
                    after_value = word_delimiter.join(words[start_index +
                                                            num_words:])
                    logging.level_debug() and logging.log_every_n(
                        3, f'Got PVs for {start_index}:{num_words} in'
                        f' {words}:{sub_value}:{sub_pvs}, lookup pvs for {before_value},'
                        f' {after_value}', self._log_every_n)
                    before_pvs = self.get_all_pvs_for_value(
                        # before_value, namespace, max_fragment_size=None)
                        before_value,
                        namespace,
                        max_fragment_size=num_words,
                    )
                    after_pvs = self.get_all_pvs_for_value(
                        # after_value, namespace, max_fragment_size=None)
                        after_value,
                        namespace,
                        max_fragment_size=num_words,
                    )
                    if before_pvs:
                        pvs_list.extend(before_pvs)
                    pvs_list.extend(sub_pvs)
                    if after_pvs:
                        pvs_list.extend(after_pvs)
                    logging.level_debug() and logging.log_every_n(
                        2, f'Got PVs for fragments {before_value}:{before_pvs},'
                        f' {sub_value}:{sub_pvs}, {after_value}:{after_pvs}',
                        self._log_every_n)
                    return pvs_list
        return None


# Local utility functions
def _get_variable_expr(stmt: str, default_var: str = 'Data') -> (str, str):
    """Parses a statement of the form <variable>=<expr> and returns variable, expr."""
    if '=' in stmt:
        (var, expr) = stmt.split('=', 1)
        return (var.strip(), expr)
    return (default_var, stmt)


# PVMap utility functions
def load_pv_map(file: str) -> dict:
    """Returns a PV map loaded from a file."""
    pvmap = PropertyValueMapper()
    for file in file_util.file_get_matching(file):
        pvmap.load_pvs_from_file(file)
    pvs = pvmap.get_pv_map()
    # Return the pvmap for the first namespace
    if pvs:
        return pvs[list(pvs.keys())[0]]
    return {}


def write_pv_map(pvmap: dict, file: str) -> str:
    """Write the PV map into a file."""
    if file_util.file_is_csv(file):
        # Write pvmap as csv file with rows as : key,prop1,value1,prop2,value2
        with file_util.FileIO(file, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            # Set CSV header as 'key, prop, value'
            csv_writer.writerow(['key', 'property', 'value'])
            # Write each pvmap node as a row.
            for key, pvs in pvmap.items():
                row = [key]
                for prop, value in pvs.items():
                    row.append(prop)
                    row.append(value)
                csv_writer.writerow(row)
    else:
        file_util.file_write_py_dict(pvmap, file)
    logging.info(f'Wrote {len(pvmap)} rows of PVs into {file}')
