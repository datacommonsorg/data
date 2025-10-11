# Copyright 2025 Google LLC
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
"""Utility classes and functions to shard files.

Supports sharding of CSV of MCF files.

To shard a CSV or MCF file using the content of a column or a property,
run the following command:
  python file_sharder.py --shard_input=<input-file> --shard_output=<prefix>@<NN>

To emit a record to a shard based on a specific column or property, set the shard_key:
      --shard_key="<column-name>"
If no shard_key is set, it uses the records, dcid if set or the fingerprint
of the entire record.

To shard by a combination of columns, set the shard_key to the list of columns,
for example, to shard a CSV file with SVObs such that each observation goes
dtereministically to a specific shard, set the shard_key with the columns:
  --shard_key="{observationDate}{observationAbout}{variableMeasured}"

To generate a specified number of output shards, use the '@N' suffix for the output file.
  --shard_output=output@10.csv generates files of the form: 'output-0000N-of-00010.csv'

To dynamically determine the shard count with a limited number of records per shard,
set the records_per_shard flasg with a wild card in the output:
  --records_per_shard=<count> --shard_output=<prefix>*.csv
This estimates the number of shards based on the first record size and the input file size.
Output shards can have more or less records than count.
The shard for a record is still determined based on the shard_key.


To use within a python scriptC:
    import file_sharder

    shard_configs = {
      'shard_key': 'observationAbout',
      'shard_count': 100,
    }
    file_sharder.shard_file(input_file, output_path, shard_configs)

"""

import csv
import hashlib
import math
import os
import sys

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(_SCRIPT_DIR), "tools", "statvar_importer"))

import file_util
import mcf_file_util
from counters import Counters
from file_dict_io import FileDictIO, open_dict_file, is_csv_file

# Defaults
_DEFAULT_ROWS_PER_SHARD = 100000
_DEFAULT_SHARD_FILENAME = 'shard-{index:05}-of-{shard_count:05d}'

_FLAGS = flags.FLAGS

flags.DEFINE_string('shard_input', '', 'Input files to be sharded')
flags.DEFINE_string('shard_output', '', 'Output file pattern for sharded file')
flags.DEFINE_string('shard_key', '', 'Key or column to shard an input record')
flags.DEFINE_integer('shard_key_prefix_length', 0,
                     'Length of key value to use for sharding')
flags.DEFINE_integer('shard_count', 0, 'Number of output shards to generate.')
flags.DEFINE_integer(
    'records_per_shard', _DEFAULT_ROWS_PER_SHARD,
    'Number of records per output shard if shard_count is not set.')
flags.DEFINE_bool('shard_skip_duplicates', False, 'Skip duplicate records.')
flags.DEFINE_integer('shard_input_records', sys.maxsize,
                     'Limit the number of input records to shard.')
flags.DEFINE_list('shard_headers', [], 'Header columns for sharded outputs.')
flags.DEFINE_float('shard_sample_rate', 1,
                   'Sampling rate for inputs in the range [0-1]')


def get_default_shard_config():
    """Returns the default config for sharding based on flags."""
    if not _FLAGS.is_parsed():
        _FLAGS.mark_as_parsed()
    return {
        'shard_key': _FLAGS.shard_key,
        'shard_key_prefix_length': _FLAGS.shard_key_prefix_length,
        'shard_count': _FLAGS.shard_count,
        'records_per_shard': _FLAGS.records_per_shard,
        'shard_skip_duplicates': _FLAGS.shard_skip_duplicates,
        'shard_input_records': _FLAGS.shard_input_records,
        'shard_headers': _FLAGS.shard_headers,
        'shard_sample_rate': _FLAGS.shard_sample_rate,
    }


def str_to_int_hash(input_string: str) -> int:
    """Returns a deterministic integer hash for a string."""
    encoded_string = input_string.encode('utf-8')

    # Calculate the SHA256 hash
    sha256_hash = hashlib.sha256(encoded_string).hexdigest()

    # Convert the hexadecimal hash to an integer
    # The '0x' prefix indicates a hexadecimal number
    integer_hash = int(sha256_hash[:16], 16)
    return integer_hash


class FileSharder:
    """Class to shard files.

    The input and output files can be CSV or MCF files with the extensions '.csv' or '.mcf'
    Usage:
      # Initialize a sharder with input and output files.
      file_sharder = FileSharder(input_files, output_files)
      # Shard the input files and generate the output files.
      file_shader.process()
    """

    def __init__(self,
                 input_files: list,
                 output_path: str,
                 config: dict = {},
                 counters: Counters = None):
        # Current input file handle for reads
        self._current_fp = None
        # Filehandles for output shards opened for writes keyed by shard index
        self._output_fp = {}

        self._config = get_default_shard_config()
        if config:
            self._config.update(config)
        self._counters = counters
        if counters is None:
            self._counters = Counters()

        # Replace '@' in sharded input filenames with wildcard
        input_files = input_files.replace('@', '*')
        # Get list of all input files
        self._input_files = file_util.file_get_matching(input_files)
        self._estimated_num_rows = file_util.file_estimate_num_rows(
            self._input_files)
        self._headers = self._config.get('shard_headers')
        # List of files to be read
        self._remaining_input_files = list(self._input_files)
        self._output_path = output_path
        self._shard_key = self._config.get('shard_key', None)
        self._output_pattern = ''
        # List of output shard filenames
        self._output_files = []
        # Fingerprint of records seen for duplicate checks.
        self._records_seen = set()
        # Sampling rate for inputs
        self.setup_sample_rate()

    def __del__(self):
        # Close all file handles for input and output.
        if self._current_fp:
            del self._current_fp
            self._current_fp = None
        for index, fp in self._output_fp.items():
            if fp is not None:
                del fp
            self._output_fp[index] = None
        self._output_fp = {}

    def open_next_input_file(self) -> bool:
        """Open the next input file.
        Returns False if there are no more files to read.
        """
        # Close the previous file, if any.
        if self._current_fp is not None:
            del self._current_fp
        self._current_fp = None

        if not self._remaining_input_files:
            return False

        # Open the next input file
        filename = self._remaining_input_files.pop(0)
        self._current_fp = open_dict_file(filename, 'r')
        headers = self._current_fp.headers()
        if not self._headers:
            # Get the csv headers for the first file.
            self._headers = headers
        elif headers and set(self._headers) != set(headers):
            logging.error(
                f'Found different headers for file: {filename}: expected: {self._headers}, got: {headers}'
            )
        self._counters.add_counter('shard-input-files', 1)

        # Prepare shard key
        # Use 'dcid' or the first columns as the shard key if none set.
        if self._shard_key is None:
            if 'dcid' in self._headers:
                self._shard_key = 'dcid'
            elif 'Node' in self._headers:
                self._shard_key = 'Node'
            elif self._headers:
                self._shard_key = self._headers[0]

        return True

    def get_next_record(self) -> dict:
        """Returns the next input record from input files as a dictionary of property:values.
        Reads the currently open file or moves to the next file if the current file is completed.
        """
        record = None
        if self._current_fp is None:
            self.open_next_input_file()
        while self._current_fp is not None:
            record = self._current_fp.next()
            if record is not None:
                # Got a record from the current file. Use it.
                self._counters.add_counter('shard-input-records', 1)
                break
            # No more records in the current file. Open the next input file.
            if not self.open_next_input_file():
                # No more files to read.
                break
        if record and not self._headers:
            # Set headers based on first record for MCF input.
            self._headers = [
                prop for prop in record.keys() if not prop.startswith('#')
            ]
        return record

    def get_output_shard_filename(self, index: int) -> str:
        """Returns the shard output filename for the shard with given index."""
        output_pattern = self._output_pattern
        # Generate the output file pattern if not set already.
        if not output_pattern:
            output_pattern = self._config.get('shard_output_path', '')
        if not output_pattern:
            # Get the output file pattern from the input file.
            output_pattern = self._input_files[0]
            suffix = '.csv'
            if not is_csv_file(output_pattern) and not is_csv_file(
                    self._input_files[0]):
                suffix = '.mcf'
            if '.' in output_pattern:
                output_pattern, suffix = output_pattern.split('.', 1)
            if not output_pattern:
                output_pattern = 'shard'
            output_pattern = output_pattern + '-{index:05d}-of-{shard_count:05d}' + suffix
            self._output_pattern = output_pattern

        return self._output_pattern.format(
            **{
                'index': index,
                self._shard_key: str(index),
                'shard_count': self._shard_count
            })

    def _prepare_output_shards(self):
        """Open output shard files for writing."""
        output_pattern = self._output_path
        self._shard_count = 0
        if '@' in output_pattern:
            # Replace @ with placeholder for index
            output_pattern, shard_count = output_pattern.split('@', 1)
            suffix = ''
            if '.' in shard_count:
                shard_count, suffix = shard_count.split('.', 1)
                suffix = '.' + suffix
            shard_count = int(shard_count)
            output_pattern += '-{index:05d}-of-' + f'{shard_count:05d}' + suffix
            self._shard_count = shard_count

        shard_count = self._shard_count
        if not shard_count:
            shard_count = self._config.get('shard_count', 0)
            if not shard_count:
                # Estimate the number of shards by shard size
                records_per_shard = self._config.get('records_per_shard', 0)
                if records_per_shard <= 0:
                    records_per_shard = _DEFAULT_ROWS_PER_SHARD
                shard_count = math.ceil(self._estimated_num_rows /
                                        records_per_shard)
            self._shard_count = shard_count

        if '*' in output_pattern:
            # Replace '*' with the patttern NNNNN-of-MMMMM
            output_pattern, suffix = output_pattern.split('*', 1)
            output_pattern += '{index:05d}-of-' + f'{shard_count:05d}' + suffix

        self._output_pattern = output_pattern
        if self._shard_key and '{' + self._shard_key + '}' in self._output_pattern:
            # Output file is named by shard column. Don't shard by count.
            self._shard_count = 0

        # Opening output shards
        if self._shard_count:
            for index in range(shard_count):
                self.get_shard_file_handle(index)

    def get_key_for_record(self, record) -> str:
        """Returns the shard key for the record."""
        key = None
        if self._shard_key:
            if '{' in self._shard_key:
                # Key is a format statement.
                try:
                    key = self._shard_key.format(**record)
                except KeyError:
                    logging.debug(
                        f'Failed to get key: {self._shard_key} for record: {record} in file {self._current_fp.filename()}'
                    )
                    key = ''
            elif self._shard_key in record:
                key = record.get(self._shard_key)
        if key is None:
            # Shard by the record fingerprint
            key = mcf_file_util.node_dict_to_text(record)

        prefix_len = self._config.get('shard_key_prefix_length', 0)
        if prefix_len > 0:
            key = key[:prefix_len]
        return key

    def get_shard_for_key(self, key: str) -> int:
        """Returns the shard index for the record."""
        if not key:
            key = ''
        if self._shard_count:
            key = str_to_int_hash(key) % self._shard_count
        return key

    def get_shard_file_handle(self, index: int) -> FileDictIO:
        """Returns the file handle for the output shard.
        Creates an output file and opens it for writes if needed.
        """
        if index not in self._output_fp:
            # Open a new file handle for the shard index.
            output_file = self.get_output_shard_filename(index)
            self._output_fp[index] = open_dict_file(output_file, 'w',
                                                    self._headers)
            self._output_files.append(output_file)
            self._counters.add_counter('shard-output-files', 1)
        return self._output_fp[index]

    def get_input_records_estimate(self) -> int:
        """Returns the estimated number of input records."""
        # For CSV inputs, return number of rows.
        if is_csv_file(self._input_files[0]):
            return self._estimated_num_rows
        # For MCF inputs, estimate records assuming one row per header
        record_size = 1
        if self._headers:
            record_size = len(self._headers)
        return self._estimated_num_rows / record_size

    def process(self):
        """Shard all the records in the input files into output files."""
        # Get the first input record and setup outputs based on that
        record = self.get_next_record()
        if record is None:
            logging.error(f'No files to process for {self._input_files}')
            return
        # Setuo output shards based on the first record.
        self._prepare_output_shards()
        logging.info(
            f'Sharding {self._input_files} using {self._shard_key} into {self._output_pattern} shards'
        )

        # Read each record from input files and write to an output shard.
        skip_duplicates = self._config.get('shard_skip_duplicates', False)
        num_input_records = 0
        max_input_records = self._config.get('shard_input_records', sys.maxsize)
        num_output_records = 0
        self._counters.add_counter('total', self.get_input_records_estimate())
        while record is not None:
            self._counters.add_counter('processed', 1)
            num_input_records += 1
            write_record = True
            if num_input_records > max_input_records:
                logging.info(f'Completed sharding {num_input_records} records.')
                break
            if skip_duplicates and self.is_duplicate_record(record):
                self._counters.add_counter('shard-duplicate-dropped', 1)
                write_record = False

            # Got a valid input.
            # Check if it can be sampled.
            if write_record:
                key = self.get_key_for_record(record)
                if not self.should_sample_key(key):
                    self._counters.add_counter('shard-input-sample-dropped', 1)
                    write_record = False

            if write_record:
                # Write it to the corresponding output shard.
                shard_index = self.get_shard_for_key(key)
                output_fp = self.get_shard_file_handle(shard_index)
                output_fp.write_record(record)

                # Update counters
                self._counters.add_counter(f'shard-{shard_index}-outputs', 1)
                self._counters.add_counter('shard-output-records', 1)
                num_output_records += 1
            else:
                self._counters.add_counter('shard-dropped-records', 1)

            # Get the next input record
            record = self.get_next_record()

        logging.info(
            f'Sharded {num_input_records} records from {len(self._input_files)} files into {len(self._output_files)} shards with {num_output_records}'
        )

    def is_duplicate_record(self, record: dict) -> bool:
        """Returns True if the record is a duplicate.
        Keeps a hash of records seen with previous calls.
        """
        record_hash = hash(mcf_file_util.node_dict_to_text(record))
        if record_hash in self._records_seen:
            return True
        self._records_seen.add(record_hash)
        return False

    def setup_sample_rate(self):
        """Set sampling rate and sampling factor for modulo sampling on hash of key."""
        sample_factor = 1
        sample_rate = self._config.get('shard_sample_rate', 1)
        if sample_rate < 1.0:
            sample_rate_str = f'{sample_rate:.12f}'.strip('0')
            if '.' in sample_rate_str:
                sample_factor = pow(10, len(sample_rate_str.split('.')[1]))
                sample_rate = int(sample_rate * sample_factor)
            else:
                logging.fatal(f'invalid rate {sample_rate}')
        self._sample_rate = sample_rate
        self._sample_factor = sample_factor
        if sample_factor > 1:
            logging.info(
                f'Sampling {sample_rate} out of {sample_factor} records.')

    def should_sample_key(self, key: str) -> bool:
        """Returns True if the key is selected based on the sampling rate."""
        if self._sample_factor == 1:
            return True
        return (str_to_int_hash(key) % self._sample_factor) <= self._sample_rate


def shard_file(input_file: str,
               output_path: str,
               config: dict = {},
               counters: Counters = None):
    """Shards a file into multiple files.
    Args:
      input_file: Path to the input file to be sharded.
      output_path: Path pattern for the output files.
      config: Dictionary of config parameters for sharding.
        see get_default_shard_config() for all options96099573
      counters: Counters object to track stats.
    """
    file_sharder = FileSharder(input_file, output_path, config, counters)
    file_sharder.process()


def main(_):
    # logging.set_verbosity(2)
    if not _FLAGS.shard_input:
        logging.fatal(f'Specify files to be sharded with --shard_input')
    shard_file(_FLAGS.shard_input, _FLAGS.shard_output)


if __name__ == '__main__':
    app.run(main)
