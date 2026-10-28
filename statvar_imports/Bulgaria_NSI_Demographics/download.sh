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

# Fetch staged annual input files from GCS bucket (kept unchanged in input_files/)
if command -v gcloud &> /dev/null; then
    gcloud storage cp --recursive "gs://unresolved_mcf/country/Bulgaria/input_files/BulgariaNSI_Demographics_Year_input_*.csv" "${SCRIPT_DIR}/input_files/"
else
    gsutil cp "gs://unresolved_mcf/country/Bulgaria/input_files/BulgariaNSI_Demographics_Year_input_*.csv" "${SCRIPT_DIR}/input_files/"
fi

PYTHON_BIN="python3"
if [[ -x "${SCRIPT_DIR}/../../.env/bin/python3" ]]; then
    PYTHON_BIN="${SCRIPT_DIR}/../../.env/bin/python3"
fi

# Write sanitized copies (removing trailing non-breaking spaces \xa0, triple quotes,
# and footnote asterisks from NSI web exports) into sanitized_input_files/,
# and validate structural and arithmetic consistency across all annual CSVs.
"${PYTHON_BIN}" - "${SCRIPT_DIR}/input_files" "${SCRIPT_DIR}/sanitized_input_files" "${SCRIPT_DIR}" << 'EOF'
import csv, glob, io, os, re, sys

input_dir = sys.argv[1]
sanitized_dir = sys.argv[2]
script_dir = sys.argv[3]
sys.path.insert(0, script_dir)
from download_current_year_data import validate_file_format

files = sorted(glob.glob(os.path.join(input_dir, 'BulgariaNSI_Demographics_Year_input_*.csv')))
if not files:
    sys.exit(f"Error: No annual input CSV files matched in {input_dir}")

for fpath in files:
    bname = os.path.basename(fpath)
    m = re.search(r'Year_input_(\d{4})\.csv$', bname)
    if not m:
        sys.exit(f"Error: Input file '{bname}' does not match expected pattern 'Year_input_YYYY.csv'")

    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('"""', '"').replace('\xa0', ' ').replace('AS OF 31.12.*', 'AS OF 31.12.')
    content = re.sub(r'(\b\d+)\s*-\s*(\d+\b)', r'\1 - \2', content)
    reader = list(csv.reader(io.StringIO(content)))
    cleaned_rows = [[re.sub(r'\s+', ' ', c).strip() for c in row] for row in reader]

    out_path = os.path.join(sanitized_dir, bname)
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(cleaned_rows)

    validate_file_format(out_path, int(m.group(1)))
EOF
