#!/bin/bash
# Copyright 2026 Google LLC
#
# Runs stat_var_processor.py across all 17 Sweden Census Category 3 (Education)
# raw CSV files using the 4 marginal-view PVMaps, metadata configs, and
# statvar_remap CSVs.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

SV_PROCESSOR="${SV_PROCESSOR:-${SCRIPT_DIR}/../../../tools/statvar_importer/stat_var_processor.py}"
PLACES_CSV="sweden_places_resolved.csv"
EXISTING_STATVAR_MCF="${EXISTING_STATVAR_MCF-gs://unresolved_mcf/scripts/statvar/stat_vars.mcf}"

rm -rf output counters
mkdir -p output counters

COMMON_PVMAP="education_common_pvmap.csv"

run_group() {
  local file_stem="$1"
  local pvmap="$2"
  local metadata="$3"
  local remap="$4"

  echo "=================================================================="
  echo "Processing ${file_stem}.csv with ${COMMON_PVMAP},${pvmap} ..."
  echo "=================================================================="
  python3 "${SV_PROCESSOR}" \
    --input_data="input_files/${file_stem}.csv" \
    --pv_map="${COMMON_PVMAP},${pvmap}" \
    --config_file="${metadata}" \
    --places_resolved_csv="${PLACES_CSV}" \
    --statvar_dcid_remap_csv="${remap}" \
    --existing_statvar_mcf="${EXISTING_STATVAR_MCF}" \
    --output_path="output/${file_stem}" \
    --output_counters="counters/${file_stem}_counters.csv"

  grep -E "error-unresolved-place|dropped-svobs|output-svobs-written|unmapped" \
    "counters/${file_stem}_counters.csv" || true
}

# 1. Group 1: Total by Education Level (4 files, 6 StatVars, mapped_columns=3)
for f in education_nuts1 education_nuts2 education_nuts3 education_municipality; do
  run_group "$f" \
    "education_total_pvmap.csv" \
    "education_total_metadata.csv" \
    "education_total_statvar_remap.csv"
done

# 2. Group 2: By Education Level & Gender (4 files, 12 StatVars, mapped_columns=4)
for f in education_gender_nuts1 education_gender_nuts2 education_gender_nuts3 education_gender_municipality; do
  run_group "$f" \
    "education_gender_pvmap.csv" \
    "education_gender_metadata.csv" \
    "education_gender_statvar_remap.csv"
done

# 3. Group 3: By Education Level & Age Group (6 files, 36 StatVars, mapped_columns=3)
for f in education_age_nuts1 education_age_nuts2 education_age_nuts3 \
         education_age_municipality_1 education_age_municipality_2 education_age_municipality_3; do
  run_group "$f" \
    "education_total_pvmap.csv" \
    "education_total_metadata.csv" \
    "education_age_statvar_remap.csv"
done

# 4. Group 4: By Education Level, Age Group & Gender (3 files, 72 StatVars, mapped_columns=4)
for f in education_age_gender_nuts1 education_age_gender_nuts2 education_age_gender_nuts3; do
  run_group "$f" \
    "education_gender_pvmap.csv" \
    "education_gender_metadata.csv" \
    "education_age_gender_statvar_remap.csv"
done

echo "All 17 Sweden Education CSVs processed successfully!"
