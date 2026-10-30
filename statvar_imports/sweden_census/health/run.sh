#!/bin/bash
# Copyright 2026 Google LLC
#
# Runs stat_var_processor.py across all 13 Sweden Census Category 2
# (Health & Vital Statistics) raw CSV files using the recovered PVMaps,
# metadata configs, and statvar_remap CSVs.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

SV_PROCESSOR="${SV_PROCESSOR:-${SCRIPT_DIR}/../../../tools/statvar_importer/stat_var_processor.py}"
PLACES_CSV="sweden_places_resolved.csv"
EXISTING_STATVAR_MCF="${EXISTING_STATVAR_MCF-gs://unresolved_mcf/scripts/statvar/stat_vars.mcf}"

rm -rf output counters
mkdir -p output counters

run_group() {
  local file_stem="$1"
  local pvmap="$2"
  local metadata="$3"
  local remap="${4:-}"

  echo "=================================================================="
  echo "Processing ${file_stem}.csv with ${pvmap} ..."
  echo "=================================================================="
  local remap_arg=()
  if [[ -n "${remap}" ]]; then
    remap_arg=("--statvar_dcid_remap_csv=${remap}")
  fi

  python3 "${SV_PROCESSOR}" \
    --input_data="input_files/${file_stem}.csv" \
    --pv_map="${pvmap}" \
    --config_file="${metadata}" \
    --places_resolved_csv="${PLACES_CSV}" \
    "${remap_arg[@]}" \
    --existing_statvar_mcf="${EXISTING_STATVAR_MCF}" \
    --output_path="output/${file_stem}" \
    --output_counters="counters/${file_stem}_counters.csv"

  grep -E "error-unresolved-place|dropped-svobs|output-svobs-csv-rows|unmapped" \
    "counters/${file_stem}_counters.csv" || true
}

# 1. Group 1: Total Deaths by Region (4 files, 1 StatVar, mapped_columns=2)
for f in Death_NUTS1 Death_NUTS2 Death_NUTS3 Death_Muncipality; do
  run_group "$f" \
    "deaths_total_pvmap.csv" \
    "deaths_total_metadata.csv" \
    "deaths_total_statvar_remap.csv"
done

# 2. Group 2: Deaths by Gender (4 files, 2 StatVars, mapped_columns=3)
for f in Death_gender_NUTS1 Death_gender_NUTS2 Death_gender_NUTS3 Death_gender_Muncipality; do
  run_group "$f" \
    "deaths_gender_pvmap.csv" \
    "deaths_gender_metadata.csv" \
    "deaths_gender_statvar_remap.csv"
done

# 3. Group 3: Deaths by Age & Gender (3 files, 22 StatVars, mapped_columns=3)
for f in Death_age_gender_NUTS1 Death_age_gender_NUTS2 Death_age_gender_NUTS3; do
  run_group "$f" \
    "deaths_age_gender_pvmap.csv" \
    "deaths_age_gender_metadata.csv" \
    "deaths_age_gender_statvar_remap.csv"
done

# 4. Group 4: Municipal Fertility Rate by Gender (1 file, 2 StatVars, mapped_columns=2)
run_group "FertilityRate_gender_Muncipality" \
  "fertility_pvmap.csv" \
  "fertility_metadata.csv"

# 5. Group 5: Historical National Live Births by Gender & Total (1 file, 3 StatVars)
run_group "LiveBirth_gender_total_country" \
  "livebirth_pvmap.csv" \
  "livebirth_metadata.csv" \
  "livebirth_statvar_remap.csv"

echo "All 13 Sweden Health & Vital Statistics CSVs processed successfully!"
