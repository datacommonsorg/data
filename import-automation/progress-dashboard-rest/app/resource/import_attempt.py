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
Import attempt resources associated with the endpoints
'/import/<string:attempt_id>' and '/imports'.
"""

from enum import Enum
import http

import flask_restful
from flask_restful import reqparse

from app.service import import_attempt_database
from app.service import validation
from app import utils


class ImportAttemptStatus(Enum):
    """Allowed status of an import attempt.

    The status of an import attempt can only be one of these.
    """
    CREATED = 'created'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


IMPORT_ATTEMPT_STATUS = frozenset(
    status.value for status in ImportAttemptStatus)

ID_NOT_MATCH_ERROR = 'attempt_id in path variable does not match attempt_id ' \
                     'in request body '
NOT_FOUND_ERROR = 'attempt_id not found'


def set_import_attempt_default_values(import_attempt):
    import_attempt.setdefault('status', ImportAttemptStatus.CREATED.value)
    import_attempt.setdefault('time_created', utils.utctime())
    import_attempt.setdefault('logs', [])
    return import_attempt


class ImportAttempt(flask_restful.Resource):
    """Base class for an import attempt resource."""
    parser = reqparse.RequestParser()
    # The parser looks for these fields in the request body.
    # The Content-Type of the request must be application/json.
    optional_fields = (
        ('attempt_id', str), ('run_id', str), ('import_name',),
        ('absolute_import_name',), ('provenance_url',),
        ('provenance_description',), ('status',), ('time_created',),
        ('time_completed',), ('logs', str, 'append'),
        ('template_mcf_url',), ('node_mcf_url',), ('csv_url',)
    )
    utils.add_fields(parser, optional_fields, required=False)


class ImportAttemptByID(ImportAttempt):
    """API for managing import attempts by attempt_id associated with
    '/import/<string:attempt_id>'.

    Attributes:
        database
        client
    """

    def __init__(self):
        self.database = import_attempt_database.ImportAttemptDatabase()
        self.client = self.database.client

    def get(self, attempt_id):
        """Retrieves an attempt by its attempt_id.

        Args:
            attempt_id: ID of the attempt as a string

        Returns:
            The import attempt with the ID if successful as a dict. Otherwise,
            (error message, error code), where the error message is a string
            and the error code is an int.
        """
        with self.client.transaction():
            import_attempt = self.database.get_by_id(attempt_id)
            if not import_attempt:
                return NOT_FOUND_ERROR, http.HTTPStatus.NOT_FOUND
            return import_attempt

    def patch(self, attempt_id):
        """Modifies the value of a field of an existing attempt.

        The attempt_id and run_id of an existing import attempt resource are
        forbidden to be patched.

        Args:
            attempt_id: ID of the import attempt as a string

        Returns:
            The import attempt with the attempt_id if successful as an Entity.
            Otherwise, (error message, error code), where the error message is
            a string and the error code is an int.
        """
        args = ImportAttempt.parser.parse_args()
        valid, err, code = validation.import_attempt_valid(
            args, attempt_id=attempt_id)
        if not valid:
            return err, code
        if 'attempt_id' in args or 'run_id' in args:
            return ('Cannot patch attempt_id or run_id',
                    http.HTTPStatus.FORBIDDEN)

        with self.client.transaction():
            import_attempt = self.database.get_by_id(attempt_id)
            if not import_attempt:
                return NOT_FOUND_ERROR, http.HTTPStatus.NOT_FOUND
            import_attempt.update(args)
            return self.database.save(import_attempt)


class ImportAttemptList(ImportAttempt):
    """API for querying a list of import attempts based on some criteria."""

    def __init__(self):
        self.database = import_attempt_database.ImportAttemptDatabase()
        self.client = self.database.client

    def get(self):
        """Retrieves a list of import attempts that pass the filter defined by
        the key-value mappings in the request body."""
        args = ImportAttempt.parser.parse_args()
        return self.database.filter(args)

    def post(self):
        args = ImportAttempt.parser.parse_args()
        valid, err, code = validation.import_attempt_valid(args)
        if not valid:
            return err, code

        # Only the API can modify these fields
        args.pop('attempt_id', None)
        args.pop('run_id', None)
        args.pop('logs', None)
        set_import_attempt_default_values(args)

        with self.client.transaction():
            attempt = self.database.get_by_id(make_new=True)
            attempt.update(args)
            return self.database.save(attempt)
