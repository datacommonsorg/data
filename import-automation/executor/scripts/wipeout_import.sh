#!/bin/bash
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
#
# Wipes out an import's data (observations, time series, edges, provenance
# summaries, and derived aggregations) from staging and/or prod Cloud Spanner:
#   1. Verifies no Airflow DAG run for the import is currently running or queued.
#   2. Pauses the import's scheduled Airflow DAG (if present).
#   3. Writes gs://datcom-prod-imports/<output_dir>/wipeout/import_summary.json
#      pointing to the shared empty MCF file (gs://datcom-prod-imports/wipeout/*.mcf).
#   4. Triggers the ManualRefresh Airflow DAG with skipImportJob=true and
#      forceIngestion=true to delete the import's data in Spanner.
#
# Prerequisites:
#   - Run `gcloud auth login` with permissions for `gs://datcom-prod-imports`
#     and the Cloud Composer Airflow environment.
#   - Ensure no import or ingestion job for the import is currently running.
#   - If the import is fed by an external transfer job (not scheduled in
#     Airflow), pause or disable that external feed first.
#
# Usage:
#   ./wipeout_import.sh <import_name> <comment> [staging|prod]
#
# Arguments:
#   <import_name>   Short import name from manifest.json (e.g.
#                   USFed_ConstantMaturityRates_Test) or full prefixed name
#                   (<import_dir>:<ImportName>).
#   <comment>       Reason for the wipeout (recorded in BigQuery ImportHistory).
#   [staging|prod]  Optional target environment. If omitted, wipes staging
#                   first and then prod sequentially.
#
# Examples:
#   # Wipe out from staging Spanner only:
#   ./wipeout_import.sh USFed_ConstantMaturityRates_Test 'Retire import' staging
#
#   # Wipe out from prod Spanner only:
#   ./wipeout_import.sh USFed_ConstantMaturityRates_Test 'Retire import' prod
#
#   # Wipe out from both staging and prod Spanner:
#   ./wipeout_import.sh USFed_ConstantMaturityRates_Test 'Retire import'
#
#   # Wipe out an import not found in local manifest.json files:
#   ./wipeout_import.sh scripts/us_fed/treasury_constant_maturity_rates:USFed_ConstantMaturityRates_Test 'Retire import'
#
# Follow-up:
#   - Monitor the triggered ManualRefresh DAG run
#     (wipeout__<user>__<ImportName>__<timestamp>) in the Airflow UI.
#   - Remove or disable the import in its manifest.json so future DAG syncs do
#     not re-schedule it.

set -euo pipefail

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    echo "Usage: $0 <import_name> <comment> [staging|prod]"
    exit 1
fi

IMPORT_NAME="$1"
COMMENT="$2"
ENVIRONMENT="${3:-}"

if [[ ! "${IMPORT_NAME}" =~ ^[A-Za-z0-9_./:-]+$ ]] || [[ "${IMPORT_NAME}" == *".."* ]] || [[ "${IMPORT_NAME}" == /* ]]; then
    echo "Error: Invalid import_name '${IMPORT_NAME}'."
    exit 1
fi

SHORT_IMPORT_NAME="${IMPORT_NAME##*:}"
if [[ ! "${SHORT_IMPORT_NAME}" =~ ^[A-Za-z0-9_-]+$ ]]; then
    echo "Error: Invalid short import name '${SHORT_IMPORT_NAME}'."
    exit 1
fi

if [ "${SHORT_IMPORT_NAME}" = "ManualRefresh" ] || [ "${SHORT_IMPORT_NAME}" = "airflow_monitoring" ]; then
    echo "Error: Refusing to wipe out system DAG '${SHORT_IMPORT_NAME}'."
    exit 1
fi

if [ -n "${ENVIRONMENT}" ] && [ "${ENVIRONMENT}" != "staging" ] && [ "${ENVIRONMENT}" != "prod" ]; then
    echo "Error: Invalid environment '${ENVIRONMENT}'. Expected 'staging' or 'prod'."
    exit 1
fi

AIRFLOW_URL="${AIRFLOW_WEB_SERVER_URL:-https://030069cf9df9415bbd743bf7e18a6a65-dot-us-central1.composer.googleusercontent.com}"
AIRFLOW_URL="${AIRFLOW_URL%/}"
GCS_BUCKET="${GCS_BUCKET_ID:-datcom-prod-imports}"
WIPEOUT_VERSION="${WIPEOUT_VERSION:-wipeout}"
WIPEOUT_EMPTY_FILE="gs://${GCS_BUCKET}/wipeout/empty.mcf"
WIPEOUT_MCF_GLOB="${WIPEOUT_MCF_PATH:-gs://${GCS_BUCKET}/wipeout/*.mcf}"
TRIGGER_DAG_ID="${DAG_ID:-ManualRefresh}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Resolve full '<import_dir>:<ImportName>' from manifest.json when only short name is given.
FULL_IMPORT_NAME="${IMPORT_NAME}"
if [[ "${IMPORT_NAME}" != *:* ]]; then
    RESOLVED_NAME="$(python3 - "${REPO_ROOT}" "${SHORT_IMPORT_NAME}" <<'PY'
import json
import os
import subprocess
import sys

repo_root, target = sys.argv[1], sys.argv[2]
manifests = []
try:
    out = subprocess.check_output(
        ["git", "-C", repo_root, "ls-files", "*manifest.json"],
        stderr=subprocess.DEVNULL,
        text=True,
    )
    manifests = [os.path.join(repo_root, p) for p in out.splitlines() if p]
except Exception:
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        if "manifest.json" in files:
            manifests.append(os.path.join(root, "manifest.json"))

for path in sorted(manifests):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        continue
    for spec in data.get("import_specifications", []):
        if spec.get("import_name") == target:
            rel_dir = os.path.relpath(os.path.dirname(path), repo_root)
            print(f"{rel_dir}:{target}")
            sys.exit(0)
PY
)"
    if [ -n "${RESOLVED_NAME}" ]; then
        FULL_IMPORT_NAME="${RESOLVED_NAME}"
        echo "Resolved '${IMPORT_NAME}' -> '${FULL_IMPORT_NAME}'"
    else
        echo "Note: No local manifest.json found for '${SHORT_IMPORT_NAME}'; using '${FULL_IMPORT_NAME}'."
    fi
fi

OUTPUT_DIR="${FULL_IMPORT_NAME//://}"
OUTPUT_DIR="${OUTPUT_DIR#/}"
OUTPUT_DIR="${OUTPUT_DIR%/}"

TARGET_ENV_DISPLAY="${ENVIRONMENT:-staging and prod}"
echo ""
echo "WARNING: You are about to wipe out import data from Cloud Spanner:"
echo "  Import:         ${FULL_IMPORT_NAME}"
echo "  Airflow DAG:    ${SHORT_IMPORT_NAME} (will be paused)"
echo "  Environment(s): ${TARGET_ENV_DISPLAY}"
echo "  GCS Summary:    gs://${GCS_BUCKET}/${OUTPUT_DIR}/${WIPEOUT_VERSION}/import_summary.json"
echo "  Comment:        ${COMMENT}"
echo ""
read -r -p "Are you sure you want to proceed? Type 'yes' to continue: " CONFIRMATION
if [ "${CONFIRMATION}" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

if ! ACCESS_TOKEN="$(gcloud auth print-access-token 2>/dev/null)" || [ -z "${ACCESS_TOKEN}" ]; then
    echo "Error: Failed to obtain a GCP access token. Please run 'gcloud auth login' and try again." >&2
    exit 1
fi

# 1. Verify no active (running or queued) Airflow DAG run exists for this import.
echo "1/4 Checking for active Airflow DAG runs for '${SHORT_IMPORT_NAME}'..."
check_active_dag_runs() {
    local check_dag_id="$1"
    local filter_by_conf="$2"
    local runs_response
    runs_response="$(curl -sS -w "\n%{http_code}" -X GET "${AIRFLOW_URL}/api/v2/dags/${check_dag_id}/dagRuns?state=running&state=queued" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -H "Accept: application/json")"
    local runs_body
    runs_body="$(echo "${runs_response}" | sed '$d')"
    local runs_status
    runs_status="$(echo "${runs_response}" | tail -n 1)"

    if [ "${runs_status}" = "404" ]; then
        return 0
    fi
    if [[ ! "${runs_status}" =~ ^[0-9]+$ ]] || [ "${runs_status}" -lt 200 ] || [ "${runs_status}" -ge 300 ]; then
        echo "Error: Failed to query DAG runs for '${check_dag_id}' (HTTP ${runs_status}): ${runs_body}" >&2
        exit 1
    fi

    local active_runs
    active_runs="$(python3 - "${check_dag_id}" "${SHORT_IMPORT_NAME}" "${FULL_IMPORT_NAME}" "${filter_by_conf}" "${runs_body}" <<'PY'
import json
import sys

dag_id, short_name, full_name, filter_by_conf, raw_body = sys.argv[1:6]
data = json.loads(raw_body or "{}")
matches = []
for run in data.get("dag_runs", []):
    state = str(run.get("state", "")).lower()
    if state not in ("running", "queued"):
        continue
    if filter_by_conf == "true":
        conf = run.get("conf") or {}
        conf_import = str(conf.get("importName", "")) if isinstance(conf, dict) else ""
        if conf_import not in (short_name, full_name) and conf_import.split(":")[-1] != short_name:
            continue
    run_id = run.get("dag_run_id") or run.get("run_id") or "unknown"
    matches.append(f"{dag_id}:{run_id} (state={state})")
if matches:
    print(", ".join(matches))
PY
)"
    if [ -n "${active_runs}" ]; then
        echo "Error: Active Airflow DAG run(s) found for '${SHORT_IMPORT_NAME}': ${active_runs}. Wait for completion or stop the run before wiping out." >&2
        exit 1
    fi
}

check_active_dag_runs "${SHORT_IMPORT_NAME}" "false"
if [ "${TRIGGER_DAG_ID}" != "${SHORT_IMPORT_NAME}" ]; then
    check_active_dag_runs "${TRIGGER_DAG_ID}" "true"
fi
echo "    No active DAG runs found for '${SHORT_IMPORT_NAME}'."

# 2. Pause the import's scheduled Airflow DAG so it does not re-ingest after wipeout.
echo "2/4 Pausing Airflow DAG '${SHORT_IMPORT_NAME}'..."
PAUSE_RESPONSE="$(curl -sS -w "\n%{http_code}" -X PATCH "${AIRFLOW_URL}/api/v2/dags/${SHORT_IMPORT_NAME}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"is_paused": true}')"
PAUSE_BODY="$(echo "${PAUSE_RESPONSE}" | sed '$d')"
PAUSE_STATUS="$(echo "${PAUSE_RESPONSE}" | tail -n 1)"

if [ "${PAUSE_STATUS}" = "200" ]; then
    echo "    Paused Airflow DAG '${SHORT_IMPORT_NAME}'."
elif [ "${PAUSE_STATUS}" = "404" ]; then
    echo "    Airflow DAG '${SHORT_IMPORT_NAME}' not found (404); skipping pause."
else
    echo "Error: Failed to pause DAG '${SHORT_IMPORT_NAME}' (HTTP ${PAUSE_STATUS}): ${PAUSE_BODY}"
    exit 1
fi

# 3. Ensure shared empty.mcf exists and upload per-import wipeout/import_summary.json.
echo "3/4 Uploading wipeout summary to gs://${GCS_BUCKET}/${OUTPUT_DIR}/${WIPEOUT_VERSION}/import_summary.json..."
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

if ! gcloud storage ls "${WIPEOUT_EMPTY_FILE}" >/dev/null 2>&1; then
    echo "    Creating missing empty MCF file at ${WIPEOUT_EMPTY_FILE}..."
    EMPTY_MCF_FILE="${TMP_DIR}/empty.mcf"
    touch "${EMPTY_MCF_FILE}"
    gcloud storage cp "${EMPTY_MCF_FILE}" "${WIPEOUT_EMPTY_FILE}"
fi

SUMMARY_FILE="${TMP_DIR}/import_summary.json"
PAYLOAD_FILE="${TMP_DIR}/dag_run_payload.json"

LOGICAL_DATE="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
DAG_RUN_ID="wipeout__${USER:-manual}__${SHORT_IMPORT_NAME}__$(date -u +%s)"

python3 - "${SHORT_IMPORT_NAME}" "${FULL_IMPORT_NAME}" "${WIPEOUT_VERSION}" "${WIPEOUT_MCF_GLOB}" "${COMMENT}" "${ENVIRONMENT}" "${DAG_RUN_ID}" "${LOGICAL_DATE}" "${SUMMARY_FILE}" "${PAYLOAD_FILE}" <<'PY'
import json
import sys

(
    short_name,
    full_name,
    wipeout_version,
    wipeout_mcf_glob,
    comment,
    environment,
    dag_run_id,
    logical_date,
    summary_path,
    payload_path,
) = sys.argv[1:11]

summary = {
    "import_name": short_name,
    "latest_version": wipeout_mcf_glob,
    "status": "INACTIVE",
}
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")

conf = {
    "importName": full_name,
    "version": wipeout_version,
    "comment": comment,
    "skipImportJob": True,
    "forceIngestion": True,
}
if environment == "staging":
    conf["skipProdIngestion"] = True
elif environment == "prod":
    conf["skipStagingIngestion"] = True

payload = {
    "dag_run_id": dag_run_id,
    "logical_date": logical_date,
    "conf": conf,
}
with open(payload_path, "w", encoding="utf-8") as f:
    json.dump(payload, f)
PY

gcloud storage cp "${SUMMARY_FILE}" "gs://${GCS_BUCKET}/${OUTPUT_DIR}/${WIPEOUT_VERSION}/import_summary.json"

# 4. Trigger ManualRefresh DAG with skipImportJob=true and forceIngestion=true.
echo "4/4 Triggering Airflow DAG '${TRIGGER_DAG_ID}' for '${FULL_IMPORT_NAME}' (run_id=${DAG_RUN_ID}${ENVIRONMENT:+, environment=${ENVIRONMENT}})..."
TRIGGER_RESPONSE="$(curl -sS -w "\n%{http_code}" -X POST "${AIRFLOW_URL}/api/v2/dags/${TRIGGER_DAG_ID}/dagRuns" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  --data-binary "@${PAYLOAD_FILE}")"
TRIGGER_BODY="$(echo "${TRIGGER_RESPONSE}" | sed '$d')"
TRIGGER_STATUS="$(echo "${TRIGGER_RESPONSE}" | tail -n 1)"

echo "${TRIGGER_BODY}"
if [[ ! "${TRIGGER_STATUS}" =~ ^[0-9]+$ ]] || [ "${TRIGGER_STATUS}" -lt 200 ] || [ "${TRIGGER_STATUS}" -ge 300 ]; then
    echo "Error: Failed to trigger '${TRIGGER_DAG_ID}' (HTTP ${TRIGGER_STATUS})." >&2
    exit 1
fi
