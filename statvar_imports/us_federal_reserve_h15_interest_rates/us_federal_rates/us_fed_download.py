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

import os, requests, datetime
from absl import app, logging
from pathlib import Path
from retry import retry
import config

INPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_files")
Path(INPUT_DIR).mkdir(parents=True, exist_ok=True)

date = datetime.date.today().strftime('%Y-%m-%d')

@retry(tries=3, delay=5, backoff=2)
def retry_method(url, headers=None):
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response

def download_files(us_fed_urls):
    logging.info("Starting download...")
    count = 1
    try:
        for url in us_fed_urls:
            response = retry_method(url.format(date))
            input_path = os.path.join(INPUT_DIR, f"us_fed_input_{count}.csv")
            with open(input_path, "wb") as f:
                f.write(response.content)
            count+=1    
        logging.info(f"Downloaded file saved to {INPUT_DIR}")
    except requests.exceptions.RequestException as e:
        logging.fatal(f"Failed to download file: {e}")
        return None

def main(argv):
    us_fed_urls = config.us_fed_urls
    download_files(us_fed_urls)

if __name__ == "__main__":
    app.run(main)
