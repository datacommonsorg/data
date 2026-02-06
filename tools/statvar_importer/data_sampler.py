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


def _define_flags():
    flags.DEFINE_string('sampler_input', '',
                        'The path to the input CSV file to be sampled.')
    flags.DEFINE_string('sampler_output', '',
                        'The path to the output file for the sampled CSV data.')
    flags.DEFINE_integer(
        'sampler_output_rows', 100,
        'The maximum number of rows to include in the sampled output.')
    flags.DEFINE_integer(
        'sampler_header_rows', 1,
        'The number of header rows to be copied directly to the output file.')
    flags.DEFINE_integer(
        'sampler_rows_per_key', 5,
        'The maximum number of rows to select for each unique value found.')
    flags.DEFINE_float(
        'sampler_rate', -1,
        'The sampling rate for random row selection (e.g., 0.1 for 10%).')
    # TODO: Rename to sampler_cell_value_regex to better reflect its purpose.
    # See: https://github.com/datacommonsorg/data/pull/1445#discussion_r2180147075
    flags.DEFINE_string(
        'sampler_column_regex', r'^[0-9]{4}$|[a-zA-Z-]',
        'A regular expression used to identify and select unique column values.')
    flags.DEFINE_string(
        'sampler_unique_columns', '',
        'A comma-separated list of column names to use for selecting unique rows.'
    )
    flags.DEFINE_string('sampler_input_delimiter', ',',
                        'The delimiter used in the input CSV file.')
    flags.DEFINE_string('sampler_input_encoding', 'UTF8',
                        'The encoding of the input CSV file.')
    flags.DEFINE_string('sampler_output_delimiter', None,
                        'The delimiter to use in the output CSV file.')


import file_util

from config_map import ConfigMap
from counters import Counters


# Class to sample a data file.
class DataSampler:
    """A class for sampling data from a file.

    This class provides functionality to sample rows from a CSV file based on
    various criteria such as unique values in columns, sampling rate, and maximum
    number of rows.

    Attributes:
        _config: A ConfigMap object containing the configuration parameters.
        _counters: A Counters object for tracking various statistics during the
          sampling process.
        _column_counts: A dictionary to store the count of unique values per
          column.
        _column_headers: A dictionary to store the headers of the columns.
        _column_regex: A compiled regular expression to filter column values.
        _selected_rows: The number of rows selected so far.
    """

    def __init__(
        self,
        config_dict: dict = None,
        counters: Counters = None,
    ):
        """Initializes the DataSampler object.

        Args:
            config_dict: A dictionary of configuration parameters.
            counters: A Counters object for tracking statistics.
        """
        self._config = ConfigMap(config_dict=get_default_config())
        if config_dict:
            self._config.add_configs(config_dict)
        self._counters = counters if counters is not None else Counters()
        self.reset()

    def reset(self) -> None:
        """Resets the state of the DataSampler.

        This method resets the internal state of the DataSampler, including the
        counts of unique column values and the number of selected rows. This is
        useful when you want to reuse the same DataSampler instance for sampling
        multiple files.
        """
        # Dictionary of unique values: count per column
        self._column_counts = {}
        # Dictionary of column index: list of header strings
        self._column_headers = {}
        self._column_regex = None
        regex = self._config.get('sampler_column_regex')
        if regex:
            self._column_regex = re.compile(regex)
        self._selected_rows = 0
        # Parse unique column names from config
        self._unique_column_names = []
        self._unique_column_indices = {}
        unique_cols_str = self._config.get('sampler_unique_columns', '')
        if unique_cols_str:
            self._unique_column_names = [
                col.strip()
                for col in unique_cols_str.split(',')
                if col.strip()
            ]

    def __del__(self) -> None:
        """Logs the column headers and counts upon object deletion."""
        logging.log(2, f'Sampler column headers: {self._column_headers}')
        logging.log(2, f'sampler column counts: {self._column_counts}')

    def _get_column_count(self, column_index: int, value: str) -> int:
        """Returns the existing number of rows for a given column value.

        This method checks if the value in a specific column should be tracked and
        returns the number of times this value has been seen before for that
        column.

        Args:
            column_index: The index of the column in the current row.
            value: The string value of the column at the given index.

        Returns:
            The number of times the value has been seen before for the column.
            Returns sys.maxsize if the column should not be tracked or if the
            column value does not match the sampler_column_regex.
        """
        # Check if this column should be tracked
        if not self._should_track_column(column_index):
            return sys.maxsize
        # Check if column value is to be tracked.
        if self._column_regex:
            if not self._column_regex.search(value):
                # Not an interesting value.
                return sys.maxsize

        col_values = self._column_counts.get(column_index)
        if col_values is None:
            return 0
        return col_values.get(value, 0)

    def _should_track_column(self, column_index: int) -> bool:
        """Determines if a column should be tracked for unique values.

        Args:
            column_index: The index of the column.

        Returns:
            True if the column should be tracked (either no unique columns
            specified or this column is in the unique columns list).
        """
        if not self._unique_column_names:
            # No specific columns specified, track all
            return True
        # Check if this column is in our unique columns
        return column_index in self._unique_column_indices.values()

    def _process_header_row(self, row: list[str]) -> None:
        """Process a header row to build column name to index mapping.

        This method is called for each header row (up to header_rows config) to
        search for columns specified in sampler_unique_columns. It only maps
        columns that are in the configured list. If called multiple times with
        duplicate column names, the last mapping is used.

        Args:
            row: A header row containing column names.
        """
        if not self._unique_column_names:
            return

        for index, column_name in enumerate(row):
            if column_name in self._unique_column_names:
                self._unique_column_indices[column_name] = index
                logging.level_debug() and logging.debug(
                    f'Mapped unique column "{column_name}" to index {index}')

    def _add_column_header(self, column_index: int, value: str) -> str:
        """Adds the first non-empty value of a column as its header.

        Args:
            column_index: The index of the column.
            value: The value to be considered for the header.

        Returns:
            The header of the column.
        """
        cur_header = self._column_headers.get(column_index, '')
        if not cur_header and value:
            # This is the first value for the column. Set as header.
            self._column_headers[column_index] = value
            return value
        return cur_header

    def _add_row_counts(self, row: list[str]) -> None:
        """Updates the column counts for a selected row.

        This method iterates through the columns of a selected row and updates the
        counts of the unique values in each column.

        Args:
            row: The row that has been selected for the sample.
        """
        # Update counts for each tracked column value in the row.
        for index in range(len(row)):
            # Skip columns not being tracked
            if not self._should_track_column(index):
                continue
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

    def select_row(self, row: list[str], sample_rate: float = -1) -> bool:
        """Determines whether a row should be added to the sample output.

        This method applies a set of rules to decide if a row should be
        selected. A row is selected if it contains a new unique value in any
        column, or if it is randomly selected based on the sampling rate.

        Args:
            row: The row to be considered for selection.
            sample_rate: The sampling rate to use for random selection. If not
              provided, the configured sampling rate is used.

        Returns:
            True if the row should be selected, False otherwise.
        """
        max_rows = self._config.get('sampler_output_rows')
        if max_rows > 0 and self._selected_rows >= max_rows:
            # Too many rows already selected. Drop it.
            return False
        max_count = self._config.get('sampler_rows_per_key', 3)
        max_uniques_per_col = self._config.get('sampler_uniques_per_column', 10)
        for index in range(len(row)):
            # Skip columns not in unique_columns list
            if not self._should_track_column(index):
                continue
            value = row[index]
            value_count = self._get_column_count(index, value)
            if value_count == 0 or value_count < max_count:
                # This is a new value for this column.
                col_counts = self._column_counts.get(index, {})
                if len(col_counts) < max_uniques_per_col:
                    # Column has few unique values. Select this row for column.
                    self._counters.add_counter('sampler-selected-rows', 1)
                    self._counters.add_counter(
                        f'sampler-selected-column-{index}', 1)
                    return True
        # No new unique value for the row.
        # Check random sampler.
        if sample_rate < 0:
            sample_rate = self._config.get('sampler_rate')
        if random.random() <= sample_rate:
            self._counters.add_counter('sampler-sampled-rows', 1)
            return True
        return False

    def sample_csv_file(self, input_file: str, output_file: str = '') -> str:
        """Emits a sample of rows from an input file into an output file.

        This method reads a CSV file, selects a sample of rows based on the
        configured criteria, and writes the selected rows to an output file.

        When sampler_unique_columns is configured, the method processes all
        header rows (up to header_rows config) to locate the specified column
        names. If any requested columns are not found within the header rows,
        a ValueError is raised.

        Args:
            input_file: The path to the input CSV file.
            output_file: The path to the output CSV file. If not provided, a
              temporary file will be created.

        Returns:
            The path to the output file with the sampled rows.

        Raises:
            ValueError: If sampler_unique_columns is configured and any of the
              specified column names are not found within the first header_rows
              rows of the input file.

        Usage:
            sampler = DataSampler()
            sampler.sample_csv_file('input.csv', 'output.csv')
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
                        self._counters.add_counter('sampler-input-row', 1)
                        row_index += 1
                        # Process and write header rows from the first input file.
                        if row_index <= header_rows and input_index == 0:
                            self._process_header_row(row)
                            csv_writer.writerow(row)
                            self._counters.add_counter('sampler-header-rows', 1)
                            # After processing all header rows, validate that all
                            # requested unique columns were found
                            if row_index == header_rows and self._unique_column_names:
                                found = set(self._unique_column_indices.keys())
                                missing = set(self._unique_column_names) - found
                                if missing:
                                    logging.error(
                                        'Failed to map unique columns %s within %d header '
                                        'row(s). Found: %s. Missing: %s. Increase '
                                        'header_rows or verify column names.',
                                        self._unique_column_names, header_rows,
                                        found or 'none', missing)
                                    raise ValueError(
                                        f'Missing unique columns in headers: {missing}'
                                    )
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
                    config: dict = None) -> str:
    """Samples a CSV file and returns the path to the sampled file.

    This function provides a convenient way to sample a CSV file with a single
    function call. It creates a DataSampler instance and uses it to perform the
    sampling.

    Args:
        input_file: The path to the input CSV file.
        output_file: The path to the output CSV file. If not provided, a
          temporary file will be created.
        config: A dictionary of configuration parameters for sampling. The
          supported parameters are:
          - sampler_output_rows: The maximum number of rows to include in the
            sample.
          - sampler_rate: The sampling rate to use for random selection.
          - header_rows: The number of header rows to copy from the input file
            and search for sampler_unique_columns. Increase this if column names
            appear in later header rows (e.g., after a title row).
          - sampler_rows_per_key: The number of rows to select for each unique
            key.
          - sampler_column_regex: A regular expression to filter column values.
          - sampler_unique_columns: A comma-separated list of column names to
            use for selecting unique rows. Column names must appear within the
            first header_rows rows or ValueError will be raised.
          - input_delimiter: The delimiter used in the input file.
          - output_delimiter: The delimiter to use in the output file.
          - input_encoding: The encoding of the input file.

    Returns:
        The path to the output file with the sampled rows.

    Raises:
        ValueError: If sampler_unique_columns is configured and any of the
          specified column names are not found within the first header_rows
          rows of the input file.

    Usage:
        # Basic usage with default settings
        sample_csv_file('input.csv', 'output.csv')

        # Sample with a specific number of output rows and a sampling rate
        config = {
            'sampler_output_rows': 50,
            'sampler_rate': 0.1,
        }
        sample_csv_file('input.csv', 'output.csv', config)

        # Sample a file with a semicolon delimiter and two header rows
        config = {
            'input_delimiter': ';',
            'header_rows': 2,
        }
        sample_csv_file('input.csv', 'output.csv', config)
    """
    if config is None:
        config = {}
    data_sampler = DataSampler(config_dict=config)
    return data_sampler.sample_csv_file(input_file, output_file)


def get_default_config() -> dict:
    """Returns a dictionary of default configuration parameter values.

    This function retrieves the default values of the configuration parameters
    from the command-line flags.

    Returns:
        A dictionary of default configuration parameter values.
    """
    # Hardcoded defaults for when flags are not defined (e.g. used as library)
    configs = {
        'sampler_rate': -1,
        'sampler_input': '',
        'sampler_output': '',
        'sampler_output_rows': 100,
        'header_rows': 1,
        'sampler_rows_per_key': 5,
        'sampler_column_regex': r'^[0-9]{4}$|[a-zA-Z-]',
        'sampler_unique_columns': '',
        'input_delimiter': ',',
        'output_delimiter': None,
        'input_encoding': 'UTF8',
    }
    # Use default values of flags if defined and parsed
    try:
        if not flags.FLAGS.is_parsed():
            flags.FLAGS.mark_as_parsed()

        # Update with flag values if they exist
        flag_map = {
            'sampler_rate': 'sampler_rate',
            'sampler_input': 'sampler_input',
            'sampler_output': 'sampler_output',
            'sampler_output_rows': 'sampler_output_rows',
            'header_rows': 'sampler_header_rows',
            'sampler_rows_per_key': 'sampler_rows_per_key',
            'sampler_column_regex': 'sampler_column_regex',
            'sampler_unique_columns': 'sampler_unique_columns',
            'input_delimiter': 'sampler_input_delimiter',
            'output_delimiter': 'sampler_output_delimiter',
            'input_encoding': 'sampler_input_encoding',
        }
        for config_key, flag_name in flag_map.items():
            if hasattr(flags.FLAGS, flag_name):
                configs[config_key] = getattr(flags.FLAGS, flag_name)
    except flags.UnparsedFlagAccessError:
        pass

    return configs


def main(_):
    sample_csv_file(flags.FLAGS.sampler_input, flags.FLAGS.sampler_output)


if __name__ == '__main__':
    _define_flags()
    app.run(main)
