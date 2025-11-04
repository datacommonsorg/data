# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Script to download and convert sustainability financial incentives data from GCS."""

import hashlib
import json
import os
import sys
from datetime import datetime
from typing import Optional

from absl import app
from absl import flags
from absl import logging
from google.cloud import storage

# Add tools/statvar_importer to Python path for direct import
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(
    os.path.join(_SCRIPT_DIR, '..', '..', 'tools', 'statvar_importer'))

from json_to_csv import file_json_to_csv

FLAGS = flags.FLAGS

flags.DEFINE_string('gcs_bucket', 'datacommons_public',
                    'GCS bucket name containing the data')
flags.DEFINE_string('gcs_base_path',
                    'source_csv/sustainability_financial_incentives',
                    'Base path in GCS bucket')
flags.DEFINE_string('input_files', 'input_files',
                    'Local directory to store downloaded files')
flags.DEFINE_string('output_csv', 'financial_incentives_data.csv',
                    'Output CSV file name')
flags.DEFINE_string('json_filename', 'financial_incentives_prod_data.json',
                    'JSON file name to download')


def find_latest_dated_folder(bucket_name: str, base_path: str) -> Optional[str]:
    """Find the most recent dated folder in the GCS bucket.
    
    Args:
        bucket_name: Name of the GCS bucket
        base_path: Base path to search for dated folders
        
    Returns:
        The name of the most recent dated folder (e.g., '2025_06_30'), or None if not found
    """
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # List all blobs with the base path prefix
        blobs = bucket.list_blobs(prefix=f"{base_path}/")

        # Extract folder names that match the date pattern YYYY_MM_DD
        dated_folders = set()
        for blob in blobs:
            # Remove base path and get the first part (folder name)
            relative_path = blob.name[len(base_path):].lstrip('/')
            if relative_path:
                folder_name = relative_path.split('/')[0]
                # Check if folder name matches YYYY_MM_DD pattern
                if len(folder_name) == 10 and folder_name.count('_') == 2:
                    try:
                        # Validate date format
                        datetime.strptime(folder_name, '%Y_%m_%d')
                        dated_folders.add(folder_name)
                    except ValueError:
                        continue

        if not dated_folders:
            logging.error(
                f"No dated folders found in {bucket_name}/{base_path}")
            return None

        # Sort and return the most recent folder
        latest_folder = sorted(dated_folders, reverse=True)[0]
        logging.info(f"Found latest dated folder: {latest_folder}")
        return latest_folder

    except Exception as e:
        logging.error(f"Error finding latest dated folder: {e}")
        return None


def download_json_file(bucket_name: str, gcs_path: str,
                       local_path: str) -> bool:
    """Download JSON file from GCS to local path.
    
    Args:
        bucket_name: Name of the GCS bucket
        gcs_path: Full path to the file in GCS
        local_path: Local file path to save the downloaded file
        
    Returns:
        True if download successful, False otherwise
    """
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)

        # Create local directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Download the file
        blob.download_to_filename(local_path)
        logging.info(f"Downloaded {gcs_path} to {os.path.abspath(local_path)}")
        return True

    except Exception as e:
        logging.error(
            f"Error downloading file from {gcs_path} to {os.path.abspath(local_path)}: {e}"
        )
        return False


def convert_json_to_csv(json_path: str, csv_path: str) -> bool:
    """Convert JSON file to CSV using the existing json_to_csv.py tool.
    
    This function extracts the incentiveSummaries array from the JSON file,
    creates a temporary JSON file with just the array data, and processes it
    with the existing CSV conversion utility.
    
    Args:
        json_path: Path to the input JSON file
        csv_path: Path for the output CSV file
        
    Returns:
        True if conversion successful, False otherwise
    """
    try:
        logging.info(
            f"Starting JSON to CSV conversion from {os.path.abspath(json_path)}"
        )

        # Load the original JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate that incentiveSummaries exists and is a non-empty list
        if 'incentiveSummaries' not in data:
            logging.error(
                f"Key 'incentiveSummaries' not found in JSON file: {os.path.abspath(json_path)}"
            )
            return False

        incentive_summaries = data['incentiveSummaries']

        if not isinstance(incentive_summaries, list):
            logging.error(
                f"'incentiveSummaries' is not a list but {type(incentive_summaries).__name__} in: {os.path.abspath(json_path)}"
            )
            return False

        if len(incentive_summaries) == 0:
            logging.error(
                f"'incentiveSummaries' list is empty in: {os.path.abspath(json_path)}"
            )
            return False

        logging.info(
            f"Found {len(incentive_summaries)} incentive summaries in JSON file"
        )

        for summary in incentive_summaries:
            extraction_config = summary.get('extractionConfig')
            if not isinstance(extraction_config, dict):
                continue
            url = extraction_config.get('url')
            if not isinstance(url, str):
                continue
            # Use BLAKE2s with 8-byte digest for a stable, shorter hash.
            # Increase digest_size here if future collisions are observed.
            hash_value = hashlib.blake2s(url.encode('utf-8'),
                                         digest_size=8).hexdigest()
            extraction_config['url_stable_hash'] = hash_value

        # Create temporary JSON file in same directory as original
        json_dir = os.path.dirname(json_path)
        json_basename = os.path.splitext(os.path.basename(json_path))[0]
        temp_json_path = os.path.join(json_dir, f"{json_basename}_temp.json")

        logging.info(
            f"Creating temporary JSON file: {os.path.abspath(temp_json_path)}")

        # Write the incentiveSummaries array to temporary file
        with open(temp_json_path, 'w', encoding='utf-8') as f:
            json.dump(incentive_summaries, f, indent=2, ensure_ascii=False)

        logging.info(
            f"Successfully created temporary JSON file with {len(incentive_summaries)} records"
        )

        # Use existing function to convert temporary JSON to CSV
        file_json_to_csv(temp_json_path, csv_path, set_key_column=False)

        logging.info(
            f"Successfully converted {os.path.abspath(temp_json_path)} to {os.path.abspath(csv_path)}"
        )
        logging.info(
            f"Temporary JSON file preserved at: {os.path.abspath(temp_json_path)}"
        )

        return True

    except Exception as e:
        logging.error(
            f"Error converting JSON to CSV from {os.path.abspath(json_path)} to {os.path.abspath(csv_path)}: {e}"
        )
        return False


def main(argv):
    """Main function to download and convert financial incentives data."""
    del argv  # Unused

    # Find the latest dated folder
    latest_folder = find_latest_dated_folder(FLAGS.gcs_bucket,
                                             FLAGS.gcs_base_path)
    if not latest_folder:
        logging.fatal("Failed to find latest dated folder")

    # Construct GCS path and local path
    gcs_file_path = f"{FLAGS.gcs_base_path}/{latest_folder}/{FLAGS.json_filename}"
    local_json_path = os.path.join(FLAGS.input_files, FLAGS.json_filename)

    # Download the JSON file
    if not download_json_file(FLAGS.gcs_bucket, gcs_file_path, local_json_path):
        logging.fatal(
            f"Failed to download JSON file from {gcs_file_path} to {os.path.abspath(local_json_path)}"
        )

    # Convert JSON to CSV
    csv_output_path = os.path.join(FLAGS.input_files, FLAGS.output_csv)
    if not convert_json_to_csv(local_json_path, csv_output_path):
        logging.fatal(
            f"Failed to convert JSON to CSV from {os.path.abspath(local_json_path)} to {os.path.abspath(csv_output_path)}"
        )

    logging.info(f"Successfully processed data from {latest_folder}")
    logging.info(f"Output CSV file: {os.path.abspath(csv_output_path)}")
    return 0


if __name__ == '__main__':
    app.run(main)
