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
"""BigQuery-based MCF differ for low-memory (O(1) RAM) parallel execution.

Loads current and previous `.mcf` datasets (local or `gs://` wildcard paths)
into combined temporary BigQuery tables (`dcid`, `typeOf`, `properties JSON`)
via `util/bq_loader.py` and `util/file_sharder.py`, executes BigQuery SQL
`FULL OUTER JOIN` queries so only changed nodes are downloaded, and streams
complete diff MCF files (`nodes-added.mcf`, `nodes-deleted.mcf`,
`nodes-modified.mcf`, `nodes-original.mcf`) along with per-StatVar counts
(`differ_summary.json` and `differ_summary.csv`) in `--output_location`.

To view all CLI flags, defaults, and usage details:
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

from collections import defaultdict
import concurrent.futures
import contextlib
import json
import os
import re
import sys
import tempfile
from typing import Any, Dict, Optional
from unittest import mock
import uuid

from absl import app
from absl import flags
from absl import logging
from google.cloud import bigquery
import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
for _path in (
        _DATA_DIR,
        _SCRIPT_DIR,
        os.path.join(_DATA_DIR, 'util'),
        os.path.join(_DATA_DIR, 'tools', 'statvar_importer'),
):
    if _path not in sys.path:
        sys.path.append(_path)

import bq_loader
import differ_utils
import file_util

OBSERVATION_KEY_PROPERTIES = [
    'variableMeasured',
    'observationAbout',
    'observationDate',
    'observationPeriod',
    'measurementMethod',
    'unit',
    'scalingFactor',
]

_DEFAULT_CHUNK_BYTES = 8 * 1024 * 1024  # 8 MiB minimum chunk size


def _sanitize_job_suffix(job_name: str) -> str:
    """Converts a job name into a safe BigQuery table suffix."""
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', job_name)
    return f'{cleaned}_{uuid.uuid4().hex[:8]}'


def _format_obs_mcf_node(obs_props: Dict[str, str], value: str,
                         node_id: str) -> str:
    """Reconstructs an observation MCF node block identically to `ImportDiffer`."""
    lines = []
    if node_id and node_id != 'nan':
        lines.append(f'Node: {node_id}')
    for prop in OBSERVATION_KEY_PROPERTIES:
        prop_val = obs_props.get(prop, '')
        if prop_val and prop_val != 'nan':
            lines.append(f'{prop}: {prop_val}')
    if value and value != 'nan':
        lines.append(f'value: {value}')
    lines.append('typeOf: StatVarObservation')
    return '\n'.join(lines) + '\n\n'


def _format_schema_mcf_node(dcid: str, type_of: str, props_json: str) -> str:
    """Reconstructs a schema MCF node block from dedicated fields and JSON properties."""
    lines = []
    dcid_str = dcid or ''
    if dcid_str.startswith('dcid:'):
        lines.append(f'dcid: {dcid_str[len("dcid:"):]}')
    else:
        lines.append(f'Node: {dcid_str}')

    props: Dict[str, Any] = {}
    if props_json:
        parsed = json.loads(props_json)
        if isinstance(parsed, dict):
            props.update(parsed)
    if type_of:
        props['typeOf'] = type_of

    for k in sorted(props.keys()):
        lines.append(f'{k}: {props[k]}')
    return '\n'.join(lines) + '\n\n'


def _row_val(row: Any, key: str) -> str:
    """Extracts a string value from a BigQuery Row or dict, returning '' for None."""
    val = row.get(key) if isinstance(row, dict) else getattr(row, key, None)
    return str(val) if val is not None else ''


def _join_output_path(output_location: str, filename: str) -> str:
    """Joins output directory and filename for local or `gs://` paths."""
    if file_util.file_is_gcs(output_location):
        return f"{output_location.rstrip('/')}/{filename}"
    return os.path.join(output_location, filename)


@contextlib.contextmanager
def _open_output_stream(path: str):
    """Opens a local file or `gs://` URI for streaming UTF-8 writes without `/tmp` staging."""
    if not file_util.file_is_gcs(path):
        file_util.file_makedirs(path)
    with file_util.FileIO(path,
                          mode='w',
                          encoding='utf-8',
                          newline='',
                          use_tempfile=False) as stream:
        yield stream


def _build_obs_diff_sql(curr_table: str, prev_table: str) -> str:
    """Builds the BigQuery SQL query for diffing observation rows in unified MCF tables.

    Observations join on the 7 normalized identity properties extracted from the
    `properties` JSON column (not on `dcid`, since observation DCIDs hash
    `value`). Values are compared numerically when both parse as finite numbers
    (using `BIGNUMERIC` alongside `FLOAT64`), preserving raw value text for
    emitted diff MCF files. Only changed rows are returned.
    """
    return f"""
    WITH curr_obs AS (
      SELECT
        dcid AS node_id,
        COALESCE(JSON_VALUE(properties, '$.variableMeasured'), '') AS variableMeasured,
        COALESCE(JSON_VALUE(properties, '$.observationAbout'), '') AS observationAbout,
        COALESCE(JSON_VALUE(properties, '$.observationDate'), '') AS observationDate,
        COALESCE(JSON_VALUE(properties, '$.observationPeriod'), '') AS observationPeriod,
        COALESCE(JSON_VALUE(properties, '$.measurementMethod'), '') AS measurementMethod,
        COALESCE(JSON_VALUE(properties, '$.unit'), '') AS unit,
        COALESCE(JSON_VALUE(properties, '$.scalingFactor'), '') AS scalingFactor,
        COALESCE(JSON_VALUE(properties, '$.value'), '') AS value
      FROM `{curr_table}`
      WHERE CONTAINS_SUBSTR(COALESCE(typeOf, ''), 'StatVarObservation')
    ),
    prev_obs AS (
      SELECT
        dcid AS node_id,
        COALESCE(JSON_VALUE(properties, '$.variableMeasured'), '') AS variableMeasured,
        COALESCE(JSON_VALUE(properties, '$.observationAbout'), '') AS observationAbout,
        COALESCE(JSON_VALUE(properties, '$.observationDate'), '') AS observationDate,
        COALESCE(JSON_VALUE(properties, '$.observationPeriod'), '') AS observationPeriod,
        COALESCE(JSON_VALUE(properties, '$.measurementMethod'), '') AS measurementMethod,
        COALESCE(JSON_VALUE(properties, '$.unit'), '') AS unit,
        COALESCE(JSON_VALUE(properties, '$.scalingFactor'), '') AS scalingFactor,
        COALESCE(JSON_VALUE(properties, '$.value'), '') AS value
      FROM `{prev_table}`
      WHERE CONTAINS_SUBSTR(COALESCE(typeOf, ''), 'StatVarObservation')
    )
    SELECT *
    FROM (
      SELECT
        COALESCE(c.variableMeasured, p.variableMeasured) AS variableMeasured,
        COALESCE(c.observationAbout, p.observationAbout) AS observationAbout,
        COALESCE(c.observationDate, p.observationDate) AS observationDate,
        COALESCE(c.observationPeriod, p.observationPeriod) AS observationPeriod,
        COALESCE(c.measurementMethod, p.measurementMethod) AS measurementMethod,
        COALESCE(c.unit, p.unit) AS unit,
        COALESCE(c.scalingFactor, p.scalingFactor) AS scalingFactor,
        c.value AS curr_value,
        p.value AS prev_value,
        c.node_id AS curr_node,
        p.node_id AS prev_node,
        CASE
          WHEN p.variableMeasured IS NULL THEN 'ADDED'
          WHEN c.variableMeasured IS NULL THEN 'DELETED'
          WHEN c.value IS DISTINCT FROM p.value
            AND NOT COALESCE(
              SAFE_CAST(c.value AS BIGNUMERIC) = SAFE_CAST(p.value AS BIGNUMERIC)
              AND SAFE_CAST(c.value AS FLOAT64) = SAFE_CAST(p.value AS FLOAT64),
              FALSE) THEN 'MODIFIED'
          ELSE 'UNMODIFIED'
        END AS diff_type
      FROM curr_obs c
      FULL OUTER JOIN prev_obs p
        ON c.variableMeasured = p.variableMeasured
       AND c.observationAbout = p.observationAbout
       AND c.observationDate = p.observationDate
       AND c.observationPeriod = p.observationPeriod
       AND c.measurementMethod = p.measurementMethod
       AND c.unit = p.unit
       AND c.scalingFactor = p.scalingFactor
    )
    WHERE diff_type != 'UNMODIFIED'
    """


def _build_schema_diff_sql(curr_table: str, prev_table: str) -> str:
    """Builds the BigQuery SQL query for diffing non-observation nodes in unified MCF tables.

    Uses `TO_JSON_STRING(properties)` (lexicographically canonicalized by
    BigQuery) so `SELECT DISTINCT` and inequality checks run directly inside
    BigQuery and only changed nodes are returned.
    """
    return f"""
    WITH curr_schema AS (
      SELECT DISTINCT
        COALESCE(dcid, '') AS dcid,
        COALESCE(typeOf, '') AS typeOf,
        COALESCE(TO_JSON_STRING(properties), '{{}}') AS props_json
      FROM `{curr_table}`
      WHERE NOT CONTAINS_SUBSTR(COALESCE(typeOf, ''), 'StatVarObservation')
    ),
    prev_schema AS (
      SELECT DISTINCT
        COALESCE(dcid, '') AS dcid,
        COALESCE(typeOf, '') AS typeOf,
        COALESCE(TO_JSON_STRING(properties), '{{}}') AS props_json
      FROM `{prev_table}`
      WHERE NOT CONTAINS_SUBSTR(COALESCE(typeOf, ''), 'StatVarObservation')
    )
    SELECT *
    FROM (
      SELECT
        COALESCE(c.dcid, p.dcid) AS dcid,
        c.typeOf AS curr_type,
        p.typeOf AS prev_type,
        c.props_json AS curr_props,
        p.props_json AS prev_props,
        CASE
          WHEN p.dcid IS NULL THEN 'ADDED'
          WHEN c.dcid IS NULL THEN 'DELETED'
          WHEN c.typeOf IS DISTINCT FROM p.typeOf
            OR c.props_json IS DISTINCT FROM p.props_json THEN 'MODIFIED'
          ELSE 'UNMODIFIED'
        END AS diff_type
      FROM curr_schema c
      FULL OUTER JOIN prev_schema p
        ON c.dcid = p.dcid
    )
    WHERE diff_type != 'UNMODIFIED'
    """


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
    chunk_size_bytes: int = _DEFAULT_CHUNK_BYTES,
) -> Dict:
    """Executes dataset diff using `util/bq_loader.py` and BigQuery FULL OUTER JOIN."""
    if not project_id:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get(
            'PROJECT_ID', '')

    client_opts = {'quota_project_id': project_id} if project_id else None
    bq_client = bigquery.Client(project=project_id or None,
                                client_options=client_opts)
    if not project_id:
        project_id = getattr(bq_client, 'project', '') or ''
    dataset_ref = f'{project_id}.{dataset_id}'
    bq_loader.ensure_bq_dataset(
        bq_client,
        dataset_ref,
        expiration_hours=expiration_hours,
        update_existing_expiration=dataset_ref.endswith(
            '.datcom_import_differ'),
    )

    suffix = _sanitize_job_suffix(job_name)
    curr_table = f'{dataset_ref}.curr_{suffix}'
    prev_table = f'{dataset_ref}.prev_{suffix}'
    logging.info(
        'Using BigQuery differ tables (TTL=%dh, suffix=%s): %s, %s',
        expiration_hours,
        suffix,
        curr_table,
        prev_table,
    )

    workers = (max_workers if max_workers and max_workers > 0 else
               (os.cpu_count() or 1))
    use_concurrent_loads = (workers > 1 and
                            not isinstance(bq_client, mock.Mock))

    if use_concurrent_loads:
        logging.info(
            'Steps 1-2/3: Loading current and previous MCF datasets in parallel (workers=%d)...',
            workers,
        )
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=workers,
                mp_context=bq_loader.get_mp_context(),
        ) as shared_proc_pool, concurrent.futures.ThreadPoolExecutor(
                max_workers=2) as step_pool:
            curr_future = step_pool.submit(
                bq_loader.load_mcf_to_bq_table,
                bq_client,
                current_data,
                curr_table,
                gcs_temp_dir,
                f'curr_{suffix}',
                expiration_hours,
                workers,
                chunk_size_bytes,
                True,
                shared_proc_pool,
            )
            prev_future = step_pool.submit(
                bq_loader.load_mcf_to_bq_table,
                bq_client,
                previous_data,
                prev_table,
                gcs_temp_dir,
                f'prev_{suffix}',
                expiration_hours,
                workers,
                chunk_size_bytes,
                True,
                shared_proc_pool,
            )
            curr_counts = curr_future.result()
            prev_counts = prev_future.result()
    else:
        logging.info('Step 1/3: Loading current MCF data into BigQuery...')
        curr_counts = bq_loader.load_mcf_to_bq_table(
            bq_client=bq_client,
            mcf_pattern=current_data,
            table_ref=curr_table,
            temp_dir=gcs_temp_dir,
            suffix=f'curr_{suffix}',
            expiration_hours=expiration_hours,
            max_workers=workers,
            chunk_size_bytes=chunk_size_bytes,
        )

        logging.info('Step 2/3: Loading previous MCF data into BigQuery...')
        prev_counts = bq_loader.load_mcf_to_bq_table(
            bq_client=bq_client,
            mcf_pattern=previous_data,
            table_ref=prev_table,
            temp_dir=gcs_temp_dir,
            suffix=f'prev_{suffix}',
            expiration_hours=expiration_hours,
            max_workers=workers,
            chunk_size_bytes=chunk_size_bytes,
        )

    curr_obs_count = curr_counts['obs_count']
    curr_schema_count = curr_counts['schema_count']
    prev_obs_count = prev_counts['obs_count']
    prev_schema_count = prev_counts['schema_count']

    logging.info('Step 3/3: Running BigQuery FULL OUTER JOIN diff...')
    obs_diff_sql = _build_obs_diff_sql(curr_table, prev_table)
    schema_diff_sql = _build_schema_diff_sql(curr_table, prev_table)

    statvar_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {
        'ADDED': 0,
        'DELETED': 0,
        'MODIFIED': 0
    })
    schema_counts = {'ADDED': 0, 'DELETED': 0, 'MODIFIED': 0}

    for fname in ('nodes-added.mcf', 'nodes-deleted.mcf', 'nodes-modified.mcf',
                  'nodes-original.mcf'):
        file_util.file_remove(_join_output_path(output_location, fname))

    with contextlib.ExitStack() as mcf_stack:
        open_streams: Dict[str, Any] = {}

        def _write_mcf_block(filename: str, block: str) -> None:
            if filename not in open_streams:
                out_path = _join_output_path(output_location, filename)
                open_streams[filename] = mcf_stack.enter_context(
                    _open_output_stream(out_path))
            open_streams[filename].write(block)

        for row in bq_client.query(obs_diff_sql).result():
            diff_type = _row_val(row, 'diff_type')
            obs_props = {
                prop: _row_val(row, prop) for prop in OBSERVATION_KEY_PROPERTIES
            }
            raw_sv = obs_props['variableMeasured']
            stat_var = (raw_sv[len('dcid:'):]
                        if raw_sv.startswith('dcid:') else raw_sv)
            if diff_type in ('ADDED', 'DELETED', 'MODIFIED'):
                statvar_counts[stat_var][diff_type] += 1
            if diff_type == 'ADDED':
                _write_mcf_block(
                    'nodes-added.mcf',
                    _format_obs_mcf_node(obs_props, _row_val(row, 'curr_value'),
                                         _row_val(row, 'curr_node')))
            elif diff_type == 'DELETED':
                _write_mcf_block(
                    'nodes-deleted.mcf',
                    _format_obs_mcf_node(obs_props, _row_val(row, 'prev_value'),
                                         _row_val(row, 'prev_node')))
            elif diff_type == 'MODIFIED':
                _write_mcf_block(
                    'nodes-modified.mcf',
                    _format_obs_mcf_node(obs_props, _row_val(row, 'curr_value'),
                                         _row_val(row, 'curr_node')))
                _write_mcf_block(
                    'nodes-original.mcf',
                    _format_obs_mcf_node(obs_props, _row_val(row, 'prev_value'),
                                         _row_val(row, 'prev_node')))

        for row in bq_client.query(schema_diff_sql).result():
            diff_type = _row_val(row, 'diff_type')
            dcid = _row_val(row, 'dcid')
            if diff_type in schema_counts:
                schema_counts[diff_type] += 1
            if diff_type == 'ADDED':
                _write_mcf_block(
                    'nodes-added.mcf',
                    _format_schema_mcf_node(dcid, _row_val(row, 'curr_type'),
                                            _row_val(row, 'curr_props')))
            elif diff_type == 'DELETED':
                _write_mcf_block(
                    'nodes-deleted.mcf',
                    _format_schema_mcf_node(dcid, _row_val(row, 'prev_type'),
                                            _row_val(row, 'prev_props')))
            elif diff_type == 'MODIFIED':
                _write_mcf_block(
                    'nodes-modified.mcf',
                    _format_schema_mcf_node(dcid, _row_val(row, 'curr_type'),
                                            _row_val(row, 'curr_props')))
                _write_mcf_block(
                    'nodes-original.mcf',
                    _format_schema_mcf_node(dcid, _row_val(row, 'prev_type'),
                                            _row_val(row, 'prev_props')))

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
            'Optional temporary directory path for intermediate JSONL shards.')
    if 'bq_table_ttl_hours' not in _FLAGS:
        flags.DEFINE_integer(
            'bq_table_ttl_hours', 12,
            'TTL in hours for temporary BigQuery differ tables.')
    if 'max_workers' not in _FLAGS:
        flags.DEFINE_integer(
            'max_workers', 0,
            'Maximum parallel worker processes for MCF conversion (0 uses all CPUs).'
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
