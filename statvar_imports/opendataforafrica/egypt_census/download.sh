#!/bin/bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rm -rf "${SCRIPT_DIR}/input_files" "${SCRIPT_DIR}/output" "${SCRIPT_DIR}/counters"
mkdir -p "${SCRIPT_DIR}/input_files" "${SCRIPT_DIR}/output" "${SCRIPT_DIR}/counters"

gcloud storage cp --verbosity=error --recursive \
  "gs://unresolved_mcf/opendataforafrica/egypt_census/input_files/*" \
  "${SCRIPT_DIR}/input_files/"

EXPECTED_TABLES=(
  actytif behvqtc bluhqme cjczlcd lxoyale mptocre pqpump szfufmb
  txbrrac ujtdaag ulouknf viytqvf wcssteb wtxyghf xovpotd zkjifzd zpdksog
)
for table_id in "${EXPECTED_TABLES[@]}"; do
  csv_file="${SCRIPT_DIR}/input_files/${table_id}.csv"
  if [[ ! -s "${csv_file}" ]]; then
    echo "ERROR: Missing or empty downloaded CSV file: ${csv_file}" >&2
    exit 1
  fi
done
