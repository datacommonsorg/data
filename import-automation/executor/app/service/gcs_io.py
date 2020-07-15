import os

from google.cloud import storage

from app import configs



class GCSBucketIO:
    def __init__(self, path_prefix='', bucket_name=configs.BUCKET_NAME, bucket=None, client=None):
        if not client:
            client = storage.Client()
        if not bucket:
            bucket = client.bucket(bucket_name)
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.prefix = path_prefix

    # def download_dir(self, src, dest):
    #     os.makedirs(dest, exist_ok=True)
    #     for blob in self.bucket.list_blobs(prefix=src):
    #         file_dest = os.path.join(dest, os.path.basename(blob.name))
    #         self.download_file(blob.name, file_dest)
    #
    # def download_file(self, src, dest):
    #     os.makedirs(os.path.dirname(dest), exist_ok=True)
    #     blob = self.bucket.blob(src)
    #     blob.download_to_filename(dest)

    # def upload_dir(self, src, dest):
    #     with os.scandir(src) as entry_iter:
    #         for entry in entry_iter:
    #             if entry.is_dir(follow_symlinks=False):
    #                 self.upload_dir(entry.path, os.path.join(dest, entry.name))
    #             elif entry.is_file(follow_symlinks=False):
    #                 self.upload_file(entry.path, os.path.join(dest, entry.name))

    def upload_file(self, src, dest):
        blob = self.bucket.blob(f'{self.prefix}/{dest}')
        blob.upload_from_filename(src)

    def update_version(self, version):
        blob = self.bucket.blob(f'{self.prefix}/latest_version.txt')
        blob.upload_from_string(version)
