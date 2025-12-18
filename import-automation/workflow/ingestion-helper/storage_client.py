"""Storage client for the ingestion helper."""

import logging
from google.cloud import storage
from google.cloud import exceptions
import json
import os

logging.getLogger().setLevel(logging.INFO)


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
        summary_file = os.path.join(output_dir, version, 'import_summary.json')
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
        version_file = os.path.join(output_dir, 'staging', 'latest_version.txt')
        logging.info(f'Reading version file {version_file}')
        try:
            blob = self.bucket.blob(version_file)
            return blob.download_as_text()
        except exceptions.NotFound:
            logging.error(f"Version file {version_file} not found")
            return ''

    def update_version_file(self, import_name: str, version: str):
        """Updates the version file and history in GCS.

        Copies the latest version file and import metadata from staging to the
        output directory and appends the new version to the history file.

        Args:
            import_name: The name of the import.
            version: The new version string.
        """
        output_dir = import_name.replace(':', '/')
        version_file = self.bucket.blob(
            os.path.join(output_dir, 'latest_version.txt'))
        version_file.upload_from_string(version)
        self.bucket.copy_blob(
            self.bucket.blob(
                os.path.join(output_dir, version, 'import_metadata_mcf.mcf')),
            self.bucket, os.path.join(output_dir, 'import_metadata_mcf.mcf'))

        history_filename = os.path.join(output_dir,
                                        'latest_version_history.txt')
        logging.info(f'Updating version history file {history_filename}')
        versions_history = [version]
        history_blob = self.bucket.blob(history_filename)
        if history_blob.exists():
            history = history_blob.download_as_text()
            if history:
                versions_history.append(history)
        history_blob.upload_from_string('\n'.join(versions_history))
        logging.info(f'Updated version history file {history_filename}')
