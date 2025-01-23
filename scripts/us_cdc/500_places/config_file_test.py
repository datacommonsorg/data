# Copyright 2021 Google LLC
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
import json
import sys
from google.cloud import storage
from retry import retry
from absl import app

CONFIG_GCP_PATH = 'gs://unresolved_mcf/cdc/cdc500places/download_config.json'

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_MODULE_DIR, '../../../util/'))
import file_util

LOCAL_CONFIG_FILE = os.path.join(_MODULE_DIR, 'download_config.json')
print(f"LOCAL_CONFIG_FILE: {LOCAL_CONFIG_FILE}")


# Function to load the local config file
def load_local_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


# Function to load the GCP config file
def load_gcp_config(gcp_path):
    with file_util.FileIO(gcp_path, 'r') as f:
        CONFIG_FILE = json.load(f)
    return CONFIG_FILE


# Compare the content of both files
def compare_configs(local_config_file, gcp_config_path):
    local_config = load_local_config(local_config_file)
    gcp_config = load_gcp_config(gcp_config_path)

    if local_config != gcp_config:
        raise ValueError(
            f"ERROR: The config files are different! Local file: {local_config_file}, GCP file: {gcp_config_path}"
        )
    else:
        print("===The config files are identical.===")


def main(_):
    compare_configs(LOCAL_CONFIG_FILE, CONFIG_GCP_PATH)


if __name__ == "__main__":
    app.run(main)
