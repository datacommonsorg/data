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

import os, sys
from absl import app, logging
from pathlib import Path
import config

script_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(script_dir, '../../../util'))

from download_util_script import download_file

Commerce_NTIA_URL = config.Commerce_NTIA_URL

INPUT_DIR = os.path.join(script_dir, "input_files")
Path(INPUT_DIR).mkdir(parents=True, exist_ok=True)

def main(argv):
    try:
        download_file(url=Commerce_NTIA_URL,
                  output_folder=INPUT_DIR,
                  unzip=False,
                  headers= None,
                  tries= 3,
                  delay= 5,
                  backoff= 2)
    except Exception as e:
        logging.fatal(f"Failed to download Commerce_NTIA file: {e}")


if __name__ == "__main__":
    app.run(main)
