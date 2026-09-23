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
# import automation workflow with skipImportJob=true.
# 
# Usage: ./update_import_version.sh <import_name> <version> <comment>
# Example: ./update_import_version.sh scripts/us_fed/treasury_constant_maturity_rates:USFed_ConstantMaturityRates_Test 2025_12_17T02_30_27_233484_08_00 'Manual validation'

set -e

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <import_name> <version> <comment>"
    exit 1
fi

PROJECT="${PROJECT_ID:-datcom-import-automation-prod}"
LOCATION="${LOCATION:-us-central1}"
WORKFLOW="${WORKFLOW_ID:-import-automation-workflow}"
FUNCTION_URL="https://ingestion-helper-service-staging-965988403328.us-central1.run.app"
IMPORT_NAME=$1
VERSION=$2
COMMENT=$3

echo "Updating import version for ${IMPORT_NAME} to ${VERSION}..."
curl -X POST "${FUNCTION_URL}/imports/version" \
  -H "Authorization: bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d "{\"imports\": [\"${IMPORT_NAME}\"], \"version\": \"${VERSION}\", \"override\": true, \"comment\": \"${COMMENT}\"}"

echo ""
echo "Triggering ${WORKFLOW} with skipImportJob=true..."
DATA="{\"importName\":\"${IMPORT_NAME}\",\"skipImportJob\":true}"

gcloud workflows execute "${WORKFLOW}" \
  --project="${PROJECT}" \
  --location="${LOCATION}" \
  --data="${DATA}"
