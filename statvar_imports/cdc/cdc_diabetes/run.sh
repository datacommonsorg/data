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
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

if [[ -x "${REPO_ROOT}/.env/bin/python3" ]]; then
  PYTHON_BIN="${REPO_ROOT}/.env/bin/python3"
else
  PYTHON_BIN="python3"
fi

BASELINE_ARG=()
if [[ -n "${CDC_DIABETES_BASELINE_DIR:-}" && -d "${CDC_DIABETES_BASELINE_DIR}" ]]; then
  BASELINE_ARG=("--baseline_dir=${CDC_DIABETES_BASELINE_DIR}")
elif [[ -d "/usr/local/google/dc/git/data-imports/shared_cache/cdc_diabetes/baseline_20240112" ]]; then
  BASELINE_ARG=("--baseline_dir=/usr/local/google/dc/git/data-imports/shared_cache/cdc_diabetes/baseline_20240112")
fi

"${PYTHON_BIN}" "${SCRIPT_DIR}/download_and_preprocess.py" \
  "${BASELINE_ARG[@]}" \
  --raw_input_dir="${SCRIPT_DIR}/input_files" \
  --output_dir="${SCRIPT_DIR}/output" \
  "$@"
