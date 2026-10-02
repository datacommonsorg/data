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
"""Standalone Cloud Run Job entrypoint for Differ + Validation."""

import json
import os
import sys
import tempfile
import time
from typing import Dict, List

from absl import app
from absl import flags
from absl import logging
from google.cloud import storage

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Support running both inside Docker (/app) and from data/import-automation/validator/
_ROOT_DIR = (_SCRIPT_DIR if os.path.exists(os.path.join(_SCRIPT_DIR, 'tools'))
             else os.path.dirname(os.path.dirname(_SCRIPT_DIR)))

for _p in [
        _ROOT_DIR,
        os.path.join(_ROOT_DIR, 'util'),
        os.path.join(_ROOT_DIR, 'tools', 'import_differ'),
        os.path.join(_ROOT_DIR, 'tools', 'import_validation'),
        os.path.join(_ROOT_DIR, 'tools', 'statvar_importer'),
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tools.import_differ import bigquery_differ
from tools.import_validation.runner import ValidationRunner
from tools.import_validation.validation_config import merge_and_save_config
import file_util

FLAGS = flags.FLAGS
flags.DEFINE_string(
    'import_name', '',
    'Import name in format <relative_import_dir>:<import_name> (required).')
flags.DEFINE_string('import_config', '{}',
                    'JSON string of import executor config overrides.')
flags.DEFINE_string('version', '',
                    'Explicit candidate version override (optional).')
flags.DEFINE_string('gcs_bucket', '',
                    'GCS bucket name (defaults to env GCS_BUCKET_ID).')
if 'bq_dataset' not in FLAGS:
    flags.DEFINE_string(
        'bq_dataset', 'datcom_import_differ',
        'BigQuery dataset ID for temporary differ tables.')
if 'bq_table_ttl_hours' not in FLAGS:
    flags.DEFINE_integer(
        'bq_table_ttl_hours', 12,
        'TTL in hours for temporary BigQuery differ tables.')


def _read_gcs_text(client: storage.Client, bucket_name: str,
                   blob_path: str) -> str:
    """Reads text content from a GCS blob if it exists, else returns ''."""
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    if not blob.exists():
        return ''
    return blob.download_as_text().strip()


def _write_gcs_text(client: storage.Client, bucket_name: str, blob_path: str,
                    content: str) -> None:
    """Uploads text content to a GCS blob."""
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_string(content)


def _discover_input_prefixes(client: storage.Client, bucket_name: str,
                             output_dir: str, version: str) -> List[str]:
    """Discovers input0, input1, ... prefixes under gs://<bucket>/<output_dir>/<version>/."""
    base_prefix = f'{output_dir}/{version}/'
    bucket = client.bucket(bucket_name)
    iterator = client.list_blobs(bucket,
                                 prefix=f'{base_prefix}input',
                                 delimiter='/')
    for _ in iterator:
        pass
    prefixes = set()
    for p in iterator.prefixes:
        top_folder = p[len(base_prefix):].rstrip('/')
        if top_folder.startswith('input'):
            prefixes.add(top_folder)
    if not prefixes:
        return ['input0']
    return sorted(prefixes)


def _resolve_validation_config(client: storage.Client, bucket_name: str,
                               output_dir: str, relative_import_dir: str,
                               import_name: str, version: str,
                               default_val_config: str, tmpdir: str) -> str:
    """Resolves validation_config.json by merging GCS/local override with default config."""
    manifest_text = _read_gcs_text(client, bucket_name,
                                   f'{output_dir}/{version}/manifest.json')
    if not manifest_text:
        return default_val_config

    try:
        manifest = json.loads(manifest_text)
        custom_cfg_rel = manifest.get('validation_config_file')
        for spec in manifest.get('import_specifications', []):
            if spec.get('import_name') == import_name and spec.get(
                    'validation_config_file'):
                custom_cfg_rel = spec.get('validation_config_file')
                break
        if not custom_cfg_rel:
            return default_val_config

        override_filename = os.path.basename(custom_cfg_rel)
        gcs_override_cfg = (
            f'gs://{bucket_name}/{output_dir}/{version}/{override_filename}')
        if file_util.file_get_matching(gcs_override_cfg):
            local_override_cfg = os.path.join(tmpdir, override_filename)
            file_util.file_copy(gcs_override_cfg, local_override_cfg)
            logging.info('Downloaded override validation config from GCS: %s',
                         gcs_override_cfg)
            return merge_and_save_config(default_val_config,
                                         local_override_cfg, tmpdir)

        local_repo_cfg = os.path.join(_ROOT_DIR, relative_import_dir,
                                      custom_cfg_rel)
        if os.path.exists(local_repo_cfg):
            return merge_and_save_config(default_val_config, local_repo_cfg,
                                         tmpdir)
        logging.warning(
            'Custom validation config %s not found in GCS or local repo; using default.',
            custom_cfg_rel)
        return default_val_config
    except Exception as exc:
        logging.warning(
            'Failed to resolve custom validation config (%s); using default.',
            exc)
        return default_val_config


def run_validation_job(absolute_import_name: str,
                       import_config_str: str,
                       version_override: str,
                       bucket_name: str,
                       bq_dataset: str,
                       bq_table_ttl_hours: int = 12) -> int:
    """Executes BigQuery differ and ValidationRunner for an import version."""
    start_time = time.time()
    if ':' not in absolute_import_name:
        raise ValueError(
            f'--import_name must be <dir>:<name>, got: {absolute_import_name}')

    relative_import_dir, import_name = absolute_import_name.split(':', 1)
    output_dir = f'{relative_import_dir}/{import_name}'

    user_config = json.loads(import_config_str) if import_config_str else {}
    if not bucket_name:
        bucket_name = (user_config.get('storage_prod_bucket_name') or
                       os.environ.get('GCS_BUCKET_ID') or
                       'datcom-prod-imports')
    project_id = (user_config.get('gcp_project_id') or
                  os.environ.get('PROJECT_ID') or
                  os.environ.get('GOOGLE_CLOUD_PROJECT', ''))
    if bq_dataset == 'datcom_import_differ':
        bq_dataset = (user_config.get('bq_dataset') or
                      os.environ.get('BQ_DATASET') or bq_dataset)
    if bq_table_ttl_hours == 12:
        env_ttl = os.environ.get('BQ_TABLE_TTL_HOURS')
        bq_table_ttl_hours = int(
            user_config.get('bq_table_ttl_hours') or env_ttl or
            bq_table_ttl_hours)

    ignore_validation_status = user_config.get('ignore_validation_status',
                                               False)
    enable_skip_status = user_config.get('enable_skip_status', True)

    gcs_client = storage.Client(project=project_id or None)

    version = version_override
    if not version:
        version = _read_gcs_text(gcs_client, bucket_name,
                                 f'{output_dir}/staging_version.txt')
    if not version:
        raise RuntimeError(
            f'No candidate version found in gs://{bucket_name}/{output_dir}/staging_version.txt'
        )

    latest_version = _read_gcs_text(gcs_client, bucket_name,
                                    f'{output_dir}/latest_version.txt')
    latest_version_uri = (f'gs://{bucket_name}/{output_dir}/{latest_version}'
                          if latest_version else '')

    logging.info('Running validator for %s version=%s (latest=%s)', output_dir,
                 version, latest_version or 'None')

    summary_raw = _read_gcs_text(
        gcs_client, bucket_name,
        f'{output_dir}/{version}/import_summary.json')
    import_summary: Dict = json.loads(summary_raw) if summary_raw else {
        'import_name': import_name,
        'latest_version': f'gs://{bucket_name}/{output_dir}/{version}',
        'import_stats': {},
    }

    input_prefixes = _discover_input_prefixes(gcs_client, bucket_name,
                                              output_dir, version)

    validation_status = True
    differ_status = False
    validation_data_size = 0

    default_val_config = os.path.join(_ROOT_DIR, 'tools', 'import_validation',
                                      'validation_config.json')

    with tempfile.TemporaryDirectory() as tmpdir:
        for input_prefix in input_prefixes:
            genmcf_local_dir = os.path.join(tmpdir, input_prefix, 'genmcf')
            val_local_dir = os.path.join(tmpdir, input_prefix, 'validation')
            os.makedirs(genmcf_local_dir, exist_ok=True)
            os.makedirs(val_local_dir, exist_ok=True)

            current_mcf_pattern = (
                f'gs://{bucket_name}/{output_dir}/{version}/{input_prefix}/genmcf/*.mcf'
            )
            previous_mcf_pattern = (
                f'{latest_version_uri}/{input_prefix}/genmcf/*.mcf'
                if latest_version_uri else '')

            diff_found = True
            differ_output_dir = ''

            # 1. Run BigQuery Differ if previous version exists
            if previous_mcf_pattern and file_util.file_get_matching(
                    previous_mcf_pattern):
                logging.info('Running BigQuery differ for %s vs %s',
                             current_mcf_pattern, previous_mcf_pattern)
                differ_summary = bigquery_differ.run_bigquery_differ(
                    current_data=current_mcf_pattern,
                    previous_data=previous_mcf_pattern,
                    output_location=val_local_dir,
                    project_id=project_id,
                    job_name=f'differ_{import_name}_{input_prefix}',
                    dataset_id=bq_dataset,
                    expiration_hours=bq_table_ttl_hours,
                )
                diff_found = (differ_summary.get('obs_diff_count', 1) != 0 or
                              differ_summary.get('schema_diff_count', 1) != 0)
                differ_output_dir = val_local_dir
            else:
                logging.info(
                    'No previous MCF files found at %s; skipping differ.',
                    previous_mcf_pattern)

            if not differ_status:
                differ_status = diff_found

            # 2. Download summary_report.csv and report.json for ValidationRunner
            summary_stats_local = os.path.join(genmcf_local_dir,
                                               'summary_report.csv')
            report_json_local = os.path.join(genmcf_local_dir, 'report.json')
            gcs_summary_stats = (
                f'gs://{bucket_name}/{output_dir}/{version}/{input_prefix}/genmcf/summary_report.csv'
            )
            gcs_report_json = (
                f'gs://{bucket_name}/{output_dir}/{version}/{input_prefix}/genmcf/report.json'
            )
            if file_util.file_get_matching(gcs_summary_stats):
                file_util.file_copy(gcs_summary_stats, summary_stats_local)
            if file_util.file_get_matching(gcs_report_json):
                file_util.file_copy(gcs_report_json, report_json_local)

            val_config_path = _resolve_validation_config(
                gcs_client, bucket_name, output_dir, relative_import_dir,
                import_name, version, default_val_config, tmpdir)

            val_output_file = os.path.join(val_local_dir,
                                           'validation_output.csv')
            runner = ValidationRunner(
                validation_config_path=val_config_path,
                differ_output=differ_output_dir,
                stats_summary=summary_stats_local,
                lint_report=report_json_local,
                validation_output=val_output_file,
            )
            overall_status, _ = runner.run_validations()
            validation_status = validation_status and overall_status

            # 3. Upload validation artifacts to GCS
            gcs_val_dest = f'{output_dir}/{version}/{input_prefix}/validation'
            bucket = gcs_client.bucket(bucket_name)
            for fname in os.listdir(val_local_dir):
                fpath = os.path.join(val_local_dir, fname)
                if os.path.isfile(fpath):
                    validation_data_size += os.path.getsize(fpath)
                    dest_blob_name = f'{gcs_val_dest}/{fname}'
                    bucket.blob(dest_blob_name).upload_from_filename(fpath)

    # 4. Update import_summary.json status in GCS
    if validation_status or ignore_validation_status:
        if not differ_status and enable_skip_status:
            import_summary['status'] = 'SKIP'
        else:
            import_summary['status'] = 'STAGING'
        exit_code = 0
    else:
        import_summary['status'] = 'VALIDATION'
        exit_code = 1

    stats = import_summary.setdefault('import_stats', {})
    stats['validation_execution_time'] = int(time.time() - start_time)
    stats['validation_data_size'] = validation_data_size

    _write_gcs_text(gcs_client, bucket_name,
                    f'{output_dir}/{version}/import_summary.json',
                    json.dumps(import_summary, indent=2))
    logging.info('Completed validator: status=%s, exit_code=%d',
                 import_summary['status'], exit_code)
    return exit_code


def main(_):
    if not FLAGS.import_name:
        raise ValueError('--import_name is required.')
    code = run_validation_job(
        absolute_import_name=FLAGS.import_name,
        import_config_str=FLAGS.import_config,
        version_override=FLAGS.version,
        bucket_name=FLAGS.gcs_bucket,
        bq_dataset=FLAGS.bq_dataset,
        bq_table_ttl_hours=FLAGS.bq_table_ttl_hours,
    )
    sys.exit(code)


if __name__ == '__main__':
    app.run(main)
