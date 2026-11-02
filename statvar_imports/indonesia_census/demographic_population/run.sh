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

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

mkdir -p "${SCRIPT_DIR}/input_files"
mkdir -p "${SCRIPT_DIR}/output_files"
mkdir -p "${SCRIPT_DIR}/counters"

# 1. Copy consolidated historical baseline CSVs (1971-2022) and shared TMCF from GCS
gsutil -m cp \
  "gs://unresolved_mcf/country/indonesia/demographic/historical/idn_population_historical_1971_2022.csv" \
  "gs://unresolved_mcf/country/indonesia/demographic/historical/idn_age_gender_historical_2010_2022.csv" \
  "${SCRIPT_DIR}/output_files/" || true
cp "${SCRIPT_DIR}/common_tmcf.tmcf" "${SCRIPT_DIR}/output_files/common_tmcf.tmcf"

# 2. Download 2023-2025+ raw input CSVs from BPS WebAPI (or fallback to staged GCS files)
python3 "${SCRIPT_DIR}/download.py" \
  --output_dir="${SCRIPT_DIR}/input_files" || \
gsutil -m cp \
  "gs://unresolved_mcf/country/indonesia/demographic/input_files/*.csv" \
  "${SCRIPT_DIR}/input_files/"

# 3. Run StatVarProcessor on Total Population (2023-2025+)
python3 "${REPO_ROOT}/tools/statvar_importer/stat_var_processor.py" \
  --input_data="${SCRIPT_DIR}/input_files/idn_population_2023_2025.csv" \
  --pv_map="${SCRIPT_DIR}/pvmaps/idn_population_pvmap.csv" \
  --config_file="${SCRIPT_DIR}/idn_demographic_metadata.csv" \
  --places_resolved_csv="${SCRIPT_DIR}/idn_places_resolved.csv" \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path="${SCRIPT_DIR}/output_files/idn_population_2023_2025" \
  --output_counters="${SCRIPT_DIR}/counters/idn_population_2023_2025_counters.csv"

# 4. Run StatVarProcessor on Age & Gender Population (2023-2025+)
python3 "${REPO_ROOT}/tools/statvar_importer/stat_var_processor.py" \
  --input_data="${SCRIPT_DIR}/input_files/idn_age_gender_2023_2025.csv" \
  --pv_map="${SCRIPT_DIR}/pvmaps/idn_age_gender_pvmap.csv" \
  --config_file="${SCRIPT_DIR}/idn_demographic_metadata.csv" \
  --places_resolved_csv="${SCRIPT_DIR}/idn_places_resolved.csv" \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path="${SCRIPT_DIR}/output_files/idn_age_gender_2023_2025" \
  --output_counters="${SCRIPT_DIR}/counters/idn_age_gender_2023_2025_counters.csv"
