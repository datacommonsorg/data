# Copyright 2022 Google LLC
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
"""Module for helper functions to read from / write to GCS.

For what is GCS, see https://cloud.google.com/storage for more on GCS.

###############################################################################
Description
###############################################################################
This module wraps gcs python library's fileio module. The fileio module
provides file like methods for interacting with GCS blobs.

Please use this module to interact with GCS.

###############################################################################
Assumptions
###############################################################################
- GCS bucket is assumed to exist.

- Caller is assumed to have object reader/write permission to read/write.

- All path consumed needs to start with "gs://"

###############################################################################
Usage
###############################################################################
- gcs_file.init() must be called in the main program, this does not have
to be in the same file from where read/write is done.

- See example usage below for how to read/write.

Note: Only read and write mode is currently supported.

###############################################################################
Example usage
###############################################################################

from util import gcs_file
...

gcs_file.init()
...

# To read a GCS blob to a string.
with gcs_file.GcsFile("gs://some-bucket/some-path, 'r') as file:
    text_string = file.read().decode()

# To write a string into a GCS blob.
with gcs_file.GcsFile("gs://some-bucket/some-other-path, 'w') as file:
    file.write("abc".encode())
"""
from google.cloud import storage


class InvalidSchemeError(Exception):
    """GCS scheme is 'gs://'."""


class BlobNotFoundError(Exception):
    """Thrown when a blob doesn't exist."""


_CLIENT = None


def init():
    """Callers of GCSFile operations must call init() before any operations.

    Uses default GCP credentials to authenticate.
    """
    global _CLIENT
    if not _CLIENT:
        _CLIENT = storage.Client()


class GcsFile:
    """GCS context manager for reading and writing to gcs like local files.

    Returns a gcs library blob reader/writer within the context.
    Note that blobs in gcs do not support append mode.
    """

    def __init__(self, gcs_path: str, mode: str = 'r'):
        if not gcs_path.startswith('gs://'):
            raise InvalidSchemeError('Expected "gs://"-prefix, got  %s' %
                                     gcs_path)
        gcs_path_without_scheme = gcs_path[len('gs://'):]
        self.bucket, self.path = gcs_path_without_scheme.split('/', 1)
        self.mode = mode
        self.reader_writer = None

    def __enter__(self):
        if not _CLIENT:
            raise Exception('gcs.init() must be called to use GcsFile.')
        bucket = _CLIENT.get_bucket(self.bucket)
        blob = bucket.blob(self.path)

        if self.mode == 'r':
            if not blob.exists():
                raise BlobNotFoundError()
            self.reader_writer = storage.fileio.BlobReader(blob)
        else:
            # write mode
            self.reader_writer = storage.fileio.BlobWriter(blob)
        return self.reader_writer

    def __exit__(self, exc_type, exc_value, tb):
        self.reader_writer.close()
