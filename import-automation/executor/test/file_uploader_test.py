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
import tempfile
import unittest
from unittest import mock

from app.service import file_uploader
from test import utils
from test import integration_test


class GCSFileUploaderTest(unittest.TestCase):

    @mock.patch('google.cloud.storage.Client')
    def setUp(self, _):
        self.io = file_uploader.GCSFileUploader(project_id='project-id',
                                                bucket_name='bucket-name')

    def test_upload_file(self):
        src = 'a/b/c/file.csv'
        dest = 'd/e/file.csv'
        self.io.upload_file(src, dest)
        self.io.bucket.blob.assert_has_calls(
            [mock.call(dest),
             mock.call().upload_from_filename(src)])

    def test_upload_string(self):
        version = '2020-1-20 123:20'
        dest = 'foo/bar/latest_version.txt'
        self.io.upload_string(version, dest)
        self.io.bucket.blob.assert_has_calls(
            [mock.call(dest),
             mock.call().upload_from_string(version)])

    def test_invalid_string_args(self):
        self.assertRaises(ValueError, file_uploader.GCSFileUploader, 'project',
                          '')
        self.assertRaises(ValueError, file_uploader.GCSFileUploader, '   ',
                          'bucket')
        self.assertRaises(ValueError, self.io.upload_file, 'src', '')
        self.assertRaises(ValueError, self.io.upload_file, '   ', 'dest')
        self.assertRaises(ValueError, self.io.upload_string, 'string', '')


class LocalFileUploaderTest(unittest.TestCase):

    def test_upload_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            uploader = file_uploader.LocalFileUploader(tmp_dir)
            src = os.path.join(
                os.getcwd(),
                'import-automation/executor/test/data/COVIDTracking_States.csv')
            uploader.upload_file(src, 'foo/bar/data.csv')
            self.assertTrue(
                utils.compare_lines(src,
                                    os.path.join(tmp_dir, 'foo/bar/data.csv'),
                                    integration_test.NUM_LINES_TO_CHECK))

    def test_upload_string(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            uploader = file_uploader.LocalFileUploader(tmp_dir)
            uploader.upload_string('12345', 'foo/bar/file')
            with open(os.path.join(tmp_dir, 'foo/bar/file')) as file:
                self.assertEqual('12345', file.read())

    def test_invalid_string_args(self):
        uploader = file_uploader.LocalFileUploader()
        self.assertRaises(ValueError, uploader.upload_file, 'src', '')
        self.assertRaises(ValueError, uploader.upload_file, '   ', 'dest')
        self.assertRaises(ValueError, uploader.upload_string, 'string', '')
