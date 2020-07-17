import unittest
from unittest import mock

from google.cloud import storage

from app.service import gcs_io


class GCSBucketIOTest(unittest.TestCase):

    @mock.patch('google.cloud.storage.Bucket', spec=storage.Bucket)
    def setUp(self, bucket):
        self.io = gcs_io.GCSBucketIO(
            path_prefix='some/random/prefix', bucket=bucket, client='not-none')

    def test_upload_file(self):
        src = 'a/b/c/file.csv'
        self.io.upload_file(src, 'd/e/file.csv')
        self.io.bucket.blob.assert_has_calls([
            mock.call('some/random/prefix/d/e/file.csv'),
            mock.call().upload_from_filename(src)
        ])

    def test_update_version(self):
        version = '2020-1-20 123:20'
        self.io.update_version(version)
        self.io.bucket.blob.assert_has_calls([
            mock.call('some/random/prefix/latest_version.txt'),
            mock.call().upload_from_string(version)
        ])
