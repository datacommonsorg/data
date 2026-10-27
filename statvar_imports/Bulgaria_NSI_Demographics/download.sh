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

# Fetch all staged input files from GCS bucket
if command -v gcloud &> /dev/null; then
    gcloud storage cp --recursive "gs://unresolved_mcf/country/Bulgaria/input_files/*.csv" "${SCRIPT_DIR}/input_files/"
else
    gsutil cp "gs://unresolved_mcf/country/Bulgaria/input_files/*.csv" "${SCRIPT_DIR}/input_files/"
fi

# Sanitize trailing non-breaking spaces (\xa0), triple quotes, and footnote asterisks from NSI web exports
python3 - "${SCRIPT_DIR}/input_files" << 'EOF'
import glob, os, re, sys

input_dir = sys.argv[1]
for fpath in glob.glob(os.path.join(input_dir, '*.csv')):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('"""', '"').replace('\xa0', ' ').replace('AS OF 31.12.*', 'AS OF 31.12.')
    content = re.sub(r'(\b\d+)\s*-\s*(\d+\b)', r'\1 - \2', content)
    lines = [l.rstrip() for l in content.splitlines()]
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
EOF
