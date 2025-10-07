#!/bin/bash
# 
# This script updates the latest version of an import.
# 
# It takes an existing cloud batch job name and a version as input parameters.
# It fetches the configuration of the job including the import name, modifies the 
# import_version_override parameter, and submits a new job with the updated configuration.
#
# Requirements:
# - gcloud
# - jq
#
# Usage: ./update_import_version.sh <job_name> <version>
# Example: ./update_import_version.sh usfed-constantmaturityrates-1755659705 2025_08_15T20_18_20_801877_07_00

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <job_name> <version>"
    echo "Example: $0 usfed-constantmaturityrates-1755659705 2025_08_15T20_18_20_801877_07_00"
    exit 1
fi

JOB_NAME=$1
VERSION=$2
LOCATION="us-central1"
PROJECT="datcom-import-automation-prod"
USER_NAME=$(whoami)
NEW_JOB_NAME="${JOB_NAME}-override-${USER_NAME}"
TEMP_JSON_FILE=$(mktemp)
trap 'rm -f -- "$TEMP_JSON_FILE"' EXIT

echo "Fetching configuration for job '${JOB_NAME}'..."
gcloud batch jobs describe "${JOB_NAME}" --location="${LOCATION}" --project="${PROJECT}" --format=json > "${TEMP_JSON_FILE}"
echo "Updating job configuration with import_version_override: '${VERSION}'"
# TODO: add check to ensure the version exists on GCS.
COMMAND_INDEX=$(jq -r '[.taskGroups[0].taskSpec.runnables[0].container.commands[] | startswith("--import_config=")] | index(true)' "${TEMP_JSON_FILE}")  
IMPORT_CONFIG_COMMAND=$(jq -r ".taskGroups[0].taskSpec.runnables[0].container.commands[${COMMAND_INDEX}]" "${TEMP_JSON_FILE}")
IMPORT_CONFIG_JSON=$(echo "${IMPORT_CONFIG_COMMAND}" | sed 's/^--import_config=//')
NEW_IMPORT_CONFIG_JSON=$(echo "${IMPORT_CONFIG_JSON}" | jq -c --arg version "${VERSION}" '. + {import_version_override: $version}')
NEW_COMMAND="--import_config=${NEW_IMPORT_CONFIG_JSON}"

UPDATED_CONFIG_FILE=$(mktemp)
trap 'rm -f -- "$TEMP_JSON_FILE" "$UPDATED_CONFIG_FILE"' EXIT 

jq --arg new_command "${NEW_COMMAND}" '.taskGroups[0].taskSpec.runnables[0].container.commands[1] = $new_command' "${TEMP_JSON_FILE}" > "${UPDATED_CONFIG_FILE}"

echo "Submitting new job '${NEW_JOB_NAME}'..."
gcloud batch jobs submit "${NEW_JOB_NAME}" \
    --location="${LOCATION}" \
    --project="${PROJECT}" \
    --config="${UPDATED_CONFIG_FILE}"

echo "Successfully submitted new job: ${NEW_JOB_NAME}"
