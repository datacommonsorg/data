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
"""Standalone Cloud Run Job entrypoint for ET-layer StatVar Aggregation."""

import json
import os
import sys
import tempfile
import time
from typing import Dict, List, Optional

from absl import app
from absl import flags
from absl import logging
from google.cloud import storage

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Support running both inside Docker (/app) and from data/import-automation/aggregator/
_ROOT_DIR = (
    _SCRIPT_DIR
    if os.path.exists(os.path.join(_SCRIPT_DIR, "tools"))
    else os.path.dirname(os.path.dirname(_SCRIPT_DIR))
)

for _p in [
    _SCRIPT_DIR,
    _ROOT_DIR,
    os.path.join(_ROOT_DIR, "util"),
    os.path.join(_ROOT_DIR, "tools", "import_differ"),
    os.path.join(_ROOT_DIR, "tools", "statvar_importer"),
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import file_util
import stat_var_aggregator

FLAGS = flags.FLAGS


def _define_cli_flags() -> None:
    """Defines CLI flags when main.py is executed as a script."""
    if "import_name" not in FLAGS:
        flags.DEFINE_string(
            "import_name",
            "",
            "Import name in format <relative_import_dir>:<import_name> (required).",
        )
    if "import_config" not in FLAGS:
        flags.DEFINE_string(
            "import_config",
            "{}",
            "JSON string of import executor config overrides.",
        )
    if "version" not in FLAGS:
        flags.DEFINE_string(
            "version",
            "",
            "Explicit candidate version override (optional).",
        )
    if "gcs_bucket" not in FLAGS:
        flags.DEFINE_string(
            "gcs_bucket",
            "",
            "GCS bucket name (defaults to env GCS_BUCKET_ID).",
        )
    if "bq_dataset" not in FLAGS:
        flags.DEFINE_string(
            "bq_dataset",
            "datcom_import_differ",
            "BigQuery dataset ID for temporary aggregation/differ tables.",
        )
    if "bq_table_ttl_hours" not in FLAGS:
        flags.DEFINE_integer(
            "bq_table_ttl_hours",
            12,
            "TTL in hours for temporary BigQuery tables.",
        )
    if "runner_mode" not in FLAGS:
        flags.DEFINE_string(
            "runner_mode",
            "bigquery",
            "Execution mode for StatVar aggregation: 'bigquery' or 'duckdb'.",
        )
    if "config_path" not in FLAGS:
        flags.DEFINE_string(
            "config_path",
            "",
            "Optional path override to statvar_aggregation.yaml.",
        )


def _read_gcs_text(
    client: storage.Client, bucket_name: str, blob_path: str
) -> str:
    """Reads text content from a GCS blob if it exists, else returns ''."""
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    if not blob.exists():
        return ""
    return blob.download_as_text().strip()


def _write_gcs_text(
    client: storage.Client, bucket_name: str, blob_path: str, content: str
) -> None:
    """Uploads text content to a GCS blob."""
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_string(content)


def _discover_input_prefixes(
    client: storage.Client, bucket_name: str, output_dir: str, version: str
) -> List[str]:
    """Discovers input0, input1, ... prefixes under gs://<bucket>/<output_dir>/<version>/."""
    base_prefix = f"{output_dir}/{version}/"
    bucket = client.bucket(bucket_name)
    iterator = client.list_blobs(
        bucket, prefix=f"{base_prefix}input", delimiter="/"
    )
    for _ in iterator:
        pass
    prefixes = set()
    for p in iterator.prefixes:
        top_folder = p[len(base_prefix) :].rstrip("/")
        if top_folder.startswith("input"):
            prefixes.add(top_folder)
    if not prefixes:
        return ["input0"]
    return sorted(prefixes)


def run_aggregation_job(
    absolute_import_name: str,
    import_config_str: str = "{}",
    version_override: str = "",
    bucket_name: str = "",
    bq_dataset: str = "datcom_import_differ",
    bq_table_ttl_hours: int = 12,
    runner_mode: str = "bigquery",
    config_path: Optional[str] = None,
) -> int:
    """Executes StatVar aggregation for an import version if configured in statvar_aggregation.yaml."""
    start_time = time.time()
    if ":" not in absolute_import_name:
        raise ValueError(
            f"--import_name must be <dir>:<name>, got: {absolute_import_name}"
        )

    relative_import_dir, import_name = absolute_import_name.split(":", 1)
    output_dir = f"{relative_import_dir}/{import_name}"

    rules = stat_var_aggregator.load_stat_var_aggregation_config(
        import_name=import_name,
        config_path=config_path or None,
    )
    if not rules:
        logging.info(
            "No StatVar aggregation rules configured for %s; skipping aggregation job.",
            import_name,
        )
        return 0

    user_config = json.loads(import_config_str) if import_config_str else {}
    if not bucket_name:
        bucket_name = (
            user_config.get("storage_prod_bucket_name")
            or os.environ.get("GCS_BUCKET_ID")
            or "datcom-prod-imports"
        )
    project_id = (
        user_config.get("gcp_project_id")
        or os.environ.get("PROJECT_ID")
        or os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    )
    if bq_dataset == "datcom_import_differ":
        bq_dataset = (
            user_config.get("bq_dataset")
            or os.environ.get("BQ_DATASET")
            or bq_dataset
        )
    if bq_table_ttl_hours == 12:
        env_ttl = os.environ.get("BQ_TABLE_TTL_HOURS")
        bq_table_ttl_hours = int(
            user_config.get("bq_table_ttl_hours")
            or env_ttl
            or bq_table_ttl_hours
        )
    mode = (
        runner_mode
        or user_config.get("aggregation_runner_mode")
        or os.environ.get("AGGREGATION_RUNNER_MODE")
        or "bigquery"
    ).strip().lower()

    gcs_client = storage.Client(project=project_id or None)

    version = version_override
    if not version:
        version = _read_gcs_text(
            gcs_client, bucket_name, f"{output_dir}/staging_version.txt"
        )
    if not version:
        raise RuntimeError(
            f"No candidate version found in gs://{bucket_name}/{output_dir}/staging_version.txt"
        )

    logging.info(
        "Running StatVar aggregation (%s) for %s version=%s (%d rules)",
        mode,
        output_dir,
        version,
        len(rules),
    )

    summary_raw = _read_gcs_text(
        gcs_client, bucket_name, f"{output_dir}/{version}/import_summary.json"
    )
    import_summary: Dict = (
        json.loads(summary_raw)
        if summary_raw
        else {
            "import_name": import_name,
            "latest_version": f"gs://{bucket_name}/{output_dir}/{version}",
            "import_stats": {},
        }
    )

    input_prefixes = _discover_input_prefixes(
        gcs_client, bucket_name, output_dir, version
    )
    bucket = gcs_client.bucket(bucket_name)
    total_agg_obs = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        for input_prefix in input_prefixes:
            local_genmcf_dir = os.path.join(tmpdir, input_prefix, "genmcf")
            os.makedirs(local_genmcf_dir, exist_ok=True)

            mcf_pattern = (
                f"gs://{bucket_name}/{output_dir}/{version}/{input_prefix}/genmcf/*.mcf"
            )
            local_agg_mcf = os.path.join(
                local_genmcf_dir, stat_var_aggregator.STAT_VAR_AGG_MCF_FILENAME
            )
            local_summary_csv = os.path.join(
                local_genmcf_dir, "summary_report.csv"
            )

            summary_blob_path = (
                f"{output_dir}/{version}/{input_prefix}/genmcf/summary_report.csv"
            )
            gcs_summary_uri = f"gs://{bucket_name}/{summary_blob_path}"
            summary_exists = False
            summary_content = _read_gcs_text(
                gcs_client, bucket_name, summary_blob_path
            )
            if summary_content:
                with open(local_summary_csv, "w", encoding="utf-8") as f:
                    f.write(summary_content + "\n")
                summary_exists = True
            elif file_util.file_get_matching(gcs_summary_uri):
                file_util.file_copy(gcs_summary_uri, local_summary_csv)
                summary_exists = True

            if mode == "duckdb":
                res = stat_var_aggregator.run_duckdb_aggregation(
                    mcf_pattern=mcf_pattern,
                    aggregations=rules,
                    output_mcf_path=local_agg_mcf,
                    summary_report_path=local_summary_csv
                    if summary_exists
                    else None,
                )
            else:
                gcs_temp_dir = (
                    f"gs://{bucket_name}/{output_dir}/{version}/{input_prefix}/aggregation/_tmp"
                )
                res = stat_var_aggregator.run_bigquery_aggregation(
                    mcf_pattern=mcf_pattern,
                    aggregations=rules,
                    output_mcf_path=local_agg_mcf,
                    project_id=project_id,
                    dataset_id=bq_dataset,
                    import_name=import_name,
                    version=version,
                    input_prefix=input_prefix,
                    summary_report_path=local_summary_csv
                    if summary_exists
                    else None,
                    gcs_temp_dir=gcs_temp_dir,
                    expiration_hours=bq_table_ttl_hours,
                )

            agg_count = int(res.get("agg_obs_count", 0))
            total_agg_obs += agg_count
            if agg_count > 0 and os.path.exists(local_agg_mcf):
                agg_mcf_blob_path = (
                    f"{output_dir}/{version}/{input_prefix}/genmcf/"
                    f"{stat_var_aggregator.STAT_VAR_AGG_MCF_FILENAME}"
                )
                bucket.blob(agg_mcf_blob_path).upload_from_filename(
                    local_agg_mcf
                )
                if summary_exists and os.path.exists(local_summary_csv):
                    bucket.blob(summary_blob_path).upload_from_filename(
                        local_summary_csv
                    )

    stats = import_summary.setdefault("import_stats", {})
    stats["aggregation_execution_time"] = int(time.time() - start_time)
    stats["aggregated_obs_count"] = total_agg_obs

    _write_gcs_text(
        gcs_client,
        bucket_name,
        f"{output_dir}/{version}/import_summary.json",
        json.dumps(import_summary, indent=2),
    )
    logging.info(
        "Completed StatVar aggregation for %s: %d aggregated observations.",
        output_dir,
        total_agg_obs,
    )
    return 0


def main(_):
    if not FLAGS.import_name:
        raise ValueError("--import_name is required.")
    code = run_aggregation_job(
        absolute_import_name=FLAGS.import_name,
        import_config_str=FLAGS.import_config,
        version_override=FLAGS.version,
        bucket_name=FLAGS.gcs_bucket,
        bq_dataset=FLAGS.bq_dataset,
        bq_table_ttl_hours=FLAGS.bq_table_ttl_hours,
        runner_mode=FLAGS.runner_mode,
        config_path=FLAGS.config_path or None,
    )
    sys.exit(code)


if __name__ == "__main__":
    _define_cli_flags()
    app.run(main)
