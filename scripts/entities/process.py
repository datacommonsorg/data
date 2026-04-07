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
import datetime
from google.cloud import storage
import os

FLAGS = flags.FLAGS
flags.DEFINE_string("entity", "Schema", "Entity type (Schema/Place).")
flags.DEFINE_string("version", "", "Import version.")


def process(entity_type: str, version: str):
    logging.info(f'Processing import {entity_type} for version {version}')
    # TODO: add processing logic


def main(_):
    """Runs the code."""
    process(FLAGS.entity, FLAGS.version)


if __name__ == "__main__":
    app.run(main)
