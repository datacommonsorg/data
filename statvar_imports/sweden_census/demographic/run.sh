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
# Runs stat_var_processor.py across all 23 Sweden Census Category 1 (Demographic)
# raw CSV files using the unified demographic_pvmap.csv, demographic_metadata.csv,
# and demographic_statvar_remap.csv with bounded parallelism.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

SV_PROCESSOR="${SV_PROCESSOR:-${SCRIPT_DIR}/../../../tools/statvar_importer/stat_var_processor.py}"
PV_MAP="demographic_pvmap.csv"
CONFIG_FILE="demographic_metadata.csv"
PLACES_CSV="sweden_places_resolved.csv"
REMAP_CSV="demographic_statvar_remap.csv"
EXISTING_STATVAR_MCF="${EXISTING_STATVAR_MCF-gs://unresolved_mcf/scripts/statvar/stat_vars.mcf}"
MAX_PARALLEL="${MAX_PARALLEL:-4}"

rm -rf output counters
mkdir -p output counters

process_csv() {
  local input_csv="$1"
  local file_stem
  file_stem="$(basename "${input_csv}" .csv)"

  echo "=================================================================="
  echo "Processing ${file_stem}.csv with ${PV_MAP} ..."
  echo "=================================================================="
  python3 "${SV_PROCESSOR}" \
    --input_data="${input_csv}" \
    --pv_map="${PV_MAP}" \
    --config_file="${CONFIG_FILE}" \
    --places_resolved_csv="${PLACES_CSV}" \
    --statvar_dcid_remap_csv="${REMAP_CSV}" \
    --existing_statvar_mcf="${EXISTING_STATVAR_MCF}" \
    --generate_statvar_name=True \
    --skip_constant_csv_columns=False \
    --output_path="output/${file_stem}" \
    --output_counters="counters/${file_stem}_counters.csv"

  grep -E "error-unresolved-place|dropped-svobs|output-svobs-csv-rows|existing-nodes-from-api" \
    "counters/${file_stem}_counters.csv" || true
}

pids=()
failed=0

for input_csv in input_files/*.csv; do
  process_csv "${input_csv}" &
  pids+=("$!")

  if (( ${#pids[@]} >= MAX_PARALLEL )); then
    for pid in "${pids[@]}"; do
      if ! wait "${pid}"; then
        failed=1
      fi
    done
    pids=()
    if (( failed != 0 )); then
      echo "ERROR: One or more stat_var_processor.py jobs failed." >&2
      exit 1
    fi
  fi
done

for pid in "${pids[@]}"; do
  if ! wait "${pid}"; then
    failed=1
  fi
done

if (( failed != 0 )); then
  echo "ERROR: One or more stat_var_processor.py jobs failed." >&2
  exit 1
fi

echo "All 23 Sweden Demographic CSVs processed successfully!"
