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

if [[ -z "${ENTITY}" || -z "${VERSION}" ]]; then
  echo "Error: --entity and --version must be non-empty." >&2
  exit 1
fi

DIR_NAME="entities"
BUCKET_NAME="datcom-prod-imports"
GCS_FOLDER_PREFIX="scripts/entities/${ENTITY}"
GCS_PATH="gs://${BUCKET_NAME}/${GCS_FOLDER_PREFIX}/${VERSION}"

echo "Downloading import ${ENTITY} for version ${VERSION} from ${GCS_PATH} to $(pwd)"
mkdir -p "${ENTITY}"
gcloud storage cp -r "${GCS_PATH}" "${ENTITY}/" &> copy.log
if [[ -n "${ENTITY}" && -n "${VERSION}" ]]; then
  rm -rf "${ENTITY}/${VERSION}"/input[0-9]*
  rm -rf "${ENTITY}/${VERSION}/source_files"
fi
echo "Successfully downloaded ${ENTITY} version ${VERSION}"
