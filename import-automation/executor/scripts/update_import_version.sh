#!/bin/bash
# Copyright 2025 Google LLC
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
# This script updates the latest version of an import and invokes the
# import automation Airflow DAG with skipImportJob=true.
# 
# Usage: ./update_import_version.sh <import_name> <version> <comment> [staging|prod]
# Example: ./update_import_version.sh USFed_ConstantMaturityRates_Test 2025_12_17T02_30_27_233484_08_00 'Manual validation' staging

set -e

if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
    echo "Usage: $0 <import_name> <version> <comment> [staging|prod]"
    exit 1
fi

AIRFLOW_URL="${AIRFLOW_WEB_SERVER_URL:-https://030069cf9df9415bbd743bf7e18a6a65-dot-us-central1.composer.googleusercontent.com}"
IMPORT_NAME=$1
VERSION=$2
if [ "${VERSION,,}" = "staging" ]; then
    VERSION="STAGING"
fi
COMMENT=$3
ENVIRONMENT=${4:-}
SHORT_IMPORT_NAME="${IMPORT_NAME##*:}"
DAG_ID="${DAG_ID:-${SHORT_IMPORT_NAME}}"

IMPORT_NAME_FIELD=""
if [[ "${IMPORT_NAME}" == *:* ]] || [ "${DAG_ID}" != "${SHORT_IMPORT_NAME}" ]; then
    IMPORT_NAME_FIELD="\"importName\":\"${IMPORT_NAME}\","
fi

INGESTION_FLAGS=""
if [ -n "${ENVIRONMENT}" ]; then
    case "${ENVIRONMENT}" in
        staging)
            INGESTION_FLAGS=",\"skipProdIngestion\":true"
            ;;
        prod)
            INGESTION_FLAGS=",\"skipStagingIngestion\":true"
            ;;
        *)
            echo "Invalid environment '${ENVIRONMENT}'. Expected 'staging' or 'prod'."
            exit 1
            ;;
    esac
fi

echo "Triggering Airflow DAG ${DAG_ID} for ${IMPORT_NAME} (version=${VERSION}, skipImportJob=true${ENVIRONMENT:+, environment=${ENVIRONMENT}})..."
LOGICAL_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DAG_RUN_ID="version_update__${USER}__${SHORT_IMPORT_NAME}__$(date -u +%s)"
CONF="{${IMPORT_NAME_FIELD}\"version\":\"${VERSION}\",\"overrideVersion\":true,\"comment\":\"${COMMENT}\",\"skipImportJob\":true${INGESTION_FLAGS}}"

curl -X POST "${AIRFLOW_URL}/api/v2/dags/${DAG_ID}/dagRuns" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d "{\"dag_run_id\": \"${DAG_RUN_ID}\", \"logical_date\": \"${LOGICAL_DATE}\", \"conf\": ${CONF}}"
echo ""
