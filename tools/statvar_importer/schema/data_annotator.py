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
"""Utility class to annotate data strings with schema property:values.

To generate PVMap for a CSV data file, run the command:
  python data_annotator.py \
      --data_annotator_input=<input-csv> \
      --annotator_output_pv_map=<output-pvmap.csv> \
      --llm_data_context=<text-file-with-metadata> \
      --llm_sample_statvars=<MCF-file-with-example-statvars-forsimilar-topics> \
      --google_api_key=<GOOGLE_API_KEY> \
      --llm_data_annotation=True

  To use LLM to generate PVMaps, set a Google API Key and llm_data_annotation=True.
  API keys can be obtained by following the steps in:
    https://ai.google.dev/gemini-api/docs/api-key
"""

import csv
import os
import pprint
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
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR))),
                 'util'))

_FLAGS = flags.FLAGS

flags.DEFINE_string('data_annotator_input', '',
                    'CSV file with columns to be annotated.')
flags.DEFINE_string('annotator_output_pv_map', '',
                    'Output file with annotations for data strings.')
flags.DEFINE_string('data_annotator_config', '',
                    'Configuration dictionary for annotator.')
flags.DEFINE_boolean('llm_data_annotation', True,
                     'Enable data annotations with LLM.')

import data_sampler
import file_util
import process_http_server

from config_map import ConfigMap
from counters import Counters
from ngram_matcher import NgramMatcher, normalized_string
from schema_matcher import SchemaMatcher
from llm_pvmap_generator import LLM_PVMapGenerator, get_llm_config_from_flags

import config_flags

# Regex
_NUMBER_REGEX = r'^[+0-9,\.$%-]+\s*$'

# Default data annotation config
# Includes annotators for place, date and value.
_DEFAULT_ANNOTATION_CONFIG = [
    # Date
    {
        'data_type': 'DATE',
        'wordlist': 'date,year,month,day,time',
        'wordlist_file': os.path.join(_SCRIPT_DIR, 'words_dates.txt'),
        # Match any pattern of the form: YYYY-MM-DD
        'regex': [
            r'^(1[89]|20)[0-9]{2}$',  # YYYY
            r'^[0-9]{4}[-/][0-9]{,2}$',  # YYYY-MM
            r'^[0-9]{4}[-/][0-9]{,2}[-/][0-9]{,2}$',  # YYYY-MM-DD
            r'^[0-9]{,2}[-/][0-9]{,2}[-/][0-9]{,4}$',  # DD-MM-YYYY
            r'[0-9/-]{,2}.*\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z/-]*[0-9]{,2}',  # Months
        ],
        'annotations': ['observationDate={Data}'],
    },
    # Value
    {
        'data_type': 'VALUE',
        'wordlist': 'count,total,amount,number,value,cost,price,ratio,index',
        'wordlist_file': '',
        'regex': [_NUMBER_REGEX],
        'annotations': ['value={Number}',],
    },
    # Place
    {
        'data_type': 'PLACE',
        'wordlist': 'place,country,state,district,county,city,location,address',
        'wordlist_file': os.path.join(_SCRIPT_DIR, 'words_place_names.txt'),
        'annotations': ['observationAbout={Data}'],
    },
]


# Data Annotator config
# dictionary of annotation types
# For each annotation, a regx or list of words to match followed by pvs.
def get_data_annotator_config() -> dict:
    config = {
        'data_annotation_config': _DEFAULT_ANNOTATION_CONFIG,
        'llm_data_annotation': _FLAGS.llm_data_annotation,
    }
    config.update(get_llm_config_from_flags())
    return config


# Base class to annotate possible types for a data string.
# Data type classification ise base on trigger words or regex.
class DataTypeAnnotator:

    def __init__(
        self,
        data_type: str = '',
        pvs: dict = {},
        words: str = [],
        words_file: str = '',
        regex_list: list[str] = [],
        config_dict: dict = {},
        counters: Counters = None,
    ):
        self._config = ConfigMap()
        self._config.update_config(config_dict)
        self._counters = counters
        if counters is None:
            self._counters = Counters()

        self._log_every_n = self._config.get('log_every_n', 10)
        self._data_type = data_type
        # PVs to be returned on a match for the type.
        self._data_pvs = set()
        self.add_data_pvs(pvs)

        # Load words to match on regex
        self._regex_list = []
        self.add_regex_list(regex_list)

        self._ngram_matcher = None
        # Load match words into the ngram matcher
        if words:
            self.add_match_words(words)
        if words_file:
            for file in file_util.file_get_matching(words_file):
                file_words = file_util.file_load_csv_dict(file)
                for key, value in file_words.items():
                    self.add_match_words(key)
                    self.add_match_words(value)
        logging.level_debug() and logging.debug(
            f'Added {self._ngram_matcher.get_tuples_count()} words for {self._data_type}'
        )

    def get_data_type(self):
        """Returns the annotators data_type."""
        return self._data_type

    def add_data_pvs(self, pvs: dict):
        """Add data PVs to be returned on a match."""
        logging.level_debug() and logging.log_every_n(
            logging.DEBUG, f'Adding PVs for {self._data_type}: {pvs}',
            self._log_every_n)
        self._data_pvs.update(pvs)

    def add_regex_list(self, regex_list: str):
        """Add a regex match."""
        for regex in regex_list:
            if regex:
                self._regex_list.append(re.compile(regex))
        logging.level_debug() and logging.log_every_n(
            logging.DEBUG,
            f'Added regex for {self._data_type}: {self._regex_list}',
            self._log_every_n)

    def add_match_words(self, words: str):
        """Add a list of words to match on."""
        if self._ngram_matcher is None:
            self._ngram_matcher = NgramMatcher()
        if isinstance(words, str):
            words = words.split(',')
        for word in words:
            for w in word.split(','):
                w = w.strip()
                self._ngram_matcher.add_key_value(w, self._data_type)

    def get_matches(self, value: str) -> dict:
        """Returns the type for the input string."""
        normalized_value = normalized_string(value)
        # Get matches by regex and ngrams.
        matches = self.get_regex_matches(normalized_value)
        matches.extend(self.get_ngram_matches(normalized_value))
        self._counters.add_counter(f'{self._data_type}-lookups', 1)
        if matches:
            self._counters.add_counter(f'{self._data_type}-matches', 1)
            logging.level_debug() and logging.log_every_n(
                2,
                f'Got {len(matches)} {self._data_type} matches for {value} {matches}',
                self._log_every_n)
            return self._data_pvs
        return {}

    def get_regex_matches(self, value: str) -> list:
        """Returns regex matches by regex."""
        matches = []
        for regex in self._regex_list:
            self._counters.add_counter('regex-lookups', 1)
            for m in regex.findall(value):
                matches.append(m)
                self._counters.add_counter('regex-matches', 1)
        return matches

    def get_ngram_matches(self, value: str) -> list:
        """Returns matches in value by ngram matcher."""
        matches = []
        if self._ngram_matcher:
            ngram_matches = self._ngram_matcher.lookup(value)
            for key, data_type in ngram_matches:
                matches.append(key)
                self._counters.add_counter('ngram-matches', 1)
            self._counters.add_counter('ngram-lookups', 1)
        return matches


# Registry of data type annotators.
_DATA_TYPE_ANNOTATORS = {
    # Default Data Type Annotator
    '': {
        'class': DataTypeAnnotator,
        'data_type': '',
    }
}


def register_data_annotator(data_type: str, cls, args):
    """Register a data annotator for a given data type.

  Args:
    data_type: string for the data the annotator can support
    cls: DataTypeAnnotator class
    args: arguments to be passed to initializer.
  """
    _DATA_TYPE_ANNOTATORS[data_type] = {
        'class': cls,
        'data_type': data_type,
        'init_args': args
    }


def get_data_annotator(data_type: str,
                       data_pvs: dict = {},
                       words: list = [],
                       words_file: str = '',
                       regex_list: list = [],
                       config_dict: dict = {},
                       counters: Counters = None) -> DataTypeAnnotator:
    """Returns a data type annotator for the given type."""
    annotator = _DATA_TYPE_ANNOTATORS.get(data_type)
    if annotator is None:
        # Get the default annotator
        annotator = _DATA_TYPE_ANNOTATORS['']
        logging.debug(
            f'No annotator registered for {data_type}. Known types: {list(_DATA_TYPE_ANNOTATORS.keys())}'
        )

    return annotator['class'](data_type, data_pvs, words, words_file,
                              regex_list, config_dict, counters,
                              **annotator.get('init_args', {}))


# Class to invoke data type annotators on a data set.
class DataAnnotator:

    def __init__(
        self,
        config_dict: dict = {},
        counters: Counters = None,
    ):
        self._config = ConfigMap()
        self._config.update_config(config_dict)
        self._counters = counters
        if counters is None:
            self._counters = Counters()

        self._data_type_annotators = []
        self._number_regex = re.compile(
            self._config.get('number_regex', _NUMBER_REGEX))
        self.reset()
        data_annotation_config = self._config.get('data_annotation_config',
                                                  _DEFAULT_ANNOTATION_CONFIG)
        self.add_data_type_annotators(data_annotation_config)
        self._llm_annotator = None
        if self._config.get('llm_data_annotation', False):
            self._llm_annotator = LLM_PVMapGenerator(self._config.get_configs(),
                                                     self._counters)
        self._sample_data_file = ''
        self._schema_matcher = SchemaMatcher(config=self._config.get_configs(),
                                             counters=self._counters)
        self._output_pvmap = {}

    def reset(self):
        """Reset current annotations for a file."""
        # property:values counts and from different annotators by index.
        self._row_pv_counts: dict[int:dict[str:int]] = {}
        self._col_pv_counts: dict[int:dict[str:int]] = {}
        # Unique strings with counts in rows and columns, keyed by index.
        self._row_str_counts: dict[int:dict[str:int]] = {}
        self._col_str_counts: dict[int:dict[str:int]] = {}
        self._col_headers_str: dict[int:dict[int:str]] = {}
        # Annotations for each string with counts
        self._str_pv_counts: dict[str:dict[str:int]] = {}
        self._header_rows = 0

    def add_annotations(self, row_index: int, col_index: int, value: str,
                        pvs: list):
        """Add a set of property:values for a data string at row_index:column_index."""
        # Add counts for annotataion pvs for row and column.
        logging.level_debug() and logging.log(
            2, f'Adding annotations: {row_index}:{col_index}:{value}:{pvs}')
        add_index_counts(col_index, pvs, self._col_pv_counts)
        add_index_counts(row_index, pvs, self._row_pv_counts)
        if value is not None:
            # Add counts for unique values for row and column.
            if value not in self._col_str_counts:
                # Save unique values in a column with the row index
                col_headers = self._col_headers_str.get(col_index, {})
                col_headers[row_index] = value
                self._col_headers_str[col_index] = col_headers
            add_index_counts(col_index, [value], self._col_str_counts)
            add_index_counts(row_index, [value], self._row_str_counts)
        add_index_counts(value, pvs, self._str_pv_counts)

    def add_data_type_annotators(self, config: list):
        """Add a data type annotators."""
        if config is None:
            return
        if isinstance(config, dict):
            config = [config]
        for cfg in config:
            # Register an annotator for the config.
            annotator = get_data_annotator(
                data_type=cfg.get('data_type', ''),
                data_pvs=cfg.get('annotations', ''),
                words=cfg.get('wordlist', '').split(','),
                words_file=cfg.get('wordlist_file', ''),
                regex_list=cfg.get('regex', ''),
                config_dict=self._config.get_configs(),
                counters=self._counters)
            if not annotator:
                logging.fatal(f'Unable to get data annotator for : {cfg}')
            self._data_type_annotators.append(annotator)

    def annotate_value(self, value: str) -> dict:
        """Returns property:value annotations fir the value from all annotators."""
        data_pvs = []
        if not value:
            return data_pvs
        for atr in self._data_type_annotators:
            atr_pvs = atr.get_matches(value)
            if atr_pvs:
                data_type = atr.get_data_type()
                data_pvs.append(f'DataType={data_type}')
                data_pvs.extend(atr_pvs)
                self._counters.add_counter(f'annotations-{data_type}', 1)
                break
        return data_pvs

    # def get_num_header_rows(self) -> int:
    #     """Get the number of header rows based on first row with numbers."""
    #     max_rows = self._config.get('max_headers', 100)
    #     max_num_counts = 1
    #     header_rows = 0
    #     for index in range(1, max_rows):
    #         count_nums = self._row_pv_counts('DataType=NUMBER')
    #         if count_nums == 0 and header_rows == (index - 1):
    #             header_rows = index
    #         if count_nums > max_num_counts:
    #             max_num_counts = count_nums
    #             header_rows = index - 1

    def is_number(self, value: str) -> bool:
        """Returns True if the value is a number."""
        if self._number_regex.match(value):
            return True
        return False

    def annotate_row(self, row_index: int, row: list[str]):
        """Get annotations for all values in a  data row."""
        self._counters.add_counter('annotate-input-rows', 1)
        # Process all columns in the csv row
        col_index = 0
        for value in row:
            self._counters.add_counter('annotate-input-cells', 1)
            col_index += 1
            # Get annotations for the cell value.
            value = value.strip().strip('"').strip()
            pvs = self.annotate_value(value)
            is_num = self.is_number(value)
            # Get the non-numeric string for annotation
            non_num_val = value
            if is_num:
                non_num_val = None
            # Record the annotations for the row and column.
            self.add_annotations(row_index, col_index, non_num_val, pvs)

    def annotate_file(self, filename: str, output_path: str) -> dict:
        """Get annotations for all cells in a CSV file."""
        input_files = file_util.file_get_matching(filename)
        for file in input_files:
            num_rows = file_util.file_estimate_num_rows(file)
            if num_rows > 1000:
                # Down sample very large files to preserve unique column strings.
                sample_file = data_sampler.sample_csv_file(
                    file, config=self._config.get_configs())
                sample_rows = file_util.file_estimate_num_rows(sample_file)
                logging.info(
                    f'Sampling {num_rows} rows {file} into {sample_rows} rows in {sample_file}'
                )
                file = sample_file

            # Process each row in the csv file.
            with file_util.FileIO(file) as input_file:
                self.reset()
                self._counters.add_counter('annotate-input-file', 1)
                csv_reader = csv.reader(
                    input_file,
                    **file_util.file_get_csv_reader_options(input_file))
                row_index = 0
                for row in csv_reader:
                    row_index += 1
                    self.annotate_row(row_index, row)
                    if row_index > self._config.get('annotate_max_rows', 10000):
                        break
            logging.info(f'Got {len(self._str_pv_counts)} unique strings.')

            # Get pvmap from annotations
            pv_map = self.generate_pvmap()

            # Add LLM annotations.
            if self._llm_annotator:
                self._llm_annotator.load_sample_data(file)
                sample_pvs = self.lookup_schema_pvs(pv_map)
                self._llm_annotator.add_sample_pvs(sample_pvs)
                pv_map = self._llm_annotator.generate_pvmap(pv_map)

            self._output_pvmap.update(pv_map)

        # Save annotations generated
        if output_path:
            self.write_annotations(output_path)

        if logging.level_debug():
            logging.debug(f'Annotations for {filename}:')
            pprint.pprint(self._row_pv_counts)
            pprint.pprint(self._col_pv_counts)
            pprint.pprint(self._row_str_counts)
            pprint.pprint(self._col_str_counts)
            pprint.pprint(self._str_pv_counts)

        return self._output_pvmap

    def get_column_header(self, col_index: int, header_rows: int = 0) -> str:
        """Returns the first non-empty string for the column as the header."""
        # Get the last header string for the column.
        col_headers = self._col_headers_str.get(col_index, {})
        for row_index in range(self._header_rows, 0, -1):
            col_str = col_headers.get(row_index)
            if col_str:
                logging.debug(
                    f'Got column header at {row_index}:{col_index}:{col_str}')
                return col_str
        # Get the first unique string for the column.
        col_str_counts = self._col_str_counts.get(col_index, {})
        for col_str, count in col_str_counts.items():
            if col_str and count > 0:
                logging.debug(f'Got column header for {col_index}:{col_str}')
                return col_str
        return ''

    def generate_pvmap(self) -> dict:
        """Returns the annotations collected for the current file."""
        pv_map = {}

        # Get the row where data values begin.
        # Row upto first data row are treated as headers.
        self._header_rows = 1
        data_type = 'DataType=VALUE'
        max_row = 1
        if self._row_pv_counts:
            max_row = max(self._row_pv_counts.keys())
        for row_index in range(self._header_rows + 1, max_row + 1):
            row_pvs = self._row_pv_counts.get(row_index)
            if row_pvs:
                if data_type in row_pvs:
                    logging.debug(
                        f'Found data values from row {row_index}: {row_pvs}')
                    break
        self._header_rows = max(1, row_index - 1)

        # Get max count for PVs across columns
        max_col_pv_count = 0
        max_columns = max(self._col_pv_counts.keys())
        for col_index in range(1, max_columns + 1):
            col_pvs = self._col_pv_counts.get(col_index, {})
            for pv, count in col_pvs.items():
                max_col_pv_count = max(max_col_pv_count, count)

        # Get columns with majority PVs.
        min_pv_col_count = max_col_pv_count / 2
        cols_with_headers = {}
        for col_index in range(1, max_columns + 1):
            col_pvs = self._col_pv_counts.get(col_index, {})
            col_header_str = self.get_column_header(col_index)
            if not col_header_str:
                # ignore columns without a header
                continue
            for pv, count in col_pvs.items():
                if count >= min_pv_col_count:
                    # use only the first DataType
                    if pv.startswith('DataType'):
                        if col_index in cols_with_headers:
                            break
                        cols_with_headers[col_index] = col_header_str
                    # Column has a majority PV. Add it for the column header.
                    _add_pv(col_header_str, '#Column', col_index, pv_map)
                    _add_pv(col_header_str, pv, '', pv_map)

        logging.level_debug() and logging.debug(
            f'Got column header pvs for {cols_with_headers}: {pv_map}')
        self._counters.add_counter('annotate-output-col-headers',
                                   len(cols_with_headers))

        # Get strings from the remaining columns.
        for col_index in range(1, max_columns + 1):
            if col_index in cols_with_headers:
                # Ignore columns with headers.
                continue
            col_strs = self._col_str_counts.get(col_index, {})
            for col_str, count in col_strs.items():
                if count > self._config.get('annotation_min_col_count', 0):
                    _add_pv(col_str, '#Column', col_index, pv_map)

        # Add remaining strings from header rows
        for row_index in range(1, self._header_rows + 1):
            row_str_counts = self._row_str_counts.get(row_index, {})
            for row_str, count in row_str_counts.items():
                if row_str not in pv_map:
                    _add_pv(row_str, '#Row', row_index, pv_map)

        logging.level_debug() and logging.debug(f'Got column pv_map: {pv_map}')
        self._counters.add_counter('annotate-output-pvmap-keys', len(pv_map))
        return pv_map

    def write_annotations(self, output_file: str):
        """Write annotations for data strings into the file."""
        pv_map = self._output_pvmap
        if pv_map:
            write_pv_map(pv_map, output_file)

    def lookup_schema_pvs(self, pv_map: dict) -> dict:
        """Retuns the PV maps from schema matcher for the pv-map keys."""
        result_pvs = {}
        logging.info(f'Looking up schema PVs for {len(pv_map)} queries')
        for key in pv_map.keys():
            pvs = self._schema_matcher.lookup_pvs_for_query(key,
                                                            prop_as_key=True)
            if pvs:
                result_pvs[key] = pvs
        return result_pvs


def _add_pv(key: str, prop: str, value: str, pvmap: dict) -> dict:
    """Adds a pv to the pvmap for the key."""
    key_pvs = pvmap.get(key, {})
    if '=' in prop:
        prop, value = prop.split('=', 1)
    key_pvs[prop] = value
    pvmap[key] = key_pvs
    return pvmap


def write_pv_map(pv_map: dict, file: str):
    """Write the pvmap to a file."""
    if file_util.file_is_csv(file):
        # Write the pvmap as CSV
        with file_util.FileIO(file_util.file_get_name(file), 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['key', 'property', 'value'])
            for key, pvs in pv_map.items():
                if not key:
                    continue
                row = [key]
                for prop, value in pvs.items():
                    if prop:
                        row.append(prop)
                        row.append(value)
                csv_writer.writerow(row)
    else:
        # Write pvmap as a dict
        file_util.file_write_py_dict(pv_map, file)
    logging.info(f'Wrote {len(pv_map)} keys into pvmap: {file}')


def generate_pvmap(data_file: str,
                   pv_map_output: str,
                   config: ConfigMap = None,
                   counters: Counters = None) -> dict:
    """Generate a PV map for a data file."""
    if config is None:
        config = ConfigMap(config_dict=get_data_annotator_config())
    if counters is None:
        counters = Counters()
    logging.info(
        f'Generating pvmap for {data_file} with config: {config.get_configs()}')
    da = DataAnnotator(config.get_configs(), counters)
    pvmap = da.annotate_file(data_file, pv_map_output)
    counters.print_counters()
    return pvmap


def add_index_counts(index: int, values: list[str],
                     indexed_counts: dict[int:dict[str:int]]) -> dict:
    """Add annotations to the stats dict, aggregating counts."""
    counts = indexed_counts.get(index, OrderedDict())
    indexed_counts[index] = add_counts(values, counts)


def add_counts(values: list[str], counts: dict[str:int]) -> dict:
    """Increment counts for each value."""
    if counts is None:
        counts = OrderedDict()
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    return counts


def main(_):
    # Launch a web server with a form for commandline args
    # if the command line flag --http_port is set.
    if process_http_server.run_http_server(script=__file__, module=__name__):
        return

    logging.set_verbosity(1)
    counters = Counters()
    config = ConfigMap(config_dict=get_data_annotator_config(),
                       filename=_FLAGS.data_annotator_config)
    generate_pvmap(_FLAGS.data_annotator_input, _FLAGS.annotator_output_pv_map,
                   config)


if __name__ == '__main__':
    app.run(main)
