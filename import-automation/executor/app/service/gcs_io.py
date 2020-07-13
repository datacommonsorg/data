import os

from google.cloud import storage


class GCSBucketIO:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)


class GCSDownloader(GCSBucketIO):

    def download_dir(self, src, dest):
        os.makedirs(dest, exist_ok=True)
        for blob in self.bucket.list_blobs(prefix=src):
            file_dest = os.path.join(dest, os.path.basename(blob.name))
            self.download_file(blob.name, file_dest)

    def download_file(self, src, dest):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        blob = self.bucket.blob(src)
        blob.download_to_filename(dest)


def upload_dir(src, dest, bucket_name=None, bucket=None, client=None):
    if not bucket_name and not bucket:
        raise ValueError('neither bucket_name or bucket is specified')
    if not client:
        client = storage.Client()
    if not bucket:
        bucket = client.bucket(bucket_name)

    with os.scandir(src) as entry_iter:
        for entry in entry_iter:
            if entry.is_dir(follow_symlinks=False):
                upload_dir(
                    entry.path,
                    os.path.join(dest, entry.name),
                    bucket=bucket,
                    client=client)
            elif entry.is_file(follow_symlinks=False):
                upload_file(
                    entry.path,
                    os.path.join(dest, entry.name),
                    bucket=bucket,
                    client=client)


def upload_file(src, dest, bucket_name=None, bucket=None, client=None):
    if not bucket_name and not bucket:
        raise ValueError('neither bucket_name or bucket is specified')
    if not client:
        client = storage.Client()
    if not bucket:
        bucket = client.bucket(bucket_name)
    blob = bucket.blob(dest)
    blob.upload_from_filename(src)
