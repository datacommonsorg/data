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

# Sanitize trailing non-breaking spaces (\xa0), triple quotes, and footnote asterisks from NSI web exports,
# and validate arithmetic consistency across both annual and historical CSVs.
python3 - "${SCRIPT_DIR}/input_files" "${SCRIPT_DIR}" << 'EOF'
import csv, glob, os, re, sys

input_dir = sys.argv[1]
script_dir = sys.argv[2]
sys.path.insert(0, script_dir)
from download_current_year_data import validate_file_format, validate_historical_file_format

for fpath in sorted(glob.glob(os.path.join(input_dir, '*.csv'))):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('"""', '"').replace('\xa0', ' ').replace('AS OF 31.12.*', 'AS OF 31.12.')
    content = re.sub(r'(\b\d+)\s*-\s*(\d+\b)', r'\1 - \2', content)
    reader = list(csv.reader(content.splitlines()))
    cleaned_rows = [[c.strip() for c in row] for row in reader]
    with open(fpath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(cleaned_rows)

    bname = os.path.basename(fpath)
    m = re.search(r'Year_input_(\d{4})\.csv$', bname)
    if m:
        validate_file_format(fpath, int(m.group(1)))
    else:
        validate_historical_file_format(fpath)
EOF
