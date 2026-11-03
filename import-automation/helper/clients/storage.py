# Copyright 2026 Google LLC
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
"""Storage client for the import helper."""

from datetime import datetime, timezone
import json
import logging
import os
import config
from google.cloud import exceptions
from google.cloud import storage

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

    def _get_output_dir(self, import_name: str) -> str:
        """Constructs the output directory path."""
        output_dir = import_name.replace(':', '/').strip('/')
        output_prefix = (config.GCS_OUTPUT_PREFIX or '').strip('/')
        if output_prefix and not output_dir.startswith(output_prefix + '/'):
            output_dir = os.path.join(output_prefix, output_dir)
        return output_dir

    def get_import_summary(self, import_name: str, version: str) -> dict:
        """Retrieves the import summary from GCS.

        Args:
            import_name: The name of the import.
            version: The version of the import.

        Returns:
            A dictionary containing the import summary, or an empty dict if not found.
        """
        output_dir = self._get_output_dir(import_name)
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
            raise

    def update_import_summary(self, import_summary: dict, version: str = None):
        """Updates the import summary in GCS.

        Args:
            import_summary: A dictionary containing the summary of the import.
            version: Optional version string.
        """
        import_name = import_summary.get('import_name')
        if not version:
            version = import_summary.get('version')

        if import_name and version:
            output_dir = self._get_output_dir(import_name)
            summary_file = os.path.join(output_dir, version, _IMPORT_SUMMARY_JSON)
        else:
            latest_version = import_summary.get('latest_version') or ''
            graph_path = (import_summary.get('graph_path') or '').lstrip('/')
            base_path = latest_version.rstrip('/')
            if graph_path and base_path.endswith(graph_path.rstrip('/')):
                base_path = base_path[:-len(graph_path.rstrip('/'))].rstrip('/')
            path = base_path.removeprefix('gs://').split('/', 1)
            summary_file = os.path.join(path[1] if len(path) > 1 else path[0], _IMPORT_SUMMARY_JSON)

        logging.info(
            f'Updating import summary at {summary_file} {import_summary}')
        blob = self.bucket.blob(summary_file)
        blob.upload_from_string(json.dumps(import_summary))
        logging.info(f'Updated import summary at {summary_file}')

    def get_import_version(self,
                           import_name: str,
                           is_staging: bool = False) -> str:
        """Retrieves the version from the version file (staging or latest) in GCS.

        Args:
            import_name: The name of the import.
            is_staging: Whether to retrieve the staging version file or the latest version file.

        Returns:
            The version string, or an empty string if not found.
        """
        file_name = _STAGING_VERSION_FILE if is_staging else _LATEST_VERSION_FILE
        file_type = "staging" if is_staging else "latest"
        output_dir = self._get_output_dir(import_name)
        version_file = os.path.join(output_dir, file_name)
        logging.info(f'Reading {file_type} version file {version_file}')
        try:
            blob = self.bucket.blob(version_file)
            return blob.download_as_text().strip()
        except exceptions.NotFound:
            logging.error(
                f"{file_type.capitalize()} version file {version_file} not found")
            raise

    def update_version_file(self,
                            import_name: str,
                            version: str,
                            is_staging: bool = False):
        """Updates the version file (staging or latest) in GCS.

        Args:
            import_name: The name of the import.
            version: The new version string.
            is_staging: Whether to update the staging version file or the latest version file.
        """
        file_name = _STAGING_VERSION_FILE if is_staging else _LATEST_VERSION_FILE
        file_type = "staging" if is_staging else "latest"
        logging.info(
            f'Updating {file_type} version file for import {import_name} to {version}'
        )
        output_dir = self._get_output_dir(import_name)
        version_file = self.bucket.blob(os.path.join(output_dir, file_name))
        version_file.upload_from_string(version)
        logging.info(
            f'Updated {file_type} version file {version_file.name} to {version}'
        )

    def update_provenance_file(self, import_name: str, version: str):
        """Updates the provenance file for the import.

        Args:
            import_name: The name of the import.
            version: The version of the import.
        """
        logging.info(
            f'Updating provenance file for import {import_name} to add {version}'
        )
        output_dir = self._get_output_dir(import_name)
        metadata_blob = self.bucket.blob(
            os.path.join(output_dir, version, 'provenance', 'genmcf',
                         _IMPORT_METADATA_MCF))
        if metadata_blob.exists():
            self.bucket.copy_blob(
                metadata_blob, self.bucket,
                os.path.join(output_dir, 'import_metadata_mcf.mcf'))
        else:
            logging.warning(
                f'Generating default metadata for import {import_name}')
            base_name = import_name.split(':')[-1]
            refresh_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            default_provenance = (
                f"Node: dcid:dc/base/{base_name}\n"
                f"typeOf: dcid:Provenance\n"
                f'lastDataRefreshDate: "{refresh_date}"\n'
            )
            new_blob = self.bucket.blob(
                os.path.join(output_dir, version, 'provenance', 'genmcf',
                             'import_metadata_mcf.mcf'))
            new_blob.upload_from_string(default_provenance)

        logging.info(
            f'Updated provenance file for import {import_name} to add {version}'
        )
