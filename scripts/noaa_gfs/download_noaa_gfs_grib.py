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

import os
import requests
from datetime import datetime
from pathlib import Path
from absl import app, flags, logging

# --- FLAG DEFINITIONS ---
FLAGS = flags.FLAGS
flags.DEFINE_string('cycle', '00', 'The model cycle (00, 06, 12, 18).')
flags.DEFINE_string('fhour', '000', 'The forecast hour (e.g., 000, 003).')
flags.DEFINE_string('date', None, 'Optional: Date in YYYYMMDD. Defaults to today.')

def download_gfs_file():
    """
    Constructs the remote URL and downloads the GRIB2 file to a dated local directory.
    
    Returns:
        str: The local file path if successful, None otherwise.
    """
    # 1. Setup Date and Paths
    date_stamp = FLAGS.date if FLAGS.date else datetime.now().strftime('%Y%m%d')
    
    # Target directory: ./input_files/YYYYMMDD/
    target_dir = Path("./input_files") / date_stamp
    target_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"gfs.t{FLAGS.cycle}z.pgrb2.0p25.f{FLAGS.fhour}"
    output_path = target_dir / file_name
    
    # 2. Construct URL
    url = (f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/"
           f"gfs.{date_stamp}/{FLAGS.cycle}/atmos/{file_name}")

    logging.info(f"Downloading: {url}")
    logging.info(f"Destination: {output_path}")

    # 3. Perform Streamed Download
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            # Check if file exists on server (e.g., handles 404 if data isn't ready)
            r.raise_for_status() 
            
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024): # 1MB chunks
                    if chunk:
                        f.write(chunk)
                        
        logging.info("Download completed successfully.")
        return str(output_path)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logging.error(f"File not found on NOMADS. The {date_stamp} data might not be posted yet.")
        else:
            logging.error(f"HTTP Error: {e}")
    except Exception as e:
        logging.error(f"Download failed: {e}")
    
    return None

def main(argv):
    """Entry point for the download script."""
    if not download_gfs_file():
        exit(1)

if __name__ == "__main__":
    app.run(main)
