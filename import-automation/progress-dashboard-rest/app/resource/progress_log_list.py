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
Progress log list resource associated with the endpoint '/logs'.
"""

import http

from app import utils
from app.resource import progress_log
from app.model import import_attempt_model
from app.model import system_run_model
from app.model import progress_log_model
from app.service import validation

_ATTEMPT = import_attempt_model.ImportAttemptModel
_RUN = system_run_model.SystemRunModel
_LOG = progress_log_model.ProgressLogModel


def add_log_to_entity(log_id, entity):
    """Adds a progress log pointer to an entity.

    Args:
        log_id: ID of the progress log as a string.
        entity: An import attempt or system run datastore Entity object.

    Returns:
        The same input entity with one log added, as a datastore Entity object.
    """
    log_ids = entity.setdefault(_ATTEMPT.logs, [])
    log_ids.append(log_id)
    return entity


class ProgressLogList(progress_log.ProgressLog):
    """API associated with the endpoint '/logs' for creating new progress logs.

    Attributes:
        See ProgressLog.
    """

    def post(self):
        """Creates a new progress log with the fields provided in the
        request body.

        Log level can only be one of the levels defined by LogLevel.
        A progress log must be linked to either a system run or an import
        attempt, or both.

        Returns:
            The created system run as a datastore Entity object with
            run_id set. Otherwise, (error message, error code), where
            the error message is a string and the error code is an int.
        """
        args = progress_log.ProgressLog.parser.parse_args()
        if args[_LOG.level] not in progress_log.LOG_LEVELS:
            return (f'Log level ({args[_LOG.level]}) is not allowed',
                    http.HTTPStatus.FORBIDDEN)
        time_logged = args.setdefault(_LOG.time_logged, utils.utctime())
        if not validation.iso_utc(time_logged):
            return (f'time_logged ({time_logged}) is not in ISO format '
                    f'with UTC timezone',
                    http.HTTPStatus.FORBIDDEN)

        run_id = args.get(_LOG.run_id)
        attempt_id = args.get(_LOG.attempt_id)
        if not run_id and not attempt_id:
            return ('Neither run_id or attempt_id is present',
                    http.HTTPStatus.FORBIDDEN)

        run = None
        attempt = None
        if run_id:
            run = self.run_database.get(run_id)
            if not run:
                return validation.get_not_found_error(_RUN.run_id, run_id)
        if attempt_id:
            attempt = self.attempt_database.get(attempt_id)
            if not attempt:
                return validation.get_not_found_error(
                    _ATTEMPT.attempt_id, attempt_id)
        if run and attempt:
            if attempt_id not in run[_RUN.import_attempts]:
                return ('The import attempt specified by the attempt_id '
                        f'({attempt_id}) in the request body is not executed '
                        'by the system run specified by the run_id '
                        f'({run_id}) in the request body',
                        http.HTTPStatus.FORBIDDEN)

        log = self.log_database.get(make_new=True)
        log.update(args)

        with self.client.transaction():
            log = self.log_database.save(log, save_content=True)
            if run:
                self.run_database.save(
                    add_log_to_entity(log.key.name, run))
            if attempt:
                self.attempt_database.save(
                    add_log_to_entity(log.key.name, attempt))
            return log
