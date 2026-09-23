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
"""Sharded file reader and writer (`ShardedFileDictIO`) for `file_dict_io`.

Supports reading and writing sharded files of any registered `FileDictIO`
format (CSV, TSV, MCF, Apache Avro, JSON, JSONL) with all sharding options from
`file_sharder.py`.

Example:
  from file_dict_io import open_dict_file

  with open_dict_file('output@3.avro', 'w', shard_key='id') as writer:
    writer.write([{'id': '11', 'val': 'a'}, {'id': '21', 'val': 'b'}])

  with open_dict_file('output@3.avro', 'r') as reader:
    for row in reader:
      print(row)
"""

import hashlib
from io import UnsupportedOperation
import json
import math
import os
import re
import sys
from absl import logging

from counters import Counters
from file_dict_io.avro_io import is_avro_file
from file_dict_io.base import FileDictIO
from file_dict_io.csv_io import is_csv_file
from file_dict_io.json_io import is_json_file
from file_dict_io.mcf_io import is_mcf_file
import file_util
import mcf_file_util

# Defaults matching file_sharder.py
_DEFAULT_ROWS_PER_SHARD = 100000
_DEFAULT_SHARD_FILENAME = 'shard-{index:05}-of-{shard_count:05d}'

_SHARD_CONFIG_KEYS = (
    'shard_key',
    'shard_key_prefix_length',
    'shard_count',
    'records_per_shard',
    'shard_skip_duplicates',
    'shard_input_records',
    'shard_headers',
    'shard_sample_rate',
    'shard_output_path',
    'estimated_num_rows',
)


def get_default_shard_config() -> dict:
    """Returns the default configuration dictionary for `ShardedFileDictIO`.

    Returns:
      A `dict` with default values for all sharding options.
    """
    return {
        'shard_key': '',
        'shard_key_prefix_length': 0,
        'shard_count': 0,
        'records_per_shard': _DEFAULT_ROWS_PER_SHARD,
        'shard_skip_duplicates': False,
        'shard_input_records': sys.maxsize,
        'shard_headers': [],
        'shard_sample_rate': 1.0,
        'shard_output_path': '',
        'estimated_num_rows': 0,
    }


def str_to_int_hash(input_string: str) -> int:
    """Returns a deterministic 64-bit integer hash for `input_string` using SHA-256.

    Args:
      input_string: The string key to hash.

    Returns:
      An unsigned integer derived from the first 16 hex digits of the SHA-256
      digest.
    """
    encoded_string = str(input_string).encode('utf-8')
    sha256_hash = hashlib.sha256(encoded_string).hexdigest()
    return int(sha256_hash[:16], 16)


def is_sharded_file(filename: str | list) -> bool:
    """Returns True if `filename` represents a sharded file pattern or file list.

    Detects:
      - `@<N>` shard count notation (e.g. `'output@10.csv'`, `'nodes@3.mcf'`)
      - `*` wildcard patterns (e.g. `'output*.avro'`, `'shard-*.csv'`)
      - `{...}` template placeholders (e.g. `'output-{country}.csv'`)
      - Comma-separated file lists or Python `list` of file paths.

    Example:
      from file_dict_io import is_sharded_file

      is_sharded_file('output@10.csv')   # Returns True
      is_sharded_file('output*.avro')    # Returns True
      is_sharded_file('single_file.csv') # Returns False

    Args:
      filename: File path, pattern string, or list of file paths.

    Returns:
      `True` if `filename` refers to sharded files; `False` otherwise.
    """
    if isinstance(filename, list):
        return True
    if not isinstance(filename, str):
        return False
    basename = os.path.basename(filename)
    if '@' in basename or '*' in filename or ',' in filename:
        return True
    if '{' in filename and '}' in filename:
        return True
    return False


@FileDictIO.register(priority=True)
class ShardedFileDictIO(FileDictIO):
    """Reads or writes sharded dictionary record files of any supported format.

    Supports CSV/TSV, MCF, Apache Avro, and JSON/JSONL shards using all
    sharding options from `file_sharder.py`:
      - `shard_key`: Column/property name (e.g. `'dcid'`, `'Node'`) or format
        string combining multiple columns (e.g. `'{observationDate}{observationAbout}'`).
        If omitted, defaults to `'dcid'`, `'Node'`, the first header column, or
        the full record fingerprint.
      - `shard_key_prefix_length`: Optional prefix length of the key value to
        use for hashing/routing.
      - `shard_count`: Number of output shards (can also be specified inline via
        `<prefix>@<N>.<ext>`, e.g. `'output@10.avro'`).
      - `records_per_shard`: Target records per shard when `shard_count` is
        estimated dynamically (e.g. with `'output*.csv'`).
      - `shard_skip_duplicates`: When `True`, drops duplicate records across
        shards.
      - `shard_input_records`: Maximum number of records to process.
      - `shard_headers`: Explicit list of column headers for output shards.
      - `shard_sample_rate`: Deterministic key-based sampling rate in `[0.0, 1.0]`.

    Example:
      from file_dict_io import ShardedFileDictIO

      # Write records into 3 Avro shards keyed by 'id':
      with ShardedFileDictIO('output@3.avro', mode='w', shard_key='id') as writer:
        writer.write([{'id': '11', 'val': 'a'}, {'id': '21', 'val': 'b'}])

      # Read all records back across all shards:
      with ShardedFileDictIO('output@3.avro', mode='r') as reader:
        for row in reader:
          print(row)
    """

    @classmethod
    def can_handle(cls, filename: str | list) -> bool:
        """Returns True if `filename` is a sharded file pattern or list."""
        return is_sharded_file(filename)

    def __init__(self,
                 filename: str | list,
                 mode: str = 'r',
                 headers: list = None,
                 encoding: str = None,
                 schema: dict = None,
                 config: dict = None,
                 counters: Counters = None,
                 **kwargs):
        """Initializes a `ShardedFileDictIO` reader or writer.

        Args:
          filename: Sharded file path pattern (e.g. `'output@10.csv'`,
            `'output*.avro'`, `'output-{id}.mcf'`) or list of input files.
          mode: File open mode ('r' for read, 'w' for write).
          headers: Optional list of column names or MCF header comments.
          encoding: Optional character encoding for text-based formats.
          schema: Optional Avro schema dictionary for `.avro` shards.
          config: Optional dictionary of sharding options (`shard_key`,
            `shard_key_prefix_length`, `shard_count`, `records_per_shard`,
            `shard_skip_duplicates`, `shard_input_records`, `shard_headers`,
            `shard_sample_rate`). Any of these may also be passed directly via
            `**kwargs`.
          counters: Optional `Counters` instance to track sharding metrics.
          **kwargs: Sharding configuration options or format-specific arguments.
        """
        self._config = get_default_shard_config()
        if config:
            self._config.update(config)
        for key in _SHARD_CONFIG_KEYS:
            if key in kwargs and kwargs[key] is not None:
                self._config[key] = kwargs.pop(key)

        effective_headers = headers if headers is not None else self._config.get(
            'shard_headers')
        super().__init__(
            filename if isinstance(filename, str) else ','.join(filename),
            mode=mode,
            headers=effective_headers,
            encoding=encoding,
            **kwargs,
        )
        self._raw_filename = filename
        self._schema = dict(schema) if schema else None
        self._extra_kwargs = kwargs
        self._counters = counters if counters is not None else Counters()

        self._current_fp: FileDictIO | None = None
        self._output_fp: dict[int | str, FileDictIO] = {}
        self._input_files: list[str] = []
        self._remaining_input_files: list[str] = []
        self._output_files: list[str] = []
        self._output_pattern: str = ''
        self._shard_key: str | None = self._config.get('shard_key') or None
        self._shard_count: int = int(self._config.get('shard_count') or 0)
        self._estimated_num_rows: int = int(
            self._config.get('estimated_num_rows') or 0)
        self._records_seen: set[int] = set()
        self._num_processed_records: int = 0
        self._shards_prepared: bool = False

        self.setup_sample_rate()
        self.open()

    def _create_single_file_io(self,
                               shard_filename: str,
                               mode: str,
                               headers: list = None) -> FileDictIO:
        """Instantiates the non-sharded `FileDictIO` handler for `shard_filename`."""
        for handler_cls in FileDictIO._registry:
            if handler_cls is ShardedFileDictIO:
                continue
            if handler_cls.can_handle(shard_filename):
                kwargs = dict(self._extra_kwargs)
                if self._schema is not None:
                    kwargs['schema'] = self._schema
                return handler_cls(shard_filename,
                                   mode=mode,
                                   headers=headers,
                                   encoding=self._encoding,
                                   **kwargs)
        if FileDictIO._default_handler is not None:
            return FileDictIO._default_handler(shard_filename,
                                               mode=mode,
                                               headers=headers,
                                               encoding=self._encoding,
                                               **self._extra_kwargs)
        raise ValueError(
            f'No FileDictIO handler found for shard file: {shard_filename}')

    def _resolve_input_files(self, filename: str | list) -> list[str]:
        """Expands `@`, `*`, or list patterns into a sorted list of matching files."""
        if isinstance(filename, list):
            patterns = filename
        else:
            patterns = [filename]

        matched_files = []
        for pattern in patterns:
            candidate_globs = [
                re.sub(r'@\d*', '*', pattern),
                pattern.replace('@', '*'),
            ]
            if '@' in pattern:
                prefix, shard_spec = pattern.split('@', 1)
                base, ext = os.path.splitext(prefix)
                if ext:
                    # Also match 'shards-*-of-*.mcf' when given 'shards.mcf@10'
                    candidate_globs.append(f'{base}-*-of-*{ext}')
                elif '.' in shard_spec:
                    _, spec_ext = shard_spec.split('.', 1)
                    # Also match 'shards.mcf-*-of-*' when given 'shards@10.mcf'
                    candidate_globs.append(f'{prefix}.{spec_ext}-*-of-*')

            for glob_pat in candidate_globs:
                matches = sorted(file_util.file_get_matching(glob_pat))
                if matches:
                    for match in matches:
                        if match not in matched_files:
                            matched_files.append(match)
                    break
        return matched_files

    def open(self):
        """Initializes input shard files (read mode) or output shard pattern (write mode)."""
        self._record_index = 0
        self._num_processed_records = 0
        self._header_written = False

        if self.is_read_mode():
            self._input_files = self._resolve_input_files(self._raw_filename)
            self._remaining_input_files = list(self._input_files)
            if (not self._estimated_num_rows and self._input_files and
                    not is_avro_file(self._input_files[0])):
                try:
                    self._estimated_num_rows = file_util.file_estimate_num_rows(
                        self._input_files)
                except UnicodeDecodeError:
                    self._estimated_num_rows = 0
            self.open_next_input_file()
        else:
            self._parse_output_pattern()
            # Pre-open output shards immediately if headers/schema are already set
            # or if the format does not require column headers (MCF / JSON).
            if self._can_prepare_shards_now():
                self._prepare_output_shards()

    def _can_prepare_shards_now(self) -> bool:
        """Returns True if output shards can be opened before the first record."""
        if self._headers or self._schema:
            return True
        if is_mcf_file(self._filename) or is_json_file(self._filename):
            return True
        return False

    def _parse_output_pattern(self):
        """Parses `@<N>`, `*`, or `{column}` in `self._filename` to determine `_output_pattern` and `_shard_count`."""
        output_pattern = self._config.get('shard_output_path') or self._filename
        shard_count = self._shard_count

        if '@' in output_pattern:
            prefix, shard_spec = output_pattern.split('@', 1)
            suffix = ''
            if '.' in shard_spec:
                shard_count_str, suffix_part = shard_spec.split('.', 1)
                suffix = '.' + suffix_part
            else:
                shard_count_str = shard_spec
            if shard_count_str.isdigit():
                shard_count = int(shard_count_str)
            if not shard_count:
                shard_count = self._estimate_shard_count()
            output_pattern = (
                f'{prefix}-{{index:05d}}-of-{shard_count:05d}{suffix}')
            self._shard_count = shard_count

        if not self._shard_count:
            self._shard_count = self._estimate_shard_count()
            shard_count = self._shard_count

        if '*' in output_pattern:
            prefix, suffix = output_pattern.split('*', 1)
            output_pattern = f'{prefix}{{index:05d}}-of-{shard_count:05d}{suffix}'

        self._output_pattern = output_pattern
        if self._shard_key and '{' + self._shard_key + '}' in self._output_pattern:
            # Output file is named dynamically by shard column value.
            self._shard_count = 0

    def _estimate_shard_count(self) -> int:
        """Determines the number of shards from config or `records_per_shard`."""
        shard_count = int(self._config.get('shard_count') or 0)
        if shard_count > 0:
            return shard_count
        records_per_shard = int(
            self._config.get('records_per_shard') or _DEFAULT_ROWS_PER_SHARD)
        if records_per_shard <= 0:
            records_per_shard = _DEFAULT_ROWS_PER_SHARD
        if self._estimated_num_rows > 0:
            return max(1, math.ceil(self._estimated_num_rows / records_per_shard))
        return 1

    def _prepare_output_shards(self):
        """Opens all output shard handles when `shard_count > 0`."""
        if self._shards_prepared:
            return
        self._parse_output_shards_key_check()
        self._shards_prepared = True
        if self._shard_count > 0:
            for index in range(self._shard_count):
                self.get_shard_file_handle(index)

    def _parse_output_shards_key_check(self):
        """Updates `_shard_count` if `_shard_key` is a template variable in `_output_pattern`."""
        if self._shard_key and '{' + self._shard_key + '}' in self._output_pattern:
            self._shard_count = 0

    def get_output_shard_filename(self, index: int | str) -> str:
        """Returns the resolved output filename for the shard at `index`.

        Args:
          index: Zero-based integer shard index or string shard key value.

        Returns:
          Formatted file path for the target shard.
        """
        output_pattern = self._output_pattern
        if not output_pattern:
            self._parse_output_pattern()
            output_pattern = self._output_pattern

        if '{' not in output_pattern:
            base, suffix = os.path.splitext(output_pattern)
            if not suffix:
                suffix = '.csv' if is_csv_file(output_pattern) else '.mcf'
            if not base:
                base = 'shard'
            output_pattern = (
                f'{base}-{{index:05d}}-of-{{shard_count:05d}}{suffix}')
            self._output_pattern = output_pattern

        format_vars = {
            'index': index,
            'shard_count': self._shard_count,
        }
        if self._shard_key:
            format_vars[self._shard_key] = str(index)
        return self._output_pattern.format(**format_vars)

    def get_shard_file_handle(self, index: int | str) -> FileDictIO:
        """Returns (and lazily opens) the `FileDictIO` writer for shard `index`.

        Args:
          index: Shard index or column key value.

        Returns:
          The open `FileDictIO` writer instance for that shard.
        """
        if index not in self._output_fp:
            output_file = self.get_output_shard_filename(index)
            self._output_fp[index] = self._create_single_file_io(
                output_file, mode='w', headers=self._headers)
            self._output_files.append(output_file)
            self._counters.add_counter('shard-output-files', 1)
        return self._output_fp[index]

    def output_files(self) -> list[str]:
        """Returns the list of output shard file paths opened by this instance."""
        return list(self._output_files)

    def input_files(self) -> list[str]:
        """Returns the list of input shard file paths matched by this instance."""
        return list(self._input_files)

    def _infer_default_shard_key(self, candidate_keys: list[str]):
        """Infers `self._shard_key` from `dcid`, `Node`, or the first available key."""
        if self._shard_key is None and candidate_keys:
            if 'dcid' in candidate_keys:
                self._shard_key = 'dcid'
            elif 'Node' in candidate_keys:
                self._shard_key = 'Node'
            else:
                self._shard_key = candidate_keys[0]

    def open_next_input_file(self) -> bool:
        """Closes the current input shard and opens the next shard in `_remaining_input_files`.

        Returns:
          `True` if a new input shard was opened; `False` if no shards remain.
        """
        if self._current_fp is not None:
            self._current_fp.close()
            self._current_fp = None

        if not self._remaining_input_files:
            return False

        filename = self._remaining_input_files.pop(0)
        self._current_fp = self._create_single_file_io(filename, mode='r')
        headers = self._current_fp.headers()
        if not self._headers and headers:
            self._headers = list(headers)
        elif headers and self._headers and set(self._headers) != set(headers):
            logging.error(
                f'Found different headers for file: {filename}: expected: {self._headers}, got: {headers}'
            )
        self._counters.add_counter('shard-input-files', 1)
        self._infer_default_shard_key(self._headers)
        return True

    def get_key_for_record(self, record: dict) -> str:
        """Extracts the shard key string for `record` according to `shard_key` and `shard_key_prefix_length`.

        Args:
          record: Dictionary record being read or written.

        Returns:
          The string key used to hash and route `record` to a shard.
        """
        if self._shard_key is None:
            self._infer_default_shard_key(
                self._headers or [
                    k for k in record.keys() if not str(k).startswith('#')
                ])

        key = None
        if self._shard_key:
            if '{' in self._shard_key:
                try:
                    key = self._shard_key.format(**record)
                except KeyError:
                    key = ''
            elif self._shard_key in record:
                val = record.get(self._shard_key)
                key = '' if val is None else str(val)
        if key is None:
            key = self._record_to_canonical_str(record)

        prefix_len = int(self._config.get('shard_key_prefix_length') or 0)
        if prefix_len > 0:
            key = key[:prefix_len]
        return key

    def get_shard_for_key(self, key: str) -> int | str:
        """Returns the target shard index (or string key if uncounted) for `key`."""
        if not key:
            key = ''
        if self._shard_count:
            return str_to_int_hash(key) % self._shard_count
        return key

    def _record_to_canonical_str(self, record: dict) -> str:
        """Serializes `record` deterministically for fingerprinting and duplicate detection."""
        try:
            return mcf_file_util.node_dict_to_text(record)
        except Exception:
            return json.dumps(record, sort_keys=True, default=str)

    def is_duplicate_record(self, record: dict) -> bool:
        """Returns True if `record` has already been seen by this instance."""
        record_hash = hash(self._record_to_canonical_str(record))
        if record_hash in self._records_seen:
            return True
        self._records_seen.add(record_hash)
        return False

    def setup_sample_rate(self):
        """Configures modulo hash sampling parameters from `shard_sample_rate`."""
        sample_factor = 1
        sample_rate = float(self._config.get('shard_sample_rate', 1.0))
        if sample_rate < 1.0:
            sample_rate_str = f'{sample_rate:.12f}'.strip('0')
            if '.' in sample_rate_str:
                sample_factor = pow(10, len(sample_rate_str.split('.')[1]))
                sample_rate = int(sample_rate * sample_factor)
            else:
                logging.fatal(f'Invalid shard_sample_rate: {sample_rate}')
        self._sample_rate = sample_rate
        self._sample_factor = sample_factor

    def should_sample_key(self, key: str) -> bool:
        """Returns True if `key` passes the configured `shard_sample_rate` filter."""
        if self._sample_factor == 1:
            return True
        return (str_to_int_hash(key) % self._sample_factor) <= self._sample_rate

    def _should_accept_record(self, record: dict) -> tuple[bool, str]:
        """Applies `shard_input_records`, `shard_skip_duplicates`, and `shard_sample_rate` filters."""
        self._num_processed_records += 1
        max_records = int(
            self._config.get('shard_input_records') or sys.maxsize)
        if self._num_processed_records > max_records:
            return False, ''

        if self._config.get('shard_skip_duplicates',
                            False) and self.is_duplicate_record(record):
            self._counters.add_counter('shard-duplicate-dropped', 1)
            self._counters.add_counter('shard-dropped-records', 1)
            return False, ''

        key = self.get_key_for_record(record)
        if not self.should_sample_key(key):
            self._counters.add_counter('shard-input-sample-dropped', 1)
            self._counters.add_counter('shard-dropped-records', 1)
            return False, key

        return True, key

    def write_header(self):
        """Writes headers to all active output shards."""
        for shard_fp in self._output_fp.values():
            shard_fp.write_header()
        self._header_written = True

    def write_record(self, record: dict):
        """Routes and writes a single dictionary record to its target output shard.

        Applies duplicate filtering, sampling rate, and record limits configured
        on this `ShardedFileDictIO` instance.

        Args:
          record: Dictionary record to write.

        Returns:
          The return value of the target shard's `write_record`, or `None` if
          the record was filtered out by `shard_skip_duplicates`,
          `shard_sample_rate`, or `shard_input_records`.

        Raises:
          UnsupportedOperation: If opened in read mode.
        """
        if self.is_read_mode():
            raise UnsupportedOperation(
                f'Cannot write record to sharded file {self.filename()} opened in read mode'
            )

        if not self._headers:
            non_comment_keys = [
                k for k in record.keys() if not str(k).startswith('#')
            ]
            if non_comment_keys and not (is_mcf_file(self._filename) or
                                         is_json_file(self._filename)):
                self.set_headers(non_comment_keys)

        if not self._shards_prepared:
            self._prepare_output_shards()

        accepted, key = self._should_accept_record(record)
        if not accepted:
            return None

        shard_index = self.get_shard_for_key(key)
        output_fp = self.get_shard_file_handle(shard_index)
        result = output_fp.write_record(record)

        self._record_index += 1
        self._counters.add_counter(f'shard-{shard_index}-outputs', 1)
        self._counters.add_counter('shard-output-records', 1)
        return result

    def next(self) -> dict:
        """Reads and returns the next dictionary record across all input shards.

        Applies `shard_input_records`, `shard_skip_duplicates`, and
        `shard_sample_rate` if configured.

        Returns:
          A `dict` for the next record, or `None` when all input shards have
          been read or `shard_input_records` is reached.
        """
        if not self.is_read_mode():
            return None

        max_records = int(
            self._config.get('shard_input_records') or sys.maxsize)
        if self._num_processed_records >= max_records:
            return None

        while self._current_fp is not None:
            record = self._current_fp.next()
            if record is not None:
                self._counters.add_counter('shard-input-records', 1)
                if not self._headers:
                    self._headers = [
                        prop for prop in record.keys()
                        if not str(prop).startswith('#')
                    ]
                accepted, _ = self._should_accept_record(record)
                if not accepted:
                    if self._num_processed_records > max_records:
                        return None
                    continue
                self._record_index += 1
                return record

            if not self.open_next_input_file():
                break

        return None

    def close(self):
        """Closes all open input and output shard file handles."""
        if self._current_fp is not None:
            self._current_fp.close()
            self._current_fp = None
        for index, fp in list(self._output_fp.items()):
            if fp is not None:
                fp.close()
            self._output_fp[index] = None
        self._output_fp.clear()
        super().close()
