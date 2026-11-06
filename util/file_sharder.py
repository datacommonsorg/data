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
after '=' is a fixed value, format template, or Python expression with the
input columns as variables and the `eval_functions` helpers such as
`format_date`:
  --shard_output_columns="dcid;value=int(v) * 100;label=f'{dcid}-{year}';date=format_date(d, '%Y-%m');typeOf='dcs:StatVarObservation'"
Default values are added before the output columns are computed.

To convert an observation CSV directly to sharded MCF files while dropping
`#input`, adding `typeOf=dcid:StatVarObservation`, and auto-generating the
`StatVarObservation` DCID:
  --shard_input=observations.csv --shard_output=obs@10.mcf \
  --shard_ignore_columns="#input" \
  --shard_add_columns="Node;typeOf=dcid:StatVarObservation"

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
import re
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
from dcid_generator import (
    DCID_IGNORE_PROPS,
    generate_node_dcid,
    generate_place_dcid,
    generate_statvar_obs_dcid,
    get_long_id,
    get_sha256_long_id,
)
import file_util
from file_dict_io import (
    FileDictIO,
    ShardedFileDictIO,
    get_default_shard_config as get_base_shard_config,
    get_record_dcid,
    is_avro_file,
    is_csv_file,
    is_json_file,
    is_jsonl_file,
    is_mcf_file,
    open_dict_file,
    record_to_canonical_str,
    str_to_int_hash,
)
import mcf_file_util
from eval_functions import EVAL_GLOBALS, evaluate_statement

# Defaults
_DEFAULT_RECORDS_PER_SHARD = 100000
_DEFAULT_SHARD_FILENAME = 'shard-{index:05}-of-{shard_count:05d}'
_DEFAULT_MIN_CHUNK_SIZE = 32 * 1024 * 1024
_DEFAULT_SHARD_THREADS = max(1, (os.cpu_count() or 1) // 2)
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

_DCID_IGNORE_PROPS = DCID_IGNORE_PROPS

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
flags.DEFINE_integer(
    'shard_threads', _DEFAULT_SHARD_THREADS,
    'Maximum number of parallel threads for reading inputs. Defaults to 50% '
    'of available CPU cores.')
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
    'value, "*" to copy all non-ignored input columns, or '
    '<column>=<expression>, a fixed value, format template, or Python '
    'expression with the input columns as variables. Example: '
    '"dcid;value=int(v)*2;label=f\'{id}-{year}\';typeOf=\'StatVarObservation\'".'
)
flags.DEFINE_string(
    'shard_add_columns', '',
    'Columns to add or override in output records while keeping non-ignored '
    'input columns, separated by ";", each as <column> or '
    '<column>=<value_or_expression>. Example: '
    '"dcid;typeOf=dcid:StatVarObservation;observationAbout=dcid:geoId/{fips}".')
flags.DEFINE_list(
    'shard_ignore_columns', [],
    'Column names or regular expressions (e.g. "#input,^#.*") to exclude '
    'from output records.')
flags.DEFINE_string(
    'shard_encoding', None,
    'Optional character encoding for reading text-based input files.')

_FORMAT_PLACEHOLDER_RE = re.compile(r'\{([A-Za-z_][A-Za-z0-9_]*)\}')
_IDENTIFIER_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_UNQUOTED_CURIE_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*:[A-Za-z0-9_./:-]+$')
_UNQUOTED_PATH_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)/[A-Za-z0-9_./:-]+$')
_SIMPLE_CONSTANT_RE = re.compile(r'^[^\s\'"()\[\]{}]+$')

# Backward-compatible helper alias for existing tests
_get_long_id = get_sha256_long_id


def _compile_ignore_patterns(patterns: list | str | None,
                             is_mcf_output: bool = False) -> list[re.Pattern]:
    """Compiles column ignore regular expressions, defaulting `#.*` for MCF output."""
    raw_patterns = [str(p) for p in _parse_list(patterns) if p]
    if (is_mcf_output and r'#.*' not in raw_patterns and
            '^#.*' not in raw_patterns):
        raw_patterns.append(r'#.*')
    return [re.compile(p) for p in raw_patterns]


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
    if not isinstance(filename, str) or not file_util.file_is_local(filename):
        return False
    lower = filename.lower()
    if lower.endswith(('.gz', '.bz2', '.zst', '.xz', '.zip', '.tgz', '.tar')):
        return False
    if file_util.file_is_google_spreadsheet(filename):
        return False
    return (is_avro_file(filename) or is_mcf_file(filename) or
            is_jsonl_file(filename) or is_csv_file(filename))


# Backward compatibility alias
is_splittable_file = is_seekable_file


def _get_flag_value(name: str):
    """Returns the flag value for `name` without mutating global parsed state."""
    flag = _FLAGS[name]
    return flag.value if _FLAGS.is_parsed() else flag._value


def get_default_shard_config() -> dict:
    """Returns the default config for sharding based on command-line flags."""
    config = get_base_shard_config()
    config.update({
        'shard_key': _get_flag_value('shard_key'),
        'shard_key_prefix_length': _get_flag_value('shard_key_prefix_length'),
        'shard_count': _get_flag_value('shard_count'),
        'records_per_shard': _get_flag_value('records_per_shard'),
        'shard_skip_duplicates': _get_flag_value('shard_skip_duplicates'),
        'shard_input_records': _get_flag_value('shard_input_records'),
        'shard_headers': _get_flag_value('shard_headers'),
        'shard_sample_rate': _get_flag_value('shard_sample_rate'),
        'shard_threads': _get_flag_value('shard_threads'),
        'shard_min_chunk_size': _get_flag_value('shard_min_chunk_size'),
        'shard_default_pvs': _get_flag_value('shard_default_pvs'),
        'shard_generate_dcid': _get_flag_value('shard_generate_dcid'),
        'shard_dcid_ignore_props': _get_flag_value('shard_dcid_ignore_props'),
        'shard_output_columns': _get_flag_value('shard_output_columns'),
        'shard_add_columns': _get_flag_value('shard_add_columns'),
        'shard_ignore_columns': _get_flag_value('shard_ignore_columns'),
        'shard_encoding': _get_flag_value('shard_encoding'),
    })
    return config


class FileSharder:
    """Shards input dictionary files into output shards using `ShardedFileDictIO`.

    Reads multiple input files in parallel with a separate `FileDictIO` reader
    per input file, applying default property values (`shard_default_pvs`),
    added/overridden columns (`shard_add_columns`), output column selection and
    expressions (`shard_output_columns`), regex column exclusion
    (`shard_ignore_columns`), deterministic DCID generation
    (`shard_generate_dcid`), shard-independent deduplication
    (`shard_skip_duplicates`), deterministic key sampling (`shard_sample_rate`),
    and record limits (`shard_input_records`), while writing to output shards
    through `ShardedFileDictIO`.

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
        self._encoding = (self._config.get('shard_encoding') or
                          self._config.get('encoding') or None)
        self._lock = threading.Lock()
        self._dedup_locks = [
            threading.Lock() for _ in range(_NUM_DEDUP_BUCKETS)
        ]
        self._records_seen_buckets: list[set[int]] = [
            set() for _ in range(_NUM_DEDUP_BUCKETS)
        ]
        self._num_input_records: int = 0
        self._num_workers: int = 1
        self._input_files = ShardedFileDictIO.resolve_input_files(input_files)
        if not self._output_path and self._input_files:
            self._output_path = self._input_files[0]

        self._default_pvs = _parse_default_pvs(
            self._config.get('shard_default_pvs') or
            self._config.get('default_pvs'))
        self._output_pvs = _parse_output_columns(
            self._config.get('shard_output_columns') or
            self._config.get('output_columns'))
        self._add_pvs = _parse_output_columns(
            self._config.get('shard_add_columns') or
            self._config.get('add_columns'))
        self._generate_dcid = bool(
            self._config.get('shard_generate_dcid') or
            self._config.get('generate_dcid', False) or
            is_mcf_file(self._output_path) or
            any(col in ('dcid', 'Node') and not expr
                for col, expr in (list(self._add_pvs.items()) +
                                  list(self._output_pvs.items()))))
        extra_ignore_props = _parse_list(
            self._config.get('shard_dcid_ignore_props') or
            self._config.get('dcid_ignore_props'))
        self._dcid_ignore_props = frozenset(_DCID_IGNORE_PROPS |
                                            set(extra_ignore_props))

        configured_headers = list(self._config.get('shard_headers') or [])
        self._headers = list(configured_headers)
        self._shard_key = self._config.get('shard_key') or None
        if self._input_files and not self._headers:
            with open_dict_file(self._input_files[0],
                                mode='r',
                                encoding=self._encoding) as preview_reader:
                preview_headers = preview_reader.headers()
                if not preview_headers and not (is_mcf_file(
                        self._output_path) or is_json_file(self._output_path)):
                    seen_cols = {}
                    for _ in range(1000):
                        sample_rec = preview_reader.next()
                        if sample_rec is None:
                            break
                        for k in sample_rec.keys():
                            if (k is not None and not str(k).startswith('#') and
                                    k not in seen_cols):
                                seen_cols[k] = None
                    preview_headers = list(seen_cols.keys())
                if preview_headers:
                    self._headers = list(preview_headers)

        self._explicit_output_cols = frozenset(
            [c for c in self._output_pvs if c != '*'] +
            list(self._add_pvs.keys()) + configured_headers)
        self._ignore_column_regexes = _compile_ignore_patterns(
            self._config.get('shard_ignore_columns') or
            self._config.get('ignore_columns'),
            is_mcf_output=is_mcf_file(self._output_path),
        )

        # Input headers are used to estimate the number of input records.
        self._input_headers = list(self._headers)
        if self._headers or self._output_pvs or self._add_pvs:
            self._headers = self._get_output_headers(self._headers)

        raw_estimate = self.get_input_records_estimate()
        max_records = int(self._config.get('shard_input_records', sys.maxsize))
        if 0 <= max_records < sys.maxsize:
            raw_estimate = min(raw_estimate, max_records)

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
            # shards for the expected number of records after limits & sampling.
            'estimated_num_records':
                round(raw_estimate * self._sample_rate),
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

    @staticmethod
    def _has_valid_dcid(record: dict) -> bool:
        """Returns True if `record` has a non-empty `dcid` or `Node` that is not an `l:` local ref."""
        if not record:
            return False
        for prop in ('dcid', 'Node'):
            raw = str(record.get(prop) or '').strip(' "')
            if not raw:
                continue
            if raw.startswith('l:'):
                continue
            cleaned = mcf_file_util.strip_namespace(raw).strip(' "')
            if cleaned and not cleaned.startswith('l:'):
                return True
        return False

    @staticmethod
    def _is_schema_record(record: dict) -> bool:
        """Returns True if `record` has Data Commons schema or observation properties."""
        if not record:
            return False
        if 'dcid' in record or 'Node' in record or 'typeOf' in record:
            return True
        if 'observationAbout' in record and 'variableMeasured' in record:
            return True
        if 'measuredProperty' in record and ('populationType' in record or
                                             'popType' in record):
            return True
        return False

    def maybe_generate_dcid(self, record: dict) -> str:
        """Generates and sets `dcid` (or `Node`) on `record` if missing and `shard_generate_dcid` is enabled.

        A record already has a dcid if its `dcid`, or else its `Node`, has a
        value, so a record with a blank `dcid` keeps its existing `Node`.
        """
        existing_dcid = get_record_dcid(record)
        if self._has_valid_dcid(record):
            return existing_dcid
        generated = generate_node_dcid(record, self._dcid_ignore_props)
        if not generated:
            return ''
        if ('Node' in record or is_mcf_file(self._output_path) or
            (self._headers and 'Node' in self._headers)):
            record['Node'] = mcf_file_util.add_namespace(generated)
        else:
            record['dcid'] = generated
        return generated

    def _get_record_shard_key(self,
                              record: dict,
                              key_record: dict = None,
                              always_resolve: bool = False) -> str | None:
        """Returns the shard routing key for `record`, generating a DCID when needed for schema records."""
        target = key_record if key_record is not None else record
        if not self._writer._shard_by_column_value and (
                self._shard_key is None or self._shard_key in ('dcid', 'Node')):
            key = None
            if self._has_valid_dcid(target):
                key = get_record_dcid(target)
            elif (self._shard_key in ('dcid', 'Node') or
                  self._is_schema_record(target)):
                key = generate_node_dcid(target, self._dcid_ignore_props)
            if key:
                prefix_len = self._writer._shard_key_prefix_length
                if prefix_len > 0:
                    key = key[:prefix_len]
                return key
        if always_resolve:
            return self._writer.get_key_for_record(target)
        return None

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

    def _is_ignored_column(self, col: str) -> bool:
        """Returns True if `col` matches any `shard_ignore_columns` regex."""
        if col is None:
            return False
        col_str = str(col)
        if col_str in self._explicit_output_cols:
            return False
        return any(
            regex.fullmatch(col_str) for regex in self._ignore_column_regexes)

    def filter_ignored_columns(self, record: dict) -> dict:
        """Removes any columns matching `shard_ignore_columns` from `record`."""
        if not self._ignore_column_regexes:
            return record
        return {
            col: val
            for col, val in record.items()
            if not self._is_ignored_column(col)
        }

    def _evaluate_column_spec(self,
                              prop: str,
                              expr: str,
                              record: dict,
                              counters: Counters = None,
                              allow_unquoted_constant: bool = False):
        """Evaluates `<prop>=<expr>` as a format template, constant, column copy, or Python expression."""
        if (not any(ch in expr for ch in ("'", '"', '(', ')')) and
                '.format(' not in expr):
            placeholders = _FORMAT_PLACEHOLDER_RE.findall(expr)
            if placeholders:
                remainder = _FORMAT_PLACEHOLDER_RE.sub('', expr)
                if '{' not in remainder and '}' not in remainder:
                    if any(record.get(ph) in (None, '') for ph in placeholders):
                        if counters is not None:
                            counters.add_counter('shard-output-column-errors',
                                                 1)
                        return None
                    return _FORMAT_PLACEHOLDER_RE.sub(
                        lambda m: str(record[m.group(1)]), expr)

        if _UNQUOTED_CURIE_RE.match(expr):
            return expr

        if allow_unquoted_constant:
            path_match = _UNQUOTED_PATH_RE.match(expr)
            if path_match:
                prefix = path_match.group(1)
                if prefix not in record and prefix not in self._input_headers:
                    return expr

        if _IDENTIFIER_RE.match(expr):
            if expr in record:
                return record[expr]
            if (allow_unquoted_constant and expr not in self._input_headers and
                    expr not in EVAL_GLOBALS and
                    expr not in ('True', 'False', 'None')):
                return expr

        # Pass 'prop=expr' so evaluate_statement splits at the first
        # '=' and the expression can contain '=', as in 'a == b'.
        _, value = evaluate_statement(f'{prop}={expr}', {
            'record': record,
            **record
        })
        if (value is None and allow_unquoted_constant and
                not _IDENTIFIER_RE.match(expr) and
                _SIMPLE_CONSTANT_RE.match(expr)):
            return expr
        if value is None and counters is not None:
            counters.add_counter('shard-output-column-errors', 1)
        return value

    def apply_add_columns(self,
                          record: dict,
                          counters: Counters = None) -> dict:
        """Adds or overrides columns configured in `shard_add_columns` on `record`."""
        if not self._add_pvs:
            return record
        for prop, expr in self._add_pvs.items():
            if not expr:
                if prop in ('dcid', 'Node') and prop not in record:
                    record[prop] = ''
                continue
            value = self._evaluate_column_spec(prop,
                                               expr,
                                               record,
                                               counters=counters,
                                               allow_unquoted_constant=True)
            if value is not None:
                record[prop] = value
        return record

    def _get_output_headers(self, input_headers: list) -> list:
        """Returns the output shard headers for records with `input_headers`.

        With `shard_output_columns`, the headers are the output columns
        (expanding `*` to non-ignored `input_headers`). Otherwise they are
        non-ignored `input_headers` plus any `shard_default_pvs` and
        `shard_add_columns`. For CSV-style headers, `dcid` is added first if
        `shard_generate_dcid` is enabled and there is no `dcid` or `Node`
        column. MCF file comment headers (where all lines start with `#`) are
        returned as is.
        """
        is_mcf_comment_headers = bool(input_headers) and all(
            str(h).startswith('#') for h in input_headers)
        if is_mcf_comment_headers and not self._output_pvs and not self._add_pvs:
            return list(input_headers)
        has_input_cols = bool(input_headers) and not is_mcf_comment_headers
        if not has_input_cols and (not self._output_pvs or
                                   '*' in self._output_pvs):
            if is_mcf_comment_headers and is_mcf_file(self._output_path):
                return list(input_headers)
            return []

        filtered_input_headers = [
            h for h in (input_headers or [])
            if not is_mcf_comment_headers and not self._is_ignored_column(h)
        ]

        if self._output_pvs:
            headers = []
            for col in self._output_pvs:
                if col == '*':
                    for h in filtered_input_headers:
                        if h not in headers:
                            headers.append(h)
                    for prop in self._add_pvs:
                        if prop not in headers:
                            headers.append(prop)
                elif col not in headers:
                    headers.append(col)
        else:
            headers = list(filtered_input_headers)
            if not headers and not self._add_pvs:
                return headers
            for prop in self._default_pvs:
                if prop not in headers and not self._is_ignored_column(prop):
                    headers.append(prop)
            if (self._generate_dcid and 'dcid' not in headers and
                    'Node' not in headers):
                id_col = ('Node' if (is_mcf_file(self._output_path) or
                                     ('Node' in self._add_pvs and
                                      'dcid' not in self._add_pvs)) else 'dcid')
                headers.insert(0, id_col)
            for prop in self._add_pvs:
                if prop not in headers:
                    headers.append(prop)
        if (self._generate_dcid and 'dcid' not in headers and
                'Node' not in headers):
            id_col = ('Node' if (is_mcf_file(self._output_path) or
                                 ('Node' in self._add_pvs and
                                  'dcid' not in self._add_pvs)) else 'dcid')
            headers.insert(0, id_col)
        return headers

    def get_output_record(self,
                          record: dict,
                          counters: Counters = None) -> dict:
        """Returns a record with only the `shard_output_columns` and without ignored columns.

        A column without an expression (`'col'`) gets the input value of
        `col` (or `''` for `dcid`/`Node` so automatic DCID generation can
        populate it). `'*'` expands to all non-ignored columns in `record`.
        A column with `<col>=<expr>` evaluates format templates (`{col}`),
        unquoted CURIE constants (`dcid:StatVarObservation`), or Python
        expressions via `eval_functions.evaluate_statement`.

        Args:
          record: Input record.
          counters: Optional `Counters` to count expressions that failed, as
            `shard-output-column-errors`.

        Returns:
          New dict with the output columns, in the configured order.
        """
        if not self._output_pvs:
            return self.filter_ignored_columns(record)
        output_record = {}
        eval_record = dict(record)
        for prop, expr in self._output_pvs.items():
            if prop == '*':
                for col, val in record.items():
                    if (not self._is_ignored_column(col) and
                            col not in output_record):
                        output_record[col] = val
                        eval_record[col] = val
                continue
            if not expr:
                value = eval_record.get(prop)
                if value is None and prop in ('dcid', 'Node'):
                    output_record[prop] = ''
                    eval_record[prop] = ''
                    continue
            else:
                value = self._evaluate_column_spec(
                    prop,
                    expr,
                    eval_record,
                    counters=counters,
                    allow_unquoted_constant=False)
            if value is not None:
                output_record[prop] = value
                eval_record[prop] = value
        return self.filter_ignored_columns(output_record)

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
        add_pvs = self._add_pvs
        generate_dcid = self._generate_dcid
        has_column_filter = bool(self._output_pvs or
                                 self._ignore_column_regexes)

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
                encoding=self._encoding,
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
                pre_filter_record = dict(
                    record) if has_column_filter else record
                if add_pvs:
                    self.apply_add_columns(record, file_counters)
                    file_counters.add_counter('shard-add-columns-applied', 1)
                if self._output_pvs:
                    record = self.get_output_record(record, file_counters)
                elif self._ignore_column_regexes:
                    record = self.filter_ignored_columns(record)

                if generate_dcid or (('dcid' in record or 'Node' in record) and
                                     not self._has_valid_dcid(record)):
                    had_valid_dcid = self._has_valid_dcid(record)
                    prev_dcid = get_record_dcid(record)
                    new_dcid = self.maybe_generate_dcid(record)
                    if new_dcid and (not had_valid_dcid or
                                     new_dcid != prev_dcid):
                        file_counters.add_counter('shard-dcid-generated', 1)

                if skip_duplicates and self.is_duplicate_record(record):
                    file_counters.add_counter('shard-duplicate-dropped', 1)
                    continue

                if not self._headers:
                    with self._lock:
                        if not self._headers:
                            inferred_headers = self._get_output_headers([
                                prop for prop in pre_filter_record.keys()
                                if prop is not None and
                                not str(prop).startswith('#')
                            ])
                            self._headers = inferred_headers or [
                                prop for prop in record.keys()
                                if prop is not None and
                                not str(prop).startswith('#')
                            ]
                            self._writer.set_headers(self._headers)

                key_record = ({
                    **pre_filter_record,
                    **record
                } if (has_column_filter and self._shard_key) else record)
                key = self._get_record_shard_key(
                    record,
                    key_record=key_record,
                    always_resolve=sample_enabled or has_column_filter,
                )
                if sample_enabled and not self.should_sample_key(key):
                    file_counters.add_counter('shard-sampled-dropped', 1)
                    continue

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

        shard_threads = int(
            self._config.get('shard_threads') or _DEFAULT_SHARD_THREADS)
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
    try:
        file_sharder.process()
    finally:
        file_sharder.close()


def main(_):
    # uncomment to run pprof
    # start_pprof_server(port=8123)

    if not _FLAGS.shard_input:
        logging.fatal('Specify files to be sharded with --shard_input')
    shard_file(_FLAGS.shard_input, _FLAGS.shard_output)


if __name__ == '__main__':
    app.run(main)
