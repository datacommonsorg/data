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
"""Class to generate StatVar and StatVarObs from data files.

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

For more details on configs and usage, please refer to the README.
"""

from collections import OrderedDict
import csv
import datetime
import glob
import itertools
import multiprocessing
import os
import re
import sys
import tempfile
import time
from typing import Union

from absl import app
from absl import flags
from absl import logging
import dateutil
from dateutil import parser
from dateutil.parser import parse
import pandas as pd
import process_http_server
import requests

# uncomment to run pprof
# os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
# from pypprof.net_http import start_pprof_server

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util')
)

import eval_functions
import file_util
import config_flags

from mcf_file_util import get_numeric_value
from mcf_file_util import load_mcf_nodes, write_mcf_nodes, add_namespace, strip_namespace
from mcf_filter import drop_existing_mcf_nodes
from mcf_diff import fingerprint_node, fingerprint_mcf_nodes, diff_mcf_node_pvs
from place_resolver import PlaceResolver
from schema_resolver import SchemaResolver
from json_to_csv import file_json_to_csv
from schema_generator import generate_schema_nodes

# imports from ../../util
from config_map import ConfigMap, read_py_dict_from_file
from counters import Counters, CounterOptions
from dc_api_wrapper import dc_api_is_defined_dcid
from download_util import download_file_from_url
from statvar_dcid_generator import get_statvar_dcid

_FLAGS = flags.FLAGS


# Local utility functions
def _is_valid_property(prop: str, schemaless: bool = False) -> bool:
  """Returns True if the property begins with a letter, lowercase.

  If schemaless is true, property can begin with uppercase as well.
  """
  if prop and isinstance(prop, str) and prop[0].isalpha():
    if schemaless or prop[0].islower():
      return True
  return False


def _is_valid_value(value: str) -> bool:
  """Returns True if the value is valid without any references."""
  if value is None:
    return False
  if isinstance(value, str):
    # Check there are no unresolved references.
    if not value or value == '""':
      return False
    if '@' in value:
      # Quoted strings can have @<2-letter-lang> suffix.
      if not re.search('@[a-z]{2}"$', value):
        return False
    if '{' in value and '}' in value:
      return False
  return True


def _is_schema_node(value: str) -> bool:
  """Returns True if the value is a schema node reference."""
  if not value or not isinstance(value, str):
    return False
  if not value[0].isalpha() and value[0] != '[':
    # Numbers or quoted strings are not schema nodes.
    return False
  # Check if string has any non alpha or non numeric codes
  non_alnum_chars = [
      c
      for c in strip_namespace(value)
      if not c.isalnum() and c not in ['_', '/', '[', ']', '.']
  ]
  if non_alnum_chars:
    return False
  return True


def _has_namespace(value: str) -> bool:
  """Returns True if the value has a namespace of letters followed by ':'."""
  if not value or not isinstance(value, str):
    return False
  len_value = len(value)
  pos = 0
  while pos < len_value:
    if not value[pos].isalpha():
      break
    pos += 1
  if pos < len_value and value[pos] == ':':
    return True
  return False


def _get_words(value: str, word_delimiter: str) -> list:
  """Returns the list of non-empty words separated by the delimiter."""
  return [w for w in re.split(word_delimiter, value) if w]


def _get_delimiter_char(re_delimiter: str) -> str:
  """Returns a single delimiter character that can be used to join words

  from the first character in the delimiter regex.
  """
  if re_delimiter:
    if '|' in re_delimiter:
      return re_delimiter.split('|')[0]
    if re_delimiter[0] == '[':
      return re_delimiter[1]
  return ' '


def _add_key_value(
    key: str,
    value: str,
    pvs: dict,
    multi_value_keys: set = {},
    overwrite: bool = True,
) -> dict:
  """Adds a key:value to the dict.

  If the key already exists, adds value to a list if key is a multi_value key,
  else replaces the value if overwrite is True.
  """
  if key not in pvs:
    # Add a new key:value
    pvs[key] = value
  else:
    # Key exists. Check if value can be added.
    if key not in multi_value_keys:
      # Replace existing value with a new one.
      if overwrite:
        pvs[key] = value
    else:
      # This key can have multiple values.
      # Add to a list of values if it doesn't exist already.
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


def _pvs_update(new_pvs: dict, pvs: dict, multi_value_keys: set = {}) -> dict:
  """Add the key:value pairs from the new_pvs into the pvs dictionary."""
  for prop, value in new_pvs.items():
    _add_key_value(prop, value, pvs, multi_value_keys)
  return pvs


def _capitalize_first_char(string: str) -> str:
  """Returns a string with the first letter capitalized."""
  if not string or not isinstance(string, str):
    return string
  return string[0].upper() + string[1:]


def _get_variable_expr(stmt: str, default_var: str = 'Data') -> (str, str):
  """Parses a statement of the form <variable>=<expr> and returns variable, expr."""
  if '=' in stmt:
    (var, expr) = stmt.split('=', 1)
    return (var.strip(), expr)
  return (default_var, stmt)


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
        f'Loaded PV map {self._pv_map} with max words {self._max_words_in_keys}'
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
      # Load rows into a dict of prop,value
      # if the first col is a config key, next column is its value
      logging.info(f'Loading PV maps for {namespace} from csv file: {filename}')
      with file_util.FileIO(filename) as csvfile:
        csv_reader = csv.reader(csvfile, skipinitialspace=True, escapechar='\\')
        for row in csv_reader:
          # Drop trailing empty columns in the row
          last_col = len(row) - 1
          while last_col >= 0 and row[last_col].strip() == '':
            last_col -= 1
          row = row[: last_col + 1]
          if not row:
            continue
          key = row[0]
          if key in self._config.get_configs():
            # Add value to the config with same type as original.
            value = ','.join(row[1:])
            config_flags.set_config_value(key, value, self._config)
          else:
            # Row is a pv map
            pvs_list = row[1:]
            if len(pvs_list) == 1:
              # PVs list has no property, just a value.
              # Use the namespace as the property
              pvs_list = [namespace]
              pvs_list.append(row[1])
            if len(pvs_list) % 2 != 0:
              logging.fatal(
                  f'Invalid list of property value: {row} in {filename}'
              )
            # Get property,values from the columns
            pvs = {}
            for i in range(0, len(pvs_list), 2):
              prop = pvs_list[i].strip()
              if not prop:
                continue
              value = pvs_list[i + 1].strip()
              # Remove extra quotes around schema values.
              # if value and value[0] == '"' and value[-1] == '"':
              #  value = value[1:-1].strip()
              if value and value[0] != '[' and prop[0] != '#':
                # Add quotes around text strings
                # with spaces without commas.
                # if re.search('[^,] +', value):
                #  value = f'"{value}"'
                if value[0] == "'" and value[-1] == "'":
                  # Replace single quote with double quotes
                  # To distinguish quote as delimiter vs value in CSVs
                  # single quote is used instead of doublw quote in CSV values.
                  value[0] = '"'
                  value[-1] = '"'
              pvs[prop] = value
            pv_map_input[key] = pvs
    else:
      logging.info(
          f'Loading PV maps for {namespace} from dictionary file: {filename}'
      )
      pv_map_input = read_py_dict_from_file(filename)
    self.load_pvs_dict(pv_map_input, namespace)

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
        if p in pvs_dict:
          # A property has multiple values from different configs.
          # Concatenate new value to existing one with '__'
          if v not in pvs_dict[p]:
            pvs_dict[p] = '__'.join(sorted([pvs_dict[p], v]))
            logging.info(f'Joining values for {key}[{p}] into {pvs_dict[p]}')
        else:
          pvs_dict[p] = v
          num_keys_added += 1
      # Track the max number of words in any of the keys.
      # This is used when splitting input-string for lookups.
      num_words_key = len(_get_words(key, word_delimiter))
      self._max_words_in_keys = max(self._max_words_in_keys, num_words_key)
      logging.level_debug() and logging.log(
          2, f'Setting PVMap[{key}] = {pvs_dict}'
      )

    self._num_pv_map_keys += num_keys_added
    logging.info(
        f'Loaded {num_keys_added} property-value mappings for "{namespace}"'
    )
    logging.level_debug() and logging.debug(
        f'Loaded pv map {namespace}:{pv_map_input}'
    )

  def get_pv_map(self) -> dict:
    """Returns the dictionary mapping input-strings to property:values."""
    return self._pv_map

  def process_pvs_for_data(self, key: str, pvs: dict) -> bool:
    """Returns true if property:values are processed successfully.

    Processes values for actionable props such as '#Regex', '#Eval', '#Format'.
    Args: pvs (input/output) dictionary of property:values Properties such as
    '#Regex', '#Eval', '#Format' are processed and resulting properties are
    updated into pvs.

    Returns:
       True if any property:values were processed and pvs dict was updated.
    """
    logging.level_debug() and logging.debug(f'Processing data PVs:{key}:{pvs}')
    data_key = self._config.get('data_key', 'Data')
    data = pvs.get(data_key, key)
    is_modified = False

    # Process regular expression and add named group matches to the PV.
    # Regex PV is of the form: '#Regex': '(?P<Start>[0-9]+) *- *(?P<End>[0-9])'
    # Parses 'Data': '10 - 20' to generate PVs:
    # { 'Start': '10', 'End': '20' }
    regex_key = self._config.get('regex_key', '#Regex')
    if regex_key in pvs and data:
      re_pattern = pvs[regex_key]
      re_matches = re.finditer(re_pattern, data)
      regex_pvs = {}
      for match in re_matches:
        regex_pvs.update(match.groupdict())
      logging.level_debug() and logging.debug(
          f'Processed regex: {re_pattern} on {key}:{data} to get {regex_pvs}'
      )
      if regex_pvs:
        self._counters.add_counter('processed-regex', 1, re_pattern)
        _pvs_update(
            regex_pvs, pvs, self._config.get('multi_value_properties', {})
        )
        pvs.pop(regex_key)
        is_modified = True

    # Format the data substituting properties with values.
    format_key = self._config.get('format_key', '#Format')
    if format_key in pvs:
      format_str = pvs[format_key]
      (format_prop, strf) = _get_variable_expr(format_str, data_key)
      try:
        format_data = strf.format(**pvs)
        logging.level_debug() and logging.debug(
            f'Processed format {format_prop}={strf} on {key}:{data} to get'
            f' {format_data}'
        )
      except (KeyError, ValueError) as e:
        format_data = format_str
        self._counters.add_counter('error-process-format', 1, format_str)
        logging.level_debug() and logging.debug(
            f'Failed to format {format_prop}={strf} on {key}:{data} with'
            f' {pvs}, {e}'
        )
      if format_prop != data_key and format_data != format_str:
        pvs[format_prop] = format_data
        self._counters.add_counter('processed-format', 1, format_str)
        pvs.pop(format_key)
        is_modified = True

    # Evaluate the expression properties as local variables.
    eval_key = self._config.get('eval_key', '#Eval')
    if eval_key in pvs:
      eval_str = pvs[eval_key]
      eval_prop, eval_data = eval_functions.evaluate_statement(
          eval_str,
          pvs,
          self._config.get('eval_globals', eval_functions.EVAL_GLOBALS),
      )
      logging.level_debug() and logging.debug(
          f'Processed eval {eval_str} with {pvs} to get {eval_prop}:{eval_data}'
      )
      if not eval_prop:
        eval_prop = data_key
      if eval_data and eval_data != eval_str:
        pvs[eval_prop] = eval_data
        self._counters.add_counter('processed-eval', 1, eval_str)
        pvs.pop(eval_key)
        is_modified = True
    logging.level_debug() and logging.debug(
        f'Processed data PVs:{is_modified}:{key}:{pvs}'
    )
    return is_modified

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
    logging.level_debug() and logging.log(
        3, f'Search PVs for {namespace}:{key}'
    )
    if namespace in self._pv_map:
      pvs = self._pv_map[namespace].get(key, None)
    else:
      # Check if key is unique and exists in any other map.
      dicts_with_key = []
      pvs = {}
      namespaces = self._config.get('default_pv_maps', ['GLOBAL'])
      for namespace in namespaces:
        logging.level_debug() and logging.log(
            3, f'Search PVs for {namespace}:{key}'
        )
        if namespace in self._pv_map.keys():
          pv_map = self._pv_map[namespace]
          if key in pv_map:
            dicts_with_key.append(namespace)
            _pvs_update(
                pv_map[key], pvs, self._config.get('multi_value_properties', {})
            )
      if len(dicts_with_key) > 1:
        logging.warning(
            f'Duplicate key {key} in property maps: {dicts_with_key}'
        )
        self._counters.add_counter(
            f'warning-multiple-property-key',
            1,
            f'{key}:' + ','.join(dicts_with_key),
        )
    if not pvs:
      logging.level_debug() and logging.log(
          3, f'Missing key {key} in property maps'
      )
      self._counters.add_counter(f'warning-missing-property-key', 1, key)
      return pvs
    logging.level_debug() and logging.debug(f'Got PVs for {key}:{pvs}')
    return pvs

  def get_pvs_for_key_variants(
      self, key: str, namespace: str = 'GLOBAL'
  ) -> list:
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
            pos + len(key) <= len(value) or not value[pos + len(key)].isalpha()
        ):
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
      #    logging.error(
      #        f'Failed re.search({key_pat}, {value}) with exception: {e}'
      #    )
      #    return False

    # Simple substring without word boundary checks.
    if key.lower() in value.lower():
      return True
    return False

  def get_pvs_for_key_substring(
      self, value: str, namespace: str = 'GLOBAL'
  ) -> dict:
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
          logging.level_debug() and logging.log(
              3, f'Got PVs for {key} in {value}: {pvs_list}'
          )
          value = value.replace(key, ' ')
    logging.level_debug() and logging.debug(
        f'Returning pvs for substrings of {value} from {keys_list}:{pvs_list}'
    )
    return pvs_list

  def get_all_pvs_for_value(
      self, value: str, namespace: str = 'GLOBAL', max_fragment_size: int = None
  ) -> list:
    """Return a list of property:value dictionaries for an input string.

    Args:
      value: input string to be mapped to property:values
      namespace: context for the input string such as the column header.
      max_fragment_size: the maximum number of words into which value can be
        fragmented when looking for matching keys in the pv_map.

    Returns:
      a list of dictionary of property:values.
    """
    logging.level_debug() and logging.log(
        1, f'Looking up PVs for {namespace}:{value}'
    )
    pvs = self.get_pvs_for_key_variants(value, namespace)
    if pvs:
      return pvs
    # Split the value into n-grams and lookup PVs for each fragment.
    word_delimiter = self._config.get('word_delimiter', ' ')
    if not word_delimiter:
      # Splitting of words is disabled. Don't match substrings.
      return None
    word_joiner = _get_delimiter_char(word_delimiter)
    words = _get_words(value, word_delimiter)
    if len(words) <= 1:
      return None
    max_fragment_words = len(words) - 1
    if not max_fragment_size:
      max_fragment_size = self._max_words_in_keys
    max_fragment_words = min(max_fragment_words, max_fragment_size)

    num_grams = (len(words) - max_fragment_size) ** 2
    if self._num_pv_map_keys < num_grams:
      # Fewer keys than n-grams in input.
      # Get PVs for keys in pv_map that are a substring of the input value.
      return self.get_pvs_for_key_substring(value, namespace)
    # Fewer n-grams than number of keys in map.
    # Check if any input n-gram matches a key.
    logging.level_debug() and logging.log(
        3, f'Looking up PVs for {max_fragment_words} words in {words}'
    )
    for num_words in range(max_fragment_words, 0, -1):
      for start_index in range(0, len(words) - num_words + 1):
        sub_value = word_joiner.join(
            words[start_index : start_index + num_words]
        )
        sub_pvs = self.get_pvs_for_key_variants(sub_value, namespace)
        if sub_pvs:
          # Got PVs for a fragment.
          # Also lookup remaining fragments before and after this.
          pvs_list = []
          before_value = word_delimiter.join(words[0:start_index])
          after_value = word_delimiter.join(words[start_index + num_words :])
          logging.level_debug() and logging.log(
              3,
              f'Got PVs for {start_index}:{num_words} in'
              f' {words}:{sub_value}:{sub_pvs}, lookup pvs for {before_value},'
              f' {after_value}',
          )
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
          logging.level_debug() and logging.debug(
              f'Got PVs for fragments {before_value}:{before_pvs},'
              f' {sub_value}:{sub_pvs}, {after_value}:{after_pvs}'
          )
          return pvs_list
    return None


class StatVarsMap:
  """Class to store StatVars and StatVarObs in a map.

  _statvar_map: dictionary with dcid as the key mapped

     to a dictionary of property:values
  _statvar_obs_map:
     dictionary with the fingerprint of place+date+variable as key
     mapped to dictionary of property:values for StatVarObs.

  Both maps may include additional internal properties such as '#Error...',
  '#input' that are used for validation and debugging.

  Processing options are passed in through a config object.
  The following configurations are used in this class:
    - schemaless: bool: to indicate support for schemaless statvars.
    - statvar_dcid_ignore_values: set of values in data source to be ignored
        such as 'NA', 'X', etc.
    - default_statvar_pvs: default property:values applicable to Statvars
    - default_svobs_pvs: default property:values applicable to StatVarVObs
    - required_statvar_properties: mandatory properties for a StatVar
    - required_statvarobs_properties: mandatory properties for a StatVarObs
    - duplicate_statvars_key: internal property to store a reference to
       duplicate statvar with same dcid but different properties.
       Such statVars and corresponding SVObs are dropped from the output.
       This is usually caused by insufficiently specified StatVar
       missing some properties.
    - duplicate_svobs_key: internal property for duplicate SVObs
        for the same place+year+StatVar but different values.
        If aggregate_duplicate_svobs is enabled, such duplicates are aggregated.
        If not this is treated as an error and the SVObs and
        the corresponding Statvars are dropped from the output.
    - aggregate_duplicate_svobs: aggregate SVObs with the same
        place+date+StatVar based on the '#Aggregate' property
        which indicates type of aggregation such as sum/min/max.
    - merged_pvs_prop: internal property (#MergedSVObs) to store references
        to SVObs that were aggregated to obtain the final value.
    - schemaless_statvar_comment_undefined_pvs: if True, when emitting
      schemaless statvars, valid properties that are not yet defined
        in the DC APi are commented out.
        If any such commented properties exist in a StatVar,
        it is converted to a schemaless statvar, i.e,
        its measuredProperty is set to its dcid.

  StatVars and StatVarObs are validated for duplicate values
  with conflicting dcids before being emited to output files.
  """

  # PVs for StatVarObs ignored when looking for dups
  _IGNORE_SVOBS_KEY_PVS = {
      'value': '',
      'measurementResult': '',
  }

  def __init__(self, config_dict: dict = None, counters_dict: dict = None):
    self._config = ConfigMap(config_dict=config_dict)
    self._counters = Counters(
        counters_dict=counters_dict,
        options=CounterOptions(debug=self._config.get('debug', False)),
    )
    # Dictionary of statvar dcid->{PVs}
    self._statvars_map = {}
    # Dictionary of existing statvars keyed by fingerprint
    self._statvar_resolver = SchemaResolver(
        self._config.get('existing_statvar_mcf', None)
    )

    # Dictionary of statvar obs_key->{PVs}
    self._statvar_obs_map = {}
    # Unique values seen per SVObs property.
    self._statvar_obs_props = dict()
    # Cache for DC API lookups.
    self._dc_api_ids_cache = {}
    # Mapping of statvar DCIDs to be renamed.
    self._statvar_dcid_remap = file_util.file_load_csv_dict(
        filename=self._config.get('statvar_dcid_remap_csv', ''),
        value_column='dcid',
    )
    logging.info(f'Loaded remapped statvar dcid: {self._statvar_dcid_remap}')

  def add_default_pvs(self, default_pvs: dict, pvs: dict) -> dict:
    """Add default values for any missing PVs.

    Args:
      default_pvs: dictionary with default property:values. properties with a
        valid value not in pvs are added to it.
      pvs: dictionary of property:values to be modified.

    Returns:
      dictionary of property:values after addition of default PVs.
    """
    if default_pvs:
      for prop, value in default_pvs.items():
        if (
            _is_valid_property(prop, self._config.get('schemaless', False))
            and value
            and prop not in pvs
        ):
          pvs[prop] = value
    return pvs

  def get_valid_pvs(self, pvs: dict) -> dict:
    """Return all valid property:value in the dictionary.

    Args:
      pvs: dictionary of property:value mappings. property is considered valid
        if if begins with a lower case or config for schemaless statvars is
        enabled. schemaless statvars can have capitalized properties that are
        commented out in the mcf. value is considered valid if it has no
        unresolved references.

    Returns:
      dictionary of valid property:value mappings
    """
    valid_pvs = {}
    for prop, value in pvs.items():
      if _is_valid_property(
          prop, self._config.get('schemaless', False)
      ) and _is_valid_value(value):
        valid_pvs[prop] = value
    return valid_pvs

  def add_dict_to_map(
      self,
      key: str,
      pvs: dict,
      pv_map: dict,
      duplicate_prop: str = None,
      allow_equal_pvs: bool = True,
      ignore_props: list = [],
  ) -> bool:
    """Returns true if the key:pvs is added to the pv_map,

      False if key already exists and values don't match.
    Args:
      key: the key to be added to the pv_map
      pvs: the dictionary value mapped to the key
      pv_map: (output) dictionary to which key is to be added.
      duplicate_prop: In case of duplicate entries, add this duplicate prop
        mapped to the pvs dict into the existing entry.
      allow_equal_pvs: If True duplicate pvs with the same property:value is not
        considered an error.

    Returns:
      True if the key:pvs tuple was added to the pv_map.
    """
    if key in pv_map:
      has_diff, diff_str, added, deleted, modified = diff_mcf_node_pvs(
          self.get_valid_pvs(pvs),
          self.get_valid_pvs(pv_map[key]),
          config={'ignore_property': ignore_props},
      )
      if allow_equal_pvs and not has_diff:
        return True
      else:
        logging.level_debug() and logging.debug(
            f'Duplicate entry {key} in map for {pvs}, diff: {diff_str}'
        )
        if duplicate_prop:
          map_pvs = pv_map[key]
          if duplicate_prop not in map_pvs:
            map_pvs[duplicate_prop] = []
          map_pvs[duplicate_prop].append(pvs)
        return False
    pv_map[key] = pvs
    return True

  def _get_dcid_term_for_pv(self, prop: str, value: str) -> str:
    """Returns the dcid term for the property:value to be used in the node's dcid.

    Args:
      prop: the property label
      value: value of the property

    Returns:
      string to be used for this PV in the dcid.
    For schemaless statvars, the property and value is used for the dcid term.
    Otherwise the term is constructed from the value.
    """
    if not value:
      return _capitalize_first_char(prop)

    if not isinstance(value, str):
      # For numeric values use the property and value.
      return _capitalize_first_char(
          re.sub(r'[^A-Za-z0-9_/]', '_', f'{prop}_{value}').replace('__', '_')
      )
    prefix = ''
    value = strip_namespace(value)
    if self._config.get('schemaless', False):
      # Add the property prefix for schemaless PVs.
      if not _is_valid_property(prop, schemaless=False) and _is_valid_property(
          prop, schemaless=True
      ):
        prop = prop.removeprefix('# ')
        if prop != value:
          prefix = _capitalize_first_char(f'{prop}_')
    if value[0] == '[':
      # Generate term for quantity range with start and optional end, unit.
      quantity_pat = (
          r'\[ *(?P<unit1>[A-Z][A-Za-z0-9_/]*)? *(?P<start>[0-9\.]+|-)?'
          r' *(?P<end>[0-9\.]+|-)? *(?P<unit2>[A-Z][A-Za-z0-9_]*)? *\]'
      )
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
    return prefix + _capitalize_first_char(value)

  def _get_schemaless_statvar_props(self, pvs: dict) -> list:
    """Returns a list of schemaless properties from the dictionary of property:values.

    Properties not defined in schema can be capitalized or commented.
    """
    schemaless_props = []
    for prop in pvs.keys():
      if prop == 'Node' or _is_valid_property(prop, schemaless=False):
        continue
      if _is_valid_property(prop, schemaless=True) or prop.startswith('# '):
        # TODO: skip internal props '#...' instead of checking prefix '# '
        schemaless_props.append(prop)
    return schemaless_props

  def generate_statvar_dcid(self, pvs: dict) -> str:
    """Return the dcid for the statvar.

    Args:
      pvs: dictionary of property:values

    Returns:
      dcid string.
    For normal statvars, uses statvar_dcid_generator.py
    For schameless statvars, uses the local implementation to add prop and
    value.
    """
    dcid = pvs.get('dcid', pvs.get('Node', ''))
    if dcid:
      return dcid
    # Check if a statvar already exists.
    pvs = self._get_exisisting_statvar(pvs)
    dcid = pvs.get('dcid', pvs.get('Node', ''))
    if dcid:
      logging.level_debug() and logging.debug(
          f'Reusing existing statvar {dcid} for {pvs}'
      )
      return dcid

    # Use the statvar_dcid_generator for statvars with defined properties.
    dcid_ignore_props = self._config.get(
        'statvar_dcid_ignore_properties',
        ['description', 'name', 'nameWithLanguage'],
    )
    if not self._config.get(
        'schemaless', False
    ) or not self._get_schemaless_statvar_props(pvs):
      try:
        dcid = get_statvar_dcid(pvs, ignore_props=dcid_ignore_props)
        dcid = re.sub(r'[^A-Za-z_0-9/_\.-]+', '_', dcid)
      except TypeError as e:
        logging.error(f'Failed to generate dcid for statvar:{pvs}, error: {e}')
        dcid = ''
    if not dcid:
      # Create a new dcid from PVs.
      dcid_terms = []
      props = list(pvs.keys())
      dcid_ignore_values = self._config.get('statvar_dcid_ignore_values', [])
      for p in self._config.get('default_statvar_pvs', {}).keys():
        if p in props and p not in dcid_ignore_props:
          props.remove(p)
          value = strip_namespace(pvs[p])
          if value and value not in dcid_ignore_values:
            dcid_terms.append(self._get_dcid_term_for_pv(p, value))
      dcid_suffixes = []
      if 'measurementDenominator' in props:
        dcid_suffixes.append('AsAFractionOf')
        dcid_suffixes.append(strip_namespace(pvs['measurementDenominator']))
        props.remove('measurementDenominator')
      for p in sorted(props, key=str.casefold):
        if p not in dcid_ignore_props:
          value = pvs[p]
          if _is_valid_property(
              p, self._config.get('schemaless', False)
          ) and _is_valid_value(value):
            dcid_terms.append(self._get_dcid_term_for_pv(p, value))
      dcid_terms.extend(dcid_suffixes)
      dcid = re.sub(r'[^A-Za-z_0-9/_-]+', '_', '_'.join(dcid_terms))
      dcid = re.sub(r'_$', '', dcid)

    # Check if the dcid is remapped.
    remap_dcid = self._statvar_dcid_remap.get(strip_namespace(dcid), '')
    if remap_dcid:
      logging.level_debug() and logging.debug(
          f'Remapped {dcid} to {remap_dcid} for {pvs}'
      )
      self._counters.add_counter(f'remapped-statvar-dcid', 1, remap_dcid)
      dcid = remap_dcid
    pvs['Node'] = add_namespace(dcid)
    logging.level_debug() and logging.debug(f'Generated dcid {dcid} for {pvs}')
    return dcid

  def remove_undefined_properties(
      self,
      pv_map_dict: dict,
      ignore_props: list = [],
      comment_removed_props: bool = False,
  ) -> list:
    """Remove any property:value tuples with undefined property or values

    Returns list of properties removed.
    Args:
      pv_map_dict: dictionary of dcids mapped to a dictionary of property:values
      ignore_props: ignore any of these properties
      comment_removed_props: if set to True, any property not defined in schema
        is commented out. This is useful for a schemaless statvar with a mix of
        defined and undefined properties.

    Returns:
      list of properties removed.
      the pv_map_dict is also updated in place.

    Batches property and values to be looked up in the DC API.
    """
    # Collect all property and values to be checked in schema.
    props_removed = []
    lookup_dcids = set()
    for namespace, pv_map in pv_map_dict.items():
      for key, pvs in pv_map.items():
        # Add Node dcids as defined in cache.
        dcid = pvs.get('Node', '')
        dcid = pvs.get('dcid', dcid)
        if dcid:
          dcid = strip_namespace(dcid)
          self._dc_api_ids_cache[dcid] = True
        # Collect property and values not in cache and to be looked up.
        for prop, value in pvs.items():
          if value:
            value = strip_namespace(value)
          if prop in ignore_props:
            continue
          if _is_valid_property(prop, self._config.get('schemaless', False)):
            lookup_dcids.add(prop)
            if _is_schema_node(value):
              lookup_dcids.add(value)

    # Lookup new Ids on the DC API.
    if lookup_dcids:
      api_lookup_dcids = [
          dcid for dcid in lookup_dcids if dcid not in self._dc_api_ids_cache
      ]
      if api_lookup_dcids:
        logging.level_debug() and logging.debug(
            f'Looking up DC API for dcids: {api_lookup_dcids} from PV map.'
        )
        schema_nodes = dc_api_is_defined_dcid(
            api_lookup_dcids, self._config.get_configs()
        )
        # Update cache
        self._dc_api_ids_cache.update(schema_nodes)
        logging.level_debug() and logging.debug(
            f'Got {len(schema_nodes)} of {len(api_lookup_dcids)} dcids from DC'
            ' API.'
        )

    # Remove any PVs not in schema.
    counter_prefix = 'error-pvmap-dropped'
    if comment_removed_props:
      counter_prefix = 'warning-commented-pvmap'
    for namespace, pv_map in pv_map_dict.items():
      for key, pvs in pv_map.items():
        for prop in list(pvs.keys()):
          if prop in ignore_props:
            continue
          value = pvs[prop]
          # Remove property looked up in schema but not defined.
          if prop in lookup_dcids and not self._dc_api_ids_cache.get(
              prop, False
          ):
            logging.error(
                f'Removing undefined property "{prop}" from PV'
                f' Map:{namespace}:{key}:{prop}:{value}'
            )
            value = pvs.pop(prop)
            if comment_removed_props:
              pvs[f'# {prop}: '] = value
            self._counters.add_counter(
                f'{counter_prefix}-undefined-property', 1, prop
            )
          # Remove value looked up in schema but not defined.
          if value in lookup_dcids and not self._dc_api_ids_cache.get(
              value, False
          ):
            logging.error(
                f'Removing undefined value "{value}" from PV'
                f' Map:{namespace}:{key}:{prop}:{value}'
            )
            if prop in pvs:
              pvs.pop(prop)
            if comment_removed_props:
              pvs[f'# {prop}: '] = value
              props_removed.append(prop)
            self._counters.add_counter(
                f'{counter_prefix}-undefined-value', 1, prop
            )
        self._counters.add_counter(f'pvmap-defined-properties', len(pvs))
    return props_removed

  def convert_to_schemaless_statvar(self, pvs: dict) -> dict:
    """Returns the property:values dictionary after converting to schemaless statvar.

      If there are any properties starting with capital letters,
      they are commented and measuredProperty is set to the statvar dcid.
    Args:
      pvs: dictionary of property:values that is modified.

    Returns:
      True if the pvs were converted to schemaless.
    """
    logging.level_debug() and logging.debug(
        f'Converting to schemaless statvar {pvs}'
    )
    schemaless_props = self._get_schemaless_statvar_props(pvs)

    # Got some capitalized properties.
    # Convert to schemaless PV:
    # - set measuredProperty to the dcid.
    # - comment out any capitalized (invalid) property
    dcid = self.generate_statvar_dcid(pvs)
    for prop in schemaless_props:
      if prop[0] != '#':
        value = pvs.pop(prop)
        pvs[f'# {prop}: '] = value
    # Comment out any PVs with undefined property or value.
    if self._config.get('schemaless_statvar_comment_undefined_pvs', False):
      schemaless_props.extend(
          self.remove_undefined_properties(
              {'StatVar': {'SV': pvs}},
              ignore_props=['Node'],
              comment_removed_props=True,
          )
      )
    if schemaless_props:
      # Found some schemaless properties. Change mProp to statvar dcid.
      if 'measuredProperty' in pvs:
        pvs['# measuredProperty:'] = pvs.pop('measuredProperty')
      pvs['measuredProperty'] = add_namespace(dcid)
    logging.level_debug() and logging.debug(
        f'Generated schemaless statvar {pvs}'
    )
    return len(schemaless_props) > 0

  def add_statvar(self, statvar_dcid: str, statvar_pvs: dict) -> bool:
    """Returns True if the statvar pvs are valid and is added to the map.

    Args:
      statvar_pvs: dictionary of property:values for the statvar

    Returns:
      True if statvar is valid, not a duplicate and was added to the map.
      The pvs may also be modified.
      A dcid is added to the statvar if not already set.
    """
    pvs = self.get_valid_pvs(statvar_pvs)
    if not statvar_dcid:
      statvar_dcid = strip_namespace(self.generate_statvar_dcid(pvs))
    pvs['Node'] = add_namespace(statvar_dcid)
    is_schemaless = False
    if self._config.get('schemaless', False):
      is_schemaless = self.convert_to_schemaless_statvar(pvs)
    # Check if all the required statvar properties are present.
    if pvs:
      missing_props = set(
          self._config.get('required_statvar_properties', [])
      ).difference(set(pvs.keys()))
      if missing_props:
        logging.error(f'Missing statvar properties {missing_props} in {pvs}')
        self._counters.add_counter(
            f'error-statvar-missing-property',
            1,
            f'{statvar_dcid}:missing-{missing_props}',
        )
        pvs['#ErrorMissingStatVarProperties'] = missing_props
        return False
    if not self.add_dict_to_map(
        statvar_dcid,
        pvs,
        self._statvars_map,
        self._config.get('duplicate_statvars_key'),
        allow_equal_pvs=True,
        ignore_props=self._config.get(
            'statvar_dcid_ignore_properties',
            ['description', 'name', 'nameWithLanguage'],
        ),
    ):
      logging.error(
          f'Cannot add duplicate statvars for {statvar_dcid}: old:'
          f' {self._statvars_map[statvar_dcid]}, new: {pvs}'
      )
      self._counters.add_counter(f'error-duplicate-statvars', 1, statvar_dcid)
      return False
    logging.level_debug() and logging.debug(f'Adding statvar {pvs}')
    self._counters.add_counter('generated-statvars', 1, statvar_dcid)
    self._counters.set_counter(
        'generated-unique-statvars', len(self._statvars_map)
    )
    if is_schemaless:
      self._counters.add_counter(
          'generated-statvars-schemaless', 1, statvar_dcid
      )
    return True

  def get_svobs_key(self, pvs: dict) -> str:
    """Returns the key for SVObs concatenating all PVs, except value.

    Args:
      pvs: dictionary of property:values for the statvar obs.

    Returns
      string fingerprint for the SVobs.
    """
    key_pvs = [
        f'{p}={pvs[p]}'
        for p in sorted(pvs.keys())
        if _is_valid_property(p, self._config.get('schemaless', False))
        and _is_valid_value(pvs[p])
        and p not in self._IGNORE_SVOBS_KEY_PVS
    ]
    return ';'.join(key_pvs)

  def aggregate_value(
      self,
      aggregation_type: str,
      current_pvs: str,
      new_pvs: dict,
      aggregate_property: str,
  ):
    """Aggregate values for the given aggregate_property from new_pvs into current_pvs.

    Args:
      aggregation_type: string which is one of the supported aggregation types:
        sum, min, max, list, first, last
      current_pvs: Existing property:values in the map.
      new_pvs: New pvs not in the map.
      aggregate_property: property whoese values are to be aggregated.

    Returns:
      True if aggregation was successful.
    """
    current_value = get_numeric_value(current_pvs.get(aggregate_property, 0))
    new_value = get_numeric_value(new_pvs.get(aggregate_property, 0))
    if current_value is None or new_value is None:
      logging.error(f'Invalid values to aggregate in {current_pvs}, {new_pvs}')
      self._counters.add_counter(f'error-aggregate-invalid-values', 1)
      return False
    aggregation_funcs = {
        'sum': lambda a, b: a + b,
        'min': lambda a, b: min(a, b),
        'max': lambda a, b: max(a, b),
        'list': lambda a, b: f'{a},{b}',
        'first': lambda a, b: a,
        'last': lambda a, b: b,
    }
    if aggregation_type:
      aggregation_type = aggregation_type.lower()
    if aggregation_type == 'mean':
      count_property = f'#Count-{aggregate_property}'
      current_count = current_pvs.get(count_property, 1)
      updated_value = (new_value + current_value * current_count) / (
          current_count + 1
      )
      current_pvs[aggregate_property] = updated_value
      current_pvs[count_property] = current_count + 1
      current_pvs['statType'] = 'dcs:meanValue'
    elif aggregation_type in aggregation_funcs:
      updated_value = aggregation_funcs[aggregation_type](
          current_value, new_value
      )
      current_pvs[aggregate_property] = updated_value
    else:
      logging.error(
          f'Unsupported aggregation {aggregation_type} for {current_pvs},'
          f' {new_pvs}'
      )
      self._counters.add_counter(
          f'error-aggregate-unsupported-{aggregation_type}', 1
      )
      return False
    merged_pvs_prop = self._config.get('merged_pvs_property', '#MergedSVObs')
    if merged_pvs_prop:
      if merged_pvs_prop not in current_pvs:
        current_pvs[merged_pvs_prop] = []
      current_pvs[merged_pvs_prop].append(new_pvs)
    # Set measurement method
    mmethod = current_pvs.get('measurementMethod', '')
    if not mmethod:
      current_pvs['measurementMethod'] = 'dcs:DataCommonsAggregate'
    elif not strip_namespace(mmethod).startswith('dcAggregate/'):
      current_pvs['measurementMethod'] = f'dcs:dcAggregate/{mmethod}'
    dup_svobs_key = self._config.get('duplicate_svobs_key')
    if dup_svobs_key in current_pvs:
      # Dups have been merged for this SVObs.
      # Remove #Error tag so it is not flagged as an error.
      current_pvs.pop(dup_svobs_key)
    self._counters.add_counter(f'aggregated-pvs-{aggregation_type}', 1)
    logging.level_debug() and logging.debug(
        f'Aggregation: {aggregation_type}:{aggregate_property}: '
        + f'value {current_value}, {new_value} into {updated_value} '
        + f'from {current_pvs} and {new_pvs}'
    )
    return True

  def set_statvar_dup_svobs(self, svobs_key: str, svobs: dict):
    """Add a duplicate SVObs for a statvar.

    Statvars with duplicate observations are likely missing constraint
    properties. The statvar and related observations will be dropped from the
    output.
    """
    # Check if SVObs aggregation is enabled.
    if svobs_key not in self._statvar_obs_map:
      log.error(f'Unexpected missing SVObs: {svobs_key}:{svobs}')
      self._counters.add_counter(
          'error-statvar-obs-missing-for-dup-svobs', 1, statvar_dcid
      )
      return
    existing_svobs = self._statvar_obs_map.get(svobs_key, None)
    if not existing_svobs:
      logging.error(f'Missing duplicate svobs for key {svobs_key}')
      return
    dup_svobs_key = self._config.get('duplicate_svobs_key')
    if dup_svobs_key not in existing_svobs:
      existing_svobs[dup_svobs_key] = []
    # Add the duplicate SVObs to the original SVObs.
    existing_svobs[dup_svobs_key].append(svobs)
    statvar_dcid = strip_namespace(svobs.get('variableMeasured', None))
    if not statvar_dcid:
      logging.error(f'Missing Statvar dcid for duplicate svobs {svobs}')
      self._counters.add_counter(
          'error-statvar-dcid-missing-for-dup-svobs', 1, statvar_dcid
      )
      return
    if statvar_dcid not in self._statvars_map:
      logging.error(
          f'Missing Statvar {statvar_dcid} for duplicate svobs {svobs}'
      )
      self._counters.add_counter(
          'error-statvar-missing-for-dup-svobs', 1, statvar_dcid
      )
      return
    # Add the duplicate SVObs to the statvar
    if self._config.get('drop_statvars_with_dup_svobs', True):
      statvar = self._statvars_map[statvar_dcid]
      if dup_svobs_key not in statvar:
        statvar[dup_svobs_key] = []
        self._counters.add_counter(
            'error-statvar-with-dup-svobs', 1, statvar_dcid
        )
      if not svobs_key:
        svobs_key = self.get_svobs_key(svobs)
      statvar[dup_svobs_key].append(svobs_key)
      logging.level_debug() and logging.debug(
          f'Added duplicate SVObs to statvar {statvar_dcid}:'
          f' {statvar[dup_svobs_key]}'
      )

  def add_statvar_obs(self, pvs: dict, has_output_column: bool = False):
    # Check if the required properties are present.
    missing_props = set(
        self._config.get('required_statvarobs_properties', [])
    ).difference(set(pvs.keys()))
    if missing_props and not has_output_column:
      logging.error(f'Missing SVObs properties {missing_props} in {pvs}')
      self._counters.add_counter(
          f'error-svobs-missing-property', 1, f'{missing_props}'
      )
      return False
    # Check if the SVObs already exists.
    allow_equal_pvs = True
    svobs_aggregation = self._config.get('aggregate_duplicate_svobs', None)
    svobs_aggregation = pvs.get(
        self._config.get('aggregate_key', '#Aggregate'), svobs_aggregation
    )
    if svobs_aggregation:
      # PVs with same value are not considered same, need to be aggregated.
      allow_equal_pvs = False
    svobs_key = self.get_svobs_key(pvs)
    if not self.add_dict_to_map(
        svobs_key,
        pvs,
        self._statvar_obs_map,
        self._config.get('duplicate_svobs_key'),
        allow_equal_pvs=allow_equal_pvs,
    ):
      existing_svobs = self._statvar_obs_map.get(svobs_key, None)
      if not existing_svobs:
        logging.error(f'Missing duplicate svobs for key {svobs_key}')
        return False
      if svobs_aggregation and self.aggregate_value(
          svobs_aggregation, existing_svobs, pvs, 'value'
      ):
        self._counters.add_counter(
            f'aggregated-svobs-{svobs_aggregation}',
            1,
            pvs.get('variableMeasured', ''),
        )
        return True

      logging.error(
          'Duplicate SVObs with mismatched values:'
          f' {self._statvar_obs_map[svobs_key]} != {pvs}'
      )
      self._counters.add_counter(
          f'error-mismatched-svobs', 1, pvs.get('variableMeasured', '')
      )
      self.set_statvar_dup_svobs(svobs_key, pvs)
      return False
    self._counters.add_counter(
        'svobs-added', 1, pvs.get('variableMeasured', '')
    )

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
    """Returns True if there are no error PVs."""
    dup_svobs_key = self._config.get('duplicate_svobs_key')
    dup_statvars_key = self._config.get('duplicate_statvars_key')
    for prop in pvs.keys():
      if prop in [dup_svobs_key, dup_statvars_key]:
        logging.error(f'Error duplicate property {prop} in {pvs}')
        return False
      if prop.startswith('#Error'):
        logging.error(f'Error property {prop} in {pvs}')
        return False
    return True

  def is_valid_statvar(self, pvs: dict) -> bool:
    """Returns True if the statvar is valid."""
    # Check if there are any duplicate StatVars or SVObs or errors.
    if not self.is_valid_pvs(pvs):
      logging.error(f'Invalid StatVar: {pvs}')
      return False
    # Check if the statvar has all mandatory properties.
    missing_props = set(
        self._config.get('required_statvar_properties', [])
    ).difference(set(pvs.keys()))
    if missing_props:
      logging.error(f'Missing properties {missing_props} for statvar {pvs}')
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
    error_props = [f'{p}:{v}' for p, v in pvs.items() if p.startswith('#Err')]
    if error_props:
      logging.error(f'Statvar {pvs} with error properties {error_props}')
      return False

    # TODO: Check if the statvar has any blocked properties
    return True

  def is_valid_svobs(self, pvs: dict) -> bool:
    """Returns True if the SVObs is valid and refers to an existing StatVar."""
    if not self.is_valid_pvs(pvs):
      logging.error(f'Invalid SVObs: {pvs}')
      return False
    # Check if the StatVar exists.
    statvar_dcid = strip_namespace(pvs.get('variableMeasured', ''))
    if not statvar_dcid and not _pvs_has_any_prop(
        pvs, self._config.get('output_columns')
    ):
      logging.error(f'Missing statvar_dcid for SVObs {pvs}')
      return False
    if statvar_dcid not in self._statvars_map:
      logging.debug(f'Missing {statvar_dcid} in StatVarMap for SVObs {pvs}')
    # Check if the statvarobs has any error properties.
    error_props = [f'{p}:{v}' for p, v in pvs.items() if p.startswith('#Err')]
    if error_props:
      logging.error(f'StatvarObs {pvs} with error properties {error_props}')
    return True

  def drop_statvars_without_svobs(self):
    """Drop any Statvars without any observations."""
    statvars_with_obs = set()
    for svobs_key, pvs in self._statvar_obs_map.items():
      statvar_dcid = strip_namespace(pvs.get('variableMeasured', None))
      if statvar_dcid:
        statvars_with_obs.add(statvar_dcid)
    drop_statvars = set(self._statvars_map.keys()).difference(statvars_with_obs)
    for statvar_dcid in drop_statvars:
      pvs = self._statvars_map.pop(statvar_dcid)
      logging.error(f'Dropping statvar {statvar_dcid} without SVObs {pvs}')
      self._counters.add_counter(
          'dropped-statvars-without-svobs', 1, statvar_dcid
      )
    return

  def drop_invalid_statvars(self):
    """Drop invalid statvars and corresponding SVObs.

    Statvars dropped include: - statvars with missing required properties -
    statvars with duplicate SVObs. - statvars with any dropped properties
    """
    # Collect valid statvars
    valid_statvars = {}
    for statvar, pvs in self._statvars_map.items():
      if self.is_valid_statvar(pvs):
        valid_statvars[statvar] = pvs
      else:
        self._counters.add_counter(f'dropped-invalid-statvars', 1, statvar)
    self._statvars_map = valid_statvars

    # Collect valid SVObs with valid statvars.
    valid_svobs = {}
    for svobs_key, pvs in self._statvar_obs_map.items():
      if self.is_valid_svobs(pvs):
        valid_svobs[svobs_key] = pvs
      else:
        self._counters.add_counter(f'dropped-invalid-svobs', 1, svobs_key)
    self._statvar_obs_map = valid_svobs

    # Drop any statvars without any observations.
    if self._config.get('drop_statvars_without_svobs', True):
      self.drop_statvars_without_svobs()

  def write_statvars_mcf(
      self,
      filename: str,
      mode: str = 'w',
      stat_var_nodes: dict = None,
      header: str = None,
  ):
    """Save the statvars into an MCF file."""
    if not stat_var_nodes:
      stat_var_nodes = self._statvars_map
    if self._config.get('output_only_new_statvars', False):
      num_statvars = len(stat_var_nodes)
      stat_var_nodes = drop_existing_mcf_nodes(
          stat_var_nodes,
          self._config.get(
              'statvar_diff_config',
              {
                  # Ignore properties that don't affect statvar dcid.
                  'ignore_property': [
                      'constraintProperties',
                      'memberOf',
                      'member',
                      'provenance',
                      'relevantVariable',
                  ],
                  # Retain SVs with new PVs like name
                  'output_nodes_with_additions': True,
              },
          ),
          self._counters,
      )
      removed_statvars = num_statvars - len(stat_var_nodes)
      self._counters.add_counter(
          'dropped-output-statvars-mcf', removed_statvars
      )
      logging.info(
          f'Removed {removed_statvars} existing nodes from'
          f' {num_statvars} statvars'
      )

    if not stat_var_nodes:
      # No new statvars to output.
      return

    commandline = ' '.join(sys.argv)
    if not header:
      header = (
          f'# Auto generated using command: "{commandline}" on'
          f' {datetime.datetime.now()}\n'
      )
    logging.info(f'Generating {len(stat_var_nodes)} statvars into {filename}')

    write_mcf_nodes(
        [stat_var_nodes],
        filename=filename,
        mode=mode,
        ignore_comments=not self._config.get('schemaless', False),
        sort=True,
        header=header,
    )
    self._counters.add_counter(
        'output-statvars-mcf',
        len(self._statvars_map),
        os.path.basename(filename),
    )

    # Generate new schema MCF
    if self._config.get('generate_schema_mcf', False):
      schema_mcf_file = self._config.get(
          'output_schema_mcf', filename.replace('.mcf', '_schema.mcf')
      )
      new_schema_nodes = generate_schema_nodes(
          stat_var_nodes,
          self._config.get('existing_schema_mcf'),
          schema_mcf_file,
          self._config.get_configs(),
      )
      if new_schema_nodes:
        logging.info(
            f'Generating new schema for {len(new_schema_nodes)} nodes into'
            f' {schema_mcf_file}'
        )
        write_mcf_nodes([new_schema_nodes], filename=schema_mcf_file, mode='w')
      self._counters.add_counter(
          'output-new-schema-mcf',
          len(new_schema_nodes),
          os.path.basename(schema_mcf_file),
      )

  def get_constant_svobs_pvs(self) -> dict:
    """Return PVs that have a fixed value across SVObs."""
    if len(self._statvar_obs_map) < 2:
      return {'typeOf': 'dcs:StatVarObservation'}
    pvs = {}
    for prop, value_list in self._statvar_obs_props.items():
      if len(value_list) == 1:
        pvs[prop] = value_list[0]
    return pvs

  def get_multi_value_svobs_pvs(self) -> dict:
    """Return SVObs properties that have multiple values."""
    svobs_pvs = set(self._statvar_obs_props)
    return list(svobs_pvs.difference(self.get_constant_svobs_pvs().keys()))

  def get_statvar_obs_columns(self) -> list:
    """Returns the list of columns for statvar Obs."""
    columns = self._config.get('output_columns', None)
    if not columns:
      if self._config.get('skip_constant_csv_columns', False):
        columns = self.get_multi_value_svobs_pvs()
      else:
        columns = list(self._statvar_obs_props)
      if not self._config.get('debug', False):
        # Remove debug columns.
        for col in columns:
          if not _is_valid_property(col, self._config.get('schemaless', False)):
            columns.remove(col)
        input_column = self._config.get('input_reference_column')
        if input_column in columns:
          columns.remove(input_column)
    # Return output columns in order configured.
    output_columns = []
    for col in self._config.get('default_svobs_pvs', {}).keys():
      if col in columns:
        output_columns.append(col)
    # Add any additional valid columns.
    debug_columns = []
    for col in columns:
      if col not in output_columns:
        if _is_valid_property(col, self._config.get('schemaless', False)):
          output_columns.append(col)
        else:
          debug_columns.append(col)
    output_columns.extend(debug_columns)
    return output_columns

  def format_svobs(self, svobs: dict) -> dict:
    """Returns dict for SVObs with formatted values."""
    formatted_svobs = {}
    for prop, value in svobs.items():
      formatted_value = value
      numeric_value = get_numeric_value(value)
      if numeric_value:
        formatted_value = _str_from_number(
            numeric_value,
            precision_digits=self._config.get('output_precision_digits', 5),
        )
      elif isinstance(value, str) and value:
        value = value.strip()
        if value and value[0] != '"':
          if ' ' in value or ',' in value:
            # Add quote for values with spaces.
            formatted_value = f'"{value}"'
      formatted_svobs[prop] = formatted_value
    return formatted_svobs

  def write_statvar_obs_csv(
      self,
      output_csv: str,
      mode: str = 'w',
      columns: list = None,
      output_tmcf_file: str = '',
  ):
    """Save the StatVar observations into a CSV file and tMCF."""
    if not columns:
      columns = self.get_statvar_obs_columns()

    logging.info(
        f'Writing {len(self._statvar_obs_map)} SVObs  into {output_csv} with'
        f' {columns}'
    )
    svobs_unique_values = {}
    with file_util.FileIO(output_csv, mode, newline='') as f_out_csv:
      csv_writer = csv.DictWriter(
          f_out_csv,
          fieldnames=columns,
          extrasaction='ignore',
          doublequote=False,
          escapechar='\\',
          lineterminator='\n',
      )
      if mode == 'w':
        csv_writer.writeheader()
      for key, svobs in self._statvar_obs_map.items():
        format_svobs = self.format_svobs(svobs)
        csv_writer.writerow(format_svobs)
        for p, v in svobs.items():
          if p in columns or _is_valid_property(
              p, self._config.get('schemaless', False)
          ):
            if p not in svobs_unique_values:
              svobs_unique_values[p] = set()
            svobs_unique_values[p].add(v)

    self._counters.add_counter(
        'output-svobs-csv-rows', len(self._statvar_obs_map), output_csv
    )
    for p, s in svobs_unique_values.items():
      self._counters.add_counter(f'output-svobs-unique-{p}', len(s))

    if output_tmcf_file:
      self.write_statvar_obs_tmcf(output_tmcf_file, columns=columns)

  def write_statvar_obs_tmcf(
      self,
      filename: str,
      mode: str = 'w',
      columns: list = None,
      constant_pvs: dict = None,
      dataset_name: str = None,
  ):
    """Generate the tMCF for the listed StatVar observation columns."""
    output_tmcf = self._config.get('output_tmcf', None)
    if not output_tmcf:
      if not dataset_name:
        if file_util.file_is_local(filename):
          dataset, ext = os.path.splitext(filename)
          dataset_name = os.path.basename(dataset)
        else:
          dataset_name = 'Data'
      if not columns:
        columns = self.get_multi_value_svobs_pvs()
      if not constant_pvs and self._config.get(
          'skip_constant_csv_columns', True
      ):
        constant_pvs = self.get_constant_svobs_pvs()

      logging.info(
          f'Writing SVObs tmcf {filename} with {columns} into {filename}.'
      )

      tmcf = [f'Node: E:{dataset_name}->E0']
      default_svobs_pvs = dict(self._config.get('default_svobs_pvs', {}))
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
          if prop in default_svobs_pvs:
            default_svobs_pvs.pop(prop)
      # Add any remaining default PVs
      for prop, value in default_svobs_pvs.items():
        if value:
          tmcf.append(f'{prop}: {value}')
      output_tmcf = '\n'.join(tmcf) + '\n'

    with file_util.FileIO(filename, mode, newline='') as f_out_tmcf:
      f_out_tmcf.write(output_tmcf)

  def _load_existing_statvars(self, mcf_file: list) -> dict:
    fp_nodes = {}
    if mcf_file:
      statvar_nodes = load_mcf_nodes(mcf_file)
      fp_nodes = fingerprint_mcf_nodes(
          statvar_nodes,
          self._config.get('statvar_fingerprint_ignore_props', []),
          self._config.get('statvar_fingerprint_include_props', []),
      )
      logging.info(f'Loaded {len(fp_nodes)} existing statvars from {mcf_file}')
    return fp_nodes

  def _get_exisisting_statvar(self, pvs: dict) -> dict:
    """Returns an existing statvar with the same PVs.

    Args:
      pvs: dictionary of statvar property:values

    Returns:
      updated dictionary of statvar pvs if one exists already.
    """
    existing_node = self._statvar_resolver.resolve_node(pvs)
    if existing_node:
      logging.level_debug() and logging.debug(
          f'Reusing existing statvar {fp}:{existing_node} for {pvs}'
      )
      for prop, value in existing_node.items():
        if prop not in pvs:
          pvs[prop] = value
      self._counters.add_counter(
          f'existing-statvars-from-mcf', 1, pvs.get('dcid')
      )
    else:
      logging.level_debug() and logging.debug(f'No existing statvar for :{pvs}')
    return pvs


class StatVarDataProcessor:
  """Class to process data and generate StatVars and StatVarObs."""

  def __init__(
      self,
      pv_mapper: PropertyValueMapper = None,
      config_dict: dict = None,
      counters_dict: dict = None,
  ):
    self.setup_config(config_dict)
    self._counters = Counters(
        counters_dict=counters_dict,
        options=CounterOptions(
            debug=self._config.get('debug', False),
            processed_counter='processed',
            total_counter='total',
        ),
    )
    if not pv_mapper:
      pv_map_files = self._config.get('pv_map', [])
      logging.level_debug() and logging.debug(
          f'Creating PropertyValueMapper with {pv_map_files}, config:'
          f' {config_dict}'
      )
      self._pv_mapper = PropertyValueMapper(
          pv_map_files,
          config_dict=config_dict,
          counters_dict=self._counters.get_counters(),
      )
    else:
      self._pv_mapper = pv_mapper
    self._statvars_map = StatVarsMap(
        config_dict=config_dict, counters_dict=self._counters.get_counters()
    )
    if self._config.get('pv_map_drop_undefined_nodes', False):
      self._statvars_map.remove_undefined_properties(
          self._pv_mapper.get_pv_map()
      )
    # Place resolver
    self._place_resolver = PlaceResolver(
        maps_api_key=self._config.get('maps_api_key', ''),
        config_dict=self._config.get_configs(),
        counters_dict=self._counters.get_counters(),
    )
    # Regex for references within values, such as, '@Variable' or '{Variable}'
    self._reference_pattern = re.compile(
        r'@([a-zA-Z0-9_]+)\b|{([a-zA-Z0-9_]+)}'
    )
    # Internal PVs created implicitly.
    self._internal_reference_keys = [
        self._config.get('data_key', 'Data'),
        self._config.get('numeric_data_key', 'Number'),
        self._config.get('pv_lookup_key', 'Key'),
    ]

  # Functions that can be overridden by child classes.
  def preprocess_row(self, row: list, row_index) -> list:
    """Modify the contents of the row and return new values.

    Can add additional columns or change values of a column. To ignore the row,
    return an empty list.
    """
    return row

  def preprocess_stat_var_obs_pvs(self, pvs: dict) -> dict:
    """Modify the PVs for a stat var and stat var observation.

    New PVs can be added or PVs can be removed. Return an empty dict to ignore
    the PVs.
    """
    return [pvs]

  def setup_config(self, config_dict: dict = {}):
    """Setup the config."""
    self._config = ConfigMap(config_dict=config_dict)
    # Convert mapped columns from letters to int
    mapped_columns = self._config.get('mapped_columns', 0)
    if mapped_columns:
      mapped_columns_indices = []
      if not isinstance(mapped_columns, list):
        if isinstance(mapped_columns, str):
          mapped_columns = mapped_columns.split(',')
        elif isinstance(mapped_columns, int):
          mapped_columns_indices.append(list(range(1, mapped_columns + 1)))
      for col in mapped_columns:
        if isinstance(col, str) and col:
          if col[0].isalpha():
            # Convert letters to int index.
            col_index = 0
            for c in col:
              col_index = col_index * 26 + (ord(c) - ord('A') + 1)
            mapped_columns_indices.append(col)
          elif col[0].isdigit():
            mapped_columns_indices.append(int(col))
      if len(mapped_columns_indices) == 1:
        mapped_columns_indices = list(range(1, mapped_columns_indices[0] + 1))
      self._config.set_config('mapped_columns', mapped_columns_indices)
      logging.debug(f'Setting mapped columns to: {mapped_columns_indices}')

    # Convert config values from strings to lists.
    for prop, default_value in config_flags._DEFAULT_CONFIG.items():
      if isinstance(default_value, list):
        # Default value is a list. Convert new value to list as well.
        value = self._config.get(prop, default_value)
        if value and isinstance(value, str):
          value_list = value.split(',')
          self._config.set_config(prop, value_list)
          logging.debug(f'Setting config to list: {prop}={value_list}')

    # Enable place resolution if place_csv is provided.
    if (
        self._config.get('dc_api_key', '')
        or self._config.get('maps_api_key', '')
        or self._config.get('places_csv', '')
        or self._config.get('places_resolved_csv', '')
    ):
      logging.info(f'Enabling place name resolution: resolve_places=True')
      self._config.set_config('resolve_places', True)
    logging.level_debug() and logging.debug(
        f'Updated configs: {self._config.get_configs()}'
    )

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

  def _set_input_context(
      self,
      filename: str = None,
      line_number: int = None,
      column_number: int = None,
  ):
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
    self._counters.add_counter(
        f'input-sections', 1, self.get_current_filename()
    )

  def get_current_filename(self) -> str:
    return self._current_filename

  def get_last_column_header(self, column_index: int) -> str:
    """Get the last string for the column header."""
    if column_index in self._column_keys:
      col_keys_dict = self._column_keys[column_index]
      last_key = next(reversed(col_keys_dict))
      return col_keys_dict[last_key]
    return None

  def generate_file_pvs(self, filename: str) -> dict:
    """Generate the PVs that apply to all data in the file."""
    word_delimiter = self._config.get('word_delimiter', ' ')
    word_joiner = word_delimiter.split('|')[0]
    normalize_filename = re.sub(r'[^A-Za-z0-9_\.-]', word_joiner, filename)
    logging.level_debug() and logging.debug(
        f'Getting PVs for filename {normalize_filename}'
    )
    pvs_list = self._pv_mapper.get_all_pvs_for_value(normalize_filename)
    return self.resolve_value_references(pvs_list)

  def set_file_header_pvs(self, pvs: dict):
    logging.level_debug() and logging.debug(f'Setting file header PVs to {pvs}')
    self._file_pvs = dict(pvs)

  def get_file_header_pvs(self):
    return self._file_pvs

  def set_column_header_pvs(
      self,
      row_index: int,
      column_index: int,
      column_key: str,
      column_pvs: dict,
      header_pvs: dict,
  ) -> dict:
    """Set the PVs for the column header."""
    if column_index not in self._column_keys:
      self._column_keys[column_index] = OrderedDict({0: column_key})
    self._column_keys[column_index][row_index] = column_key
    if column_index not in header_pvs:
      header_pvs[column_index] = {}
    header_pvs[column_index].update(column_pvs)
    logging.level_debug() and logging.debug(
        'Setting header for'
        f' column:{row_index}:{column_index}:{column_key}:{header_pvs[column_index]}'
    )

  def get_column_header_pvs(self, column_index: int) -> dict:
    """Return the dict for column headers if any."""
    return self._column_pvs.get(column_index, {})

  def get_column_header_key(self, column_index) -> str:
    """Return the last column header."""
    if column_index in self._column_keys:
      col_keys = self._column_keys[column_index]
      for row_index, column_key in col_keys.items():
        return column_key
    return None

  def get_last_column_header_key(self, column_index) -> str:
    """Return the last column header."""
    if column_index in self._column_keys:
      col_keys = self._column_keys[column_index]
      return list(col_keys.values())[-1]
    return None

  def get_section_header_pvs(self, column_index: int) -> dict:
    """Return the dict for column headers if any."""
    return self._section_column_pvs.get(column_index, {})

  def add_column_header_pvs(
      self, row_index: int, row_col_pvs: dict, columns: list
  ):
    """Add PVs per column as file column header or section column headers."""
    column_headers = self._column_pvs
    num_svobs = self._counters.get_counter(
        'output-svobs-' + self.get_current_filename()
    )
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
      # Get all PVs for the column from the pv-map.
      col_pvs = dict(row_col_pvs.get(col_index, {}))
      # Remove any empty @Data PVs.
      data_key = self._config.get('data_key', 'Data')
      if data_key in col_pvs and not col_pvs[data_key]:
        col_pvs.pop(data_key)
      column_value = columns[col_index]
      if not col_pvs and not column_value:
        # Empty column without any PVs could be a multi-column-span
        # header. Carry over previous column PVs if any.
        col_pvs = prev_col_pvs
      self.set_column_header_pvs(
          row_index, col_index, column_value, col_pvs, column_headers
      )
      prev_col_pvs = col_pvs
    logging.level_debug() and logging.debug(
        f'Setting column headers: {column_headers}'
    )

  def get_reference_names(self, value: str) -> str:
    """Return any named references, such as '@var' or '{@var}' in the value."""
    refs = []
    if not value or not isinstance(value, str):
      return refs
    for n1, n2 in self._reference_pattern.findall(value):
      if n1:
        refs.append(n1)
      if n2:
        refs.append(n2)
    return refs

  def resolve_value_references(
      self, pvs_list: list, process_pvs: bool = False
  ) -> dict:
    """Return a single dict merging a list of dicts and resolving any references."""
    # Merge all PVs resolving references from last to first.
    if not pvs_list:
      return {}
    pvs = dict()
    resolved_props = set()
    unresolved_refs = dict()
    for d in reversed(pvs_list):
      for prop, value_list in d.items():
        if not isinstance(value_list, list):
          value_list = [value_list]
        for value in value_list:
          # Check if the value has any references with @
          value_unresolved_refs = dict()
          refs = self.get_reference_names(value)
          # Replace each reference with its value.
          for ref in refs:
            replacement = None
            for ref_key in [f'@{ref}', ref]:
              if ref_key in pvs:
                replacement = str(pvs[ref_key])
              elif ref_key in d:
                replacement = str(d[ref_key])
            if replacement is not None:
              logging.level_debug() and logging.debug(
                  f'Replacing reference {ref} with {replacement} for'
                  f' {prop}:{value}'
              )
              value = (
                  value.replace('{' + ref + '}', replacement)
                  .replace('{@' + ref + '}', replacement)
                  .replace('@' + ref, replacement)
              )
            else:
              value_unresolved_refs[ref] = {prop: value}
          if value_unresolved_refs:
            unresolved_refs.update(value_unresolved_refs)
            logging.level_debug() and logging.debug(
                f'Unresolved refs {value_unresolved_refs} remain in'
                f' {prop}:{value} at {self._file_context}'
            )
            self._counters.add_counter(
                'warning-unresolved-value-ref',
                1,
                ','.join(value_unresolved_refs.keys()),
            )
          else:
            resolved_props.add(prop)

          _add_key_value(
              prop,
              value,
              pvs,
              self._config.get('multi_value_properties', {}),
              overwrite=False,
          )
          logging.level_debug() and logging.debug(
              f'Adding {value} for {prop}:{pvs[prop]}'
          )
    logging.level_debug() and logging.debug(
        f'Resolved references in {pvs_list} into {pvs} with unresolved:'
        f' {unresolved_refs}'
    )
    resolvable_refs = resolved_props.intersection(unresolved_refs.keys())
    if resolvable_refs:
      # Additional unresolved props can be resolved.
      logging.level_debug() and logging.debug(
          f'Re-resolving references {resolvable_refs} in {pvs} for unresolved'
          f' pvs: {unresolved_refs}'
      )
      resolve_pvs_list = []
      for ref in resolvable_refs:
        resolve_pvs_list.append(unresolved_refs[ref])
      resolve_pvs_list.append(pvs)
      pvs = self.resolve_value_references(resolve_pvs_list, process_pvs=False)
    if process_pvs:
      if self._pv_mapper.process_pvs_for_data(key=None, pvs=pvs):
        # PVs were processed. Resolve any references again.
        return self.resolve_value_references([pvs], process_pvs=False)
    return pvs

  def process_data_files(self, filenames: list, output_path: str):
    """Process a data file to generate statvars."""
    self._counters.set_prefix('1:process_input_')
    time_start = time.perf_counter()
    # Check if output already exists.
    if self._config.get('resume', False):
      outputs = self.get_output_files(output_path)
      missing_outputs = [file for file in outputs if not os.path.exists(file)]
      if not missing_outputs:
        logging.info(f'Skipping processing as {outputs} exist')
        return
    # Expand any wildcard in filenames
    encoding = self._config.get('input_encoding', 'utf-8')
    files = file_util.file_get_matching(filenames)
    for file in files:
      self._counters.add_counter(
          'total', file_util.file_estimate_num_rows(file)
      )
    # Process all input data files, one at a time.
    for filename in files:
      logging.info(
          f'Processing input data file {filename} with encoding:{encoding}...'
      )
      file_start_time = time.perf_counter()
      if filename.endswith('.json'):
        # Convert json to csv file.
        logging.info(f'Converting json file {filename} into csv')
        filename = file_json_to_csv(filename)
      fileio = file_util.FileIO(filename, newline='', encoding=encoding)
      with fileio as csvfile:
        self._counters.add_counter('input-files-processed', 1)
        num_file_rows = file_util.file_estimate_num_rows(
            fileio.get_local_filename()
        )
        self._counters.add_counter(f'num-rows-{filename}', num_file_rows)
        # Guess the input format.
        try:
          dialect = csv.Sniffer().sniff(csvfile.read(5024))
        except csv.Error:
          dialect = self._config.get('input_data_dialect', 'excel')
        max_rows_per_file = int(self._config.get('input_rows', sys.maxsize))
        max_cols_per_file = int(self._config.get('input_columns', sys.maxsize))
        self._counters.add_counter(
            f'total', min(max_rows_per_file, num_file_rows)
        )
        csvfile.seek(0)
        csv_reader_options = {}
        delimiter = self._config.get('input_delimiter', ',')
        if delimiter:
          csv_reader_options['delimiter'] = delimiter
        reader = csv.reader(csvfile, dialect=dialect, **csv_reader_options)
        line_number = 0
        self.init_file_state(filename)
        skip_rows = self._config.get('skip_rows', 0)
        process_rows = self._config.get('process_rows', [0])
        # Process each row in the input data file.
        for row in reader:
          line_number += 1
          if line_number <= skip_rows:
            logging.level_debug() and logging.debug(
                f'Skipping row {filename}:{line_number}:{row}'
            )
            continue
          if max_rows_per_file >= 0 and line_number > max_rows_per_file:
            logging.level_debug() and logging.debug(
                f'Stopping at input {filename}:{line_number}:{row}'
            )
            break
          if (
              process_rows
              and process_rows[0] != 0
              and line_number not in process_rows
          ):
            logging.level_debug() and logging.debug(
                f'Skipping unprocessed row {filename}:{line_number}:{row}'
            )
            continue

          row = row[:max_cols_per_file]
          self._set_input_context(filename=filename, line_number=line_number)
          self.process_row(row, line_number)
          self._counters.add_counter('processed', 1, filename)
      time_end = time.perf_counter()
      time_taken = time_end - time_start
      self._counters.set_counter(
          'processing-time-seconds', time_taken, filename
      )
      line_rate = line_number / (time_end - file_start_time)
      self._counters.print_counters()
      logging.info(
          f'Processed {line_number} lines from {filename} @'
          f' {line_rate:.2f} lines/sec.'
      )
      self._counters.set_counter(
          f'processing-input-rows-rate', line_rate, filename
      )
    # TODO: resolve svobs place in batch mode.
    time_end = time.perf_counter()
    rows_processed = self._counters.get_counter('input-rows-processed')
    time_taken = time_end - time_start
    input_rate = rows_processed / time_taken
    logging.info(
        f'Processed {rows_processed} rows from {len(files)} files @'
        f' {input_rate:.2f} rows/sec.'
    )
    self._counters.set_counter(f'processing-input-rows-rate', input_rate)

  def should_lookup_pv_for_row_column(
      self, row_index: int, column_index: int
  ) -> bool:
    """Returns True if PVs should be looked up for cell row_index:column_index

    Assumes row_index and column_index start from 1.
    """
    # Check if this is a header row. Lookups are made for header cells.
    if self.is_header_index(row_index, column_index):
      return True
    # Check if the row is a mapped row.
    lookup_pv_rows = self._config.get('mapped_rows', 0)
    if isinstance(lookup_pv_rows, int):
      if lookup_pv_rows > 0 and row_index <= lookup_pv_rows:
        return True
    elif isinstance(lookup_pv_rows, list):
      if row_index in lookup_pv_rows:
        return True
    # Check if the column is a mapped column
    lookup_pv_columns = self._config.get('mapped_columns', 0)
    if isinstance(lookup_pv_columns, int):
      if lookup_pv_columns > 0 and column_index <= lookup_pv_columns:
        return True
    elif column_index in lookup_pv_columns:
      return True

    # Check if the column header has a pv-map namespace.
    column_header = self.get_column_header_key(column_index - 1)
    if column_header and column_header in self._pv_mapper.get_pv_map():
      # Column header has a PV mapping file. Allow PV lookup.
      return True
    return not lookup_pv_rows and not lookup_pv_columns

  def is_header_index(self, row_index: int, column_index: int) -> bool:
    """Returns True if the row and columns is a header."""
    header_rows = self._config.get('header_rows', 0)
    header_columns = self._config.get('header_columns', 0)
    if header_rows > 0 and row_index <= header_rows:
      return True
    if header_columns > 0 and column_index <= header_columns:
      return True
    # return header_rows <= 0 and header_columns <= 0
    return False

  def is_possible_header_index(self, row_index: int, column_index: int) -> bool:
    """Returns True if the row and columns is a possible header."""
    if self.is_header_index(row_index, column_index):
      return True
    if (
        self._config.get('header_rows', 0) > 0
        or self._config.get('header_columns', 0) > 0
    ):
      return False
    # No header setting in config. Any row can be a header
    return True

  def process_row_header_pvs(
      self,
      row: list,
      row_index: int,
      row_col_pvs: dict,
      row_svobs: int,
      cols_with_pvs: int,
  ):
    """Returns True if any header properties are set for the row."""
    # If row has no SVObs but has PVs, it must be a header.
    if (
        not row_svobs
        and cols_with_pvs
        and self.is_possible_header_index(row_index, len(row) + 1)
    ):
      # Any column with PVs must be a header applicable to entire column.
      logging.level_debug() and logging.debug(
          f'Setting column header PVs for row:{row_index}:{row_col_pvs}'
      )
      self.add_column_header_pvs(row_index, row_col_pvs, row)
      self._counters.add_counter(
          f'input-header-rows', 1, self.get_current_filename()
      )
      return True

    # Look for any PVs with '#header' property for any column
    logging.debug(f'Looking for headers in row:{row_index}:{row_col_pvs}')
    col_headers = {}
    header_prop = self._config.get('header_property', '#header')
    for col_index, col_pvs in row_col_pvs.items():
      if col_pvs and header_prop in col_pvs:
        # Get column header properties if any specified or
        # use all PVs as headers
        col_header_props = col_pvs.get(header_prop, '').split(',')
        if not col_header_props:
          col_header_props = col_pvs.keys()
        col_header_pvs = {}
        for prop in col_header_props:
          # Use any property=value in the header tag or
          # get the value from the column PVs
          value = col_pvs.get(prop, '')
          if '=' in prop:
            prop, value = prop.split('=', 1)
          if value:
            col_header_pvs[prop] = value
        if col_header_pvs:
          col_headers[col_index] = col_header_pvs
    if col_headers:
      logging.level_debug() and logging.debug(
          f'Setting column header tagged PVs for row:{row_index}:{col_headers}'
      )
      self.add_column_header_pvs(row_index, col_headers, row)
      self._counters.add_counter(
          f'input-header-rows', 1, self.get_current_filename()
      )
      return True
    return False

  def process_row(self, row: list, row_index: int):
    """Process a row of data with multiple columns.

    The row cold be a file header or a section header with SVObs or the row
    could have SVObs in some columns.
    """
    logging.level_debug() and logging.debug(
        f'Processing row:{row_index}: {row}'
    )
    row = self.preprocess_row(row, row_index)
    if not row:
      logging.level_debug() and logging.debug(
          f'Preprocess dropping row {row_index}'
      )
      self._counters.add_counter(
          'input-rows-ignored-preprocess', 1, self.get_current_filename()
      )
      return
    if not row or len(row) < self._config.get('input_min_columns_per_row', 2):
      logging.level_debug() and logging.debug(
          f'Ignoring row with too few columns: {row}'
      )
      self._counters.add_counter(
          'input-rows-ignored-too-few-columns', 1, self.get_current_filename()
      )
      return
    self._counters.add_counter(
        'input-rows-processed', 1, self.get_current_filename()
    )
    # Collect all PVs for the columns in the row.
    row_col_pvs = OrderedDict()
    cols_with_pvs = 0
    for col_index in range(len(row)):
      col_value = row[col_index].strip().replace('\n', ' ')
      col_pvs = {}
      if self.should_lookup_pv_for_row_column(row_index, col_index + 1):
        self._set_input_context(column_number=col_index)
        logging.level_debug() and logging.debug(
            f'Getting PVs for column:{row_index}:{col_index}:{col_value}'
        )
        pvs_list = self._pv_mapper.get_all_pvs_for_value(
            col_value, self.get_last_column_header_key(col_index)
        )
        # if pvs_list:
        #    pvs_list.append(
        #        {self._config.get('data_key', '@Data'): col_value})
        # else:
        # if not pvs_list:
        #    pvs_list = [{self._config.get('data_key', '@Data'): col_value}]
        col_pvs = self.resolve_value_references(pvs_list, process_pvs=True)
      if col_pvs:
        # Column has mapped PVs.
        # It could be a header or be applied to other values in the row.
        row_col_pvs[col_index] = col_pvs
        cols_with_pvs += 1
        logging.level_debug() and logging.debug(
            f'Got pvs for column:{row_index}:{col_index}:{col_pvs}'
        )
      else:
        # Column has no PVs. Check if it has a value.
        col_numeric_val = get_numeric_value(
            col_value,
            self._config.get('number_decimal', '.'),
            self._config.get('number_separator', ', '),
        )
        if col_numeric_val is not None:
          if self._config.get('use_all_numeric_data_values', False):
            row_col_pvs[col_index] = {'value': col_numeric_val}
          else:
            row_col_pvs[col_index] = {
                self._config.get('numeric_data_key', 'Number'): col_numeric_val
            }
          logging.level_debug() and logging.debug(
              f'Got PVs for column:{row_index}:{col_index}:'
              f' value:{row[col_index]}, PVS: {row_col_pvs[col_index]}'
          )
        else:
          logging.level_debug() and logging.debug(
              f'Got no PVs for column:{row_index}:{col_index}:'
              f' value:{row[col_index]}'
          )

    logging.level_debug() and logging.debug(
        f'Processing row:{row_index}:{row}: into PVs: {row_col_pvs} in'
        f' {self._file_context}'
    )
    if not row_col_pvs:
      # No interesting data or PVs in the row. Ignore it.
      logging.level_debug() and logging.debug(
          f'Ignoring row without PVs: {row} in {self._file_context}'
      )
      self._counters.add_counter(
          'input-rows-ignored', 1, self.get_current_filename()
      )
      return

    # Process values in the row, applying row and column PVs.
    row_pvs = {}  # All PVs in the row from the leftmost column to right.
    column_pvs = {}  # PVs per column, indexed by the column number.
    for col_index in range(0, len(row)):
      col_value = row[col_index].strip().replace('\n', ' ')
      # Get column header PVs and resolved any references
      self._set_input_context(column_number=col_index)
      col_pvs_list = []
      # Collect PVs that apply to the cell from from column headers
      col_pvs_list.append(self.get_file_header_pvs())
      col_pvs_list.append(self.get_column_header_pvs(col_index))
      col_pvs_list.append(self.get_section_header_pvs(col_index))
      col_pvs_list.append(row_col_pvs.get(col_index, {}))
      col_pvs_list.append({self._config.get('data_key', 'Data'): col_value})
      merged_col_pvs = self.resolve_value_references(
          col_pvs_list, process_pvs=True
      )
      # Collect PVs that apply to the row
      merged_row_pvs = self.resolve_value_references(
          [row_pvs, row_col_pvs.get(col_index, {}), col_pvs_list[-1]],
          process_pvs=True,
      )
      # Collect resolved PVs for the cell from row and column headers.
      cell_pvs = self.resolve_value_references([merged_row_pvs, merged_col_pvs])
      logging.level_debug() and logging.debug(
          f'Merged PVs for column:{row_index}:{col_index}: {col_pvs_list} and'
          f' {row_pvs} into {cell_pvs}'
      )
      self._set_input_context(column_number=col_index)
      cell_pvs[self._config.get('input_reference_column')] = self._file_context
      column_pvs[col_index] = cell_pvs
      if ('value' not in cell_pvs) and ('measurementResult' not in cell_pvs):
        # Carry forward the non-SVObs PVs to the next column.
        # Collect resolved PVs or PVs with references for a cell
        # to be applied to the whole row.
        for prop, value in cell_pvs.items():
          if (
              value
              and prop not in self._internal_reference_keys
              and not self.get_reference_names(value)
          ):
            _add_key_value(
                prop,
                value,
                row_pvs,
                self._config.get('multi_value_properties', {}),
            )
        for prop, value in row_col_pvs.get(col_index, {}).items():
          if value and prop not in self._internal_reference_keys:
            _add_key_value(
                prop,
                value,
                row_pvs,
                self._config.get('multi_value_properties', {}),
            )
    # Process per-column PVs after merging with row-wide PVs.
    # If a cell has a statvar obs, save the svobs and the statvar.
    logging.level_debug() and logging.debug(
        f'Looking for SVObs in row:{row_index}: with row PVs: {row_pvs}, column'
        f' PVs: {column_pvs}'
    )
    row_svobs = 0
    resolved_col_pvs = dict()
    for col_index, col_pvs in column_pvs.items():
      self._set_input_context(column_number=col_index)
      merged_col_pvs = self.resolve_value_references(
          [row_pvs, col_pvs], process_pvs=True
      )
      merged_col_pvs[self._config.get('input_reference_column')] = (
          self._file_context
      )
      resolved_col_pvs[col_index] = merged_col_pvs
      if not self.is_header_index(
          row_index, col_index + 1
      ) and self.process_stat_var_obs_pvs(merged_col_pvs, row_index, col_index):
        row_svobs += 1
    self.process_row_header_pvs(
        row, row_index, row_col_pvs, row_svobs, cols_with_pvs
    )
    # If row has no SVObs but has PVs, it must be a header.
    if row_svobs:
      logging.level_debug() and logging.debug(
          f'Found {row_svobs} SVObs in row:{row_index}'
      )
      self._counters.add_counter(
          f'input-data-rows', 1, self.get_current_filename()
      )

  def process_stat_var_obs_value(self, pvs: dict) -> bool:
    """Process the value applying any multiplication factor if required."""
    if ('value' not in pvs) and ('measurementResult' not in pvs):
      return False
    measurement_result = pvs.get('measurementResult', '')
    if _is_valid_value(measurement_result):
      return True
    value = pvs.get('value', '')
    if not _is_valid_value(value):
      return False
    numeric_value = get_numeric_value(value)
    if numeric_value is not None:
      multiply_prop = self._config.get('multiply_factor', '#Multiply')
      if multiply_prop in pvs:
        multiply_factor = get_numeric_value(pvs[multiply_prop])
        pvs['value'] = numeric_value * multiply_factor
        pvs.pop(multiply_prop)
    return True

  def pvs_has_output_columns(self, pvs: dict) -> bool:
    """Returns True if the pvs have any of the output columns as keys."""
    output_columns = self._config.get('output_columns')
    if pvs and output_columns:
      # value is a mandatory column for SVObs
      if 'value' in output_columns:
        value = pvs.get('value')
        if not _is_valid_value(value):
          # Output columns are SVObs but no value present. Ignore it.
          return False
      for prop in pvs.keys():
        if prop in output_columns:
          return True
    return False

  def should_ignore_stat_var_obs_pvs(self, pvs: dict) -> bool:
    """Returns True if the pvs should be ignored."""
    # TODO(ajaits): add a config to filter pvs.
    if '#ignore' in pvs:
      return True
    return False

  def process_stat_var_obs_pvs(
      self, pvs: dict, row_index: int, col_index: int
  ) -> bool:
    """Process a set of SVObs PVs flattening list values."""
    logging.level_debug() and logging.debug(
        f'Processing SVObs PVs for:{row_index}:{col_index}: {pvs} for'
        f' {self._file_context}'
    )
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
    logging.level_debug() and logging.debug(
        f'Flattening list values for keys: {list_keys} in PVs:{pvs} for'
        f' {self._file_context}'
    )
    status = True
    list_values = [pvs[key] for key in list_keys]
    for items in itertools.product(*list_values):
      flattened_pvs = dict(singular_pvs)
      for index in range(len(list_keys)):
        flattened_pvs[list_keys[index]] = items[index]
      status &= self.process_stat_var_obs(flattened_pvs)
    return status

  def process_stat_var_obs(self, pvs: dict) -> bool:
    """Process PV for a statvar obs."""
    svobs_pvs_list = self.preprocess_stat_var_obs_pvs(pvs)
    if not svobs_pvs_list:
      logging.level_debug() and logging.debug(
          f'Preprocess dropping SVObs PVs for {self._file_context}'
      )
      return False
    logging.level_debug() and logging.debug(
        f'Got {len(svobs_pvs_list)} SVObs pvs after preprocess:'
        f' {svobs_pvs_list} for {self._file_context}'
    )
    status = True
    for svobs_pvs in svobs_pvs_list:
      status &= self.process_single_stat_var_obs(svobs_pvs)
    return status

  def process_single_stat_var_obs(self, pvs: dict) -> bool:
    has_output_column = False
    if not self.process_stat_var_obs_value(pvs):
      has_output_column = self.pvs_has_output_columns(pvs)
      if not has_output_column:
        # No values in this data cell. May be a header.
        logging.level_debug() and logging.debug(
            f'No SVObs value in dict {pvs} in {self._file_context}'
        )
        return False

    if self.should_ignore_stat_var_obs_pvs(pvs):
      # Ignore these PVs,
      logging.level_debug() and logging.debug(
          f'Ignoring SVObs PVs {pvs} in {self._file_context}'
      )
      self._counters.add_counter(f'ignored-svobs-pvs', 1)
      # Return True so the cell with value is not treated as a header
      return True

    if not self.resolve_svobs_date(pvs) and not has_output_column:
      logging.error(f'Unable to resolve SVObs date in {pvs}')
      self._counters.add_counter(f'dropped-svobs-unresolved-date', 1)
      return False
    logging.level_debug() and logging.debug(
        f'Creating SVObs for {pvs} in {self._file_context}'
    )
    # Separate out PVs for StatVar and StatvarObs
    statvar_pvs = {}
    svobs_pvs = {}
    output_columns = self._config.get('output_columns', [])
    for prop, value in pvs.items():
      if prop == self._config.get('aggregate_key', '#Aggregate'):
        svobs_pvs[prop] = value
      elif _is_valid_property(
          prop, self._config.get('schemaless', False)
      ) and _is_valid_value(value):
        if (
            prop in self._config.get('default_svobs_pvs')
            or prop in output_columns
        ):
          svobs_pvs[prop] = value
        else:
          statvar_pvs[prop] = value
    if not svobs_pvs:
      logging.error(f'No SVObs PVs in {pvs} in file:{self._file_context}')
      return False
    # Remove internal PVs
    for p in [
        self._config.get('data_key', 'Data'),
        self._config.get('numeric_data_key', 'Number'),
        self._config.get('pv_lookup_key', 'Key'),
    ]:
      if p in statvar_pvs:
        statvar_pvs.pop(p)

    statvar_dcid = ''
    if statvar_pvs:
      self.generate_dependant_stat_vars(statvar_pvs, svobs_pvs)
      variable_measured = strip_namespace(svobs_pvs.get('variableMeasured'))
      statvar_dcid = self.process_stat_var_pvs(statvar_pvs, variable_measured)
      if not statvar_dcid:
        if not variable_measured:
          # No statvar or variable measured in obs, drop it.
          logging.error(
              f'Dropping SVObs {svobs_pvs} for invalid statvar {statvar_pvs} in'
              f' {self._file_context}'
          )
          self._counters.add_counter(
              f'dropped-svobs-with-invalid-statvar', 1, statvar_dcid
          )
          return False
        statvar_dcid = variable_measured
      svobs_pvs['variableMeasured'] = add_namespace(statvar_dcid)
    svobs_pvs[self._config.get('input_reference_column')] = self._file_context

    # Create and add SVObs.
    self._statvars_map.add_default_pvs(
        self._config.get('default_svobs_pvs', {}), svobs_pvs
    )
    if not self.resolve_svobs_place(svobs_pvs) and not has_output_column:
      logging.error(f'Unable to resolve SVObs place in {pvs}')
      self._counters.add_counter(
          f'dropped-svobs-unresolved-place', 1, statvar_dcid
      )
      return False
    if not self._statvars_map.add_statvar_obs(svobs_pvs, has_output_column):
      logging.error(
          f'Dropping invalid SVObs {svobs_pvs} for statvar {statvar_pvs} in'
          f' {self._file_context}'
      )
      self._counters.add_counter(f'dropped-svobs-invalid', 1, statvar_dcid)
      return False
    self._counters.add_counter(f'generated-svobs', 1, statvar_dcid)
    self._counters.add_counter(
        'generated-svobs-' + self.get_current_filename(), 1
    )
    self._section_svobs += 1
    logging.level_debug() and logging.debug(
        f'Added SVObs {svobs_pvs} in {self._file_context}'
    )
    return True

  def generate_dependant_stat_vars(self, statvar_pvs: dict, svobs_pvs: dict):
    """Create stat vars dcids for properties referring to statvars,

    such as, variableMeasured or measurementDenominator.

    The value of this property is a comma separated list of property name=values
    to be used to generate the dcid.

    If the property name begins with '-' it is excluded and
    if it if begins with '+' it is included additionally to existing properties.
    """
    statvar_ref_props = self._config.get(
        'properties_with_statvars',
        ['measurementDenominator', 'variableMeasured'],
    )
    for statvar_prop in statvar_ref_props:
      for pvs in [statvar_pvs, svobs_pvs]:
        if pvs and statvar_prop in pvs:
          prop_value = pvs[statvar_prop]
          prop_value = prop_value.strip().strip('"').strip()
          if (
              (not prop_value)
              or (prop_value[0].isupper())
              or (_has_namespace(prop_value))
          ):
            # Property value is a reference to a DCID, skip it.
            continue
          # Property has a reference to other properties.
          # Get a set of selected properties to generate DCID.
          selected_props = set()
          additional_props = set()
          exclude_props = set(statvar_ref_props)
          for prop in prop_value.split(','):
            prop = prop.strip()
            if not prop:
              continue
            if prop[0] == '-':
              # Exclude the prop
              exclude_props.add(prop[1:])
            elif prop[0] == '+':
              additional_props.add(prop[1:])
            else:
              selected_props.add(prop)
          if not selected_props:
            selected_props.update(statvar_pvs.keys())
            if statvar_prop == 'measurementDenominator':
              # Drop ignore props from numerator
              selected_props.difference_update(
                  self._config.get('statvar_dcid_ignore_properties', {})
              )
          selected_props.update(additional_props)
          selected_props = selected_props.difference(exclude_props)
          # Create a new statvar for the selected PVs
          new_statvar_pvs = {}
          for sv_prop in selected_props:
            if sv_prop in statvar_pvs and sv_prop not in new_statvar_pvs:
              new_statvar_pvs[sv_prop] = statvar_pvs[sv_prop]
            elif '=' in sv_prop:
              prop, value = sv_prop.split('=', 1)
              new_statvar_pvs[prop] = value
          logging.level_debug() and logging.debug(
              f'Generating statvar for {statvar_prop}:{prop_value} with'
              f' {new_statvar_pvs} from {pvs}'
          )
          statvar_dcid = self.process_stat_var_pvs(new_statvar_pvs)
          if statvar_dcid:
            pvs[statvar_prop] = add_namespace(statvar_dcid)
          else:
            self._counters.add_counter(
                f'error_generating_statvar_dcid_{statvar_prop}', 1
            )
          if statvar_prop == 'variableMeasured':
            # Reset statvar pvs in the caller to the new PVs computed.
            statvar_pvs.update(new_statvar_pvs)
            for p in list(statvar_pvs.keys()):
              if p not in new_statvar_pvs:
                statvar_pvs.pop(p)

  def process_stat_var_pvs(
      self, statvar_pvs: dict, statvar_dcid: str = None
  ) -> str:
    """Returns the dcid of the StatVar if processed successfully."""
    if statvar_dcid and not statvar_pvs:
      return statvar_dcid
    # Set the dcid for the StatVar
    self._statvars_map.add_default_pvs(
        self._config.get('default_statvar_pvs'), statvar_pvs
    )
    if not statvar_dcid:
      statvar_dcid = strip_namespace(statvar_pvs.get('dcid', statvar_dcid))
    if not statvar_dcid:
      statvar_dcid = strip_namespace(
          self._statvars_map.generate_statvar_dcid(statvar_pvs)
      )
    if statvar_dcid:
      # Add StatVar to the global map.
      if not self._statvars_map.add_statvar(statvar_dcid, statvar_pvs):
        return None
    return statvar_dcid

  def resolve_svobs_place(self, pvs: dict) -> bool:
    """Resolve any references in the StatVarObs PVs, such as places."""
    place = pvs.get('observationAbout', None)
    if not place:
      logging.warning(f'No place in SVObs {pvs}')
      self._counters.add_counter(
          f'warning-svobs-missing-place', 1, pvs.get('variableMeasured', '')
      )
      return False
    if _is_place_dcid(place):
      # Place is a resolved dcid or a place property.
      return True

    logging.level_debug() and logging.debug(
        f'Resolving place: {place} in {pvs}'
    )
    # Lookup dcid for the place.
    place_dcid = place
    place_pvs = self.resolve_value_references(
        self._pv_mapper.get_all_pvs_for_value(place, 'observationAbout')
    )
    if place_pvs:
      place_dcid = place_pvs.get('observationAbout', '')
    if not _is_place_dcid(place_dcid):
      # Place is not resolved yet. Try resolving through Maps API.
      if self._config.get('resolve_places', False):
        resolved_place = self._place_resolver.resolve_name({
            place_dcid: {
                'place_name': place_dcid,
                'country': pvs.get(
                    '#country', self._config.get('maps_api_country', None)
                ),
                'administrative_area': pvs.get(
                    '#administrative_area',
                    self._config.get('maps_api_administrative_area', None),
                ),
            }
        })
        resolved_dcid = resolved_place.get(place_dcid, {}).get('dcid', None)
        logging.level_debug() and logging.debug(
            f'Got place dcid: {resolved_dcid} for place {place} from'
            f' {resolved_place}'
        )
        if resolved_dcid:
          place_dcid = add_namespace(resolved_dcid)
    if _is_place_dcid(place_dcid):
      pvs['observationAbout'] = place_dcid
      logging.level_debug() and logging.debug(
          f'Resolved place {place} to {place_dcid}'
      )
      self._counters.add_counter(f'resolved-places', 1)
      return True

    logging.warning(f'Unable to resolve place {place} in {pvs}')
    self._counters.add_counter(f'error-unresolved-place', 1, place_dcid)
    return False

  def resolve_svobs_date(self, pvs: dict) -> bool:
    """Resolve date in SVObs to YYYY-MM-DD format."""
    date = pvs.get('observationDate', None)
    if not date:
      # No date to resolve
      return True
    # Convert any non alpha numeric characters to space
    date_normalized = re.sub(r'[^A-Za-z0-9]+', '-', date).strip('-')
    date_tokens = date_normalized.split('-')
    output_date_format = '%Y'
    num_tokens = len(date_tokens)
    if num_tokens > 1:
      output_date_format += '-%m'
    if num_tokens > 2:
      output_date_format += '-%d'
    # Check if date is already formatted as expected
    try:
      resolved_date = datetime.datetime.strptime(
          date_normalized, output_date_format
      ).strftime(output_date_format)
      # Date already formatted as expected. Nothing more to do.
      return True
    except ValueError as e:
      # Date is not in expected format. Try formatting it.
      logging.debug(f'Formatting date {date} into {output_date_format}')
      resolved_date = ''

    # If input has a date format, parse date string by input format
    input_date_format = pvs.get(
        self._config.get('date_format_key', '#DateFormat'),
        self._config.get('date_format'),
    )
    if input_date_format:
      try:
        resolved_date = datetime.datetime.strptime(
            date_normalized, input_date_format
        ).strftime(output_date_format)
        logging.debug(
            f'Formatted date {date} as {input_date_format} into {resolved_date}'
        )
      except ValueError as e:
        logging.debug(
            f'Unable to parse date {date_normalized} as {input_date_format}'
        )
        resolved_date = ''
    if not resolved_date:
      # Try formatting date into output format
      resolved_date = eval_functions.format_date(
          date_normalized, output_date_format
      )
    if resolved_date:
      pvs['observationDate'] = resolved_date
      return True
    return False

  def write_outputs(self, output_path: str):
    """Generate output mcf, csv and tmcf."""
    logging.info(f'Generating output: {output_path}')
    self._counters.set_prefix('2:prepare_output_')
    self._statvars_map.drop_invalid_statvars()
    if self._config.get('generate_statvar_mcf', True):
      self._counters.set_prefix('3:write_statvar_mcf_')
      statvar_mcf_file = self._config.get(
          'output_mcf', output_path + '_stat_vars.mcf'
      )
      self._statvars_map.write_statvars_mcf(filename=statvar_mcf_file, mode='w')
    if self._config.get('generate_csv', True):
      self._counters.set_prefix('4:write_svobs_csv_')
      output_csv = self._config.get('output_csv_file', output_path + '.csv')
      output_tmcf_file = ''
      if self._config.get('generate_tmcf', True):
        output_tmcf_file = self._config.get(
            'output_tmcf_file', output_path + '.tmcf'
        )
      self._statvars_map.write_statvar_obs_csv(
          output_csv,
          mode=self._config.get('output_csv_mode', 'w'),
          columns=self._config.get('output_columns', []),
          output_tmcf_file=output_tmcf_file,
      )
    self._counters.print_counters()
    counters_filename = self._config.get(
        'output_counters_file', output_path + '_counters.txt'
    )
    logging.info(f'Writing counters to {counters_filename}')
    file_util.file_write_csv_dict(
        OrderedDict(sorted(self._counters.get_counters().items())),
        counters_filename,
    )

  def get_output_files(self, output_path: str) -> list:
    """Returns the list of output file names."""
    outputs = []
    if not output_path:
      return
    if self._config.get('generate_statvar_mcf', True):
      outputs.append(output_path + '.mcf')
    if self._config.get('generate_csv', True):
      outputs.append(output_path + '.csv')
    if self._config.get('generate_tmcf', True):
      outputs.append(output_path + '.tmcf')
    return outputs


def _is_place_dcid(place: str) -> bool:
  """Returns True if the input string is a dcid without extra characters."""
  if place and isinstance(place, str):
    # Check if all characters are alpha or digits.
    if place.startswith('dcid:') or place.startswith('dcs:'):
      return True
    for c in place:
      if not c.isalnum():
        if c != '/' and c != ':' and c != '_':
          return False
    return '/' in place
  return False


def _str_from_number(
    number: Union[int, float], precision_digits: int = None
) -> str:
  """Returns the number converted to string.

  Ints and floats with 0 decimal parts get int strings. Floats get precision
  digits.
  """
  # Check if number is an integer or float without any decimals.
  if int(number) == number:
    number_int = int(number)
    return f'{number_int}'
  # Return float rounded to precision digits.
  if precision_digits:
    number = round(number, precision_digits)
  return f'{number}'


def _pvs_has_any_prop(pvs: dict, columns: list = None) -> bool:
  if pvs and columns:
    for prop, value in pvs.items():
      if value and prop in columns:
        return True
  return False


def download_csv_from_url(urls: list, data_path: str) -> list:
  """Download data from the URL into the given file.

  Returns a list of files downloaded.
  """
  data_files = []
  if not isinstance(urls, list):
    urls = [urls]
  for url in urls:
    output_file = download_file_from_url(url=url, overwrite=False)
    if output_file:
      data_files.append(output_file)
  logging.info(f'Downloaded {urls} into {data_files}.')
  return data_files


def shard_csv_data(
    files: list,
    column: str = None,
    prefix_len: int = sys.maxsize,
    keep_existing_files: bool = True,
) -> list:
  """Shard CSV file by unique values in column.

  Returns the list of output files.
  """
  logging.info(
      f'Loading data files: {files} for sharding by column: {column}...'
  )
  dfs = []
  for file in files:
    dfs.append(pd.read_csv(file_util.FileIO(file), dtype=str, na_filter=False))
  df = pd.concat(dfs)
  if not column:
    # Pick the first column.
    column = list(df.columns)[0]
  # Convert nan to empty string so sharding doesn't drop any rows.
  # df[column] = df[column].fillna('')
  # Get unique shard prefix values from column.
  shards = list(sorted(set([str(x)[:prefix_len] for x in df[column].unique()])))
  if file_util.file_is_local(file):
    (file_prefix, file_ext) = os.path.splitext(file)
  else:
    fd, file_prefix = tempfile.mkstemp()
    file_ext = '.csv'
  column_suffix = re.sub(r'[^A-Za-z0-9_-]', '-', column)
  output_path = f'{file_prefix}-{column_suffix}'
  logging.info(
      f'Sharding {files} into {len(shards)} shards by column'
      f' {column}:{shards} into {output_path}-*.csv.'
  )
  output_files = []
  num_shards = len(shards)
  for shard_index in range(num_shards):
    shard_value = shards[shard_index]
    output_file = f'{output_path}-{shard_index:05d}-of-{num_shards:05d}.csv'
    logging.info(f'Sharding by {column}:{shard_value} into {output_file}...')
    if not os.path.exists(output_file) or not keep_existing_files:
      if shard_value:
        df[df[column].str.startswith(shard_value)].to_csv(
            output_file, index=False
        )
      else:
        df[df[column] == ''].to_csv(output_file, index=False)
    output_files.append(output_file)
  return output_files


def convert_xls_to_csv(filenames: list, sheets: list) -> list:
  """Returns a list of csv files extracted from the sheets within the xls."""
  csv_files = []
  for file in filenames:
    filename, ext = os.path.splitext(file)
    logging.info(f'Converting {filename}{ext} into csv for {sheets}')
    if '.xls' in ext:
      # Convert the xls file into csv file per sheet.
      xls = pd.ExcelFile(file)
      for sheet in xls.sheet_names:
        # Read each sheet as a Pandas DataFrame and save it as csv
        if not sheets or sheet in sheets:
          df = pd.read_excel(xls, sheet_name=sheet, dtype=str)
          csv_filename = re.sub(
              '[^A-Za-z0-9_.-]+', '_', f'{filename}_{sheet}.csv'
          )
          df.to_csv(csv_filename, index=False)
          logging.info(f'Converted {file}:{sheet} into csv {csv_filename}')
          csv_files.append(csv_filename)
    else:
      csv_files.append(file)
  return csv_files


def prepare_input_data(config: dict) -> bool:
  """Prepare the input data, download and shard if needed."""
  input_data = config.get('input_data', '')
  input_files = file_util.file_get_matching(input_data)
  if not input_files:
    # Download input data from the URL.
    data_url = config.get('data_url', '')
    if not data_url:
      logging.fatal(f'Provide data with --data_url or --input_data.')
      return False
    input_files = download_csv_from_url(
        data_url, os.path.dirname(input_data[0])
    )
  input_files = convert_xls_to_csv(input_files, config.get('input_xls', []))
  shard_column = config.get('shard_input_by_column', '')
  if config.get('parallelism', 0) > 0 and shard_column:
    return shard_csv_data(
        input_files,
        shard_column,
        config.get('shard_prefix_length', sys.maxsize),
        True,
    )
  return input_files


def parallel_process(
    data_processor_class: StatVarDataProcessor,
    input_data: list,
    output_path: str,
    config: dict,
    pv_map_files: list,
    counters: dict = None,
    parallelism: int = 0,
) -> bool:
  """Process files in parallel, calling process() for each input file."""
  if not parallelism:
    parallelism = os.cpu_count()
  logging.info(
      f'Processing {input_data} with {parallelism} parallel processes.'
  )
  # Invoke process() for each input file in parallel.
  input_files = file_util.file_get_matching(input_data)
  num_inputs = len(input_files)
  with multiprocessing.get_context('spawn').Pool(parallelism) as pool:
    for input_index in range(num_inputs):
      input_file = input_files[input_index]
      if not output_path:
        fd, output_path = tempfile.mkstemp()
      output_file_path = f'{output_path}-{input_index:05d}-of-{num_inputs:05d}'
      logging.info(f'Processing {input_file} into {output_file_path}...')
      process_args = {
          'data_processor_class': data_processor_class,
          'input_data': [input_file],
          'output_path': output_file_path,
          'config': config,
          'pv_map_files': pv_map_files,
          'counters': counters,
          'parallelism': 0,
      }
      task = pool.apply_async(process, kwds=process_args)
      task.get()
    pool.close()
    pool.join()

  # Merge statvar mcf files into a single mcf output.
  mcf_files = f'{output_path}-*-of-*.mcf'
  statvar_nodes = load_mcf_nodes(mcf_files)
  output_mcf_file = f'{output_path}.mcf'
  commandline = ' '.join(sys.argv)
  header = (
      f'# Auto generated using command: "{commandline}" on'
      f' {datetime.datetime.now()}\n'
  )
  write_mcf_nodes(
      node_dicts=[statvar_nodes],
      filename=output_mcf_file,
      mode='w',
      sort=True,
      header=header,
  )
  logging.info(
      f'Merged {len(statvar_nodes)} stat var MCF nodes from {mcf_files} into'
      f' {output_mcf_file}.'
  )

  # Create a common TMCF from output, removing the shard suffix.
  with file_util.FileIO(
      f'{output_path}-00000-of-{num_inputs:05d}.tmcf', mode='r'
  ) as tmcf:
    tmcf_node = tmcf.read()
    tmcf_node = re.sub(r'-[0-9]*-of-[0-9]*', '', tmcf_node)
    with file_util.FileIO(f'{output_path}.tmcf', mode='w') as output_tmcf:
      output_tmcf.write(tmcf_node)
  logging.info(f'Generated TMCF {output_path}.tmcf')
  return True


def process(
    data_processor_class: StatVarDataProcessor,
    input_data: list,
    output_path: str,
    config: str,
    pv_map_files: list,
    counters: dict = None,
    parallelism: int = 0,
) -> bool:
  """Process all input_data files to extract StatVars and StatvarObs.

  Emit the StatVars and StataVarObs into output mcf and csv files.
  """
  config = config_flags.get_config_from_flags(config)
  config_dict = config.get_configs()
  if input_data:
    config_dict['input_data'] = input_data
  if _FLAGS.debug or config_dict.get('debug', False):
    logging.set_verbosity(2)
  logging.info(
      f'Processing data {input_data} into {output_path} using config:'
      f' {config_dict}...'
  )
  input_data = prepare_input_data(config_dict)
  input_files = file_util.file_get_matching(input_data)
  num_inputs = len(input_files)
  if file_util.file_is_local(output_path):
    output_dir = os.path.dirname(output_path)
    if output_dir:
      logging.info(f'Creating output directory: {output_dir}')
      os.makedirs(output_dir, exist_ok=True)
  parallelism = config_dict.get('parallelism', parallelism)
  if parallelism <= 1 or len(input_files) <= 1:
    logging.info(f'Processing data {input_files} into {output_path}...')
    if pv_map_files:
      config_dict['pv_map'] = pv_map_files
    if counters is None:
      counters = {}
    if not data_processor_class:
      data_processor_class = StatVarDataProcessor

    data_processor = data_processor_class(
        config_dict=config_dict, counters_dict=counters
    )
    data_processor.process_data_files(input_files, output_path)
    data_processor.write_outputs(output_path)
    # Check if there were any errors.
    error_counters = [
        f'{c}={v}' for c, v in counters.items() if c.startswith('err')
    ]
    if error_counters:
      logging.info(f'Error Counters: {error_counters}')
      return False
  else:
    return parallel_process(
        data_processor_class=data_processor_class,
        input_data=input_files,
        output_path=output_path,
        config=config.get_configs(),
        pv_map_files=pv_map_files,
        counters=counters,
        parallelism=parallelism,
    )
  return True


def main(_):
  # uncomment to run pprof
  # start_pprof_server(port=8123)

  # Launch a web server with a form for commandline args
  # if the command line flag --http_port is set.
  process_http_server.run_http_server(
      http_port=_FLAGS.http_port, script=__file__, module=config_flags
  )
  process(
      StatVarDataProcessor,
      input_data=_FLAGS.input_data,
      output_path=_FLAGS.output_path,
      config=_FLAGS.config,
      pv_map_files=_FLAGS.pv_map,
      parallelism=_FLAGS.parallelism,
  )


if __name__ == '__main__':
  app.run(main)
