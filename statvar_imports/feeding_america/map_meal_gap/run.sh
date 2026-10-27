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

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="${INPUT_DIR:-${SCRIPT_DIR}/input_files}"
OUTPUT_DIR="${OUTPUT_DIR:-${SCRIPT_DIR}/output}"
GCS_MMG_PREFIX="${GCS_MMG_PREFIX:-gs://unresolved_mcf/feeding_america/map_meal_gap}"
GCS_FI_INPUT_PREFIX="${GCS_FI_INPUT_PREFIX:-gs://unresolved_mcf/feeding_america/food_insecurity/input_files}"

mkdir -p "${INPUT_DIR}" "${OUTPUT_DIR}"

if ! compgen -G "${INPUT_DIR}/*.csv" >/dev/null && ! compgen -G "${INPUT_DIR}/*.xlsx" >/dev/null; then
  echo "Staging Feeding America source files from GCS into ${INPUT_DIR}..."
  if command -v gcloud >/dev/null 2>&1; then
    gcloud storage cp "${GCS_MMG_PREFIX}/*.csv" "${INPUT_DIR}/" 2>/dev/null || true
    gcloud storage cp "${GCS_MMG_PREFIX}/*.xlsx" "${INPUT_DIR}/" 2>/dev/null || true
    gcloud storage cp "${GCS_FI_INPUT_PREFIX}/*.xlsx" "${INPUT_DIR}/" 2>/dev/null || true
  elif command -v gsutil >/dev/null 2>&1; then
    gsutil cp "${GCS_MMG_PREFIX}/*.csv" "${INPUT_DIR}/" 2>/dev/null || true
    gsutil cp "${GCS_MMG_PREFIX}/*.xlsx" "${INPUT_DIR}/" 2>/dev/null || true
    gsutil cp "${GCS_FI_INPUT_PREFIX}/*.xlsx" "${INPUT_DIR}/" 2>/dev/null || true
  fi
fi

if ! compgen -G "${INPUT_DIR}/*.csv" >/dev/null && ! compgen -G "${INPUT_DIR}/*.xlsx" >/dev/null && ! compgen -G "${INPUT_DIR}/table/*.csv" >/dev/null; then
  echo "ERROR: No input CSV or Excel files found in ${INPUT_DIR}." >&2
  exit 1
fi

python3 "${SCRIPT_DIR}/process_mmg.py" \
  --input_dir="${INPUT_DIR}" \
  --output_dir="${OUTPUT_DIR}" \
  --tmcf_path="${SCRIPT_DIR}/FeedingAmerica_MMG.tmcf"
