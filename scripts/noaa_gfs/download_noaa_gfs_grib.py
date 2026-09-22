# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Automates GFS GRIB2 source file retrieval from NOAA NOMADS.
This script manages dated directory structures and utilizes memory-efficient 
HTTP streaming to download large-scale meteorological datasets for 
downstream Data Commons ingestion.
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from absl import app, flags, logging
from google.cloud import storage
from google.api_core import exceptions

# --- FLAG DEFINITIONS ---
FLAGS = flags.FLAGS
flags.DEFINE_string('project_id', 'datcom', 'The GCP Project ID.')
flags.DEFINE_string('bucket_name', 'datcom-prod-imports',
                    'The GCS bucket name.')
flags.DEFINE_string('state_path',
                    'scripts/noaa_gfs/NOAA_GlobalForecastSystem/state.json',
                    'The path within the bucket for state.json.')


def get_gcs_client():
    """Initializes the GCS client with a specific Project ID."""
    return storage.Client(project=FLAGS.project_id)


def load_state():
    """Reads state from GCS. Returns default if file doesn't exist."""
    client = get_gcs_client()
    bucket = client.bucket(FLAGS.bucket_name)
    blob = bucket.blob(FLAGS.state_path)

    try:
        state_data = blob.download_as_text()
        logging.info(
            f"Successfully loaded state from gs://{FLAGS.bucket_name}/{FLAGS.state_path}"
        )
        return json.loads(state_data)
    except exceptions.NotFound:
        logging.warning(
            "State file not found in GCS. Starting from default (24h ago).")
        # Default: Start 24 hours ago
        yesterday = (datetime.now() - timedelta(days=1))
        return {"date": yesterday.strftime('%Y%m%d'), "cycle": "18"}


def get_next_slot(current_date_str, current_cycle):
    """Calculates the next 6-hour GFS slot."""
    current_dt = datetime.strptime(f"{current_date_str}{current_cycle}",
                                   '%Y%m%d%H')
    next_dt = current_dt + timedelta(hours=6)
    return next_dt.strftime('%Y%m%d'), next_dt.strftime('%H')


def download_gfs_file(date_stamp, cycle, fhour="000"):
    """Downloads the GRIB2 file from NOAA."""
    # 1. Setup Paths
    # Target directory: ./input_files/YYYYMMDD/
    target_dir = Path("./input_files") / date_stamp
    target_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"gfs.t{cycle}z.pgrb2.0p25.f{fhour}"
    output_path = target_dir / file_name

    # 2. Construct URL
    url = (f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/"
           f"gfs.{date_stamp}/{cycle}/atmos/{file_name}")

    logging.info(f"Downloading: {url}")
    logging.info(f"Destination: {output_path}")

    # 3. Perform Streamed Download
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            # Check if file exists on server (e.g., handles 404 if data isn't ready)
            r.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 *
                                            1024):  # 1MB chunks
                    if chunk:
                        f.write(chunk)

        logging.info(f"Successfully downloaded: {date_stamp} Cycle {cycle}")
        return str(output_path)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logging.error(
                f"File not found on NOMADS. The {date_stamp} data might not be posted yet."
            )
        else:
            logging.error(f"HTTP Error: {e}")
    except Exception as e:
        logging.error(f"Download failed: {e}")

    return None


def main(argv):
    """Entry point for the download script."""
    state = load_state()
    current_date = state['date']
    current_cycle = state['cycle']

    # Get the latest possible slot (NOAA usually has a few hours delay)
    now = datetime.now() - timedelta(hours=4)

    logging.info(f"Iterating from: {current_date} {current_cycle}z")

    while True:
        # 1. Determine the next slot to try
        next_date, next_cycle = get_next_slot(current_date, current_cycle)
        next_dt = datetime.strptime(f"{next_date}{next_cycle}", '%Y%m%d%H')

        # 2. Stop if we are trying to download files from the future
        if next_dt > now:
            logging.info(
                "All available files up to current time have been checked.")
            break

        # 3. Attempt Download
        if download_gfs_file(next_date, next_cycle):
            current_date, current_cycle = next_date, next_cycle
        else:
            # If a file isn't found, it might not be posted yet.
            # We stop here to maintain chronological integrity.
            logging.info(
                f"Reached the end of available data on server at {next_date} {next_cycle}z."
            )
            break


if __name__ == "__main__":
    app.run(main)
