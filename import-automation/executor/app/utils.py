from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2 import id_token
import google.cloud.logging
import requests


def utctime():
    return datetime.now(timezone.utc).isoformat()


def setup_logging():
    client = google.cloud.logging.Client()
    client.get_default_handler()
    client.setup_logging()

