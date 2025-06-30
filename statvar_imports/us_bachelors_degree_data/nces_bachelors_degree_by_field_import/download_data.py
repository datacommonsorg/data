# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, config, sys
from absl import logging, app

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, '../../../util'))

from download_util_script import _retry_method

def download(inputdir):
    if not os.path.exists(inputdir):        
        os.makedirs(inputdir, exist_ok=True)
        logging.info(f"Created download directory: {inputdir}")

    count = 0
    for url_config in config.URL_CONFIGS:
        for i in range(config.START_DIGEST_YEAR, config.END_DIGEST_YEAR + 1):
            try:
                url = url_config["url_template"].format(i)
                gender_code = url_config["gender_code"]
                response = _retry_method(url.format(i), headers=None, tries=3, delay=5, backoff=2)
                if response.status_code==200:
                    with open(os.path.join(inputdir,f"table_{gender_code}_{count}.xlsx"),"wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    logging.info(f"Successfully downloaded the data for the url {url.format(i)}")
                else:
                    logging.warning(f"Skipping download for {url}. Received non-200 status code: {response.status_code}")
                count+=1
            except Exception as e:
                logging.error(f"Error occured while downloading the data: {e}")      
    logging.info("Download process finished.") 

def main(_):
    input_dir = os.path.join(SCRIPT_DIR, "input_files")
    try:
        download(input_dir)
    except Exception as e:
        logging.fatal(f"A critical error prevented the download process from  completing: {e}")

if __name__ == "__main__":
   app.run(main)

