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

BUCKET_NAME = 'datcom-prod-imports'
FILE_NAME = 'staging_version.txt'


def process(entity_type: str):
    # Ensure the import data is available in GCS.
    current_date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    logging.info(f'Checking import {entity_type} for date {current_date}')
    file_path = os.path.join('scripts', os.path.basename(os.getcwd()),
                             entity_type, FILE_NAME)
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_path)
    version = blob.download_as_text()
    if version == current_date:
        logging.info(
            f'Successfully validated import {entity_type} for date {current_date}'
        )
        return 0
    else:
        raise RuntimeError(
            f'{entity_type} data not present in GCS bucket {BUCKET_NAME} for date {current_date}'
        )


def main(_):
    """Runs the code."""
    process(FLAGS.entity)


if __name__ == "__main__":
    app.run(main)
