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

import google.cloud.logging


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
        parser.add_argument(
            field_name, type=data_type, action=action,
            store_missing=False, required=required, location='json')


def setup_logging():
    """Connects the default logger to Google Cloud Logging.

    Only logs at INFO level or higher will be captured.
    """
    client = google.cloud.logging.Client()
    client.get_default_handler()
    client.setup_logging()
