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

# Import absl for logging and flags
from absl import app, flags, logging


from datacommons_client import DataCommonsClient

# Configure absl logging
logging.set_verbosity(logging.INFO)

FLAGS = flags.FLAGS
flags.DEFINE_string('output_path', 'tmp_data', 'Output directory')


# --- GCS Configuration ---
GCS_BUCKET_NAME = "unresolved_mcf"
GCS_API_KEYS_PREFIX = "epa/parent_company/latest"
API_KEYS_FILENAME = "api_key.json"
# Add the gcs_source_path flag with a default value
flags.DEFINE_string('gcs_source_path',
                    f"gs://{GCS_BUCKET_NAME}/{GCS_API_KEYS_PREFIX}/{API_KEYS_FILENAME}",
                    'Google Cloud Storage path for the API key JSON file.')
                    
# Get the directory of the current script
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define PROJECT_ROOT based on the provided path:

PROJECT_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..', '..', '..'))

# Add PROJECT_ROOT to sys.path
sys.path.insert(0, PROJECT_ROOT)
# Add the 'data/util' directory to sys.path for file_util import
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'data', 'util'))

# Now, directly import file_util.
try:
    from data.util import file_util
except ImportError as e:
    logging.fatal(f"Failed to import file_util: {e}. "
                    "Please ensure data/util/file_util.py exists and is accessible, "
                    "and that the project root and data/util are correctly set in sys.path.", exc_info=True)
    # Added RuntimeError
    raise RuntimeError(f"Initialization failed: {e}")
    sys.exit(1) # Exit if file_util cannot be imported


def get_api_key_from_gcs():
    """
    Retrieves the Data Commons API key from a JSON file in a GCS bucket.
    The file is downloaded to a temporary local directory before being read.
    """
    local_temp_dir = tempfile.mkdtemp()
    local_filepath = os.path.join(local_temp_dir, API_KEYS_FILENAME)
    api_key = None

    try:
        logging.info("--- Starting GCS File Transfer for API key ---")
        
        # Use the gcs_source_path flag
        gcs_source_path = FLAGS.gcs_source_path

        # Use file_util.file_copy to download the file from GCS
        file_util.file_copy(gcs_source_path, local_filepath)
        logging.info(f"Copied '{gcs_source_path}' to '{local_filepath}' using file_util.")

        # Load the JSON file from the local temporary path
        with open(local_filepath, 'r') as f:
            api_keys_data = json.load(f)

        # Extract the specific Data Commons API key
        api_key = api_keys_data.get("DATACOMMONS_API_KEY")
        if not api_key:
            logging.fatal("DATACOMMONS_API_KEY not found in the loaded api_key.json. "
                            "Please ensure the key exists and is named correctly within the JSON.")
            # Added RuntimeError
            raise RuntimeError("API key not found in JSON.")

    except FileNotFoundError as e:
        logging.fatal(f"API keys file not found locally: {local_filepath}. "
                      "Ensure it was successfully downloaded from GCS and the GCS path is correct.")
        # Added RuntimeError
        raise RuntimeError(f"API key file not found: {e}")
    except json.JSONDecodeError as json_err:
        logging.fatal(f"Error decoding JSON from {local_filepath}: {json_err}. "
                      "Please check the file's JSON format in GCS.")
        # Added RuntimeError
        raise RuntimeError(f"JSON decoding error: {json_err}")
    except Exception as e:
        logging.fatal(f"An unexpected error occurred while loading API key from GCS: {e}")
        # Added RuntimeError
        raise RuntimeError(f"Unexpected error during API key retrieval: {e}")
    finally:
        # Clean up the temporary directory
        if os.path.exists(local_temp_dir):
            try:
                shutil.rmtree(local_temp_dir) # Use shutil for cleaner removal
            except OSError as e:
                logging.warning(f"Error cleaning up temporary directory {local_temp_dir}: {e}")
    return api_key


def main(_):
    # Fetch API key from GCS
    api_key = get_api_key_from_gcs()

    pathlib.Path(FLAGS.output_path).mkdir(exist_ok=True)
    out_file = os.path.join(FLAGS.output_path, 'existing_facilities.csv')

    client = DataCommonsClient(api_key=api_key) # Use the fetched API key
    res = client.node.fetch(
        node_dcids=["EpaReportingFacility"],
        expression="<-typeOf"
    )

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
