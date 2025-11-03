# Copyright 2025 Google LLC
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
"""Utilities for statvar imports"""

import os
import sys
import glob
import json
from typing import Union

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_SCRIPT_DIR.split('/data/')[0], 'data')
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(_DATA_DIR, 'util')

import file_util
from config_map import ConfigMap

# Utilities to get import related files.


def load_manifest_json(file: str) -> dict:
  """Parses a manifest.json file into a dict object."""
  try:
    with open(file, 'r') as fp:
      manifest_json = json.loads(fp.read())
      return manifest_json
  except e:
    logging.error(f'Unable to load manifest {file}, error: {e}')
    return {}


# Get the manifest.josn file for an import
def get_import_manifest(import_name: str, root_dir: str = _DATA_DIR) -> str:
  """Returns the folder containing the manifest.json for the import name."""
  files = glob.glob(os.path.join(root_dir, '**'), recurive=True)
  for file in files:
    if file.endswith('manifest.json'):
      # Check if the manifets.json is for this import.
      import_manifest = load_manifest_json(file)
      if import_manifest:
        return file


