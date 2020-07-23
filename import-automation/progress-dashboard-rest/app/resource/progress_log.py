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
Import log resources associated with the endpoints
'/import_attempts/<string:attempt_id>/logs',
'/system_runs/<string:run_id>/logs', and '/logs/<string:log_id>'.
"""

import enum

import flask_restful
from flask_restful import reqparse

from app import utils
from app.service import validation
from app.service import import_attempt_database
from app.service import system_run_database
from app.service import progress_log_database
from app.model import import_attempt_model
from app.model import system_run_model
from app.model import progress_log_model

# TODO(intrepiditee): Rename from *_model.*Model to *.Model.
_ATTEMPT = import_attempt_model.ImportAttemptModel
_RUN = system_run_model.SystemRunModel
_LOG = progress_log_model.ProgressLogModel


# TODO(intrepiditee): Move to model.
class LogLevel(enum.Enum):
    """Allowed log levels of a log.

    The level of a log can only be one of these.
    """
    CRITICAL = 'critical'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'
    DEBUG = 'debug'


LOG_LEVELS = frozenset(level.value for level in LogLevel)


class ProgressLog(flask_restful.Resource):
    """Base class for a progress log resource.

    Attributes:
        client: datastore Client object used to communicate with Datastore.
        run_database: SystemRunDatabase object for querying and storing
            system runs using the client.
        log_database: ProgressLogDatabase object for querying and storing
            progress logs using the client.
        attempt_database: ImportAttemptDatabase object for querying and storing
            import attempts using the client.
    """
    parser = reqparse.RequestParser()
    required_fields = [(_LOG.level,), (_LOG.message,)]
    optional_fields = [(_LOG.time_logged,), (_LOG.run_id,), (_LOG.attempt_id,)]
    utils.add_fields(parser, required_fields, required=True)
    utils.add_fields(parser, optional_fields, required=False)

    # TODO(intrepiditee): Change other resources to also accept an optional arg.
    def __init__(self, client=None):
        """Constructs a ProgressLog.

        Args:
            client: datastore Client object used to communicate with Datastore.
        """
        if not client:
            client = utils.create_datastore_client()
        self.client = client
        self.run_database = system_run_database.SystemRunDatabase(self.client)
        self.log_database = progress_log_database.ProgressLogDatabase(
            self.client)
        self.attempt_database = import_attempt_database.ImportAttemptDatabase(
            self.client)


class ProgressLogByID(ProgressLog):
    """API associated with the endpoint '/logs/<string:log_id>' for querying
    a progress log by its log_id.

    Attributes:
        See ImportLog.
    """

    # TODO(intrepiditee): Use a helper for get.
    # TODO(intrepiditee): Use exception for request errors.
    def get(self, log_id):
        """Queries the progress logs by its log_id.

        Args:
            log_id: ID of the progress log as a string.

        Returns:
            A list of progress logs with messages loaded of the
            system run if successful. Otherwise, (error message, error code).
        """
        log = self.log_database.get(log_id, load_content=True)
        if not log:
            return validation.get_not_found_error(_LOG.log_id, log_id)
        return log


class ProgressLogByRunID(ProgressLog):
    """API associated with the endpoint '/import/<string:attempt_id>/logs' for
    querying the progress logs of an import attempt specified by its attempt_id.

    Attributes:
        See ImportLog.
    """

    def get(self, run_id):
        """Queries the progress logs of a system run.

        Args:
            run_id: ID of the system run as a string.

        Returns:
            A list of progress logs each as a datastore Entity object with
            messages loaded of the system run if successful. Otherwise,
            (error message, error code).
        """
        run = self.run_database.get(run_id)
        if not run:
            return validation.get_not_found_error(_RUN.run_id, run_id)
        log_ids = run.get(_RUN.logs, [])
        return {_RUN.logs: self.log_database.load_logs(log_ids)}


class ProgressLogByAttemptID(ProgressLog):
    """API associated with the endpoint '/import/<string:attempt_id>/logs' for
    querying the progress logs of an import attempt specified by its attempt_id.

    Attributes:
        See ImportLog.
    """

    def get(self, attempt_id):
        """Queries the progress logs of an import attempt.

        Args:
            attempt_id: ID of the import attempt as a string.

        Returns:
           A list of progress logs each as a datastore Entity object with
            messages loaded of the import attempt if successful. Otherwise,
            (error message, error code).
        """
        attempt = self.attempt_database.get(attempt_id)
        if not attempt:
            return validation.get_not_found_error(_ATTEMPT.attempt_id,
                                                  attempt_id)
        log_ids = attempt.get(_ATTEMPT.logs, [])
        return {_ATTEMPT.logs: self.log_database.load_logs(log_ids)}
