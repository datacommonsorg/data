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
"""BigQuery-based MCF differ for low-memory ($O(1)$ RAM) execution.

Streams current and previous `.mcf` files (local or `gs://` wildcard paths) into
normalized observation and schema CSVs in constant memory, loads them into
ephemeral BigQuery tables, executes SQL FULL OUTER JOIN queries to compute
per-StatVar ADDED/DELETED/MODIFIED counts, writes `differ_summary.json` and
`differ_summary.csv` to `--output_location`, and drops the temporary tables.

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

import contextlib
import csv
from datetime import datetime, timedelta, timezone
import io
import os
import re
import sys
import tempfile
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from absl import app
from absl import flags
from absl import logging
from google.cloud import bigquery
from google.cloud import storage

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.join(_DATA_DIR, 'util'))
sys.path.append(os.path.join(_DATA_DIR, 'tools', 'statvar_importer'))

import differ_utils
from file_util import file_get_gcs_blob, file_get_matching, file_is_gcs
from mcf_file_util import normalize_value, strip_namespace, strip_value

OBSERVATION_KEY_PROPERTIES = [
    'variableMeasured',
    'observationAbout',
    'observationDate',
    'observationPeriod',
    'measurementMethod',
    'unit',
    'scalingFactor',
]

OBS_CSV_COLUMNS = [
    'key_combined',
    'variableMeasured',
    'value',
    'observationAbout',
    'observationDate',
    'observationPeriod',
    'measurementMethod',
    'unit',
    'scalingFactor',
    'row_num',
]

OBS_BQ_SCHEMA = [
    bigquery.SchemaField('key_combined', 'STRING'),
    bigquery.SchemaField('variableMeasured', 'STRING'),
    bigquery.SchemaField('value', 'STRING'),
    bigquery.SchemaField('observationAbout', 'STRING'),
    bigquery.SchemaField('observationDate', 'STRING'),
    bigquery.SchemaField('observationPeriod', 'STRING'),
    bigquery.SchemaField('measurementMethod', 'STRING'),
    bigquery.SchemaField('unit', 'STRING'),
    bigquery.SchemaField('scalingFactor', 'STRING'),
    bigquery.SchemaField('row_num', 'INT64'),
]

SCHEMA_NODE_BQ_SCHEMA = [
    bigquery.SchemaField('dcid', 'STRING'),
    bigquery.SchemaField('value_combined', 'STRING'),
]


def get_import_bq_table_ids(
    dataset_ref: str,
    import_name: str,
    version: str,
    input_prefix: str = 'input0',
) -> Dict[str, str]:
    """Returns deterministic BigQuery table IDs shared between aggregator and validator jobs."""
    safe_import = re.sub(r'[^a-zA-Z0-9_]', '_', import_name)
    safe_version = re.sub(r'[^a-zA-Z0-9_]', '_', version)
    safe_prefix = re.sub(r'[^a-zA-Z0-9_]', '_', input_prefix)
    tag = f'{safe_import}_{safe_version}_{safe_prefix}'
    return {
        'raw_obs': f'{dataset_ref}.raw_obs_{tag}',
        'raw_schema': f'{dataset_ref}.raw_schema_{tag}',
        'agg_obs': f'{dataset_ref}.agg_obs_{tag}',
    }


def format_key_combined_sql(
    var_expr: str,
    about_expr: str,
    date_expr: str,
    period_expr: str,
    method_expr: str,
    unit_expr: str,
    scaling_expr: str,
) -> str:
    """Returns a SQL expression computing key_combined identical to _flush_node_to_csv."""

    def _dcid_sql(expr: str) -> str:
        return (
            f"CASE WHEN COALESCE({expr}, '') = '' THEN '' "
            f"WHEN {expr} LIKE 'dcid:%' THEN {expr} "
            f"ELSE CONCAT('dcid:', {expr}) END"
        )

    def _quote_sql(expr: str) -> str:
        return (
            f"CASE WHEN COALESCE({expr}, '') = '' THEN '' "
            f"WHEN {expr} LIKE '\"%\"' THEN {expr} "
            f"ELSE CONCAT('\"', {expr}, '\"') END"
        )

    return (
        f"CONCAT("
        f"{_dcid_sql(var_expr)}, ';', "
        f"{_dcid_sql(about_expr)}, ';', "
        f"{_quote_sql(date_expr)}, ';', "
        f"{_quote_sql(period_expr)}, ';', "
        f"{_dcid_sql(method_expr)}, ';', "
        f"{_dcid_sql(unit_expr)}, ';', "
        f"{_quote_sql(scaling_expr)}"
        f")"
    )


def cleanup_shared_bq_tables(
    project_id: str,
    shared_table_ids: Optional[Dict[str, str]],
    bq_client: Optional[bigquery.Client] = None,
) -> None:
    """Deletes shared temporary BigQuery tables (raw_obs, raw_schema, agg_obs) if they exist."""
    if not shared_table_ids:
        return
    if not project_id:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get(
            'PROJECT_ID', '')
    try:
        client = bq_client or bigquery.Client(project=project_id)
        for key in ('raw_obs', 'raw_schema', 'agg_obs'):
            table_id = shared_table_ids.get(key)
            if table_id:
                client.delete_table(table_id, not_found_ok=True)
    except Exception as exc:
        logging.warning('Failed to clean up shared BigQuery tables %s: %s',
                        shared_table_ids, exc)


def ensure_bq_dataset(bq_client: bigquery.Client,
                      dataset_ref: str,
                      expiration_hours: int = 12) -> None:
    """Creates or updates the BigQuery dataset with the specified default table TTL."""
    expected_ttl_ms = expiration_hours * 3600 * 1000
    try:
        ds = bq_client.get_dataset(dataset_ref)
        if ds.default_table_expiration_ms != expected_ttl_ms:
            ds.default_table_expiration_ms = expected_ttl_ms
            bq_client.update_dataset(ds, ['default_table_expiration_ms'])
    except Exception:
        logging.info('Creating BigQuery dataset %s', dataset_ref)
        ds = bigquery.Dataset(dataset_ref)
        ds.default_table_expiration_ms = expected_ttl_ms
        bq_client.create_dataset(ds, exists_ok=True)


def _normalize_prop_val(value) -> str:
    """Normalizes a property value string identically to ImportDiffer."""
    if isinstance(value, list):
        return ', '.join(sorted([_normalize_prop_val(v) for v in value]))
    if isinstance(value, str):
        return str(normalize_value(value))
    return str(value) if value is not None else ''


def _clean_prop_val(value) -> str:
    """Strips namespace prefixes (dcid:, dcs:, schema:) and surrounding quotes."""
    if value is None:
        return ''
    if isinstance(value, list):
        value = value[-1] if value else ''
    val = strip_value(str(value)).strip()
    if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
        val = val[1:-1].strip()
    return strip_namespace(val).strip('"').strip()


def _flush_node_to_csv(node: Dict[str, Any],
                       obs_writer: csv.writer,
                       schema_writer: csv.writer,
                       row_num: int = 1) -> Tuple[int, int]:
    """Writes a single parsed MCF node to either the observation or schema CSV writer."""
    type_of = node.get('typeOf', '')
    type_of_list = type_of if isinstance(type_of, list) else [type_of]
    if any('StatVarObservation' in str(t) for t in type_of_list):
        key_parts = [
            _normalize_prop_val(node.get(prop, ''))
            for prop in OBSERVATION_KEY_PROPERTIES
        ]
        key_combined = ';'.join(key_parts)
        var_measured = _normalize_prop_val(node.get('variableMeasured', ''))
        val = _normalize_prop_val(node.get('value', ''))
        obs_about = _clean_prop_val(node.get('observationAbout', ''))
        obs_date = _clean_prop_val(node.get('observationDate', ''))
        obs_period = _clean_prop_val(node.get('observationPeriod', ''))
        m_method = _clean_prop_val(node.get('measurementMethod', ''))
        unit = _clean_prop_val(node.get('unit', ''))
        scaling = _clean_prop_val(node.get('scalingFactor', ''))
        obs_writer.writerow([
            key_combined,
            var_measured,
            val,
            obs_about,
            obs_date,
            obs_period,
            m_method,
            unit,
            scaling,
            row_num,
        ])
        return 1, 0
    else:
        raw_id = node.get('dcid') or node.get('Node', '')
        dcid = _normalize_prop_val(raw_id)
        if dcid and not dcid.startswith('dcid:'):
            dcid = f'dcid:{dcid}'
        props = []
        for k in sorted(node.keys()):
            if k not in ('Node', 'dcid'):
                props.append(f'{k}:{_normalize_prop_val(node[k])}')
        value_combined = ';'.join(props)
        schema_writer.writerow([dcid, value_combined])
        return 0, 1


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
            raw_stream = storage.fileio.BlobWriter(blob)
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


def _remove_temp_file(path: str) -> None:
    """Deletes a temporary local file or gs:// blob if it exists."""
    try:
        if file_is_gcs(path):
            blob = file_get_gcs_blob(path, exists=True)
            if blob:
                blob.delete()
        elif os.path.exists(path):
            os.remove(path)
    except Exception as exc:
        logging.warning('Failed to remove temporary file %s: %s', path, exc)


def stream_mcf_to_csv(
    mcf_pattern: str,
    obs_csv_path: str,
    schema_csv_path: str,
    exclude_filenames: Optional[Set[str]] = None,
) -> Tuple[int, int]:
    """Streams MCF files node-by-node into observation and schema CSVs in O(1) memory."""
    mcf_files = file_get_matching(mcf_pattern)
    if exclude_filenames:
        mcf_files = [
            f for f in mcf_files if os.path.basename(f) not in exclude_filenames
        ]
    total_obs = 0
    total_schema = 0

    with _open_text_stream(obs_csv_path, mode='w') as obs_file, \
         _open_text_stream(schema_csv_path, mode='w') as schema_file:
        obs_writer = csv.writer(obs_file)
        schema_writer = csv.writer(schema_file)
        obs_writer.writerow(OBS_CSV_COLUMNS)
        schema_writer.writerow(['dcid', 'value_combined'])

        for mcf_file in mcf_files:
            logging.info('Streaming MCF file to CSV: %s', mcf_file)
            with _open_text_stream(mcf_file, mode='r') as in_f:
                current_node: Dict[str, Any] = {}
                for raw_line in in_f:
                    line = raw_line.strip()
                    if not line or line.startswith('#'):
                        if current_node:
                            o_inc, s_inc = _flush_node_to_csv(
                                current_node,
                                obs_writer,
                                schema_writer,
                                row_num=total_obs + 1)
                            total_obs += o_inc
                            total_schema += s_inc
                            current_node = {}
                        continue
                    if ':' in line:
                        k, v = line.split(':', 1)
                        k = k.strip()
                        v = v.strip()
                        if k == 'Node' and current_node:
                            o_inc, s_inc = _flush_node_to_csv(
                                current_node,
                                obs_writer,
                                schema_writer,
                                row_num=total_obs + 1)
                            total_obs += o_inc
                            total_schema += s_inc
                            current_node = {}
                        if k in current_node:
                            if isinstance(current_node[k], list):
                                current_node[k].append(v)
                            else:
                                current_node[k] = [current_node[k], v]
                        else:
                            current_node[k] = v
                if current_node:
                    o_inc, s_inc = _flush_node_to_csv(current_node,
                                                      obs_writer,
                                                      schema_writer,
                                                      row_num=total_obs + 1)
                    total_obs += o_inc
                    total_schema += s_inc

    logging.info('Completed streaming MCF to CSV: %d obs, %d schema nodes',
                 total_obs, total_schema)
    return total_obs, total_schema


def load_csv_to_bq_table(bq_client: bigquery.Client,
                         csv_path: str,
                         table_ref: str,
                         schema: List[bigquery.SchemaField],
                         expiration_hours: int = 12) -> None:
    """Loads a local or GCS CSV file into a BigQuery table with a specified TTL."""
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        allow_quoted_newlines=True,
    )
    if csv_path.startswith('gs://'):
        load_job = bq_client.load_table_from_uri(csv_path,
                                                 table_ref,
                                                 job_config=job_config)
    else:
        with open(csv_path, 'rb') as f:
            load_job = bq_client.load_table_from_file(f,
                                                      table_ref,
                                                      job_config=job_config)
    load_job.result()

    table = bq_client.get_table(table_ref)
    table.expires = datetime.now(
        timezone.utc) + timedelta(hours=expiration_hours)
    bq_client.update_table(table, ['expires'])


def load_mcf_to_bq_tables(
    bq_client: bigquery.Client,
    mcf_pattern: str,
    obs_table_ref: str,
    schema_table_ref: Optional[str] = None,
    temp_dir: Optional[str] = None,
    suffix: str = '',
    expiration_hours: int = 12,
    exclude_filenames: Optional[Set[str]] = None,
) -> Tuple[int, int]:
    """Streams MCF files to CSVs and loads them into BigQuery observation and schema tables."""
    with contextlib.ExitStack() as stack:
        base_dir = (temp_dir.rstrip('/') if temp_dir else stack.enter_context(
            tempfile.TemporaryDirectory()))
        tag = f'_{suffix}' if suffix else ''
        obs_csv = (f'{base_dir}/obs{tag}.csv' if file_is_gcs(base_dir) else
                   os.path.join(base_dir, f'obs{tag}.csv'))
        schema_csv = (f'{base_dir}/schema{tag}.csv' if file_is_gcs(base_dir)
                      else os.path.join(base_dir, f'schema{tag}.csv'))

        try:
            obs_count, schema_count = stream_mcf_to_csv(
                mcf_pattern,
                obs_csv,
                schema_csv,
                exclude_filenames=exclude_filenames)
            try:
                load_csv_to_bq_table(bq_client, obs_csv, obs_table_ref,
                                     OBS_BQ_SCHEMA, expiration_hours)
            finally:
                _remove_temp_file(obs_csv)
            if schema_table_ref:
                try:
                    load_csv_to_bq_table(bq_client, schema_csv,
                                         schema_table_ref,
                                         SCHEMA_NODE_BQ_SCHEMA,
                                         expiration_hours)
                finally:
                    _remove_temp_file(schema_csv)
        finally:
            _remove_temp_file(obs_csv)
            _remove_temp_file(schema_csv)
        return obs_count, schema_count


def _sanitize_job_suffix(job_name: str) -> str:
    """Converts a job name into a safe BigQuery table suffix."""
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', job_name)
    return f'{cleaned}_{uuid.uuid4().hex[:8]}'


def _get_existing_bq_table(bq_client: bigquery.Client,
                           table_ref: Optional[str]) -> Optional[Any]:
    """Returns the BigQuery Table object if table_ref exists, else None."""
    if not table_ref:
        return None
    try:
        return bq_client.get_table(table_ref)
    except Exception:
        return None


def _get_table_num_rows(table_obj: Any) -> int:
    """Extracts an integer row count from a BigQuery Table object if available."""
    num_rows = getattr(table_obj, 'num_rows', 0)
    return int(num_rows) if isinstance(num_rows, (int, float)) else 0


def run_bigquery_differ(
    current_data: str,
    previous_data: str,
    output_location: str,
    project_id: str,
    job_name: str = 'differ',
    dataset_id: str = 'datcom_import_differ',
    gcs_temp_dir: Optional[str] = None,
    expiration_hours: int = 12,
    shared_table_ids: Optional[Dict[str, str]] = None,
) -> Dict:
    """Executes dataset diff using streaming MCF-to-CSV and BigQuery FULL OUTER JOIN."""
    if not project_id:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get(
            'PROJECT_ID', '')

    bq_client = bigquery.Client(project=project_id)
    dataset_ref = f'{project_id}.{dataset_id}'
    ensure_bq_dataset(bq_client, dataset_ref, expiration_hours=expiration_hours)

    suffix = _sanitize_job_suffix(job_name)
    curr_obs_table = f'{dataset_ref}.curr_obs_{suffix}'
    prev_obs_table = f'{dataset_ref}.prev_obs_{suffix}'
    curr_schema_table = f'{dataset_ref}.curr_schema_{suffix}'
    prev_schema_table = f'{dataset_ref}.prev_schema_{suffix}'

    raw_obs_table = shared_table_ids.get('raw_obs') if shared_table_ids else None
    raw_schema_table = (shared_table_ids.get('raw_schema')
                        if shared_table_ids else None)
    agg_obs_table = shared_table_ids.get('agg_obs') if shared_table_ids else None

    tables_to_delete: List[str] = []

    try:
        raw_obs_tbl_obj = _get_existing_bq_table(bq_client, raw_obs_table)
        if raw_obs_table and raw_obs_tbl_obj is not None:
            logging.info(
                'Step 1/3: Reusing existing BigQuery table %s from aggregation job...',
                raw_obs_table)
            active_curr_obs_table = raw_obs_table
            curr_obs_count = _get_table_num_rows(raw_obs_tbl_obj)

            agg_obs_tbl_obj = _get_existing_bq_table(bq_client, agg_obs_table)
            has_agg_obs = bool(agg_obs_table and agg_obs_tbl_obj is not None)
            if has_agg_obs:
                curr_obs_count += _get_table_num_rows(agg_obs_tbl_obj)

            raw_schema_tbl_obj = _get_existing_bq_table(bq_client,
                                                        raw_schema_table)
            if raw_schema_table and raw_schema_tbl_obj is not None:
                active_curr_schema_table = raw_schema_table
                curr_schema_count = _get_table_num_rows(raw_schema_tbl_obj)
            else:
                active_curr_schema_table = raw_schema_table or curr_schema_table
                curr_schema_count = 0

            tables_to_delete = [
                t for t in (raw_obs_table, raw_schema_table, agg_obs_table,
                            prev_obs_table, prev_schema_table) if t
            ]
        else:
            has_agg_obs = False
            active_curr_obs_table = curr_obs_table
            active_curr_schema_table = curr_schema_table
            if shared_table_ids:
                tables_to_delete = [
                    t for t in (curr_obs_table, prev_obs_table,
                                curr_schema_table, prev_schema_table,
                                raw_obs_table, raw_schema_table, agg_obs_table)
                    if t
                ]
            else:
                tables_to_delete = [
                    curr_obs_table, prev_obs_table, curr_schema_table,
                    prev_schema_table
                ]

            logging.info('Step 1/3: Loading current MCF data into BigQuery...')
            curr_obs_count, curr_schema_count = load_mcf_to_bq_tables(
                bq_client,
                current_data,
                curr_obs_table,
                curr_schema_table,
                temp_dir=gcs_temp_dir,
                suffix=f'curr_{suffix}',
                expiration_hours=expiration_hours)

        logging.info('Step 2/3: Loading previous MCF data into BigQuery...')
        prev_obs_count, prev_schema_count = load_mcf_to_bq_tables(
            bq_client,
            previous_data,
            prev_obs_table,
            prev_schema_table,
            temp_dir=gcs_temp_dir,
            suffix=f'prev_{suffix}',
            expiration_hours=expiration_hours)

        logging.info('Step 3/3: Running BigQuery FULL OUTER JOIN diff...')
        if has_agg_obs and agg_obs_table:
            curr_obs_source_sql = f"""(
              SELECT key_combined, variableMeasured, value FROM `{active_curr_obs_table}`
              UNION ALL
              SELECT key_combined, variableMeasured, value FROM `{agg_obs_table}`
            )"""
        else:
            curr_obs_source_sql = f'`{active_curr_obs_table}`'

        obs_diff_sql = f"""
        WITH diff AS (
          SELECT
            COALESCE(c.variableMeasured, p.variableMeasured) AS variableMeasured,
            CASE
              WHEN p.key_combined IS NULL THEN 'ADDED'
              WHEN c.key_combined IS NULL THEN 'DELETED'
              WHEN c.value != p.value THEN 'MODIFIED'
              ELSE 'UNMODIFIED'
            END AS diff_type
          FROM {curr_obs_source_sql} c
          FULL OUTER JOIN `{prev_obs_table}` p
            ON c.key_combined = p.key_combined
          WHERE c.value IS DISTINCT FROM p.value
        )
        SELECT
          REGEXP_REPLACE(variableMeasured, '^dcid:', '') AS StatVar,
          COUNTIF(diff_type = 'ADDED') AS ADDED,
          COUNTIF(diff_type = 'DELETED') AS DELETED,
          COUNTIF(diff_type = 'MODIFIED') AS MODIFIED
        FROM diff
        GROUP BY StatVar
        ORDER BY StatVar
        """
        obs_diff_df = bq_client.query(obs_diff_sql).to_dataframe()

        schema_diff_sql = f"""
        WITH diff AS (
          SELECT
            CASE
              WHEN p.dcid IS NULL THEN 'ADDED'
              WHEN c.dcid IS NULL THEN 'DELETED'
              WHEN c.value_combined != p.value_combined THEN 'MODIFIED'
              ELSE 'UNMODIFIED'
            END AS diff_type
          FROM `{active_curr_schema_table}` c
          FULL OUTER JOIN `{prev_schema_table}` p
            ON c.dcid = p.dcid
          WHERE c.value_combined IS DISTINCT FROM p.value_combined
        )
        SELECT
          COUNTIF(diff_type = 'ADDED') AS added_schema_count,
          COUNTIF(diff_type = 'DELETED') AS deleted_schema_count,
          COUNTIF(diff_type = 'MODIFIED') AS modified_schema_count
        FROM diff
        """
        schema_rows = list(bq_client.query(schema_diff_sql).result())
        if schema_rows:
            added_schema = int(schema_rows[0].added_schema_count or 0)
            deleted_schema = int(schema_rows[0].deleted_schema_count or 0)
            modified_schema = int(schema_rows[0].modified_schema_count or 0)
        else:
            added_schema = deleted_schema = modified_schema = 0

    finally:
        if not tables_to_delete:
            tables_to_delete = [
                t for t in (curr_obs_table, prev_obs_table, curr_schema_table,
                            prev_schema_table, raw_obs_table, raw_schema_table,
                            agg_obs_table) if t
            ]
        for table_id in dict.fromkeys(tables_to_delete):
            bq_client.delete_table(table_id, not_found_ok=True)

    added_obs = int(obs_diff_df['ADDED'].sum()) if not obs_diff_df.empty else 0
    deleted_obs = int(
        obs_diff_df['DELETED'].sum()) if not obs_diff_df.empty else 0
    modified_obs = int(
        obs_diff_df['MODIFIED'].sum()) if not obs_diff_df.empty else 0
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
    )


if __name__ == '__main__':
    _define_cli_flags()
    app.run(main)
