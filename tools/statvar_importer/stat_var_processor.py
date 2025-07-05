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

from tools.statvar_importer.stat_vars_map import StatVarsMap

# uncomment to run pprof
# os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
# from pypprof.net_http import start_pprof_server

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))
sys.path.append(os.path.join(_SCRIPT_DIR, 'place'))
sys.path.append(os.path.join(_SCRIPT_DIR, 'schema'))

import eval_functions
from utils import (is_place_dcid, get_observation_date_format,
                   get_observation_period_for_date, prepare_input_data)
import file_util
import config_flags
import data_annotator
# import llm_statvar_name_generator

import property_value_utils as pv_utils

from mcf_file_util import get_numeric_value, get_value_list, add_pv_to_node
from mcf_file_util import load_mcf_nodes, write_mcf_nodes, add_namespace, strip_namespace
from mcf_diff import fingerprint_node
from place_resolver import PlaceResolver
from property_value_mapper import PropertyValueMapper
from json_to_csv import file_json_to_csv

# imports from ../../util
from config_map import ConfigMap, read_py_dict_from_file
from counters import Counters, CounterOptions
from download_util import download_file_from_url

_FLAGS = flags.FLAGS


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
                f' {config_dict}')
            self._pv_mapper = PropertyValueMapper(
                pv_map_files,
                config_dict=config_dict,
                counters_dict=self._counters.get_counters(),
            )
            pvmap = self._pv_mapper.get_pv_map()
            if not pvmap or not pvmap.get('GLOBAL'):
                self.generate_pvmap()

        else:
            self._pv_mapper = pv_mapper
        self._statvars_map = StatVarsMap(
            config_dict=config_dict,
            counters_dict=self._counters.get_counters())
        if self._config.get('pv_map_drop_undefined_nodes', False):
            self._statvars_map.remove_undefined_properties(
                self._pv_mapper.get_pv_map())
        # Place resolver
        self._place_resolver = PlaceResolver(
            maps_api_key=self._config.get('maps_api_key', ''),
            config_dict=self._config.get_configs(),
            counters_dict=self._counters.get_counters(),
        )
        # Regex for references within values, such as, '@Variable' or '{Variable}'
        self._reference_pattern = re.compile(
            r'@([a-zA-Z0-9_]{3,}+)\b|{([a-zA-Z0-9_]+)}')
        # Internal PVs created implicitly.
        self._internal_reference_keys = [
            self._config.get('data_key', 'Data'),
            self._config.get('numeric_data_key', 'Number'),
            self._config.get('pv_lookup_key', 'Key'),
        ]

    def generate_pvmap(self):
        """Generate a PV Map from the input data."""
        # Get input data with column headers to be mapped.
        input_data = self._config.get('input_data', '')
        input_files = file_util.file_get_matching(input_data)
        if not input_files:
            logging.info(f'Skipping pvmap generation without input data')
            return
        pv_map_files = file_util.file_get_matching(
            self._config.get('pv_map', ''))
        # Get path for the generated pvmap.
        pv_map_file = ''
        if pv_map_files:
            pv_map_file = pv_map_files[0]
        else:
            output_path = self._config.get('output_path', '')
            if output_path:
                pv_map_file = file_util.file_get_name(output_path,
                                                      suffix='-pvmap',
                                                      file_ext='.csv')
        if not pv_map_file:
            logging.info(f'Skipping pvmap generation without pvmap file')
            return
        logging.info(f'Generating PV map from {input_data} into {pv_map_file}')
        pvmap = data_annotator.generate_pvmap(input_data, pv_map_file,
                                              self._config, self._counters)
        self._pv_mapper.load_pvs_dict(pvmap)

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
                    mapped_columns_indices.append(
                        list(range(1, mapped_columns + 1)))
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
                mapped_columns_indices = list(
                    range(1, mapped_columns_indices[0] + 1))
            self._config.set_config('mapped_columns', mapped_columns_indices)
            logging.debug(
                f'Setting mapped columns to: {mapped_columns_indices}')

        # Convert config values from strings to lists.
        for prop, default_value in config_flags.get_default_config().items():
            if isinstance(default_value, list):
                # Default value is a list. Convert new value to list as well.
                value = self._config.get(prop, default_value)
                if value and isinstance(value, str):
                    value_list = value.split(',')
                    self._config.set_config(prop, value_list)
                    logging.log(2,
                                f'Setting config to list: {prop}={value_list}')

        # Enable place resolution if place_csv is provided.
        if (self._config.get('dc_api_key', '') or
                self._config.get('maps_api_key', '') or
                self._config.get('places_csv', '') or
                self._config.get('places_resolved_csv', '')):
            logging.info(f'Enabling place name resolution: resolve_places=True')
            self._config.set_config('resolve_places', True)
        logging.level_debug() and logging.debug(
            f'Updated configs: {self._config.get_configs()}')

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
        self._counters.add_counter(f'input-sections', 1,
                                   self.get_current_filename())

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
        logging.level_debug() and logging.log(
            2, f'Getting PVs for filename {normalize_filename}')
        pvs_list = self._pv_mapper.get_all_pvs_for_value(normalize_filename)
        default_pv_string = self._config.get('default_pvs_key', 'DEFAULT_PV')
        default_pvs = self._pv_mapper.get_all_pvs_for_value(normalize_filename)
        logging.level_debug() and logging.log(
            2, f'Got default PVs for {default_pv_string}: {default_pvs}')
        if default_pvs:
            pvs_list.extend(default_pvs)
        return self.resolve_value_references(pvs_list)

    def set_file_header_pvs(self, pvs: dict):
        logging.level_debug() and logging.debug(
            f'Setting file header PVs to {pvs}')
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

    def should_copy_header_pvs(self, pvs: dict) -> bool:
        """Returns true if the PVs can be copied to next merged column."""
        merged_cell = pvs.get('#MergedCell', None)
        if merged_cell is not None:
            return config_flags.get_value_type(merged_cell, True)
        return self._config.get('merged_cells')

    def add_column_header_pvs(self, row_index: int, row_col_pvs: dict,
                              columns: list):
        """Add PVs per column as file column header or section column headers."""
        column_headers = self._column_pvs
        num_svobs = self._counters.get_counter('output-svobs-' +
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
            # Get all PVs for the column from the pv-map.
            col_pvs = dict(row_col_pvs.get(col_index, {}))
            # Remove any empty @Data PVs.
            data_key = self._config.get('data_key', 'Data')
            if data_key in col_pvs and not col_pvs[data_key]:
                col_pvs.pop(data_key)
            column_value = columns[col_index]
            if not col_pvs and not column_value:
                # Empty column without any PVs could be a multi-column-span
                # header. Carry over previous column PVs if merged cells
                if self.should_copy_header_pvs(prev_col_pvs):
                    col_pvs = prev_col_pvs
            self.set_column_header_pvs(row_index, col_index, column_value,
                                       col_pvs, column_headers)
            prev_col_pvs = col_pvs
        logging.level_debug() and logging.debug(
            f'Setting column headers: {column_headers}')

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

    def resolve_value_references(self,
                                 pvs_list: list,
                                 process_pvs: bool = False) -> dict:
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
                            logging.level_debug() and logging.log(
                                2,
                                f'Replacing reference {ref} with {replacement} for'
                                f' {prop}:{value}')
                            value = (value.replace('{' + ref + '}',
                                                   replacement).replace(
                                                       '{@' + ref + '}',
                                                       replacement).replace(
                                                           '@' + ref,
                                                           replacement))
                        else:
                            value_unresolved_refs[ref] = {prop: value}
                    if value_unresolved_refs:
                        unresolved_refs.update(value_unresolved_refs)
                        logging.level_debug() and logging.log(
                            2,
                            f'Unresolved refs {value_unresolved_refs} remain in'
                            f' {prop}:{value} at {self._file_context}')
                        self._counters.add_counter(
                            'warning-unresolved-value-ref',
                            1,
                            ','.join(value_unresolved_refs.keys()),
                        )
                    else:
                        resolved_props.add(prop)

                    pv_utils.add_key_value(
                        prop,
                        value,
                        pvs,
                        self._config.get('multi_value_properties', {}),
                        overwrite=False,
                    )
                    logging.level_debug() and logging.log(
                        2, f'Adding {value} for {prop}:{pvs.get(prop)}')
        logging.level_debug() and logging.log(
            2, f'Resolved references in {pvs_list} into {pvs} with unresolved:'
            f' {unresolved_refs}')
        resolvable_refs = resolved_props.intersection(unresolved_refs.keys())
        if resolvable_refs:
            # Additional unresolved props can be resolved.
            logging.level_debug() and logging.log(
                2,
                f'Re-resolving references {resolvable_refs} in {pvs} for unresolved'
                f' pvs: {unresolved_refs}')
            resolve_pvs_list = []
            for ref in resolvable_refs:
                resolve_pvs_list.append(unresolved_refs[ref])
            resolve_pvs_list.append(pvs)
            pvs = self.resolve_value_references(resolve_pvs_list,
                                                process_pvs=False)
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
            missing_outputs = [
                file for file in outputs if not os.path.exists(file)
            ]
            if not missing_outputs:
                logging.info(f'Skipping processing as {outputs} exist')
                return
        # Expand any wildcard in filenames
        encoding = self._config.get('input_encoding', 'utf-8')
        files = file_util.file_get_matching(filenames)
        for file in files:
            self._counters.add_counter('total',
                                       file_util.file_estimate_num_rows(file))
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
                    fileio.get_local_filename())
                self._counters.add_counter(f'num-rows-{filename}',
                                           num_file_rows)
                max_rows_per_file = int(
                    self._config.get('input_rows', sys.maxsize))
                max_cols_per_file = int(
                    self._config.get('input_columns', sys.maxsize))
                self._counters.add_counter(
                    f'total', min(max_rows_per_file, num_file_rows))
                csvfile.seek(0)
                csv_reader_options = {}
                dialect = self._config.get('input_data_dialect')
                if dialect:
                    csv_reader_options['dialect'] = dialect
                delimiter = self._config.get('input_delimiter', ',')
                if delimiter:
                    csv_reader_options['delimiter'] = delimiter
                reader = csv.reader(csvfile,
                                    dialect=dialect,
                                    **csv_reader_options)
                line_number = 0
                self.init_file_state(filename)
                skip_rows = self._config.get('skip_rows', 0)
                # Process each row in the input data file.
                for row in reader:
                    self._counters.add_counter('processed', 1, filename)
                    line_number += 1
                    if line_number <= skip_rows:
                        logging.level_debug() and logging.log(
                            2, f'Skipping row {filename}:{line_number}:{row}')
                        self._counters.add_counter('input-rows-skipped', 1,
                                                   self.get_current_filename())
                        continue
                    if max_rows_per_file >= 0 and line_number > max_rows_per_file:
                        logging.level_debug() and logging.log(
                            2,
                            f'Stopping at input {filename}:{line_number}:{row}')
                        break
                    if not self.should_process_row(row, line_number):
                        logging.level_debug() and logging.log(
                            2,
                            f'Skipping unprocessed row {filename}:{line_number}:{row}'
                        )
                        self._counters.add_counter('input-rows-ignored', 1,
                                                   self.get_current_filename())
                        continue

                    row = row[:max_cols_per_file]
                    self._set_input_context(filename=filename,
                                            line_number=line_number)
                    self.process_row(row, line_number)
            time_end = time.perf_counter()
            time_taken = time_end - time_start
            self._counters.set_counter('processing-time-seconds', time_taken,
                                       filename)
            line_rate = line_number / (time_end - file_start_time)
            self._counters.print_counters()
            logging.info(f'Processed {line_number} lines from {filename} @'
                         f' {line_rate:.2f} lines/sec.')
            self._counters.set_counter(f'processing-input-rows-rate', line_rate,
                                       filename)

        # Filter outlisers
        self._statvars_map.filter_svobs()

        # TODO: resolve svobs place in batch mode.
        time_end = time.perf_counter()
        rows_processed = self._counters.get_counter('input-rows-processed')
        time_taken = time_end - time_start
        input_rate = rows_processed / time_taken
        logging.info(
            f'Processed {rows_processed} rows from {len(files)} files @'
            f' {input_rate:.2f} rows/sec.')
        self._counters.set_counter(f'processing-input-rows-rate', input_rate)

    def should_lookup_pv_for_row_column(self, row_index: int,
                                        column_index: int) -> bool:
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

    def is_possible_header_index(self, row_index: int,
                                 column_index: int) -> bool:
        """Returns True if the row and columns is a possible header."""
        if self.is_header_index(row_index, column_index):
            return True
        if (self._config.get('header_rows', 0) > 0 or
                self._config.get('header_columns', 0) > 0):
            return False
        # No header setting in config. Any row can be a header
        return True

    def should_process_row(self, row: list, line_number: int) -> bool:
        """Returns True if this row with line number should be processed."""
        process_rows = self._config.get('process_rows', [0])
        if (process_rows and process_rows[0] != 0 and
                line_number not in process_rows):
            # Line not in rows listed to be processed. Ignore it.
            return False
        ignore_rows = self._config.get('ignore_rows', [0])
        if ignore_rows and ignore_rows[0] != 0 and line_number in ignore_rows:
            # Line explicitly listed to be ignored.
            return False
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
        if (not row_svobs and cols_with_pvs and
                self.is_possible_header_index(row_index,
                                              len(row) + 1)):
            # Any column with PVs must be a header applicable to entire column.
            logging.level_debug() and logging.debug(
                f'Setting column header PVs for row:{row_index}:{row_col_pvs}')
            self.add_column_header_pvs(row_index, row_col_pvs, row)
            self._counters.add_counter(f'input-header-rows', 1,
                                       self.get_current_filename())
            return True

        # Look for any PVs with '#Header' property for any column
        logging.log(2, f'Looking for headers in row:{row_index}:{row_col_pvs}')
        col_headers = {}
        header_prop = self._config.get('header_property', '#Header')
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
            logging.level_debug() and logging.log(
                2,
                f'Setting column header tagged PVs for row:{row_index}:{col_headers}'
            )
            self.add_column_header_pvs(row_index, col_headers, row)
            self._counters.add_counter(f'input-header-rows', 1,
                                       self.get_current_filename())
            return True
        return False

    def process_row(self, row: list, row_index: int):
        """Process a row of data with multiple columns.

    The row cold be a file header or a section header with SVObs or the row
    could have SVObs in some columns.
    """
        logging.level_debug() and logging.debug(
            f'Processing row:{row_index}: {row}')
        row = self.preprocess_row(row, row_index)
        if not row:
            logging.level_debug() and logging.debug(
                f'Preprocess dropping row {row_index}')
            self._counters.add_counter('input-rows-ignored-preprocess', 1,
                                       self.get_current_filename())
            return
        if not row or len(row) < self._config.get('input_min_columns_per_row',
                                                  2):
            logging.level_debug() and logging.debug(
                f'Ignoring row with too few columns: {row}')
            self._counters.add_counter('input-rows-ignored-too-few-columns', 1,
                                       self.get_current_filename())
            return
        # Collect all PVs for the columns in the row.
        row_col_pvs = OrderedDict()
        cols_with_pvs = 0
        for col_index in range(len(row)):
            col_value = row[col_index].strip().replace('\n', ' ')
            col_pvs = {}
            if self.should_lookup_pv_for_row_column(row_index, col_index + 1):
                self._set_input_context(column_number=col_index)
                logging.level_debug() and logging.log(
                    2,
                    f'Getting PVs for column:{row_index}:{col_index}:{col_value}'
                )
                pvs_list = self._pv_mapper.get_all_pvs_for_value(
                    col_value, self.get_last_column_header_key(col_index))
                # if pvs_list:
                #    pvs_list.append(
                #        {self._config.get('data_key', '@Data'): col_value})
                # else:
                # if not pvs_list:
                #    pvs_list = [{self._config.get('data_key', '@Data'): col_value}]
                col_pvs = self.resolve_value_references(pvs_list,
                                                        process_pvs=True)
            if col_pvs:
                # Column has mapped PVs.
                # It could be a header or be applied to other values in the row.
                row_col_pvs[col_index] = col_pvs
                cols_with_pvs += 1
                logging.level_debug() and logging.debug(
                    f'Got pvs for column:{row_index}:{col_index}:{col_pvs}')
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
                            self._config.get('numeric_data_key', 'Number'):
                                col_numeric_val
                        }
                    logging.level_debug() and logging.log(
                        2, f'Got PVs for column:{row_index}:{col_index}:'
                        f' value:{row[col_index]}, PVS: {row_col_pvs[col_index]}'
                    )
                else:
                    logging.level_debug() and logging.log(
                        2, f'Got no PVs for column:{row_index}:{col_index}:'
                        f' value:{row[col_index]}')

        logging.level_debug() and logging.debug(
            f'Processing row:{row_index}:{row}: into PVs: {row_col_pvs} in'
            f' {self._file_context}')
        if not row_col_pvs:
            # No interesting data or PVs in the row. Ignore it.
            logging.level_debug() and logging.log(
                2, f'Ignoring row without PVs: {row} in {self._file_context}')
            self._counters.add_counter('input-rows-ignored', 1,
                                       self.get_current_filename())
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
            col_pvs_list.append(
                {self._config.get('data_key', 'Data'): col_value})
            merged_col_pvs = self.resolve_value_references(col_pvs_list,
                                                           process_pvs=True)
            # Collect PVs that apply to the row
            merged_row_pvs = self.resolve_value_references(
                [row_pvs,
                 row_col_pvs.get(col_index, {}), col_pvs_list[-1]],
                process_pvs=True,
            )
            # Collect resolved PVs for the cell from row and column headers.
            cell_pvs = self.resolve_value_references(
                [merged_row_pvs, merged_col_pvs])
            logging.level_debug() and logging.log(
                2,
                f'Merged PVs for column:{row_index}:{col_index}: {col_pvs_list} and'
                f' {row_pvs} into {cell_pvs}')
            self._set_input_context(column_number=col_index)
            cell_pvs[self._config.get(
                'input_reference_column')] = self._file_context
            column_pvs[col_index] = cell_pvs
            if ('value' not in cell_pvs) and ('measurementResult'
                                              not in cell_pvs):
                # Carry forward the non-SVObs PVs to the next column.
                # Collect resolved PVs or PVs with references for a cell
                # to be applied to the whole row.
                for prop, value in cell_pvs.items():
                    if (value is not None and
                            prop not in self._internal_reference_keys and
                            not self.get_reference_names(value)):
                        pv_utils.add_key_value(
                            prop,
                            value,
                            row_pvs,
                            self._config.get('multi_value_properties', {}),
                        )
                for prop, value in row_col_pvs.get(col_index, {}).items():
                    if value is not None and prop not in self._internal_reference_keys:
                        pv_utils.add_key_value(
                            prop,
                            value,
                            row_pvs,
                            self._config.get('multi_value_properties', {}),
                        )
        if config_flags.get_value_type(row_pvs.get('#IgnoreRow'), False):
            logging.level_debug() and logging.log(
                2, f'Ignoring row: {row} in {self._file_context}')
            self._counters.add_counter('input-rows-ignored', 1,
                                       self.get_current_filename())
            return
        # Process per-column PVs after merging with row-wide PVs.
        # If a cell has a statvar obs, save the svobs and the statvar.
        logging.level_debug() and logging.debug(
            f'Looking for SVObs in row:{row_index}: with row PVs: {row_pvs}, column'
            f' PVs: {column_pvs}')
        row_svobs = 0
        resolved_col_pvs = dict()
        for col_index, col_pvs in column_pvs.items():
            self._set_input_context(column_number=col_index)
            merged_col_pvs = self.resolve_value_references([row_pvs, col_pvs],
                                                           process_pvs=True)
            merged_col_pvs[self._config.get('input_reference_column')] = (
                self._file_context)
            resolved_col_pvs[col_index] = merged_col_pvs
            if not self.is_header_index(
                    row_index, col_index + 1) and self.process_stat_var_obs_pvs(
                        merged_col_pvs, row_index, col_index):
                row_svobs += 1
        self.process_row_header_pvs(row, row_index, row_col_pvs, row_svobs,
                                    cols_with_pvs)
        # If row has no SVObs but has PVs, it must be a header.
        if row_svobs:
            logging.level_debug() and logging.debug(
                f'Found {row_svobs} SVObs in row:{row_index}')
            self._counters.add_counter(f'input-data-rows', 1,
                                       self.get_current_filename())
        self._counters.add_counter('input-rows-processed', 1,
                                   self.get_current_filename())

    def process_stat_var_obs_value(self, pvs: dict) -> bool:
        """Process the value applying any multiplication factor if required."""
        if ('value' not in pvs) and ('measurementResult' not in pvs):
            return False
        measurement_result = pvs.get('measurementResult', '')
        if pv_utils.is_valid_value(measurement_result):
            return True
        value = pvs.get('value', '')
        if not pv_utils.is_valid_value(value):
            return False
        numeric_value = get_numeric_value(value)
        if numeric_value is not None:
            multiply_prop = self._config.get('multiply_factor', '#Multiply')
            if multiply_prop in pvs:
                multiply_factor = get_numeric_value(pvs[multiply_prop])
                if multiply_factor is not None:
                    pvs['value'] = numeric_value * multiply_factor
                else:
                    logging.error(
                        f'Invalid multiply factor: {pvs[multiply_prop]}')
                    self._counters.add_counter('error-invalid-multiply-factor',
                                               1)
                pvs.pop(multiply_prop)
        return True

    def pvs_has_output_columns(self, pvs: dict) -> bool:
        """Returns True if the pvs have any of the output columns as keys."""
        output_columns = self._config.get('output_columns')
        if pvs and output_columns:
            # value is a mandatory column for SVObs
            if 'value' in output_columns:
                value = pvs.get('value')
                if not pv_utils.is_valid_value(value):
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

    def should_allow_stat_var_obs_pvs(self, pvs: dict) -> bool:
        """Returns False if the pvs should be dropped by filter.
    Evaluates any #Filter clause and if it returns False, drops the pvs.
    There can be more than one filter per set of pvs, each with a suffix.
    """
        filter_key = self._config.get('filter_key', '#Filter')
        for prop in list(pvs.keys()):
            value = pvs.get(prop)
            if prop.startswith(filter_key):
                filter_prop, filter_result = eval_functions.evaluate_statement(
                    value,
                    pvs,
                    self._config.get('eval_globals',
                                     eval_functions.EVAL_GLOBALS),
                )
                logging.level_debug() and logging.log(
                    2,
                    f'Evaluated filter {filter_prop}={filter_result} for {prop}:{value} with {pvs}'
                )
                if filter_result is not None:
                    # Filter eval returned a valid result. Check if it passed the filter.
                    if filter_prop:
                        pvs[filter_prop] = filter_result
                    self._counters.add_counter(
                        f'filter-result-{prop}-{filter_result}-{filter_prop}',
                        1)
                    if not filter_result:
                        return False
        return True

    def process_stat_var_obs_pvs(self, pvs: dict, row_index: int,
                                 col_index: int) -> bool:
        """Process a set of SVObs PVs flattening list values."""
        logging.level_debug() and logging.debug(
            f'Processing SVObs PVs for:{row_index}:{col_index}: {pvs} for'
            f' {self._file_context}')

        # Add SVObs PVS for observationAbout
        self._statvars_map.add_default_pvs(
            self._config.get('default_svobs_pvs', {}), pvs)

        # Get properties with list of values
        singular_pvs = {}
        list_keys = []
        statvar_singular_props = self._config.get(
            'properties_with_statvars',
            ['measurementDenominator', 'variableMeasured'])
        statvar_singular_props.extend(
            self._config.get(
                'statvar_dcid_ignore_properties',
                [
                    'typeOf', 'description', 'name', 'nameWithLanguage',
                    'descriptionUrl', 'alternateName'
                ],
            ))
        for prop, value in pvs.items():
            if prop in statvar_singular_props:
                singular_pvs[prop] = value
                continue
            value = pv_utils.get_value_as_list(value)
            if isinstance(value, list):
                pvs[prop] = value
                list_keys.append(prop)
            else:
                singular_pvs[prop] = value

        if not list_keys:
            return self.process_stat_var_obs(pvs)

        # Flatten all list PVs.
        logging.level_debug() and logging.debug(
            f'Flattening list values for keys: {list_keys} in PVs:{pvs} for'
            f' {self._file_context}')
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
        self.resolve_svobs_place(pvs)
        svobs_pvs_list = self.preprocess_stat_var_obs_pvs(pvs)
        if not svobs_pvs_list:
            logging.level_debug() and logging.debug(
                f'Preprocess dropping SVObs PVs for {self._file_context}')
            return False
        logging.level_debug() and logging.debug(
            f'Got {len(svobs_pvs_list)} SVObs pvs after preprocess:'
            f' {svobs_pvs_list} for {self._file_context}')
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
                    f'No SVObs value in dict {pvs} in {self._file_context}')
                return False

        if self.should_ignore_stat_var_obs_pvs(pvs):
            # Ignore these PVs,
            logging.level_debug() and logging.debug(
                f'Ignoring SVObs PVs {pvs} in {self._file_context}')
            self._counters.add_counter(f'ignored-svobs-pvs', 1)
            # Return True so the cell with value is not treated as a header
            return True

        if not self.resolve_svobs_date(pvs) and not has_output_column:
            logging.error(f'Unable to resolve SVObs date in {pvs}')
            self._counters.add_counter(f'dropped-svobs-unresolved-date', 1)
            return False

        if not self.should_allow_stat_var_obs_pvs(pvs):
            # PVs did not pass filters. Drop this.
            logging.level_debug() and logging.debug(
                f'Filtering out SVObs PVs {pvs} in {self._file_context}')
            self._counters.add_counter(f'filter-dropped-svobs-pvs', 1)
            # Return True so the cell with value is not treated as a header
            return True

        logging.level_debug() and logging.debug(
            f'Creating SVObs for {pvs} in {self._file_context}')
        # Separate out PVs for StatVar and StatvarObs
        statvar_pvs = {}
        svobs_pvs = {}
        output_columns = self._config.get('output_columns', [])
        for prop, value in pvs.items():
            if prop == self._config.get('aggregate_key', '#Aggregate'):
                svobs_pvs[prop] = value
            elif pv_utils.is_valid_property(
                    prop,
                    self._config.get('schemaless',
                                     False)) and pv_utils.is_valid_value(value):
                if (prop in self._config.get('default_svobs_pvs') or
                        prop in output_columns):
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
            variable_measured = strip_namespace(
                svobs_pvs.get('variableMeasured'))
            statvar_dcid = self.process_stat_var_pvs(statvar_pvs,
                                                     variable_measured)
            if not statvar_dcid:
                if not variable_measured:
                    # No statvar or variable measured in obs, drop it.
                    logging.error(
                        f'Dropping SVObs {svobs_pvs} for invalid statvar {statvar_pvs} in'
                        f' {self._file_context}')
                    self._counters.add_counter(
                        f'dropped-svobs-with-invalid-statvar', 1, statvar_dcid)
                    return False
                statvar_dcid = variable_measured
            svobs_pvs['variableMeasured'] = add_namespace(statvar_dcid)
        svobs_pvs[self._config.get(
            'input_reference_column')] = self._file_context

        # Create and add SVObs.
        self._statvars_map.add_default_pvs(
            self._config.get('default_svobs_pvs', {}), svobs_pvs)
        if not self.resolve_svobs_place(svobs_pvs) and not has_output_column:
            logging.error(f'Unable to resolve SVObs place in {pvs}')
            self._counters.add_counter(f'dropped-svobs-unresolved-place', 1,
                                       statvar_dcid)
            return False
        if not self._statvars_map.add_statvar_obs(svobs_pvs, has_output_column):
            logging.error(
                f'Dropping invalid SVObs {svobs_pvs} for statvar {statvar_pvs} in'
                f' {self._file_context}')
            self._counters.add_counter(f'dropped-svobs-invalid', 1,
                                       statvar_dcid)
            return False
        self._counters.add_counter(f'generated-svobs', 1, statvar_dcid)
        self._counters.add_counter(
            'generated-svobs-' + self.get_current_filename(), 1)
        self._section_svobs += 1
        logging.level_debug() and logging.debug(
            f'Added SVObs {svobs_pvs} in {self._file_context}')
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
            ['measurementDenominator', 'variableMeasured'])
        for statvar_prop in statvar_ref_props:
            for pvs in [statvar_pvs, svobs_pvs]:
                if pvs and statvar_prop in pvs:
                    prop_value = pvs[statvar_prop]
                    prop_value = prop_value.strip().strip('"').strip()
                    if ((not prop_value) or (prop_value[0].isupper()) or
                        (pv_utils.has_namespace(prop_value))):
                        # Property value is a reference to a DCID, skip it.
                        continue
                    # Property has a reference to other properties.
                    # Get a set of selected properties to generate DCID.
                    logging.level_debug() and logging.debug(
                        f'Processing dependant statvar {statvar_prop} for {pvs}'
                    )
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
                        # Add all properties from stavtar if none explicitly
                        # selected.
                        ignore_props = {}
                        if statvar_prop == 'measurementDenominator':
                            # Ignore props like 'name' from denominator
                            ignore_props = self._config.get(
                                'statvar_dcid_ignore_properties', [
                                    'description', 'name', 'nameWithLanguage',
                                    'descriptionUrl', 'alternateName'
                                ])
                        statvar_props = set(statvar_pvs.keys())
                        statvar_props.difference_update(ignore_props)
                        selected_props.update(statvar_props)
                    selected_props.update(additional_props)
                    selected_props.difference_update(exclude_props)
                    # Create a new statvar for the selected PVs
                    new_statvar_pvs = {}
                    for sv_prop in selected_props:
                        if sv_prop in statvar_pvs and sv_prop not in new_statvar_pvs:
                            new_statvar_pvs[sv_prop] = statvar_pvs[sv_prop]
                        elif '=' in sv_prop:
                            prop, value = sv_prop.split('=', 1)
                            new_statvar_pvs[prop] = value
                    statvar_dcid = self.process_stat_var_pvs(new_statvar_pvs)
                    if statvar_dcid:
                        pvs[statvar_prop] = add_namespace(statvar_dcid)
                    else:
                        self._counters.add_counter(
                            f'error_generating_statvar_dcid_{statvar_prop}', 1)
                    logging.level_debug() and logging.debug(
                        f'Generated statvar {statvar_dcid} for '
                        f'{statvar_prop}:{prop_value} with '
                        f'{new_statvar_pvs} from {pvs}')
                    if statvar_prop == 'variableMeasured':
                        # Reset statvar pvs in the caller to the new PVs computed.
                        statvar_pvs.update(new_statvar_pvs)
                        for p in list(statvar_pvs.keys()):
                            if p not in new_statvar_pvs:
                                statvar_pvs.pop(p)

    def process_stat_var_pvs(self,
                             statvar_pvs: dict,
                             statvar_dcid: str = None) -> str:
        """Returns the dcid of the StatVar if processed successfully."""
        if statvar_dcid and not statvar_pvs:
            return statvar_dcid
        # Set the dcid for the StatVar
        self._statvars_map.add_default_pvs(
            self._config.get('default_statvar_pvs'), statvar_pvs)
        if not statvar_dcid:
            statvar_dcid = strip_namespace(statvar_pvs.get(
                'dcid', statvar_dcid))
        if not statvar_dcid:
            statvar_dcid = strip_namespace(
                self._statvars_map.generate_statvar_dcid(statvar_pvs))
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
            self._counters.add_counter(f'warning-svobs-missing-place', 1,
                                       pvs.get('variableMeasured', ''))
            return False
        if is_place_dcid(place):
            # Place is a resolved dcid or a place property.
            return True

        logging.level_debug() and logging.debug(
            f'Resolving place: {place} in {pvs}')
        # Lookup dcid for the place.
        place_dcid = place
        place_pvs = self.resolve_value_references(
            self._pv_mapper.get_all_pvs_for_value(place, 'observationAbout'))
        if place_pvs:
            place_dcid = place_pvs.get('observationAbout', '')
        if not is_place_dcid(place_dcid):
            # Place is not resolved yet. Try resolving through Maps API.
            if self._config.get('resolve_places', False):
                resolved_place = self._place_resolver.resolve_name({
                    place_dcid: {
                        'place_name':
                            place_dcid,
                        'country':
                            pvs.get('#country',
                                    self._config.get('maps_api_country', None)),
                        'administrative_area':
                            pvs.get(
                                '#administrative_area',
                                self._config.get('maps_api_administrative_area',
                                                 None),
                            ),
                    }
                })
                resolved_dcid = resolved_place.get(place_dcid,
                                                   {}).get('dcid', None)
                logging.level_debug() and logging.log(
                    2, f'Got place dcid: {resolved_dcid} for place {place} from'
                    f' {resolved_place}')
                if resolved_dcid:
                    place_dcid = add_namespace(resolved_dcid)
        if is_place_dcid(place_dcid):
            pvs['observationAbout'] = place_dcid
            logging.level_debug() and logging.debug(
                f'Resolved place {place} to {place_dcid}')
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
        output_date_format = self._config.get('observation_date_format', '')
        obs_period = pvs.get('observationPeriod')
        if not output_date_format:
            output_date_format = get_observation_date_format(date_normalized)
        # Check if date is already formatted as expected
        try:
            resolved_date = datetime.datetime.strptime(
                date_normalized,
                output_date_format).strftime(output_date_format)
        except ValueError as e:
            # Date is not in expected format. Try formatting it.
            logging.log(2, f'Formatting date {date} into {output_date_format}')
            resolved_date = ''
        if not resolved_date:
            # If input has a date format, parse date string by input format
            input_date_format = pvs.get(
                self._config.get('date_format_key', '#DateFormat'),
                self._config.get('date_format'),
            )
            if input_date_format:
                try:
                    resolved_date = datetime.datetime.strptime(
                        date_normalized,
                        input_date_format).strftime(output_date_format)
                    logging.log(
                        2,
                        f'Formatted date {date} as {input_date_format} into {resolved_date}'
                    )
                except ValueError as e:
                    logging.error(
                        f'Unable to parse date {date_normalized} as {input_date_format}'
                    )
                    resolved_date = ''
        if not resolved_date:
            # Try formatting date into output format
            resolved_date = eval_functions.format_date(date_normalized,
                                                       output_date_format)
        if not resolved_date:
            return False

        # Got a valid date
        pvs['observationDate'] = resolved_date

        # Set the observation period based on date, if empty
        if obs_period == '':
            period = get_observation_period_for_date(resolved_date,
                                                     pvs['observationPeriod'])
            if period:
                pvs['observationPeriod'] = period
                logging.level_debug() and logging.debug(
                    f'Setting observationPeriod for {resolved_date} to {period}'
                )

        return True

    def write_outputs(self, output_path: str):
        """Generate output mcf, csv and tmcf."""
        logging.info(f'Generating output: {output_path}')
        self._counters.set_prefix('2:prepare_output_')
        self._statvars_map.drop_invalid_statvars()
        if self._config.get('generate_statvar_mcf', True):
            self._counters.set_prefix('3:write_statvar_mcf_')
            statvar_mcf_file = self._config.get('output_statvar_mcf',
                                                output_path + '_stat_vars.mcf')
            self._statvars_map.write_statvars_mcf(filename=statvar_mcf_file,
                                                  mode='w')
        if self._config.get('generate_csv', True):
            self._counters.set_prefix('4:write_svobs_csv_')
            output_csv = self._config.get('output_csv', output_path + '.csv')
            output_tmcf_file = ''
            if self._config.get('generate_tmcf', True):
                output_tmcf_file = self._config.get('output_tmcf_file',
                                                    output_path + '.tmcf')
            self._statvars_map.write_statvar_obs_csv(
                output_csv,
                mode=self._config.get('output_csv_mode', 'w'),
                columns=self._config.get('output_columns', []),
                output_tmcf_file=output_tmcf_file,
            )
        self._counters.print_counters()
        counters_filename = self._config.get('output_counters',
                                             output_path + '_counters.txt')
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
        f'Processing {input_data} with {parallelism} parallel processes.')
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
    header = (f'# Auto generated using command: "{commandline}" on'
              f' {datetime.datetime.now()}\n')
    write_mcf_nodes(
        node_dicts=[statvar_nodes],
        filename=output_mcf_file,
        mode='w',
        sort=True,
        header=header,
    )
    logging.info(
        f'Merged {len(statvar_nodes)} stat var MCF nodes from {mcf_files} into'
        f' {output_mcf_file}.')

    # Create a common TMCF from output, removing the shard suffix.
    with file_util.FileIO(f'{output_path}-00000-of-{num_inputs:05d}.tmcf',
                          mode='r') as tmcf:
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
    config = config_flags.init_config_from_flags(config)
    config_dict = config.get_configs()
    if input_data:
        config_dict['input_data'] = input_data
    if output_path:
        config_dict['output_path'] = output_path
    logging.info(
        f'Processing data {input_data} into {output_path} using config:'
        f' {config_dict}...')
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

        data_processor = data_processor_class(config_dict=config_dict,
                                              counters_dict=counters)
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
    process_http_server.run_http_server(http_port=_FLAGS.http_port,
                                        script=__file__,
                                        module=config_flags)
    process(
        StatVarDataProcessor,
        input_data=_FLAGS.input_data,
        output_path=_FLAGS.output_path,
        config=_FLAGS.config_file,
        pv_map_files=_FLAGS.pv_map,
        parallelism=_FLAGS.parallelism,
    )


if __name__ == '__main__':
    app.run(main)
