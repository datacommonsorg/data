# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""BigQuery-based MCF differ for low-memory ($O(1)$ RAM) parallel execution.

Streams current and previous `.mcf` files (local or `gs://` wildcard paths) in
parallel across node-aligned byte-range chunks into normalized observation and
schema CSV shards in bounded memory, loads them into temporary BigQuery tables
(which auto-expire after `--bq_table_ttl_hours`), executes SQL FULL OUTER JOIN
queries to stream complete diff MCF files (`nodes-added.mcf`,
`nodes-deleted.mcf`, `nodes-modified.mcf`, `nodes-original.mcf`), and computes
per-StatVar ADDED/DELETED/MODIFIED counts (`differ_summary.json` and
`differ_summary.csv`) in `--output_location`.

To view all CLI flags, defaults, and usage details (recommended for agents):
  $ python3 tools/import_differ/bigquery_differ.py --help

Standalone CLI Usage:
  $ python3 tools/import_differ/bigquery_differ.py \\
      --current_data="gs://bucket/import/2026_09_17/input0/genmcf/*.mcf" \\
      --previous_data="gs://bucket/import/2026_09_10/input0/genmcf/*.mcf" \\
      --output_location="/tmp/diff_results" \\
      --project_id="datcom-import-automation-prod" \\
      --bq_dataset="datcom_import_differ" \\
      --bq_table_ttl_hours=12

Usage via import_differ.py:
  $ python3 tools/import_differ/import_differ.py \\
      --runner_mode=bigquery \\
      --current_data="gs://bucket/import/2026_09_17/input0/genmcf/*.mcf" \\
      --previous_data="gs://bucket/import/2026_09_10/input0/genmcf/*.mcf" \\
      --output_location="/tmp/diff_results" \\
      --project_id="datcom-import-automation-prod"
"""

import bisect
from collections import defaultdict
import concurrent.futures
import contextlib
import csv
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import fnmatch
import functools
import glob
import io
import multiprocessing
import os
import queue
import re
import sys
import tempfile
import threading
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union
from unittest import mock
import uuid

from absl import app
from absl import flags
from absl import logging
from google.api_core import exceptions as gcp_exceptions
from google.cloud import bigquery
from google.cloud import storage

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
for _path in (
        _SCRIPT_DIR,
        os.path.join(_DATA_DIR, 'util'),
        os.path.join(_DATA_DIR, 'tools', 'statvar_importer'),
):
    if _path not in sys.path:
        sys.path.append(_path)

OBSERVATION_KEY_PROPERTIES = [
    'variableMeasured',
    'observationAbout',
    'observationDate',
    'observationPeriod',
    'measurementMethod',
    'unit',
    'scalingFactor',
]

_OBS_KEY_PROPS_BYTES = tuple(
    prop.encode('ascii') for prop in OBSERVATION_KEY_PROPERTIES)

OBS_BQ_SCHEMA = [
    bigquery.SchemaField('key_combined', 'STRING'),
    bigquery.SchemaField('value', 'STRING'),
    bigquery.SchemaField('node_id', 'STRING'),
]

SCHEMA_NODE_BQ_SCHEMA = [
    bigquery.SchemaField('dcid', 'STRING'),
    bigquery.SchemaField('value_combined', 'STRING'),
]

_OBS_CSV_HEADER = ('key_combined', 'value', 'node_id')
_SCHEMA_CSV_HEADER = ('dcid', 'value_combined')

_DEFAULT_MIN_CHUNK_BYTES = 8 * 1024 * 1024  # 8 MiB minimum chunk size
_MIN_PARALLEL_TOTAL_BYTES = 4 * 1024 * 1024  # Run in-process below 4 MiB
_MAX_SHARDS_PER_DATASET = 256
_LOCAL_READ_BUF_BYTES = 8 * 1024 * 1024  # 8 MiB
_GCS_FETCH_BLOCK_BYTES = 16 * 1024 * 1024  # 16 MiB ranged GET block
_GCS_BOUNDARY_SLACK_BYTES = 64 * 1024  # 64 KiB boundary over-read slack
_GCS_WRITE_CHUNK_BYTES = 16 * 1024 * 1024  # 16 MiB resumable PUT chunk
_CSV_BATCH_ROWS = 16384
_NORM_CACHE_MAX_ENTRIES = 262144
_RAW_VAL_CACHE_MAX_ENTRIES = 65536
_BQ_MAX_URIS_PER_LOAD = 10000

_WORKER_GCS_CLIENT: Optional[storage.Client] = None
_NORMALIZE_VALUE_FN: Any = None


def file_is_gcs(filename: str) -> bool:
    """Returns True if filename is a gs:// URI."""
    return bool(filename and filename.startswith('gs://'))


def file_is_local(filename: str) -> bool:
    """Returns True if filename is a local filesystem path."""
    return bool(filename and not file_is_gcs(filename) and
                not filename.startswith('http://') and
                not filename.startswith('https://'))


def file_get_gcs_blob(filename: str, exists: bool = True) -> Any:
    """Resolves a GCS Blob via file_util (kept at module level for compatibility/mocks)."""
    import file_util
    return file_util.file_get_gcs_blob(filename, exists=exists)


def file_get_matching(filepat: Union[str, list]) -> list:
    """Expands local or GCS file wildcards via file_util."""
    import file_util
    return file_util.file_get_matching(filepat)


def _get_normalize_value_fn():
    """Lazily imports mcf_file_util.normalize_value to avoid heavy worker startup imports."""
    global _NORMALIZE_VALUE_FN
    if _NORMALIZE_VALUE_FN is None:
        from mcf_file_util import normalize_value
        _NORMALIZE_VALUE_FN = normalize_value
    return _NORMALIZE_VALUE_FN


def _get_worker_gcs_client() -> storage.Client:
    """Returns a per-process cached Google Cloud Storage client."""
    global _WORKER_GCS_CLIENT
    if _WORKER_GCS_CLIENT is None:
        _WORKER_GCS_CLIENT = storage.Client()
    return _WORKER_GCS_CLIENT


def _ensure_spawn_pythonpath() -> None:
    """Ensures spawned/forkserver worker processes can import repo modules."""
    required = [
        _DATA_DIR,
        _SCRIPT_DIR,
        os.path.join(_DATA_DIR, 'util'),
        os.path.join(_DATA_DIR, 'tools', 'statvar_importer'),
    ]
    existing = os.environ.get('PYTHONPATH', '')
    existing_parts = [p for p in existing.split(os.pathsep) if p]
    missing = [p for p in required if p not in existing_parts]
    if missing:
        os.environ['PYTHONPATH'] = os.pathsep.join(missing + existing_parts)


def _get_mp_context() -> multiprocessing.context.BaseContext:
    """Returns forkserver on Linux (fast fork from clean zygote) or spawn elsewhere."""
    _ensure_spawn_pythonpath()
    available = multiprocessing.get_all_start_methods()
    if 'forkserver' in available:
        return multiprocessing.get_context('forkserver')
    return multiprocessing.get_context('spawn')


def ensure_bq_dataset(bq_client: bigquery.Client,
                      dataset_ref: str,
                      expiration_hours: int = 12) -> None:
    """Ensures the BigQuery dataset exists, setting default TTL on dedicated differ datasets."""
    expected_ttl_ms = expiration_hours * 3600 * 1000
    try:
        ds = bq_client.get_dataset(dataset_ref)
        if (dataset_ref.endswith('.datcom_import_differ') and
                ds.default_table_expiration_ms != expected_ttl_ms):
            ds.default_table_expiration_ms = expected_ttl_ms
            bq_client.update_dataset(ds, ['default_table_expiration_ms'])
    except gcp_exceptions.NotFound:
        logging.info('Creating BigQuery dataset %s', dataset_ref)
        ds = bigquery.Dataset(dataset_ref)
        ds.default_table_expiration_ms = expected_ttl_ms
        bq_client.create_dataset(ds, exists_ok=True)


@functools.lru_cache(maxsize=_NORM_CACHE_MAX_ENTRIES)
def _normalize_str_cached(value: str) -> str:
    """Normalizes a single string property value identically to normalize_value."""
    if not value:
        return ''
    stripped = value.strip()
    if not stripped:
        return ''
    if (',' not in stripped and ' ' not in stripped and '\t' not in stripped and
            '"' not in stripped and '[' not in stripped and
            '__' not in stripped):
        colon_idx = stripped.find(':')
        if colon_idx > 0:
            prefix = stripped[:colon_idx]
            rest = stripped[colon_idx + 1:]
            if (prefix.isalpha() and rest and rest[0].isalpha() and
                    ':' not in rest):
                return stripped if prefix == 'dcid' else f'dcid:{rest}'
        elif stripped[0].isalpha():
            return f'dcid:{stripped}'
    elif (len(stripped) <= 100 and stripped[0] == '"' and
          stripped[-1] == '"' and '"' not in stripped[1:-1] and
          ',' not in stripped and ' ' not in stripped and
          '[' not in stripped and ']' not in stripped):
        return stripped
    return str(_get_normalize_value_fn()(stripped))


def _normalize_prop_val(value: Any) -> str:
    """Normalizes a property value string identically to ImportDiffer."""
    if value is None or value == '':
        return ''
    if isinstance(value, str):
        return _normalize_str_cached(value)
    if isinstance(value, list):
        return ', '.join(sorted([_normalize_prop_val(v) for v in value]))
    return str(value)


def _decode_bytes_prop(raw_val: Any) -> Any:
    """Decodes a bytes or list-of-bytes property value into stripped str(s)."""
    if raw_val is None:
        return ''
    if raw_val.__class__ is bytes:
        return raw_val.decode('utf-8', 'replace')
    if isinstance(raw_val, list):
        return [x.decode('utf-8', 'replace') for x in raw_val]
    return str(raw_val)


def _format_raw_bytes_prop(raw_val: Any) -> str:
    """Formats a raw bytes or list-of-bytes property value without coercion."""
    if raw_val is None:
        return ''
    if raw_val.__class__ is bytes:
        return raw_val.decode('utf-8', 'replace')
    if isinstance(raw_val, list):
        return ', '.join(x.decode('utf-8', 'replace') for x in raw_val)
    return str(raw_val).strip()


def _cache_miss_obs_prop(raw_v: bytes, bytes_norm_cache: Dict[Any, str]) -> str:
    """Populates bytes_norm_cache on a cache miss for an observation key property."""
    if len(bytes_norm_cache) >= _NORM_CACHE_MAX_ENTRIES:
        bytes_norm_cache.clear()
        bytes_norm_cache[None] = ''
        bytes_norm_cache[b''] = ''
    norm_v = _normalize_str_cached(raw_v.decode('utf-8', 'replace'))
    bytes_norm_cache[raw_v] = norm_v
    return norm_v


def _build_obs_key_slow(node: Dict[bytes, Any],
                        bytes_norm_cache: Dict[Any, str]) -> str:
    """Fallback builder when an observation key property has multiple values (list)."""
    parts: List[str] = []
    for prop_b in _OBS_KEY_PROPS_BYTES:
        raw_v = node.get(prop_b)
        if raw_v is None:
            parts.append('')
        elif raw_v.__class__ is bytes:
            norm_v = bytes_norm_cache.get(raw_v)
            if norm_v is None:
                norm_v = _cache_miss_obs_prop(raw_v, bytes_norm_cache)
            parts.append(norm_v)
        else:
            parts.append(_normalize_prop_val(_decode_bytes_prop(raw_v)))
    return ';'.join(parts)


def _flush_schema_bytes_node(
    node: Dict[bytes, Any],
    schema_batch: List[Tuple[str, str]],
) -> None:
    """Formats a non-observation MCF node from bytes dictionary into schema_batch."""
    str_node = {
        k.decode('utf-8', 'replace'): _decode_bytes_prop(v)
        for k, v in node.items()
    }
    raw_id = str_node.get('dcid') or str_node.get('Node', '')
    dcid = _normalize_prop_val(raw_id)
    if dcid and not dcid.startswith('dcid:'):
        dcid = f'dcid:{dcid}'
    props = []
    for k in sorted(str_node.keys()):
        if k not in ('Node', 'dcid'):
            props.append(f'{k}:{_normalize_prop_val(str_node[k])}')
    schema_batch.append((dcid, ';'.join(props)))


def _flush_any_bytes_node(
    node: Dict[bytes, Any],
    obs_batch: List[Tuple[str, str, str]],
    schema_batch: List[Tuple[str, str]],
    bytes_norm_cache: Dict[Any, str],
    raw_val_cache: Dict[Any, str],
) -> Tuple[int, int]:
    """Flushes a binary-parsed MCF node into obs_batch or schema_batch."""
    type_of = node.get(b'typeOf')
    if type_of is not None:
        if type_of.__class__ is bytes:
            is_obs = b'StatVarObservation' in type_of
        elif isinstance(type_of, list):
            is_obs = any(b'StatVarObservation' in t for t in type_of)
        else:
            is_obs = False
    else:
        is_obs = False

    if not is_obs:
        _flush_schema_bytes_node(node, schema_batch)
        return 0, 1

    node_get = node.get
    cache_get = bytes_norm_cache.get
    try:
        p0 = cache_get(node_get(b'variableMeasured'))
        if p0 is None:
            p0 = _cache_miss_obs_prop(node[b'variableMeasured'],
                                      bytes_norm_cache)
        p1 = cache_get(node_get(b'observationAbout'))
        if p1 is None:
            p1 = _cache_miss_obs_prop(node[b'observationAbout'],
                                      bytes_norm_cache)
        p2 = cache_get(node_get(b'observationDate'))
        if p2 is None:
            p2 = _cache_miss_obs_prop(node[b'observationDate'],
                                      bytes_norm_cache)
        p3 = cache_get(node_get(b'observationPeriod'))
        if p3 is None:
            p3 = _cache_miss_obs_prop(node[b'observationPeriod'],
                                      bytes_norm_cache)
        p4 = cache_get(node_get(b'measurementMethod'))
        if p4 is None:
            p4 = _cache_miss_obs_prop(node[b'measurementMethod'],
                                      bytes_norm_cache)
        p5 = cache_get(node_get(b'unit'))
        if p5 is None:
            p5 = _cache_miss_obs_prop(node[b'unit'], bytes_norm_cache)
        p6 = cache_get(node_get(b'scalingFactor'))
        if p6 is None:
            p6 = _cache_miss_obs_prop(node[b'scalingFactor'], bytes_norm_cache)
        key_combined = f'{p0};{p1};{p2};{p3};{p4};{p5};{p6}'
    except TypeError:
        key_combined = _build_obs_key_slow(node, bytes_norm_cache)

    raw_val = node_get(b'value')
    if raw_val is None:
        val = ''
    elif raw_val.__class__ is bytes:
        val = raw_val_cache.get(raw_val)
        if val is None:
            if len(raw_val_cache) >= _RAW_VAL_CACHE_MAX_ENTRIES:
                raw_val_cache.clear()
            val = raw_val.decode('utf-8', 'replace')
            raw_val_cache[raw_val] = val
    else:
        val = _format_raw_bytes_prop(raw_val)

    raw_nid = node_get(b'Node') or node_get(b'dcid')
    if raw_nid is None:
        node_id = ''
    elif raw_nid.__class__ is bytes:
        node_id = raw_nid.decode('utf-8', 'replace')
    else:
        node_id = _format_raw_bytes_prop(raw_nid)

    obs_batch.append((key_combined, val, node_id))
    return 1, 0


@contextlib.contextmanager
def _open_text_stream(path: str, mode: str = 'r'):
    """Opens a local file or gs:// URI as a streaming UTF-8 text file without /tmp buffering."""
    newline = '' if mode.startswith('w') else None
    if file_is_gcs(path):
        if mode.startswith('r'):
            blob = file_get_gcs_blob(path, exists=True)
            if not blob:
                raise FileNotFoundError(f'GCS blob not found: {path}')
            raw_stream = storage.fileio.BlobReader(blob)
            with io.TextIOWrapper(raw_stream,
                                  encoding='utf-8',
                                  errors='replace') as stream:
                yield stream
        elif mode.startswith('w'):
            blob = file_get_gcs_blob(path, exists=False)
            if not blob:
                raise RuntimeError(
                    f'Failed to create GCS blob for write: {path}')
            raw_stream = storage.fileio.BlobWriter(blob, ignore_flush=True)
            with io.TextIOWrapper(raw_stream, encoding='utf-8',
                                  newline=newline) as stream:
                yield stream
        else:
            raise ValueError(f'Unsupported mode for GCS stream: {mode}')
    else:
        if mode.startswith('w'):
            parent_dir = os.path.dirname(path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
        with open(path,
                  mode=mode,
                  encoding='utf-8',
                  newline=newline,
                  errors='replace' if mode.startswith('r') else None) as stream:
            yield stream


def _get_gcs_blob_no_bucket_rpc(path: str) -> storage.Blob:
    """Constructs a GCS Blob reference without making a bucket.get_bucket RPC."""
    if isinstance(file_get_gcs_blob, mock.Mock):
        blob = file_get_gcs_blob(path, exists=False)
        if not blob:
            raise RuntimeError(f'Failed to resolve GCS blob: {path}')
        return blob
    bucket_name, blob_name = path[len('gs://'):].split('/', 1)
    client = _get_worker_gcs_client()
    return client.bucket(bucket_name).blob(blob_name)


def _remove_temp_file(path: str) -> None:
    """Deletes a temporary local file or gs:// blob if it exists."""
    try:
        if file_is_gcs(path):
            if isinstance(file_get_gcs_blob, mock.Mock):
                blob = file_get_gcs_blob(path, exists=True)
                if blob:
                    blob.delete()
            else:
                blob = _get_gcs_blob_no_bucket_rpc(path)
                try:
                    blob.delete()
                except gcp_exceptions.NotFound:
                    pass
        elif os.path.exists(path):
            os.remove(path)
    except Exception as exc:
        logging.warning('Failed to remove temporary file %s: %s', path, exc)


def _remove_temp_files_parallel(paths: Sequence[str]) -> None:
    """Deletes multiple temporary local files or GCS blobs concurrently."""
    if not paths:
        return
    if len(paths) == 1 or all(not file_is_gcs(p) for p in paths):
        for path in paths:
            _remove_temp_file(path)
        return
    workers = min(32, len(paths))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(_remove_temp_file, paths))


class _AsyncBatchCsvSink:
    """Batched CSV writer with optional background GCS upload thread."""

    def __init__(self,
                 path: str,
                 header: Sequence[str],
                 write_header: bool = True,
                 lazy_create: bool = False):
        self._path = path
        self._header = tuple(header)
        self._write_header = write_header
        self._lazy_create = lazy_create
        self._is_gcs = file_is_gcs(path)
        self._created = False
        self._raw_fh: Any = None
        self._queue: Optional[queue.Queue] = None
        self._writer_thread: Optional[threading.Thread] = None
        self._writer_exc: Optional[BaseException] = None
        self._string_buf = io.StringIO()
        self._csv_writer = csv.writer(self._string_buf)
        if not self._lazy_create:
            self._ensure_open()

    @property
    def created(self) -> bool:
        return self._created

    def _ensure_open(self) -> None:
        if self._created:
            return
        self._created = True
        if self._is_gcs:
            if isinstance(file_get_gcs_blob, mock.Mock):
                blob = file_get_gcs_blob(self._path, exists=False)
                if not blob:
                    raise RuntimeError(
                        f'Failed to create GCS blob for write: {self._path}')
            else:
                blob = _get_gcs_blob_no_bucket_rpc(self._path)
            self._raw_fh = storage.fileio.BlobWriter(
                blob, chunk_size=_GCS_WRITE_CHUNK_BYTES, ignore_flush=True)
            self._queue = queue.Queue(maxsize=3)
            self._writer_thread = threading.Thread(target=self._gcs_write_loop,
                                                   daemon=True)
            self._writer_thread.start()
        else:
            parent_dir = os.path.dirname(self._path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            self._raw_fh = open(self._path, 'wb')

        if self._write_header:
            self.write_rows([self._header])

    def _gcs_write_loop(self) -> None:
        assert self._queue is not None
        try:
            while True:
                data = self._queue.get()
                if data is None:
                    break
                self._raw_fh.write(data)
        except BaseException as exc:
            self._writer_exc = exc
        finally:
            try:
                self._raw_fh.close()
            except BaseException as exc:
                if self._writer_exc is None:
                    self._writer_exc = exc

    def write_rows(self, rows: Sequence[Sequence[str]]) -> None:
        if not rows:
            return
        if not self._created:
            self._ensure_open()
        if self._writer_exc is not None:
            raise self._writer_exc
        self._string_buf.seek(0)
        self._string_buf.truncate(0)
        self._csv_writer.writerows(rows)
        payload = self._string_buf.getvalue().encode('utf-8')
        if self._is_gcs:
            assert self._queue is not None
            while True:
                if self._writer_exc is not None:
                    raise self._writer_exc
                try:
                    self._queue.put(payload, timeout=0.5)
                    break
                except queue.Full:
                    continue
        else:
            self._raw_fh.write(payload)

    def close(self) -> None:
        if not self._created:
            return
        if self._is_gcs:
            if self._queue is not None and self._writer_thread is not None:
                while self._writer_thread.is_alive():
                    try:
                        self._queue.put(None, timeout=0.5)
                        break
                    except queue.Full:
                        if self._writer_exc is not None:
                            break
                self._writer_thread.join()
            if self._writer_exc is not None:
                raise self._writer_exc
        elif self._raw_fh is not None:
            self._raw_fh.close()


def _iter_raw_bytes_blocks(
    path: str,
    seek_pos: int,
    end_offset: Optional[int],
    known_size: Optional[int] = None,
) -> Iterator[bytes]:
    """Yields raw byte blocks starting at seek_pos with GCS ranged prefetch."""
    if not file_is_gcs(path):
        with open(path, 'rb') as fh:
            if seek_pos > 0:
                fh.seek(seek_pos)
            while True:
                chunk = fh.read(_LOCAL_READ_BUF_BYTES)
                if not chunk:
                    break
                yield chunk
        return

    if isinstance(file_get_gcs_blob, mock.Mock):
        blob = file_get_gcs_blob(path, exists=True)
        if not blob:
            raise FileNotFoundError(f'GCS blob not found: {path}')
        with storage.fileio.BlobReader(blob) as reader:
            if seek_pos > 0:
                reader.seek(seek_pos)
            while True:
                chunk = reader.read(_LOCAL_READ_BUF_BYTES)
                if not chunk:
                    break
                yield chunk
        return

    blob = _get_gcs_blob_no_bucket_rpc(path)
    total_size = known_size
    if total_size is None or total_size <= 0:
        try:
            blob.reload()
        except gcp_exceptions.NotFound as exc:
            raise FileNotFoundError(f'GCS blob not found: {path}') from exc
        total_size = blob.size or 0

    if seek_pos >= total_size:
        return

    stop_event = threading.Event()
    block_queue: queue.Queue = queue.Queue(maxsize=3)
    initial_limit = (min(total_size, end_offset + _GCS_BOUNDARY_SLACK_BYTES)
                     if end_offset is not None else total_size)

    def _prefetch_loop() -> None:
        pos = seek_pos
        target_limit = initial_limit
        try:
            while pos < total_size and not stop_event.is_set():
                if pos < target_limit:
                    remaining_to_limit = target_limit - pos
                    if remaining_to_limit <= (_GCS_FETCH_BLOCK_BYTES +
                                              _GCS_BOUNDARY_SLACK_BYTES):
                        fetch_end = target_limit
                    else:
                        fetch_end = pos + _GCS_FETCH_BLOCK_BYTES
                else:
                    fetch_end = min(total_size, pos + 4 * 1024 * 1024)
                    target_limit = fetch_end

                try:
                    data = blob.download_as_bytes(start=pos,
                                                  end=fetch_end - 1,
                                                  raw_download=True,
                                                  checksum=None)
                except gcp_exceptions.RequestRangeNotSatisfiable:
                    break
                except gcp_exceptions.NotFound as exc:
                    raise FileNotFoundError(
                        f'GCS blob not found: {path}') from exc

                if not data:
                    break
                pos += len(data)
                while not stop_event.is_set():
                    try:
                        block_queue.put(('data', data), timeout=0.5)
                        break
                    except queue.Full:
                        continue
        except BaseException as exc:
            while not stop_event.is_set():
                try:
                    block_queue.put(('error', exc), timeout=0.5)
                    break
                except queue.Full:
                    continue
        finally:
            while not stop_event.is_set():
                try:
                    block_queue.put(('eof', b''), timeout=0.5)
                    break
                except queue.Full:
                    continue

    prefetch_thread = threading.Thread(target=_prefetch_loop, daemon=True)
    prefetch_thread.start()
    try:
        while True:
            kind, payload = block_queue.get()
            if kind == 'error':
                raise payload
            if kind == 'eof':
                break
            yield payload
    finally:
        stop_event.set()
        while prefetch_thread.is_alive():
            try:
                block_queue.get_nowait()
            except queue.Empty:
                pass
            prefetch_thread.join(timeout=0.1)


def _iter_mcf_line_blocks(
    path: str,
    start_offset: int = 0,
    end_offset: Optional[int] = None,
    known_size: Optional[int] = None,
) -> Iterator[Tuple[int, int, List[bytes], bool]]:
    """Yields (block_start_offset, block_end_offset, complete_lines, is_ascii) per ~8-16 MiB block."""
    seek_pos = start_offset - 1 if start_offset > 0 else 0
    discard_partial = start_offset > 0
    pos = seek_pos
    carryover = b''

    for block in _iter_raw_bytes_blocks(path,
                                        seek_pos=seek_pos,
                                        end_offset=end_offset,
                                        known_size=known_size):
        if discard_partial:
            nl_idx = block.find(b'\n')
            if nl_idx < 0:
                pos += len(block)
                continue
            pos += nl_idx + 1
            block = block[nl_idx + 1:]
            discard_partial = False
            if not block:
                continue

        if b'\n' not in block:
            carryover += block
            continue

        prev_carry_len = len(carryover)
        is_ascii = block.isascii() and (prev_carry_len == 0 or
                                        carryover.isascii())
        parts = block.split(b'\n')
        if prev_carry_len:
            parts[0] = carryover + parts[0]
        carryover = parts.pop()
        consumed = prev_carry_len + len(block) - len(carryover)
        block_start = pos
        pos += consumed
        yield block_start, pos, parts, is_ascii

    if not discard_partial and carryover:
        yield pos, pos + len(carryover), [carryover], carryover.isascii()


def _stream_mcf_slice_to_sinks(
    mcf_path: str,
    start_offset: int,
    end_offset: Optional[int],
    known_size: Optional[int],
    obs_sink: _AsyncBatchCsvSink,
    schema_sink: _AsyncBatchCsvSink,
    bytes_norm_cache: Dict[Any, str],
    raw_val_cache: Dict[Any, str],
) -> Tuple[int, int]:
    """Parses MCF nodes in [B(start_offset), B(end_offset)) into CSV sinks."""
    total_obs = 0
    total_schema = 0
    obs_batch: List[Tuple[str, str, str]] = []
    schema_batch: List[Tuple[str, str]] = []
    current_node: Dict[bytes, Any] = {}

    skipping = start_offset > 0
    after_sep = False
    past_end = False
    after_sep_since_end = False
    reached_chunk_end = False

    for block_start, block_end, lines, is_ascii in _iter_mcf_line_blocks(
            mcf_path, start_offset, end_offset, known_size=known_size):
        # Fast interior loop: no boundary tracking or per-line byte offset math
        # needed when already past start boundary and entire block < end_offset.
        if (is_ascii and not skipping and not past_end and
            (end_offset is None or block_end <= end_offset)):
            for raw_line in lines:
                if not raw_line:
                    is_sep = True
                else:
                    stripped = raw_line.strip()
                    is_sep = (not stripped) or (stripped[0] == 35)
                if is_sep:
                    if current_node:
                        o_inc, s_inc = _flush_any_bytes_node(
                            current_node,
                            obs_batch,
                            schema_batch,
                            bytes_norm_cache,
                            raw_val_cache,
                        )
                        total_obs += o_inc
                        total_schema += s_inc
                        current_node = {}
                        if len(obs_batch) >= _CSV_BATCH_ROWS:
                            obs_sink.write_rows(obs_batch)
                            obs_batch.clear()
                        if len(schema_batch) >= _CSV_BATCH_ROWS:
                            schema_sink.write_rows(schema_batch)
                            schema_batch.clear()
                    continue

                k_b, sep_b, v_b = stripped.partition(b':')
                if not sep_b:
                    continue
                k_b = k_b.strip()
                v_b = v_b.strip()
                if k_b == b'Node' and current_node:
                    o_inc, s_inc = _flush_any_bytes_node(
                        current_node,
                        obs_batch,
                        schema_batch,
                        bytes_norm_cache,
                        raw_val_cache,
                    )
                    total_obs += o_inc
                    total_schema += s_inc
                    current_node = {}
                    if len(obs_batch) >= _CSV_BATCH_ROWS:
                        obs_sink.write_rows(obs_batch)
                        obs_batch.clear()
                    if len(schema_batch) >= _CSV_BATCH_ROWS:
                        schema_sink.write_rows(schema_batch)
                        schema_batch.clear()

                existing = current_node.get(k_b)
                if existing is None:
                    current_node[k_b] = v_b
                elif existing.__class__ is list:
                    existing.append(v_b)
                else:
                    current_node[k_b] = [existing, v_b]
            continue

        # Boundary / non-ASCII loop with exact per-line byte offset tracking.
        line_pos = block_start
        for raw_line in lines:
            line_offset = line_pos
            line_pos += len(raw_line) + 1

            if is_ascii:
                stripped = raw_line.strip()
                is_sep = (not stripped) or (stripped[0] == 35)
                if not is_sep:
                    k_b, sep_b, v_b = stripped.partition(b':')
                    if not sep_b:
                        continue
                    k_b = k_b.strip()
                    v_b = v_b.strip()
            else:
                stripped_str = raw_line.decode('utf-8', 'replace').strip()
                is_sep = (not stripped_str) or (stripped_str[0] == '#')
                if not is_sep:
                    k_str, sep_str, v_str = stripped_str.partition(':')
                    if not sep_str:
                        continue
                    k_b = k_str.strip().encode('utf-8')
                    v_b = v_str.strip().encode('utf-8')

            if skipping:
                if end_offset is not None and line_offset >= end_offset:
                    if is_sep or (not after_sep) or k_b == b'Node':
                        return 0, 0
                    skipping = False
                    past_end = True
                    after_sep_since_end = False
                else:
                    if is_sep:
                        after_sep = True
                        continue
                    if after_sep or k_b == b'Node':
                        skipping = False
                    else:
                        continue

            if (end_offset is not None and not past_end and
                    line_offset >= end_offset):
                past_end = True
                after_sep_since_end = False

            if is_sep:
                if current_node:
                    o_inc, s_inc = _flush_any_bytes_node(
                        current_node,
                        obs_batch,
                        schema_batch,
                        bytes_norm_cache,
                        raw_val_cache,
                    )
                    total_obs += o_inc
                    total_schema += s_inc
                    current_node = {}
                    if len(obs_batch) >= _CSV_BATCH_ROWS:
                        obs_sink.write_rows(obs_batch)
                        obs_batch.clear()
                    if len(schema_batch) >= _CSV_BATCH_ROWS:
                        schema_sink.write_rows(schema_batch)
                        schema_batch.clear()
                if past_end:
                    after_sep_since_end = True
                continue

            if past_end and (after_sep_since_end or k_b == b'Node'):
                if current_node:
                    o_inc, s_inc = _flush_any_bytes_node(
                        current_node,
                        obs_batch,
                        schema_batch,
                        bytes_norm_cache,
                        raw_val_cache,
                    )
                    total_obs += o_inc
                    total_schema += s_inc
                    current_node = {}
                reached_chunk_end = True
                break

            if k_b == b'Node' and current_node:
                o_inc, s_inc = _flush_any_bytes_node(
                    current_node,
                    obs_batch,
                    schema_batch,
                    bytes_norm_cache,
                    raw_val_cache,
                )
                total_obs += o_inc
                total_schema += s_inc
                current_node = {}
                if len(obs_batch) >= _CSV_BATCH_ROWS:
                    obs_sink.write_rows(obs_batch)
                    obs_batch.clear()
                if len(schema_batch) >= _CSV_BATCH_ROWS:
                    schema_sink.write_rows(schema_batch)
                    schema_batch.clear()

            existing = current_node.get(k_b)
            if existing is None:
                current_node[k_b] = v_b
            elif existing.__class__ is list:
                existing.append(v_b)
            else:
                current_node[k_b] = [existing, v_b]

        if reached_chunk_end:
            break

    if current_node:
        o_inc, s_inc = _flush_any_bytes_node(
            current_node,
            obs_batch,
            schema_batch,
            bytes_norm_cache,
            raw_val_cache,
        )
        total_obs += o_inc
        total_schema += s_inc

    if obs_batch:
        obs_sink.write_rows(obs_batch)
        obs_batch.clear()
    if schema_batch:
        schema_sink.write_rows(schema_batch)
        schema_batch.clear()

    return total_obs, total_schema


def _process_mcf_work_unit(
    slices: Sequence[Tuple[str, int, Optional[int], Optional[int]]],
    obs_csv_path: str,
    schema_csv_path: str,
    lazy_create: bool = True,
) -> Tuple[int, int, Optional[str], Optional[str]]:
    """Worker entrypoint that converts one or more MCF byte slices into CSV shard files."""
    obs_sink = _AsyncBatchCsvSink(obs_csv_path,
                                  _OBS_CSV_HEADER,
                                  write_header=True,
                                  lazy_create=lazy_create)
    schema_sink = _AsyncBatchCsvSink(schema_csv_path,
                                     _SCHEMA_CSV_HEADER,
                                     write_header=True,
                                     lazy_create=lazy_create)
    bytes_norm_cache: Dict[Any, str] = {None: '', b'': ''}
    raw_val_cache: Dict[Any, str] = {}
    total_obs = 0
    total_schema = 0
    try:
        for mcf_path, start_offset, end_offset, known_size in slices:
            o_cnt, s_cnt = _stream_mcf_slice_to_sinks(
                mcf_path=mcf_path,
                start_offset=start_offset,
                end_offset=end_offset,
                known_size=known_size,
                obs_sink=obs_sink,
                schema_sink=schema_sink,
                bytes_norm_cache=bytes_norm_cache,
                raw_val_cache=raw_val_cache,
            )
            total_obs += o_cnt
            total_schema += s_cnt
    finally:
        obs_sink.close()
        schema_sink.close()

    return (
        total_obs,
        total_schema,
        obs_csv_path if obs_sink.created else None,
        schema_csv_path if schema_sink.created else None,
    )


def _list_mcf_files_with_sizes(
        mcf_pattern: Union[str, Sequence[str]]) -> List[Tuple[str, int]]:
    """Lists matching local or GCS MCF files along with their byte sizes in one pass."""
    if not mcf_pattern:
        return []

    if (isinstance(file_get_matching, mock.Mock) or
            isinstance(file_get_gcs_blob, mock.Mock)):
        matched = file_get_matching(mcf_pattern)
        results: List[Tuple[str, int]] = []
        for path in matched:
            if file_is_local(path) and os.path.exists(path):
                results.append((path, os.path.getsize(path)))
            elif file_is_gcs(path):
                blob = file_get_gcs_blob(path, exists=True)
                raw_size = getattr(blob, 'size', 0) if blob else 0
                results.append(
                    (path, raw_size if isinstance(raw_size, int) else 0))
            else:
                results.append((path, 0))
        return results

    patterns: List[str] = []
    raw_items = [mcf_pattern] if isinstance(mcf_pattern,
                                            str) else list(mcf_pattern)
    for item in raw_items:
        if isinstance(item, str):
            for part in item.split(','):
                part = part.strip()
                if part and part not in patterns:
                    patterns.append(part)

    size_by_file: Dict[str, int] = {}
    for pat in patterns:
        if file_is_local(pat):
            for local_path in glob.glob(pat, recursive=True):
                if os.path.isfile(local_path):
                    size_by_file[local_path] = os.path.getsize(local_path)
        elif file_is_gcs(pat):
            bucket_name, blob_pat = pat[len('gs://'):].split('/', 1)
            wildcard_match = re.search(r'[*?\[]', blob_pat)
            if wildcard_match:
                prefix = blob_pat[:wildcard_match.start()]
                client = _get_worker_gcs_client()
                for blob in client.list_blobs(bucket_name, prefix=prefix):
                    if fnmatch.fnmatch(blob.name, blob_pat):
                        uri = f'gs://{bucket_name}/{blob.name}'
                        size_by_file[uri] = int(blob.size or 0)
            else:
                blob = _get_gcs_blob_no_bucket_rpc(pat)
                try:
                    blob.reload()
                    size_by_file[pat] = int(blob.size or 0)
                except gcp_exceptions.NotFound:
                    pass
        else:
            for matched_path in file_get_matching(pat):
                size_by_file[matched_path] = 0

    return sorted(size_by_file.items(), key=lambda kv: kv[0])


def _plan_mcf_work_units(
    files_with_sizes: Sequence[Tuple[str, int]],
    max_workers: int,
    chunk_size_bytes: int = _DEFAULT_MIN_CHUNK_BYTES,
    max_shards: int = _MAX_SHARDS_PER_DATASET,
) -> List[List[Tuple[str, int, Optional[int], Optional[int]]]]:
    """Splits large MCF files into byte-range slices and packs small files into balanced units."""
    if not files_with_sizes:
        return []

    total_bytes = sum(max(0, size) for _, size in files_with_sizes)
    workers = max(1, max_workers)
    if workers == 1:
        return [[(path, 0, None, size if size > 0 else None)
                 for path, size in files_with_sizes]]

    target_shards = min(max_shards, max(workers * 4, 16))
    min_chunk = max(1, chunk_size_bytes)
    effective_chunk = max(min_chunk,
                          (total_bytes + target_shards - 1) // target_shards)

    work_units: List[List[Tuple[str, int, Optional[int], Optional[int]]]] = []
    small_bundle: List[Tuple[str, int, Optional[int], Optional[int]]] = []
    small_bundle_bytes = 0

    for path, size in files_with_sizes:
        if size <= 0:
            small_bundle.append((path, 0, None, None))
        elif size <= effective_chunk:
            if small_bundle and (small_bundle_bytes + size > effective_chunk):
                work_units.append(small_bundle)
                small_bundle = []
                small_bundle_bytes = 0
            small_bundle.append((path, 0, None, size))
            small_bundle_bytes += size
        else:
            if small_bundle:
                work_units.append(small_bundle)
                small_bundle = []
                small_bundle_bytes = 0
            offset = 0
            while offset < size:
                next_offset = offset + effective_chunk
                if next_offset >= size:
                    work_units.append([(path, offset, None, size)])
                    break
                work_units.append([(path, offset, next_offset, size)])
                offset = next_offset

    if small_bundle:
        work_units.append(small_bundle)

    return work_units


def stream_mcf_to_csv(mcf_pattern: str, obs_csv_path: str,
                      schema_csv_path: str) -> Tuple[int, int]:
    """Streams MCF files node-by-node into observation and schema CSVs in O(1) memory."""
    files_with_sizes = _list_mcf_files_with_sizes(mcf_pattern)
    logging.info('Streaming %d MCF file(s) to CSV: %s', len(files_with_sizes),
                 mcf_pattern)
    slices = [(path, 0, None, size if size > 0 else None)
              for path, size in files_with_sizes]
    total_obs, total_schema, _, _ = _process_mcf_work_unit(
        slices=slices,
        obs_csv_path=obs_csv_path,
        schema_csv_path=schema_csv_path,
        lazy_create=False,
    )
    logging.info('Completed streaming MCF to CSV: %d obs, %d schema nodes',
                 total_obs, total_schema)
    return total_obs, total_schema


class _ChainedLocalCsvReader(io.RawIOBase):
    """Seekable binary file-like reader that chains multiple local CSV shards cleanly."""

    mode = 'rb'

    def __init__(self, paths: Sequence[str]):
        super().__init__()
        self._segments: List[Tuple[str, int, int]] = []
        self._cum_ends: List[int] = []
        total = 0
        for idx, path in enumerate(paths):
            file_size = os.path.getsize(path)
            header_skip = 0
            if idx > 0 and file_size > 0:
                with open(path, 'rb') as fh:
                    header_skip = len(fh.readline())
            seg_len = max(0, file_size - header_skip)
            if seg_len > 0 or idx == 0:
                self._segments.append((path, header_skip, seg_len))
                total += seg_len
                self._cum_ends.append(total)
        self._total_size = total
        self._pos = 0
        self._cur_idx: Optional[int] = None
        self._cur_fh: Optional[io.BufferedReader] = None

    @property
    def total_size(self) -> int:
        return self._total_size

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self._pos

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        if whence == os.SEEK_SET:
            new_pos = offset
        elif whence == os.SEEK_CUR:
            new_pos = self._pos + offset
        elif whence == os.SEEK_END:
            new_pos = self._total_size + offset
        else:
            raise ValueError(f'Unsupported whence: {whence}')
        if new_pos < 0:
            raise ValueError(f'Negative seek position: {new_pos}')
        self._pos = min(new_pos, self._total_size)
        return self._pos

    def _open_segment(self, idx: int) -> io.BufferedReader:
        if self._cur_idx != idx or self._cur_fh is None:
            if self._cur_fh is not None:
                self._cur_fh.close()
            self._cur_fh = open(self._segments[idx][0], 'rb')
            self._cur_idx = idx
        return self._cur_fh

    def read(self, size: int = -1) -> bytes:
        if self._pos >= self._total_size or size == 0 or not self._segments:
            return b''
        remaining = (self._total_size - self._pos if size is None or size < 0
                     else min(size, self._total_size - self._pos))
        chunks: List[bytes] = []
        while remaining > 0 and self._pos < self._total_size:
            seg_idx = bisect.bisect_right(self._cum_ends, self._pos)
            if seg_idx >= len(self._segments):
                break
            seg_start = 0 if seg_idx == 0 else self._cum_ends[seg_idx - 1]
            _, header_skip, seg_len = self._segments[seg_idx]
            within_seg = self._pos - seg_start
            to_read = min(remaining, seg_len - within_seg)
            fh = self._open_segment(seg_idx)
            fh.seek(header_skip + within_seg)
            data = fh.read(to_read)
            if not data:
                break
            chunks.append(data)
            read_len = len(data)
            self._pos += read_len
            remaining -= read_len
        return chunks[0] if len(chunks) == 1 else b''.join(chunks)

    def close(self) -> None:
        if self._cur_fh is not None:
            self._cur_fh.close()
            self._cur_fh = None
            self._cur_idx = None
        super().close()


def _set_bq_table_ttl(bq_client: bigquery.Client, table_ref: str,
                      expiration_hours: int) -> None:
    """Applies the table expiration timestamp to a BigQuery table."""
    table = bq_client.get_table(table_ref)
    table.expires = datetime.now(
        timezone.utc) + timedelta(hours=expiration_hours)
    bq_client.update_table(table, ['expires'])


def load_csv_to_bq_table(
    bq_client: bigquery.Client,
    csv_path: Union[str, Sequence[str]],
    table_ref: str,
    schema: List[bigquery.SchemaField],
    expiration_hours: int = 12,
) -> None:
    """Loads one or more local or GCS CSV files into a BigQuery table with a specified TTL."""
    csv_paths = [csv_path] if isinstance(csv_path, str) else list(csv_path)
    if not csv_paths:
        empty_buf = io.BytesIO(
            (','.join(field.name for field in schema) + '\n').encode('utf-8'))
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            schema=schema,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            allow_quoted_newlines=True,
        )
        load_job = bq_client.load_table_from_file(empty_buf,
                                                  table_ref,
                                                  job_config=job_config)
        load_job.result()
        _set_bq_table_ttl(bq_client, table_ref, expiration_hours)
        return

    if csv_paths[0].startswith('gs://'):
        for batch_start in range(0, len(csv_paths), _BQ_MAX_URIS_PER_LOAD):
            uri_batch = csv_paths[batch_start:batch_start +
                                  _BQ_MAX_URIS_PER_LOAD]
            disposition = (bigquery.WriteDisposition.WRITE_TRUNCATE
                           if batch_start == 0 else
                           bigquery.WriteDisposition.WRITE_APPEND)
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.CSV,
                skip_leading_rows=1,
                schema=schema,
                write_disposition=disposition,
                allow_quoted_newlines=True,
            )
            source_arg: Union[str, List[str]] = (uri_batch[0] if len(uri_batch)
                                                 == 1 else uri_batch)
            load_job = bq_client.load_table_from_uri(source_arg,
                                                     table_ref,
                                                     job_config=job_config)
            load_job.result()
    elif len(csv_paths) == 1:
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            schema=schema,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            allow_quoted_newlines=True,
        )
        with open(csv_paths[0], 'rb') as fh:
            load_job = bq_client.load_table_from_file(fh,
                                                      table_ref,
                                                      job_config=job_config)
        load_job.result()
    else:
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            schema=schema,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            allow_quoted_newlines=True,
        )
        with _ChainedLocalCsvReader(csv_paths) as chained_fh:
            load_job = bq_client.load_table_from_file(
                chained_fh,
                table_ref,
                size=chained_fh.total_size,
                job_config=job_config,
            )
        load_job.result()

    _set_bq_table_ttl(bq_client, table_ref, expiration_hours)


def convert_mcf_to_csv_shards(
    mcf_pattern: str,
    base_dir: str,
    tag: str = '',
    max_workers: Optional[int] = None,
    chunk_size_bytes: int = _DEFAULT_MIN_CHUNK_BYTES,
    process_pool: Optional[concurrent.futures.ProcessPoolExecutor] = None,
) -> Tuple[int, int, List[str], List[str]]:
    """Converts MCF files in parallel into sharded obs and schema CSV files."""
    files_with_sizes = _list_mcf_files_with_sizes(mcf_pattern)
    total_bytes = sum(max(0, size) for _, size in files_with_sizes)
    workers = (max_workers if max_workers and max_workers > 0 else
               (os.cpu_count() or 1))
    if (total_bytes < _MIN_PARALLEL_TOTAL_BYTES and
            chunk_size_bytes >= _DEFAULT_MIN_CHUNK_BYTES):
        workers = 1

    work_units = _plan_mcf_work_units(
        files_with_sizes,
        max_workers=workers,
        chunk_size_bytes=chunk_size_bytes,
    )
    if not work_units:
        return 0, 0, [], []

    is_gcs_dir = file_is_gcs(base_dir)

    def _part_path(prefix: str, idx: int) -> str:
        if len(work_units) == 1:
            fname = f'{prefix}{tag}.csv'
        else:
            fname = f'{prefix}{tag}_part_{idx:05d}.csv'
        return (f'{base_dir}/{fname}' if is_gcs_dir else os.path.join(
            base_dir, fname))

    logging.info(
        'Converting %d MCF file(s) (%.2f MiB) across %d shard(s) (workers=%d)...',
        len(files_with_sizes),
        total_bytes / (1024 * 1024),
        len(work_units),
        workers,
    )

    total_obs = 0
    total_schema = 0
    obs_parts: List[str] = []
    schema_parts: List[str] = []

    if len(work_units) == 1 or workers == 1:
        for idx, slices in enumerate(work_units):
            o_cnt, s_cnt, o_path, s_path = _process_mcf_work_unit(
                slices=slices,
                obs_csv_path=_part_path('obs', idx),
                schema_csv_path=_part_path('schema', idx),
                lazy_create=True,
            )
            total_obs += o_cnt
            total_schema += s_cnt
            if o_path:
                obs_parts.append(o_path)
            if s_path:
                schema_parts.append(s_path)
    else:
        owned_pool = process_pool is None
        pool = (process_pool if process_pool is not None else
                concurrent.futures.ProcessPoolExecutor(
                    max_workers=min(workers, len(work_units)),
                    mp_context=_get_mp_context(),
                ))
        try:
            futures = [
                pool.submit(
                    _process_mcf_work_unit,
                    slices,
                    _part_path('obs', idx),
                    _part_path('schema', idx),
                    True,
                ) for idx, slices in enumerate(work_units)
            ]
            for fut in futures:
                o_cnt, s_cnt, o_path, s_path = fut.result()
                total_obs += o_cnt
                total_schema += s_cnt
                if o_path:
                    obs_parts.append(o_path)
                if s_path:
                    schema_parts.append(s_path)
        finally:
            if owned_pool:
                pool.shutdown(wait=True)

    logging.info(
        'Completed MCF to CSV conversion: %d obs (%d shard(s)), %d schema nodes (%d shard(s))',
        total_obs,
        len(obs_parts),
        total_schema,
        len(schema_parts),
    )
    return total_obs, total_schema, obs_parts, schema_parts


def load_mcf_to_bq_tables(
    bq_client: bigquery.Client,
    mcf_pattern: str,
    obs_table_ref: str,
    schema_table_ref: str,
    temp_dir: Optional[str] = None,
    suffix: str = '',
    expiration_hours: int = 12,
    max_workers: Optional[int] = None,
    chunk_size_bytes: int = _DEFAULT_MIN_CHUNK_BYTES,
    process_pool: Optional[concurrent.futures.ProcessPoolExecutor] = None,
) -> Tuple[int, int]:
    """Streams MCF files in parallel to CSV shards and loads them into BigQuery tables."""
    with contextlib.ExitStack() as stack:
        base_dir = (temp_dir.rstrip('/') if temp_dir else stack.enter_context(
            tempfile.TemporaryDirectory()))
        tag = f'_{suffix}' if suffix else ''
        obs_parts: List[str] = []
        schema_parts: List[str] = []

        try:
            obs_count, schema_count, obs_parts, schema_parts = (
                convert_mcf_to_csv_shards(
                    mcf_pattern=mcf_pattern,
                    base_dir=base_dir,
                    tag=tag,
                    max_workers=max_workers,
                    chunk_size_bytes=chunk_size_bytes,
                    process_pool=process_pool,
                ))
            try:
                load_csv_to_bq_table(bq_client, obs_parts, obs_table_ref,
                                     OBS_BQ_SCHEMA, expiration_hours)
            finally:
                _remove_temp_files_parallel(obs_parts)
                obs_parts = []
            try:
                load_csv_to_bq_table(bq_client, schema_parts, schema_table_ref,
                                     SCHEMA_NODE_BQ_SCHEMA, expiration_hours)
            finally:
                _remove_temp_files_parallel(schema_parts)
                schema_parts = []
        finally:
            _remove_temp_files_parallel(obs_parts)
            _remove_temp_files_parallel(schema_parts)
        return obs_count, schema_count


def _sanitize_job_suffix(job_name: str) -> str:
    """Converts a job name into a safe BigQuery table suffix."""
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', job_name)
    return f'{cleaned}_{uuid.uuid4().hex[:8]}'


def _format_obs_mcf_node(key_combined: str, value: str, node_id: str) -> str:
    """Reconstructs an observation MCF node block identically to ImportDiffer."""
    lines = []
    if node_id and node_id != 'nan':
        lines.append(f'Node: {node_id}')
    keys = (key_combined or '').split(';')
    for i, prop in enumerate(OBSERVATION_KEY_PROPERTIES):
        if i < len(keys) and keys[i] and keys[i] != 'nan':
            lines.append(f'{prop}: {keys[i]}')
    if value and value != 'nan':
        lines.append(f'value: {value}')
    lines.append('typeOf: StatVarObservation')
    return '\n'.join(lines) + '\n\n'


def _format_schema_mcf_node(dcid: str, value_combined: str) -> str:
    """Reconstructs a schema MCF node block identically to ImportDiffer."""
    lines = []
    dcid_str = dcid or ''
    if dcid_str.startswith('dcid:'):
        lines.append(f'dcid: {dcid_str[len("dcid:"):]}')
    else:
        lines.append(f'Node: {dcid_str}')
    for kv in (value_combined or '').split(';'):
        if ':' in kv:
            k, v = kv.split(':', 1)
            lines.append(f'{k}: {v}')
    return '\n'.join(lines) + '\n\n'


def _row_val(row: Any, key: str) -> str:
    """Extracts a string value from a BigQuery Row or dict, returning '' for None."""
    val = row.get(key) if isinstance(row, dict) else getattr(row, key, None)
    return str(val) if val is not None else ''


def _join_output_path(output_location: str, filename: str) -> str:
    """Joins output directory and filename for local or gs:// paths."""
    if file_is_gcs(output_location):
        return f"{output_location.rstrip('/')}/{filename}"
    return os.path.join(output_location, filename)


def run_bigquery_differ(
    current_data: str,
    previous_data: str,
    output_location: str,
    project_id: str,
    job_name: str = 'differ',
    dataset_id: str = 'datcom_import_differ',
    gcs_temp_dir: Optional[str] = None,
    expiration_hours: int = 12,
    max_workers: Optional[int] = None,
    chunk_size_bytes: int = _DEFAULT_MIN_CHUNK_BYTES,
) -> Dict:
    """Executes dataset diff using parallel MCF-to-CSV streaming and BigQuery FULL OUTER JOIN."""
    import differ_utils
    import pandas as pd

    if not project_id:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get(
            'PROJECT_ID', '')

    client_opts = {'quota_project_id': project_id} if project_id else None
    bq_client = bigquery.Client(project=project_id or None,
                                client_options=client_opts)
    if not project_id:
        project_id = getattr(bq_client, 'project', '') or ''
    dataset_ref = f'{project_id}.{dataset_id}'
    ensure_bq_dataset(bq_client, dataset_ref, expiration_hours=expiration_hours)

    suffix = _sanitize_job_suffix(job_name)
    curr_obs_table = f'{dataset_ref}.curr_obs_{suffix}'
    prev_obs_table = f'{dataset_ref}.prev_obs_{suffix}'
    curr_schema_table = f'{dataset_ref}.curr_schema_{suffix}'
    prev_schema_table = f'{dataset_ref}.prev_schema_{suffix}'
    logging.info(
        'Using BigQuery differ tables (TTL=%dh, suffix=%s): %s, %s, %s, %s',
        expiration_hours,
        suffix,
        curr_obs_table,
        prev_obs_table,
        curr_schema_table,
        prev_schema_table,
    )

    statvar_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {
        'ADDED': 0,
        'DELETED': 0,
        'MODIFIED': 0
    })
    schema_counts = {'ADDED': 0, 'DELETED': 0, 'MODIFIED': 0}

    workers = (max_workers if max_workers and max_workers > 0 else
               (os.cpu_count() or 1))
    use_concurrent_steps = (workers > 1 and
                            not isinstance(bq_client, mock.Mock))

    if use_concurrent_steps:
        logging.info(
            'Steps 1-2/3: Loading current and previous MCF data in parallel (workers=%d)...',
            workers,
        )
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=workers,
                mp_context=_get_mp_context(),
        ) as shared_proc_pool, concurrent.futures.ThreadPoolExecutor(
                max_workers=2) as step_pool:
            curr_future = step_pool.submit(
                load_mcf_to_bq_tables,
                bq_client,
                current_data,
                curr_obs_table,
                curr_schema_table,
                gcs_temp_dir,
                f'curr_{suffix}',
                expiration_hours,
                workers,
                chunk_size_bytes,
                shared_proc_pool,
            )
            prev_future = step_pool.submit(
                load_mcf_to_bq_tables,
                bq_client,
                previous_data,
                prev_obs_table,
                prev_schema_table,
                gcs_temp_dir,
                f'prev_{suffix}',
                expiration_hours,
                workers,
                chunk_size_bytes,
                shared_proc_pool,
            )
            curr_obs_count, curr_schema_count = curr_future.result()
            prev_obs_count, prev_schema_count = prev_future.result()
    else:
        logging.info('Step 1/3: Loading current MCF data into BigQuery...')
        curr_obs_count, curr_schema_count = load_mcf_to_bq_tables(
            bq_client,
            current_data,
            curr_obs_table,
            curr_schema_table,
            temp_dir=gcs_temp_dir,
            suffix=f'curr_{suffix}',
            expiration_hours=expiration_hours,
            max_workers=workers,
            chunk_size_bytes=chunk_size_bytes,
        )

        logging.info('Step 2/3: Loading previous MCF data into BigQuery...')
        prev_obs_count, prev_schema_count = load_mcf_to_bq_tables(
            bq_client,
            previous_data,
            prev_obs_table,
            prev_schema_table,
            temp_dir=gcs_temp_dir,
            suffix=f'prev_{suffix}',
            expiration_hours=expiration_hours,
            max_workers=workers,
            chunk_size_bytes=chunk_size_bytes,
        )

    logging.info('Step 3/3: Running BigQuery FULL OUTER JOIN diff...')
    obs_diff_sql = f"""
    SELECT
      COALESCE(c.key_combined, p.key_combined) AS key_combined,
      c.value AS curr_value,
      p.value AS prev_value,
      c.node_id AS curr_node,
      p.node_id AS prev_node,
      CASE
        WHEN p.key_combined IS NULL THEN 'ADDED'
        WHEN c.key_combined IS NULL THEN 'DELETED'
        WHEN c.value IS DISTINCT FROM p.value THEN 'MODIFIED'
        ELSE 'UNMODIFIED'
      END AS diff_type
    FROM `{curr_obs_table}` c
    FULL OUTER JOIN `{prev_obs_table}` p
      ON c.key_combined = p.key_combined
    WHERE p.key_combined IS NULL
       OR c.key_combined IS NULL
       OR c.value IS DISTINCT FROM p.value
    """

    schema_diff_sql = f"""
    WITH curr_schema AS (
      SELECT DISTINCT dcid, value_combined FROM `{curr_schema_table}`
    ),
    prev_schema AS (
      SELECT DISTINCT dcid, value_combined FROM `{prev_schema_table}`
    )
    SELECT
      COALESCE(c.dcid, p.dcid) AS dcid,
      c.value_combined AS curr_value,
      p.value_combined AS prev_value,
      CASE
        WHEN p.dcid IS NULL THEN 'ADDED'
        WHEN c.dcid IS NULL THEN 'DELETED'
        WHEN c.value_combined IS DISTINCT FROM p.value_combined THEN 'MODIFIED'
        ELSE 'UNMODIFIED'
      END AS diff_type
    FROM curr_schema c
    FULL OUTER JOIN prev_schema p
      ON c.dcid = p.dcid
    WHERE p.dcid IS NULL
       OR c.dcid IS NULL
       OR c.value_combined IS DISTINCT FROM p.value_combined
    """

    for fname in ('nodes-added.mcf', 'nodes-deleted.mcf', 'nodes-modified.mcf',
                  'nodes-original.mcf'):
        _remove_temp_file(_join_output_path(output_location, fname))

    with contextlib.ExitStack() as mcf_stack:
        open_streams: Dict[str, Any] = {}

        def _write_mcf_block(filename: str, block: str) -> None:
            if filename not in open_streams:
                out_path = _join_output_path(output_location, filename)
                open_streams[filename] = mcf_stack.enter_context(
                    _open_text_stream(out_path, mode='w'))
            open_streams[filename].write(block)

        for row in bq_client.query(obs_diff_sql).result():
            diff_type = _row_val(row, 'diff_type')
            key_combined = _row_val(row, 'key_combined')
            raw_sv = key_combined.split(';', 1)[0]
            stat_var = (raw_sv[len('dcid:'):]
                        if raw_sv.startswith('dcid:') else raw_sv)
            if diff_type in ('ADDED', 'DELETED', 'MODIFIED'):
                statvar_counts[stat_var][diff_type] += 1
            if diff_type == 'ADDED':
                _write_mcf_block(
                    'nodes-added.mcf',
                    _format_obs_mcf_node(key_combined,
                                         _row_val(row, 'curr_value'),
                                         _row_val(row, 'curr_node')))
            elif diff_type == 'DELETED':
                _write_mcf_block(
                    'nodes-deleted.mcf',
                    _format_obs_mcf_node(key_combined,
                                         _row_val(row, 'prev_value'),
                                         _row_val(row, 'prev_node')))
            elif diff_type == 'MODIFIED':
                _write_mcf_block(
                    'nodes-modified.mcf',
                    _format_obs_mcf_node(key_combined,
                                         _row_val(row, 'curr_value'),
                                         _row_val(row, 'curr_node')))
                _write_mcf_block(
                    'nodes-original.mcf',
                    _format_obs_mcf_node(key_combined,
                                         _row_val(row, 'prev_value'),
                                         _row_val(row, 'prev_node')))

        for row in bq_client.query(schema_diff_sql).result():
            diff_type = _row_val(row, 'diff_type')
            dcid = _row_val(row, 'dcid')
            if diff_type in schema_counts:
                schema_counts[diff_type] += 1
            if diff_type == 'ADDED':
                _write_mcf_block(
                    'nodes-added.mcf',
                    _format_schema_mcf_node(dcid, _row_val(row, 'curr_value')))
            elif diff_type == 'DELETED':
                _write_mcf_block(
                    'nodes-deleted.mcf',
                    _format_schema_mcf_node(dcid, _row_val(row, 'prev_value')))
            elif diff_type == 'MODIFIED':
                _write_mcf_block(
                    'nodes-modified.mcf',
                    _format_schema_mcf_node(dcid, _row_val(row, 'curr_value')))
                _write_mcf_block(
                    'nodes-original.mcf',
                    _format_schema_mcf_node(dcid, _row_val(row, 'prev_value')))

    if statvar_counts:
        obs_diff_df = pd.DataFrame([{
            'StatVar': sv,
            'ADDED': counts['ADDED'],
            'DELETED': counts['DELETED'],
            'MODIFIED': counts['MODIFIED'],
        } for sv, counts in sorted(statvar_counts.items())])
    else:
        obs_diff_df = pd.DataFrame(
            columns=['StatVar', 'ADDED', 'DELETED', 'MODIFIED'])

    added_obs = int(obs_diff_df['ADDED'].sum()) if not obs_diff_df.empty else 0
    deleted_obs = int(
        obs_diff_df['DELETED'].sum()) if not obs_diff_df.empty else 0
    modified_obs = int(
        obs_diff_df['MODIFIED'].sum()) if not obs_diff_df.empty else 0
    added_schema = schema_counts['ADDED']
    deleted_schema = schema_counts['DELETED']
    modified_schema = schema_counts['MODIFIED']
    obs_diff_total = added_obs + deleted_obs + modified_obs
    schema_diff_total = added_schema + deleted_schema + modified_schema

    differ_summary = {
        'current_version': current_data,
        'previous_version': previous_data,
        'current_obs_count': curr_obs_count,
        'previous_obs_count': prev_obs_count,
        'current_schema_count': curr_schema_count,
        'previous_schema_count': prev_schema_count,
        'added_obs_count': added_obs,
        'deleted_obs_count': deleted_obs,
        'modified_obs_count': modified_obs,
        'added_schema_count': added_schema,
        'deleted_schema_count': deleted_schema,
        'modified_schema_count': modified_schema,
        'obs_diff_count': obs_diff_total,
        'schema_diff_count': schema_diff_total,
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        differ_utils.write_json_data(differ_summary, output_location,
                                     'differ_summary.json', tmp_dir)
        differ_utils.write_csv_data(obs_diff_df, output_location,
                                    'differ_summary.csv', tmp_dir)

    logging.info('BigQuery Differ summary: %s', differ_summary)
    return differ_summary


_FLAGS = flags.FLAGS


def _define_cli_flags():
    """Defines CLI flags when bigquery_differ.py is executed as a script."""
    if 'current_data' not in _FLAGS:
        flags.DEFINE_string(
            'current_data', '',
            'Path to the current MCF data (local or gs:// wildcard supported).')
    if 'previous_data' not in _FLAGS:
        flags.DEFINE_string(
            'previous_data', '',
            'Path to the previous MCF data (local or gs:// wildcard supported).'
        )
    if 'output_location' not in _FLAGS:
        flags.DEFINE_string(
            'output_location', 'results',
            'Output directory (local or gs://) for differ_summary.json and differ_summary.csv.'
        )
    if 'project_id' not in _FLAGS:
        flags.DEFINE_string(
            'project_id', '',
            'GCP project ID for BigQuery jobs and dataset (defaults to GOOGLE_CLOUD_PROJECT).'
        )
    if 'job_name' not in _FLAGS:
        flags.DEFINE_string(
            'job_name', 'differ',
            'Prefix name for temporary BigQuery differ tables.')
    if 'bq_dataset' not in _FLAGS:
        flags.DEFINE_string('bq_dataset', 'datcom_import_differ',
                            'BigQuery dataset ID for temporary differ tables.')
    if 'gcs_temp_dir' not in _FLAGS:
        flags.DEFINE_string(
            'gcs_temp_dir', None,
            'Optional temporary directory path for intermediate CSV files.')
    if 'bq_table_ttl_hours' not in _FLAGS:
        flags.DEFINE_integer(
            'bq_table_ttl_hours', 12,
            'TTL in hours for temporary BigQuery differ tables.')
    if 'max_workers' not in _FLAGS:
        flags.DEFINE_integer(
            'max_workers', 0,
            'Maximum parallel worker processes for MCF-to-CSV conversion (0 uses all CPUs).'
        )
    if 'chunk_size_mb' not in _FLAGS:
        flags.DEFINE_integer(
            'chunk_size_mb', 8,
            'Minimum byte-range chunk size in MiB when splitting large MCF files.'
        )


def main(_):
    """CLI entrypoint for running the BigQuery differ directly."""
    if not _FLAGS.current_data or not _FLAGS.previous_data:
        raise ValueError(
            'Both --current_data and --previous_data are required. Run with --help for usage.'
        )
    run_bigquery_differ(
        current_data=_FLAGS.current_data,
        previous_data=_FLAGS.previous_data,
        output_location=_FLAGS.output_location,
        project_id=_FLAGS.project_id,
        job_name=_FLAGS.job_name,
        dataset_id=_FLAGS.bq_dataset,
        gcs_temp_dir=_FLAGS.gcs_temp_dir,
        expiration_hours=_FLAGS.bq_table_ttl_hours,
        max_workers=_FLAGS.max_workers or None,
        chunk_size_bytes=max(1, _FLAGS.chunk_size_mb) * 1024 * 1024,
    )


if __name__ == '__main__':
    _define_cli_flags()
    app.run(main)
