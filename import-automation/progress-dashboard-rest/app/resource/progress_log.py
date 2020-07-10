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

import http
from enum import Enum
import flask_restful

from app import utils
from app.resource import import_attempt
from app.resource import system_run
from app.service import import_attempt_database
from app.service import system_run_database
from app.service import progress_log_database


class LogLevel(Enum):
    """Allowed log levels of a log.

    The level of a log can only be one of these.
    """
    INFO = 'info'
    WARNING = 'warning'
    SEVERE = 'severe'


LOG_LEVELS = frozenset(level.value for level in LogLevel)


class ProgressLogByID(flask_restful.Resource):

    def __init__(self):
        self.database = progress_log_database.ProgressLogDatabase()
        self.bucket = utils.create_storage_bucket()

    def get(self, log_id):
        log = self.database.get(entity_id=log_id, load_content=True)
        if not log:
            return 'not found', http.HTTPStatus.NOT_FOUND
        return log


class ProgressLogByRunID(flask_restful.Resource):
    """
    Attributes:
        See ImportLog.
    """

    def __init__(self):
        self.client = utils.create_datastore_client()
        self.run_database = system_run_database.SystemRunDatabase(
            client=self.client)
        self.log_database = progress_log_database.ProgressLogDatabase(
            client=self.client)
        self.bucket = utils.create_storage_bucket()

    def get(self, run_id):
        run = self.run_database.get(run_id)
        if not run:
            return system_run.NOT_FOUND_ERROR, http.HTTPStatus.NOT_FOUND
        log_ids = run.get('logs', [])
        return self.log_database.load_logs(log_ids, self.bucket)


class ImportLogByAttemptID(flask_restful.Resource):
    """API for managing the logs of an attempt specified by its attempt_id
    associated with the endpoint '/import/<string:attempt_id>/logs'.

    Attributes:
        See ImportLog.
    """

    def __init__(self):
        self.client = utils.create_datastore_client()
        self.attempt_database = import_attempt_database.ImportAttemptDatabase(
            client=self.client)
        self.log_database = progress_log_database.ProgressLogDatabase(
            client=self.client)
        self.bucket = utils.create_storage_bucket()

    def get(self, attempt_id):
        """Queries the logs of an attempt.

        Args:
            attempt_id: ID string of the attempt

        Returns:
            A list of logs of the attempt if successful. Otherwise,
            (error message, error code).
        """
        attempt = self.attempt_database.get(attempt_id)
        if not attempt:
            return import_attempt.NOT_FOUND_ERROR, http.HTTPStatus.NOT_FOUND
        log_ids = attempt.get('logs', [])
        return self.log_database.load_logs(log_ids, self.bucket)
