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
format (CSV, TSV, MCF, Apache Avro, JSON, JSONL) with per-shard `Counters`
and thread-safe parallel shard reads and writes.

Example:
  from file_dict_io import open_dict_file

  with open_dict_file('output@3.avro', 'w', shard_key='id') as writer:
    writer.write([{'id': '11', 'val': 'a'}, {'id': '21', 'val': 'b'}])

  with open_dict_file('output@3.avro', 'r') as reader:
    for row in reader:
      print(row)
"""

import functools
import hashlib
from io import UnsupportedOperation
import json
import math
import os
import re
import threading
from absl import logging

from counters import CounterOptions, Counters
from file_dict_io.avro_io import is_avro_file
from file_dict_io.base import FileDictIO
from file_dict_io.csv_io import is_csv_file
from file_dict_io.json_io import is_json_file, is_jsonl_file
from file_dict_io.mcf_io import (
    NODE_ID_PROPS,
    McfFileDictIO,
    get_record_dcid,
    is_mcf_file,
)
import file_util
import mcf_file_util

# Defaults
_DEFAULT_RECORDS_PER_SHARD = 100000
_DEFAULT_SHARD_FILENAME = 'shard-{index:05}-of-{shard_count:05d}'

_SHARD_CONFIG_KEYS = (
    'shard_key',
    'shard_key_prefix_length',
    'shard_count',
    'records_per_shard',
    'shard_headers',
    'estimated_num_records',
)


def get_default_shard_config() -> dict:
    """Returns the default configuration dictionary for `ShardedFileDictIO`.

    Returns:
      A `dict` with default values for sharding options.
    """
    return {
        'shard_key': '',
        'shard_key_prefix_length': 0,
        'shard_count': 0,
        'records_per_shard': _DEFAULT_RECORDS_PER_SHARD,
        'shard_headers': [],
        'estimated_num_records': 0,
    }


@functools.lru_cache(maxsize=131072)
def str_to_int_hash(input_string: str) -> int:
    """Returns a deterministic 64-bit integer hash for `input_string` using SHA-256.

    Args:
      input_string: The string key to hash.

    Returns:
      An unsigned integer derived from the first 8 bytes (16 hex digits) of the
      SHA-256 digest.
    """
    encoded_string = str(input_string).encode('utf-8')
    return int.from_bytes(hashlib.sha256(encoded_string).digest()[:8], 'big')


@functools.lru_cache(maxsize=131072)
def _hash_key_to_shard(key: str, shard_count: int) -> int:
    """Returns the cached modulo shard index for `(key, shard_count)`."""
    return str_to_int_hash(key) % shard_count


def is_sharded_file(filename: str | list) -> bool:
    """Returns True if `filename` represents a sharded file pattern or file list.

    Detects:
      - `@<N>` shard count notation (e.g. `'output@10.csv'`, `'nodes.mcf@10'`)
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

    Supports CSV/TSV, MCF, Apache Avro, and JSON/JSONL shards:
      - `shard_key`: Column/property name (e.g. `'dcid'`, `'Node'`) or format
        string combining multiple columns (e.g. `'{observationDate}{observationAbout}'`).
        If omitted, defaults to `'dcid'`, `'Node'`, the first header column, or
        the normalized record fingerprint. With `'dcid'` or `'Node'`, records
        are routed by the node's dcid, using `Node` if `dcid` is blank.
      - `shard_key_prefix_length`: Optional prefix length of the key value to
        use for hashing/routing.
      - `shard_count`: Number of output shards (can also be specified inline via
        `<prefix>@<N>.<ext>` or `<prefix>.<ext>@<N>`, e.g. `'output@10.avro'`
        or `'shards.mcf@10'`).
      - `records_per_shard`: Target records per shard when `shard_count` is
        estimated dynamically (e.g. with `'output*.csv'`).
      - `shard_headers`: Explicit list of column headers for output shards.
      - `estimated_num_records`: Optional estimated total records used to
        compute `shard_count` when `records_per_shard` is used.

    Thread Safety & Per-Shard State:
      - In write mode, each output shard maintains its own `Counters` instance
        (`get_shard_counters(shard_index)`) and per-shard lock so multiple
        threads can write to different shards in parallel without lock contention.
      - In read mode, `next()` uses a read lock so multiple worker threads can
        safely pull records from the same `ShardedFileDictIO` instance in parallel.

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
            `'shards.mcf@10'`, `'output*.avro'`, `'output-{year}.csv'`) or list
            of input files.
          mode: File open mode ('r' for read, 'w' for write).
          headers: Optional list of column names or MCF header comments. MCF
            shards get only the headers starting with `#`, as comment lines.
          encoding: Optional character encoding for text-based formats.
          schema: Optional Avro schema dictionary for `.avro` shards.
          config: Optional dictionary of sharding options (`shard_key`,
            `shard_key_prefix_length`, `shard_count`, `records_per_shard`,
            `shard_headers`, `estimated_num_records`). Any of these may also be
            passed directly via `**kwargs`.
          counters: Optional parent `Counters` instance into which per-shard
            counters are aggregated.
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

        self._init_lock = threading.Lock()
        self._read_lock = threading.Lock()
        self._current_fp: FileDictIO | None = None
        self._output_fp: dict[int | str, FileDictIO] = {}
        self._shard_locks: dict[int | str, threading.Lock] = {}
        self._shard_counters: dict[int | str, Counters] = {}
        self._shard_record_counts: dict[int | str, int] = {}
        self._unflushed_shard_counts: dict[int | str, int] = {}
        self._key_shard_cache: dict[str, int] = {}

        self._files: list[str] = []
        self._remaining_input_files: list[str] = []
        self._output_pattern: str = ''
        raw_shard_key = self._config.get('shard_key') or None
        if (isinstance(raw_shard_key, str) and raw_shard_key.startswith('{') and
                raw_shard_key.endswith('}') and raw_shard_key.count('{') == 1):
            raw_shard_key = raw_shard_key[1:-1]
        self._shard_key: str | None = raw_shard_key
        self._shard_key_prefix_length: int = int(
            self._config.get('shard_key_prefix_length') or 0)
        self._shard_count: int = int(self._config.get('shard_count') or 0)
        self._shard_by_column_value: bool = False
        self._estimated_num_records: int = int(
            self._config.get('estimated_num_records') or 0)
        self._shards_prepared: bool = False

        self.open()

    def open(self):
        """Initializes input shard files (read mode) or output shard pattern (write mode)."""
        self._record_index = 0
        self._header_written = False

        if self.is_read_mode():
            self._files = self._resolve_input_files(self._raw_filename)
            self._remaining_input_files = list(self._files)
            if not self._estimated_num_records and self._files:
                self._estimated_num_records = self._estimate_input_records()
            self.open_next_input_file()
        else:
            self._parse_output_pattern()
            # Pre-open output shards immediately if shard_count and headers/schema
            # are already known (or if MCF/JSON format does not require headers).
            if self._can_prepare_shards_now():
                self._prepare_output_shards()

    def close(self):
        """Merges per-shard counters and closes all open input and output shard handles."""
        self._merge_shard_counters()
        if self._current_fp is not None:
            self._current_fp.close()
            self._current_fp = None
        for index, fp in list(self._output_fp.items()):
            if fp is not None:
                with self._get_shard_lock(index):
                    fp.close()
            self._output_fp[index] = None
        self._output_fp.clear()
        super().close()

    def next(self) -> dict:
        """Reads and returns the next dictionary record across all input shards.

        Thread-safe: multiple threads may call `next()` (or `read()`) on the
        same `ShardedFileDictIO` instance concurrently.

        Returns:
          A `dict` for the next record, or `None` when all input shards have
          been read.
        """
        if not self.is_read_mode():
            return None

        with self._read_lock:
            while self._current_fp is not None:
                record = self._current_fp.next()
                if record is not None:
                    self._counters.add_counter('shard-input-records', 1)
                    if not self._headers:
                        self._headers = [
                            prop for prop in record.keys()
                            if not str(prop).startswith('#')
                        ]
                    self._record_index += 1
                    return record

                if not self.open_next_input_file():
                    break

        return None

    def write_record(self, record: dict, key: str = None):
        """Routes and writes a single dictionary record to its target output shard.

        Uses per-shard locks and per-shard `Counters` so multiple threads
        writing to different shards execute in parallel without global lock
        contention.

        Args:
          record: Dictionary record to write.
          key: Optional precomputed shard key string for `record`.

        Returns:
          The return value of the target shard's `write_record`.

        Raises:
          UnsupportedOperation: If opened in read mode.
        """
        if self._mode == 'r':
            raise UnsupportedOperation(
                f'Cannot write record to sharded file {self.filename()} opened in read mode'
            )

        if not self._shards_prepared:
            with self._init_lock:
                if not self._headers:
                    non_comment_keys = [
                        k for k in record.keys() if not str(k).startswith('#')
                    ]
                    if non_comment_keys and not (is_mcf_file(self._filename) or
                                                 is_json_file(self._filename)):
                        self.set_headers(non_comment_keys)
                if not self._shards_prepared:
                    self._prepare_output_shards()

        if key is None:
            key = self.get_key_for_record(record)
        shard_index = self.get_shard_for_key(key)

        with self._get_shard_lock(shard_index):
            output_fp = self.get_shard_file_handle(shard_index)
            self._unflushed_shard_counts[shard_index] = (
                self._unflushed_shard_counts.get(shard_index, 0) + 1)
            return output_fp.write_record(record)

    def write_header(self):
        """Writes headers to all active output shards."""
        for index, shard_fp in list(self._output_fp.items()):
            with self._get_shard_lock(index):
                shard_fp.write_header()
        self._header_written = True

    def files(self) -> list[str]:
        """Returns the list of input shard files (in read mode) or output shard files (in write mode)."""
        return list(self._files)

    def current_record_index(self) -> int:
        """Returns the total number of records read or written across all shards."""
        if not self.is_read_mode() and (self._shard_record_counts or
                                        self._unflushed_shard_counts):
            return sum(self._shard_record_counts.values()) + sum(
                self._unflushed_shard_counts.values())
        return self._record_index

    def counters(self) -> Counters:
        """Flushes all per-shard counters into the parent `Counters` instance and returns it."""
        self._merge_shard_counters()
        return self._counters

    def get_shard_counters(self, index: int | str) -> Counters:
        """Returns the dedicated per-shard `Counters` instance for `index`.

        Because each shard has its own `Counters` object, threads writing to
        different shards can increment counters without lock contention.

        Args:
          index: Shard index or column key value.

        Returns:
          The `Counters` object dedicated to shard `index`.
        """
        counters = self._shard_counters.get(index)
        if counters is None:
            counters = Counters(options=CounterOptions(show_every_n_sec=0))
            self._shard_counters[index] = counters
        pending = self._unflushed_shard_counts.get(index, 0)
        if pending > 0:
            self._unflushed_shard_counts[index] = 0
            self._shard_record_counts[index] = (
                self._shard_record_counts.get(index, 0) + pending)
            counters.add_counter(f'shard-{index}-outputs', pending)
            counters.add_counter('shard-output-records', pending)
        return counters

    def get_output_shard_filename(self, index: int | str) -> str:
        """Returns the resolved output filename for the shard at `index`.

        Safely formats both integer shard indices (`0`, `1`, ...) and string
        column values (such as `'2024'` or `'USA'` when sharding by `{year}` or
        `{country}`) without raising `ValueError` or `KeyError`.

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

        effective_shard_count = self._shard_count
        if not self._shard_by_column_value and effective_shard_count <= 0:
            effective_shard_count = self._estimate_shard_count()

        formatted_index = index
        pattern_to_format = output_pattern
        if not isinstance(index, int):
            if str(index).isdigit():
                formatted_index = int(index)
            else:
                pattern_to_format = re.sub(r'\{index:[^}]+\}', '{index}',
                                           pattern_to_format)

        format_vars = {
            'index': formatted_index,
            'shard_count': effective_shard_count,
        }
        if self._shard_key:
            clean_key = self._shard_key.strip('{}')
            format_vars[clean_key] = str(index)
            format_vars[self._shard_key] = str(index)

        for placeholder in re.findall(
                r'\{([a-zA-Z_][a-zA-Z0-9_]*)(?::[^}]*)?\}', pattern_to_format):
            if placeholder not in format_vars:
                format_vars[placeholder] = str(index)

        return pattern_to_format.format(**format_vars)

    def get_shard_file_handle(self, index: int | str) -> FileDictIO:
        """Returns (and lazily opens) the `FileDictIO` writer for shard `index`.

        Args:
          index: Shard index or column key value.

        Returns:
          The open `FileDictIO` writer instance for that shard.
        """
        fp = self._output_fp.get(index)
        if fp is None:
            output_file = self.get_output_shard_filename(index)
            fp = self._create_single_file_io(output_file,
                                             mode='w',
                                             headers=self._headers)
            self._output_fp[index] = fp
            self._shard_locks.setdefault(index, threading.Lock())
            self._shard_record_counts.setdefault(index, 0)
            self._unflushed_shard_counts.setdefault(index, 0)
            self._files.append(output_file)
            self.get_shard_counters(index).add_counter('shard-output-files', 1)
        return fp

    def get_key_for_record(self, record: dict) -> str:
        """Extracts the shard key string for `record` according to `shard_key` and `shard_key_prefix_length`.

        When `shard_key` is `dcid` or `Node`, the key is the node's dcid: the
        `dcid` value, or the `Node` value if the `dcid` is missing or blank,
        without quotes or a namespace prefix such as `dcid:`. So
        `{'dcid': 'geoId/06'}` and `{'Node': 'dcid:geoId/06'}` are routed to
        the same shard.

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
            elif self._shard_key in NODE_ID_PROPS:
                key = get_record_dcid(record)
                if not key:
                    # No dcid or Node value: use the shard key value as is.
                    val = record.get(self._shard_key)
                    key = None if val is None else str(val)
            else:
                val = record.get(self._shard_key)
                if val is not None:
                    key = str(val)
        if key is None:
            key = self._record_to_canonical_str(record)

        if self._shard_key_prefix_length > 0:
            key = key[:self._shard_key_prefix_length]
        return key

    def get_shard_for_key(self, key: str) -> int | str:
        """Returns the target shard index (or string key if uncounted) for `key`."""
        if not key:
            key = ''
        if self._shard_count and not self._shard_by_column_value:
            return _hash_key_to_shard(key, self._shard_count)
        return key

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
            self._counters.add_counter('error-shard-mismatched-headers', 1)
        self._counters.add_counter('shard-input-files', 1)
        self._infer_default_shard_key(self._headers)
        return True

    # Internal helper methods

    def _create_single_file_io(self,
                               shard_filename: str,
                               mode: str,
                               headers: list = None) -> FileDictIO:
        """Instantiates the non-sharded `FileDictIO` handler for `shard_filename`."""
        handler_cls = FileDictIO.get_handler(shard_filename)
        if handler_cls is ShardedFileDictIO:
            handler_cls = FileDictIO._default_handler
        if handler_cls is None:
            raise ValueError(
                f'No FileDictIO handler found for shard file: {shard_filename}')
        if headers and issubclass(handler_cls, McfFileDictIO):
            # MCF headers are written as comment lines, so pass only comment
            # headers and not column names such as those from a CSV input.
            if isinstance(headers, str):
                headers = [headers]
            headers = [h for h in headers if str(h).startswith('#')]
        kwargs = dict(self._extra_kwargs)
        if self._schema is not None:
            kwargs['schema'] = self._schema
        return handler_cls(shard_filename,
                           mode=mode,
                           headers=headers,
                           encoding=self._encoding,
                           **kwargs)

    @classmethod
    def resolve_input_files(cls, filename: str | list) -> list[str]:
        """Expands `@`, `*`, comma-separated, or list patterns into sorted matching shard files.

        When `@<N>` is specified (e.g. `node.mcf@10` or `node@10.mcf`), only
        files with digit shard indices and the matching shard count (`00010`)
        are matched (`node.mcf-[0-9]*-of-00010` or `node-[0-9]*-of-00010.mcf`),
        preventing false matches against `nodes.mcf-...` or `...-of-00002`.
        """
        if isinstance(filename, list):
            raw_items = filename
        elif isinstance(filename, str):
            raw_items = [filename]
        else:
            return []

        patterns = []
        for item in raw_items:
            if isinstance(item, str) and ',' in item:
                patterns.extend(p.strip() for p in item.split(',') if p.strip())
            elif item:
                patterns.append(item)

        matched_files = []
        for pattern in patterns:
            if '@' in pattern:
                prefix, shard_spec = pattern.split('@', 1)
                spec_ext = ''
                if '.' in shard_spec:
                    shard_count_str, ext_part = shard_spec.split('.', 1)
                    spec_ext = '.' + ext_part
                else:
                    shard_count_str = shard_spec

                if shard_count_str.isdigit():
                    count_pat = f'{int(shard_count_str):05d}'
                else:
                    count_pat = '[0-9]*'

                base, prefix_ext = os.path.splitext(prefix)
                candidate_globs = []
                if prefix_ext:
                    candidate_globs.append(
                        f'{prefix}-[0-9]*-of-{count_pat}')
                    candidate_globs.append(
                        f'{base}-[0-9]*-of-{count_pat}{prefix_ext}')
                elif spec_ext:
                    candidate_globs.append(
                        f'{prefix}-[0-9]*-of-{count_pat}{spec_ext}')
                    candidate_globs.append(
                        f'{prefix}{spec_ext}-[0-9]*-of-{count_pat}')
                else:
                    candidate_globs.append(
                        f'{prefix}-[0-9]*-of-{count_pat}')
            else:
                candidate_globs = [pattern]

            for glob_pat in candidate_globs:
                matches = sorted(file_util.file_get_matching(glob_pat))
                if matches:
                    for match in matches:
                        if match not in matched_files:
                            matched_files.append(match)
                    break
        return matched_files

    def _resolve_input_files(self, filename: str | list) -> list[str]:
        """Expands input file patterns using `resolve_input_files`."""
        return self.resolve_input_files(filename)

    @classmethod
    def estimate_input_records(cls,
                               files: list[str],
                               headers: list = None) -> int:
        """Estimates the number of records across `files` for CSV, JSON/JSONL, MCF, or Avro."""
        if not files:
            return 0
        first_file = files[0]
        if is_avro_file(first_file):
            return 0
        try:
            if is_csv_file(first_file) or is_jsonl_file(first_file):
                return file_util.file_estimate_num_rows(files)
            if is_json_file(first_file):
                filesize = file_util.file_get_size(files)
                if filesize <= 0:
                    return 0
                with file_util.FileIO(first_file, use_tempfile=False) as fp:
                    sample = fp.read(4000)
                if isinstance(sample, bytes):
                    sample = sample.decode('utf-8', errors='ignore')
                num_objects = max(sample.count('}'), 1)
                bytes_per_record = max(len(sample) / num_objects, 1)
                return int(filesize / bytes_per_record)
            # MCF or default multi-line node files:
            estimated_lines = file_util.file_estimate_num_rows(files)
            if headers:
                non_comment_headers = [
                    h for h in headers if not str(h).startswith('#')
                ]
                if non_comment_headers:
                    return int(
                        estimated_lines / max(1, len(non_comment_headers)))
            with file_util.FileIO(first_file, use_tempfile=False) as fp:
                sample = fp.read(4000)
            if isinstance(sample, bytes):
                sample = sample.decode('utf-8', errors='ignore')
            sample_lines = [
                line.strip() for line in sample.splitlines() if line.strip()
            ]
            node_count = sum(
                1 for line in sample_lines if line.startswith('Node:'))
            if node_count > 0:
                lines_per_node = max(1, len(sample_lines) / node_count)
                return int(estimated_lines / lines_per_node)
            return estimated_lines
        except UnicodeDecodeError:
            return 0

    def _estimate_input_records(self) -> int:
        """Estimates the number of records across `self._files`."""
        return self.estimate_input_records(self._files, self._headers)

    def _can_prepare_shards_now(self) -> bool:
        """Returns True if output shards can be opened before the first record."""
        if self._shard_by_column_value or self._shard_count <= 0:
            return False
        if self._headers or self._schema:
            return True
        if is_mcf_file(self._filename) or is_json_file(self._filename):
            return True
        return False

    def _parse_output_pattern(self):
        """Parses `@<N>`, `*`, or `{column}` in `self._filename` to set `_output_pattern` and `_shard_count`.

        Keeps `{shard_count:05d}` as a deferred placeholder in `_output_pattern`
        when `shard_count` is not yet known at `open()` time so it can be
        resolved later in `_prepare_output_shards()`.
        """
        output_pattern = self._filename
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
                self._shard_count = shard_count
            output_pattern = (
                f'{prefix}-{{index:05d}}-of-{{shard_count:05d}}{suffix}')

        if '*' in output_pattern:
            prefix, suffix = output_pattern.split('*', 1)
            output_pattern = (
                f'{prefix}{{index:05d}}-of-{{shard_count:05d}}{suffix}')

        self._output_pattern = output_pattern
        self._detect_column_value_pattern()

    def _detect_column_value_pattern(self):
        """Detects `{column}` placeholders (such as `{year}`) in `_output_pattern`."""
        placeholders = re.findall(r'\{([a-zA-Z_][a-zA-Z0-9_]*)(?::[^}]*)?\}',
                                  self._output_pattern)
        custom_cols = [
            p for p in placeholders if p not in ('index', 'shard_count')
        ]
        if custom_cols:
            self._shard_by_column_value = True
            self._shard_count = 0
            if not self._shard_key:
                self._shard_key = custom_cols[0]
        elif self._shard_key:
            clean_key = self._shard_key.strip('{}')
            if clean_key in placeholders and clean_key not in (
                    'index', 'shard_count'):
                self._shard_by_column_value = True
                self._shard_count = 0

    def _estimate_shard_count(self) -> int:
        """Determines the number of shards from `config` or `records_per_shard`."""
        shard_count = int(self._config.get('shard_count') or 0)
        if shard_count > 0:
            return shard_count
        records_per_shard = int(
            self._config.get('records_per_shard') or _DEFAULT_RECORDS_PER_SHARD)
        if records_per_shard <= 0:
            records_per_shard = _DEFAULT_RECORDS_PER_SHARD
        if self._estimated_num_records > 0:
            return max(
                1, math.ceil(self._estimated_num_records / records_per_shard))
        return 1

    def _prepare_output_shards(self):
        """Resolves `self._shard_count` (if deferred) and pre-opens output shard handles."""
        if self._shards_prepared:
            return
        self._detect_column_value_pattern()
        if self._shard_key is None and self._headers:
            self._infer_default_shard_key(self._headers)
        if not self._shard_by_column_value and self._shard_count <= 0:
            self._shard_count = self._estimate_shard_count()
        self._shards_prepared = True
        if self._shard_count > 0:
            for index in range(self._shard_count):
                self.get_shard_file_handle(index)

    def _get_shard_lock(self, index: int | str) -> threading.Lock:
        """Returns the per-shard `threading.Lock` for `index`."""
        lock = self._shard_locks.get(index)
        if lock is None:
            with self._init_lock:
                lock = self._shard_locks.get(index)
                if lock is None:
                    lock = threading.Lock()
                    self._shard_locks[index] = lock
        return lock

    def _merge_shard_counters(self):
        """Locks each shard, merges its `Counters` into `self._counters`, and resets the per-shard counter."""
        all_indices = set(self._shard_counters.keys()) | set(
            self._unflushed_shard_counts.keys())
        for index in list(all_indices):
            with self._get_shard_lock(index):
                shard_counter = self.get_shard_counters(index)
                if shard_counter._counters:
                    for name, count in list(shard_counter._counters.items()):
                        if (name == 'start_time' or
                                name.startswith(('process_', 'process-')) or
                                (name == 'processed' and count == 0)):
                            continue
                        self._counters.add_counter(name, count)
                    shard_counter._counters.clear()

    def _infer_default_shard_key(self, candidate_keys: list[str]):
        """Infers `self._shard_key` from `dcid`, `Node`, or the first available key."""
        if self._shard_key is None and candidate_keys:
            if 'dcid' in candidate_keys:
                self._shard_key = 'dcid'
            elif 'Node' in candidate_keys:
                self._shard_key = 'Node'
            else:
                self._shard_key = candidate_keys[0]

    def _record_to_canonical_str(self, record: dict) -> str:
        """Normalizes and serializes `record` deterministically for fingerprinting."""
        try:
            normalized = mcf_file_util.normalize_mcf_node(record)
            return mcf_file_util.node_dict_to_text(normalized)
        except Exception:
            return json.dumps(record, sort_keys=True, default=str)
