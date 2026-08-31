#!/bin/bash

# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Usage:
#   ./agents/skills/dc-import-diagnostics/scripts/create_short_lived_bq_table.sh \
#     --csv='gs://bucket/path/*.csv' --table='debug_table'
# Optional: --ttl_secs=SECONDS. The default is 86400 seconds (one day).
# Run with --help for all options.

set -euo pipefail

readonly DEFAULT_BQ_PROJECT="datcom-store"
readonly DEFAULT_BQ_DATASET="scratch"
readonly DEFAULT_TTL_SECS=86400

usage() {
  echo "Usage: $0 (--csv=GCS_URI|--avro=GCS_URI|--parquet=GCS_URI) --table=TABLE_ID|PROJECT_ID.DATASET_ID.TABLE_ID [--ttl_secs=SECONDS]"
}

show_help() {
  echo "Load a GCS file or file pattern into a short-lived BigQuery table."
  echo
  usage
  echo
  echo "Source options (specify exactly one):"
  echo "  --csv=GCS_URI"
  echo "  --avro=GCS_URI"
  echo "  --parquet=GCS_URI"
  echo
  echo "Table options:"
  echo "  --table=TABLE_ID"
  echo "      Uses the default destination: datcom-store.scratch.TABLE_ID"
  echo "  --table=PROJECT_ID.DATASET_ID.TABLE_ID"
  echo "      Uses the fully qualified destination."
  echo
  echo "Optional:"
  echo "  --ttl_secs=SECONDS"
  echo "      Sets the table lifetime. The default is 86400 seconds (one day)."
  echo
  echo "Example:"
  echo "  $0 --csv='gs://bucket/path/*.csv' --table='debug_table'"
  echo
  echo "The script never replaces an existing table. It prints the full table name when created or already present."
}

if [[ $# -eq 1 && "$1" == "--help" ]]; then
  show_help
  exit 0
fi

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage >&2
  exit 2
fi

source_count=0
table_count=0
ttl_secs_count=0
source_format=""
gcs_uri=""
table_input=""
ttl_secs="$DEFAULT_TTL_SECS"
bq_project="$DEFAULT_BQ_PROJECT"
bq_dataset="$DEFAULT_BQ_DATASET"

for arg in "$@"; do
  case "$arg" in
    --csv=*)
      source_count=$((source_count + 1))
      source_format="CSV"
      gcs_uri="${arg#*=}"
      ;;
    --avro=*)
      source_count=$((source_count + 1))
      source_format="AVRO"
      gcs_uri="${arg#*=}"
      ;;
    --parquet=*)
      source_count=$((source_count + 1))
      source_format="PARQUET"
      gcs_uri="${arg#*=}"
      ;;
    --table=*)
      table_count=$((table_count + 1))
      table_input="${arg#*=}"
      ;;
    --ttl_secs=*)
      ttl_secs_count=$((ttl_secs_count + 1))
      ttl_secs="${arg#*=}"
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$source_count" -ne 1 ]]; then
  echo "Specify exactly one of --csv, --avro, or --parquet." >&2
  exit 2
fi

if [[ "$table_count" -ne 1 ]]; then
  echo "Specify --table exactly once." >&2
  exit 2
fi

if [[ "$ttl_secs_count" -gt 1 || ! "$ttl_secs" =~ ^[1-9][0-9]*$ ]]; then
  echo "--ttl_secs must be specified at most once as a positive number of seconds." >&2
  exit 2
fi

if [[ "$gcs_uri" != gs://* ]]; then
  echo "GCS path must start with gs://: $gcs_uri" >&2
  exit 2
fi

if [[ "$table_input" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
  table_name="$table_input"
elif [[ "$table_input" =~ ^([A-Za-z0-9][A-Za-z0-9-]*)\.([A-Za-z0-9_]+)\.([A-Za-z_][A-Za-z0-9_]*)$ ]]; then
  bq_project="${BASH_REMATCH[1]}"
  bq_dataset="${BASH_REMATCH[2]}"
  table_name="${BASH_REMATCH[3]}"
else
  echo "Table must use TABLE_ID or PROJECT_ID.DATASET_ID.TABLE_ID format: $table_input" >&2
  exit 2
fi

command -v bq >/dev/null || {
  echo "bq is required." >&2
  exit 1
}

dataset_ref="${bq_project}:${bq_dataset}"
table_ref="${dataset_ref}.${table_name}"
sql_table_ref="${bq_project}.${bq_dataset}.${table_name}"

if ! bq show --dataset "$dataset_ref" >/dev/null 2>&1; then
  echo "BigQuery dataset does not exist or is not accessible: $dataset_ref" >&2
  exit 1
fi

if bq show "$table_ref" >/dev/null 2>&1; then
  echo "BigQuery table already exists: $sql_table_ref" >&2
  echo "$sql_table_ref"
  exit 3
fi

bq load \
  --autodetect \
  --source_format="$source_format" \
  "$table_ref" \
  "$gcs_uri" >/dev/null

if ! bq update --expiration="$ttl_secs" "$table_ref" >/dev/null; then
  echo "Table was loaded, but its expiration could not be set: $sql_table_ref" >&2
  exit 1
fi

echo "$sql_table_ref"
