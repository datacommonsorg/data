from google.cloud import storage


def _get_content(gcs_uri, bucket):
    blob = bucket.blob(gcs_uri)
    return blob.download_as_string().encode(blob.content_encoding)


def load_log_messages(logs, bucket):
    field = 'message'
    for log in logs:
        if field in log:
            log[field] = _get_content(log[field], bucket)
    return logs


def save_log_message(message, uri):
    pass