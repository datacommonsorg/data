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
"""Utility classes and functions to shard files using `ShardedFileDictIO`.

Supports sharding of CSV, TSV, MCF, Apache Avro, and JSON/JSONL files.

To shard a file using the content of a column or a property, run:
  python file_sharder.py --shard_input=<input-file> --shard_output=<prefix>@<NN>

To emit a record to a shard based on a specific column or property, set `shard_key`:
  --shard_key="<column-name>"
If no `shard_key` is set, it uses the record's `dcid` (or `Node`) if set, or the
fingerprint of the entire record.

To shard by a combination of columns, set `shard_key` to a format string:
  --shard_key="{observationDate}{observationAbout}{variableMeasured}"

To generate a specified number of output shards, use the `@N` suffix:
  --shard_output=output@10.csv  # generates 'output-0000N-of-00010.csv'

To dynamically determine the shard count with a target number of records per shard:
  --records_per_shard=<count> --shard_output=<prefix>*.csv

Example usage within a Python script:
  import file_sharder

  shard_configs = {
      'shard_key': 'observationAbout',
      'shard_count': 100,
  }
  file_sharder.shard_file(input_file, output_path, shard_configs)
"""

import os
import sys

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(_SCRIPT_DIR), 'tools', 'statvar_importer'))

from counters import Counters
from file_dict_io import (
    FileDictIO,
    ShardedFileDictIO,
    get_default_shard_config as get_base_shard_config,
    is_csv_file,
    open_dict_file,
    str_to_int_hash,
)

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


def get_default_shard_config() -> dict:
    """Returns the default config for sharding based on command-line flags."""
    if not _FLAGS.is_parsed():
        _FLAGS.mark_as_parsed()
    config = get_base_shard_config()
    config.update({
        'shard_key': _FLAGS.shard_key,
        'shard_key_prefix_length': _FLAGS.shard_key_prefix_length,
        'shard_count': _FLAGS.shard_count,
        'records_per_shard': _FLAGS.records_per_shard,
        'shard_skip_duplicates': _FLAGS.shard_skip_duplicates,
        'shard_input_records': _FLAGS.shard_input_records,
        'shard_headers': _FLAGS.shard_headers,
        'shard_sample_rate': _FLAGS.shard_sample_rate,
    })
    return config


class FileSharder:
    """Shards input dictionary files into output shards using `ShardedFileDictIO`.

    Supports CSV, TSV, MCF, Apache Avro, and JSON/JSONL files.

    Example:
      from file_sharder import FileSharder

      sharder = FileSharder('input.csv', 'output@10.csv', {'shard_key': 'dcid'})
      sharder.process()
    """

    def __init__(self,
                 input_files: str | list,
                 output_path: str,
                 config: dict = None,
                 counters: Counters = None):
        """Initializes a `FileSharder` backed by `ShardedFileDictIO`.

        Args:
          input_files: Input file path, sharded pattern, or list of file paths.
          output_path: Output shard file pattern (e.g. `'output@10.csv'`).
          config: Optional dictionary of sharding configuration parameters.
          counters: Optional `Counters` object to track sharding statistics.
        """
        self._config = get_default_shard_config()
        if config:
            self._config.update(config)
        self._counters = counters if counters is not None else Counters()
        self._output_path = output_path

        # Initialize reader via ShardedFileDictIO (handles single or sharded inputs).
        self._reader = ShardedFileDictIO(
            input_files,
            mode='r',
            counters=self._counters,
        )
        self._input_files = self._reader.input_files()
        self._headers = self._config.get('shard_headers') or self._reader.headers()
        self._shard_key = self._config.get('shard_key') or self._reader._shard_key

        writer_config = dict(self._config)
        if self._shard_key:
            writer_config['shard_key'] = self._shard_key
        writer_config['estimated_num_rows'] = self.get_input_records_estimate()

        self._writer = ShardedFileDictIO(
            self._output_path,
            mode='w',
            headers=self._headers,
            config=writer_config,
            counters=self._counters,
        )

    def __del__(self):
        self.close()

    def close(self):
        """Closes the underlying `ShardedFileDictIO` reader and writer."""
        if getattr(self, '_reader', None) is not None:
            self._reader.close()
        if getattr(self, '_writer', None) is not None:
            self._writer.close()

    def get_next_record(self) -> dict:
        """Returns the next record from the input `ShardedFileDictIO` reader."""
        record = self._reader.next()
        if record and not self._headers:
            self._headers = [
                prop for prop in record.keys() if not str(prop).startswith('#')
            ]
            self._writer.set_headers(self._headers)
        return record

    def get_output_shard_filename(self, index: int) -> str:
        """Returns the output shard filename for shard `index`."""
        return self._writer.get_output_shard_filename(index)

    def get_key_for_record(self, record: dict) -> str:
        """Returns the extracted shard key for `record`."""
        return self._writer.get_key_for_record(record)

    def get_shard_for_key(self, key: str) -> int | str:
        """Returns the shard index for `key`."""
        return self._writer.get_shard_for_key(key)

    def get_shard_file_handle(self, index: int) -> FileDictIO:
        """Returns the `FileDictIO` writer handle for shard `index`."""
        return self._writer.get_shard_file_handle(index)

    def is_duplicate_record(self, record: dict) -> bool:
        """Returns True if `record` is a duplicate."""
        return self._writer.is_duplicate_record(record)

    def should_sample_key(self, key: str) -> bool:
        """Returns True if `key` is selected by the configured sample rate."""
        return self._writer.should_sample_key(key)

    def get_input_records_estimate(self) -> int:
        """Returns the estimated number of input records."""
        if not self._input_files:
            return 0
        if is_csv_file(self._input_files[0]):
            return self._reader._estimated_num_rows
        record_size = len(self._headers) if self._headers else 1
        return self._reader._estimated_num_rows / max(1, record_size)

    def process(self):
        """Reads all records from the input files and writes them to output shards."""
        record = self.get_next_record()
        if record is None:
            logging.error(f'No files to process for {self._input_files}')
            self.close()
            return

        if not self._writer._shard_key and self._reader._shard_key:
            self._writer._shard_key = self._reader._shard_key

        self._counters.add_counter('total', self.get_input_records_estimate())
        while record is not None:
            self._counters.add_counter('processed', 1)
            self._writer.write_record(record)
            record = self.get_next_record()

        self.close()


def shard_file(input_file: str,
               output_path: str,
               config: dict = None,
               counters: Counters = None):
    """Shards `input_file` into multiple output shard files at `output_path`.

    Args:
      input_file: Path or pattern to the input file(s) to be sharded.
      output_path: Path pattern for the output shard files (e.g. `'output@10.csv'`).
      config: Optional dictionary of config parameters for sharding.
      counters: Optional `Counters` object to track stats.
    """
    file_sharder = FileSharder(input_file, output_path, config, counters)
    file_sharder.process()


def main(_):
    if not _FLAGS.shard_input:
        logging.fatal('Specify files to be sharded with --shard_input')
    shard_file(_FLAGS.shard_input, _FLAGS.shard_output)


if __name__ == '__main__':
    app.run(main)
