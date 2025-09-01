#!/usr/bin/env python3

# Copyright 2020 Google LLC
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

import json
import sys
from dataclasses import dataclass
from typing import List

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('import_config', None,
                    'Path to import config JSON file (required)')
flags.mark_flag_as_required('import_config')


@dataclass
class ImportConfig:
    input_data: List[str]
    input_metadata: List[str]


def load_import_config(config_path: str) -> ImportConfig:
    """Load import configuration from JSON file."""
    with open(config_path, 'r') as f:
        data = json.load(f)
    return ImportConfig(**data)


def generate_pvmap(config: ImportConfig):
    """Generate PV map from import configuration."""
    # TODO: Implement PV map generation logic
    pass


def main(argv):
    """Main function for PV Map generator."""
    config = load_import_config(FLAGS.import_config)
    print(
        f"Loaded config with {len(config.input_data)} data files and {len(config.input_metadata)} metadata files"
    )
    generate_pvmap(config)
    print("PV Map generation completed.")
    return 0


if __name__ == '__main__':
    app.run(main)
