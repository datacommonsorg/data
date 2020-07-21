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

import os
import shutil

from google.cloud import storage

from app import configs


class FileUploader:
    def upload_file(self, src: str, dest: str) -> None:
        raise NotImplementedError

    def upload_string(self, string: str, dest: str) -> None:
        raise NotImplementedError


class GCSFileUploader(FileUploader):
    def __init__(self, project_id, bucket_name):
        self.bucket = storage.Client(project=project_id).bucket(bucket_name)

    def upload_file(self, src: str, dest: str) -> None:
        """Uploads a file to the bucket.

        Args:
            src: Path to the file to upload, as a string.
            dest: Destination in the bucket as a string. This will be prefixed
                by the prefix attribute.
        """
        blob = self.bucket.blob(dest)
        blob.upload_from_filename(src)

    def upload_string(self, string: str, dest: str) -> None:
        """Uploads a string to a file, overwriting it.

        Args:
            string: The string to upload.
            dest: Destination in the bucket as a string.
        """
        blob = self.bucket.blob(dest)
        blob.upload_from_string(string)


class LocalFileUploader(FileUploader):
    def __init__(self, output_dir=''):
        self.output_dir = os.path.abspath(output_dir)

    def upload_file(self, src: str, dest: str) -> None:
        dest = os.path.join(self.output_dir, dest)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(src, dest)

    def upload_string(self, string: str, dest: str) -> None:
        with open(dest, 'w+') as out:
            out.write(string)
