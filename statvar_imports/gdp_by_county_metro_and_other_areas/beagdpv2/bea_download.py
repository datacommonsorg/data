# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, shutil, requests
import zipfile
from absl import app, logging
from pathlib import Path
from retry import retry
import config

BEA_ZIP_URL = config.BEA_ZIP_URL

INPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_files")
Path(INPUT_DIR).mkdir(parents=True, exist_ok=True)

@retry(tries=3, delay=5, backoff=2)
def retry_method(url, headers=None):
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response

#Function to download and save the ZIP file
def download_file():
    logging.info("Starting download...")
    zip_path = os.path.join(INPUT_DIR, "CAGDP9.zip")
    
    try:
        response = retry_method(BEA_ZIP_URL)
        with open(zip_path, "wb") as f:
            f.write(response.content)
            
        logging.info(f"Downloaded file saved to {zip_path}")
        return  zip_path
    
    except Exception as e:
        logging.fatal(f"Failed to download file: {e}")
        return None
    
#Function to extract and process the CSV file from ZIP
def extract_and_process(zip_path):
    logging.info("Extracting ZIP file...")
    
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(INPUT_DIR)
            input_file = [filename for filename in zip_ref.namelist() if filename.endswith(".csv") and "ALL_AREAS" in filename]
            input_file_path = os.path.join(INPUT_DIR, input_file[0])
            for filename in os.listdir(INPUT_DIR):
                file_path = os.path.join(INPUT_DIR, filename)
                if file_path == input_file_path:
                    logging.info(f"Keeping file: {input_file_path}")
                    continue
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)             
    except Exception as e:
        logging.fatal(f"Failed to extract the file: {e}")

def main(argv):
    zip_path = download_file()
    if zip_path:
        extract_and_process(zip_path)

if __name__ == "__main__":  
    app.run(main)
    
