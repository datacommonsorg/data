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
'''
Import script to handle schema/place node files on GCS.
Currently, it only checks the existince of the files on GCS.
'''

from absl import app
from absl import flags
from absl import logging
import os
import sys

# Add the scripts directory to sys.path
script_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'import-automation',
                 'executor', 'scripts'))
sys.path.append(script_dir)
import generate_provisional_nodes

FLAGS = flags.FLAGS
flags.DEFINE_string("entity", "", "Entity type (Schema/Place).")
flags.DEFINE_string("version", "", "Import version.")
flags.DEFINE_string(
    "output_dir", "",
    "Directory to write output files (default: directory containing manifest.json)."
)


def process(entity_type: str, version: str, output_dir: str = ""):
    logging.info(f'Processing import {entity_type} for version {version}')
    local_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), entity_type, version))

    # Default output directory to the folder containing manifest.json (os.path.dirname(__file__))
    if not output_dir:
        output_dir = os.path.abspath(os.path.dirname(__file__))

    # Local path to data
    logging.info(
        f'Generating provisional nodes for {entity_type} in {local_path} (output: {output_dir})'
    )
    generate_provisional_nodes.generate_provisional_nodes(local_path,
                                                          output_dir=output_dir)
    return 0


def main(_):
    """Runs the code."""
    process(FLAGS.entity, FLAGS.version, FLAGS.output_dir)


if __name__ == "__main__":
    app.run(main)
