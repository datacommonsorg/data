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

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

from config_map import ConfigMap

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
flags.DEFINE_list(
    'input_xls', [],
    'Comma separated list of sheets within xls files to be processed.')
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
    'aggregate_duplicate_svobs', None,
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

# Flags for place name resolution
flags.DEFINE_string('maps_api_key', '',
                    'Maps API key for place lookup by name.')
flags.DEFINE_list('places_csv', [],
                  'CSV file with place names and dcids to match.')
flags.DEFINE_string('places_resolved_csv', '',
                    'CSV file with resolved place names and dcids to match.')
flags.DEFINE_list('place_type', [],
                  'List of places types for name reoslution.')
flags.DEFINE_list('places_within', [],
                  'List of places types for name reoslution.')

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
    'input_data':
        _FLAGS.input_data,
    'input_xls':
        _FLAGS.input_xls,
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
        _FLAGS.aggregate_duplicate_svobs,
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
            'measurementResult': '',
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
        _FLAGS.existing_statvar_mcf,
    'statvar_fingerprint_ignore_props': ['dcid', 'name', 'description', 'provenance', 'memberOf'],
    'statvar_fingerprint_include_props': [],

    # Use numeric data in any column as a value.
    # It may still be dropped if no SVObs can be constructed out of it.
    # If False, SVObs is only emitted for PVs that have a map for 'value',
    # for example, 'MyColumn': { 'value': '@Data' }
    'use_all_numeric_data_values':
        False,
    # Number format in input.
    'number_decimal': '.', # decimal character
    'number_seperator': ', ', # seperators stripped.

    # Word separator, used to split words into phrases for PV map lookups.
    'word_delimiter':
        ' ',
    # List of default PVS maps to lookup column values if there is no map for a
    # column name.
    'default_pv_maps': ['GLOBAL'],
    # Row and column indices with content to be looked up in pv_maps.
    'mapped_rows': 0,
    'mapped_columns': 0,
    'show_counters_every_n':
        0,
    'show_counters_every_sec':
        30,
    # Settings for place name resolution
    'maps_api_key': _FLAGS.maps_api_key,
    'resolve_places':
        False,
    'places_csv': _FLAGS.places_csv,
    'places_resolved_csv': _FLAGS.places_resolved_csv,
    'place_type': _FLAGS.place_type,
    'places_within': _FLAGS.places_within,

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
        True,  # Skip emitting columns with constant values in the csv
    'output_only_new_statvars':
        True,  # Drop existing statvars from output

    # Settings for DC API.
    'dc_api_root':
        'http://autopush.api.datacommons.org',
    'dc_api_use_cache':
        False,
    'dc_api_batch_size':
        100,

    # Settings from flags
    'pv_map':
        _FLAGS.pv_map,
    'input_rows':
        _FLAGS.input_rows,
    'skip_rows':
        _FLAGS.skip_rows,
    'header_rows':
        _FLAGS.header_rows,
    'header_columns':
        _FLAGS.header_columns,
    'parallelism':
        _FLAGS.parallelism,
    'debug':
        _FLAGS.debug,
    'log_level':
        _FLAGS.log_level,
}


def get_config_from_flags(filename: str = None) -> ConfigMap:
    '''Returns a Config object with parameters loaded from a file.
    Args:
      filename: name of the file to load.
    Returns:
      Config object with all the parameters loaded into the config_dict.
    '''
    if _FLAGS.debug:
        logging.set_verbosity(2)
    if _FLAGS.log_level:
        logging.set_verbosity(_FLAGS.log_level)
    config_dict = dict(_DEFAULT_CONFIG)
    if isinstance(filename, dict):
      config_dict.update(filename)
      filename = None
    return ConfigMap(config_dict=config_dict, filename=filename)
