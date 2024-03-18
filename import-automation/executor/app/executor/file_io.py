# Copyright 2024 Google LLC
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
"""Utilities to read/write files on GCS"""

from typing import Union
from absl import app
from absl import logging
from google.cloud import storage


def file_is_gcs(filename: str) -> bool:
    """Returns true if the file is a GCS file starting with gs://."""
    if filename:
        return filename.startswith('gs://')
    return False


# Global Google Storage Client for GCS file operations.
_GCS_CLIENT = None


def file_get_gcs_bucket(filename: str) -> storage.bucket.Bucket:
    """Return the GCS bucket for the file path.

  Assumes the project is default or set in env variable: GOOGLE_CLOUD_PROJECT.

  Args:
      filename: string filename that begins with 'gs://'

  Returns:
    GCS bucket for the file.
  """
    if file_is_gcs(filename):
        gcs_path_without_scheme = filename[len('gs://'):]
        bucket_name, filepath = gcs_path_without_scheme.split('/', 1)
        if bucket_name and filepath:
            global _GCS_CLIENT
            if not _GCS_CLIENT:
                _GCS_CLIENT = storage.Client()
            bucket = _GCS_CLIENT.get_bucket(bucket_name)
            return bucket
    return None


def file_get_gcs_blob(filename: str, exists: bool = True) -> storage.blob.Blob:
    """Returns the GCS blob for the GCS file.

  Args:
    filename: string with GCS filename.
    exists: boolean set to True if filename should be looked up. Can be False
      for write operations.

  Returns:
    GCS blob for the file.
  """
    if file_is_gcs(filename):
        bucket_name, filepath = filename[len('gs://'):].split('/', 1)
        bucket = file_get_gcs_bucket(filename)
        if bucket:
            if exists:
                return bucket.get_blob(filepath)
            else:
                return bucket.blob(filepath)
        else:
            logging.debug(f'Failed to get bucket: {bucket_name}/{filepath}')
    return None


def file_open(filename: str, mode: str = 'r'):
    """Return the file handle for read() or write() operations.

  Args:
    filename: file to be opened.

  Returns:
    file handle
  """
    if file_is_gcs(filename):
        # Get the GCS blob handle.
        if mode.startswith('r'):
            logging.debug(f'Opening GCS file {filename} for read.')
            blob = file_get_gcs_blob(filename, exists=True)
            return storage.fileio.BlobReader(blob)
        else:
            logging.debug(f'Opening GCS file {filename} for write.')
            blob = file_get_gcs_blob(filename, exists=False)
            return storage.fileio.BlobWriter(blob)
    # Open a local file directly for given mode.
    return open(filename, mode=mode)


def file_copy(src_filename: str, dst_filename: str) -> str:
    """Copies over the src_file into the dst_file and returns the filename.

  Supports both local files, GCS files and spreadsheets.

  Args:
    src_filename: string filename of file to be copied
    dst_filename: string filename of file to be copied into

  Returns:
    the destination file into which source file content was copied into.
  """

    # Get source file handle to read from
    src_fh = None
    with file_open(src_filename, mode='rb') as src_file:
        with file_open(dst_filename, mode='wb') as dst_file:
            _copy_file_chunks(src_file, dst_file)
    return dst_filename


def _copy_file_chunks(src, dst, chunk_size=1000000):
    """Copy file content from src to dst in chunks of given size."""
    buf = src.read(chunk_size)
    while len(buf):
        dst.write(buf)
        buf = src.read(chunk_size)
