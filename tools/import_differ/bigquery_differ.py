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
"""BigQuery-based differ for low-memory execution."""

import csv
from datetime import datetime, timedelta, timezone
import os
import re
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple
import uuid

from absl import logging
from google.cloud import bigquery

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.join(_DATA_DIR, 'util'))
sys.path.append(os.path.join(_DATA_DIR, 'tools', 'statvar_importer'))

import differ_utils
from file_util import FileIO, file_get_matching
from mcf_file_util import normalize_value

OBSERVATION_KEY_PROPERTIES = [
    'variableMeasured',
    'observationAbout',
    'observationDate',
    'observationPeriod',
    'measurementMethod',
    'unit',
    'scalingFactor',
]

OBS_BQ_SCHEMA = [
    bigquery.SchemaField('key_combined', 'STRING'),
    bigquery.SchemaField('variableMeasured', 'STRING'),
    bigquery.SchemaField('value', 'STRING'),
]

SCHEMA_NODE_BQ_SCHEMA = [
    bigquery.SchemaField('dcid', 'STRING'),
    bigquery.SchemaField('value_combined', 'STRING'),
]


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


def _flush_node_to_csv(node: Dict[str, Any], obs_writer: csv.writer,
                       schema_writer: csv.writer) -> Tuple[int, int]:
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
        obs_writer.writerow([key_combined, var_measured, val])
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


def stream_mcf_to_csv(mcf_pattern: str, obs_csv_path: str,
                      schema_csv_path: str) -> Tuple[int, int]:
    """Streams MCF files node-by-node into observation and schema CSVs in O(1) memory."""
    mcf_files = file_get_matching(mcf_pattern)
    total_obs = 0
    total_schema = 0

    with FileIO(obs_csv_path, mode='w', encoding='utf-8') as obs_file, \
         FileIO(schema_csv_path, mode='w', encoding='utf-8') as schema_file:
        obs_writer = csv.writer(obs_file)
        schema_writer = csv.writer(schema_file)
        obs_writer.writerow(['key_combined', 'variableMeasured', 'value'])
        schema_writer.writerow(['dcid', 'value_combined'])

        for mcf_file in mcf_files:
            logging.info('Streaming MCF file to CSV: %s', mcf_file)
            with FileIO(mcf_file, mode='r', encoding='utf-8') as in_f:
                current_node: Dict[str, Any] = {}
                for raw_line in in_f:
                    line = raw_line.strip()
                    if not line or line.startswith('#'):
                        if current_node:
                            o_inc, s_inc = _flush_node_to_csv(
                                current_node, obs_writer, schema_writer)
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
                                current_node, obs_writer, schema_writer)
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
                    o_inc, s_inc = _flush_node_to_csv(current_node, obs_writer,
                                                      schema_writer)
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


def load_mcf_to_bq_tables(bq_client: bigquery.Client,
                          mcf_pattern: str,
                          obs_table_ref: str,
                          schema_table_ref: str,
                          temp_dir: Optional[str] = None,
                          suffix: str = '',
                          expiration_hours: int = 12) -> Tuple[int, int]:
    """Streams MCF files to CSVs and loads them into BigQuery observation and schema tables."""
    with tempfile.TemporaryDirectory() as local_tmpdir:
        base_dir = temp_dir if temp_dir else local_tmpdir
        tag = f'_{suffix}' if suffix else ''
        obs_csv = os.path.join(base_dir, f'obs{tag}.csv')
        schema_csv = os.path.join(base_dir, f'schema{tag}.csv')

        obs_count, schema_count = stream_mcf_to_csv(mcf_pattern, obs_csv,
                                                    schema_csv)
        load_csv_to_bq_table(bq_client, obs_csv, obs_table_ref, OBS_BQ_SCHEMA,
                             expiration_hours)
        load_csv_to_bq_table(bq_client, schema_csv, schema_table_ref,
                             SCHEMA_NODE_BQ_SCHEMA, expiration_hours)
        return obs_count, schema_count


def _sanitize_job_suffix(job_name: str) -> str:
    """Converts a job name into a safe BigQuery table suffix."""
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', job_name)
    return f'{cleaned}_{uuid.uuid4().hex[:8]}'


def run_bigquery_differ(
    current_data: str,
    previous_data: str,
    output_location: str,
    project_id: str,
    job_name: str = 'differ',
    dataset_id: str = 'datcom_import_differ',
    gcs_temp_dir: Optional[str] = None,
    expiration_hours: int = 12,
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

    try:
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
          FROM `{curr_obs_table}` c
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
          FROM `{curr_schema_table}` c
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
        for table_id in (curr_obs_table, prev_obs_table, curr_schema_table,
                         prev_schema_table):
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
