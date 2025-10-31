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

import os
import sys
import json
import time
from datetime import datetime
from absl import app, logging, flags

# Add the project root to the Python path, so that the util module can be imported.
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))

from download_util_script import download_file

FLAGS = flags.FLAGS

def main(_):
    """
    Downloads data from specified URLs and saves them to the 'input_files' directory.
    """
    logging.set_verbosity(logging.INFO)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_output_folder = os.path.join(script_dir, 'input_files')
    
    # Load configuration from JSON file
    config_path = os.path.join(script_dir, 'import_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Download static URL files
    for url in config.get('static_urls', []):
        download_file(url, base_output_folder, unzip=False, tries=5, delay=10)
        time.sleep(1)  # Pause for 1 second between downloads

    # Download year-based files
    current_year = datetime.now().year
    for yearly_config in config.get('yearly_urls', []):
        output_subfolder = os.path.join(base_output_folder, yearly_config['output_folder'])
        os.makedirs(output_subfolder, exist_ok=True)
        for year in range(yearly_config['start_year'], current_year + 1):
            url = yearly_config['base_url'].format(year=year)
            if not download_file(url, output_subfolder, unzip=False, tries=3, delay=5, backoff=1):
                logging.warning(f"Failed to download data for year {year}. The file may not exist.")
            time.sleep(10)  # Pause for 1 second between downloads

if __name__ == "__main__":
    app.run(main)
