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
mkdir -p "${SCRIPT_DIR}/input_files"
mkdir -p "${SCRIPT_DIR}/output"

# Stage provisional place node for Conflict Areas to output/
cp "${SCRIPT_DIR}/qiubrhc_places.mcf" "${SCRIPT_DIR}/output/qiubrhc_places.mcf"

gcloud storage cp --recursive "gs://unresolved_mcf/opendataforafrica/uganda_census/input_files/*" "${SCRIPT_DIR}/input_files/"
