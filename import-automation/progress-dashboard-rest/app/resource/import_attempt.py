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
from app import utils


class ImportStatus(Enum):
    """Allowed status of an import attempt.

    The status of an import attempt can only be one of these.
    """
    CREATED = 'created'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


IMPORT_STATUS = set(status.value for status in ImportStatus)

ID_NOT_MATCH_ERROR = 'attempt_id in path variable does not match attempt_id ' \
                     'in request body '
NOT_FOUND_ERROR = 'attempt_id not found'


class ImportAttempt(flask_restful.Resource):
    """Base class for an import attempt resource.

    Attributes:
        database: A database service for storing import attempts
    """
    parser = reqparse.RequestParser()
    # The parser looks for these fields in the request body.
    # The Content-Type of the request must be application/json.
    optional_fields = (
        ('attempt_id',), ('branch_name',), ('repo_name',), ('pr_number', int),
        ('import_name',), ('provenance_url',), ('provenance_description',),
        ('email',), ('status',), ('time_created',), ('logs', dict, 'append')
    )
    utils.add_fields(parser, optional_fields, required=False)

    def __init__(self):
        self.database = import_attempt_database.ImportAttemptDatabase()


class ImportAttemptByID(ImportAttempt):
    """API for managing import attempts by attempt_id associated with
    '/import/<string:attempt_id>'."""

    def put(self, attempt_id):
        """Overwrites or creates an attempt with the given ID.

        time_created must be in ISO 8601 format with timezone UTC+0, e.g.
        '2020-06-30T04:28:53.717569+00:00'. If time_created is not specified,
        the time at which the request is processed will be used.

        status must be one of the allowed status defined by ImportStatus. If
        status is not specified, 'created' will be used.

        Args:
            attempt_id: ID string of the attempt

        Returns:
            The created import attempt if successful as a dict. Otherwise,
            (error message, error code), where the error message is a string
            and the error code is an int.
        """
        # See ImportAttempt class for what fields the parser looks for.
        args = ImportAttempt.parser.parse_args()
        if attempt_id != args.setdefault('attempt_id', attempt_id):
            return ID_NOT_MATCH_ERROR, http.HTTPStatus.CONFLICT
        status = args.setdefault('status', ImportStatus.CREATED.value)
        if status not in IMPORT_STATUS:
            return ('Import status {} is not allowed'.format(status),
                    http.HTTPStatus.FORBIDDEN)

        import_attempt = self.database.get_by_id(attempt_id, make_new=True)
        args.setdefault('logs', [])
        args.setdefault('time_created', utils.utctime())
        import_attempt.update(args)

        return self.database.save(import_attempt)

    def get(self, attempt_id):
        """Retrieves an attempt by its attempt_id.

        Args:
            attempt_id: ID of the attempt as a string

        Returns:
            The import attempt with the ID if successful as a dict. Otherwise,
            (error message, error code), where the error message is a string
            and the error code is an int.
        """
        import_attempt = self.database.get_by_id(attempt_id)
        if not import_attempt:
            return NOT_FOUND_ERROR, http.HTTPStatus.NOT_FOUND
        return import_attempt

    def patch(self, attempt_id):
        """Modifies the value of a field of an existing attempt.

        The attempt_id of an existing import attempt resource is forbidden
        to be patched.

        Args:
            attempt_id: ID of theI attempt as a string

        Returns:
            The import attempt with the ID if successful as a dict. Otherwise,
            (error message, error code), where the error message is a string
            and the error code is an int.
        """
        args = ImportAttempt.parser.parse_args()
        if args.get('attempt_id', attempt_id) != attempt_id:
            return 'Cannot patch attempt_id', http.HTTPStatus.FORBIDDEN

        import_attempt = self.database.get_by_id(attempt_id)
        if not import_attempt:
            return NOT_FOUND_ERROR, http.HTTPStatus.NOT_FOUND
        import_attempt.update(args)
        return self.database.save(import_attempt)


class ImportAttemptList(ImportAttempt):
    """API for querying a list of import attempts based on some criteria."""

    def get(self):
        """Retrieves a list of import attempts that pass the filter defined by
        the key-value mappings in the request body."""
        args = ImportAttempt.parser.parse_args()
        return self.database.filter(args)
