from app import utils


class LogMessageManager:
    def __init__(self):
        self.bucket = utils.create_storage_bucket()

    def load_message(self, log_id):
        blob = self.bucket.blob(log_id)
        return blob.download_as_string().decode('UTF-8')

    def save_message(self, message, log_id):
        blob = self.bucket.blob(log_id)
        blob.upload_from_string(message)
        return log_id
