#!/bin/bash
# 
# This script updates the latest version of an import.
# 
# Usage: ./update_import_version.sh <import_name> <version> <reason>
# Example: ./update_import_version.sh scripts/us_fed/treasury_constant_maturity_rates:USFed_ConstantMaturityRates_Test 2025_12_17T02_30_27_233484_08_00 'Manual validation'

set -e

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <import_name> <version> <reason>"
    exit 1
fi

# Deployed using import-automation/workflow/cloudbuild.yaml
FUNCTION_URL="https://us-central1-datcom-import-automation-prod.cloudfunctions.net/spanner-ingestion-helper"
IMPORT_NAME=$1
VERSION=$2
REASON=$3

curl -X POST "${FUNCTION_URL}" \
  -H "Authorization: bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d "{\"actionType\": \"update_import_version\", \"importName\": \"${IMPORT_NAME}\", \"version\": \"${VERSION}\", \"reason\": \"${REASON}\"}"
