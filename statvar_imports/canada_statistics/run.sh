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
# Downloads manually-staged Statistics Canada raw CSVs from GCS into local
# input_files/ unchanged (following the semi-automated import pattern).

set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <gcs_path>" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GCS_PATH="${1%/}/"
DESTINATION_DIR="${SCRIPT_DIR}/input_files"

EXPECTED_FILES=(
  "Population.csv"
  "can_agri_producer_deliveries_major_grains.csv"
  "can_infant_mortality.csv"
  "can_life_expectancy.csv"
  "can_mortality_rate.csv"
  "can_pop_age_gender.csv"
  "can_public_school_enrollment.csv"
  "can_unemployment_rate_above15.csv"
)

mkdir -p "${DESTINATION_DIR}"
rm -f "${DESTINATION_DIR}"/*.csv
gcloud storage cp --verbosity=error "${GCS_PATH}*.csv" "${DESTINATION_DIR}/"

missing=0
for fname in "${EXPECTED_FILES[@]}"; do
  if [ ! -s "${DESTINATION_DIR}/${fname}" ]; then
    echo "ERROR: Missing or empty staged CSV: ${DESTINATION_DIR}/${fname}" >&2
    missing=1
  fi
done
if [ "${missing}" -ne 0 ]; then
  exit 1
fi
