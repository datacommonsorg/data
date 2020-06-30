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
Import log resource associated with the endpoint
'/import/<string:attempt_id>/logs'.
"""

from enum import Enum
import http

from flask_restful import Resource, reqparse
from google.cloud import datastore

from app import utils
from app.resource import import_attempt
from app.service import import_attempt_database


class LogLevel(Enum):
    """Allowed log levels of a log.

    The level of a log can only be one of these.
    """
    INFO = 'info'
    WARNING = 'warning'
    SEVERE = 'severe'


LOG_LEVELS = set(level.value for level in LogLevel)


class ImportLog(Resource):
    """API for managing the logs of an attempt specified by its attempt_id
    associated with the endpoint '/import/<string:attempt_id>/logs'.

    Attributes:
        database: A database service for storing import attempts
    """
    parser = reqparse.RequestParser()
    required_fields = [('level',), ('message',)]
    optional_fields = [('time_logged',)]
    utils.add_required_fields(parser, required_fields)
    utils.add_optional_fields(parser, optional_fields)

    def __init__(self):
        """Constructs an ImportLog."""
        self.database = import_attempt_database.ImportAttemptDatabase()

    def get(self, attempt_id):
        """Queries the logs of an attempt.

        Args:
            attempt_id: ID string of the attempt

        Returns:
            A list of logs of the attempt if successful. Otherwise,
            (error message, error code).
        """
        attempt = self.database.get_by_id(attempt_id)
        if not attempt:
            return import_attempt.NOT_FOUND_ERROR, http.HTTPStatus.NOT_FOUND
        return attempt.get('logs', [])

    def post(self, attempt_id):
        """Adds a new log to an existing attempt.

        time_logged must be in ISO 8601 format with timezone UTC+0, e.g.
        "2020-06-30T04:28:53.717569+00:00". If time_logged is not specified,
        the time at which the request is processed will be used.

        level must be one of the allowed levels defined by LogLevel.

        Args:
            attempt_id: ID string of the attempt

        Returns:
            A list of logs of the attempt if successful. Otherwise,
            (error message, error code).
        """
        args = ImportLog.parser.parse_args()
        if args['level'] not in LOG_LEVELS:
            return ('Log level {} is not allowed'.format(args['level']),
                    http.HTTPStatus.FORBIDDEN)

        attempt = self.database.get_by_id(attempt_id)
        if not attempt:
            return import_attempt.NOT_FOUND_ERROR, http.HTTPStatus.NOT_FOUND
        if attempt_id != args.get('attempt_id', attempt_id):
            return import_attempt.ID_NOT_MATCH_ERROR, http.HTTPStatus.CONFLICT

        args.setdefault('time_logged', utils.utctime())
        logs = attempt.setdefault('logs', [])
        log = datastore.Entity(exclude_from_indexes=('message',))
        log.update(args)
        logs.append(log)
        self.database.save(attempt)

        return logs
