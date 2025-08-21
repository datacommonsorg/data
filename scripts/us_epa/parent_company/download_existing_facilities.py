#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A simple script to download existing Facilities in Data Commons."""

import os
import pathlib
import pandas as pd
import json
import tempfile
import sys
import shutil
from absl import app
from absl import flags
from absl import logging
from datacommons_client import DataCommonsClient


FLAGS = flags.FLAGS
flags.DEFINE_string('output_path', 'tmp_data', 'Output directory')

# --- GCS Configuration ---
flags.DEFINE_string(
    'gcs_source_path',
    'gs://unresolved_mcf/epa/parent_company/latest/api_key.json',
    'Google Cloud Storage path for the API key JSON file.'
)

# Get the directory of the current script
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define PROJECT_ROOT based on the provided path:

PROJECT_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..', '..',
                                            '..'))

# Add PROJECT_ROOT to sys.path
sys.path.insert(0, PROJECT_ROOT)
# Add the 'data/util' directory to sys.path for file_util import
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'data', 'util'))

from data.util import file_util
def get_api_key_from_gcs():
    """
    Retrieves the Data Commons API key from a JSON file in a GCS bucket.
    The file is downloaded to a temporary local directory before being read.

    Returns:
        str: The Data Commons API key if found.

    Raises:
        RuntimeError: If the API key file cannot be found, the JSON is
                      malformed, the key is missing from the JSON, or
                      an unexpected error occurs.
    """
    logging.info("--- Starting GCS File Transfer for API key ---")
    local_temp_dir = tempfile.mkdtemp()
    
    api_key = None  

    try:
        gcs_source_path = FLAGS.gcs_source_path
        local_filepath = os.path.join(local_temp_dir, 'api_key.json')

        # Download the file from GCS
        file_util.file_copy(gcs_source_path, local_filepath)
        logging.info(f"Copied '{gcs_source_path}' to '{local_filepath}'.")

        # Load and validate the JSON data
        with open(local_filepath, 'r') as f:
            api_keys_data = json.load(f)
        
        api_key = api_keys_data.get("DATACOMMONS_API_KEY")
        if not api_key:
            logging.fatal("DATACOMMONS_API_KEY not found in the JSON file.")
            raise RuntimeError("API key not found in JSON.")
        
        return api_key

    except Exception as e:
        # Log the specific error and re-raise as a RuntimeError
        logging.fatal(f"An unexpected error occurred during API key retrieval: {e}.")
        raise RuntimeError("Unexpected error during API key retrieval.") from e
        
    finally:
        shutil.rmtree(local_temp_dir, ignore_errors=True)
        logging.info("Temporary directory cleaned up.")

def main(_):
    # Fetch API key from GCS
    api_key = get_api_key_from_gcs()

    pathlib.Path(FLAGS.output_path).mkdir(exist_ok=True)
    out_file = os.path.join(FLAGS.output_path, 'existing_facilities.csv')

    client = DataCommonsClient(api_key=api_key)  # Use the fetched API key
    res = client.node.fetch(node_dcids=["EpaReportingFacility"],
                            expression="<-typeOf")

    # Convert to dict for safe traversal
    res_dict = res.to_dict(exclude_none=True)
    data = res_dict.get("data") or res_dict

    facility_ids = []
    for type_dcid, obj in data.items():
        arcs = obj.get("arcs", {})
        typeOf = arcs.get("typeOf", {})
        nodes = typeOf.get("nodes", [])
        for node in nodes:
            dcid = node.get("dcid")
            if dcid:
                facility_ids.append(dcid)

    df = pd.DataFrame({"epaGhgrpFacilityId": facility_ids})
    df.to_csv(out_file, index=False)

    logging.info(f" Wrote {len(facility_ids)} facility IDs to: {out_file}")


if __name__ == '__main__':
    app.run(main)
