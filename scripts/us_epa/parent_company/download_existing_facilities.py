# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A simple script to download existing Facilities in Data Commons."""

import os
import sys
from pathlib import Path

import pandas as pd
import requests

from absl import app
from absl import flags

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from util.dc_api_wrapper import get_dc_api_key

FLAGS = flags.FLAGS

_V2_SPARQL_URL = "https://api.datacommons.org/v2/sparql"


def _define_flags() -> None:
    flags.DEFINE_string('output_path', 'tmp_data', 'Output directory')


def download_existing_facilities(output_path: str) -> str:
    Path(output_path).mkdir(exist_ok=True)
    out_file = os.path.join(output_path, 'existing_facilities.csv')

    q = "SELECT DISTINCT ?dcid WHERE {?a typeOf EpaReportingFacility . ?a dcid ?dcid }"
    headers = {"Content-Type": "application/json"}
    api_key = get_dc_api_key()
    if api_key:
        headers["X-API-Key"] = api_key
    response = requests.post(_V2_SPARQL_URL, json={"query": q}, headers=headers)
    response.raise_for_status()
    res = response.json()

    facility_ids = []
    for row in res.get('rows', []):
        cells = row.get('cells', [])
        if not cells:
            continue
        value = cells[0].get('value')
        if value:
            facility_ids.append(value)

    df = pd.DataFrame.from_dict({"epaGhgrpFacilityId": facility_ids})
    df.to_csv(out_file, mode="w", header=True, index=False)
    return out_file


def main(_: list[str]) -> int:
    output_path = FLAGS.output_path
    if not output_path:
        raise ValueError("output_path is required.")
    download_existing_facilities(output_path)
    return 0


if __name__ == '__main__':
    _define_flags()
    app.run(main)
