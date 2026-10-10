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

Supports sharding of CSV, TSV, MCF, Apache Avro, and JSON/JSONL files, along
with duplicate record elimination, key-based sampling, and input record limits.

To shard a file using the content of a column or a property, run:
  python file_sharder.py --shard_input=<input-file> --shard_output=<prefix>@<NN>

To emit a record to a shard based on a specific column or property, set `shard_key`:
  --shard_key="<column-name>"
If no `shard_key` is set, it uses `dcid` if the input has that column or
property, else `Node`, else the first column or property. With `dcid` or `Node`,
a record is routed by its dcid, or by its `Node` if the dcid is empty. A record
that doesn't have the key is routed by the fingerprint of the entire record,
and all records with an empty key go to the same shard.

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

import concurrent.futures
import functools
import hashlib
import json
import os
import sys
import threading

from absl import app
from absl import flags
from absl import logging

# uncomment to run pprof
# os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
# from pypprof.net_http import start_pprof_server

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(_SCRIPT_DIR), 'tools', 'statvar_importer'))

from counters import CounterOptions, Counters
from file_dict_io import (
    FileDictIO,
    ShardedFileDictIO,
    get_default_shard_config as get_base_shard_config,
    get_record_dcid,
    open_dict_file,
    str_to_int_hash,
)
import mcf_file_util

# Defaults
_DEFAULT_RECORDS_PER_SHARD = 100000
_DEFAULT_SHARD_FILENAME = 'shard-{index:05}-of-{shard_count:05d}'
_NUM_DEDUP_BUCKETS = 64
# Number of input records between updates to the global progress counters.
_PROGRESS_BATCH_SIZE = 100000

# Counters specific to a `Counters` instance (timestamps, rates, and totals set
# separately) that must not be summed when merging counters.
_NON_ADDITIVE_COUNTERS = frozenset({'start_time', 'total', 'processing_rate'})
_NON_ADDITIVE_COUNTER_PREFIXES = ('process_', 'process-')

# Base32 encoding map and default ignored properties for DCID generation
_DCID_BASE32_MAP = '0123456789bcdfghjklmnpqrstvwxyze'
_MAX_LONG_ID_LEN = 13
_MAX_NUM_BITS = 5

_DCID_IGNORE_PROPS = frozenset({
    'Node',
    'dcid',
    'name',
    'description',
    'descriptionUrl',
    'alternateName',
    'nameWithLanguage',
    'constraintProperties',
    'memberOf',
    'provenance',
    'label',
    'isPublic',
    'keyString',
    'resMCFFile',
    'localCuratorLevelId',
    'censusACSTableId',
})

_FLAGS = flags.FLAGS

flags.DEFINE_string('shard_input', '', 'Input files to be sharded')
flags.DEFINE_string('shard_output', '', 'Output file pattern for sharded file')
flags.DEFINE_string(
    'shard_key', '', 'Key or column to shard an input record. Defaults to '
    'dcid, else Node, else the first column.')
flags.DEFINE_integer('shard_key_prefix_length', 0,
                     'Length of key value to use for sharding')
flags.DEFINE_integer('shard_count', 0, 'Number of output shards to generate.')
flags.DEFINE_integer(
    'records_per_shard', _DEFAULT_RECORDS_PER_SHARD,
    'Number of records per output shard if shard_count is not set.')
flags.DEFINE_bool('shard_skip_duplicates', False, 'Skip duplicate records.')
flags.DEFINE_integer('shard_input_records', sys.maxsize,
                     'Limit the number of input records to shard.')
flags.DEFINE_list('shard_headers', [], 'Header columns for sharded outputs.')
flags.DEFINE_float(
    'shard_sample_rate', 1,
    'Fraction of shard keys to keep, in the range [0, 1]. All records with '
    'the same shard key are kept or dropped together.')
flags.DEFINE_integer('shard_threads', 1,
                     'Maximum number of parallel threads for reading inputs.')
flags.DEFINE_list(
    'shard_default_pvs', [],
    'Default property:value pairs to add to each record if not present '
    '(e.g. "typeOf:StatVarObservation").')
flags.DEFINE_bool(
    'shard_generate_dcid', False,
    'Generate a deterministic dcid for records that do not have a dcid/Node.')
flags.DEFINE_list(
    'shard_dcid_ignore_props', [],
    'Additional properties to ignore when generating a dcid for a record.')


def _base32_encode_uint64(value: int) -> str:
    """Encodes a 64-bit unsigned integer into up to 13 DC base32 characters."""
    val = value & 0xFFFFFFFFFFFFFFFF
    chars = []
    for _ in range(_MAX_LONG_ID_LEN):
        chars.append(_DCID_BASE32_MAP[val & 0x1F])
        val >>= _MAX_NUM_BITS
        if val == 0:
            break
    return ''.join(chars)


def _get_long_id(key_string: str) -> str:
    """Computes a cross-language portable SHA-256 64-bit base32 ID for `key_string`."""
    return _base32_encode_uint64(str_to_int_hash(key_string))


def generate_node_dcid(
    record: dict,
    ignore_props: set[str] | frozenset[str] = _DCID_IGNORE_PROPS,
) -> str:
    r"""Generates a deterministic DCID for `record` using all non-ignored properties.

    The dcid is computed as follows, so it can be reproduced in any language:
      1. Properties: every property that is not in `ignore_props` and doesn't
         start with `#`, with a value that is not empty after removing
         surrounding spaces and double quotes. Returns `''` if there are none,
         or if any of these values starts with `l:` (a local reference).
      2. Values: each value is converted to a string, and surrounding spaces
         and double quotes are removed. A quantity range such as
         `[10 20 Years]` is normalized with `mcf_file_util.normalize_range`.
         Then, if the value has no `"` and its first non-letter character is
         `:`, everything up to and including that `:` is removed and
         surrounding whitespace is stripped, so `dcid:geoId/06` becomes
         `geoId/06` (`mcf_file_util.strip_namespace`).
      3. Key: the JSON array of `[property, value]` pairs sorted by property
         (Unicode code point order), with no whitespace, for example
         `[["observationAbout","geoId/06"],["value","39538223"]]`. Only `"`,
         `\` and U+0000 to U+001F are escaped, as `\"`, `\\`, `\b`, `\f`,
         `\n`, `\r`, `\t` or `\u00xx` with lowercase hex. All other
         characters, including non-ASCII, `/`, `<`, `>` and `&`, are written
         as is. For valid Unicode strings, this is Python's
         `json.dumps(pairs, ensure_ascii=False, separators=(',', ':'))` and
         JavaScript's `JSON.stringify(pairs)`.
      4. Id: the first 8 bytes of the SHA-256 digest of the UTF-8 encoded key,
         read as a big-endian unsigned integer, written as base-32 digits
         `0123456789bcdfghjklmnpqrstvwxyze`, least significant digit first,
         stopping after the highest non-zero digit (at most 13 digits).
      5. Prefix: `dc/o/<id>` for a `StatVarObservation` (its `typeOf`, or a
         record with `observationAbout` and `variableMeasured` and no
         `typeOf`), and `dc/<id>` for other nodes.

    Args:
      record: Dictionary of property-value pairs for the node.
      ignore_props: Set of property names to exclude when building the DCID key.

    Returns:
      Generated DCID string (e.g. `'dc/o/...'` or `'dc/...'`), or `''` if no
      non-ignored properties are present or an unresolved local reference
      (`l:...`) is found.
    """
    if not record:
        return ''

    type_of = mcf_file_util.strip_namespace(
        str(record.get('typeOf', '')).strip(' "'))
    if not type_of and 'observationAbout' in record and 'variableMeasured' in record:
        type_of = 'StatVarObservation'

    props = []
    for prop, raw_val in record.items():
        if not prop or str(prop).startswith('#') or prop in ignore_props:
            continue
        val_str = '' if raw_val is None else str(raw_val).strip(' "')
        if not val_str:
            continue
        if val_str.startswith('l:'):
            return ''
        props.append(prop)

    if not props:
        return ''

    props.sort()
    pairs = []
    for prop in props:
        val_str = str(record[prop]).strip(' "')
        if val_str.startswith('['):
            val_str = mcf_file_util.normalize_range(
                val_str, quantity_range_to_dcid=True)
        pairs.append([prop, mcf_file_util.strip_namespace(val_str)])

    # JSON keeps the property and value boundaries unambiguous. Joining
    # 'prop=value' strings gave {'a': 'b', 'c': 'd'} and {'a': 'bc=d'} the
    # same key.
    key_string = json.dumps(pairs, ensure_ascii=False, separators=(',', ':'))
    prefix = 'dc/o/' if type_of == 'StatVarObservation' else 'dc/'
    return f'{prefix}{_get_long_id(key_string)}'


def _parse_default_pvs(default_pvs: dict | list | str | None) -> dict[str, str]:
    """Parses `default_pvs` from a dict, list of 'prop:val' strings, or comma-separated string."""
    if not default_pvs:
        return {}
    if isinstance(default_pvs, dict):
        return {str(k).strip(): str(v).strip() for k, v in default_pvs.items() if k}
    items = (
        [s.strip() for s in default_pvs.split(',') if s.strip()]
        if isinstance(default_pvs, str) else list(default_pvs)
    )
    parsed = {}
    for item in items:
        if not isinstance(item, str):
            continue
        sep = ':' if ':' in item else ('=' if '=' in item else None)
        if sep:
            prop, val = item.split(sep, 1)
            if prop.strip():
                parsed[prop.strip()] = val.strip()
    return parsed


@functools.lru_cache(maxsize=131072)
def _get_sample_fraction(key: str) -> float:
    """Returns a deterministic, uniformly distributed fraction in [0, 1) for `key`.

    Uses bytes 8-15 of the SHA-256 digest of the UTF-8 encoded `key`, while
    records are routed to shards with bytes 0-7 (`str_to_int_hash`). The two
    are independent, so keys selected for sampling are spread uniformly across
    all output shards. The big-endian 64-bit value is reduced to its top 53
    bits so the fraction is exactly representable as a double in any language.

    Args:
      key: Shard key string for a record.

    Returns:
      A float in the range [0, 1).
    """
    digest = hashlib.sha256(str(key).encode('utf-8')).digest()
    return (int.from_bytes(digest[8:16], 'big') >> 11) / float(1 << 53)


def _is_additive_counter(name: str, value) -> bool:
    """Returns True if counter `name` with `value` can be summed across `Counters`."""
    if name in _NON_ADDITIVE_COUNTERS or name.startswith(
            _NON_ADDITIVE_COUNTER_PREFIXES):
        return False
    return isinstance(value, (int, float))


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
        'shard_threads': _FLAGS.shard_threads,
        'shard_default_pvs': _FLAGS.shard_default_pvs,
        'shard_generate_dcid': _FLAGS.shard_generate_dcid,
        'shard_dcid_ignore_props': _FLAGS.shard_dcid_ignore_props,
    })
    return config


class FileSharder:
    """Shards input dictionary files into output shards using `ShardedFileDictIO`.

    Reads multiple input files in parallel with a separate `FileDictIO` reader
    per input file, applying default property values (`shard_default_pvs`),
    deterministic DCID generation (`shard_generate_dcid`), shard-independent
    deduplication (`shard_skip_duplicates`), deterministic key sampling
    (`shard_sample_rate`), and record limits (`shard_input_records`), while
    writing to output shards through `ShardedFileDictIO`.

    Example:
      from file_sharder import FileSharder

      sharder = FileSharder('input.csv', 'output@10.csv', {'shard_key': 'dcid'})
      sharder.process()
    """

    def __init__(self,
                 input_files: str | list,
                 output_path: str = '',
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
        # Validate before creating any state so invalid configs fail cleanly.
        self.setup_sample_rate()
        self._counters = counters if counters is not None else Counters()
        self._reader_counters = Counters(
            options=CounterOptions(show_every_n_sec=0))
        self._writer_counters = Counters(
            options=CounterOptions(show_every_n_sec=0))
        self._output_path = (
            output_path or self._config.get('shard_output_path') or '')
        self._lock = threading.Lock()
        self._dedup_locks = [
            threading.Lock() for _ in range(_NUM_DEDUP_BUCKETS)
        ]
        self._records_seen_buckets: list[set[int]] = [
            set() for _ in range(_NUM_DEDUP_BUCKETS)
        ]
        self._num_input_records: int = 0
        self._num_workers: int = 1
        self._default_pvs = _parse_default_pvs(
            self._config.get('shard_default_pvs') or
            self._config.get('default_pvs'))
        self._generate_dcid = bool(
            self._config.get('shard_generate_dcid') or
            self._config.get('generate_dcid', False))
        extra_ignore_props = (
            self._config.get('shard_dcid_ignore_props') or
            self._config.get('dcid_ignore_props') or [])
        if isinstance(extra_ignore_props, str):
            extra_ignore_props = [
                p.strip() for p in extra_ignore_props.split(',') if p.strip()
            ]
        self._dcid_ignore_props = frozenset(_DCID_IGNORE_PROPS |
                                            set(extra_ignore_props))

        self._input_files = ShardedFileDictIO.resolve_input_files(input_files)
        self._headers = list(self._config.get('shard_headers') or [])
        self._shard_key = self._config.get('shard_key') or None
        if self._input_files and not self._headers:
            with open_dict_file(self._input_files[0], mode='r') as preview_reader:
                preview_headers = preview_reader.headers()
                if preview_headers:
                    self._headers = list(preview_headers)

        if not self._output_path and self._input_files:
            self._output_path = self._input_files[0]

        if self._headers and not str(self._headers[0]).startswith('#'):
            for prop in self._default_pvs:
                if prop not in self._headers:
                    self._headers.append(prop)
            if (self._generate_dcid and 'dcid' not in self._headers and
                    'Node' not in self._headers):
                self._headers.insert(0, 'dcid')

        writer_config = {
            'shard_key': self._shard_key,
            'shard_key_prefix_length': self._config.get(
                'shard_key_prefix_length', 0),
            'shard_count': self._config.get('shard_count', 0),
            'records_per_shard': self._config.get(
                'records_per_shard', _DEFAULT_RECORDS_PER_SHARD),
            'shard_headers': self._headers,
            # Used to derive shard_count from records_per_shard, so size the
            # shards for the expected number of records after sampling.
            'estimated_num_records': round(
                self.get_input_records_estimate() * self._sample_rate),
        }

        self._writer = ShardedFileDictIO(
            self._output_path,
            mode='w',
            headers=self._headers,
            config=writer_config,
            counters=self._writer_counters,
        )

    def __del__(self):
        self.close()

    def close(self):
        """Closes the underlying `ShardedFileDictIO` writer and merges writer counters."""
        if getattr(self, '_writer', None) is not None:
            self._writer.close()
        writer_counters = getattr(self, '_writer_counters', None)
        if writer_counters is not None:
            for name, count in writer_counters.get_counters().items():
                # Global 'processed' counts input records as they are read.
                if name == 'processed' or not _is_additive_counter(name, count):
                    continue
                self._counters.add_counter(name, count)
            writer_counters._counters.clear()

    def apply_default_pvs(self, record: dict) -> dict:
        """Adds configured `shard_default_pvs` to `record` for properties not already set."""
        if not self._default_pvs:
            return record
        for prop, default_val in self._default_pvs.items():
            if prop not in record or record[prop] in (None, ''):
                record[prop] = default_val
        return record

    def maybe_generate_dcid(self, record: dict) -> str:
        """Generates and sets `dcid` (or `Node`) on `record` if missing and `shard_generate_dcid` is enabled.

        A record already has a dcid if its `dcid`, or else its `Node`, has a
        value, so a record with a blank `dcid` keeps its existing `Node`.
        """
        existing_dcid = get_record_dcid(record)
        if existing_dcid and not existing_dcid.startswith('l:'):
            return existing_dcid
        generated = generate_node_dcid(record, self._dcid_ignore_props)
        if not generated:
            return ''
        if 'Node' in record or (self._headers and 'Node' in self._headers):
            record['Node'] = mcf_file_util.add_namespace(generated)
        else:
            record['dcid'] = generated
        return generated

    def is_duplicate_record(self, record: dict) -> bool:
        """Returns True if `record` is a duplicate of a previously seen record.

        Normalizes the record using `mcf_file_util.normalize_mcf_node` so
        equivalent nodes with different property ordering or value list ordering
        are recognized as duplicates. Uses hash-bucketed locks (`_NUM_DEDUP_BUCKETS`)
        keyed by the record fingerprint hash so duplicate detection is completely
        independent of `shard_index` while remaining lock-contention-free across
        worker threads.
        """
        try:
            normalized = mcf_file_util.normalize_mcf_node(record)
            canonical = mcf_file_util.node_dict_to_text(normalized)
        except Exception:
            canonical = json.dumps(record, sort_keys=True, default=str)
        record_hash = str_to_int_hash(canonical)
        bucket_idx = record_hash % _NUM_DEDUP_BUCKETS
        with self._dedup_locks[bucket_idx]:
            seen_set = self._records_seen_buckets[bucket_idx]
            if record_hash in seen_set:
                return True
            seen_set.add(record_hash)
            return False

    def setup_sample_rate(self):
        """Validates `shard_sample_rate`, the fraction of shard keys to keep.

        Raises:
          ValueError: If `shard_sample_rate` is outside the range [0, 1].
        """
        sample_rate = self._config.get('shard_sample_rate')
        sample_rate = 1.0 if sample_rate is None else float(sample_rate)
        if not 0.0 <= sample_rate <= 1.0:
            raise ValueError(f'Invalid shard_sample_rate {sample_rate}: '
                             'expected a value in the range [0, 1]')
        self._sample_rate = sample_rate
        if sample_rate < 1.0:
            logging.info(f'Sampling a fraction {sample_rate} of shard keys.')

    def should_sample_key(self, key: str) -> bool:
        """Returns True if `key` is selected based on `shard_sample_rate`.

        A key is selected when its `_get_sample_fraction()` is below the sample
        rate, so a rate of 0 keeps no keys and a rate of 1 keeps all keys. All
        records with the same key are kept or dropped together, and selection
        is independent of the shard index, so kept keys are spread uniformly
        across the output shards.
        """
        if self._sample_rate >= 1.0:
            return True
        return _get_sample_fraction(key) < self._sample_rate

    def get_input_records_estimate(self) -> int:
        """Returns the estimated number of input records across `self._input_files`."""
        return ShardedFileDictIO.estimate_input_records(self._input_files,
                                                        self._headers)

    def _process_input_file(self, input_file: str) -> tuple[int, int]:
        """Reads and shards a single `input_file` using its own `FileDictIO` reader."""
        max_records = int(self._config.get('shard_input_records', sys.maxsize))
        skip_duplicates = bool(self._config.get('shard_skip_duplicates', False))
        sample_enabled = self._sample_rate < 1.0
        default_pvs = self._default_pvs
        generate_dcid = self._generate_dcid

        # Per-file progress is printed only with a single worker so progress
        # from parallel workers doesn't interleave. Global progress is updated
        # every _PROGRESS_BATCH_SIZE records in either case.
        if self._num_workers > 1:
            file_counters = Counters(options=CounterOptions(show_every_n_sec=0))
        else:
            file_counters = Counters()
        file_counters.add_counter(
            'total',
            ShardedFileDictIO.estimate_input_records([input_file],
                                                     self._headers),
        )
        file_counters.add_counter('shard-input-files', 1)
        file_input_records = 0
        file_output_records = 0
        batch_processed = 0

        with open_dict_file(input_file, mode='r') as reader:
            file_headers = reader.headers()
            if file_headers:
                expected_headers = list(file_headers)
                if not str(expected_headers[0]).startswith('#'):
                    for prop in default_pvs:
                        if prop not in expected_headers:
                            expected_headers.append(prop)
                    if (generate_dcid and 'dcid' not in expected_headers and
                            'Node' not in expected_headers):
                        expected_headers.insert(0, 'dcid')
                with self._lock:
                    if not self._headers:
                        self._headers = expected_headers
                        self._writer.set_headers(self._headers)
                    elif (self._headers != expected_headers and
                          not str(expected_headers[0]).startswith('#')):
                        logging.error(
                            f'Mismatched headers in {input_file}: {expected_headers} != {self._headers}'
                        )
                        file_counters.add_counter(
                            'error-shard-mismatched-headers', 1)

            for record in reader:
                if max_records < sys.maxsize:
                    with self._lock:
                        if self._num_input_records >= max_records:
                            break
                        self._num_input_records += 1

                file_input_records += 1
                batch_processed += 1
                if batch_processed >= _PROGRESS_BATCH_SIZE:
                    # Update progress before any record is skipped below.
                    self._add_processed_records(file_counters, batch_processed)
                    batch_processed = 0

                if default_pvs:
                    self.apply_default_pvs(record)
                    file_counters.add_counter('shard-default-pvs-applied', 1)

                if generate_dcid:
                    prev_dcid = get_record_dcid(record)
                    new_dcid = self.maybe_generate_dcid(record)
                    if new_dcid and new_dcid != prev_dcid:
                        file_counters.add_counter('shard-dcid-generated', 1)

                if skip_duplicates and self.is_duplicate_record(record):
                    file_counters.add_counter('shard-duplicate-dropped', 1)
                    continue

                key = None
                if sample_enabled:
                    key = self._writer.get_key_for_record(record)
                    if not self.should_sample_key(key):
                        file_counters.add_counter('shard-sampled-dropped', 1)
                        continue

                if not self._headers:
                    with self._lock:
                        if not self._headers:
                            self._headers = [
                                prop for prop in record.keys()
                                if not str(prop).startswith('#')
                            ]
                            self._writer.set_headers(self._headers)

                self._writer.write_record(record, key=key)
                file_output_records += 1

        self._add_processed_records(file_counters, batch_processed)
        with self._lock:
            for name, count in file_counters.get_counters().items():
                # 'processed' is already added by _add_processed_records().
                if name == 'processed' or not _is_additive_counter(name, count):
                    continue
                self._reader_counters.add_counter(name, count)
                self._counters.add_counter(name, count)
            self._reader_counters.add_counter(
                'total', file_counters.get_counter('total'))
        return file_input_records, file_output_records

    def _add_processed_records(self, file_counters: Counters, count: int):
        """Adds `count` processed input records to the per-file and global counters.

        Called every `_PROGRESS_BATCH_SIZE` records so global progress, rate, and
        remaining time stay current while a large input file is being read.

        Args:
          file_counters: Per-file `Counters` for the input file being read.
          count: Number of input records processed since the last update.
        """
        if count <= 0:
            return
        file_counters.add_counter('processed', count)
        with self._lock:
            self._reader_counters.add_counter('processed', count)
            self._counters.add_counter('processed', count)

    def process(self):
        """Reads all input files in parallel with separate `FileDictIO` readers and writes output shards."""
        if not self._input_files:
            logging.error(f'No files to process for {self._input_files}')
            self.close()
            return

        self._counters.add_counter('total', self.get_input_records_estimate())
        num_input_records = 0
        num_output_records = 0

        num_files = len(self._input_files)
        max_workers = max(
            1,
            min(num_files, int(self._config.get('shard_threads') or 1)),
        )
        self._num_workers = max_workers
        if max_workers == 1:
            for input_file in self._input_files:
                in_cnt, out_cnt = self._process_input_file(input_file)
                num_input_records += in_cnt
                num_output_records += out_cnt
        else:
            executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers)
            try:
                futures = [
                    executor.submit(self._process_input_file, input_file)
                    for input_file in self._input_files
                ]
                concurrent.futures.wait(futures)
                for future in futures:
                    in_cnt, out_cnt = future.result()
                    num_input_records += in_cnt
                    num_output_records += out_cnt
            finally:
                # shutdown(wait=True) joins all worker threads before proceeding.
                executor.shutdown(wait=True)

        reader_counters_str = self._reader_counters.get_counters_string()
        writer_counters_str = self._writer.counters().get_counters_string()
        self.close()
        logging.info(
            f'Sharded {num_input_records} records from {len(self._input_files)} files '
            f'into {len(self._writer.files())} shards with {num_output_records} records.\n'
            f'Reader {reader_counters_str}\n'
            f'Writer {writer_counters_str}'
        )


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
    # uncomment to run pprof
    # start_pprof_server(port=8123)

    if not _FLAGS.shard_input:
        logging.fatal('Specify files to be sharded with --shard_input')
    shard_file(_FLAGS.shard_input, _FLAGS.shard_output)


if __name__ == '__main__':
    app.run(main)
