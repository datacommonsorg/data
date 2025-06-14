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

import os, requests, config
from absl import logging, app
from retry import retry

@retry(tries=3, delay=5, backoff=2)
def retry_method(url, headers=None):
    response = requests.get(url, headers=headers, timeout=10, stream=True)
    response.raise_for_status()
    return response

def download(urls, inputdir):
    if not os.path.exists(inputdir):
        os.makedirs(inputdir)
        logging.info(f"Created download directory: {inputdir}")
    count = 0

    for url in urls:
        for i in range(13,32):
            try:
                response = retry_method(url.format(i))
                if "40" in url:
                    gender_code = 40
                elif "50" in url:
                    gender_code = 50
                if response.status_code==200:
                    with open(os.path.join(inputdir,f"table_{gender_code}_{count}.xlsx"),"wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                else:
                    logging.warning(f"Skipping download for {url}. Received non-200 status code: {response.status_code}")
                count+=1
            except Exception as e:
                logging.error(f"Error occured while downloading the data: {e}")      
    logging.info("Download process finished.") 

def main(_):
    nces_urls = config.urls
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "input_files")

    try:
        download(nces_urls, input_dir)
    except Exception as e:
        logging.fatal(f"A critical error prevented the download process from  completing: {e}")

if __name__ == "__main__":
   app.run(main)