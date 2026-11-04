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

To add default values for properties that are missing or empty, separate the
properties with ';' (a value can be a comma separated list):
  --shard_default_pvs="typeOf:dcs:StatVarObservation;measurementMethod=dcs:A,dcs:B"

To emit only some columns, or columns computed from other columns, separate
the columns with ';'. A column without '=' copies the input value; anything
after '=' is a Python expression with the input columns as variables and the
`eval_functions` helpers such as `format_date`:
  --shard_output_columns="dcid;value=int(v) * 100;label=f'{dcid}-{year}';date=format_date(d, '%Y-%m');typeOf='dcs:StatVarObservation'"
Default values are added before the output columns are computed.

Example usage within a Python script:
  import file_sharder

  shard_configs = {
      'shard_key': 'observationAbout',
      'shard_count': 100,
      'shard_default_pvs': 'unit:dcs:Count',
      'shard_output_columns': "observationAbout;value=float(value);unit",
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
import file_util
from file_dict_io import (
    FileDictIO,
    ShardedFileDictIO,
    get_default_shard_config as get_base_shard_config,
    get_record_dcid,
    is_avro_file,
    is_csv_file,
    is_jsonl_file,
    is_mcf_file,
    open_dict_file,
    record_to_canonical_str,
    str_to_int_hash,
)
import mcf_file_util
from eval_functions import evaluate_statement

# Defaults
_DEFAULT_RECORDS_PER_SHARD = 100000
_DEFAULT_SHARD_FILENAME = 'shard-{index:05}-of-{shard_count:05d}'
_DEFAULT_MIN_CHUNK_SIZE = 32 * 1024 * 1024
_NUM_DEDUP_BUCKETS = 64
# Number of input records between updates to the global progress counters.
_PROGRESS_BATCH_SIZE = 100000
# Separator between property-value items in `shard_default_pvs` and
# `shard_output_columns`. Not ',', since a value can be a comma separated list.
_PV_ITEM_SEPARATOR = ';'

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
flags.DEFINE_integer(
    'shard_min_chunk_size', _DEFAULT_MIN_CHUNK_SIZE,
    'Minimum byte size of chunks when splitting a file across parallel workers.'
)
flags.DEFINE_string(
    'shard_default_pvs', '',
    'Default property values to add to a record when the property is missing '
    'or empty, separated by ";", each as <property>:<value> or '
    '<property>=<value>. A value can be a comma separated list. Example: '
    '"typeOf:dcs:StatVarObservation;measurementMethod=dcs:A,dcs:B".')
flags.DEFINE_bool(
    'shard_generate_dcid', False,
    'Generate a deterministic dcid for records that do not have a dcid/Node.')
flags.DEFINE_list(
    'shard_dcid_ignore_props', [],
    'Additional properties to ignore when generating a dcid for a record.')

flags.DEFINE_string(
    'shard_output_columns', None,
    'Output columns separated by ";", each as <column> to copy the input '
    'value, or <column>=<expression>, a Python expression with the input '
    'columns as variables. Example: '
    '"dcid;value=int(v)*2;label=f\'{id}-{year}\';typeOf=\'StatVarObservation\'".'
)


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
      2. Values: the properties are normalized with
         `mcf_file_util.normalize_mcf_node(props, quantity_range_to_dcid=True)`
         and each normalized value is converted to a string. That normalizes
         each value with `mcf_file_util.normalize_value`:
         - A value with `,` is a list: items are split (as CSV if the value
           has `"`), normalized, deduplicated, sorted and joined with `,`,
           so `dcs:B, A` becomes `dcid:A,dcid:B`. A quoted list with `{` or
           `[` is kept as is.
         - A quantity range `[10 20 Years]` becomes `dcid:Years10To20`.
         - A number is written without trailing zeros: `1.0` becomes `1`.
         - A value with a space, or a quoted value, is enclosed in `"`. A
           quoted value longer than 100 characters is kept as is.
         - Any other value gets the `dcid:` namespace instead of its own, and
           `__` separated parts are sorted: `a__c__b` becomes `dcid:a__b__c`.
      3. Key: the JSON array of `[property, value]` pairs sorted by property
         (Unicode code point order), with no whitespace, for example
         `[["observationAbout","dcid:geoId/06"],["value","39538223"]]`. Only `"`,
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

    props = {}
    for prop, raw_val in record.items():
        if not prop or str(prop).startswith('#') or prop in ignore_props:
            continue
        val_str = '' if raw_val is None else str(raw_val).strip(' "')
        if not val_str:
            continue
        if val_str.startswith('l:'):
            return ''
        # normalize_mcf_node reads Node and dcid as strings.
        props[prop] = str(raw_val) if prop in ('Node', 'dcid') else raw_val

    if not props:
        return ''

    normalized = mcf_file_util.normalize_mcf_node(props,
                                                  quantity_range_to_dcid=True)
    pairs = [[prop, str(val)] for prop, val in sorted(normalized.items())]

    # JSON keeps the property and value boundaries unambiguous. Joining
    # 'prop=value' strings gave {'a': 'b', 'c': 'd'} and {'a': 'bc=d'} the
    # same key.
    key_string = json.dumps(pairs, ensure_ascii=False, separators=(',', ':'))
    prefix = 'dc/o/' if type_of == 'StatVarObservation' else 'dc/'
    return f'{prefix}{_get_long_id(key_string)}'


def _parse_list(value: list | str | None, sep: str = ',') -> list:
    """Returns `value` as a list, splitting a string on `sep` and dropping empty items."""
    if not value:
        return []
    if isinstance(value, str):
        value = value.split(sep)
    return [
        item.strip() if isinstance(item, str) else item
        for item in value
        if not isinstance(item, str) or item.strip()
    ]


def _parse_pvs(pvs: dict | list | str | None,
               pv_seps: str,
               require_value: bool = False,
               item_sep: str = _PV_ITEM_SEPARATOR) -> dict[str, str]:
    """Parses property-value pairs from a dict, a list, or a string.

    Args:
      pvs: A dict of property to value, a list of `'<prop><sep><value>'`
        strings, or a string of them separated by `item_sep`.
      pv_seps: Characters that separate a property from its value. The first
        one found in an item is used, so the value can contain any of them:
        with `pv_seps=':='`, `'typeOf=dcs:Place'` is `typeOf` and `dcs:Place`.
      require_value: If True, items without a separator are ignored.
        Otherwise they get an empty value.
      item_sep: Separator between items in a string. Defaults to `';'`, so
        values can be comma separated lists.

    Returns:
      Dict of property to value, in the order given.
    """
    if not pvs:
        return {}
    if isinstance(pvs, dict):
        items = pvs.items()
    else:
        items = []
        for item in _parse_list(pvs, item_sep):
            if not isinstance(item, str):
                continue
            positions = [p for p in (item.find(s) for s in pv_seps) if p >= 0]
            if positions:
                pos = min(positions)
                items.append((item[:pos], item[pos + 1:]))
            elif not require_value:
                items.append((item, ''))
    parsed = {}
    for prop, val in items:
        prop = str(prop).strip()
        if prop:
            parsed[prop] = '' if val is None else str(val).strip()
    return parsed


def _parse_default_pvs(default_pvs: dict | list | str | None) -> dict[str, str]:
    """Parses `shard_default_pvs` into a dict of property to default value.

    Args:
      default_pvs: A dict of property to value, a list of `'<prop>:<value>'`
        or `'<prop>=<value>'` strings, or a string of them separated by `;`,
        such as `'typeOf:dcs:StatVarObservation;measurementMethod=dcs:A,dcs:B'`.
        The first `:` or `=` separates the property from the value, and the
        value can be a comma separated list. Items without a value are
        ignored.

    Returns:
      Dict of property to default value, in the order given.
    """
    return _parse_pvs(default_pvs, pv_seps=':=', require_value=True)


def _parse_output_columns(columns: dict | list | str | None) -> dict[str, str]:
    """Parses `shard_output_columns` into a dict of output column to expression.

    Args:
      columns: A dict of column to expression, a list of `'<column>'` or
        `'<column>=<expression>'` strings, or a string of them separated by
        `;`, such as `"id;v2=int(v) * 2;label=f'{id}-{year}'"`. Everything
        after the first `=` is the expression, so it can contain `=`, `:` and
        `,`, but not `;`.

    Returns:
      Dict of output column to its expression (`''` to copy the input
      column), in the order given.
    """
    return _parse_pvs(columns, pv_seps='=')


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


def _merge_counters(source: Counters, *targets: Counters):
    """Adds the additive counters in `source` to each of `targets`.

    Skips `processed`, which `FileSharder` adds to the global counters as
    input records are read, and non-additive counters such as timestamps and
    rates (see `_is_additive_counter`).
    """
    for name, count in source.get_counters().items():
        if name == 'processed' or not _is_additive_counter(name, count):
            continue
        for target in targets:
            target.add_counter(name, count)


def is_seekable_file(filename: str) -> bool:
    """Returns True if the file format supports parallel chunk reading via seek()."""
    if not isinstance(filename, str):
        return False
    lower = filename.lower()
    if lower.endswith(('.gz', '.bz2', '.zst', '.zip', '.tgz', '.tar')):
        return False
    if file_util.file_is_google_spreadsheet(filename):
        return False
    return (is_avro_file(lower) or is_mcf_file(lower) or is_jsonl_file(lower) or
            is_csv_file(lower))


# Backward compatibility alias
is_splittable_file = is_seekable_file


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
        'shard_min_chunk_size': _FLAGS.shard_min_chunk_size,
        'shard_default_pvs': _FLAGS.shard_default_pvs,
        'shard_generate_dcid': _FLAGS.shard_generate_dcid,
        'shard_dcid_ignore_props': _FLAGS.shard_dcid_ignore_props,
        'shard_output_columns': _FLAGS.shard_output_columns,
    })
    return config


class FileSharder:
    """Shards input dictionary files into output shards using `ShardedFileDictIO`.

    Reads multiple input files in parallel with a separate `FileDictIO` reader
    per input file, applying default property values (`shard_default_pvs`),
    output column selection and expressions (`shard_output_columns`),
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
        self._reader_counters = Counters(options=CounterOptions(
            show_every_n_sec=0))
        self._writer_counters = Counters(options=CounterOptions(
            show_every_n_sec=0))
        self._output_path = (output_path or
                             self._config.get('shard_output_path') or '')
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
        self._output_pvs = _parse_output_columns(
            self._config.get('shard_output_columns'))
        self._generate_dcid = bool(
            self._config.get('shard_generate_dcid') or
            self._config.get('generate_dcid', False))
        extra_ignore_props = _parse_list(
            self._config.get('shard_dcid_ignore_props') or
            self._config.get('dcid_ignore_props'))
        self._dcid_ignore_props = frozenset(_DCID_IGNORE_PROPS |
                                            set(extra_ignore_props))

        self._input_files = ShardedFileDictIO.resolve_input_files(input_files)
        self._headers = list(self._config.get('shard_headers') or [])
        self._shard_key = self._config.get('shard_key') or None
        if self._input_files and not self._headers:
            with open_dict_file(self._input_files[0],
                                mode='r') as preview_reader:
                preview_headers = preview_reader.headers()
                if preview_headers:
                    self._headers = list(preview_headers)

        if not self._output_path and self._input_files:
            self._output_path = self._input_files[0]

        # Input headers are used to estimate the number of input records.
        self._input_headers = list(self._headers)
        if self._headers or self._output_pvs:
            self._headers = self._get_output_headers(self._headers)

        writer_config = {
            'shard_key':
                self._shard_key,
            'shard_key_prefix_length':
                self._config.get('shard_key_prefix_length', 0),
            'shard_count':
                self._config.get('shard_count', 0),
            'records_per_shard':
                self._config.get('records_per_shard',
                                 _DEFAULT_RECORDS_PER_SHARD),
            'shard_headers':
                self._headers,
            # Used to derive shard_count from records_per_shard, so size the
            # shards for the expected number of records after sampling.
            'estimated_num_records':
                round(self.get_input_records_estimate() * self._sample_rate),
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
            _merge_counters(writer_counters, self._counters)
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

        Uses the record fingerprint (`record_to_canonical_str`), so
        equivalent nodes with different property ordering or value list ordering
        are recognized as duplicates. Uses hash-bucketed locks (`_NUM_DEDUP_BUCKETS`)
        keyed by the record fingerprint hash so duplicate detection is completely
        independent of `shard_index` while remaining lock-contention-free across
        worker threads.
        """
        record_hash = str_to_int_hash(record_to_canonical_str(record))
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
                                                        self._input_headers)

    def _get_output_headers(self, input_headers: list) -> list:
        """Returns the output shard headers for records with `input_headers`.

        With `shard_output_columns`, the headers are the output columns.
        Otherwise they are `input_headers` plus any `shard_default_pvs`. For
        CSV-style headers, `dcid` is added first if `shard_generate_dcid` is
        set and there is no `dcid` or `Node` column. MCF comment headers
        (starting with `#`) are returned as is.
        """
        if self._output_pvs:
            headers = list(self._output_pvs)
        else:
            headers = list(input_headers)
            if not headers or str(headers[0]).startswith('#'):
                return headers
            for prop in self._default_pvs:
                if prop not in headers:
                    headers.append(prop)
        if (self._generate_dcid and 'dcid' not in headers and
                'Node' not in headers):
            headers.insert(0, 'dcid')
        return headers

    def get_output_record(self,
                          record: dict,
                          counters: Counters = None) -> dict:
        """Returns a record with only the `shard_output_columns`.

        A column without an expression (`'col'`) gets the input value of
        `col`. A column with an expression (`'v2=int(v) * 2'`) gets the result
        of `eval_functions.evaluate_statement`, with the input columns as
        variables and the `eval_functions` helpers such as `format_date` and
        `str_to_camel_case`. Constants must be quoted (`"typeOf='Place'"`),
        and f-strings combine columns (`"label=f'{id}-{year}'"`). A column is
        left out if it has no value or its expression fails.

        Args:
          record: Input record.
          counters: Optional `Counters` to count expressions that failed, as
            `shard-output-column-errors`.

        Returns:
          New dict with the output columns, in the configured order.
        """
        output_record = {}
        for prop, expr in self._output_pvs.items():
            if not expr:
                value = record.get(prop)
            else:
                # Pass 'prop=expr' so evaluate_statement splits at the first
                # '=' and the expression can contain '=', as in 'a == b'.
                _, value = evaluate_statement(f'{prop}={expr}', record)
                if value is None and counters is not None:
                    counters.add_counter('shard-output-column-errors', 1)
            if value is not None:
                output_record[prop] = value
        return output_record

    def _generate_input_tasks(
            self, max_threads: int) -> list[tuple[str, int, int | None]]:
        """Generates worker tasks (filename, start_offset, end_offset).

        Seekable files whose size is at least 2 * shard_min_chunk_size are
        divided into byte chunks across available worker threads. Non-seekable
        files or files smaller than the chunk threshold are read as a single
        task (filename, 0, None).
        """
        min_chunk_size = int(
            self._config.get('shard_min_chunk_size') or _DEFAULT_MIN_CHUNK_SIZE)
        if min_chunk_size <= 0:
            min_chunk_size = _DEFAULT_MIN_CHUNK_SIZE

        seekable_count = sum(
            1 for f in self._input_files if is_seekable_file(f))
        non_seekable_count = len(self._input_files) - seekable_count
        self._counters.set_counter('shard-seekable-files', seekable_count)
        self._reader_counters.set_counter('shard-seekable-files',
                                          seekable_count)
        self._counters.set_counter('shard-non-seekable-files',
                                   non_seekable_count)
        self._reader_counters.set_counter('shard-non-seekable-files',
                                          non_seekable_count)

        if max_threads <= 1:
            self._counters.set_counter('shard-chunks', len(self._input_files))
            self._reader_counters.set_counter('shard-chunks',
                                              len(self._input_files))
            return [(f, 0, None) for f in self._input_files]

        tasks = []
        for input_file in self._input_files:
            if not is_seekable_file(input_file):
                tasks.append((input_file, 0, None))
                continue

            file_size = file_util.file_get_size(input_file)
            if file_size is None or file_size < min_chunk_size * 2:
                tasks.append((input_file, 0, None))
                continue

            num_chunks = max(1, min(max_threads, file_size // min_chunk_size))
            if num_chunks <= 1:
                tasks.append((input_file, 0, None))
                continue

            chunk_size = file_size // num_chunks
            for i in range(num_chunks):
                start = i * chunk_size
                end = (i + 1) * chunk_size if i < num_chunks - 1 else None
                tasks.append((input_file, start, end))

        self._counters.set_counter('shard-chunks', len(tasks))
        self._reader_counters.set_counter('shard-chunks', len(tasks))
        return tasks

    def _process_input_file(
        self,
        input_file: str,
        start_offset: int = 0,
        end_offset: int = None,
    ) -> tuple[int, int]:
        """Reads and shards a single `input_file` chunk using its own `FileDictIO` reader."""
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
        if start_offset == 0:
            file_counters.add_counter(
                'total',
                ShardedFileDictIO.estimate_input_records([input_file],
                                                         self._input_headers),
            )
            file_counters.add_counter('shard-input-files', 1)
        file_input_records = 0
        file_output_records = 0
        batch_processed = 0

        with open_dict_file(
                input_file,
                mode='r',
                start_offset=start_offset,
                end_offset=end_offset,
        ) as reader:
            file_headers = reader.headers()
            if file_headers:
                expected_headers = self._get_output_headers(file_headers)
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
                if self._output_pvs:
                    record = self.get_output_record(record, file_counters)

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
            # 'processed' is already added by _add_processed_records().
            _merge_counters(file_counters, self._reader_counters,
                            self._counters)
            if self._reader_counters.get_counter('total') == 0:
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

        total_estimate = self.get_input_records_estimate()
        self._counters.set_counter('total', total_estimate)
        self._reader_counters.set_counter('total', total_estimate)
        self._counters.set_counter('processed', 0)
        self._reader_counters.set_counter('processed', 0)

        num_input_records = 0
        num_output_records = 0

        shard_threads = int(self._config.get('shard_threads') or 1)
        tasks = self._generate_input_tasks(max_threads=shard_threads)
        max_workers = max(1, min(len(tasks), shard_threads))
        self._num_workers = max_workers

        self._counters.set_counter('shard-workers', max_workers)
        self._counters.set_counter('workers', max_workers)
        self._reader_counters.set_counter('shard-workers', max_workers)
        self._reader_counters.set_counter('workers', max_workers)

        self._counters.set_counter('shard-tasks', len(tasks))
        self._reader_counters.set_counter('shard-tasks', len(tasks))
        self._counters.set_counter('shard-tasks-completed', 0)
        self._reader_counters.set_counter('shard-tasks-completed', 0)

        if max_workers == 1:
            for input_file, start_offset, end_offset in tasks:
                in_cnt, out_cnt = self._process_input_file(
                    input_file,
                    start_offset=start_offset,
                    end_offset=end_offset)
                num_input_records += in_cnt
                num_output_records += out_cnt
                self._counters.add_counter('shard-tasks-completed', 1)
                self._reader_counters.add_counter('shard-tasks-completed', 1)
        else:
            executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers)
            try:
                futures = [
                    executor.submit(
                        self._process_input_file,
                        input_file,
                        start_offset=start_offset,
                        end_offset=end_offset,
                    ) for input_file, start_offset, end_offset in tasks
                ]
                for future in concurrent.futures.as_completed(futures):
                    in_cnt, out_cnt = future.result()
                    with self._lock:
                        num_input_records += in_cnt
                        num_output_records += out_cnt
                        self._counters.add_counter('shard-tasks-completed', 1)
                        self._reader_counters.add_counter(
                            'shard-tasks-completed', 1)
            finally:
                # shutdown(wait=True) joins all worker threads before proceeding.
                executor.shutdown(wait=True)

        if num_input_records > self._counters.get_counter('total'):
            self._counters.set_counter('total', num_input_records)
            self._reader_counters.set_counter('total', num_input_records)
        self._counters.set_counter('processed', num_input_records)
        self._reader_counters.set_counter('processed', num_input_records)
        self._counters.set_counter('shard-input-records', num_input_records)
        self._reader_counters.set_counter('shard-input-records',
                                          num_input_records)

        reader_counters_str = self._reader_counters.get_counters_string()
        writer_counters_str = self._writer.counters().get_counters_string()
        self.close()
        logging.info(
            f'Sharded {num_input_records} records from {len(self._input_files)} files '
            f'({len(tasks)} tasks, {max_workers} workers) '
            f'into {len(self._writer.files())} shards with {num_output_records} records.\n'
            f'Reader {reader_counters_str}\n'
            f'Writer {writer_counters_str}')


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
