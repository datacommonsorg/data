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
"""Shared BigQuery loader utilities for MCF, JSONL, CSV, and Avro files.

Converts MCF datasets in parallel via `util/file_sharder.py` into sharded
newline-delimited JSON (`.jsonl`) with a unified schema (`dcid STRING`,
`typeOf STRING`, `properties JSON`) and loads local or `gs://` shards into
BigQuery tables with configurable expiration (TTL).

Standalone CLI Usage:
  $ python3 util/bq_loader.py \\
      --input_files="gs://bucket/import/genmcf/*.mcf" \\
      --table="my-project.my_dataset.my_table" \\
      --expiration_hours=12
"""

import bisect
import concurrent.futures
import contextlib
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import functools
import io
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from absl import app
from absl import flags
from absl import logging
from google.api_core import exceptions as gcp_exceptions
from google.cloud import bigquery

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.dirname(_SCRIPT_DIR)
for _path in (
        _DATA_DIR,
        _SCRIPT_DIR,
        os.path.join(_DATA_DIR, 'tools', 'statvar_importer'),
):
    if _path not in sys.path:
        sys.path.append(_path)

from counters import Counters
from file_dict_io import get_file_extension
from file_dict_io import is_mcf_file
import file_sharder
import file_util

# Unified MCF table schema (Option X): dedicated `dcid` and `typeOf` columns
# plus a native BigQuery `JSON` column holding all remaining node properties.
MCF_BQ_SCHEMA = [
    bigquery.SchemaField('dcid', 'STRING'),
    bigquery.SchemaField('typeOf', 'STRING'),
    bigquery.SchemaField('properties', 'JSON'),
]

_DEFAULT_CHUNK_BYTES = 8 * 1024 * 1024  # 8 MiB minimum chunk size
_MIN_PARALLEL_TOTAL_BYTES = 4 * 1024 * 1024  # Run in-process below 4 MiB
_NORM_CACHE_MAX_ENTRIES = 262144
_BQ_MAX_URIS_PER_LOAD = 10000
_NORMALIZE_VALUE_FN: Any = None


def _get_normalize_value_fn():
    """Lazily imports `mcf_file_util.normalize_value` in worker processes."""
    global _NORMALIZE_VALUE_FN
    if _NORMALIZE_VALUE_FN is None:
        from mcf_file_util import normalize_value
        _NORMALIZE_VALUE_FN = normalize_value
    return _NORMALIZE_VALUE_FN


@functools.lru_cache(maxsize=_NORM_CACHE_MAX_ENTRIES)
def _normalize_str_cached(value: str) -> str:
    """Normalizes a single string property value identically to `normalize_value`."""
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


def normalize_prop_val(value: Any) -> str:
    """Normalizes an MCF property value string identically to `ImportDiffer`."""
    if value is None or value == '':
        return ''
    if isinstance(value, str):
        return _normalize_str_cached(value)
    if isinstance(value, list):
        return ', '.join(sorted([normalize_prop_val(v) for v in value]))
    return str(value)


def _format_raw_prop(value: Any) -> str:
    """Formats a property value without numeric/namespace coercion."""
    if value is None:
        return ''
    if isinstance(value, list):
        return ', '.join(str(v).strip() for v in value)
    return str(value).strip()


def _is_observation_type(type_of: Any) -> bool:
    """Returns True if `type_of` includes `StatVarObservation`."""
    if not type_of:
        return False
    if isinstance(type_of, list):
        return any('StatVarObservation' in str(t) for t in type_of)
    return 'StatVarObservation' in str(type_of)


def mcf_node_to_bq_record(
    record: Dict[str, Any],
    stats: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Transforms a parsed MCF node dict into a unified BigQuery JSONL row.

    Output row shape matches `MCF_BQ_SCHEMA`:
      `{'dcid': str, 'typeOf': str, 'properties': dict[str, str]}`.

    - For `StatVarObservation` nodes, `dcid` preserves the raw `Node`/`dcid`
      identifier and `properties['value']` preserves the raw `value` text (so
      downstream consumers such as `bigquery_differ` can apply numeric equality
      and emit original MCF values), while all other properties are normalized.
    - For non-observation (schema/entity) nodes, `dcid` is normalized with a
      `dcid:` prefix and all non-ID properties are normalized.
    """
    raw_type_of = record.get('typeOf', '')
    is_obs = _is_observation_type(raw_type_of)
    norm_type_of = normalize_prop_val(raw_type_of)

    if is_obs:
        if stats is not None:
            stats['bq-obs-count'] = stats.get('bq-obs-count', 0) + 1
        dcid = _format_raw_prop(record.get('Node') or record.get('dcid', ''))
        props: Dict[str, str] = {}
        for k, v in record.items():
            if not k or k in ('Node', 'dcid',
                              'typeOf') or str(k).startswith('#'):
                continue
            if k == 'value':
                props['value'] = _format_raw_prop(v)
            else:
                norm_v = normalize_prop_val(v)
                if norm_v:
                    props[k] = norm_v
    else:
        if stats is not None:
            stats['bq-schema-count'] = stats.get('bq-schema-count', 0) + 1
        raw_id = record.get('dcid') or record.get('Node', '')
        dcid = normalize_prop_val(raw_id)
        if dcid and not dcid.startswith('dcid:'):
            dcid = f'dcid:{dcid}'
        props = {}
        for k in sorted(record.keys()):
            if not k or k in ('Node', 'dcid',
                              'typeOf') or str(k).startswith('#'):
                continue
            props[k] = normalize_prop_val(record[k])

    return {
        'dcid': dcid,
        'typeOf': norm_type_of,
        'properties': props,
    }


def mcf_node_to_raw_bq_record(
    record: Dict[str, Any],
    stats: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Transforms a parsed MCF node dict into a unified BigQuery row without normalization."""
    raw_type_of = _format_raw_prop(record.get('typeOf', ''))
    is_obs = _is_observation_type(raw_type_of)
    if stats is not None:
        key = 'bq-obs-count' if is_obs else 'bq-schema-count'
        stats[key] = stats.get(key, 0) + 1
    dcid = _format_raw_prop(record.get('dcid') or record.get('Node', ''))
    props = {
        k: _format_raw_prop(record[k])
        for k in sorted(record.keys())
        if k and k not in ('Node', 'dcid',
                           'typeOf') and not str(k).startswith('#')
    }
    return {
        'dcid': dcid,
        'typeOf': raw_type_of,
        'properties': props,
    }


def ensure_bq_dataset(
    bq_client: bigquery.Client,
    dataset_ref: str,
    expiration_hours: Optional[int] = 12,
    update_existing_expiration: bool = False,
) -> None:
    """Ensures the BigQuery dataset exists, optionally updating default table TTL."""
    expected_ttl_ms = (int(expiration_hours) * 3600 * 1000
                       if expiration_hours and expiration_hours > 0 else None)
    try:
        ds = bq_client.get_dataset(dataset_ref)
        if (update_existing_expiration and expected_ttl_ms is not None and
                ds.default_table_expiration_ms != expected_ttl_ms):
            ds.default_table_expiration_ms = expected_ttl_ms
            bq_client.update_dataset(ds, ['default_table_expiration_ms'])
    except gcp_exceptions.NotFound:
        logging.info('Creating BigQuery dataset %s', dataset_ref)
        ds = bigquery.Dataset(dataset_ref)
        if expected_ttl_ms is not None:
            ds.default_table_expiration_ms = expected_ttl_ms
        bq_client.create_dataset(ds, exists_ok=True)


def set_bq_table_ttl(bq_client: bigquery.Client, table_ref: str,
                     expiration_hours: Optional[int]) -> None:
    """Sets the expiration timestamp on `table_ref` when `expiration_hours > 0`."""
    if not expiration_hours or expiration_hours <= 0:
        return
    table = bq_client.get_table(table_ref)
    table.expires = datetime.now(
        timezone.utc) + timedelta(hours=expiration_hours)
    bq_client.update_table(table, ['expires'])


def _remove_files_parallel(paths: Sequence[str]) -> None:
    """Deletes multiple local files or GCS blobs concurrently."""
    if not paths:
        return
    if len(paths) == 1 or all(not file_util.file_is_gcs(p) for p in paths):
        for path in paths:
            file_util.file_remove(path)
        return
    workers = min(32, len(paths))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(file_util.file_remove, paths))


class _ChainedLocalFileReader(io.RawIOBase):
    """Seekable binary reader chaining multiple local JSONL or CSV shard files."""

    mode = 'rb'

    def __init__(self, paths: Sequence[str], skip_subsequent_headers: bool):
        super().__init__()
        self._segments: List[Tuple[str, int, int]] = []
        self._cum_ends: List[int] = []
        total = 0
        for idx, path in enumerate(paths):
            file_size = os.path.getsize(path)
            header_skip = 0
            if skip_subsequent_headers and idx > 0 and file_size > 0:
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
        if not chunks:
            return b''
        return chunks[0] if len(chunks) == 1 else b''.join(chunks)

    def close(self) -> None:
        if self._cur_fh is not None:
            self._cur_fh.close()
            self._cur_fh = None
            self._cur_idx = None
        super().close()


def _infer_bq_source_format(path: str) -> str:
    """Infers the `bigquery.SourceFormat` constant from `path`'s extension."""
    ext = get_file_extension(path)
    if ext in ('.jsonl', '.ndjson', '.json'):
        return bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    if ext in ('.csv', '.tsv'):
        return bigquery.SourceFormat.CSV
    if ext == '.avro':
        return bigquery.SourceFormat.AVRO
    if ext == '.parquet':
        return bigquery.SourceFormat.PARQUET
    raise ValueError(f'Cannot infer BigQuery source format for file: {path}')


def _make_load_job_config(
    source_format: str,
    schema: Optional[Sequence[bigquery.SchemaField]],
    write_disposition: str,
    skip_leading_rows: Optional[int],
    field_delimiter: Optional[str] = None,
) -> bigquery.LoadJobConfig:
    """Builds a `bigquery.LoadJobConfig` for the requested format and schema."""
    kwargs: Dict[str, Any] = {
        'source_format': source_format,
        'write_disposition': write_disposition,
    }
    if schema is not None:
        kwargs['schema'] = list(schema)
    else:
        kwargs['autodetect'] = True

    if source_format == bigquery.SourceFormat.CSV:
        kwargs['skip_leading_rows'] = (1 if skip_leading_rows is None else
                                       skip_leading_rows)
        kwargs['allow_quoted_newlines'] = True
        if field_delimiter:
            kwargs['field_delimiter'] = field_delimiter
    return bigquery.LoadJobConfig(**kwargs)


def load_files_to_bq_table(
    bq_client: bigquery.Client,
    file_paths: Union[str, Sequence[str]],
    table_ref: str,
    schema: Optional[Sequence[bigquery.SchemaField]] = None,
    source_format: Optional[str] = None,
    expiration_hours: Optional[int] = 12,
    skip_leading_rows: Optional[int] = None,
    write_disposition: str = bigquery.WriteDisposition.WRITE_TRUNCATE,
) -> None:
    """Loads one or more local or GCS files into a BigQuery table with optional TTL.

    Supports newline-delimited JSON (`.jsonl`/`.ndjson`), CSV/TSV, Avro, and
    Parquet. Multiple GCS URIs are loaded via batched `load_table_from_uri()`
    (up to 10,000 URIs per job); multiple local CSV/JSONL shards are streamed in
    a single `load_table_from_file()` call via `_ChainedLocalFileReader`.
    """
    paths = [file_paths] if isinstance(file_paths, str) else list(file_paths)
    if not paths:
        fmt = source_format or bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        if fmt == bigquery.SourceFormat.CSV and schema:
            empty_payload = (','.join(f.name for f in schema) +
                             '\n').encode('utf-8')
        else:
            empty_payload = b''
        job_config = _make_load_job_config(
            source_format=fmt,
            schema=schema,
            write_disposition=write_disposition,
            skip_leading_rows=skip_leading_rows,
        )
        load_job = bq_client.load_table_from_file(io.BytesIO(empty_payload),
                                                  table_ref,
                                                  job_config=job_config)
        load_job.result()
        set_bq_table_ttl(bq_client, table_ref, expiration_hours)
        return

    fmt = source_format or _infer_bq_source_format(paths[0])
    field_delimiter = ('\t' if get_file_extension(paths[0]) == '.tsv' else None)

    if file_util.file_is_gcs(paths[0]):
        for batch_start in range(0, len(paths), _BQ_MAX_URIS_PER_LOAD):
            uri_batch = paths[batch_start:batch_start + _BQ_MAX_URIS_PER_LOAD]
            disposition = (write_disposition if batch_start == 0 else
                           bigquery.WriteDisposition.WRITE_APPEND)
            job_config = _make_load_job_config(
                source_format=fmt,
                schema=schema,
                write_disposition=disposition,
                skip_leading_rows=skip_leading_rows,
                field_delimiter=field_delimiter,
            )
            source_arg: Union[str, List[str]] = (uri_batch[0] if len(uri_batch)
                                                 == 1 else uri_batch)
            load_job = bq_client.load_table_from_uri(source_arg,
                                                     table_ref,
                                                     job_config=job_config)
            load_job.result()
    elif len(paths) == 1:
        job_config = _make_load_job_config(
            source_format=fmt,
            schema=schema,
            write_disposition=write_disposition,
            skip_leading_rows=skip_leading_rows,
            field_delimiter=field_delimiter,
        )
        with open(paths[0], 'rb') as fh:
            load_job = bq_client.load_table_from_file(fh,
                                                      table_ref,
                                                      job_config=job_config)
        load_job.result()
    elif fmt in (bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                 bigquery.SourceFormat.CSV):
        job_config = _make_load_job_config(
            source_format=fmt,
            schema=schema,
            write_disposition=write_disposition,
            skip_leading_rows=skip_leading_rows,
            field_delimiter=field_delimiter,
        )
        skip_headers = (fmt == bigquery.SourceFormat.CSV and
                        (skip_leading_rows is None or skip_leading_rows > 0))
        with _ChainedLocalFileReader(
                paths, skip_subsequent_headers=skip_headers) as chained_fh:
            load_job = bq_client.load_table_from_file(
                chained_fh,
                table_ref,
                size=chained_fh.total_size,
                job_config=job_config,
            )
        load_job.result()
    else:
        for idx, path in enumerate(paths):
            disposition = (write_disposition if idx == 0 else
                           bigquery.WriteDisposition.WRITE_APPEND)
            job_config = _make_load_job_config(
                source_format=fmt,
                schema=schema,
                write_disposition=disposition,
                skip_leading_rows=skip_leading_rows,
                field_delimiter=field_delimiter,
            )
            with open(path, 'rb') as fh:
                load_job = bq_client.load_table_from_file(fh,
                                                          table_ref,
                                                          job_config=job_config)
            load_job.result()

    set_bq_table_ttl(bq_client, table_ref, expiration_hours)


def convert_mcf_to_jsonl_shards(
    mcf_pattern: Union[str, Sequence[str]],
    output_dir: str,
    tag: str = '',
    max_workers: Optional[int] = None,
    chunk_size_bytes: int = _DEFAULT_CHUNK_BYTES,
    normalize: bool = True,
    process_pool: Optional[concurrent.futures.ProcessPoolExecutor] = None,
) -> Tuple[int, int, List[str]]:
    """Converts MCF files via `file_sharder` into unified-schema JSONL shards.

    Returns:
      Tuple of `(obs_count, schema_count, output_shard_paths)`.
    """
    files_with_sizes = file_util.file_list_with_sizes(mcf_pattern)
    if not files_with_sizes:
        return 0, 0, []

    total_bytes = sum(max(0, size) for _, size in files_with_sizes)
    workers = (max_workers if max_workers and max_workers > 0 else
               (os.cpu_count() or 1))
    if (total_bytes < _MIN_PARALLEL_TOTAL_BYTES and
            chunk_size_bytes >= _DEFAULT_CHUNK_BYTES):
        workers = 1

    is_gcs_dir = file_util.file_is_gcs(output_dir)
    base_dir = output_dir.rstrip('/')
    out_pattern = (f'{base_dir}/mcf{tag}*.jsonl' if is_gcs_dir else
                   os.path.join(base_dir, f'mcf{tag}*.jsonl'))

    transform_fn = (mcf_node_to_bq_record
                    if normalize else mcf_node_to_raw_bq_record)
    counters = Counters()
    shard_config = {
        'shard_routing': 'task',
        'shard_use_processes': workers > 1,
        'shard_threads': workers,
        'shard_min_chunk_size': chunk_size_bytes,
        'shard_record_transform': transform_fn,
        'shard_process_pool': process_pool,
    }
    logging.info(
        'Converting %d MCF file(s) (%.2f MiB) to JSONL shards via file_sharder (workers=%d)...',
        len(files_with_sizes),
        total_bytes / (1024 * 1024),
        workers,
    )
    shard_paths = file_sharder.shard_file(
        input_file=[p for p, _ in files_with_sizes],
        output_path=out_pattern,
        config=shard_config,
        counters=counters,
    )
    obs_count = int(counters.get_counter('bq-obs-count') or 0)
    schema_count = int(counters.get_counter('bq-schema-count') or 0)
    logging.info(
        'Completed MCF to JSONL conversion: %d obs, %d schema nodes across %d shard(s)',
        obs_count,
        schema_count,
        len(shard_paths),
    )
    return obs_count, schema_count, shard_paths


def load_mcf_to_bq_table(
    bq_client: bigquery.Client,
    mcf_pattern: Union[str, Sequence[str]],
    table_ref: str,
    temp_dir: Optional[str] = None,
    suffix: str = '',
    expiration_hours: Optional[int] = 12,
    max_workers: Optional[int] = None,
    chunk_size_bytes: int = _DEFAULT_CHUNK_BYTES,
    normalize: bool = True,
    process_pool: Optional[concurrent.futures.ProcessPoolExecutor] = None,
) -> Dict[str, int]:
    """Converts MCF files via `file_sharder` and loads them into one BigQuery table.

    Uses `MCF_BQ_SCHEMA` (`dcid STRING`, `typeOf STRING`, `properties JSON`) and
    cleans up temporary intermediate `.jsonl` shards after loading.

    Returns:
      Dictionary with `'obs_count'`, `'schema_count'`, and `'total_count'`.
    """
    with contextlib.ExitStack() as stack:
        base_dir = (temp_dir.rstrip('/') if temp_dir else stack.enter_context(
            tempfile.TemporaryDirectory()))
        tag = f'_{suffix}' if suffix else ''
        shard_paths: List[str] = []
        try:
            obs_count, schema_count, shard_paths = convert_mcf_to_jsonl_shards(
                mcf_pattern=mcf_pattern,
                output_dir=base_dir,
                tag=tag,
                max_workers=max_workers,
                chunk_size_bytes=chunk_size_bytes,
                normalize=normalize,
                process_pool=process_pool,
            )
            load_files_to_bq_table(
                bq_client=bq_client,
                file_paths=shard_paths,
                table_ref=table_ref,
                schema=MCF_BQ_SCHEMA,
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                expiration_hours=expiration_hours,
            )
        finally:
            _remove_files_parallel(shard_paths)
        return {
            'obs_count': obs_count,
            'schema_count': schema_count,
            'total_count': obs_count + schema_count,
        }


def get_mp_context():
    """Returns the multiprocessing context used by `file_sharder`."""
    return file_sharder._get_mp_context()


def _define_cli_flags():
    """Defines CLI flags when `bq_loader.py` is run directly as a script."""
    flags.DEFINE_string(
        'input_files', '',
        'Input file path or wildcard pattern (local or gs://; MCF/JSONL/CSV/Avro).'
    )
    flags.DEFINE_string(
        'table', '', 'Destination BigQuery table (`project.dataset.table`).')
    flags.DEFINE_string('project_id', '',
                        'GCP project ID (defaults to table project or env).')
    flags.DEFINE_string(
        'temp_dir', None,
        'Optional staging directory (local or gs://) for MCF-to-JSONL shards.')
    flags.DEFINE_integer(
        'expiration_hours', 12,
        'TTL in hours for the loaded BigQuery table (0=none).')
    flags.DEFINE_integer(
        'max_workers', 0,
        'Maximum parallel worker processes for MCF conversion (0 uses all CPUs).'
    )
    flags.DEFINE_integer(
        'chunk_size_mb', 8,
        'Minimum byte-range chunk size in MiB when splitting large MCF files.')
    flags.DEFINE_bool(
        'normalize', True,
        'Whether to normalize MCF property values when loading MCF files.')


def main(_):
    """CLI entrypoint for loading MCF or tabular files into BigQuery."""
    flag_values = flags.FLAGS
    if not flag_values.input_files or not flag_values.table:
        raise ValueError('Both --input_files and --table are required.')

    table_parts = flag_values.table.split('.')
    if len(table_parts) != 3:
        raise ValueError(
            f'--table must be project.dataset.table, got: {flag_values.table}')
    project_id = (flag_values.project_id or table_parts[0] or
                  os.environ.get('GOOGLE_CLOUD_PROJECT', ''))
    client_opts = {'quota_project_id': project_id} if project_id else None
    bq_client = bigquery.Client(project=project_id or None,
                                client_options=client_opts)
    dataset_ref = f'{table_parts[0]}.{table_parts[1]}'
    ensure_bq_dataset(bq_client,
                      dataset_ref,
                      expiration_hours=flag_values.expiration_hours)

    matched = file_util.file_get_matching(flag_values.input_files)
    if matched and is_mcf_file(matched[0]):
        counts = load_mcf_to_bq_table(
            bq_client=bq_client,
            mcf_pattern=flag_values.input_files,
            table_ref=flag_values.table,
            temp_dir=flag_values.temp_dir,
            expiration_hours=flag_values.expiration_hours,
            max_workers=flag_values.max_workers or None,
            chunk_size_bytes=max(1, flag_values.chunk_size_mb) * 1024 * 1024,
            normalize=flag_values.normalize,
        )
        logging.info('Loaded MCF to %s: %s', flag_values.table, counts)
    else:
        load_files_to_bq_table(
            bq_client=bq_client,
            file_paths=matched,
            table_ref=flag_values.table,
            expiration_hours=flag_values.expiration_hours,
        )
        logging.info('Loaded %d file(s) to %s', len(matched), flag_values.table)


if __name__ == '__main__':
    _define_cli_flags()
    app.run(main)
