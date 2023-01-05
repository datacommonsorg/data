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
'''Class to store configuration parameters as a dictionary.'''

import ast
import collections.abc
import os
import sys

from absl import app
from absl import flags
from absl import logging
from collections import OrderedDict
from typing import Union

_FLAGS = flags.FLAGS

flags.DEFINE_string('config', '', 'File with configuration parameters.')
flags.DEFINE_list('data_url', '', 'URLs to download the data from.')
flags.DEFINE_string('shard_input_by_column', '',
                    'Shard input data by unique values in column.')
flags.DEFINE_integer('shard_prefix_length', sys.maxsize,
                    'Shard input data by value prefix of given length.')
flags.DEFINE_list(
    'pv_map', [],
    'Comma separated list of namespace:file with property values.')
flags.DEFINE_list('input_data', [],
                  'Comma separated list of data files to be processed.')
flags.DEFINE_integer('input_rows', sys.maxsize,
                     'Number of rows per input file to process.')
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
flags.DEFINE_string('existing_statvar_mcf', '',
                    'StatVar MCF files for any existing nodes to be resused.')
flags.DEFINE_integer('parallelism', 0, 'Number of parallel processes to use.')
flags.DEFINE_integer('pprof_port', 0, 'HTTP port for pprof server.')
flags.DEFINE_bool('debug', False, 'Enable debug messages.')
flags.DEFINE_integer('log_level', logging.INFO,
                     'Log level messages to be shown.')
flags.DEFINE_bool(
    'resume', False,
    'Resume processing to create output files not yet generated.')
_FLAGS(sys.argv)  # Allow invocation without app.run()

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

    # Settings to compare StatVars with existing statvars to reuse dcids.
    'existing_statvar_mcf':
        '',
    'statvar_fingerprint_ignore_props': ['dcid', 'name', 'description'],
    'statvar_fingerprint_include_props': [],

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


def _deep_update(src: dict, upd: dict) -> dict:
    '''Deep update of parameters in upd into src.
    Args:
      src: source dictionary into which new parameters are added.
      upd: dictionary with new parameters to be added.
    Returns:
      src dictionary with updated parameters.

    Note:
    Assumes the new dictionary has same type(dict/list) for updated parameters.
    '''
    for k, v in upd.items():
        if isinstance(v, collections.abc.Mapping):
            src[k] = _deep_update(src.get(k, {}), v)
        elif isinstance(v, list):
            src[k].extend(v)
        else:
            src[k] = v
    return src


def get_py_dict_from_file(filename: str) -> dict:
    '''Load a python dict from a file.
    Args:
      filename: JSON or a python file containing parameter to value mappings.
    Returns:
      dictionary loaded from the file.
    '''
    if not filename or not os.path.exists(filename):
        return {}
    logging.info(f'Loading python dict from {filename}...')
    with open(filename) as file:
        pv_map_str = file.read()

    # Load the map assuming a python dictionary.
    # Can also be used with JSON with trailing commas and comments.
    param_dict = ast.literal_eval(pv_map_str)
    logging.debug(f'Loaded {filename} into dict {param_dict}')
    return param_dict


class Config:
    '''Class to store config mapping of named parameters to values as a dictoinary.'''

    def __init__(self, config_dict: dict = None, filename: str = None):
        self._config_dict = dict(_DEFAULT_CONFIG)
        self.add_configs(self.get_config_from_flags())
        if config_dict:
            self.add_configs(config_dict)
        if filename:
            self.load_config_file(filename)
        logging.set_verbosity(self.get_config('log_level'))
        logging.debug(f'Using config: {self.get_configs()}')

    def get_config_from_flags(self) -> dict:
        '''Returns a dictionary of config options from command line flags.'''
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
            'existing_statvar_mcf':
                _FLAGS.existing_statvar_mcf,
            'schemaless':
                _FLAGS.schemaless,
            'parallelism':
                _FLAGS.parallelism,
            'resume':
                _FLAGS.resume,
            'debug':
                _FLAGS.debug,
            'log_level':
                max(_FLAGS.log_level, logging.DEBUG if _FLAGS.debug else 0),
        }

    def load_config_file(self, filename: str) -> dict:
        '''Load configs from a file overwriting any existing parameter with a new value.
        Args:
            filename: a py or json file with a dictionary of parameter:value mappings.
        Returns:
          The config dictionary.
          '''
        self.add_configs(get_py_dict_from_file(filename))
        return self._config_dict

    def add_configs(self, configs: dict) -> dict:
        '''Add new or replace existing config parameters
        Args:
            configs: dictionary with new parameter:value mappings
        Returns:
            dictionary with all parameter:value mappings.
        '''
        if configs:
            self._config_dict.update(configs)
        return self._config_dict

    def update_config(self, configs: dict) -> dict:
        '''Does a deep update of the dict updating nested dicts as well.
        Args:
            configs: dictionary with additional parameter:value mappings.
        Returns:
            dictionary with all parameter:value mappings.
        '''
        return _deep_update(self._config_dict, configs)

    def get_config(self,
                   parameter: str,
                   default_value=None) -> Union[str, int, float, list, dict]:
        '''Return the value of a named config parameter.
        Args:
            parameter: name of the parameter to lookup
            default_value: Default value to be returned if the parameter doesn't exist.
        Returns:
            value of the parameter in the config dict if it exists or the default_value.
        '''
        return self._config_dict.get(parameter, default_value)

    def get_configs(self) -> dict:
        '''Return the config dictionary with all the parameter and values.'''
        return self._config_dict

    def set_config(self, parameter: str, value):
        '''Set the value for a parameter overwriting one if it already exists
        Args:
          parameter: Name of the parameter
          value: Value to be set.
        '''
        self._config_dict[parameter] = value


def get_config_from_file(filename: str) -> Config:
    '''Returns a Config object with parameters loaded from a file.
    Args:
      filename: name of the file to load.
    Returns:
      Config object with all the parameters loaded into the config_dict.
    '''
    return Config(filename=filename)
