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

import unittest
from unittest import mock

from google.cloud import storage

from app.service import file_uploader


class GCSFileUploaderTest(unittest.TestCase):

    @mock.patch('google.cloud.storage.Client')
    def setUp(self, _):
        self.io = file_uploader.GCSFileUploader(
            project_id='project-id',
            bucket_name='bucket-name')

    def test_upload_file(self):
        src = 'a/b/c/file.csv'
        dest = 'd/e/file.csv'
        self.io.upload_file(src, dest)
        self.io.bucket.blob.assert_has_calls([
            mock.call(dest),
            mock.call().upload_from_filename(src)
        ])

    def test_upload_string(self):
        version = '2020-1-20 123:20'
        dest = 'foo/bar/latest_version.txt'
        self.io.upload_string(version, dest)
        self.io.bucket.blob.assert_has_calls([
            mock.call(dest),
            mock.call().upload_from_string(version)
        ])


class LocalFileUploaderTest(unittest.TestCase):
    # TODO
    pass
