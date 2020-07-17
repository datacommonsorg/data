import os

from google.cloud import storage

from app import configs


class GCSBucketIO:
    def __init__(self, path_prefix='', bucket_name=None, bucket=None, client=None):
        if not bucket_name:
            bucket_name = configs.BUCKET_NAME
        if not client:
            client = storage.Client()
        if not bucket:
            bucket = client.bucket(bucket_name)
        self.client = client
        self.bucket = bucket
        self.prefix = path_prefix

    def upload_file(self, src, dest):
        """Uploads a file to the bucket.

        Args:
            src: Path to the file to upload, as a string.
            dest: Destination in the bucket as a string. This will be prefixed
                by the prefix attribute.
        """
        blob = self.bucket.blob(os.path.join(self.prefix, dest))
        blob.upload_from_filename(src)

    def update_version(self, version):
        """Updates the version file in the bucket at
        <prefix>/latest_version.txt.

        Args:
            version: New version as a string
        """
        blob = self.bucket.blob(os.path.join(self.prefix, 'latest_version.txt'))
        blob.upload_from_string(version)
