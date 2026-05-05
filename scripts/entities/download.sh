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

set -e

# Parse arguments
for i in "$@"; do
  case $i in
    --entity=*)
      ENTITY="${i#*=}"
      ;;
    --version=*)
      VERSION="${i#*=}"
      ;;
    *)
      # Skip unknown options
      ;;
  esac
done

BUCKET_NAME="datcom-prod-imports"
DIR_NAME=$(basename "$(pwd)")
GCS_FOLDER_PREFIX="scripts/${DIR_NAME}/${ENTITY}"
GCS_PATH="gs://${BUCKET_NAME}/${GCS_FOLDER_PREFIX}/${VERSION}"

echo "Downloading import ${ENTITY} for version ${VERSION} from ${GCS_PATH} to $(pwd)"
mkdir -p "${ENTITY}"
gcloud storage cp -r "${GCS_PATH}" "${ENTITY}/" &> copy.log
echo "Successfully downloaded ${ENTITY} version ${VERSION}"

# TODO: remove after scrpts are checked in
# Download scripts from GCS
SCRIPTS_GCS_PATH="gs://${BUCKET_NAME}/scripts/${DIR_NAME}/process/*"
SCRIPTS_LOCAL_PATH="../../import-automation/executor/scripts"
echo "Downloading scripts from ${SCRIPTS_GCS_PATH} to ${SCRIPTS_LOCAL_PATH}"
mkdir -p "${SCRIPTS_LOCAL_PATH}"
gcloud storage cp -r "${SCRIPTS_GCS_PATH}" "${SCRIPTS_LOCAL_PATH}/"



