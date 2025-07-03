# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 20 ('License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#           https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# How to run the script to copy the files:
# python3 download_util_script.py --download_url="<url>" --unzip=<True if files have to be unzipped.>
#python3 copy_script.py --source="local folder path" --target="GCS Bucket path"      copy the files from local to gcs
#python3 copy_script.py --source="gcs folder path" --target="local folder path" copy the files from gcs to local
#python3 copy_script.py --source="gcs folder path" --target="gcs folder path" copy the files from gcs to gcs
#python3 copy_script.py --source="local folder path" --target="local folder path" copy the files from local to local

import os
import shutil
from pathlib import Path
from typing import Union
from google.cloud import storage
from absl import flags
from absl import app
from absl import logging

FLAGS = flags.FLAGS
flags.DEFINE_string('source', None, 'The source path for the files')
flags.DEFINE_string('target', None, 'The target path for the files')

def _is_gcs_path(path_str):
    return path_str.startswith("gs://")

def common_copy_files(source_path_str, target_path_str):
    """
    Copies files from a source path to a target path, supporting all combinations of
    local file system and Google Cloud Storage (GCS) locations.

    Args:
        source_path_str (str): The source path(local or GCS PATH).
        target_path_str (str): The target path (local or GCS PATH).
    """
    is_source_gcs = _is_gcs_path(source_path_str)
    is_target_gcs = _is_gcs_path(target_path_str)
    gcs_client = storage.Client()
    copied_count = 0
    skipped_count = 0
    error_count = 0
    try:
        if not is_source_gcs:
            source_local_path = Path(source_path_str)
            if not source_local_path.is_dir():
                raise FileNotFoundError(f"Source folder '{source_local_path}' does not exist or is not a directory.")
            logging.info(f"Local source folder: '{source_local_path}'")
        else:
            # gcs bucket logic to fetch the bucket_name and folder name
            if not source_path_str.startswith("gs://"):
                raise ValueError(f"Invalid GCS path for source: '{source_path_str}'. must start with 'gs://'.")
            src_uri_without_scheme = source_path_str[len("gs://"):]
            src_parts = src_uri_without_scheme.split('/', 1)
            src_bucket_name = src_parts[0]
            src_gcs_prefix = src_parts[1] if len(src_parts) > 1 else ""
            if src_gcs_prefix and not src_gcs_prefix.endswith('/'):
                src_gcs_prefix += '/'

            try:
            
                source_bucket = gcs_client.bucket(src_bucket_name)
                source_bucket.exists()
            except Exception as e:
                raise RuntimeError(f"Unexpected error initializing source bucket '{src_bucket_name}': {e}") from e
            logging.info(f"GCS source bucket: '{src_bucket_name}', prefix: '{src_gcs_prefix}'")

        if not is_target_gcs:
            target_local_path = Path(target_path_str)
            try:
                target_local_path.mkdir(parents=True, exist_ok=True)
                logging.info(f"Local target folder '{target_local_path}' ensured to exist.")
            except OSError as e:
                raise IOError(f"Error creating local target folder '{target_local_path}': {e}") from e
        else:
            # gcs path logic to chech that path is valid and fetched the bucket name and folder name
            if not target_path_str.startswith("gs://"):
                raise ValueError(f"Invalid GCS URI for target: '{target_path_str}'. Must start with 'gs://'.")
            dest_uri_without_scheme = target_path_str[len("gs://"):]
            dest_parts = dest_uri_without_scheme.split('/', 1)
            dest_bucket_name = dest_parts[0]
            dest_gcs_prefix = dest_parts[1] if len(dest_parts) > 1 else ""
            if dest_gcs_prefix and not dest_gcs_prefix.endswith('/'):
                dest_gcs_prefix += '/'

            try:
                target_bucket = gcs_client.bucket(dest_bucket_name)
                target_bucket.exists() 
            except Exception as e:
                raise RuntimeError(f"Unexpected error initializing target bucket '{dest_bucket_name}': {e}") from e
            logging.info(f"GCS target bucket: '{dest_bucket_name}', prefix: '{dest_gcs_prefix}'")


        # Iterating the  source items and perform copy operation
        if not is_source_gcs: 
            logging.info(f"Iterating local source '{source_local_path}' (only files directly in this directory will be copied).")
            for item in source_local_path.iterdir():
                if not item.is_file():
                    logging.info(f"  Skipped local non-file item: '{item.name}'")
                    skipped_count += 1
                    continue

                source_item_name = item.name # The base filename from the local source
                try:
                     # Local to Local Copy operation
                    if not is_target_gcs:
                        destination_path = target_local_path / source_item_name
                        shutil.copy2(item, destination_path)
                        logging.info(f"  Copied: '{item.name}' to local '{destination_path}'")
                    # Local to GCS Copy
                    else: 
                        blob_target_name = dest_gcs_prefix + source_item_name
                        blob = target_bucket.blob(blob_target_name)
                        blob.upload_from_filename(item)
                        logging.info(f"  Uploaded: '{item.name}' to GCS object '{blob_target_name}'")
                    copied_count += 1
                except Exception as e:
                    logging.error(f"  Error processing local file '{item.name}': {e}")
                    error_count += 1
        else: # Source is GCS 
            # list of all blobs under the source GCS prefix.
            for blob in source_bucket.list_blobs(prefix=src_gcs_prefix):
                # Skip GCS objects that represent directory markers (ending with '/')
                if blob.name.endswith('/'):
                    if blob.name == src_gcs_prefix and not blob.exists(): # If it's the prefix and not an actual object.
                        # if blob might represent the 'folder' itself and not a file so no operation .
                        pass 
                    else:
                        logging.info(f"  Skipped GCS directory marker: '{blob.name}'")
                        skipped_count += 1
                    continue
                relative_path_in_source = blob.name[len(src_gcs_prefix):]
                #used for gcs to local file transfer and gcs to gcs file transfer
                target_item_name = relative_path_in_source
                try:
                    if not is_target_gcs: # GCS to Local Copy
                        logging.info(target_local_path / target_item_name)
                        local_file_path = target_local_path / target_item_name
                        os.makedirs(local_file_path.parent, exist_ok=True)
                        blob.download_to_filename(local_file_path)
                        logging.info(f"  Downloaded: '{blob.name}' to local '{local_file_path}'")
                    else: # GCS to GCS Copy
                        new_blob_name = dest_gcs_prefix + target_item_name
                        source_bucket.copy_blob(blob, target_bucket, new_name=new_blob_name)
                        logging.info(f"  Copied: '{blob.name}' to '{new_blob_name}'")
                    copied_count += 1
            
                except Exception as e:
                    logging.error(f"  An unexpected error occurred during GCS object '{blob.name}' transfer: {e}")
    except Exception as e:
        logging.fatal(f"\nAn unhandled exception occurred: {e}")
    
    logging.info(f"Successfully copied/uploaded/downloaded: {copied_count}")
    logging.info(f"Total items skipped: {skipped_count}")
    logging.info(f"Copy operation finished.")


def main(argv):
    source_path_str = FLAGS.source
    target_path_str = FLAGS.target
    if not source_path_str or not target_path_str:
        logging.fatal("Error: Both --source and --target flags are required.")
        exit()

    common_copy_files(source_path_str, target_path_str)

if __name__ == '__main__':
    flags.mark_flag_as_required('source')
    flags.mark_flag_as_required('target')
    app.run(main)