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
"""Utilities to sample csv files.

To sample a CSV data file, run the command:
  python data_sampler.py --sampler_input=<input-csv> --sampler_output=<output-csv>

This generates a sample output CSV with atmost 100 rows selecting input rows
with unique column values.

Use the function: sample_csv_file(<input_file>, <output_file>)
to generate sample CSV in code.
"""

import csv
import os
import random
import re
import sys
import tempfile

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

flags.DEFINE_string('sampler_input', '', 'CSV file to be sample')
flags.DEFINE_string('sampler_output', '', 'Output file for CSV.')
flags.DEFINE_integer('sampler_output_rows', 100,
                     'Maximum number of output rows.')
flags.DEFINE_integer('sampler_header_rows', 1,
                     'Number of header rows to be copied to output.')
flags.DEFINE_integer('sampler_rows_per_key', 5,
                     'Number of rows per unique value.')
flags.DEFINE_float('sampler_rate', -1, 'Number of rows per unique value.')
flags.DEFINE_string('sampler_column_regex', r'^[0-9]{4}$|[a-zA-Z-]',
                    'Regex to select unique column values.')
flags.DEFINE_string('sampler_unique_columns', '',
                    'List of columns to look for unique values.')
flags.DEFINE_string('sampler_input_delimiter', ',', 'delimiter for input data')
flags.DEFINE_string('sampler_input_encoding', 'UTF8',
                    'delimiter for input data')
flags.DEFINE_string('sampler_output_delimiter', None,
                    'delimiter for output data')

_FLAGS = flags.FLAGS

import file_util
import process_http_server

from config_map import ConfigMap
from counters import Counters
from config_map import ConfigMap


# Class to sample a data file.
class DataSampler:

    def __init__(
        self,
        config_dict: dict = None,
        counters: dict = None,
    ):
        self._config = ConfigMap(config_dict=get_default_config())
        if config_dict:
            self._config.add_configs(config_dict)
        self._counters = counters
        if counters is None:
            self._counters = Counters()
        self.reset()

    def reset(self):
        """Reset state for unique column values."""
        # Dictionary of unique values: count per column
        self._column_counts = {}
        # Dictionary of column index: list of header strings
        self._column_headers = {}
        self._column_regex = None
        regex = self._config.get('sampler_column_regex')
        if regex:
            self._column_regex = re.compile(regex)
        self._selected_rows = 0

    def __del__(self):
        logging.log(2, f'Sampler column headers: {self._column_headers}')
        logging.log(2, f'sampler column counts: {self._column_counts}')

    def _get_column_count(self, column_index: int, value: str) -> int:
        """Returns the existing number of rows for column value.
        Count is only returned for values matching sampler_column_regex.

        Args:
          column_index: index of the column value in the current row.
          value: string value of the column in oclumn_index

        Returns:
          number of times this value has been seen before for the column.
          sys.maxsize if column value doesn't match sampler_column_regex
        """
        # Check if column value is to be tracked.
        if self._column_regex:
            if not self._column_regex.search(value):
                # Not an interesting value.
                return sys.maxsize

        col_values = self._column_counts.get(column_index)
        if col_values is None:
            return 0
        return col_values.get(value, 0)

    def _add_column_header(self, column_index: int, value: str):
        """Adds the first value for column as header."""
        cur_header = self._column_headers.get(column_index, '')
        if not cur_header and value:
            # This is the first value for the column. Set as header.
            self._column_headers[column_index] = value
            return value
        return cur_header

    def _add_row_counts(self, row: list):
        """Update column counts for a selected row."""
        # Update counts for each column value in the row.
        for index in range(len(row)):
            value = row[index]
            col_counts = self._column_counts.get(index)
            if col_counts is None:
                # Add a new column
                col_counts = {}
                self._column_counts[index] = col_counts
            # Add count for column value
            if value not in col_counts:
                header = self._add_column_header(index, value)
                self._counters.add_counter(
                    f'sampler-unique-values-column-{index}-{header}', 1)
            count = col_counts.get(value, 0)
            col_counts[value] = count + 1
        self._selected_rows += 1
        return

    def select_row(self, row: list, sample_rate: float = -1) -> bool:
        """Returns True if row can be added ot the sample output."""
        max_rows = self._config.get('sampler_output_rows')
        if max_rows > 0 and self._selected_rows >= max_rows:
            # Too many rows already selected. Drop it.
            return False
        max_count = self._config.get('sampler_rows_per_key', 3)
        max_uniques_per_col = self._config.get('sampler_uniques_per_column', 10)
        for index in range(len(row)):
            value = row[index]
            value_count = self._get_column_count(index, value)
            if value_count == 0 or value_count < max_count:
                # This is a new value for this column.
                col_counts = self._column_counts.get(index, {})
                if len(col_counts) < max_uniques_per_col:
                    # Column has few unique values. Select this row for column.
                    self._counters.add_counter(f'sampler-selected-rows', 1)
                    self._counters.add_counter(
                        f'sampler-selected-column-{index}', 1)
                    return True
        # No new unique value for the row.
        # Check random sampler.
        if sample_rate < 0:
            sample_rate = self._config.get('sampler_rate')
        if random.random() <= sample_rate:
            self._counters.add_counter(f'sampler-sampled-rows', 1)
            return True
        return False

    def sample_csv_file(self, input_file: str, output_file: str = '') -> str:
        """Emits a sample of rows from input_file into the output.

        Args:
          input_file: CSV file to be processed.
          output_file: CSV file to be generated with smapled rows.
          config: dictionary of config parameters:
             output_rows: Maximum output rows to be generated.
             header_rows: Header rows to be copied to the output as is.
             rows_per_key: Maximum rows per unique value.
             unique_columns: List of columns to select unique keys.
               It can be column numbers or column headers.
               For a combination of columns, use '+', such as 1+2.
          counters: dictionary of counters to be updated.

        Returns:
          output file with the sampled rows.
        """
        max_rows = self._config.get('sampler_output_rows')
        sample_rate = self._config.get('sampler_rate')
        header_rows = self._config.get('header_rows', 1)
        input_files = file_util.file_get_matching(input_file)
        if not input_files:
            return None
        output_delimiter = self._config.get('output_delimiter')
        if not output_file:
            if not file_util.file_is_local(output_file):
                output_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix='-sample.csv').name
            else:
                output_file = file_util.file_get_name(input_files[0], '-sample',
                                                      '.csv')
        # Set sampling rate by file size
        num_rows = file_util.file_estimate_num_rows(input_files)
        if num_rows and self._config.get('sampler_rate') < 0:
            if max_rows > 0:
                sample_rate = float(max_rows) / float(num_rows)
                logging.debug(
                    f'Sampling rate for {input_files}: {sample_rate} for {num_rows} rows'
                )

        # Get sample rows from each input file.
        for input_index in range(len(input_files)):
            file = input_files[input_index]
            input_encoding = self._config.get('input_encoding')
            if not input_encoding:
                input_encoding = file_util.file_get_encoding(file)
            with file_util.FileIO(file, encoding=input_encoding) as csv_file:
                csv_options = {'delimiter': self._config.get('input_delimiter')}
                csv_options = file_util.file_get_csv_reader_options(
                    file, csv_options)
                if not output_delimiter:
                    # No output delimiter set. Use same as input.
                    output_delimiter = csv_options.get('delimiter', ',')
                output_mode = 'w' if input_index == 0 else 'a'
                # Write sample rows from current input
                with file_util.FileIO(output_file, mode=output_mode) as output:
                    csv_writer = csv.writer(output,
                                            delimiter=output_delimiter,
                                            doublequote=False,
                                            escapechar='\\')
                    logging.level_debug() and logging.debug(
                        f'Sampling rows from {file} with config: {self._config.get_configs()}'
                    )
                    # Examine each input row for any unique column values
                    csv_reader = csv.reader(csv_file, **csv_options)
                    row_index = 0
                    for row in csv_reader:
                        self._counters.add_counter(f'sampler-input-row', 1)
                        row_index += 1
                        # Write headers from first input file to the output.
                        if row_index <= header_rows and input_index == 0:
                            csv_writer.writerow(row)
                            self._counters.add_counter(f'sampler-header-rows',
                                                       1)
                            continue
                        # Check if input row has any unique values to be output
                        if self.select_row(row, sample_rate):
                            self._add_row_counts(row)
                            csv_writer.writerow(row)
                            logging.level_debug() and logging.log(
                                2, f'Selecting row:{file}:{row_index}')
                        if max_rows > 0 and self._selected_rows >= max_rows:
                            # Got enough sample output rows
                            break
                logging.info(
                    f'Sampled {self._selected_rows} row from {file} into {output_file}'
                )
        logging.level_debug() and logging.debug(
            f'Column counts: {self._column_counts}')
        return output_file


def sample_csv_file(input_file: str,
                    output_file: str = '',
                    config: dict = {}) -> str:
    """Returns the output file name into which a sample of rows from input_file is written.

    Args:
      input_file: input file pattern to be loaded.
      output_file: (optional) output file into whcih sampled rows are written.
        If empty, creates a file with suffix '-sample.csv'
      config: dictionary of parameters for sampling including:
        sampler_output_rows: maximum number of output rows.
        sampler_rate: number between 0 to 1 for sampling rate if
          sampler_output_rows is not set.
        header_rows: number of headers rows from input copied over to output.
        sampler_column_regex: regex to select unique cell values
        sampler_rows_per_key: number of rows with duplcate values for a key.
    """
    data_sampler = DataSampler(config_dict=config)
    return data_sampler.sample_csv_file(input_file, output_file)


def get_default_config() -> dict:
    """Returns a dictionary of config parameter values from flags."""
    # Use default values of flags for tests
    if not _FLAGS.is_parsed():
        _FLAGS.mark_as_parsed()
    return {
        'sampler_rate': _FLAGS.sampler_rate,
        'sampler_input': _FLAGS.sampler_input,
        'sampler_output': _FLAGS.sampler_output,
        'sampler_output_rows': _FLAGS.sampler_output_rows,
        'header_rows': _FLAGS.sampler_header_rows,
        'sampler_rows_per_key': _FLAGS.sampler_rows_per_key,
        'sampler_column_regex': _FLAGS.sampler_column_regex,
        'sampler_unique_columns': _FLAGS.sampler_unique_columns,
        'input_delimiter': _FLAGS.sampler_input_delimiter,
        'output_delimiter': _FLAGS.sampler_output_delimiter,
        'input_encoding': _FLAGS.sampler_input_encoding,
    }


def main(_):
    sample_csv_file(_FLAGS.sampler_input, _FLAGS.sampler_output)


if __name__ == '__main__':
    app.run(main)
