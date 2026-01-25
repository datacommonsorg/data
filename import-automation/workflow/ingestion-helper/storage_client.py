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
"""Storage client for the ingestion helper."""

import logging
from google.cloud import storage
from google.cloud import exceptions
import json
import os

logging.getLogger().setLevel(logging.INFO)

_STAGING_VERSION_FILE = 'staging_version.txt'
_LATEST_VERSION_FILE = 'latest_version.txt'
_IMPORT_METADATA_MCF = 'import_metadata_mcf.mcf'
_IMPORT_SUMMARY_JSON = 'import_summary.json'


class StorageClient:

    def __init__(self, bucket_name: str):
        """Initializes a GCS client."""
        self.storage = storage.Client()
        self.bucket = self.storage.bucket(bucket_name)

    def get_import_summary(self, import_name: str, version: str) -> dict:
        """Retrieves the import summary from GCS.

        Args:
            import_name: The name of the import.
            version: The version of the import.            

        Returns:
            A dictionary containing the import summary, or an empty dict if not found.
        """
        output_dir = import_name.replace(':', '/')
        summary_file = os.path.join(output_dir, version, _IMPORT_SUMMARY_JSON)
        logging.info(f'Reading import summary from {summary_file}')
        try:
            blob = self.bucket.blob(summary_file)
            json_data_string = blob.download_as_text()
            data = json.loads(json_data_string)
            logging.info(f"Successfully read {summary_file}")
            return data
        except (exceptions.NotFound, json.JSONDecodeError) as e:
            logging.error(
                f'Error reading import summary file {summary_file}: {e}')
            return {}

    def get_staging_version(self, import_name: str) -> str:
        """Retrieves the latest version from the staging directory.

        Args:
            import_name: The name of the import.

        Returns:
            The version string, or an empty string if not found.
        """
        output_dir = import_name.replace(':', '/')
        version_file = os.path.join(output_dir, _STAGING_VERSION_FILE)
        logging.info(f'Reading version file {version_file}')
        try:
            blob = self.bucket.blob(version_file)
            return blob.download_as_text()
        except exceptions.NotFound:
            logging.error(f"Version file {version_file} not found")
            return ''

    def update_staging_version(self, import_name: str, version: str):
        """Updates the staging version file in GCS.

        Args:
            import_name: The name of the import.
            version: The new version string.
        """
        try:
            logging.info(
                f'Updating staging version file for import {import_name} to {version}'
            )
            output_dir = import_name.replace(':', '/')
            version_file = self.bucket.blob(
                os.path.join(output_dir, _STAGING_VERSION_FILE))
            version_file.upload_from_string(version)
            logging.info(
                f'Updated staging version file {version_file} to {version}')
        except exceptions.NotFound as e:
            logging.error(f'Error updating version file for {import_name}: {e}')
            raise

    def update_version_file(self, import_name: str, version: str):
        """Updates the version file in GCS.

        Copies the latest version file and import metadata from staging to the
        output directory.

        Args:
            import_name: The name of the import.
            version: The new version string.
        """
        try:
            logging.info(
                f'Updating version history file for import {import_name} to add {version}'
            )
            output_dir = import_name.replace(':', '/')
            version_file = self.bucket.blob(
                os.path.join(output_dir, _LATEST_VERSION_FILE))
            metadata_blob = self.bucket.blob(
                os.path.join(output_dir, version, _IMPORT_METADATA_MCF))
            if metadata_blob.exists():
                self.bucket.copy_blob(
                    metadata_blob, self.bucket,
                    os.path.join(output_dir, 'import_metadata_mcf.mcf'))
            else:
                logging.error(
                    f'Metadata file not found for import {import_name} {version}'
                )
            version_file.upload_from_string(version)
            logging.info(f'Updated version history file {version_file}')
        except exceptions.NotFound as e:
            logging.error(f'Error updating version file for {import_name}: {e}')
            raise
