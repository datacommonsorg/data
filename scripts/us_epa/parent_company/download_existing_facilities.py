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

from absl import app
from absl import flags
from absl import logging

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from util.dc_api_wrapper import dc_api_wrapper
from util.dc_api_wrapper import get_datacommons_client

FLAGS = flags.FLAGS


def _define_flags() -> None:
    flags.DEFINE_string('output_path', os.path.join(_SCRIPT_PATH,
                                                    'input_files'),
                        'Output directory')


def download_existing_facilities(output_path: str) -> str:
    Path(output_path).mkdir(parents=True, exist_ok=True)
    out_file = os.path.join(output_path, 'existing_facilities.csv')

    logging.info(
        'Fetching existing EpaReportingFacility nodes from Data Commons...')
    client = get_datacommons_client()
    response = dc_api_wrapper(
        function=client.node.fetch_property_values,
        args={
            'node_dcids': 'EpaReportingFacility',
            'properties': 'typeOf',
            'out': False,
        },
        retries=5,
        retry_secs=5,
    )
    if not response:
        raise RuntimeError(
            'Failed to fetch EpaReportingFacility nodes from Data Commons.')
    facility_nodes = response.get_properties().get("EpaReportingFacility",
                                                   {}).get("typeOf", [])
    facility_ids = []
    facility_ids_set = set()
    for node in facility_nodes:
        value = getattr(node, "dcid", None)
        if not value or value in facility_ids_set:
            continue
        facility_ids_set.add(value)
        facility_ids.append(value)

    if not facility_ids:
        raise RuntimeError(
            'No EpaReportingFacility nodes returned from Data Commons.')

    logging.info(f'Found {len(facility_ids)} unique EpaReportingFacility DCIDs '
                 f'(from {len(facility_nodes)} raw node entries).')
    df = pd.DataFrame.from_dict({"epaGhgrpFacilityId": facility_ids})
    tmp_file = out_file + '.tmp'
    df.to_csv(tmp_file, mode="w", header=True, index=False)
    os.replace(tmp_file, out_file)
    logging.info(f'Wrote existing facilities to {out_file}.')
    return out_file


def main(_: list[str]) -> int:
    logging.set_verbosity(logging.INFO)
    output_path = FLAGS.output_path
    if not output_path:
        raise ValueError("output_path is required.")
    download_existing_facilities(output_path)
    return 0


if __name__ == '__main__':
    _define_flags()
    app.run(main)
