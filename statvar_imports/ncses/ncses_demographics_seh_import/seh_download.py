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

import os
from absl import app, logging, flags
import sys
from google.cloud import storage

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, '../../../util'))
INPUT_DIR = os.path.join(SCRIPT_DIR, "input_files")

from download_util_script import download_file

flags.DEFINE_string(
    'config_file_path',
    'gs://unresolved_mcf/country/ncses/ncses_demographics_seh/latest/configs.py',
    'Config file path')

def reads_config_file():
    _FLAGS = flags.FLAGS
    config_file_path = _FLAGS.config_file_path
    try:
        storage_client = storage.Client()
        bucket_name = config_file_path.split('/')[2]
        bucket = storage_client.bucket(bucket_name)
        blob_name = '/'.join(config_file_path.split('/')[3:])
        blob = bucket.blob(blob_name)
        file_contents = blob.download_as_text()
        local_vars = {}
        exec(file_contents, {}, local_vars)
        return local_vars
    except Exception as e:
        logging.fatal(f"Cannot extract url and related configs: {e}")

def download_files(URL_CONFIGS):
    try:
        for config_url in URL_CONFIGS:
            download_file(url=config_url,
                  output_folder=INPUT_DIR,
                  unzip=False,
                  headers= None,
                  tries= 3,
                  delay= 5,
                  backoff= 2)
            
    except Exception as e:
        logging.fatal(f"Download error: {str(e)}")


def main(_):
    configs = reads_config_file()
    SEH_URL = configs['URLS_CONFIG']
    download_files(SEH_URL)
    logging.info("Download process Completed successfully")


if __name__ == "__main__":  
    app.run(main)