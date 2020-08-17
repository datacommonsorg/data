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
"""
Utility functions.
"""

import datetime
import uuid

from google.cloud import logging
from google.cloud import datastore
from google.cloud import storage

from app import configs


def utctime():
    """Returns the current time string in ISO 8601 with timezone UTC+0, e.g.
    '2020-06-30T04:28:53.717569+00:00'."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def add_fields(parser, fields, required=True):
    """Adds a set of fields to the parser.

    Args:
        parser: A reqparse RequestParser.
        fields: A set of fields to add as a list, tuple, or anything iterable.
            Each field is represented as a tuple. The first element is the name
            of field as a string. The second element, if present, is the data
            type of the string. If absent, str is used. The third element, if
            present, is the action the parser should take when encountering
            the field. If absent, 'store' is used. See
            https://flask-restful.readthedocs.io/en/latest/api.html?highlight=RequestParser#reqparse.Argument.
        required: Whether the fields are required, as a boolean.
    """
    for field in fields:
        field_name = field[0]
        data_type = field[1] if len(field) > 1 else str
        action = field[2] if len(field) > 2 else 'store'
        parser.add_argument(field_name,
                            type=data_type,
                            action=action,
                            store_missing=False,
                            required=required,
                            nullable=False)


def setup_logging():
    """Connects the default logger to Google Cloud Logging.

    Only logs at INFO level or higher will be captured.
    """
    client = logging.Client()
    client.get_default_handler()
    client.setup_logging()


def create_storage_bucket(project=configs.PROJECT_ID,
                          bucket_name=configs.LOG_BUCKET_NAME):
    """Creates a Google Cloud Storage bucket.

    Args:
        project: ID of the Google Cloud project as a string.
        bucket_name: Name of the bucket as a string.
    """
    return storage.Client(project).bucket(bucket_name)


def create_datastore_client(project=configs.PROJECT_ID,
                            namespace=configs.DASHBOARD_NAMESPACE,
                            credentials=None):
    """
    Args:
        project: ID of the Google Cloud project as a string.
        namespace: Namespace in which the import attempts will be stored
            as a string.
        credentials: Credentials to authenticate with Datastore.
    """
    return datastore.Client(project=project,
                            namespace=namespace,
                            credentials=credentials)


def get_id():
    """Returns a random UUID as a hex string."""
    return uuid.uuid4().hex


def list_to_str(a_list, sep=', '):
    """Converts a list to string.

    Args:
        a_list: The list to convert to string.
        sep: Separator between elements.

    Returns:
        String representation of the list.
    """
    return sep.join(a_list)
