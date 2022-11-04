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
"""GCS Filesystem helpers."""
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


class File:
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
            raise Exception('gcs.init() must be called to use gcs.File.')
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
