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
mkdir -p "${SCRIPT_DIR}/input_files" "${SCRIPT_DIR}/sanitized_input_files"

# Fetch previously staged annual input files from GCS bucket into input_files/
gcloud storage cp --recursive "gs://unresolved_mcf/country/Bulgaria/input_files/BulgariaNSI_Demographics_Year_input_*" "${SCRIPT_DIR}/input_files/"

PYTHON_BIN="python3"
if [[ -x "${SCRIPT_DIR}/../../.env/bin/python3" ]]; then
    PYTHON_BIN="${SCRIPT_DIR}/../../.env/bin/python3"
fi

# Download latest data from live NSI portal (preferring live source over cached
# GCS files, saving raw .html and .csv into input_files/) and write sanitized
# CSV copies into sanitized_input_files/ for stat_var_processor.py.
"${PYTHON_BIN}" "${SCRIPT_DIR}/download_current_year_data.py" \
    --local_dir="${SCRIPT_DIR}/input_files" \
    --sanitized_dir="${SCRIPT_DIR}/sanitized_input_files" \
    --allow_staged_fallback
