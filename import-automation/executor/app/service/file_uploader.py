# Copyright 2020 Google LLC
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
"""
File uploaders for uploading generated data files.
"""

import os
import shutil

from google.cloud import storage


class FileUploader:
    """Base class for all file uploaders."""

    def upload_file(self, src: str, dest: str) -> None:
        """Uploads the file at src to a file at dest."""
        raise NotImplementedError

    def upload_string(self, string: str, dest: str) -> None:
        """Uploads the string to a file at dest."""
        raise NotImplementedError


class GCSFileUploader(FileUploader):
    """Class for uploading files to a Google Storage Bucket.

    Attributes:
        bucket: google.cloud.storage.Bucket object for the bucket files are
            uploaded to.
        path_prefix: Path prefix in the bucket as a string.
    """

    def __init__(self,
                 project_id: str,
                 bucket_name: str,
                 path_prefix: str = ''):
        """Constructs a GCSFileUploader.

        Args:
            project_id: ID of the Google Cloud project that hosts the bucket,
                as a string.
            bucket_name: Name of the Cloud Storage Bucket to upload files to,
                as a string.
            path_prefix: Path prefix in the bucket as a string.

        Raises:
            ValueError: project_id or bucket_name is None, empty, or all spaces.
        """
        _strings_not_empty(project_id, bucket_name)
        self.bucket = storage.Client(project=project_id).bucket(bucket_name)
        self.path_prefix = path_prefix

    def upload_file(self, src: str, dest: str) -> None:
        """Uploads a file to the bucket.

        Args:
            src: Path to the file to upload, as a string.
            dest: Relative destination in the bucket as a string. The actual
                destination would be {self.path_prefix}/{dest}.

        Raises:
            ValueError: src or dest is None, empty, or all spaces.
        """
        _strings_not_empty(src, dest)
        blob = self.bucket.blob(self._fix_path(dest))
        blob.upload_from_filename(src)

    def upload_string(self, string: str, dest: str) -> None:
        """Uploads a string to a file in the bucket, overwriting it.

        Args:
            string: The string to upload.
            dest: Relative destination in the bucket as a string. The actual
                destination would be {self.path_prefix}/{dest}.

        Raises:
            ValueError: dest is None, empty, or all spaces.
        """
        _strings_not_empty(dest)
        blob = self.bucket.blob(self._fix_path(dest))
        blob.upload_from_string(string)

    def _fix_path(self, path):
        """Returns {self.path_prefix}/{path}."""
        return os.path.join(self.path_prefix, path)


class LocalFileUploader(FileUploader):
    """Class for copying files to a different location in the local filesystem.

    Attributes:
        output_dir: Path to the directory files are copied to. E.g.,
            LocalFileUploader('/tmp').upload_file('/foo/file', 'bar/file') will
            copy '/foo/file' to '/tmp/bar/file'.
    """

    def __init__(self, output_dir: str = ''):
        self.output_dir = os.path.abspath(output_dir)

    def upload_file(self, src: str, dest: str) -> None:
        """Copies the file at src to a file at <output_dir>/<dest>.

        Raises:
            Same exceptions as shutil.copyfile.
            ValueError: src or dest is None, empty, or all spaces.
        """
        _strings_not_empty(src, dest)
        dest = os.path.join(self.output_dir, dest)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(src, dest)

    def upload_string(self, string: str, dest: str) -> None:
        """Writes a string into a file at <output_dir>/<dest>, overwriting any
        existing files.

        Raises:
            Same exceptions as open and write.
            ValueError: dest is None, empty, or all spaces.
        """
        _strings_not_empty(dest)
        dest = os.path.join(self.output_dir, dest)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'w+') as out:
            out.write(string)


def _strings_not_empty(*args: str):
    """Ensures that the strings are not None, empty, or all spaces.

    Raises:
        ValueError: The string is None, empty, or all spaces.
    """
    for string in args:
        if not string or string.isspace():
            raise ValueError(f'{string} is None, empty, or all spaces')
